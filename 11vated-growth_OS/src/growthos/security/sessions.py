"""Opaque, revocable session tokens.

The client holds only a random token; the database stores its SHA-256 hash.
This makes logout and revocation deterministic.

Hygiene policy (deterministic, not on-every-restart):

- expired sessions are deleted
- revoked sessions are deleted after ``revoked_session_retention_days``
- active sessions per founder are capped at ``max_sessions_per_founder``;
  the oldest (by last-seen) are revoked first
- every policy revocation writes an ``AuditEvent``
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_audit
from growthos.config import get_settings
from growthos.domain.models_system import Session
from growthos.shared.ids import new_id


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(
    session: AsyncSession, founder_id: str
) -> tuple[str, datetime]:
    """Create a session and return (token, expires_at).

    Enforces the per-founder session cap before adding the new session so a
    single founder cannot accumulate unbounded live sessions.
    """
    settings = get_settings()
    # Make room for the new session: keep (cap - 1) live ones, revoke the rest.
    await _revoke_over_cap(session, founder_id, keep=settings.max_sessions_per_founder - 1)
    token = new_session_token()
    expires_at = datetime.now(UTC) + timedelta(
        seconds=settings.session_ttl_seconds
    )
    record = Session(
        id=new_id(),
        founder_id=founder_id,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    session.add(record)
    await session.flush()
    return token, expires_at


async def resolve_session(
    session: AsyncSession, token: str
) -> Session | None:
    """Return the live session for a token, or None."""
    result = await session.execute(
        select(Session).where(Session.token_hash == hash_token(token))
    )
    record = result.scalar_one_or_none()
    if record is None or record.revoked:
        return None
    if record.expires_at <= datetime.now(UTC):
        return None
    record.last_seen_at = datetime.now(UTC)
    await session.flush()
    return record


async def revoke_session(
    session: AsyncSession,
    record: Session,
    *,
    reason: str,
    actor: str = "founder",
) -> None:
    """Revoke a session and record an audit event."""
    record.revoked = True
    await record_audit(
        session,
        actor=actor,
        action="session.revoked",
        entity_type="session",
        entity_id=record.id,
        reason=reason,
    )
    await session.flush()


async def cleanup_sessions(session: AsyncSession) -> dict[str, int]:
    """Apply the session hygiene policy. Returns counts of affected records."""
    settings = get_settings()
    now = datetime.now(UTC)
    stats = {"expired": 0, "revoked_stale": 0, "over_cap_revoked": 0}

    # 1. Expired sessions are removed outright.
    expired = await session.execute(
        select(Session).where(Session.expires_at <= now)
    )
    expired_ids = [s.id for s in expired.scalars().all()]
    if expired_ids:
        await session.execute(delete(Session).where(Session.id.in_(expired_ids)))
        stats["expired"] = len(expired_ids)
        await record_audit(
            session,
            actor="system",
            action="session.cleanup.expired",
            entity_type="session",
            reason=f"purged {len(expired_ids)} expired session(s)",
        )

    # 2. Revoked sessions are deleted after the retention window.
    cutoff = now - timedelta(days=settings.revoked_session_retention_days)
    stale = await session.execute(
        select(Session).where(Session.revoked.is_(True), Session.updated_at < cutoff)
    )
    stale_ids = [s.id for s in stale.scalars().all()]
    if stale_ids:
        await session.execute(delete(Session).where(Session.id.in_(stale_ids)))
        stats["revoked_stale"] = len(stale_ids)
        await record_audit(
            session,
            actor="system",
            action="session.cleanup.revoked",
            entity_type="session",
            reason=f"purged {len(stale_ids)} stale revoked session(s)",
        )

    # 3. Cap live sessions per founder.
    result = await session.execute(
        select(Session.founder_id)
        .where(
            Session.revoked.is_(False),
            Session.expires_at > now,
        )
        .distinct()
    )
    for (founder_id,) in result.all():
        over = await _revoke_over_cap(
            session, founder_id, keep=settings.max_sessions_per_founder
        )
        stats["over_cap_revoked"] += over

    await session.flush()
    return stats


async def _revoke_over_cap(
    session: AsyncSession, founder_id: str, *, keep: int
) -> int:
    """Revoke the oldest live sessions beyond ``keep`` for a founder."""
    now = datetime.now(UTC)
    result = await session.execute(
        select(Session)
        .where(
            Session.founder_id == founder_id,
            Session.revoked.is_(False),
            Session.expires_at > now,
        )
        .order_by(
            Session.last_seen_at.is_(None),  # never-seen sessions are oldest
            Session.last_seen_at.asc(),
            Session.created_at.asc(),
        )
    )
    live = list(result.scalars().all())
    excess = live[keep:]
    for record in excess:
        record.revoked = True
        await record_audit(
            session,
            actor="system",
            action="session.revoked",
            entity_type="session",
            entity_id=record.id,
            reason=f"exceeded max sessions per founder ({keep})",
        )
    return len(excess)
