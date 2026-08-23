"""Campaign engine routes."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from growthos.api.deps import FounderDep, SessionDep
from growthos.domain.models_commercial import Campaign
from growthos.services import campaigns as campaign_service

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignCreateIn(BaseModel):
    product_id: str
    name: str = Field(min_length=1, max_length=300)
    objective: str | None = None
    revenue_objective: Decimal | None = None
    buyer: str | None = None
    offer: str | None = None
    pricing_hypothesis: str | None = None
    channels: list[str] = []
    prospect_criteria: dict[str, Any] = {}


def _serialize(campaign: Campaign) -> dict[str, Any]:
    return {
        "id": campaign.id,
        "name": campaign.name,
        "product_id": campaign.product_id,
        "objective": campaign.objective,
        "revenue_objective": str(campaign.revenue_objective)
        if campaign.revenue_objective is not None
        else None,
        "buyer": campaign.buyer,
        "offer": campaign.offer,
        "channels": campaign.channels,
        "status": campaign.status.value,
        "created_at": campaign.created_at,
    }


@router.get("")
async def list_campaigns(session: SessionDep, founder: FounderDep):
    result = await session.execute(select(Campaign).order_by(Campaign.created_at))
    return {"campaigns": [_serialize(c) for c in result.scalars().all()]}


@router.post("", status_code=201)
async def create_campaign(
    session: SessionDep, founder: FounderDep, body: CampaignCreateIn
):
    try:
        campaign = await campaign_service.create_campaign(
            session,
            product_id=body.product_id,
            name=body.name,
            actor=founder.email,
            objective=body.objective,
            revenue_objective=body.revenue_objective,
            buyer=body.buyer,
            offer=body.offer,
            pricing_hypothesis=body.pricing_hypothesis,
            channels=body.channels,
            prospect_criteria=body.prospect_criteria,
        )
        return _serialize(campaign)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{campaign_id}")
async def get_campaign(
    session: SessionDep, founder: FounderDep, campaign_id: str
):
    result = await session.execute(
        select(Campaign).where(Campaign.id == campaign_id)
    )
    campaign = result.scalar_one_or_none()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _serialize(campaign)
