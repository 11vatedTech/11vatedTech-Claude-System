"""Qualification and Capability Canon integration tests."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import CapabilityStatus, ScoutProspectState
from growthos.domain.models_scout import CommercialOffer, WebsiteAudit
from growthos.intelligence.discovery import DiscoveredOrganization
from growthos.services.scout import (
    create_capability,
    create_prospect,
    requalify_prospect,
    review_capability,
)


class FakeAudit:
    async def audit(self, url: str) -> dict:
        return {
            "url": url,
            "http_status": 200,
            "observations": [
                {
                    "observation": "Contact/booking copy present but no HTML form found — manual workflow signal",
                    "truth_class": "inference",
                    "confidence": 0.8,
                },
                {
                    "observation": "Served over plain HTTP; booking path is not protected",
                    "truth_class": "direct_observation",
                    "confidence": 1.0,
                },
            ],
        }


def _org() -> DiscoveredOrganization:
    return DiscoveredOrganization(
        name="Evidence Dental",
        source="overpass",
        source_url="https://overpass-api.de/",
        website="https://evidence-dental.example",
        industry="dentist",
        evidence="tagged dentist; publishes a website",
        retrieval_method="overpass_query",
        captured_at=datetime.now(UTC),
        confidence=0.9,
    )


async def test_discovery_identity_does_not_become_ready_without_problem_or_capability(
    session: AsyncSession,
) -> None:
    prospect, _ = await create_prospect(session, _org())
    await session.commit()
    result = await requalify_prospect(session, prospect, audit_engine=FakeAudit())
    assert result["problem_evidence"] is True
    assert result["capability_matches"] == 0
    assert result["state"] == ScoutProspectState.PROBLEM_EVIDENCE_FOUND.value
    assert result["confidence_dimensions"]["identity_confidence"] > 0.8
    assert result["confidence_dimensions"]["capability_fit_confidence"] == 0.0
    assert result["confidence_dimensions"]["outreach_readiness_confidence"] == 0.0
    assert result["reason"] == "NO_APPROVED_CAPABILITY_MATCH"
    assert await session.scalar(select(CommercialOffer.id)) is None


async def test_founder_reviewed_capability_can_ground_hypothesis_but_not_send(
    session: AsyncSession,
) -> None:
    capability = await create_capability(
        session,
        name="Conversion-focused booking frontend",
        definition="Build a focused booking journey for a business website.",
        typical_customer_problem="booking conversion friction",
        deliverables=["responsive booking journey"],
    )
    assert capability.status == CapabilityStatus.PROPOSED
    await review_capability(
        session,
        capability,
        status=CapabilityStatus.FOUNDER_CONFIRMED.value,
        note="Founder confirms this delivery capability.",
    )
    assert capability.external_claimable is True

    prospect, _ = await create_prospect(session, _org())
    await session.commit()
    result = await requalify_prospect(session, prospect, audit_engine=FakeAudit())
    assert result["capability_matches"] == 1
    assert result["offer_id"] is not None
    assert result["state"] == ScoutProspectState.OFFER_DEFINED.value
    offer = await session.scalar(select(CommercialOffer))
    assert offer is not None
    assert offer.status.value == "HYPOTHESIS"
    assert await session.scalar(select(WebsiteAudit.id)) is not None


async def test_cannot_approve_capability_without_review_or_proof(session: AsyncSession) -> None:
    capability = await create_capability(
        session, name="Unproven Capability", definition="A proposed delivery capability."
    )
    try:
        await review_capability(session, capability, status=CapabilityStatus.EVIDENCE_VERIFIED.value)
    except ValueError as exc:
        assert "proof" in str(exc).lower() or "review" in str(exc).lower()
    else:
        raise AssertionError("unproven capability was approved")
