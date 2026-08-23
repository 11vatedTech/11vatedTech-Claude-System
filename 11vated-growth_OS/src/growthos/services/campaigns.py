"""Campaign engine: turning "market this" into a persisted Campaign.

A new campaign starts in DRAFT with zero real prospects. Market conclusions
are hypotheses until validated.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from growthos.audit import record_audit
from growthos.domain.enums import CampaignStatus
from growthos.domain.models_commercial import Campaign
from growthos.services.products import get_product
from growthos.shared.ids import new_id


async def create_campaign(
    session: AsyncSession,
    *,
    product_id: str,
    name: str,
    actor: str = "founder",
    objective: str | None = None,
    revenue_objective: Decimal | None = None,
    market_id: str | None = None,
    icp_id: str | None = None,
    buyer: str | None = None,
    offer: str | None = None,
    pricing_hypothesis: str | None = None,
    channels: list[str] | None = None,
    prospect_criteria: dict[str, Any] | None = None,
    messaging_strategy: str | None = None,
    proof_assets: list[str] | None = None,
    validation_goals: list[str] | None = None,
    success_metrics: list[str] | None = None,
    stop_conditions: list[str] | None = None,
) -> Campaign:
    """Create a DRAFT campaign referencing a real product."""
    await get_product(session, product_id)  # raises NotFoundError if absent
    if not name.strip():
        raise ValueError("Campaign name is required")

    campaign = Campaign(
        id=new_id(),
        name=name.strip(),
        product_id=product_id,
        objective=objective,
        revenue_objective=revenue_objective,
        market_id=market_id,
        icp_id=icp_id,
        buyer=buyer,
        offer=offer,
        pricing_hypothesis=pricing_hypothesis,
        channels=list(channels or []),
        prospect_criteria=prospect_criteria or {},
        messaging_strategy=messaging_strategy,
        proof_assets=list(proof_assets or []),
        validation_goals=list(validation_goals or []),
        success_metrics=list(success_metrics or []),
        stop_conditions=list(stop_conditions or []),
        status=CampaignStatus.DRAFT,
    )
    session.add(campaign)
    await record_audit(
        session,
        actor=actor,
        action="campaign.create",
        entity_type="campaign",
        entity_id=campaign.id,
        new_state={"name": campaign.name, "product_id": product_id, "status": "draft"},
    )
    await session.flush()
    return campaign
