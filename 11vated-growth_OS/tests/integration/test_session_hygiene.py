"""Integration tests for the deterministic session hygiene policy."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from growthos.domain.models_system import AuditEvent, Founder, Session
from growthos.security.sessions import (
    cleanup_sessions,
    create_session,
    hash_token,
    revoke_session,
)
from growthos.shared.ids import new_id


async def _founder(session) -> Founder:
    founder = Founder(
        id=new_id(),
        email="founder@11vatedtech.com",
        display_name="Founder",
        password_hash="x" * 60,
    )
    session.add(founder)
    await session.flush()
    return founder


async def _live_count(session) -> int:
    return await session.scalar(
        select(func.count(Session.id)).where(
            Session.revoked.is_(False), Session.expires_at > datetime.now(UTC)
        )
    )


async def test_create_session_enforces_cap(session) -> None:
    founder = await _founder(session)
    for _ in range(12):
        await create_session(session, founder.id)
    await session.flush()
    assert await _live_count(session) == 10
    revoked = await session.scalar(
        select(func.count(Session.id)).where(Session.revoked.is_(True))
    )
    assert revoked == 2


async def test_cleanup_purges_expired_and_stale_revoked(session) -> None:
    founder = await _founder(session)
    now = datetime.now(UTC)
    expired = Session(
        id=new_id(),
        founder_id=founder.id,
        token_hash=hash_token("expired"),
        expires_at=now - timedelta(days=1),
    )
    stale_revoked = Session(
        id=new_id(),
        founder_id=founder.id,
        token_hash=hash_token("stale"),
        expires_at=now + timedelta(days=30),
        revoked=True,
        updated_at=now - timedelta(days=30),
    )
    session.add_all([expired, stale_revoked])
    await session.flush()

    stats = await cleanup_sessions(session)
    await session.flush()
    assert stats["expired"] == 1
    assert stats["revoked_stale"] == 1
    remaining = await session.scalar(select(func.count(Session.id)))
    assert remaining == 0
    audit = await session.scalar(
        select(func.count(AuditEvent.id)).where(AuditEvent.action == "session.cleanup.expired")
    )
    assert audit == 1


async def test_cleanup_caps_live_sessions_and_audits_revocations(session) -> None:
    founder = await _founder(session)
    now = datetime.now(UTC)
    # Insert 12 live sessions directly (bypassing the create-time cap).
    for i in range(12):
        session.add(
            Session(
                id=new_id(),
                founder_id=founder.id,
                token_hash=hash_token(f"live-{i}"),
                expires_at=now + timedelta(days=30),
            )
        )
    await session.flush()
    assert await _live_count(session) == 12

    stats = await cleanup_sessions(session)
    await session.flush()
    assert stats["over_cap_revoked"] == 2
    assert await _live_count(session) == 10
    cap_audits = await session.scalar(
        select(func.count(AuditEvent.id)).where(AuditEvent.action == "session.revoked")
    )
    assert cap_audits >= 2


async def test_revoke_session_records_audit(session) -> None:
    founder = await _founder(session)
    token, _ = await create_session(session, founder.id)
    record = await session.execute(
        select(Session).where(Session.token_hash == hash_token(token))
    )
    sess = record.scalar_one()
    await revoke_session(session, sess, reason="founder logout", actor=founder.email)
    await session.flush()
    assert sess.revoked is True
    audit = await session.scalar(
        select(func.count(AuditEvent.id)).where(
            AuditEvent.action == "session.revoked", AuditEvent.reason == "founder logout"
        )
    )
    assert audit == 1
