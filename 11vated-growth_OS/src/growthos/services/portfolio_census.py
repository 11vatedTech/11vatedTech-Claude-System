"""GitHub Portfolio Evidence Census service.

Enumerates public repositories under the founder-authorized profiles, runs a
lightweight first-pass evidence census, classifies evidence strength, scores
repositories for capability-evidence value, clusters them into project
families, detects overlap, selects repositories for deep analysis, and (only
then) generates cross-project Capability Proposals.

Hard rules:

- repository existence is not capability proof;
- README claims are not implementation proof;
- empty/minimal repositories never generate proposals;
- several repos describing the same system never multiply capability breadth;
- every generated capability stays PROPOSED (never auto-confirmed).
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

import growthos.domain.models  # noqa: F401  (register all tables)
from growthos.domain.enums import CapabilityStatus
from growthos.domain.models_capability import (
    CapabilityEvidenceRecord,
    GitHubProfileEvidenceSource,
    ProjectFamily,
    RepositoryEvidence,
)
from growthos.domain.models_scout import CapabilityCanon
from growthos.intelligence.github_portfolio import (
    AUTHORIZED_PROFILES,
    GitHubProfileClient,
    _strength_rank,
    classify_repository,
    cluster_families,
    family_overlap_note,
    score_repository,
    select_deep_analysis,
)
from growthos.shared.ids import new_id


async def ensure_authorized_profiles(session: AsyncSession) -> list[GitHubProfileEvidenceSource]:
    rows: list[GitHubProfileEvidenceSource] = []
    for login in AUTHORIZED_PROFILES:
        row = (
            await session.execute(
                select(GitHubProfileEvidenceSource).where(
                    GitHubProfileEvidenceSource.login == login
                )
            )
        ).scalar_one_or_none()
        if row is None:
            row = GitHubProfileEvidenceSource(
                id=new_id(),
                login=login,
                source_url=f"https://github.com/{login}",
                authorization_state="AUTHORIZED_READ_ONLY",
                visibility_state="UNSCANNED",
            )
            session.add(row)
            await session.flush()
        rows.append(row)
    await session.flush()
    return rows


async def run_profile_census(
    session: AsyncSession,
    profile: GitHubProfileEvidenceSource,
    *,
    client: GitHubProfileClient | None = None,
) -> dict[str, Any]:
    """Enumerate + census one authorized profile's public repositories."""
    client = client or GitHubProfileClient()
    account_kind, repos = await client.list_repos(profile.login)
    profile.last_scan_at = datetime.now(UTC)
    if client.rate_limited or not repos:
        # A rate-limited or empty listing is not a zero-census; preserve the
        # previously persisted counters so a transient limit never erases them.
        if client.rate_limited:
            profile.visibility_state = "RATE_LIMITED"
            profile.error = "GitHub API rate limit reached; prior census retained."
        else:
            profile.visibility_state = "NO_PUBLIC_REPOSITORIES"
        await session.flush()
        return {
            "login": profile.login,
            "account_kind": account_kind,
            "repositories_discovered": profile.repositories_discovered,
            "repositories_analyzed": profile.repositories_analyzed,
            "skipped": "rate_limited" if client.rate_limited else "no_public_repositories",
        }
    profile.repositories_discovered = len(repos)
    profile.error = None

    analyzed = 0
    repo_rows: list[RepositoryEvidence] = []
    for meta in repos:
        full_name = str(meta.get("full_name") or "")
        tree = await client.get_tree(full_name, meta.get("default_branch"))
        releases = await client.get_releases(full_name)
        classified = classify_repository(meta, tree, releases_present=releases)
        score, breakdown = score_repository(classified)

        existing = (
            await session.execute(
                select(RepositoryEvidence).where(RepositoryEvidence.full_name == full_name)
            )
        ).scalar_one_or_none()
        pushed = classified.get("pushed_at")
        if pushed:
            try:
                pushed_dt = datetime.fromisoformat(str(pushed).replace("Z", "+00:00"))
            except ValueError:
                pushed_dt = None
        else:
            pushed_dt = None

        fields = dict(
            owner=profile.login,
            name=classified["name"],
            html_url=classified["html_url"],
            description=classified["description"] or None,
            topics=classified["topics"],
            visibility=classified["visibility"],
            archived=classified["archived"],
            fork=classified["fork"],
            default_branch=classified["default_branch"],
            primary_language=classified["primary_language"],
            languages=classified["languages"],
            size_kb=classified["size_kb"],
            stargazers=classified["stargazers"],
            readme_present=classified["readme_present"],
            source_present=classified["source_present"],
            tests_present=classified["tests_present"],
            ci_build_present=classified["ci_build_present"],
            releases_present=classified["releases_present"],
            architecture_docs_present=classified["architecture_docs_present"],
            empty_or_minimal=classified["empty_or_minimal"],
            evidence_strength=classified["evidence_strength"],
            evidence_value_score=score,
            score_breakdown=breakdown,
            pushed_at=pushed_dt,
            last_scanned_at=datetime.now(UTC),
        )
        if existing is None:
            existing = RepositoryEvidence(
                id=new_id(),
                profile_id=profile.id,
                full_name=full_name,
                **fields,
            )
            session.add(existing)
        else:
            existing.profile_id = profile.id
            for key, value in fields.items():
                setattr(existing, key, value)
        repo_rows.append(existing)
        analyzed += 1

    profile.repositories_analyzed = analyzed
    if client.rate_limited:
        profile.visibility_state = "RATE_LIMITED"
    elif analyzed > 0:
        profile.visibility_state = "PUBLIC_VISIBLE"
    else:
        profile.visibility_state = "NO_PUBLIC_REPOSITORIES"
    await session.flush()
    return {
        "login": profile.login,
        "account_kind": account_kind,
        "repositories_discovered": len(repos),
        "repositories_analyzed": analyzed,
    }


