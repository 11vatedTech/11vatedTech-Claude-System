"""Persistent job system.

Jobs survive frontend reloads and server restarts. Features:

- retry with exponential backoff
- idempotency via ``(type, idempotency_key)``
- dead-letter state after ``max_attempts`` failures
- scheduled execution and priority
- concurrency-safe claiming via ``FOR UPDATE SKIP LOCKED``
- full job history retained for inspection
"""

from __future__ import annotations

import asyncio
import secrets
import traceback
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import JobState
from growthos.domain.models_system import Job
from growthos.shared.ids import new_id

JobHandler = Callable[[AsyncSession, dict[str, Any]], Awaitable[dict[str, Any] | None]]

_HANDLERS: dict[str, JobHandler] = {}


def register_job_handler(job_type: str) -> Callable[[JobHandler], JobHandler]:
    """Register a handler function for a job type."""

    def decorator(fn: JobHandler) -> JobHandler:
        _HANDLERS[job_type] = fn
        return fn

    return decorator


def get_handler(job_type: str) -> JobHandler | None:
    return _HANDLERS.get(job_type)


def utcnow() -> datetime:
    return datetime.now(UTC)


def compute_backoff(job: Job, attempt: int) -> datetime:
    """Exponential backoff: base * 2^(attempt-1) seconds, capped at 24h."""
    seconds = min(job.backoff_base_seconds * (2 ** (attempt - 1)), 24 * 3600)
    return utcnow() + timedelta(seconds=seconds)


async def enqueue(
    session: AsyncSession,
    job_type: str,
    payload: dict[str, Any] | None = None,
    *,
    idempotency_key: str | None = None,
    scheduled_at: datetime | None = None,
    max_attempts: int = 5,
    priority: int = 0,
    backoff_base_seconds: int = 2,
) -> Job:
    """Create a job, honoring idempotency.

    If a job with the same ``(type, idempotency_key)`` already exists it is
    returned unchanged rather than duplicated.
    """
    if idempotency_key is not None:
        existing = await session.execute(
            select(Job).where(
                Job.type == job_type,
                Job.idempotency_key == idempotency_key,
            )
        )
        found = existing.scalar_one_or_none()
        if found is not None:
            return found

    job = Job(
        id=new_id(),
        type=job_type,
        payload=payload or {},
        idempotency_key=idempotency_key,
        scheduled_at=scheduled_at,
        max_attempts=max_attempts,
        priority=priority,
        backoff_base_seconds=backoff_base_seconds,
    )
    session.add(job)
    await session.flush()
    return job


async def claim_next(
    session: AsyncSession,
    worker_id: str,
    job_types: list[str] | None = None,
    limit: int = 1,
) -> list[Job]:
    """Atomically claim up to ``limit`` due jobs for a worker."""
    now = utcnow()
    stmt = select(Job).where(
        Job.state == JobState.PENDING,
        (Job.scheduled_at.is_(None)) | (Job.scheduled_at <= now),
    )
    if job_types:
        stmt = stmt.where(Job.type.in_(job_types))
    stmt = (
        stmt.order_by(Job.priority.desc(), Job.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    result = await session.execute(stmt)
    jobs = list(result.scalars().all())
    for job in jobs:
        job.state = JobState.RUNNING
        job.locked_at = now
        job.locked_by = worker_id
        job.attempts += 1
    await session.flush()
    return jobs


async def complete(
    session: AsyncSession, job: Job, result: dict[str, Any] | None = None
) -> None:
    job.state = JobState.SUCCEEDED
    job.result = result
    job.completed_at = utcnow()
    job.locked_at = None
    job.locked_by = None
    job.error = None
    await session.flush()


async def fail(
    session: AsyncSession, job: Job, error: str
) -> None:
    """Mark a job failed, scheduling a retry or moving it to dead-letter."""
    job.error = error
    if job.attempts >= job.max_attempts:
        job.state = JobState.DEAD
        job.completed_at = utcnow()
        job.locked_at = None
        job.locked_by = None
    else:
        job.state = JobState.PENDING
        job.scheduled_at = compute_backoff(job, job.attempts)
        job.locked_at = None
        job.locked_by = None
    await session.flush()


async def run_job(session: AsyncSession, job: Job) -> None:
    """Execute a claimed job's handler, recording result or error."""
    handler = get_handler(job.type)
    if handler is None:
        await fail(session, job, f"No handler registered for job type {job.type!r}")
        return
    try:
        result = await handler(session, job.payload)
        await complete(session, job, result)
    except Exception as exc:  # noqa: BLE001 - record and retry
        await fail(
            session,
            job,
            f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=5)}",
        )


class JobWorker:
    """A long-running loop that claims and executes jobs."""

    def __init__(
        self,
        session_factory,
        job_types: list[str] | None = None,
        poll_seconds: float = 1.0,
    ) -> None:
        self._session_factory = session_factory
        self._job_types = job_types
        self._poll_seconds = poll_seconds
        self._worker_id = f"worker-{secrets.token_hex(6)}"
        self._stop = asyncio.Event()

    def stop(self) -> None:
        self._stop.set()

    async def run_once(self, batch: int = 5) -> int:
        """Claim and execute one batch. Returns number of jobs handled."""
        handled = 0
        async with self._session_factory() as session:
            jobs = await claim_next(
                session, self._worker_id, self._job_types, limit=batch
            )
            for job in jobs:
                await run_job(session, job)
                handled += 1
            await session.commit()
        return handled

    async def run(self) -> None:
        while not self._stop.is_set():
            try:
                handled = await self.run_once()
                if handled == 0:
                    await asyncio.sleep(self._poll_seconds)
            except Exception:  # noqa: BLE001 - worker must survive transient errors
                await asyncio.sleep(self._poll_seconds)
