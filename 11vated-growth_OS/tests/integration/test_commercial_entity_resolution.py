"""Integration tests for Commercial Entity Resolution + Buyer Qualification.

Covers the pre-prospect layer: reclassification of GitHub discoveries, honest
enrichment, the promotion gate, funnel separation, source effectiveness, market
reassessment, and the no-outbound invariant. All use the isolated
``growthos_test`` database.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import (
    ActivityStatus,
    CommercialEntityStatus,
    DiscoveryCandidateState,
    NeedEvidenceClass,
    OrganizationType,
    ScoutProspectState,
)
from growthos.domain.models_commercial import Prospect
from growthos.domain.models_comms import Outreach
from growthos.domain.models_identity import Company
from growthos.domain.models_scout import (
    DiscoveryCandidate,
)
from growthos.services.entity_resolution import (
    assess_source_effectiveness,
    candidate_funnel,
    enrich_candidate,
    promote_candidate,
    reassess_market,
    reclassify_github_prospects,
)
from growthos.services.scout import funnel_counts
from growthos.shared.ids import new_id


async def _github_prospect(
    session: AsyncSession, owner: str, *, owner_type: str = "User"
) -> Prospect:
    company = Company(
        id=new_id(),
        name=owner,
        origin_source="github",
        external_ids={
            "github_owner": owner,
            "github_owner_type": owner_type,
            "github_owner_url": f"https://github.com/{owner}",
            "topics": ["2d", "sprite", "game"],
            "languages": ["GDScript"],
            "repos": [
                {
                    "full_name": f"{owner}/demo",
                    "html_url": f"https://github.com/{owner}/demo",
                    "description": "2D game",
                    "language": "GDScript",
                    "topics": ["2d", "game"],
                    "stars": 1,
                }
            ],
        },
    )
    session.add(company)
    await session.flush()
    prospect = Prospect(
        id=new_id(),
        company_id=company.id,
        status=ScoutProspectState.ENRICHMENT_REQUIRED.value,
        source="github",
        qualification={"evidence": "public GitHub repository"},
    )
    session.add(prospect)
    await session.flush()
    return prospect


def _candidate(
    owner: str,
    *,
    entity_type: OrganizationType = OrganizationType.UNKNOWN,
    commercial_status: CommercialEntityStatus = CommercialEntityStatus.COMMERCIAL_UNVERIFIED,
    need: NeedEvidenceClass = NeedEvidenceClass.NO_NEED_EVIDENCE,
    activity: ActivityStatus = ActivityStatus.UNKNOWN,
    identity: float = 0.6,
) -> DiscoveryCandidate:
    return DiscoveryCandidate(
        id=new_id(),
        source="github",
        source_identity_key=f"github:{owner}",
        canonical_name=owner,
        entity_type=entity_type,
        commercial_status=commercial_status,
        need_evidence_class=need,
        activity_status=activity,
        identity_confidence=identity,
        external_ids={"github_owner": owner, "topics": ["2d", "sprite"]},
    )


async def test_github_prospect_is_reclassified_not_deleted(session: AsyncSession) -> None:
    prospect = await _github_prospect(session, "hobby_dev")
    report = await reclassify_github_prospects(session)
    await session.commit()

    assert report["reclassified"] == 1

    # Prospect is retained but moved out of the commercial funnel.
    refreshed = (
        await session.execute(select(Prospect).where(Prospect.id == prospect.id))
    ).scalar_one()
    assert refreshed.status == ScoutProspectState.RECLASSIFIED_AS_CANDIDATE.value

    candidate = (
        await session.execute(
            select(DiscoveryCandidate).where(
                DiscoveryCandidate.legacy_prospect_id == prospect.id
            )
        )
    ).scalar_one()
    assert candidate.source == "github"
    assert candidate.source_identity_key == "github:hobby_dev"


async def test_funnel_separates_candidates_from_prospects(session: AsyncSession) -> None:
    # One real (overpass) prospect and one GitHub discovery.
    real = Company(id=new_id(), name="Real Dental", origin_source="overpass")
    session.add(real)
    await session.flush()
    session.add(
        Prospect(
            id=new_id(),
            company_id=real.id,
            status=ScoutProspectState.RESEARCHED.value,
            source="overpass",
        )
    )
    await _github_prospect(session, "gh_dev")
    await session.flush()

    await reclassify_github_prospects(session)
    await session.commit()

    funnel = await funnel_counts(session)
    # GitHub discoveries must not inflate the commercial prospect total.
    assert funnel["total"] == 1
    assert funnel["researched"] == 1
    assert funnel["discovered"] == 0

    candidate_counts = await candidate_funnel(session)
    assert candidate_counts["candidates"] == 1


async def test_hobby_candidate_enriches_non_commercial_and_is_not_promoted(
    session: AsyncSession,
) -> None:
    candidate = _candidate("hobby_owner")
    session.add(candidate)
    await session.flush()

    result = await enrich_candidate(
        session,
        candidate,
        profile={"name": "Hobby Dev", "blog": "", "company": "", "public_repos": 1},
    )
    await session.commit()

    assert result["entity_type"] == OrganizationType.HOBBY_PROJECT.value
    assert result["commercial_status"] == CommercialEntityStatus.NON_COMMERCIAL.value
    assert result["state"] == DiscoveryCandidateState.NOT_COMMERCIAL.value

    promotion = await promote_candidate(session, candidate)
    assert promotion["promoted"] is False
    assert "commercial actor" in promotion["reason"] or "commercial" in promotion["reason"]


async def test_promotion_gate_requires_commercial_verification(
    session: AsyncSession,
) -> None:
    # Even a commercial-looking GitHub org stays UNVERIFIED (GitHub is not a
    # commercial identity authority), so it cannot be promoted.
    candidate = _candidate(
        "org_studio",
        entity_type=OrganizationType.COMMERCIAL_COMPANY,
        commercial_status=CommercialEntityStatus.COMMERCIAL_UNVERIFIED,
        activity=ActivityStatus.ACTIVE,
        need=NeedEvidenceClass.INDIRECT_NEED_SIGNAL,
        identity=0.95,
    )
    session.add(candidate)
    await session.flush()

    promotion = await promote_candidate(session, candidate)
    await session.commit()

    assert promotion["promoted"] is False
    assert "commercial actor not independently verified" in promotion["reason"]


async def test_source_effectiveness_recommends_github_as_technical_only(
    session: AsyncSession,
) -> None:
    session.add(_candidate("a", entity_type=OrganizationType.HOBBY_PROJECT,
                            commercial_status=CommercialEntityStatus.NON_COMMERCIAL))
    session.add(_candidate("b", entity_type=OrganizationType.INDIVIDUAL,
                            commercial_status=CommercialEntityStatus.NON_COMMERCIAL))
    session.add(_candidate("c", entity_type=OrganizationType.UNKNOWN))
    await session.flush()

    row = await assess_source_effectiveness(session, "github", market="2D indie & mobile game studios")
    await session.commit()

    assert row.candidates_found == 3
    assert row.verified_commercial_entities == 0
    assert row.false_positive_rate > 0.0
    assert row.problem_signal_rate == 0.0
    assert "TECHNICAL" in row.recommendation or "technical" in row.recommendation
    assert "commercial" in row.recommendation.lower()


async def test_market_reassessment_distinguishes_poor_source_from_poor_market(
    session: AsyncSession,
) -> None:
    session.add(_candidate("x", entity_type=OrganizationType.HOBBY_PROJECT,
                            commercial_status=CommercialEntityStatus.NON_COMMERCIAL))
    await session.flush()

    result = await reassess_market(session, "2D indie & mobile game studios", source="github")
    await session.commit()

    assert result["conclusion"] == "POOR_SOURCE_FIT"
    # The explanation must attribute the finding to source limitation, not
    # declare the market itself bad.
    assert "source" in result["explanation"].lower()


async def test_no_outbound_ever_created(session: AsyncSession) -> None:
    """Enrichment and promotion never create outbound communication."""
    candidate = _candidate("quiet_owner")
    session.add(candidate)
    await session.flush()

    await enrich_candidate(session, candidate, profile={"public_repos": 1})
    await promote_candidate(session, candidate)
    await session.commit()

    outreach_count = await session.scalar(select(func.count(Outreach.id)))
    assert outreach_count == 0


async def test_discovery_priority_has_no_revenue_score(session: AsyncSession) -> None:
    """Candidates carry a Discovery Priority Score, never a Revenue Score."""
    candidate = _candidate("triage_owner")
    session.add(candidate)
    await session.flush()
    await enrich_candidate(
        session,
        candidate,
        profile={
            "blog": "https://triage.example",
            "company": "Triage Studio",
            "name": "Triage",
            "public_repos": 3,
            "updated_at": datetime.now(UTC).isoformat(),
        },
    )
    await session.commit()

    assert candidate.discovery_priority_score > 0.0
    # A DiscoveryCandidate has no revenue-opportunity scoring column at all.
    assert not hasattr(candidate, "revenue_opportunity_score")


async def test_restart_persistence_of_candidate(session: AsyncSession) -> None:
    """Candidates survive a session boundary (committed, re-read)."""
    candidate = _candidate("persist_owner")
    session.add(candidate)
    await session.commit()

    re_read = (
        await session.execute(
            select(DiscoveryCandidate).where(DiscoveryCandidate.id == candidate.id)
        )
    ).scalar_one()
    assert re_read.canonical_name == "persist_owner"
    assert re_read.source_identity_key == "github:persist_owner"
