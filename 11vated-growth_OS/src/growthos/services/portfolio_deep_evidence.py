"""Portfolio Deep Evidence service.

Runs deep evidence analysis on the selected repositories, persists findings
as CapabilityEvidenceRecord rows, reassesses the four existing portfolio
capability proposals, and produces a founder-ready review report.

No capability is auto-confirmed. All new proposals remain PROPOSED.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import growthos.domain.models  # noqa: F401
from growthos.domain.enums import CapabilityStatus
from growthos.domain.models_capability import (
    CapabilityEvidenceRecord,
    RepositoryEvidence,
)
from growthos.domain.models_scout import CapabilityCanon
from growthos.intelligence.deep_evidence import (
    EvidenceClass,
    run_portfolio_deep_evidence,
)
from growthos.intelligence.github_portfolio import (
    GitHubProfileClient,
)
from growthos.shared.ids import new_id

# ---------------------------------------------------------------------------
# Persistence: store deep evidence findings
# ---------------------------------------------------------------------------


async def _persist_deep_evidence(
    session: AsyncSession,
    results: list[dict[str, Any]],
    *,
    capability_id: str | None = None,
) -> int:
    """Persist deep evidence findings as CapabilityEvidenceRecord rows.

    Returns the number of evidence records created.
    """
    count = 0
    for result in results:
        synthesis = result.get("synthesis", {})
        if not synthesis and not result.get("from_prior_run"):
            continue
        if result.get("from_prior_run"):
            continue  # don't re-persist prior-run results

        files_analyzed = result.get("files_analyzed", 0)
        impl_files = synthesis.get("implementation_files", 0)
        test_files = synthesis.get("test_files", 0)

        # Determine deep review status
        if result.get("budget_exhausted"):
            deep_status = "DEEP_REVIEW_RATE_LIMITED"
        elif result.get("error"):
            deep_status = "DEEP_REVIEW_BLOCKED"
        elif files_analyzed <= 1:
            deep_status = "DEEP_REVIEW_INSUFFICIENT"
        elif files_analyzed < 5:
            deep_status = "DEEP_REVIEW_PARTIAL"
        else:
            deep_status = "DEEP_REVIEW_COMPLETE"

        # Coverage limitations
        limitations: list[str] = []
        if test_files == 0:
            limitations.append("No test files inspected")
        if impl_files == 0:
            limitations.append("No implementation files confirmed")
        if result.get("budget_exhausted"):
            limitations.append("Rate limit interrupted analysis")

        # Evidence quality markers
        test_quality = None
        if test_files > 0:
            test_quality = "TESTS_DISCOVERED"
        build_quality = None
        if synthesis.get("evidence_classes") and "BUILD_EVIDENCE" in synthesis["evidence_classes"]:
            build_quality = "BUILD_CONFIG_PRESENT"
        runtime_quality = "STATIC_ONLY"  # we don't execute remote code

        evidence = CapabilityEvidenceRecord(
            id=new_id(),
            capability_id=capability_id or "",
            project_id=None,
            source_type="github_deep_evidence",
            source_location=result.get("full_name", ""),
            artifact=result.get("name", ""),
            category=_dominant_evidence_class(synthesis.get("evidence_classes", [])),
            summary=_evidence_summary(result, synthesis),
            confidence=_deep_confidence(synthesis),
            sensitivity="INTERNAL",
            verified_at=datetime.now(UTC),
            private=True,
            # Provenance
            branch=None,  # will be set by caller if available
            commit_sha=None,
            evidence_source="github",
            # Sufficiency
            files_discovered=files_analyzed,
            files_inspected=files_analyzed,
            source_files_inspected=impl_files,
            test_files_inspected=test_files,
            build_files_inspected=0,
            docs_inspected=1 if result.get("readme_analysis") else 0,
            deep_review_status=deep_status,
            coverage_limitations=limitations,
            # Quality
            test_quality=test_quality,
            build_quality=build_quality,
            runtime_quality=runtime_quality,
            # Semantic details
            implementation_details={
                "architecture_signals": synthesis.get("architecture_signals", []),
                "unique_modules": synthesis.get("unique_modules", []),
                "contradictions": synthesis.get("contradictions", []),
                "maturity_assessment": synthesis.get("maturity_assessment"),
                "reproducibility": synthesis.get("reproducibility"),
                "confidence_dimensions": synthesis.get("confidence_dimensions", {}),
            },
        )
        session.add(evidence)
        count += 1

    await session.flush()
    return count


def _dominant_evidence_class(classes: list[str]) -> str:
    """Determine the dominant evidence class from a list."""
    priority = [
        EvidenceClass.DIRECT_IMPLEMENTATION,
        EvidenceClass.TEST_EVIDENCE,
        EvidenceClass.BUILD_EVIDENCE,
        EvidenceClass.RUNTIME_EVIDENCE,
        EvidenceClass.ARCHITECTURE_EVIDENCE,
        EvidenceClass.EXPERIMENTAL_EVIDENCE,
        EvidenceClass.DOCUMENTED_CLAIM,
    ]
    for cls in priority:
        if cls in classes:
            return cls
    return EvidenceClass.MISSING_EVIDENCE


def _evidence_summary(result: dict[str, Any], synthesis: dict[str, Any]) -> str:
    """Build a concise evidence summary for persistence."""
    parts = []
    parts.append(f"Files analyzed: {synthesis.get('files_analyzed', 0)}")
    parts.append(f"Implementation files: {synthesis.get('implementation_files', 0)}")
    parts.append(f"Test files: {synthesis.get('test_files', 0)}")
    parts.append(f"Maturity: {synthesis.get('maturity_assessment', 'UNKNOWN')}")
    parts.append(f"Reproducibility: {synthesis.get('reproducibility', 'UNKNOWN')}")

    arch = synthesis.get("architecture_signals", [])
    if arch:
        parts.append(f"Architecture: {', '.join(arch[:5])}")

    contradictions = synthesis.get("contradictions", [])
    if contradictions:
        parts.append(f"Contradictions: {len(contradictions)}")

    return "; ".join(parts)


def _deep_confidence(synthesis: dict[str, Any]) -> float:
    """Compute overall confidence from deep evidence synthesis."""
    dims = synthesis.get("confidence_dimensions", {})
    impl = dims.get("implementation", 0.0)
    test = dims.get("testing", 0.0)
    build = dims.get("build", 0.0)
    runtime = dims.get("runtime", 0.0)
    repro = dims.get("reproducibility", 0.0)
    return round(0.30 * impl + 0.25 * test + 0.15 * build + 0.15 * runtime + 0.15 * repro, 3)


# ---------------------------------------------------------------------------
# Proposal reassessment
# ---------------------------------------------------------------------------

# The four census proposals we need to reassess
_CENSUS_PROPOSALS = [
    "Interactive Frontend Development (Portfolio Evidence)",
    "Interactive Game & Sprite Systems Prototyping",
    "Local AI & Autonomous Agent Systems",
    "Spatial Computing & Interactive 3D Prototyping",
]


def _reassess_frontend(
    deep_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reassess the Frontend Portfolio Evidence proposal after deep analysis."""
    evidence_support: list[str] = []
    evidence_weakness: list[str] = []

    for r in deep_results:
        synth = r.get("synthesis", {})
        arch = synth.get("architecture_signals", [])
        impl_files = synth.get("implementation_files", 0)

        # Check for frontend-specific evidence
        has_frontend_arch = any(
            s in ("API surface", "routing layer", "middleware")
            for s in arch
        )
        if has_frontend_arch and impl_files >= 2:
            evidence_support.append(f"{r['name']}: {impl_files} implementation files, frontend architecture detected")
        elif impl_files >= 3:
            evidence_support.append(f"{r['name']}: {impl_files} implementation files (general, not frontend-specific)")
        if impl_files < 2 and synth.get("total_roadmap_signals", 0) > 3:
            evidence_weakness.append(f"{r['name']}: mostly roadmap claims ({synth.get('total_roadmap_signals', 0)} signals)")

    support_strength = len(evidence_support)
    weakness_count = len(evidence_weakness)

    if support_strength >= 3 and weakness_count <= 1:
        decision = "KEEP"
        rename = None
        reason = f"Cross-project evidence supports frontend capability ({support_strength} projects with implementation evidence)"
    elif support_strength >= 2:
        decision = "NARROW"
        rename = "Interactive Frontend Prototyping"
        reason = f"Some frontend evidence exists ({support_strength} projects) but not strong enough for general frontend development"
    else:
        decision = "REJECT"
        rename = None
        reason = f"Weak cross-project frontend evidence ({support_strength} supporting, {weakness_count} contradictory)"

    return {
        "proposal": "Interactive Frontend Development (Portfolio Evidence)",
        "decision": decision,
        "recommended_name": rename,
        "reason": reason,
        "evidence_support": evidence_support,
        "evidence_weakness": evidence_weakness,
    }


