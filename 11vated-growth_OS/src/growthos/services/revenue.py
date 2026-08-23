"""Deterministic revenue intelligence.

Every metric derives only from persistent records. Pipeline value is the sum
of legitimate active opportunity estimates; booked/collected revenue come only
from recorded revenue events. When data is insufficient, the result says so.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import PipelineStage
from growthos.domain.models_commercial import Opportunity, RevenueEvent

# Stages still counting as open pipeline (everything before a won/lost/terminal
# outcome).
TERMINAL_PIPELINE_STAGES = {
    PipelineStage.WON,
    PipelineStage.HANDOFF,
    PipelineStage.DELIVERY,
    PipelineStage.COMPLETED,
    PipelineStage.EXPANSION,
    PipelineStage.REFERRAL,
    PipelineStage.LOST,
    PipelineStage.DORMANT,
}


@dataclass(frozen=True)
class RevenueMetrics:
    pipeline_value: Decimal
    weighted_pipeline: Decimal
    booked_revenue: Decimal
    collected_revenue: Decimal
    active_opportunities: int
    won_opportunities: int
    has_sufficient_data: bool


async def compute_revenue_metrics(session: AsyncSession) -> RevenueMetrics:
    """Aggregate revenue/pipeline metrics from persisted state."""

    active_stages = [
        s for s in PipelineStage if s not in TERMINAL_PIPELINE_STAGES
    ]

    pipeline_value = await session.scalar(
        select(func.coalesce(func.sum(Opportunity.estimated_value), 0)).where(
            Opportunity.stage.in_(active_stages)
        )
    )

    weighted = await session.scalar(
        select(
            func.coalesce(
                func.sum(Opportunity.estimated_value * Opportunity.probability), 0
            )
        ).where(
            Opportunity.stage.in_(active_stages),
            Opportunity.estimated_value.is_not(None),
        )
    )

    active_count = await session.scalar(
        select(func.count(Opportunity.id)).where(
            Opportunity.stage.in_(active_stages)
        )
    )
    won_count = await session.scalar(
        select(func.count(Opportunity.id)).where(
            Opportunity.stage.in_(
                [
                    PipelineStage.WON,
                    PipelineStage.HANDOFF,
                    PipelineStage.DELIVERY,
                    PipelineStage.COMPLETED,
                ]
            )
        )
    )

    booked = await session.scalar(
        select(func.coalesce(func.sum(RevenueEvent.amount), 0)).where(
            RevenueEvent.event_type == "booked"
        )
    )
    collected = await session.scalar(
        select(func.coalesce(func.sum(RevenueEvent.amount), 0)).where(
            RevenueEvent.event_type == "collected"
        )
    )

    return RevenueMetrics(
        pipeline_value=Decimal(pipeline_value or 0),
        weighted_pipeline=Decimal(weighted or 0),
        booked_revenue=Decimal(booked or 0),
        collected_revenue=Decimal(collected or 0),
        active_opportunities=int(active_count or 0),
        won_opportunities=int(won_count or 0),
        has_sufficient_data=(int(active_count or 0) + int(won_count or 0)) > 0,
    )
