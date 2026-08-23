"""Capability Attribution Service — wires the attribution engine with the database.

Runs attribution against local mirror evidence, persists per-file attributions,
and rebuilds capability recommendations from attributed evidence (not raw file counts).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

import growthos.domain.models  # noqa: F401
from growthos.domain.models_capability import (
    CapabilityEvidenceAttribution,
    EvidenceMirror,
)
from growthos.domain.models_scout import CapabilityCanon
from growthos.intelligence.capability_attribution import (
    CAPABILITY_DEFINITIONS,
    CapabilityDefinition,
    PortfolioAttributionSummary,
    attribute_portfolio,
)
from growthos.intelligence.local_semantic import (
    ImplementationGraph,
    analyze_mirror_locally,
)
from growthos.shared.ids import new_id

# ---------------------------------------------------------------------------
# Attributed confidence computation
# ---------------------------------------------------------------------------


def _compute_attributed_confidence(
    summary: PortfolioAttributionSummary,
    cap_def: CapabilityDefinition,
) -> dict[str, float]:
    """Compute independent confidence dimensions from attributed evidence.

    Unlike the file-count-based approach, this uses only directly attributed
    files and their directness classes.
    """
    # Implementation confidence: based on direct core files
    impl = min(1.0, 0.2 + 0.15 * summary.total_direct_core) if summary.total_direct_core else 0.0

    # Testing confidence: based on attributed + validating tests
    test = min(1.0, 0.15 + 0.12 * summary.total_validating_tests) if summary.total_validating_tests else 0.0

    # Independence: more independent repos = higher
    independence = min(1.0, 0.3 * summary.independent_core_repos) if summary.independent_core_repos else 0.0

    # Coverage: ratio of attributed files to total evaluated
    total_attr = summary.total_direct_core + summary.total_direct_supporting
    total_evaluated = total_attr + summary.total_indirect_supporting + summary.total_not_relevant
    coverage = total_attr / max(1, total_evaluated)

    # Delivery: based on subsystem implementation quality
    tested_subsystems = 0
    for repo in summary.repo_results:
        for _name, directness, conf, _reason in repo.subsystem_attributions:
            if directness in ("DIRECT_CORE",) and conf >= 0.6:
                tested_subsystems += 1
    delivery = min(1.0, 0.2 + 0.15 * tested_subsystems) if tested_subsystems else 0.0

    return {
        "implementation": round(impl, 3),
        "testing": round(test, 3),
        "independence": round(independence, 3),
        "coverage": round(coverage, 3),
        "delivery": round(delivery, 3),
        "overall": round(summary.overall_confidence, 3),
    }


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------


async def _clear_attributions_for_capability(
    session: AsyncSession,
    capability_id: str,
) -> int:
    """Delete all existing attributions for a capability (idempotent rebuild)."""
    await session.execute(
        delete(CapabilityEvidenceAttribution).where(
            CapabilityEvidenceAttribution.capability_id == capability_id
        )
    )
    return 0


async def _persist_attribution(
    session: AsyncSession,
    capability_id: str,
    repo_name: str,
    branch: str | None,
    commit_sha: str | None,
    attr: Any,  # FileAttribution
) -> CapabilityEvidenceAttribution:
    """Persist a single file attribution record."""
    record = CapabilityEvidenceAttribution(
        id=new_id(),
        capability_id=capability_id,
        repository=repo_name,
        file_path=attr.file_path,
        subsystem=attr.subsystem,
        evidence_type=attr.evidence_type,
        attribution_directness=attr.directness,
        attribution_reason=attr.reason,
        symbol_name=attr.symbol_name,
        language=attr.language,
        line_count=attr.line_count,
        branch=branch,
        commit_sha=commit_sha,
        evidence_source="local_mirror",
        attribution_confidence=attr.confidence,
        has_validating_test=attr.has_validating_test,
        validating_test_path=attr.validating_test_path,
        validates_subsystem=attr.validates_subsystem,
    )
    session.add(record)
    return record


# ---------------------------------------------------------------------------
# Main attribution pass
# ---------------------------------------------------------------------------


async def run_capability_attribution_pass(
    session: AsyncSession,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Run the full capability evidence attribution pass.

    For every non-terminal capability:
    1. Load all local_deep_evidence records and their mirror graphs
    2. Run the attribution engine against each capability definition
    3. Persist per-file attributions
    4. Recompute attributed confidence
    5. Update capability recommendations

    Does NOT change founder state. Does NOT confirm capabilities.
    """
    # Load evidence mirrors and re-analyze
    mirrors = list(
        (await session.execute(
            select(EvidenceMirror).where(EvidenceMirror.mirror_state == "READY")
        )).scalars().all()
    )

    # Analyze each mirror locally (reuse cached analysis if available)
    repo_graphs: dict[str, tuple[ImplementationGraph, str | None, str | None]] = {}
    repo_details: dict[str, dict[str, Any]] = {}

    for mirror in mirrors:
        repo_name = mirror.full_name
        try:
            graph = await analyze_mirror_locally(
                mirror.local_path,
                max_files=500,
                max_file_size=100_000,
                include_tests=True,
                include_docs=True,
                include_build=True,
            )
            repo_graphs[repo_name] = (graph, mirror.default_branch, mirror.remote_commit_sha)
            repo_details[repo_name] = {
                "files_discovered": len(graph.all_files),
                "impl_files": graph.total_impl_files,
                "test_files": graph.total_test_files,
                "maturity_hint": "LOCAL_ANALYZED",
            }
        except Exception as exc:
            repo_details[repo_name] = {"error": str(exc)}

    if not repo_graphs:
        return {"error": "No mirror graphs available", "mirrors_checked": len(mirrors)}

    # For each capability, run attribution
    results: list[dict[str, Any]] = []

    # Also attribute FOUNDER_CONFIRMED capabilities (for completeness)
    all_capabilities = list(
        (await session.execute(select(CapabilityCanon))).scalars().all()
    )

    for cap in all_capabilities:
        # SUPERSEDED/REJECTED: set recommendation and skip attribution
        if cap.status in ("SUPERSEDED", "REJECTED"):
            cap.recommended_decision = "WITHHOLD"
            cap.recommendation_reason = f"Capability is {cap.status} — no recommendation"
            cap.recommendation_confidence = 0.0
            results.append({
                "capability": cap.name,
                "founder_state": cap.status,
                "recommended_decision": "WITHHOLD",
                "recommendation_reason": f"Capability is {cap.status}",
                "confidence": {"overall": 0.0},
                "evidence_numerator": "Skipped",
                "evidence_denominator": "Skipped",
                "repos_with_core_evidence": 0,
                "attributed_files_persisted": 0,
                "per_repo_summary": {},
            })
            continue

        # Find matching capability definition
        cap_def = None
        for cd in CAPABILITY_DEFINITIONS:
            if cd.name.lower() in cap.name.lower() or cap.name.lower() in cd.name.lower():
                cap_def = cd
                break

        if not cap_def:
            # No definition match — create a minimal one from the capability's own data
            cap_def = CapabilityDefinition(
                name=cap.name,
                buyer_problem=cap.typical_customer_problem or "Unknown",
                core_file_patterns=cap.name.lower().split(),
            )

        # Run attribution
        summary = attribute_portfolio(repo_graphs, cap_def)
        conf = _compute_attributed_confidence(summary, cap_def)

        # Clear old attributions and persist new ones
        await _clear_attributions_for_capability(session, cap.id)

        total_persisted = 0
        # Track already-attributed (capability, repo, file) to avoid unique constraint violations
        attributed_files: set[tuple[str, str, str]] = set()

        for repo_result in summary.repo_results:
            branch = repo_result.branch
            sha = repo_result.commit_sha

            # Persist file attributions (direct core + direct supporting only)
            for attr in repo_result.file_attributions:
                if attr.directness in ("DIRECT_CORE", "DIRECT_SUPPORTING"):
                    key = (cap.id, repo_result.repository, attr.file_path)
                    if key in attributed_files:
                        continue
                    attributed_files.add(key)
                    await _persist_attribution(
                        session, cap.id, repo_result.repository,
                        branch, sha, attr,
                    )
                    total_persisted += 1

            # Persist test attributions
            for attr in repo_result.test_attributions:
                if attr.directness in ("DIRECT_CORE", "DIRECT_SUPPORTING"):
                    key = (cap.id, repo_result.repository, attr.file_path)
                    if key in attributed_files:
                        continue
                    attributed_files.add(key)
                    await _persist_attribution(
                        session, cap.id, repo_result.repository,
                        branch, sha, attr,
                    )
                    total_persisted += 1

        # Update capability with attributed evidence summary
        cap.evidence_summary_for_review = {
            "attributed_evidence": {
                "numerator": summary.evidence_numerator,
                "denominator": summary.evidence_denominator,
                "confidence": conf,
                "repos_with_core_evidence": summary.independent_core_repos,
                "total_attributed_files": summary.total_direct_core + summary.total_direct_supporting,
                "total_context_excluded": summary.total_context_only,
                "total_not_relevant_excluded": summary.total_not_relevant,
            },
            "per_repo": {
                r.repository: {
                    "direct_core": r.direct_core_count,
                    "direct_supporting": r.direct_supporting_count,
                    "indirect": r.indirect_supporting_count,
                    "context_only": r.context_only_count,
                    "not_relevant": r.not_relevant_count,
                    "attributed_tests": r.attributed_test_count,
                    "confidence": r.overall_confidence,
                    "subsystems": [
                        {"name": n, "directness": d, "confidence": c}
                        for n, d, c, _ in r.subsystem_attributions
                        if d != "NOT_RELEVANT"
                    ],
                }
                for r in summary.repo_results
                if r.direct_core_count > 0 or r.direct_supporting_count > 0
            },
        }

        # SUPERSEDED/REJECTED capabilities get no recommendation
        if cap.status in ("SUPERSEDED", "REJECTED"):
            cap.recommended_decision = "WITHHOLD"
            cap.recommendation_reason = f"Capability is {cap.status} — no recommendation"
            cap.recommendation_confidence = 0.0
            result_entry = {
                "capability": cap.name,
                "founder_state": cap.status,
                "recommended_decision": "WITHHOLD",
                "recommendation_reason": f"Capability is {cap.status}",
                "confidence": {"overall": 0.0},
                "evidence_numerator": summary.evidence_numerator,
                "evidence_denominator": summary.evidence_denominator,
                "repos_with_core_evidence": summary.independent_core_repos,
                "attributed_files_persisted": 0,
                "per_repo_summary": {},
            }
            results.append(result_entry)
            continue

        # Determine recommendation from attributed evidence
        if summary.total_direct_core >= 3 and summary.independent_core_repos >= 1:
            rec = "KEEP"
            reason = (
                f"{summary.total_direct_core} direct core files across "
                f"{summary.independent_core_repos} repos, "
                f"{summary.total_validating_tests} validating tests"
            )
            rec_conf = conf["overall"]
        elif summary.total_direct_core >= 1 or summary.total_direct_supporting >= 3:
            rec = "KEEP"
            reason = (
                f"{summary.total_direct_core} core + {summary.total_direct_supporting} supporting files; "
                f"needs broader evidence for stronger confidence"
            )
            rec_conf = conf["overall"] * 0.8
        elif summary.total_direct_supporting >= 1:
            rec = "REQUEST_MORE_EVIDENCE"
            reason = f"Only {summary.total_direct_supporting} supporting files — insufficient direct evidence"
            rec_conf = conf["overall"] * 0.5
        else:
            rec = "WITHHOLD"
            reason = "No directly attributed evidence found"
            rec_conf = 0.1

        # Do NOT change founder state
        cap.recommended_decision = rec
        cap.recommendation_reason = reason
        cap.recommendation_confidence = rec_conf

        # Build the founder-visible evidence summary
        result_entry = {
            "capability": cap.name,
            "founder_state": cap.status,
            "recommended_decision": rec,
            "recommendation_reason": reason,
            "confidence": conf,
            "evidence_numerator": summary.evidence_numerator,
            "evidence_denominator": summary.evidence_denominator,
            "repos_with_core_evidence": summary.independent_core_repos,
            "attributed_files_persisted": total_persisted,
            "per_repo_summary": {
                r.repository: {
                    "direct_core": r.direct_core_count,
                    "direct_supporting": r.direct_supporting_count,
                    "attributed_tests": r.attributed_test_count,
                }
                for r in summary.repo_results
                if r.direct_core_count > 0 or r.direct_supporting_count > 0
            },
        }
        results.append(result_entry)

    await session.flush()

    return {
        "capabilities_analyzed": len(results),
        "mirrors_used": len(repo_graphs),
        "results": results,
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


async def run_attribution_cli(session: AsyncSession) -> dict[str, Any]:
    """CLI entry point for the attribution pass."""
    return await run_capability_attribution_pass(session, force=False)
