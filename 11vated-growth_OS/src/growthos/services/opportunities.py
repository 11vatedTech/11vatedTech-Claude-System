"""Opportunity engine.

Opportunities require legitimate underlying evidence. Transitions are validated
against the pipeline state machine and recorded in history. Scoring is
deterministic.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_audit
from growthos.domain.enums import PipelineStage
from growthos.domain.models_commercial import (
    Opportunity,
    OpportunityScore,
    OpportunityTransition,
)
from growthos.domain.state_machines import assert_pipeline_transition
from growthos.intelligence.scoring import score_opportunity
from growthos.shared.errors import NotFoundError, ValidationError
from growthos.shared.ids import new_id


async def get_opportunity(
    session: AsyncSession, opportunity_id: str
) -> Opportunity:
    result = await session.execute(
        select(Opportunity).where(Opportunity.id == opportunity_id)
    )
    opportunity = result.scalar_one_or_none()
    if opportunity is None:
        raise NotFoundError(f"Opportunity {opportunity_id!r} not found")
    return opportunity


async def create_opportunity(
    session: AsyncSession,
    *,
    title: str,
    source_evidence_id: str,
    actor: str = "founder",
    company_id: str | None = None,
    person_id: str | None = None,
    campaign_id: str | None = None,
    estimated_value: Decimal | None = None,
    notes: str | None = None,
) -> Opportunity:
    """Create an opportunity from real evidence."""
    if not title.strip():
        raise ValidationError("Opportunity title is required")
    if not source_evidence_id:
        raise ValidationError("Opportunity requires source evidence")

    opportunity = Opportunity(
        id=new_id(),
        title=title.strip(),
        company_id=company_id,
        person_id=person_id,
        campaign_id=campaign_id,
        source_evidence_id=source_evidence_id,
        stage=PipelineStage.DISCOVERED,
        estimated_value=estimated_value,
        probability=0.0,
        confidence=0.0,
        notes=notes,
    )
    session.add(opportunity)
    await session.flush()

    session.add(
        OpportunityTransition(
            id=new_id(),
            opportunity_id=opportunity.id,
            from_stage=PipelineStage.DISCOVERED,
            to_stage=PipelineStage.DISCOVERED,
            reason="Opportunity created from evidence",
            actor=actor,
            occurred_at=datetime.now(UTC),
        )
    )
    await record_audit(
        session,
        actor=actor,
        action="opportunity.create",
        entity_type="opportunity",
        entity_id=opportunity.id,
        new_state={"title": title, "stage": PipelineStage.DISCOVERED.value},
        context={"source_evidence_id": source_evidence_id},
    )
    await session.flush()
    return opportunity


async def transition_opportunity(
    session: AsyncSession,
    *,
    opportunity_id: str,
    to_stage: PipelineStage,
    actor: str = "founder",
    reason: str | None = None,
) -> Opportunity:
    """Validate and record a pipeline transition."""
    opportunity = await get_opportunity(session, opportunity_id)
    assert_pipeline_transition(opportunity.stage, to_stage)

    previous = opportunity.stage
    opportunity.stage = to_stage
    if to_stage in {PipelineStage.LOST}:
        opportunity.closed_reason = reason
    session.add(
        OpportunityTransition(
            id=new_id(),
            opportunity_id=opportunity_id,
            from_stage=previous,
            to_stage=to_stage,
            reason=reason,
            actor=actor,
            occurred_at=datetime.now(UTC),
        )
    )
    await record_audit(
        session,
        actor=actor,
        action="opportunity.transition",
        entity_type="opportunity",
        entity_id=opportunity_id,
        previous_state={"stage": previous.value},
        new_state={"stage": to_stage.value},
        reason=reason,
    )
    await session.flush()
    return opportunity


async def score_opportunity_record(
    session: AsyncSession,
    *,
    opportunity_id: str,
    factors: dict[str, float | None],
    actor: str = "agent",
) -> OpportunityScore:
    """Score an opportunity and persist individual factor scores."""
    opportunity = await get_opportunity(session, opportunity_id)
    result = score_opportunity(factors)

    record = OpportunityScore(
        id=new_id(),
        opportunity_id=opportunity_id,
        need_severity=factors.get("need_severity") or 0.0,
        customer_fit=factors.get("customer_fit") or 0.0,
        buyer_authority=factors.get("buyer_authority") or 0.0,
        ability_to_pay=factors.get("ability_to_pay") or 0.0,
        urgency=factors.get("urgency") or 0.0,
        reachability=factors.get("reachability") or 0.0,
        delivery_confidence=factors.get("delivery_confidence") or 0.0,
        potential_margin=factors.get("potential_margin") or 0.0,
        strategic_value=factors.get("strategic_value") or 0.0,
        repeat_potential=factors.get("repeat_potential") or 0.0,
        referral_potential=factors.get("referral_potential") or 0.0,
        relationship_leverage=factors.get("relationship_leverage") or 0.0,
        scope_risk=factors.get("scope_risk") or 0.0,
        payment_risk=factors.get("payment_risk") or 0.0,
        competitive_pressure=factors.get("competitive_pressure") or 0.0,
        overall_score=result.overall_score,
        confidence=result.confidence,
        classification=result.classification,
        reasoning="; ".join(result.reasoning),
        recommended_next_action=result.recommended_next_action,
    )
    session.add(record)

    opportunity.probability = result.overall_score
    opportunity.confidence = result.confidence
    opportunity.classification = result.classification
    opportunity.next_action = result.recommended_next_action

    await record_audit(
        session,
        actor=actor,
        action="opportunity.score",
        entity_type="opportunity",
        entity_id=opportunity_id,
        new_state={
            "overall_score": result.overall_score,
            "confidence": result.confidence,
            "classification": result.classification.value,
        },
    )
    await session.flush()
    return record
