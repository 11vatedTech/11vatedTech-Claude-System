"""Integration tests for the first founder capability activation.

Covers the founder decision boundary (Edit & Confirm / Reject), the persistent
``CAPABILITY_CANON_CHANGED`` event, the Problem <-> Capability graph, buyer
offer hypotheses, commercial-model assessment, product/IP hypotheses, and the
capability-driven market theses — all with outbound strictly disabled.

These use the isolated ``growthos_test`` database (see conftest.py) and create
no synthetic production data.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    CapabilityStatus,
    CommercialOfferStatus,
    MarketThesisStatus,
)
from growthos.domain.models_capability import (
    CapabilityCanonEvent,
    CapabilityProductHypothesis,
    ProblemCapabilityMatch,
)
from growthos.domain.models_scout import (
    CapabilityCanon,
    CommercialOffer,
    MarketOpportunityThesis,
)
from growthos.services.capability_activation import (
    activate_capability,
    assess_commercial_models,
    confirm_capability,
    process_canon_events,
    reject_capability,
    run_capability_discovery,
    select_validation_market,
)
from growthos.shared.ids import new_id


async def _make_proposal(session: AsyncSession, name: str, definition: str) -> CapabilityCanon:
    cap = CapabilityCanon(
        id=new_id(),
        name=name,
        definition=definition,
        status=CapabilityStatus.PROPOSED,
        proof_evidence=[{"category": "TEST_EVIDENCE", "summary": "Deterministic verification exists."}],
        limitations=["not yet founder reviewed"],
        source_evidence_ids=["ev-1"],
    )
    session.add(cap)
    await session.flush()
    return cap


async def test_founder_edit_and_confirm_persists_narrowed_capability(session: AsyncSession) -> None:
    cap = await _make_proposal(
        session,
        "Interactive Sprite System Prototyping",
        "Prototype interactive sprite systems.",
    )
    confirmed = await confirm_capability(
        session,
        cap,
        name="Interactive Sprite Runtime & Behavior Prototyping",
        definition="Design and prototype interactive 2D sprite/character runtime systems.",
        maturity="PROTOTYPE_PROVEN",
        limitations=["Prototype-level commercial maturity", "No production-scale licensing"],
        external_summary="11vatedTech can prototype interactive 2D sprite runtime behaviors.",
    )
    await session.commit()

    assert confirmed.status == CapabilityStatus.FOUNDER_CONFIRMED
    assert confirmed.name == "Interactive Sprite Runtime & Behavior Prototyping"
    assert confirmed.maturity == "PROTOTYPE_PROVEN"
    assert confirmed.external_claimable is True
    assert "Prototype-level commercial maturity" in confirmed.limitations
    # External summary must not leak a local path or credential.
    assert "\\" not in (confirmed.external_summary or "")
    assert "token" not in (confirmed.external_summary or "").lower()

    events = (
        await session.execute(
            select(CapabilityCanonEvent).where(CapabilityCanonEvent.capability_id == cap.id)
        )
    ).scalars().all()
    assert any(e.event_type == "CAPABILITY_CANON_CHANGED" and e.status == "pending" for e in events)


async def test_reject_preserves_evidence_and_marks_rejected(session: AsyncSession) -> None:
    cap = await _make_proposal(
        session,
        "Interactive Frontend Development",
        "Build responsive interactive web interfaces.",
    )
    rejected = await reject_capability(
        session,
        cap,
        reason=(
            "GSPL-Sprites contains supporting project UI, but does not independently "
            "prove a general externally marketable frontend capability."
        ),
    )
    await session.commit()

    assert rejected.status == CapabilityStatus.REJECTED
    assert rejected.external_claimable is False
    assert rejected.founder_review_note and "project UI" in rejected.founder_review_note
    # Evidence and proposal are retained, not deleted.
    assert rejected.proof_evidence
    assert rejected.name == "Interactive Frontend Development"


async def test_commercial_models_do_not_overstate_licensing(session: AsyncSession) -> None:
    cap = await _make_proposal(session, "Sprite Runtime", "Prototype sprite runtime behavior.")
    models = assess_commercial_models(cap)
    by_name = {m["model"]: m["fit"] for m in models}
    assert by_name["custom prototype engagement"] == "FIT"
    assert by_name["licensing"] == "NOT_CURRENTLY_SUPPORTED"
    assert by_name["SDK/tooling"] == "NOT_CURRENTLY_SUPPORTED"
    assert by_name["middleware"] == "NOT_CURRENTLY_SUPPORTED"


async def test_activation_pipeline_builds_graph_offers_theses_and_no_outbound(
    session: AsyncSession,
) -> None:
    cap = await _make_proposal(session, "Sprite Runtime", "Prototype sprite runtime behavior.")
    await confirm_capability(
        session,
        cap,
        name="Interactive Sprite Runtime & Behavior Prototyping",
        definition="Design and prototype interactive 2D sprite/character runtime systems.",
        maturity="PROTOTYPE_PROVEN",
        limitations=["Prototype-level commercial maturity"],
        external_summary="11vatedTech can prototype interactive 2D sprite runtime behaviors.",
    )
    report = await activate_capability(session, cap)
    await session.commit()

    # Problem <-> Capability graph was created (normalized problem classes).
    assert len(report["problem_graph"]) >= 1
    matches = (
        await session.execute(
            select(ProblemCapabilityMatch).where(ProblemCapabilityMatch.capability_id == cap.id)
        )
    ).scalars().all()
    assert len(matches) == len(report["problem_graph"])

    # Offer hypotheses remain HYPOTHESIS and are buyer-oriented.
    offers = (
        await session.execute(
            select(CommercialOffer).where(CommercialOffer.included_capability_ids.contains([cap.id]))
        )
    ).scalars().all()
    assert len(offers) >= 1
    assert all(o.status == CommercialOfferStatus.HYPOTHESIS for o in offers)
    assert all(o.buyer for o in offers)

    # Product/IP/SDK/middleware hypotheses persisted separately.
    hypotheses = (
        await session.execute(
            select(CapabilityProductHypothesis).where(
                CapabilityProductHypothesis.capability_id == cap.id
            )
        )
    ).scalars().all()
    assert len(hypotheses) == 4

    # Capability-driven market theses, ranked with separate short/strategic scores.
    theses = (
        await session.execute(
            select(MarketOpportunityThesis).where(MarketOpportunityThesis.capability_id == cap.id)
        )
    ).scalars().all()
    assert len(theses) >= 3
    assert all(t.status == MarketThesisStatus.HYPOTHESIS for t in theses)
    assert report["selected_validation_market"] is not None
    selected = await select_validation_market(session, cap)
    assert selected is not None and selected.capability_id == cap.id

    # Outbound remains disabled throughout activation.
    assert report["outbound"] == "disabled"


async def test_zero_match_requalification_returns_zeros(session: AsyncSession) -> None:
    """With no prospects carrying problem evidence, requalification reports zero
    matches rather than manufacturing a dentist->sprite fit."""
    cap = await _make_proposal(session, "Sprite Runtime", "Prototype sprite runtime behavior.")
    await confirm_capability(
        session,
        cap,
        name="Interactive Sprite Runtime & Behavior Prototyping",
        definition="Design and prototype interactive 2D sprite/character runtime systems.",
        maturity="PROTOTYPE_PROVEN",
        limitations=["Prototype-level commercial maturity"],
        external_summary="11vatedTech can prototype interactive 2D sprite runtime behaviors.",
    )
    report = await activate_capability(session, cap)
    requalification = report["requalification"]
    assert requalification["reconsidered"] == 0
    assert requalification["capability_matches"] == 0
    assert requalification["no_match"] == 0


async def test_process_canon_events_is_restart_safe(session: AsyncSession) -> None:
    cap = await _make_proposal(session, "Sprite Runtime", "Prototype sprite runtime behavior.")
    await confirm_capability(
        session,
        cap,
        name="Interactive Sprite Runtime & Behavior Prototyping",
        definition="Design and prototype interactive 2D sprite/character runtime systems.",
        maturity="PROTOTYPE_PROVEN",
        limitations=["Prototype-level commercial maturity"],
        external_summary="11vatedTech can prototype interactive 2D sprite runtime behaviors.",
    )
    await session.commit()

    result = await process_canon_events(session)
    await session.commit()
    assert result["processed"]
    events = (
        await session.execute(
            select(CapabilityCanonEvent).where(CapabilityCanonEvent.capability_id == cap.id)
        )
    ).scalars().all()
    assert all(e.status == "processed" for e in events)


async def test_discovery_is_bounded_and_never_sends(session: AsyncSession) -> None:
    cap = await _make_proposal(session, "Sprite Runtime", "Prototype sprite runtime behavior.")
    await confirm_capability(
        session,
        cap,
        name="Interactive Sprite Runtime & Behavior Prototyping",
        definition="Design and prototype interactive 2D sprite/character runtime systems.",
        maturity="PROTOTYPE_PROVEN",
        limitations=["Prototype-level commercial maturity"],
        external_summary="11vatedTech can prototype interactive 2D sprite runtime behaviors.",
    )
    await build_markets(session, cap)
    report = await run_capability_discovery(session, cap, limit=15)
    # Discovery is always outbound-disabled and the cohort is bounded.
    assert report["outbound"] == "disabled"
    assert report.get("discovered", 0) <= 20
    assert report.get("new_prospects", 0) <= 20


async def build_markets(session: AsyncSession, cap: CapabilityCanon) -> None:
    from growthos.services.capability_activation import build_capability_market_theses

    await build_capability_market_theses(session, cap)
    await session.flush()
