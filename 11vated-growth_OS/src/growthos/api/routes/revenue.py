"""Revenue intelligence routes."""

from __future__ import annotations

from fastapi import APIRouter

from growthos.api.deps import FounderDep, SessionDep
from growthos.services.revenue import compute_revenue_metrics

router = APIRouter(prefix="/revenue", tags=["revenue"])


@router.get("/metrics")
async def metrics(session: SessionDep, founder: FounderDep):
    m = await compute_revenue_metrics(session)
    return {
        "pipeline_value": str(m.pipeline_value),
        "weighted_pipeline": str(m.weighted_pipeline),
        "booked_revenue": str(m.booked_revenue),
        "collected_revenue": str(m.collected_revenue),
        "active_opportunities": m.active_opportunities,
        "won_opportunities": m.won_opportunities,
        "has_sufficient_data": m.has_sufficient_data,
    }