async def cluster_families_and_link(session: AsyncSession) -> list[ProjectFamily]:
    """Cluster all census repositories into families and persist the grouping.

    Fully idempotent: existing families are cleared and re-derived from the
    current repository evidence (their member links are reset via SET NULL).
    """
    await session.execute(delete(ProjectFamily))
    repos = list((await session.execute(select(RepositoryEvidence))).scalars().all())
    payloads = [_repo_payload(r) for r in repos]
    families = cluster_families(payloads)

    family_rows: list[ProjectFamily] = []
    for stem, fam in families.items():
        members = fam["members"]
        member_rows = [
            (await session.execute(
                select(RepositoryEvidence).where(
                    RepositoryEvidence.full_name == m["full_name"]
                )
            )).scalar_one()
            for m in members
        ]
        best_strength = max(
            (_strength_rank(r.evidence_strength) for r in member_rows), default=-1
        )
        strength_label = (
            ["EMPTY_OR_MINIMAL", "DOCUMENTATION_ONLY", "EXPERIMENTAL",
             "IMPLEMENTATION_PRESENT", "TEST_EVIDENCE_PRESENT",
             "BUILD_EVIDENCE_PRESENT", "RUNTIME_EVIDENCE_PRESENT",
             "STRONG_CAPABILITY_EVIDENCE"][best_strength]
            if best_strength >= 0
            else "EMPTY_OR_MINIMAL"
        )
        slug = stem or f"family-{len(family_rows)}"
        row = (
            await session.execute(
                select(ProjectFamily).where(ProjectFamily.slug == slug)
            )
        ).scalar_one_or_none()
        if row is None:
            row = ProjectFamily(
                id=new_id(),
                slug=slug,
                name=_family_display_name(stem, member_rows),
                description=_family_description(member_rows),
                primary_languages=sorted(fam["languages"]),
                evidence_strength=strength_label,
                evidence_summary=_family_evidence_summary(member_rows),
                overlap_note=family_overlap_note(payloads_of(member_rows)),
                capability_candidates=[],
            )
            session.add(row)
            await session.flush()
        else:
            row.primary_languages = sorted(fam["languages"])
            row.evidence_strength = strength_label
            row.evidence_summary = _family_evidence_summary(member_rows)
            row.overlap_note = family_overlap_note(payloads_of(member_rows))
        for m in member_rows:
            m.family_id = row.id
        family_rows.append(row)
    await session.flush()
    return family_rows


