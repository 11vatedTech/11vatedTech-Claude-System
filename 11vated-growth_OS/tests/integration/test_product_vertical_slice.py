"""Product intake → campaign vertical slice (persistence).

The keys are persistence across sessions and versioned history — not visual
polish. Uses only synthetic TEST_ONLY data in an isolated database.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.models_product import Product, ProductVersion
from growthos.services import campaigns, products


async def test_product_intake_persists_and_recalls(
    session: AsyncSession, session_factory
):
    product = await products.intake_product(
        session,
        name="TEST_ONLY GSPL Sprites",
        description="TEST_ONLY product",
        features=["TEST_ONLY sprite engine"],
        value_propositions=["TEST_ONLY value"],
    )
    await session.commit()

    async with session_factory() as fresh:
        recalled = await fresh.execute(
            select(Product).where(Product.id == product.id)
        )
        loaded = recalled.scalar_one()
        assert loaded.name == "TEST_ONLY GSPL Sprites"
        assert "TEST_ONLY sprite engine" in loaded.features


async def test_product_update_records_version_history(session: AsyncSession):
    product = await products.intake_product(session, name="TEST_ONLY Product A")
    await session.flush()

    _, version2 = await products.update_product(
        session,
        product_id=product.id,
        changes={"positioning": "TEST_ONLY new positioning"},
        change_summary="TEST_ONLY positioning change",
    )
    assert version2.version == 2

    versions = await session.execute(
        select(ProductVersion).where(ProductVersion.product_id == product.id)
    )
    history = versions.scalars().all()
    assert [v.version for v in history] == [1, 2]
    # History is preserved; the first snapshot differs from the second.
    assert history[0].snapshot["positioning"] != history[1].snapshot["positioning"]


async def test_campaign_references_product_and_starts_empty(session: AsyncSession):
    product = await products.intake_product(session, name="TEST_ONLY Product B")
    await session.flush()

    campaign = await campaigns.create_campaign(
        session,
        product_id=product.id,
        name="TEST_ONLY Campaign",
        objective="TEST_ONLY find customers",
    )
    await session.commit()

    assert campaign.product_id == product.id
    assert campaign.status.value == "draft"
    assert campaign.prospect_criteria == {}

    from growthos.domain.models_commercial import Prospect

    prospects = await session.execute(select(Prospect))
    assert prospects.scalars().all() == []  # zero real prospects
