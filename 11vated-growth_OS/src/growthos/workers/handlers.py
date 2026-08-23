"""Concrete job handlers registered with the persistent worker.

Importing this module registers handlers (side effect). The worker CLI imports
it at startup; tests may import it directly.

Recurring jobs chain themselves: each run schedules the next future instance.
A pending (not running) instance of the same type suppresses stacking; the
currently running job never blocks the next tick because each chained instance
gets a unique idempotency key.
"""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select

from growthos.config import get_settings
from growthos.domain.enums import JobState
from growthos.domain.models_system import Job
from growthos.integrations.gmail import GmailClient
from growthos.integrations.gmail_oauth import (
    GmailSetupError,
    load_refresh_token,
    refresh_access_token,
    store_access_token,
)
from growthos.integrations.gmail_sync import sync_once
from growthos.security.sessions import cleanup_sessions
from growthos.workers.jobs import enqueue, register_job_handler, utcnow


async def ensure_scheduled(
    session,
    job_type: str,
    interval_seconds: int,
    *,
    idempotency_key: str,
) -> None:
    """Ensure a future instance of a recurring job exists (no stacking).

    Only PENDING jobs count as scheduled; the currently RUNNING instance does
    not block scheduling the next tick.
    """
    result = await session.execute(
        select(Job).where(
            Job.type == job_type,
            Job.state == JobState.PENDING,
        )
    )
    if result.scalar_one_or_none() is not None:
        return
    await enqueue(
        session,
        job_type,
        scheduled_at=utcnow() + timedelta(seconds=interval_seconds),
        idempotency_key=f"{idempotency_key}.{utcnow().isoformat()}",
        max_attempts=10,
    )


@register_job_handler("session.cleanup")
async def handle_session_cleanup(session, payload: dict) -> dict:
    """Apply session hygiene and reschedule the next pass.

    Self-rescheduling keeps cleanup running without deleting sessions on every
    restart: only the policy (expired / stale-revoked / over-cap) removes or
    revokes records, and legitimate active sessions are preserved.
    """
    stats = await cleanup_sessions(session)
    settings = get_settings()
    await ensure_scheduled(
        session,
        "session.cleanup",
        settings.session_cleanup_interval_seconds,
        idempotency_key="session.cleanup.recurring",
    )
    return stats


@register_job_handler("gmail.sync")
async def handle_gmail_sync(session, payload: dict) -> dict:
    """Run one Gmail sync pass and schedule the next tick."""
    settings = get_settings()
    refresh_token = load_refresh_token()
    if not refresh_token:
        raise GmailSetupError("Gmail not authorized: no refresh token in keychain")
    access_token = await refresh_access_token(refresh_token)
    store_access_token(access_token)  # transient; never persisted to repo
    client = GmailClient(access_token)
    summary = await sync_once(session, client=client, config=payload.get("config"))
    await ensure_scheduled(
        session,
        "gmail.sync",
        settings.gmail_sync_interval_seconds,
        idempotency_key="gmail.sync.recurring",
    )
    return summary


@register_job_handler("gmail.send")
async def handle_gmail_send(session, payload: dict) -> dict:
    """Execute an approval-controlled Gmail send.

    The approval gate runs in the route; this handler is the executor that
    re-verifies the approval record and performs the API call.
    """
    from growthos.integrations.gmail_send import execute_approved_send

    return await execute_approved_send(session, payload=payload)


@register_job_handler("scout.daily")
async def handle_scout_daily(session, payload: dict) -> dict:
    """Daily autonomous Revenue Scout loop and self-reschedule.

    The scout decides what to research, discovers real public organizations,
    scores and qualifies them, and — only inside approved campaign policy —
    prepares/executes outreach. Compliance, suppression, and the kill switch
    are enforced inside the scout service.
    """
    from growthos.config import get_settings
    from growthos.services.scout import get_control, run_discovery

    control = await get_control(session)
    summary: dict = {"skipped": False, "mode": control.mode.value}
    if control.enabled is not False and not control.kill_switch:
        summary = await run_discovery(
            session,
            limit=payload.get("limit", control.daily_prospect_target or 10),
            run_type="daily",
        )
    else:
        summary["skipped"] = True

    settings = get_settings()
    await ensure_scheduled(
        session,
        "scout.daily",
        settings.scout_daily_interval_seconds,
        idempotency_key="scout.daily.recurring",
    )
    return summary


@register_job_handler("scout.light")
async def handle_scout_light(session, payload: dict) -> dict:
    """Lightweight intraday checks: new replies, follow-ups due, thresholds.

    Never sends outreach; only surfaces founder-attention items and advances
    nothing beyond reply linking.
    """
    from growthos.config import get_settings
    from growthos.services.scout import build_founder_brief, get_control

    control = await get_control(session)
    result: dict = {"mode": control.mode.value}
    if control.enabled is not False:
        brief = await build_founder_brief(session)
        result["brief"] = brief

    settings = get_settings()
    await ensure_scheduled(
        session,
        "scout.light",
        settings.scout_light_interval_seconds,
        idempotency_key="scout.light.recurring",
    )
    return result