def payloads_of(member_rows: list[RepositoryEvidence]) -> list[dict[str, Any]]:
    return [_repo_payload(m) for m in member_rows]


def _repo_payload(r: RepositoryEvidence) -> dict[str, Any]:
    return {
        "name": r.name,
        "full_name": r.full_name,
        "topics": r.topics,
        "languages": r.languages,
        "score": r.evidence_value_score,
    }


def _family_display_name(stem: str, members: list[RepositoryEvidence]) -> str:
    return str(members[0].name if len(members) == 1 else stem.replace("-", " ").title())


def _family_description(members: list[RepositoryEvidence]) -> str | None:
    descs = [m.description for m in members if m.description]
    return "; ".join(descs[:3])[:500] or None


def _family_evidence_summary(members: list[RepositoryEvidence]) -> str:
    strengths = [m.evidence_strength for m in members]
    return (
        f"{len(members)} repository(s); strengths: {', '.join(sorted(set(strengths)))}"
    )


# ---------------------------------------------------------------------------
# Cross-project capability proposals (never auto-confirmed)
# ---------------------------------------------------------------------------


def _candidates_for_family(
    family: ProjectFamily, members: list[RepositoryEvidence]
) -> list[dict[str, str]]:
    """Derive capability candidates from observed languages/topics/names only."""
    languages = {lang.lower() for lang in (family.primary_languages or [])}
    for m in members:
        languages |= {lang.lower() for lang in m.languages}
    topics = {t.lower() for m in members for t in m.topics}
    corpus = " ".join([family.name.lower(), family.slug.lower(),
                       *[m.name.lower() for m in members],
                       *[str(m.description or "").lower() for m in members],
                       *topics])
    # Token-set matching: short tokens ("ar", "3d", "ai") must be whole tokens,
    # never substrings of unrelated words like "architecture".
    tokens = set(re.findall(r"[a-z0-9]+", corpus))

    candidates: list[dict[str, str]] = []

    def add(name: str, definition: str, reason: str) -> None:
        candidates.append({"name": name, "definition": definition, "reason": reason})

    def has(*terms: str) -> bool:
        return any(t in tokens for t in terms)

    is_frontend = bool({"typescript", "javascript", "vue", "svelte", "react"} & languages) or has(
        "frontend", "react", "web", "ui", "vite", "typescript", "javascript"
    )
    is_ai = has("agent", "agents", "llm", "ollama", "langchain", "ai", "brain", "automation")
    is_game = bool({"gdscript", "c#", "c++", "lua", "csharp"} & languages) or has(
        "game", "sprite", "sprites", "2d", "3d", "engine", "playable"
    )
    is_data = has("scrape", "extract", "parse", "data", "ingest", "pipeline")
    is_spatial = has("spatial", "vr", "ar", "vision", "3d", "metaverse")
    is_tooling = has("tool", "cli", "sdk", "compiler", "generator", "dev")

    # Only propose where there is real implementation evidence (not empty repos).
    has_implementation = any(m.source_present for m in members)
    if not has_implementation:
        return candidates

    if is_game:
        add(
            "Interactive Game & Sprite Systems Prototyping",
            "Prototype interactive 2D/3D game and sprite runtime systems where project evidence demonstrates implementation, tests, and build/runtime behavior.",
            "Game/sprite-oriented source, languages, and/or documentation evidence observed across the family.",
        )
    if is_frontend:
        add(
            "Interactive Frontend Development",
            "Build responsive interactive web interfaces and experiences from cross-project implementation evidence.",
            "TypeScript/JavaScript/frontend source and build evidence observed across the family.",
        )
    if is_ai:
        add(
            "Local AI & Autonomous Agent Systems",
            "Design local-first AI-assisted and autonomous-agent software workflows within verified runtime constraints.",
            "Agent/AI/automation source and documentation evidence observed across the family.",
        )
    if is_data:
        add(
            "Data Extraction & Processing Systems",
            "Build bounded data extraction, parsing, and processing pipelines from demonstrated implementation evidence.",
            "Data/extraction/pipeline source evidence observed across the family.",
        )
    if is_spatial:
        add(
            "Spatial Computing & Interactive 3D Prototyping",
            "Prototype spatial/interactive 3D experiences where implementation evidence supports it.",
            "Spatial/3D source evidence observed across the family.",
        )
    if is_tooling and not (is_frontend or is_game or is_ai):
        add(
            "Developer Tooling & Code Generation",
            "Build developer tooling, CLIs, and code-generation utilities from demonstrated implementation evidence.",
            "Tooling/CLI/code-generation source evidence observed across the family.",
        )
    return candidates


