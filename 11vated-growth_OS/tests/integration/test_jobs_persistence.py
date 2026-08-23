"""Persistent job system integration tests (TEST_ONLY)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import JobState
from growthos.domain.models_system import Job
from growthos.workers.jobs import claim_next, complete, enqueue, fail


async def test_enqueue_idempotent_by_key(session: AsyncSession):
    first = await enqueue(
        session, "test.job", {"x": 1}, idempotency_key="TEST_ONLY-1"
    )
    await session.flush()
    second = await enqueue(
        session, "test.job", {"x": 2}, idempotency_key="TEST_ONLY-1"
    )
    await session.flush()
    assert first.id == second.id
    assert second.payload == {"x": 1}


async def test_claim_and_complete(session: AsyncSession):
    job = await enqueue(session, "test.job", {"x": 1})
    await session.commit()

    claimed = await claim_next(session, "worker-test", ["test.job"], limit=1)
    assert len(claimed) == 1
    assert claimed[0].state is JobState.RUNNING

    await complete(session, claimed[0], {"ok": True})
    await session.commit()

    reloaded = await session.execute(select(Job).where(Job.id == job.id))
    assert reloaded.scalar_one().state is JobState.SUCCEEDED


async def test_fail_schedules_retry_then_dead_letter(session: AsyncSession):
    job = await enqueue(
        session, "test.job", max_attempts=2, backoff_base_seconds=0
    )
    await session.commit()

    claimed = await claim_next(session, "worker-test", ["test.job"], limit=1)
    await fail(session, claimed[0], "boom")
    await session.commit()

    reloaded = await session.execute(select(Job).where(Job.id == job.id))
    retried = reloaded.scalar_one()
    assert retried.state is JobState.PENDING  # retry scheduled
    assert retried.scheduled_at is not None

    # Second failure exhausts attempts -> dead-letter.
    claimed2 = await claim_next(session, "worker-test", ["test.job"], limit=1)
    assert len(claimed2) == 1
    await fail(session, claimed2[0], "boom again")
    await session.commit()

    reloaded2 = await session.execute(select(Job).where(Job.id == job.id))
    assert reloaded2.scalar_one().state is JobState.DEAD
