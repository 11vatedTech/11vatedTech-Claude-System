"""Integration tests for the Growth Agent product pipeline.

Runs against the isolated test database. Covers natural-language intake,
Product Canon persistence, truth classes, versioning, context resolution,
sales readiness, market map, pricing hypotheses, and campaign creation with
zero fabricated prospects.
"""

from __future__ import annotations

from sqlalchemy import func, select

from growthos.domain.enums import CampaignStatus, ProductMaturity
from growthos.domain.models_commercial import Campaign
from growthos.domain.models_product import Product, ProductVersion
from growthos.services.agent import handle_agent_message
from growthos.services.product_intelligence import (
    commercial_model_analysis,
    market_map,
    pricing_hypotheses,
    sales_readiness,
)


async def _count(session, model) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar() or 0


async def test_product_intake_creates_persisted_canon(session, session_factory) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message=(
            "I built a platform called StoryFrame that turns short stories into "
            "cinematic full-screen experiences. Add it as a product and help me "
            "understand how we can sell it."
        ),
    )
    await session.commit()
    assert resp.intent == "PRODUCT_INTAKE_INTENT"
    assert resp.product_id is not None

    async with session_factory() as check:
        product = await check.get(Product, resp.product_id)
        assert product is not None
        assert product.name == "StoryFrame"
        assert "cinematic full-screen experiences" in (product.definition or "")
        assert product.maturity == ProductMaturity.IDEA  # unknown stays unknown
        # Refresh survives.
        product2 = await check.get(Product, resp.product_id)
        assert product2 is not None and product2.id == product.id


async def test_intake_requires_name_and_asks(session) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="I built a platform that does great things.",
    )
    assert resp.needs_clarification is True
    assert resp.product_id is None
    assert (await _count(session, Product)) == 0


async def test_version_history_on_update(session, session_factory) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="I built a tool called Vault that helps teams organize receipts.",
    )
    await session.commit()
    pid = resp.product_id
    assert pid is not None

    resp2 = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="It's production ready now.",
        product_id=pid,
    )
    await session.commit()
    assert resp2.intent == "PRODUCT_UPDATE_INTENT"

    async with session_factory() as check:
        product = await check.get(Product, pid)
        assert product is not None
        assert product.maturity == ProductMaturity.PRODUCTION
        versions = (
            await check.execute(
                select(ProductVersion).where(ProductVersion.product_id == pid)
            )
        ).scalars().all()
        assert len(versions) == 2
        assert versions[0].version == 1
        assert versions[1].version == 2


async def test_pricing_update_is_versioned_hypothesis(session, session_factory) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="I built a platform called FrameWorks for video editors.",
    )
    await session.commit()
    pid = resp.product_id
    await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="Target pricing should start at $5,000.",
        product_id=pid,
    )
    await session.commit()
    async with session_factory() as check:
        product = await check.get(Product, pid)
        assert product is not None
        ph = product.pricing_hypotheses
        assert ph and ph[-1]["target_price"] == 5000.0
        assert ph[-1]["label"] == "PRICING HYPOTHESIS"
        assert product.maturity == ProductMaturity.IDEA  # untouched by pricing update


async def test_context_resolution_uses_persisted_entities(session) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message=(
            "I built a platform called Signal that surfaces buying signals from "
            "client email. Add it as a product."
        ),
    )
    await session.commit()
    pid = resp.product_id

    # Fresh session: context must resolve from persisted state, not chat memory.
    resp2 = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="Who should buy this?",
        product_id=pid,
    )
    assert resp2.intent == "CONTEXT_QUESTION_INTENT"
    assert "Signal" in resp2.reply


async def test_market_this_creates_draft_campaign_with_zero_prospects(
    session, session_factory
) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message=(
            "I built a platform called Atlas that maps small business "
            "relationships. Add it as a product."
        ),
    )
    await session.commit()
    pid = resp.product_id
    assert pid is not None

    resp2 = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="Market this.",
        product_id=pid,
    )
    await session.commit()
    assert resp2.intent == "MARKET_THIS_INTENT"
    assert resp2.campaign_id is not None

    async with session_factory() as check:
        campaign = await check.get(Campaign, resp2.campaign_id)
        assert campaign is not None
        assert campaign.product_id == pid
        assert campaign.status == CampaignStatus.DRAFT
        assert "0 real prospects" in resp2.reply
        # No fabricated prospects linked to the campaign.
        from growthos.domain.models_commercial import CampaignProspect

        n = (
            await check.execute(
                select(func.count()).select_from(CampaignProspect).where(
                    CampaignProspect.campaign_id == campaign.id
                )
            )
        ).scalar()
        assert n == 0


async def test_market_map_and_readiness_are_hypotheses(session, session_factory) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message=(
            "I built a product called LedgerFlow for bookkeepers. "
            "It automates reconciliation."
        ),
    )
    await session.commit()
    pid = resp.product_id
    async with session_factory() as check:
        product = await check.get(Product, pid)
        assert product is not None
        mm = market_map(product)
        assert mm["truth_class"] == "HYPOTHESIS"
        sm = sales_readiness(product)
        assert 0 <= sm["overall"] <= 100
        # Without evidence, confidence stays low — never a fabricated number.
        assert sm["components"]["pricing_confidence"]["score"] == 0.0
        ph = pricing_hypotheses(product)
        assert ph["truth_class"] == "PRICING HYPOTHESIS"
        assert ph["final_price_requires_founder_approval"] is True
        cm = commercial_model_analysis(product)
        assert cm["truth_class"] == "HYPOTHESIS"


async def test_intake_without_name_does_not_create(session) -> None:
    resp = await handle_agent_message(
        session,
        founder_email="founder@11vatedtech.com",
        message="I built an app that helps people save money.",
    )
    assert resp.needs_clarification is True
    assert (await _count(session, Product)) == 0
