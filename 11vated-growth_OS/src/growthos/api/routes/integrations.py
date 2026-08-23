"""Integration status, Gmail sync control, drafts, and approval-gated send."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.models_identity import IntegrationAccount
from growthos.integrations.gmail_oauth import (
    clear_credentials,
    has_client_secret,
    load_access_token,
    load_refresh_token,
    oauth_state,
    revoke_token,
)
from growthos.integrations.gmail_send import execute_approved_send, request_send
from growthos.intelligence.ollama_status import ollama_status
from growthos.security.permissions import AutonomyEngine
from growthos.shared.errors import PermissionDeniedError
from growthos.workers.jobs import enqueue

router = APIRouter(prefix="/integrations", tags=["integrations"])

PROVIDERS = ["gmail", "linkedin", "sms_gateway", "ollama", "research"]


class DraftIn(BaseModel):
    to: str
    subject: str = Field(max_length=998)
    body: str = Field(max_length=200_000)
    conversation_id: str | None = None
    person_id: str | None = None


class SendIn(BaseModel):
    to: str
    subject: str = Field(max_length=998)
    body: str = Field(max_length=200_000)
    approval_id: str | None = None
    conversation_id: str | None = None
    person_id: str | None = None


class DecideIn(BaseModel):
    decision: str  # approved | denied


def _gmail_status() -> dict[str, Any]:
    state = oauth_state(
        refresh_token=load_refresh_token(),
        access_token=load_access_token(),
        error=None,
    )
    return {
        "provider": "gmail",
        "state": state.value,
        "configured": has_client_secret(),
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"],
    }


@router.get("")
async def list_integrations(session: SessionDep, founder: FounderDep):
    accounts = await session.execute(select(IntegrationAccount))
    rows = {a.provider: a for a in accounts.scalars().all()}
    integrations: list[dict[str, Any]] = []
    for provider in PROVIDERS:
        account = rows.get(provider)
        if provider == "gmail":
            status = _gmail_status()
            if account:
                status.update(
                    {
                        "account": account.display,
                        "connected_at": account.created_at,
                        "last_checked_at": account.last_checked_at,
                        "last_sync_at": (account.health or {}).get("last_sync_at"),
                        "messages_ingested": (account.health or {}).get("messages_ingested", 0),
                        "history_id": (account.health or {}).get("history_id"),
                        "error_message": account.error_message,
                    }
                )
            integrations.append(status)
        elif provider == "ollama":
            # Truthful live probe — never report connected from stale state.
            o = await ollama_status()
            integrations.append(
                {
                    "provider": "ollama",
                    "state": o.state,
                    "configured": o.state == "CONNECTED",
                    "account": o.model,
                    "model_available": o.model_available,
                    "model_pull_state": o.model_pull_state,
                    "generation_ok": o.generation_ok,
                    "structured_output_ok": o.structured_output_ok,
                    "tool_selection_ok": o.tool_selection_ok,
                    "latency_ms": o.latency_ms,
                    "models_installed": o.models_installed,
                    "last_checked_at": None,
                    "error_message": o.error_message,
                }
            )
        else:
            integrations.append(
                {
                    "provider": provider,
                    "state": (account.status.value if account else "NOT_CONFIGURED"),
                    "configured": account is not None,
                    "account": account.display if account else None,
                    "last_checked_at": account.last_checked_at if account else None,
                    "error_message": account.error_message if account else None,
                }
            )
    return {"integrations": integrations}


@router.get("/gmail/status")
async def gmail_status(session: SessionDep, founder: FounderDep):
    account = (
        await session.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.kind == "gmail",
                IntegrationAccount.provider == "gmail",
            )
        )
    ).scalar_one_or_none()
    status = _gmail_status()
    if account:
        status.update(
            {
                "account": account.display,
                "granted_scopes": account.granted_scopes,
                "connected_at": account.created_at,
                "last_checked_at": account.last_checked_at,
                "last_sync_at": (account.health or {}).get("last_sync_at"),
                "messages_ingested": (account.health or {}).get("messages_ingested", 0),
                "history_id": (account.health or {}).get("history_id"),
                "error_message": account.error_message,
            }
        )
    status["publishing_state_note"] = (
        "If the Google Cloud OAuth consent screen project is in 'Testing', "
        "refresh tokens expire after 7 days; publish the app or re-run "
        "authorization before then to avoid a silent disconnect."
    )
    return status


@router.post("/gmail/sync")
async def trigger_sync(session: SessionDep, founder: FounderDep):
    if not load_refresh_token():
        raise HTTPException(
            status_code=409,
            detail="Gmail is not authorized yet. Complete `growthos setup gmail` first.",
        )
    job = await enqueue(
        session, "gmail.sync", idempotency_key=f"gmail.sync.manual.{founder.email}"
    )
    return {"job_id": job.id, "status": "scheduled"}


@router.post("/gmail/disconnect")
async def disconnect(session: SessionDep, founder: FounderDep):
    from contextlib import suppress

    token = load_access_token() or load_refresh_token()
    if token:
        with suppress(Exception):  # best-effort revocation
            await revoke_token(token)
    clear_credentials()
    account = (
        await session.execute(
            select(IntegrationAccount).where(
                IntegrationAccount.kind == "gmail",
                IntegrationAccount.provider == "gmail",
            )
        )
    ).scalar_one_or_none()
    if account is not None:
        await session.delete(account)
    return {"ok": True}


@router.post("/gmail/drafts", status_code=201)
async def create_draft(
    session: SessionDep, founder: FounderDep, body: DraftIn
):
    """Create a draft. Drafting is autonomous; sending is not."""
    from growthos.audit import record_agent_action
    from growthos.domain.enums import AgentActionStatus, PermissionDecision
    from growthos.domain.models_comms import Outreach
    from growthos.integrations.gmail import GmailClient
    from growthos.integrations.gmail_oauth import refresh_access_token, store_access_token
    from growthos.shared.ids import new_id

    policy = AutonomyEngine().evaluate("draft_email", via_channel="web")
    if policy.decision is not PermissionDecision.ALLOW:
        raise PermissionDeniedError("drafting denied by policy")

    refresh_token = load_refresh_token()
    if not refresh_token:
        raise HTTPException(status_code=409, detail="Gmail is not authorized yet.")
    access_token = await refresh_access_token(refresh_token)
    store_access_token(access_token)
    client = GmailClient(access_token)
    draft = await client.create_draft(to=body.to, subject=body.subject, body=body.body)

    outreach = Outreach(
        id=new_id(),
        conversation_id=body.conversation_id,
        person_id=body.person_id,
        channel="email",
        state="draft",
        subject=body.subject,
        body=body.body,
    )
    session.add(outreach)
    await record_agent_action(
        session,
        actor=founder.email,
        action="draft_email",
        decision=PermissionDecision.ALLOW,
        status=AgentActionStatus.SUCCEEDED,
        tool="gmail.draft",
        integration="gmail",
        result={"gmail_draft_id": draft.get("id")},
    )
    return {"gmail_draft_id": draft.get("id"), "outreach_id": outreach.id}


@router.post("/gmail/send")
async def send_email(session: SessionDep, founder: FounderDep, body: SendIn):
    """Approval-enforced send.

    Without ``approval_id`` the request routes through the autonomy policy
    engine (REQUIRE_APPROVAL -> 202 with approval id). With an ``approval_id``
    the backend re-verifies the approval record before executing — a forged or
    unapproved id yields 403 ACTION_DENIED and an audit event.
    """
    if body.approval_id:
        try:
            result = await execute_approved_send(
                session,
                payload={
                    "approval_id": body.approval_id,
                    "to": body.to,
                    "subject": body.subject,
                    "body": body.body,
                    "actor": founder.email,
                    "person_id": body.person_id,
                    "conversation_id": body.conversation_id,
                },
            )
            return result
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    result = await request_send(
        session,
        actor=founder.email,
        to=body.to,
        subject=body.subject,
        body=body.body,
        person_id=body.person_id,
        conversation_id=body.conversation_id,
    )
    if result["status"] == "approval_required":
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=202, content=result)
    return result


@router.get("/gmail/messages/{message_id}/attachments/{attachment_id}")
async def get_attachment(
    session: SessionDep,
    founder: FounderDep,
    message_id: str,
    attachment_id: str,
):
    """On-demand attachment retrieval (never auto-downloaded at sync time)."""
    from growthos.integrations.gmail import GmailClient
    from growthos.integrations.gmail_oauth import refresh_access_token, store_access_token

    refresh_token = load_refresh_token()
    if not refresh_token:
        raise HTTPException(status_code=409, detail="Gmail is not authorized yet.")
    access_token = await refresh_access_token(refresh_token)
    store_access_token(access_token)
    client = GmailClient(access_token)
    data = await client.get_attachment(message_id, attachment_id)
    return data


# ---------------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------------

approvals_router = APIRouter(prefix="/approvals", tags=["approvals"])


@approvals_router.get("")
async def list_approvals(session: SessionDep, founder: FounderDep):
    from growthos.domain.models_system import Approval

    result = await session.execute(
        select(Approval).order_by(Approval.created_at.desc()).limit(50)
    )
    return {
        "approvals": [
            {
                "id": a.id,
                "action": a.action,
                "target_entity_type": a.target_entity_type,
                "target_entity_id": a.target_entity_id,
                "status": a.status.value,
                "reason": a.reason,
                "payload": a.payload,
                "decided_at": a.decided_at,
                "decided_by": a.decided_by,
                "created_at": a.created_at,
            }
            for a in result.scalars().all()
        ]
    }


@approvals_router.post("/{approval_id}/decide")
async def decide(
    session: SessionDep,
    founder: FounderDep,
    approval_id: str,
    body: DecideIn,
):
    from growthos.domain.enums import ApprovalStatus
    from growthos.security.approvals import decide_approval

    if body.decision not in {"approved", "denied"}:
        raise HTTPException(status_code=422, detail="decision must be approved or denied")
    decision = ApprovalStatus.APPROVED if body.decision == "approved" else ApprovalStatus.DENIED
    approval = await decide_approval(
        session, approval_id=approval_id, decision=decision, decided_by=founder.email
    )
    return {"id": approval.id, "status": approval.status.value}