async def _candidate_capability_name(
    session: AsyncSession, base_name: str
) -> str:
    """Resolve a distinct capability name for a candidate.

    A name already held by a REJECTED or founder-confirmed capability belongs
    to that specific evidence chain; the portfolio census must not silently
    resurrect it or fold new evidence into it. Census-derived PROPOSED rows are
    reused for idempotency.
    """
    existing = (
        await session.execute(
            select(CapabilityCanon).where(CapabilityCanon.name == base_name)
        )
    ).scalar_one_or_none()
    if existing is None:
        return base_name
    status = getattr(existing.status, "value", str(existing.status))
    if existing.entered_from == "github_portfolio_census" and status == "PROPOSED":
        return base_name
    if status in {"REJECTED", "FOUNDER_CONFIRMED", "EVIDENCE_VERIFIED"}:
        return f"{base_name} (Portfolio Evidence)"
    return base_name


async def generate_capability_proposals(session: AsyncSession) -> list[CapabilityCanon]:
    """Generate cross-project Capability Proposals (all PROPOSED, none confirmed).

    Idempotent: previously census-derived proposals are cleared and re-derived.
    """
    await session.execute(
        delete(CapabilityCanon).where(CapabilityCanon.entered_from == "github_portfolio_census")
    )
    families = list((await session.execute(select(ProjectFamily))).scalars().all())
    by_name: dict[str, dict[str, Any]] = {}
    for family in families:
        members = list(
            (await session.execute(
                select(RepositoryEvidence).where(RepositoryEvidence.family_id == family.id)
            )).scalars().all()
        )
        members = [m for m in members if not m.empty_or_minimal]
        if not members:
            continue
        for cand in _candidates_for_family(family, members):
            name = cand["name"]
            entry = by_name.setdefault(name, {"reason": cand["reason"], "definition": cand["definition"], "repos": [], "families": []})
            entry["repos"].extend(m.full_name for m in members)
            entry["families"].append(family.slug)

    created: list[CapabilityCanon] = []
    for name, data in by_name.items():
        repos = sorted(set(data["repos"]))
        final_name = await _candidate_capability_name(session, name)
        existing = (
            await session.execute(
                select(CapabilityCanon).where(CapabilityCanon.name == final_name)
            )
        ).scalar_one_or_none()
        if existing is None:
            capability = CapabilityCanon(
                id=new_id(),
                name=final_name,
                definition=data["definition"],
                category="cross_project",
                status=CapabilityStatus.PROPOSED,
                external_claimable=False,
                entered_from="github_portfolio_census",
                maturity="EXPERIMENTAL",
                proof_evidence=[
                    {
                        "repositories": repos,
                        "reason": data["reason"],
                        "status": "PROPOSED",
                    }
                ],
                related_completed_work=repos,
                limitations=[
                    "Cross-project census evidence only; no deep analysis yet",
                    "No founder confirmation",
                    "No independent customer delivery evidence",
                ],
            )
            session.add(capability)
            await session.flush()
        else:
            capability = existing
        for repo_full in repos:
            repo = (
                await session.execute(
                    select(RepositoryEvidence).where(RepositoryEvidence.full_name == repo_full)
                )
            ).scalar_one_or_none()
            evidence = CapabilityEvidenceRecord(
                id=new_id(),
                capability_id=capability.id,
                project_id=None,
                source_type="github_repository_census",
                source_location=repo.html_url if repo else repo_full,
                artifact=repo.name if repo else repo_full,
                category=repo.evidence_strength if repo else "IMPLEMENTATION_PRESENT",
                summary=data["reason"],
                confidence=0.5,
                sensitivity="INTERNAL",
                verified_at=datetime.now(UTC),
                private=True,
            )
            session.add(evidence)
        created.append(capability)
    await session.flush()
    return created


