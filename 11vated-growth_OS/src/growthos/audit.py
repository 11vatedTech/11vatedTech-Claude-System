"""Audit and agent-action recording.

Nothing commercially consequential happens invisibly. Every consequential
operation writes an ``AuditEvent`` and an ``AgentAction``.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    AgentActionStatus,
    PermissionDecision,
)
from growthos.domain.models_system import AgentAction, AuditEvent
from growthos.shared.ids import new_id


async def record_audit(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
    decision: str | None = None,
    reason: str | None = None,
    context: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=new_id(),
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_state=previous_state,
        new_state=new_state,
        decision=decision,
        reason=reason,
        context=context or {},
    )
    session.add(event)
    await session.flush()
    return event


async def record_agent_action(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    decision: PermissionDecision,
    status: AgentActionStatus,
    tool: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    source_evidence_ids: list[str] | None = None,
    reasoning_summary: str | None = None,
    confidence: float | None = None,
    approval_id: str | None = None,
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
    integration: str | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> AgentAction:
    record = AgentAction(
        id=new_id(),
        actor=actor,
        action=action,
        tool=tool,
        entity_type=entity_type,
        entity_id=entity_id,
        source_evidence_ids=source_evidence_ids or [],
        reasoning_summary=reasoning_summary,
        confidence=confidence,
        decision=decision,
        approval_id=approval_id,
        status=status,
        previous_state=previous_state,
        new_state=new_state,
        integration=integration,
        result=result,
        error=error,
    )
    session.add(record)
    await session.flush()
    return record