def _reassess_game_sprite(
    deep_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reassess the Game & Sprite Systems proposal."""
    evidence_support: list[str] = []
    evidence_weakness: list[str] = []

    for r in deep_results:
        synth = r.get("synthesis", {})
        modules = synth.get("unique_modules", [])
        impl_files = synth.get("implementation_files", 0)

        has_sprite_evidence = any(
            m for m in modules
            if any(kw in m.lower() for kw in ["sprite", "character", "animation", "game", "scene", "render"])
        )
        if has_sprite_evidence and impl_files >= 2:
            evidence_support.append(f"{r['name']}: {impl_files} impl files, sprite/game modules found")
        elif impl_files >= 3:
            evidence_support.append(f"{r['name']}: {impl_files} impl files (general)")
        if impl_files < 2:
            evidence_weakness.append(f"{r['name']}: minimal implementation evidence")

    # GSPL-Sprites already has a confirmed capability — check overlap
    has_sprite_overlap = any(
        "sprite" in r.get("name", "").lower()
        for r in deep_results
    )

    support_strength = len(evidence_support)
    if support_strength >= 2 and not has_sprite_overlap:
        decision = "KEEP"
        rename = "Interactive Game Systems Prototyping"
        reason = "Cross-project evidence supports game systems capability beyond sprite runtime"
    elif has_sprite_overlap:
        decision = "NARROW"
        rename = None
        reason = "Overlaps with existing confirmed sprite capability; narrow to complementary game-systems aspects only"
    else:
        decision = "REQUEST_MORE_EVIDENCE"
        rename = None
        reason = f"Limited cross-project game evidence ({support_strength} supporting projects)"

    return {
        "proposal": "Interactive Game & Sprite Systems Prototyping",
        "decision": decision,
        "recommended_name": rename,
        "reason": reason,
        "evidence_support": evidence_support,
        "evidence_weakness": evidence_weakness,
    }


def _reassess_local_ai(
    deep_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reassess the Local AI & Autonomous Agent Systems proposal."""
    evidence_support: list[str] = []
    evidence_weakness: list[str] = []

    # Broader AI/agent keyword set — covers class names like AgentLoop,
    # OllamaClient, ToolExecutor, Planner, etc.
    _AI_KEYWORDS = [
        "agent", "llm", "ai", "model", "brain", "ollama", "chat",
        "planner", "executor", "tool", "memory", "permission",
        "diff", "routing", "conversation", "hook", "watcher",
        "prompt", "inference", "completion", "embed", "tokenize",
    ]

    for r in deep_results:
        synth = r.get("synthesis", {})
        modules = synth.get("unique_modules", [])
        arch = synth.get("architecture_signals", [])
        impl_files = synth.get("implementation_files", 0)

        has_ai_modules = any(
            m for m in modules
            if any(kw in m.lower() for kw in _AI_KEYWORDS)
        )
        has_agent_arch = any(
            s in arch for s in [
                "plugin system", "hook system", "event system",
                "adapter pattern", "API surface", "authentication",
            ]
        )
        # Strong signal: AI-specific modules + implementation depth
        if has_ai_modules and impl_files >= 2:
            evidence_support.append(f"{r['name']}: {impl_files} impl files, AI/agent modules detected: {[m for m in modules if any(kw in m.lower() for kw in _AI_KEYWORDS)][:5]}")
        # Corroborating signal: substantial implementation + agent-like architecture
        elif has_agent_arch and impl_files >= 4:
            evidence_support.append(f"{r['name']}: {impl_files} impl files, agent-like architecture ({', '.join(arch[:3])})")
        if impl_files < 2:
            evidence_weakness.append(f"{r['name']}: insufficient implementation depth ({impl_files} files)")

    support_strength = len(evidence_support)
    if support_strength >= 3:
        decision = "KEEP"
        rename = "Local AI Agent System Development"
        reason = f"Strong cross-project evidence for local AI/agent systems ({support_strength} projects)"
    elif support_strength >= 2:
        decision = "NARROW"
        rename = "Local AI Integration"
        reason = f"Some AI evidence ({support_strength} projects) but narrower than full agent systems"
    else:
        decision = "REQUEST_MORE_EVIDENCE"
        rename = None
        reason = f"Insufficient cross-project AI evidence ({support_strength} supporting projects)"

    return {
        "proposal": "Local AI & Autonomous Agent Systems",
        "decision": decision,
        "recommended_name": rename,
        "reason": reason,
        "evidence_support": evidence_support,
        "evidence_weakness": evidence_weakness,
    }


def _reassess_spatial(
    deep_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reassess the Spatial Computing & Interactive 3D Prototyping proposal."""
    evidence_support: list[str] = []
    evidence_weakness: list[str] = []

    for r in deep_results:
        synth = r.get("synthesis", {})
        modules = synth.get("unique_modules", [])
        arch = synth.get("architecture_signals", [])
        impl_files = synth.get("implementation_files", 0)

        has_spatial_evidence = any(
            m for m in modules
            if any(kw in m.lower() for kw in ["vr", "ar", "spatial", "3d", "render", "canvas", "webgl", "xr"])
        )
        has_multi_device = any(
            s in arch for s in ["WebSocket", "API surface", "adapter pattern"]
        )
        if (has_spatial_evidence or has_multi_device) and impl_files >= 2:
            evidence_support.append(f"{r['name']}: {impl_files} impl files, spatial/multi-device evidence")
        elif impl_files >= 3:
            evidence_support.append(f"{r['name']}: {impl_files} impl files (general)")
        if impl_files < 2:
            evidence_weakness.append(f"{r['name']}: minimal implementation evidence for spatial capability")

    support_strength = len(evidence_support)
    if support_strength >= 2:
        decision = "KEEP"
        rename = "Headless Spatial Interaction Prototyping"
        reason = f"Cross-project evidence supports spatial/multi-device prototyping ({support_strength} projects)"
    elif support_strength == 1:
        decision = "NARROW"
        rename = "Multi-Device Interactive Experience Prototyping"
        reason = "Limited spatial evidence; narrow to multi-device interaction"
    else:
        decision = "REQUEST_MORE_EVIDENCE"
        rename = None
        reason = f"Insufficient cross-project spatial evidence ({support_strength} supporting projects)"

    return {
        "proposal": "Spatial Computing & Interactive 3D Prototyping",
        "decision": decision,
        "recommended_name": rename,
        "reason": reason,
        "evidence_support": evidence_support,
        "evidence_weakness": evidence_weakness,
    }


# ---------------------------------------------------------------------------
# New capability discovery from deep evidence
# ---------------------------------------------------------------------------


def _discover_new_capabilities(
    deep_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Discover new capability candidates from deep evidence that the census missed."""
    new_caps: list[dict[str, Any]] = []

    # Collect all architecture signals across repos
    all_arch: dict[str, list[str]] = {}
    all_modules: dict[str, list[str]] = {}
    for r in deep_results:
        name = r.get("name", "unknown")
        synth = r.get("synthesis", {})
        for arch in synth.get("architecture_signals", []):
            all_arch.setdefault(arch, []).append(name)
        for mod in synth.get("unique_modules", []):
            all_modules.setdefault(mod, []).append(name)

    # Data extraction / pipeline capability
    # Find repos whose modules contain data/pipeline-related keywords
    data_repos = []
    for r in deep_results:
        rname = r.get("name", "unknown")
        mods = r.get("synthesis", {}).get("unique_modules", [])
        if any(
            any(kw in mod.lower() for kw in ["scrape", "extract", "parse", "pipeline", "ingest", "data"])
            for mod in mods
        ):
            data_repos.append(rname)
    pipeline_arch = [
        r.get("name", "unknown")
        for r in deep_results
        if "pipeline architecture" in r.get("synthesis", {}).get("architecture_signals", [])
    ]
    all_data_repos = list(dict.fromkeys(data_repos + pipeline_arch))  # dedupe preserving order
    if len(all_data_repos) >= 2 or (pipeline_arch and len(pipeline_arch) >= 1):
        new_caps.append({
            "name": "Data Extraction & Processing Systems",
            "definition": "Build bounded data extraction, parsing, and processing pipelines from demonstrated implementation evidence.",
            "supporting_projects": all_data_repos[:5],
            "confidence": 0.4,
            "reason": "Pipeline/data architecture and modules detected across multiple projects",
        })

    # Business automation capability
    biz_repos = [
        r.get("name", "") for r in deep_results
        if r.get("synthesis", {}).get("has_api_surface")
        and r.get("synthesis", {}).get("has_database")
    ]
    if len(biz_repos) >= 2:
        new_caps.append({
            "name": "Business Automation & Workflow Systems",
            "definition": "Design and implement automated business workflows with API surfaces, database persistence, and job scheduling.",
            "supporting_projects": biz_repos[:5],
            "confidence": 0.35,
            "reason": "Multiple projects with API + database + scheduling evidence",
        })

    # Developer tooling capability
    # Find repos whose modules contain tooling-related keywords
    tool_repos = []
    for r in deep_results:
        rname = r.get("name", "unknown")
        mods = r.get("synthesis", {}).get("unique_modules", [])
        if any(
            any(kw in mod.lower() for kw in ["cli", "tool", "sdk", "compiler", "generator", "devtool"])
            for mod in mods
        ):
            tool_repos.append(rname)
    all_tool_repos = list(dict.fromkeys(tool_repos))  # dedupe
    if len(all_tool_repos) >= 2:
        new_caps.append({
            "name": "Developer Tooling & Code Generation",
            "definition": "Build developer tooling, CLIs, and code-generation utilities from demonstrated implementation evidence.",
            "supporting_projects": all_tool_repos[:5],
            "confidence": 0.3,
            "reason": "Developer tooling modules detected across projects",
        })

    # Asset/media pipeline capability
    asset_repos = [
        r.get("name", "") for r in deep_results
        if any(
            kw in " ".join(r.get("synthesis", {}).get("unique_modules", [])).lower()
            for kw in ["asset", "sprite", "tensor", "graph", "media", "forge", "pipeline"]
        )
    ]
    if len(asset_repos) >= 2:
        new_caps.append({
            "name": "Asset Intelligence & Media Pipeline Systems",
            "definition": "Build deterministic asset processing, graph-based pipelines, and media intelligence systems from demonstrated implementation.",
            "supporting_projects": asset_repos[:5],
            "confidence": 0.35,
            "reason": "Asset/media/pipeline modules detected across projects",
        })

    return new_caps


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------


async def run_portfolio_deep_evidence_pass(
    session: AsyncSession,
    *,
    client: GitHubProfileClient | None = None,
) -> dict[str, Any]:
    """Run the full portfolio deep evidence pipeline.

    1. Run deep analysis on 8 selected repos
    2. Persist evidence findings
    3. Reassess the 4 existing census proposals
    4. Discover new capabilities from deep evidence
    5. Generate/update proposals (all PROPOSED, never confirmed)
    6. Produce founder review report
    """
    # Step 1: Deep analysis
    deep = await run_portfolio_deep_evidence(session, client=client, limit=8)
    deep_results = deep.get("results", [])

    # Step 2: Persist deep evidence (link to existing confirmed sprite capability for reference)
    confirmed = (
        await session.execute(
            select(CapabilityCanon).where(
                CapabilityCanon.status == CapabilityStatus.FOUNDER_CONFIRMED
            )
        )
    ).scalars().first()
    evidence_count = await _persist_deep_evidence(
        session, deep_results,
        capability_id=confirmed.id if confirmed else None,
    )

    # Step 3: Reassess the 4 census proposals
    reassessments = [
        _reassess_frontend(deep_results),
        _reassess_game_sprite(deep_results),
        _reassess_local_ai(deep_results),
        _reassess_spatial(deep_results),
    ]

    # Step 4: Discover new capabilities
    new_caps = _discover_new_capabilities(deep_results)

    # Step 5: Update/create proposals based on reassessment
    proposal_actions: list[dict[str, Any]] = []
    for reassess in reassessments:
        proposal_name = reassess["proposal"]
        decision = reassess["decision"]

        # Find existing proposal (by original name or any recommended_name)
        existing = (
            await session.execute(
                select(CapabilityCanon).where(CapabilityCanon.name == proposal_name)
            )
        ).scalar_one_or_none()

        # Also check by recommended_name if set (may have been created by a prior run)
        if existing is None and reassess.get("recommended_name"):
            existing = (
                await session.execute(
                    select(CapabilityCanon).where(
                        CapabilityCanon.name == reassess["recommended_name"]
                    )
                )
            ).scalar_one_or_none()

        if existing is None:
            # Create fresh proposal
            final_name = reassess.get("recommended_name") or proposal_name
            existing = CapabilityCanon(
                id=new_id(),
                name=final_name,
                definition=f"Deep evidence reassessment of {proposal_name}",
                category="deep_evidence",
                status=CapabilityStatus.PROPOSED,
                external_claimable=False,
                entered_from="portfolio_deep_evidence",
                maturity="EXPERIMENTAL",
                proof_evidence=[{
                    "reassessment": reassess,
                    "status": "PROPOSED",
                }],
                related_completed_work=[r.get("full_name", "") for r in deep_results],
                limitations=["Awaiting founder review after deep evidence pass"],
            )
            session.add(existing)
            await session.flush()

        # Machine recommendation (never overwrites founder decisions)
        # Only modify status for PROPOSED capabilities; leave FOUNDER_CONFIRMED untouched.
        is_founder_controlled = existing.status in (
            CapabilityStatus.FOUNDER_CONFIRMED,
            CapabilityStatus.REJECTED,  # only founder may reject
        )

        # Set machine recommendation fields
        existing.recommended_decision = decision
        existing.recommendation_reason = reassess["reason"]
        existing.recommendation_confidence = 0.5  # baseline; overridden per-type below

        if decision == "REJECT" and not is_founder_controlled:
            # Machine recommends withholding — do NOT set status=REJECTED
            existing.status = CapabilityStatus.WITHHELD_BY_CRITIC
            existing.recommendation_confidence = 0.6
        elif decision == "NARROW" and not is_founder_controlled:
            new_name = reassess.get("recommended_name")
            if new_name and new_name != existing.name:
                conflict = (
                    await session.execute(
                        select(CapabilityCanon).where(
                            CapabilityCanon.name == new_name,
                            CapabilityCanon.id != existing.id,
                        )
                    )
                ).scalar_one_or_none()
                if conflict:
                    existing.status = CapabilityStatus.SUPERSEDED
                    existing.recommendation_reason = (
                        f"Superseded: target '{new_name}' already exists. {reassess['reason']}"
                    )
                else:
                    # Record the intended rename in recommendation; don't change name yet
                    existing.recommendation_reason = (
                        f"NARROW to '{new_name}': {reassess['reason']}"
                    )
            existing.recommendation_confidence = 0.5
        elif decision == "REQUEST_MORE_EVIDENCE":
            existing.status = CapabilityStatus.INSUFFICIENT_EVIDENCE
            existing.recommendation_confidence = 0.4
        elif decision == "KEEP":
            existing.recommendation_confidence = 0.7

        # Evidence summary for founder review
        existing.evidence_summary_for_review = {
            "reassessment": reassess,
            "deep_evidence_summary": {
                "files_analyzed": sum(r.get("synthesis", {}).get("files_analyzed", 0) for r in deep_results),
                "implementation_files": sum(r.get("synthesis", {}).get("implementation_files", 0) for r in deep_results),
                "repos_analyzed": len(deep_results),
            },
            "machine_decision": decision,
            "machine_confidence": existing.recommendation_confidence,
        }

        # Deep review completeness per supporting repo
        existing.deep_review_completeness = {
            r.get("name", "unknown"): (
                "DEEP_REVIEW_COMPLETE" if r.get("synthesis", {}).get("files_analyzed", 0) >= 5
                else "DEEP_REVIEW_PARTIAL" if r.get("synthesis", {}).get("files_analyzed", 0) > 1
                else "DEEP_REVIEW_INSUFFICIENT"
            )
            for r in deep_results
        }

        proposal_actions.append({
            "proposal": proposal_name,
            "action": decision,
            "final_name": existing.name,
            "reason": reassess["reason"],
        })

    # Create new capability proposals from deep evidence
    for cap_data in new_caps:
        final_name = await _resolve_capability_name(session, cap_data["name"])
        existing = (
            await session.execute(
                select(CapabilityCanon).where(CapabilityCanon.name == final_name)
            )
        ).scalar_one_or_none()

        if existing is None:
            new_cap = CapabilityCanon(
                id=new_id(),
                name=final_name,
                definition=cap_data["definition"],
                category="deep_evidence",
                status=CapabilityStatus.PROPOSED,
                external_claimable=False,
                entered_from="portfolio_deep_evidence",
                maturity="EXPERIMENTAL",
                proof_evidence=[{
                    "supporting_projects": cap_data["supporting_projects"],
                    "reason": cap_data["reason"],
                    "status": "PROPOSED",
                }],
                related_completed_work=cap_data["supporting_projects"],
                limitations=[
                    "New capability from deep evidence; no founder confirmation",
                    "Confidence below 0.5; needs stronger evidence",
                    "No independent customer delivery evidence",
                ],
            )
            session.add(new_cap)
            await session.flush()

            # Create evidence records
            for repo_name in cap_data["supporting_projects"]:
                repo = (
                    await session.execute(
                        select(RepositoryEvidence).where(RepositoryEvidence.name == repo_name)
                    )
                ).scalar_one_or_none()
                if repo:
                    evidence = CapabilityEvidenceRecord(
                        id=new_id(),
                        capability_id=new_cap.id,
                        project_id=None,
                        source_type="github_deep_evidence",
                        source_location=repo.html_url or repo_name,
                        artifact=repo_name,
                        category="EXPERIMENTAL_EVIDENCE",
                        summary=cap_data["reason"],
                        confidence=cap_data["confidence"],
                        sensitivity="INTERNAL",
                        verified_at=datetime.now(UTC),
                        private=True,
                    )
                    session.add(evidence)

            proposal_actions.append({
                "proposal": cap_data["name"],
                "action": "NEW_PROPOSED",
                "final_name": final_name,
                "reason": cap_data["reason"],
            })

    await session.flush()

    # Step 6: Build founder review report
    all_capabilities = list(
        (await session.execute(
            select(CapabilityCanon).where(
                CapabilityCanon.status.in_([
                    CapabilityStatus.PROPOSED,
                    CapabilityStatus.FOUNDER_CONFIRMED,
                    CapabilityStatus.REJECTED,
                ])
            )
        )).scalars().all()
    )

    confirmed_caps = [c for c in all_capabilities if c.status == CapabilityStatus.FOUNDER_CONFIRMED]
    proposed_caps = [c for c in all_capabilities if c.status == CapabilityStatus.PROPOSED]
    rejected_caps = [c for c in all_capabilities if c.status == CapabilityStatus.REJECTED]

    return {
        "deep_evidence": {
            "repos_analyzed": deep.get("repos_analyzed", 0),
            "evidence_records_created": evidence_count,
            "github_health": deep.get("github_health", {}),
            "portfolio_summary": deep.get("portfolio_summary", {}),
        },
        "proposal_reassessments": proposal_actions,
        "new_capabilities_proposed": [
            c for c in proposal_actions if c["action"] == "NEW_PROPOSED"
        ],
        "portfolio_review": {
            "confirmed_capabilities": [
                {"name": c.name, "maturity": c.maturity, "definition": c.definition[:200]}
                for c in confirmed_caps
            ],
            "proposed_capabilities": [
                {
                    "name": c.name,
                    "status": str(c.status),
                    "entered_from": c.entered_from,
                    "founder_review_note": c.founder_review_note,
                    "limitations": c.limitations[:3],
                }
                for c in proposed_caps
            ],
            "rejected_capabilities": [
                {"name": c.name, "reason": c.founder_review_note}
                for c in rejected_caps
            ],
        },
        "founder_actions_required": [
            {
                "capability": c.name,
                "action": "REVIEW",
                "status": str(c.status),
                "evidence_summary": (c.founder_review_note or "")[:200],
            }
            for c in proposed_caps
        ],
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def _resolve_capability_name(session: AsyncSession, base_name: str) -> str:
    """Resolve a distinct name for a new capability, avoiding collisions."""
    existing = (
        await session.execute(
            select(CapabilityCanon).where(CapabilityCanon.name == base_name)
        )
    ).scalar_one_or_none()
    if existing is None:
        return base_name
    # If the name collides with a REJECTED or confirmed entry, add suffix
    status_val = getattr(existing.status, "value", str(existing.status))
    if status_val in {"REJECTED", "FOUNDER_CONFIRMED", "EVIDENCE_VERIFIED"}:
        return f"{base_name} (Deep Evidence)"
    # If it's already a census proposal, reuse it
    if existing.entered_from == "github_portfolio_census" and status_val == "PROPOSED":
        return base_name
    return base_name