# ---------------------------------------------------------------------------
# Census report
# ---------------------------------------------------------------------------


async def census_report(session: AsyncSession) -> dict[str, Any]:
    profiles = list((await session.execute(select(GitHubProfileEvidenceSource))).scalars().all())
    repos = list((await session.execute(select(RepositoryEvidence))).scalars().all())
    families = list((await session.execute(select(ProjectFamily))).scalars().all())
    capabilities = (
        await session.execute(
            select(CapabilityCanon).where(
                CapabilityCanon.entered_from == "github_portfolio_census"
            )
        )
    ).scalars().all()

    def profile_block(p: GitHubProfileEvidenceSource) -> dict[str, Any]:
        prs = [r for r in repos if r.profile_id == p.id]
        evidence_rich = sum(1 for r in prs if r.evidence_value_score >= 0.4 and not r.empty_or_minimal)
        minimal = sum(1 for r in prs if r.empty_or_minimal)
        # Persisted repository evidence is authoritative over live-listing counters
        # (which can be transiently zeroed by a rate limit).
        found = len(prs)
        return {
            "login": p.login,
            "authorization_state": p.authorization_state,
            "visibility_state": p.visibility_state,
            "repositories_found": found,
            "repositories_analyzed": found,
            "evidence_rich": evidence_rich,
            "minimal_or_empty": minimal,
            "deep_analysis_selected": [r.name for r in prs if r.full_name in _deep_selection(session, repos, families)],
        }

    ranked = sorted(repos, key=lambda r: -r.evidence_value_score)
    deep = _deep_selection(session, repos, families)
    deep_repos = [r for r in repos if r.full_name in deep]

    return {
        "profiles": [profile_block(p) for p in profiles],
        "repositories_found": len(repos),
        "evidence_rich": sum(1 for r in repos if r.evidence_value_score >= 0.4 and not r.empty_or_minimal),
        "minimal_or_empty": sum(1 for r in repos if r.empty_or_minimal),
        "top_repositories": [
            {"name": r.name, "full_name": r.full_name, "score": r.evidence_value_score, "strength": r.evidence_strength, "languages": r.languages}
            for r in ranked[:10]
        ],
        "project_families": [
            {
                "slug": f.slug,
                "name": f.name,
                "repositories": [r.name for r in repos if r.family_id == f.id],
                "evidence_strength": f.evidence_strength,
                "overlap_note": f.overlap_note,
            }
            for f in families
        ],
        "deep_analysis_selected": [
            {"name": r.name, "full_name": r.full_name, "reason": _deep_reason(r)}
            for r in deep_repos
        ],
        "capability_candidates": [
            {
                "name": c.name,
                "supporting_repositories": c.related_completed_work,
                "status": str(c.status),
            }
            for c in capabilities
        ],
        "outbound": "disabled",
    }


def _deep_selection(
    session: AsyncSession,
    repos: list[RepositoryEvidence],
    families: list[ProjectFamily],
) -> set[str]:
    del session
    payloads = [_repo_payload(r) for r in repos]
    fams = cluster_families(payloads)
    return set(select_deep_analysis(payloads, fams, max_count=8))


def _deep_reason(r: RepositoryEvidence) -> str:
    return (
        f"{r.evidence_strength}; score {r.evidence_value_score}; "
        f"languages {', '.join(r.languages) or r.primary_language or 'unknown'}"
    )


async def run_full_census(session: AsyncSession) -> dict[str, Any]:
    """Enumerate + census both authorized profiles, cluster, and propose."""
    profiles = await ensure_authorized_profiles(session)
    client = GitHubProfileClient()
    per_profile: list[dict[str, Any]] = []
    for profile in profiles:
        per_profile.append(await run_profile_census(session, profile, client=client))
    families = await cluster_families_and_link(session)
    proposals = await generate_capability_proposals(session)
    report = await census_report(session)
    report["per_profile"] = per_profile
    report["families_created"] = len(families)
    report["proposals_generated"] = [p.name for p in proposals]
    await session.flush()
    return report
