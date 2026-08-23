"""Opportunity engine routes."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.enums import PipelineStage
from growthos.domain.models_commercial import Opportunity
from growthos.services import opportunities as opportunity_service
from growthos.shared.errors import StateTransitionError, ValidationError

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


class OpportunityCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    source_evidence_id: str
    company_id: str | None = None
    person_id: str | None = None
    campaign_id: str | None = None
    estimated_value: Decimal | None = None
    notes: str | None = None


class TransitionIn(BaseModel):
    to_stage: str
    reason: str | None = None


class ScoreIn(BaseModel):
    factors: dict[str, float | None]


def _serialize(opportunity: Opportunity) -> dict[str, Any]:
    return {
        "id": opportunity.id,
        "title": opportunity.title,
        "company_id": opportunity.company_id,
        "person_id": opportunity.person_id,
        "stage": opportunity.stage.value,
        "estimated_value": str(opportunity.estimated_value)
        if opportunity.estimated_value is not None
        else None,
        "probability": opportunity.probability,
        "classification": opportunity.classification.value
        if opportunity.classification
        else None,
        "confidence": opportunity.confidence,
        "next_action": opportunity.next_action,
        "created_at": opportunity.created_at,
    }


@router.get("")
async def list_opportunities(session: SessionDep, founder: FounderDep):
    result = await session.execute(
        select(Opportunity).order_by(Opportunity.created_at.desc())
    )
    return {"opportunities": [_serialize(o) for o in result.scalars().all()]}


@router.post("", status_code=201)
async def create_opportunity(
    session: SessionDep, founder: FounderDep, body: OpportunityCreateIn
):
    try:
        opportunity = await opportunity_service.create_opportunity(
            session,
            title=body.title,
            source_evidence_id=body.source_evidence_id,
            actor=founder.email,
            company_id=body.company_id,
            person_id=body.person_id,
            campaign_id=body.campaign_id,
            estimated_value=body.estimated_value,
            notes=body.notes,
        )
        return _serialize(opportunity)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{opportunity_id}/transition")
async def transition(
    session: SessionDep,
    founder: FounderDep,
    opportunity_id: str,
    body: TransitionIn,
):
    try:
        to_stage = PipelineStage(body.to_stage)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid stage") from exc
    try:
        opportunity = await opportunity_service.transition_opportunity(
            session,
            opportunity_id=opportunity_id,
            to_stage=to_stage,
            actor=founder.email,
            reason=body.reason,
        )
        return _serialize(opportunity)
    except StateTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{opportunity_id}/score")
async def score(
    session: SessionDep,
    founder: FounderDep,
    opportunity_id: str,
    body: ScoreIn,
):
    try:
        record = await opportunity_service.score_opportunity_record(
            session,
            opportunity_id=opportunity_id,
            factors=body.factors,
            actor=founder.email,
        )
        return {
            "overall_score": record.overall_score,
            "confidence": record.confidence,
            "classification": record.classification.value
            if record.classification
            else None,
            "recommended_next_action": record.recommended_next_action,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
