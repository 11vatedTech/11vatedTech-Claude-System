"""Health and installation-state routes."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import func, select, text

from growthos.api.deps import SessionDep
from growthos.domain import models as domain_models

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health(session: SessionDep):
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}


@router.get("/state")
async def state(session: SessionDep):
    """Installation truth: real counts, never synthetic."""

    async def count(model) -> int:
        return int(await session.scalar(select(func.count()).select_from(model)) or 0)

    return {
        "prospects": await count(domain_models.Prospect),
        "opportunities": await count(domain_models.Opportunity),
        "campaigns": await count(domain_models.Campaign),
        "products": await count(domain_models.Product),
        "people": await count(domain_models.Person),
        "companies": await count(domain_models.Company),
        "evidence": await count(domain_models.SourceEvidence),
        "messages": await count(domain_models.Message),
        "revenue_events": await count(domain_models.RevenueEvent),
    }
