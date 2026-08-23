"""Persistent job system logic (no DB)."""

from datetime import timedelta

from growthos.domain.models_system import Job
from growthos.workers.jobs import compute_backoff, get_handler, register_job_handler


def _job(max_attempts: int = 5, base: int = 2) -> Job:
    return Job(
        type="test",
        max_attempts=max_attempts,
        backoff_base_seconds=base,
    )


def test_backoff_is_exponential():
    from datetime import UTC, datetime
    from unittest.mock import patch

    fixed_now = datetime(2026, 1, 1, tzinfo=UTC)
    with patch("growthos.workers.jobs.utcnow", return_value=fixed_now):
        job = _job()
        first = compute_backoff(job, 1)
        second = compute_backoff(job, 2)
        third = compute_backoff(job, 3)
    # With base=2: attempt 1 → 2s, attempt 2 → 4s, attempt 3 → 8s
    assert first - fixed_now == timedelta(seconds=2)
    assert second - fixed_now == timedelta(seconds=4)
    assert third - fixed_now == timedelta(seconds=8)


def test_backoff_caps_at_24h():
    job = _job()
    late = compute_backoff(job, 30)
    assert (late - compute_backoff(job, 0)).total_seconds() <= 24 * 3600


def test_handler_registry():
    @register_job_handler("test.registry")
    async def handler(session, payload):
        return {"ok": True}

    assert get_handler("test.registry") is handler
    assert get_handler("does.not.exist") is None
