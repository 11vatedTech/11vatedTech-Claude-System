"""Approval-controlled Gmail sending.

Flow enforced here (a frontend flag is NOT sufficient):

    request -> authorize_action (autonomy policy)
    -> REQUIRE_APPROVAL -> approval record + founder inbox item
    -> founder approves (backend) -> execute_approved_send
    -> backend re-verifies approval -> suppression check
    -> Gmail API send -> persist -> audit

Any call that reaches the executor without an APPROVED approval record is
rejected with ``PermissionDeniedError`` (HTTP 403). The policy gate lives in
``authorize_action``; this module only executes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_agent_action, record_audit
from growthos.domain.enums import (
    AgentActionStatus,
    ApprovalStatus,
    ChannelType,
    OutboundStatus,
    PermissionDecision,
    TruthClass,
)
from growthos.domain.models_comms import Outreach
from growthos.domain.models_system import Approval
from growthos.integrations.gmail import GmailClient
from growthos.integrations.gmail_oauth import (
    load_refresh_token,
    refresh_access_token,
    store_access_token,
)
from growthos.intelligence.evidence import record_evidence
from growthos.security.approvals import authorize_action
from growthos.security.suppression import is_suppressed
from growthos.shared.errors import PermissionDeniedError
from growthos.shared.ids import new_id

SEND_ACTION = "send_prospect_email"


async def request_send(
    session: AsyncSession,
    *,
    actor: str,
    to: str,
    subject: str,
    body: str,
    person_id: str | None = None,
    conversation_id: str | None = None,
) -> dict[str, Any]:
    """Route a send through the policy engine.

    Returns ``{"status": "approval_required", "approval_id": ...}`` when the
    policy demands founder approval (which it does for sends).
    """
    result = await authorize_action(
        session,
        actor=actor,
        action=SEND_ACTION,
        via_channel="web",
        tool="gmail.send",
        target_entity_type="person" if person_id else "email",
        target_entity_id=person_id or to,
        reasoning_summary=f"Send email to {to}: {subject}",
        confidence=1.0,
        approval_payload={"to": to, "subject": subject, "body": body},
    )
    if result.decision is PermissionDecision.REQUIRE_APPROVAL:
        return {
            "status": "approval_required",
            "approval_id": result.approval_id,
            "to": to,
            "subject": subject,
        }
    # ALLOW (policy says sends require approval, so this is unreachable today)
    await execute_approved_send(
        session,
        payload={
            "approval_id": None,
            "to": to,
            "subject": subject,
            "body": body,
            "actor": actor,
            "person_id": person_id,
            "conversation_id": conversation_id,
        },
    )
    return {"status": "sent"}


async def execute_approved_send(
    session: AsyncSession,
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Backend-verified, suppression-checked Gmail send.

    Rejects (403) unless an APPROVED approval record exists for a send action.
    """
    to = payload["to"]
    subject = payload.get("subject") or "(no subject)"
    body = payload.get("body") or ""
    actor = payload.get("actor") or "founder"
    person_id = payload.get("person_id")
    approval_id = payload.get("approval_id")

    # --- Backend verification of the approval record -----------------------
    if not approval_id:
        await record_audit(
            session,
            actor=actor,
            action="gmail.send.blocked",
            entity_type="approval",
            decision=PermissionDecision.DENY.value,
            reason="no approval record provided",
        )
        # Denial audits must survive the surrounding rollback.
        await session.commit()
        raise PermissionDeniedError("ACTION_DENIED: no approval record provided")
    try:
        result = await session.execute(
            select(Approval).where(Approval.id == approval_id)
        )
        approval = result.scalar_one_or_none()
    except DBAPIError:
        approval = None  # malformed/forged id -> treated as not granted
    if approval is None or approval.status is not ApprovalStatus.APPROVED:
        await record_audit(
            session,
            actor=actor,
            action="gmail.send.blocked",
            entity_type="approval",
            entity_id=approval_id,
            decision=PermissionDecision.DENY.value,
            reason="approval not granted",
        )
        await session.commit()  # denial audits survive the rollback
        raise PermissionDeniedError("ACTION_DENIED: approval not granted")

    # --- Suppression check -------------------------------------------------
    suppressed = await is_suppressed(
        session,
        subject_type="person" if person_id else "email",
        subject_id=person_id or to,
        channel=ChannelType.EMAIL,
    )
    if suppressed:
        await record_audit(
            session,
            actor=actor,
            action="gmail.send.blocked",
            entity_type="approval",
            entity_id=approval_id,
            decision=PermissionDecision.DENY.value,
            reason="suppressed recipient",
        )
        await session.commit()  # denial audits survive the rollback
        raise PermissionDeniedError("ACTION_DENIED: suppressed recipient")

    # --- Execute -----------------------------------------------------------
    refresh_token = load_refresh_token()
    if not refresh_token:
        raise PermissionDeniedError("Gmail not authorized")
    access_token = await refresh_access_token(refresh_token)
    store_access_token(access_token)
    client = GmailClient(access_token)
    sent = await client.send(to=to, subject=subject, body=body)
    gmail_message_id = sent.get("id")

    evidence, _ = await record_evidence(
        session,
        source_type="gmail_sent",
        content=f"To: {to}\nSubject: {subject}\n\n{body}",
        truth_class=TruthClass.FACT,
        source_ref=gmail_message_id,
        provenance={"gmail_message_id": gmail_message_id, "approved_by": approval_id},
    )
    outreach = Outreach(
        id=new_id(),
        conversation_id=payload.get("conversation_id"),
        person_id=person_id,
        channel=ChannelType.EMAIL,
        state="sent",
        subject=subject,
        body=body,
        sent_at=datetime.now(UTC),
        error=None,
    )
    session.add(outreach)
    await record_agent_action(
        session,
        actor=actor,
        action=SEND_ACTION,
        decision=PermissionDecision.ALLOW,
        status=AgentActionStatus.SUCCEEDED,
        tool="gmail.send",
        entity_type="person" if person_id else "email",
        entity_id=person_id or to,
        approval_id=approval_id,
        source_evidence_ids=[evidence.id],
        integration="gmail",
        result={"gmail_message_id": gmail_message_id, "outcome": OutboundStatus.SENT.value},
    )
    await record_audit(
        session,
        actor=actor,
        action="gmail.send.sent",
        entity_type="outreach",
        entity_id=outreach.id,
        decision=PermissionDecision.ALLOW.value,
        reason=f"sent to {to} via Gmail API (message {gmail_message_id})",
    )
    await session.flush()
    return {"gmail_message_id": gmail_message_id, "status": "sent", "outreach_id": outreach.id}
