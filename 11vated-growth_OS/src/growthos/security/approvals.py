"""Approval workflow and the central policy gate.

``authorize_action`` is the single chokepoint for consequential operations:

    actor -> requested action -> target -> policy -> permission
         -> approval requirement -> execution -> audit

Bypassing the UI still lands here, so the policy cannot be skipped.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_agent_action, record_audit
from growthos.domain.enums import (
    AgentActionStatus,
    ApprovalStatus,
    FounderInboxKind,
    FounderInboxStatus,
    PermissionDecision,
)
from growthos.domain.models_comms import FounderInboxItem
from growthos.domain.models_system import Approval
from growthos.security.permissions import AutonomyEngine, PolicyResult
from growthos.shared.errors import ApprovalRequiredError, PermissionDeniedError
from growthos.shared.ids import new_id


@dataclass(frozen=True)
class AuthorizationResult:
    decision: PermissionDecision
    approval_id: str | None
    reason: str | None


async def authorize_action(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    via_channel: str = "web",
    tool: str | None = None,
    target_entity_type: str | None = None,
    target_entity_id: str | None = None,
    source_evidence_ids: list[str] | None = None,
    reasoning_summary: str | None = None,
    confidence: float | None = None,
    approval_payload: dict[str, Any] | None = None,
) -> AuthorizationResult:
    """Evaluate policy and record the decision.

    - ALLOW -> agent action recorded as succeeded; caller may execute.
    - REQUIRE_APPROVAL -> approval request + inbox item created.
    - DENY -> raises ``PermissionDeniedError``.
    """
    engine = AutonomyEngine()
    policy: PolicyResult = engine.evaluate(action, via_channel=via_channel)

    if policy.decision is PermissionDecision.DENY:
        await record_agent_action(
            session,
            actor=actor,
            action=action,
            decision=PermissionDecision.DENY,
            status=AgentActionStatus.DENIED,
            tool=tool,
            entity_type=target_entity_type,
            entity_id=target_entity_id,
            source_evidence_ids=source_evidence_ids,
            reasoning_summary=reasoning_summary,
            confidence=confidence,
            error=policy.reason,
        )
        await record_audit(
            session,
            actor=actor,
            action=action,
            entity_type=target_entity_type,
            entity_id=target_entity_id,
            decision=PermissionDecision.DENY.value,
            reason=policy.reason,
        )
        raise PermissionDeniedError(policy.reason or "Denied by policy")

    if policy.decision is PermissionDecision.REQUIRE_APPROVAL:
        approval = Approval(
            id=new_id(),
            action=action,
            target_entity_type=target_entity_type or "",
            target_entity_id=target_entity_id or "",
            requested_by=actor,
            status=ApprovalStatus.REQUESTED,
            reason=policy.reason,
            payload=approval_payload or {},
        )
        session.add(approval)
        await session.flush()

        session.add(
            FounderInboxItem(
                id=new_id(),
                kind=FounderInboxKind.APPROVAL_REQUESTED,
                title=f"Approval required: {action}",
                summary=reasoning_summary or approval.reason,
                entity_type="approval",
                entity_id=approval.id,
                status=FounderInboxStatus.UNREAD,
                payload={"approval_id": approval.id, "action": action},
            )
        )

        await record_agent_action(
            session,
            actor=actor,
            action=action,
            decision=PermissionDecision.REQUIRE_APPROVAL,
            status=AgentActionStatus.REQUESTED,
            tool=tool,
            entity_type=target_entity_type,
            entity_id=target_entity_id,
            source_evidence_ids=source_evidence_ids,
            reasoning_summary=reasoning_summary,
            confidence=confidence,
            approval_id=approval.id,
        )
        await record_audit(
            session,
            actor=actor,
            action=action,
            entity_type=target_entity_type,
            entity_id=target_entity_id,
            decision=PermissionDecision.REQUIRE_APPROVAL.value,
            reason=policy.reason,
            context={"approval_id": approval.id},
        )
        return AuthorizationResult(
            decision=PermissionDecision.REQUIRE_APPROVAL,
            approval_id=approval.id,
            reason=policy.reason,
        )

    # ALLOW
    await record_agent_action(
        session,
        actor=actor,
        action=action,
        decision=PermissionDecision.ALLOW,
        status=AgentActionStatus.SUCCEEDED,
        tool=tool,
        entity_type=target_entity_type,
        entity_id=target_entity_id,
        source_evidence_ids=source_evidence_ids,
        reasoning_summary=reasoning_summary,
        confidence=confidence,
    )
    await record_audit(
        session,
        actor=actor,
        action=action,
        entity_type=target_entity_type,
        entity_id=target_entity_id,
        decision=PermissionDecision.ALLOW.value,
    )
    return AuthorizationResult(
        decision=PermissionDecision.ALLOW, approval_id=None, reason=None
    )


async def decide_approval(
    session: AsyncSession,
    *,
    approval_id: str,
    decision: ApprovalStatus,
    decided_by: str,
) -> Approval:
    """Resolve a pending approval.

    Only APPROVED or DENIED are valid decisions.
    """
    if decision not in {ApprovalStatus.APPROVED, ApprovalStatus.DENIED}:
        raise ValueError("decision must be APPROVED or DENIED")
    result = await session.execute(
        select(Approval).where(Approval.id == approval_id)
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise ApprovalRequiredError(f"Approval {approval_id!r} not found")
    approval.status = decision
    approval.decided_at = datetime.now(UTC)
    approval.decided_by = decided_by
    await record_audit(
        session,
        actor=decided_by,
        action=f"approval.{decision.value.lower()}",
        entity_type="approval",
        entity_id=approval_id,
        decision=decision.value,
    )
    await session.flush()
    return approval
