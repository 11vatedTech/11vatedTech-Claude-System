"""Job history and inspection routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.models_system import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _serialize(job: Job) -> dict[str, Any]:
    return {
        "id": job.id,
        "type": job.type,
        "state": job.state.value,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "scheduled_at": job.scheduled_at,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "error": job.error,
    }


@router.get("")
async def list_jobs(session: SessionDep, founder: FounderDep):
    result = await session.execute(
        select(Job).order_by(Job.created_at.desc()).limit(100)
    )
    return {"jobs": [_serialize(j) for j in result.scalars().all()]}


@router.get("/{job_id}")
async def get_job(session: SessionDep, founder: FounderDep, job_id: str):
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    data = _serialize(job)
    data["payload"] = job.payload
    data["result"] = job.result
    return data
