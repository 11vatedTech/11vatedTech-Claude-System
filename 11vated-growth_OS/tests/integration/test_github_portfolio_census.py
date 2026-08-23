"""Integration tests for the GitHub portfolio evidence census service.

Covers: profile registration, repository persistence, family clustering,
cross-project capability proposals (all PROPOSED, none confirmed), empty-repo
suppression, and the no-outbound invariant. Uses the isolated test database.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import CapabilityStatus
from growthos.domain.models_capability import (
    ProjectFamily,
    RepositoryEvidence,
)
from growthos.domain.models_comms import Outreach
from growthos.domain.models_scout import CapabilityCanon
from growthos.services.portfolio_census import (
    census_report,
    cluster_families_and_link,
    ensure_authorized_profiles,
    generate_capability_proposals,
)
from growthos.shared.ids import new_id


def _repo(
    session: AsyncSession,
    profile_id: str,
    name: str,
    *,
    source_present: bool = True,
    tests: bool = False,
    ci: bool = False,
    empty: bool = False,
    languages: list[str] | None = None,
    topics: list[str] | None = None,
    score: float = 0.5,
    strength: str = "IMPLEMENTATION_PRESENT",
) -> RepositoryEvidence:
    row = RepositoryEvidence(
        id=new_id(),
        profile_id=profile_id,
        owner="11vatedTech",
        name=name,
        full_name=f"11vatedTech/{name}",
        html_url=f"https://github.com/11vatedTech/{name}",
        description="test",
        topics=topics or [],
        languages=languages or ["Python"],
        source_present=source_present,
        tests_present=tests,
        ci_build_present=ci,
        empty_or_minimal=empty,
        evidence_strength=strength,
        evidence_value_score=score,
        last_scanned_at=datetime.now(UTC),
    )
    session.add(row)
    return row


async def test_authorized_profiles_are_persisted(session: AsyncSession) -> None:
    profiles = await ensure_authorized_profiles(session)
    await session.commit()

    logins = {p.login for p in profiles}
    assert logins == {"11vatedTech", "11vated"}
    assert all(p.authorization_state == "AUTHORIZED_READ_ONLY" for p in profiles)


async def test_clustering_groups_same_lineage(session: AsyncSession) -> None:
    profile = (await ensure_authorized_profiles(session))[0]
    await session.flush()
    _repo(session, profile.id, "my-app", languages=["TypeScript"], topics=["web"])
    _repo(session, profile.id, "my-app-v2", languages=["TypeScript"], topics=["web", "react"])
    _repo(session, profile.id, "game-engine", languages=["GDScript"], topics=["game"])
    await session.flush()

    families = await cluster_families_and_link(session)
    await session.commit()

    # my-app + my-app-v2 share a stem -> one family; game-engine -> another.
    assert len(families) == 2


async def test_proposals_are_proposed_never_confirmed(session: AsyncSession) -> None:
    profile = (await ensure_authorized_profiles(session))[0]
    await session.flush()
    _repo(
        session, profile.id, "web-app",
        languages=["TypeScript"], topics=["react", "frontend"],
        tests=True, ci=True, strength="TEST_EVIDENCE_PRESENT",
    )
    await session.flush()
    await cluster_families_and_link(session)

    proposals = await generate_capability_proposals(session)
    await session.commit()

    assert len(proposals) >= 1
    assert all(p.status == CapabilityStatus.PROPOSED for p in proposals)
    assert all(p.external_claimable is False for p in proposals)


async def test_empty_repos_generate_no_proposals(session: AsyncSession) -> None:
    profile = (await ensure_authorized_profiles(session))[0]
    await session.flush()
    _repo(
        session, profile.id, "empty-repo",
        source_present=False, empty=True, strength="EMPTY_OR_MINIMAL",
    )
    await session.flush()
    await cluster_families_and_link(session)

    before = await session.scalar(select(func.count(CapabilityCanon.id)))
    await generate_capability_proposals(session)
    await session.commit()
    after = await session.scalar(select(func.count(CapabilityCanon.id)))

    assert after == before  # no new capability from an empty repo


async def test_census_report_structure(session: AsyncSession) -> None:
    await ensure_authorized_profiles(session)
    profile = (await ensure_authorized_profiles(session))[0]
    await session.flush()
    _repo(session, profile.id, "web-app", languages=["TypeScript"], topics=["frontend"])
    await session.flush()
    await cluster_families_and_link(session)
    await generate_capability_proposals(session)

    report = await census_report(session)
    await session.commit()

    assert "profiles" in report
    assert report["outbound"] == "disabled"
    assert any(p["login"] == "11vatedTech" for p in report["profiles"])
    assert report["repositories_found"] >= 1


async def test_no_outbound_ever_created(session: AsyncSession) -> None:
    profile = (await ensure_authorized_profiles(session))[0]
    await session.flush()
    _repo(session, profile.id, "web-app", languages=["TypeScript"])
    await session.flush()
    await cluster_families_and_link(session)
    await generate_capability_proposals(session)
    await session.commit()

    assert await session.scalar(select(func.count(Outreach.id))) == 0


async def test_restart_persistence_of_families(session: AsyncSession) -> None:
    profile = (await ensure_authorized_profiles(session))[0]
    await session.flush()
    _repo(session, profile.id, "persist-app", languages=["Python"])
    await session.flush()
    await cluster_families_and_link(session)
    await session.commit()

    families = list((await session.execute(select(ProjectFamily))).scalars().all())
    assert len(families) == 1
    assert families[0].slug
