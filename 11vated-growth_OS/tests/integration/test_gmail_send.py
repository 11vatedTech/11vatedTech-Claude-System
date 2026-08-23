"""Integration tests for approval-controlled Gmail sending.

The policy gate, backend verification, suppression check, and audit trail are
exercised with a fake Gmail client injected via monkeypatch — no real network.
"""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from growthos.domain.enums import ApprovalStatus
from growthos.domain.models_comms import FounderInboxItem, Outreach, SuppressionRecord
from growthos.domain.models_evidence import SourceEvidence
from growthos.domain.models_system import AgentAction, AuditEvent
from growthos.integrations import gmail_send
from growthos.integrations.gmail_send import execute_approved_send, request_send
from growthos.security.approvals import decide_approval
from growthos.shared.errors import PermissionDeniedError


class FakeGmailClient:
    def __init__(self):
        self.sent: list[dict] = []

    async def send(self, *, to, subject, body):
        self.sent.append({"to": to, "subject": subject, "body": body})
        return {"id": f"gmail-sent-{len(self.sent)}"}


@pytest.fixture
def fake_gmail(monkeypatch):
    client = FakeGmailClient()

    async def fake_refresh(rt):
        return "at"

    monkeypatch.setattr(gmail_send, "load_refresh_token", lambda: "rt")
    monkeypatch.setattr(gmail_send, "refresh_access_token", fake_refresh)
    monkeypatch.setattr(gmail_send, "store_access_token", lambda at: None)
    monkeypatch.setattr(gmail_send, "GmailClient", lambda token: client)
    return client


async def test_send_requires_approval_and_executes_after_approval(session, fake_gmail) -> None:
    result = await request_send(
        session,
        actor="founder@11vatedtech.com",
        to="jane@example.com",
        subject="Proposal",
        body="Here is the proposal.",
    )
    assert result["status"] == "approval_required"
    approval_id = result["approval_id"]
    await session.flush()
    await session.commit()

    # Approval request surfaced as an inbox item.
    inbox = await session.scalar(select(func.count(FounderInboxItem.id)))
    assert inbox == 1

    # Founder approves (backend).
    await decide_approval(
        session, approval_id=approval_id, decision=ApprovalStatus.APPROVED, decided_by="founder@11vatedtech.com"
    )
    await session.commit()

    sent = await execute_approved_send(
        session,
        payload={
            "approval_id": approval_id,
            "to": "jane@example.com",
            "subject": "Proposal",
            "body": "Here is the proposal.",
            "actor": "founder@11vatedtech.com",
        },
    )
    await session.commit()
    assert sent["status"] == "sent"
    assert sent["gmail_message_id"].startswith("gmail-sent-")
    assert len(fake_gmail.sent) == 1

    # Persisted + audited.
    outreach = await session.scalar(select(func.count(Outreach.id)))
    assert outreach == 1
    audit = await session.scalar(
        select(func.count(AuditEvent.id)).where(AuditEvent.action == "gmail.send.sent")
    )
    assert audit == 1
    agent = await session.scalar(
        select(func.count(AgentAction.id)).where(AgentAction.action == "send_prospect_email")
    )
    assert agent == 2  # approval-request record + succeeded record


async def test_direct_send_without_approval_is_rejected(session, fake_gmail) -> None:
    with pytest.raises(PermissionDeniedError):
        await execute_approved_send(
            session,
            payload={"approval_id": None, "to": "x@example.com", "subject": "S", "body": "B", "actor": "founder"},
        )
    await session.rollback()
    assert len(fake_gmail.sent) == 0
    # A denied attempt is audited.
    blocked = await session.scalar(
        select(func.count(AuditEvent.id)).where(AuditEvent.action == "gmail.send.blocked")
    )
    assert blocked == 1


async def test_forged_unapproved_approval_id_is_rejected(session, fake_gmail) -> None:
    with pytest.raises(PermissionDeniedError):
        await execute_approved_send(
            session,
            payload={
                "approval_id": "forged-id",
                "to": "x@example.com",
                "subject": "S",
                "body": "B",
                "actor": "founder",
            },
        )
    await session.rollback()
    assert len(fake_gmail.sent) == 0


async def test_suppressed_recipient_never_sends(session, fake_gmail) -> None:
    session.add(
        SuppressionRecord(
            scope="all_channels",
            subject_type="email",
            subject_id="optout@example.com",
            reason="founder opted out",
            status="active",
            source="founder",
            created_by="founder",
        )
    )
    await session.flush()
    result = await request_send(
        session, actor="founder", to="optout@example.com", subject="S", body="B"
    )
    approval_id = result["approval_id"]
    await session.commit()
    await decide_approval(
        session, approval_id=approval_id, decision=ApprovalStatus.APPROVED, decided_by="founder"
    )
    await session.commit()

    with pytest.raises(PermissionDeniedError):
        await execute_approved_send(
            session,
            payload={
                "approval_id": approval_id,
                "to": "optout@example.com",
                "subject": "S",
                "body": "B",
                "actor": "founder",
            },
        )
    await session.rollback()
    assert len(fake_gmail.sent) == 0


async def test_send_persists_sent_evidence(session, fake_gmail) -> None:
    result = await request_send(session, actor="founder", to="a@example.com", subject="S", body="B")
    await session.commit()
    await decide_approval(
        session, approval_id=result["approval_id"], decision=ApprovalStatus.APPROVED, decided_by="founder"
    )
    await session.commit()
    await execute_approved_send(
        session,
        payload={"approval_id": result["approval_id"], "to": "a@example.com", "subject": "S", "body": "B", "actor": "founder"},
    )
    await session.commit()
    evidence = await session.scalar(select(func.count(SourceEvidence.id)))
    assert evidence == 1
