"""Opportunity engine and revenue metrics (TEST_ONLY fixtures)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import PipelineStage, TruthClass
from growthos.intelligence.evidence import record_evidence
from growthos.services.opportunities import (
    create_opportunity,
    score_opportunity_record,
    transition_opportunity,
)
from growthos.services.revenue import compute_revenue_metrics
from growthos.shared.errors import StateTransitionError, ValidationError


async def _evidence(session: AsyncSession):
    evidence, _ = await record_evidence(
        session,
        source_type="TEST_ONLY",
        content="TEST_ONLY: client expressed interest in a sprite engine",
        truth_class=TruthClass.FACT,
    )
    await session.flush()
    return evidence


async def test_opportunity_requires_evidence(session: AsyncSession):
    with pytest.raises(ValidationError):
        await create_opportunity(
            session, title="TEST_ONLY opp", source_evidence_id=""
        )


async def test_opportunity_creation_and_scoring(session: AsyncSession):
    evidence = await _evidence(session)
    opp = await create_opportunity(
        session,
        title="TEST_ONLY sprite engagement",
        source_evidence_id=evidence.id,
        estimated_value=Decimal("5000"),
    )
    await session.flush()
    assert opp.stage is PipelineStage.DISCOVERED

    score = await score_opportunity_record(
        session,
        opportunity_id=opp.id,
        factors={
            "need_severity": 0.9,
            "customer_fit": 0.9,
            "buyer_authority": 0.8,
            "ability_to_pay": 0.7,
            "urgency": 0.6,
            "reachability": 0.9,
            "delivery_confidence": 0.9,
            "potential_margin": 0.7,
            "strategic_value": 0.7,
            "repeat_potential": 0.5,
            "referral_potential": 0.5,
            "relationship_leverage": 0.6,
            "scope_risk": 0.2,
            "payment_risk": 0.2,
            "competitive_pressure": 0.2,
        },
    )
    assert score.overall_score > 0.0
    assert opp.probability == score.overall_score
    await session.flush()


async def test_illegal_transition_rejected(session: AsyncSession):
    evidence = await _evidence(session)
    opp = await create_opportunity(
        session,
        title="TEST_ONLY illegal transition",
        source_evidence_id=evidence.id,
    )
    await session.flush()
    with pytest.raises(StateTransitionError):
        await transition_opportunity(
            session, opportunity_id=opp.id, to_stage=PipelineStage.WON
        )


async def test_revenue_metrics_derive_from_records(session: AsyncSession):
    evidence = await _evidence(session)
    await create_opportunity(
        session,
        title="TEST_ONLY revenue",
        source_evidence_id=evidence.id,
        estimated_value=Decimal("10000"),
    )
    await session.flush()

    metrics = await compute_revenue_metrics(session)
    assert metrics.pipeline_value == Decimal("10000")
    assert metrics.active_opportunities == 1
    assert metrics.booked_revenue == Decimal("0")
