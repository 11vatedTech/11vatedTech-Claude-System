"""Revenue Scout integration tests (TEST_ONLY, isolated test DB).

Uses a fake Overpass source (no network). Verifies the real pipeline:
discovery -> provenance -> dedup -> scoring -> qualification/rejection ->
outbound gate (compliance / kill switch / suppression / campaign policy).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    OutreachBlockReason,
    ScoutMode,
    ScoutProspectState,
    ScoutReplyClass,
)
from growthos.domain.models_commercial import Campaign, Prospect
from growthos.domain.models_commercial import Product as ProductModel
from growthos.domain.models_comms import SuppressionRecord
from growthos.domain.models_evidence import SourceEvidence
from growthos.domain.models_scout import (
    ProspectEvent,
    ScoutControl,
    ScoutRun,
)
from growthos.intelligence.discovery import DiscoveredOrganization
from growthos.services.scout import (
    check_campaign_policy,
    compliance_status,
    create_prospect,
    draft_outreach,
    find_duplicate_prospect,
    get_control,
    link_reply,
    outbound_gate,
    run_discovery,
    transition_prospect,
)


class FakeOverpass:
    kind = "overpass"

    def __init__(self, orgs: list[DiscoveredOrganization]):
        self.orgs = orgs

    async def search(self, query: dict, limit: int = 50):
        return self.orgs[:limit]


def _org(
    name: str,
    *,
    website: str | None = None,
    email: str | None = None,
    industry: str | None = None,
    location: str | None = None,
    confidence: float = 0.7,
) -> DiscoveredOrganization:
    return DiscoveredOrganization(
        name=name,
        source="overpass",
        source_url="https://overpass-api.de/",
        website=website,
        email=email,
        industry=industry,
        location=location,
        evidence=f"tagged {industry or 'business'}; located at {location or 'unknown'}",
        retrieval_method="overpass_query",
        captured_at=datetime.now(UTC),
        confidence=confidence,
    )


async def _seed_control(session: AsyncSession) -> ScoutControl:
    control = await get_control(session)
    control.mode = ScoutMode.ASSIST
    control.enabled = True
    control.kill_switch = False
    control.min_revenue_score = 0.0  # so tests can exercise qualification both ways
    control.min_evidence_confidence = 0.0
    # Compliance prerequisites configured by default in tests.
    control.business_postal_address = "11vatedTech, 1 Main St"
    control.opt_out_email = "unsubscribe@11vatedtech.com"
    await session.flush()
    return control


async def test_discovery_creates_real_prospects_with_provenance(session: AsyncSession) -> None:
    await _seed_control(session)
    orgs = [
        _org("Joe's Dental", website="https://joesdental.com", email="hello@joesdental.com", industry="dentist"),
        _org("Main St Cafe", website="https://mainstcafe.example", industry="cafe"),
    ]
    import growthos.services.scout as scout_module

    original = scout_module.discovery_sources
    scout_module.discovery_sources = lambda: {"overpass": FakeOverpass(orgs), "website_audit": object()}
    try:
        report = await run_discovery(session, limit=10)
        await session.commit()
    finally:
        scout_module.discovery_sources = original

    assert report["discovered"] == 2
    assert report["new_prospects"] == 2

    prospects = (await session.execute(select(Prospect))).scalars().all()
    assert len(prospects) == 2
    for p in prospects:
        assert p.source == "overpass"
        assert p.source_evidence_id is not None
        assert p.status == ScoutProspectState.ENRICHMENT_REQUIRED.value
        # Every prospect has a real company + evidence.
        assert p.company_id is not None
        assert p.qualification.get("evidence")

    evidence = await session.scalar(select(func.count(SourceEvidence.id)))
    assert evidence == 2
    runs = await session.scalar(select(func.count(ScoutRun.id)))
    assert runs == 1


async def test_dedup_prevents_rediscovery(session: AsyncSession) -> None:
    await _seed_control(session)
    org = _org("Joe's Dental", website="https://joesdental.com", email="hello@joesdental.com")

    first, is_new = await create_prospect(session, org)
    await session.commit()
    assert is_new is True

    dup, is_new = await create_prospect(session, org)
    await session.commit()
    assert is_new is False
    assert dup.id == first.id

    # Domain-based dedup (same site, different email).
    org2 = _org(
        "Joe's Dental LLC",
        website="https://joesdental.com",
        email="bookings@joesdental.com",
    )
    dup2, is_new2 = await create_prospect(session, org2)
    assert is_new2 is False
    assert dup2.id == first.id

    found = await find_duplicate_prospect(session, website="https://www.joesdental.com/")
    assert found is not None
    assert found.id == first.id


async def test_qualification_and_rejection_state_machine(session: AsyncSession) -> None:
    control = await _seed_control(session)
    # Discovery factors are deliberately conservative; 0.3 is reachable by a
    # strong listing (0.9 confidence) but not by a bare listing (0.1).
    control.min_revenue_score = 0.3
    control.min_evidence_confidence = 0.5
    await session.flush()

    strong = _org(
        "Strong Prospect Co",
        website="https://strong.example",
        email="ceo@strong.example",
        industry="dentist",
        confidence=0.9,
    )
    weak = _org("Weak Listing", industry="unknown", confidence=0.1)

    import growthos.services.scout as scout_module

    original = scout_module.discovery_sources
    scout_module.discovery_sources = lambda: {"overpass": FakeOverpass([strong, weak]), "website_audit": object()}
    try:
        report = await run_discovery(session, limit=10)
        await session.commit()
    finally:
        scout_module.discovery_sources = original

    assert report["qualified"] == 0
    assert report["rejected"] == 0
    assert report["enrichment_required"] == 2

    prospects = (await session.execute(select(Prospect))).scalars().all()
    assert {p.status for p in prospects} == {ScoutProspectState.ENRICHMENT_REQUIRED.value}

    # Discovery is audited as requiring enrichment rather than pretending to qualify.
    rejected = prospects[0]
    events = (
        await session.execute(
            select(ProspectEvent).where(ProspectEvent.prospect_id == rejected.id)
        )
    ).scalars().all()
    assert any(e.to_state == ScoutProspectState.ENRICHMENT_REQUIRED for e in events)


async def test_invalid_transition_rejected(session: AsyncSession) -> None:
    org = _org("Some Co", website="https://someco.example")
    prospect, _ = await create_prospect(session, org)
    await session.commit()
    with pytest.raises(ValueError):
        # WON directly from DISCOVERED is invalid.
        await transition_prospect(session, prospect, ScoutProspectState.WON)
    await session.rollback()


async def test_compliance_gate_blocks_without_postal_address(session: AsyncSession) -> None:
    control = await _seed_control(session)
    control.business_postal_address = None
    control.opt_out_email = None
    await session.flush()

    status = await compliance_status(session)
    assert status["outbound_marketing_allowed"] is False
    assert status["block_reason"] == OutreachBlockReason.COMPLIANCE_NOT_CONFIGURED.value


async def test_kill_switch_blocks_outbound_but_allows_research(session: AsyncSession) -> None:
    control = await _seed_control(session)
    control.kill_switch = True
    await session.flush()

    org = _org("Kill Co", website="https://killco.example", email="info@killco.example")
    prospect, _ = await create_prospect(session, org)
    await session.commit()

    ok, reason, _detail = await outbound_gate(session, prospect=prospect, campaign=None)
    assert ok is False
    assert reason == OutreachBlockReason.KILL_SWITCH.value

    # Research may continue with the kill switch on.
    import growthos.services.scout as scout_module

    original = scout_module.discovery_sources
    scout_module.discovery_sources = lambda: {"overpass": FakeOverpass([org]), "website_audit": object()}
    try:
        report = await run_discovery(session, limit=5)
        await session.commit()
    finally:
        scout_module.discovery_sources = original
    assert report["discovered"] == 1


async def test_mode_observe_blocks_outreach(session: AsyncSession) -> None:
    control = await _seed_control(session)
    control.mode = ScoutMode.OBSERVE
    await session.flush()

    org = _org("Observe Co", website="https://observe.example", email="info@observe.example")
    prospect, _ = await create_prospect(session, org)
    await session.commit()

    ok, reason, _detail = await outbound_gate(session, prospect=prospect, campaign=None)
    assert ok is False
    assert reason == OutreachBlockReason.MODE_OBSERVE.value


async def test_suppression_overrides_autonomy(session: AsyncSession) -> None:
    await _seed_control(session)
    org = _org("Suppressed Co", website="https://suppressed.example", email="info@suppressed.example")
    prospect, _ = await create_prospect(session, org)
    await session.commit()

    session.add(
        SuppressionRecord(
            id=__import__("growthos.shared.ids", fromlist=["new_id"]).new_id(),
            scope="all_channels",
            subject_type="company",
            subject_id=prospect.company_id,
            reason="opted out",
            status="active",
        )
    )
    await session.commit()

    ok, reason, _detail = await outbound_gate(session, prospect=prospect, campaign=None)
    assert ok is False
    assert reason == OutreachBlockReason.SUPPRESSED.value


async def test_campaign_policy_denies_ineligible_prospect(session: AsyncSession) -> None:
    await _seed_control(session)
    org = _org(
        "Excluded Industry Co",
        website="https://excluded.example",
        email="info@excluded.example",
        industry="restaurant",
    )
    prospect, _ = await create_prospect(session, org)
    await session.commit()

    product = ProductModel(id=__import__("growthos.shared.ids", fromlist=["new_id"]).new_id(), name="Test Product")
    session.add(product)
    await session.flush()
    campaign = Campaign(
        id=__import__("growthos.shared.ids", fromlist=["new_id"]).new_id(),
        name="Dentists Only",
        product_id=product.id,
        status="active",
        prospect_criteria={"industries": ["dentist"], "excluded_industries": ["restaurant"]},
    )
    session.add(campaign)
    await session.commit()

    ok, reason = await check_campaign_policy(session, campaign, prospect)
    assert ok is False
    assert reason  # industry fails target criteria / exclusion policy

    ok2, reason2, _detail2 = await outbound_gate(session, prospect=prospect, campaign=campaign)
    assert ok2 is False
    assert reason2 == OutreachBlockReason.CAMPAIGN_POLICY.value


async def test_draft_outreach_and_reply_linking(session: AsyncSession) -> None:
    await _seed_control(session)
    org = _org(
        "Reply Co",
        website="https://reply.example",
        email="hello@reply.example",
        industry="dentist",
    )
    prospect, _ = await create_prospect(session, org)
    await session.commit()

    product = ProductModel(id=__import__("growthos.shared.ids", fromlist=["new_id"]).new_id(), name="Test Product")
    session.add(product)
    await session.flush()
    campaign = Campaign(
        id=__import__("growthos.shared.ids", fromlist=["new_id"]).new_id(),
        name="Test Campaign",
        product_id=product.id,
        status="active",
        prospect_criteria={},
    )
    session.add(campaign)
    await session.commit()

    # Drafting is blocked until the full qualification lifecycle is complete.
    prospect.qualification = {
        "problem_evidence": "Publicly observed booking friction",
        "capability_match": {"name": "approved booking UX"},
        "offer_id": "offer-hypothesis",
    }
    for state in (
        ScoutProspectState.RESEARCHING,
        ScoutProspectState.RESEARCHED,
        ScoutProspectState.PROBLEM_EVIDENCE_FOUND,
        ScoutProspectState.CAPABILITY_MATCHED,
        ScoutProspectState.OFFER_DEFINED,
        ScoutProspectState.CONTACT_PATH_VERIFIED,
        ScoutProspectState.SALES_QUALIFIED,
        ScoutProspectState.READY_TO_CONTACT,
    ):
        await transition_prospect(session, prospect, state, reason="test qualification evidence")
    await session.commit()
    outreach = await draft_outreach(session, prospect, campaign, offer="a booking experience")
    await session.commit()
    assert outreach.prospect_id == prospect.id
    assert outreach.campaign_id == campaign.id
    assert "Reply Co" in outreach.body
    assert outreach.state == "draft"

    # Positive reply -> ENGAGED.
    await link_reply(
        session,
        prospect,
        reply_class=ScoutReplyClass.POSITIVE_INTEREST,
        reason="they asked for a call",
    )
    await session.commit()
    reloaded = (
        await session.execute(select(Prospect).where(Prospect.id == prospect.id))
    ).scalar_one()
    assert reloaded.status == ScoutProspectState.ENGAGED.value

    # Opt-out -> suppression + archived.
    opt_prospect, _ = await create_prospect(
        session, _org("Opt Co", website="https://opt.example", email="no@opt.example")
    )
    await link_reply(session, opt_prospect, reply_class=ScoutReplyClass.OPT_OUT, reason="please stop")
    await session.commit()
    assert (
        await session.scalar(
            select(Prospect).where(Prospect.id == opt_prospect.id)
        )
    ).status == ScoutProspectState.ARCHIVED.value
    suppressions = await session.scalar(select(func.count(SuppressionRecord.id)))
    assert suppressions >= 1
