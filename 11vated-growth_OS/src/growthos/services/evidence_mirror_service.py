"""Evidence Mirror Service — orchestrates mirror creation, local analysis, and evidence persistence.

Connects the evidence_mirror and local_semantic modules with the database layer.
Provides the main entry point for local deep evidence analysis.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import growthos.domain.models  # noqa: F401
from growthos.domain.enums import DeepReviewStatus, EvidenceIndependence, MirrorState
from growthos.domain.models_capability import (
    CapabilityEvidenceRecord,
    RepositoryEvidence,
)
from growthos.domain.models_scout import CapabilityCanon
from growthos.intelligence.evidence_mirror import (
    ensure_mirror,
    verify_mirror_safety,
    verify_no_remote_mutation,
)
from growthos.intelligence.local_semantic import (
    ImplementationGraph,
    analyze_mirror_locally,
    compute_graph_confidence,
    graph_to_dict,
)
from growthos.shared.ids import new_id

# ---------------------------------------------------------------------------
# Deep review status determination
# ---------------------------------------------------------------------------


def _determine_deep_review_status(graph: ImplementationGraph) -> str:
    """Determine deep review status from a local analysis graph."""
    if graph.total_impl_files == 0 and graph.total_test_files == 0:
        if len(graph.all_files) <= 5:
            return DeepReviewStatus.INSUFFICIENT
        return DeepReviewStatus.PARTIAL
    if graph.total_impl_files < 3:
        return DeepReviewStatus.PARTIAL
    return DeepReviewStatus.COMPLETE


def _determine_maturity(graph: ImplementationGraph) -> str:
    """Determine maturity from local evidence."""
    impl = graph.total_impl_files
    tests = graph.total_test_files
    has_build = graph.total_build_files > 0
    has_entry = len(graph.entry_points) > 0

    if impl >= 8 and tests >= 5 and has_build and has_entry:
        return "CLIENT_READY"
    if impl >= 5 and tests >= 3 and has_build:
        return "INTERNAL_PROVEN"
    if impl >= 3 and tests >= 1:
        return "PROTOTYPE_PROVEN"
    if impl >= 1:
        return "EXPERIMENTAL"
    return "EXPERIMENTAL"


def _determine_reproducibility(graph: ImplementationGraph) -> str:
    if graph.total_test_files > 0 and graph.total_build_files > 0:
        return "HIGH"
    if graph.total_test_files > 0:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------------
# Local analysis + persistence
# ---------------------------------------------------------------------------


async def run_local_deep_analysis(
    session: AsyncSession,
    repo: RepositoryEvidence,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Run local deep evidence analysis on one repository.

    1. Ensures a mirror exists (creates if needed)
    2. Runs local semantic analysis on the mirror filesystem
    3. Persists findings as CapabilityEvidenceRecord
    4. Returns the analysis results

    Does NOT confirm any capability. Does NOT send outreach.
    """
    result: dict[str, Any] = {
        "full_name": repo.full_name,
        "mirror_state": "unknown",
        "analysis": None,
        "persisted": False,
        "error": None,
    }

    # Step 1: Ensure mirror
    try:
        mirror = await ensure_mirror(session, repo)
    except Exception as exc:
        result["error"] = f"Mirror creation failed: {type(exc).__name__}: {exc}"
        result["mirror_state"] = "FAILED"
        return result

    result["mirror_state"] = mirror.mirror_state

    if mirror.mirror_state != MirrorState.READY:
        result["error"] = f"Mirror not ready: {mirror.mirror_state}"
        if mirror.error:
            result["error"] += f" — {mirror.error[:200]}"
        return result

    # Step 2: Safety verification
    safety = await verify_mirror_safety(mirror)
    if not safety.get("safe"):
        result["error"] = f"Mirror safety check failed: {safety}"
        result["mirror_state"] = "UNSAFE"
        return result

    mutation_check = await verify_no_remote_mutation(mirror)
    if not mutation_check.get("safe"):
        result["error"] = f"Remote mutation detected: {mutation_check}"
        result["mirror_state"] = "MUTATION_DETECTED"
        return result

    # Step 3: Local semantic analysis
    try:
        graph = await analyze_mirror_locally(
            mirror.local_path,
            max_files=500,
            max_file_size=100_000,
            include_tests=True,
            include_docs=True,
            include_build=True,
        )
    except Exception as exc:
        result["error"] = f"Local analysis failed: {type(exc).__name__}: {exc}"
        return result

    graph_dict = graph_to_dict(graph)
    confidence = compute_graph_confidence(graph)
    maturity = _determine_maturity(graph)
    reproducibility = _determine_reproducibility(graph)
    deep_status = _determine_deep_review_status(graph)

    result["analysis"] = {
        "graph": graph_dict,
        "confidence": confidence,
        "maturity": maturity,
        "reproducibility": reproducibility,
        "deep_review_status": deep_status,
    }

    # Step 4: Update mirror record
    mirror.files_discovered = len(graph.all_files)
    mirror.source_roots = graph.source_roots
    mirror.languages = list(graph.languages.keys())
    mirror.last_deep_analysis_at = datetime.now(UTC)

    # Step 5: Persist evidence record
    # Check if already persisted for this repo (idempotency)
    existing = (
        await session.execute(
            select(CapabilityEvidenceRecord).where(
                CapabilityEvidenceRecord.source_type == "local_deep_evidence",
                CapabilityEvidenceRecord.source_location == repo.full_name,
            )
        )
    ).scalar_one_or_none()

    # Build coverage limitations
    limitations: list[str] = []
    if graph.total_test_files == 0:
        limitations.append("No test files found")
    if graph.total_impl_files == 0:
        limitations.append("No implementation files confirmed")
    if graph.total_build_files == 0:
        limitations.append("No build configuration found")

    # Compute overall confidence
    overall_confidence = round(
        0.30 * confidence.get("implementation", 0)
        + 0.25 * confidence.get("testing", 0)
        + 0.15 * confidence.get("build", 0)
        + 0.15 * confidence.get("runtime", 0)
        + 0.15 * confidence.get("reproducibility", 0),
        3,
    )

    # Dominant evidence class
    evidence_classes = []
    if graph.total_impl_files > 0:
        evidence_classes.append("DIRECT_IMPLEMENTATION")
    if graph.total_test_files > 0:
        evidence_classes.append("TEST_EVIDENCE")
    if graph.total_build_files > 0:
        evidence_classes.append("BUILD_EVIDENCE")
    if graph.entry_points:
        evidence_classes.append("RUNTIME_EVIDENCE")

    # Subsystem summary
    subsystem_summary = {}
    for s in graph.subsystems:
        subsystem_summary[s.category] = {
            "name": s.name,
            "status": s.status,
            "impl_files": len(s.implementation_files),
            "test_files": len(s.test_files),
        }

    summary_parts = [
        f"Files: {len(graph.all_files)} total, {graph.total_impl_files} impl, {graph.total_test_files} test, {graph.total_build_files} build",
        f"Classes: {graph.total_classes}, Functions: {graph.total_functions}, Lines: {graph.total_lines}",
        f"Maturity: {maturity}, Reproducibility: {reproducibility}",
        f"Subsystems: {len(graph.subsystems)} detected",
    ]
    if graph.contradictions:
        summary_parts.append(f"Contradictions: {len(graph.contradictions)}")

    if existing:
        # Update existing record
        existing.summary = "; ".join(summary_parts)
        existing.confidence = overall_confidence
        existing.deep_review_status = deep_status
        existing.files_discovered = len(graph.all_files)
        existing.files_inspected = graph.total_impl_files + graph.total_test_files
        existing.source_files_inspected = graph.total_impl_files
        existing.test_files_inspected = graph.total_test_files
        existing.build_files_inspected = graph.total_build_files
        existing.docs_inspected = graph.total_docs_files
        existing.coverage_limitations = limitations
        existing.test_quality = "TESTS_DISCOVERED" if graph.total_test_files > 0 else None
        existing.build_quality = "BUILD_CONFIG_PRESENT" if graph.total_build_files > 0 else None
        existing.runtime_quality = "RUNTIME_ENTRYPOINT_PRESENT" if graph.entry_points else "STATIC_ONLY"
        existing.evidence_independence = EvidenceIndependence.INDEPENDENT_IMPLEMENTATION
        existing.implementation_details = {
            "architecture_signals": graph_dict.get("architecture_signals", []),
            "unique_modules": graph_dict.get("unique_classes", []),
            "contradictions": graph.contradictions,
            "maturity_assessment": maturity,
            "reproducibility": reproducibility,
            "confidence_dimensions": confidence,
            "subsystems": subsystem_summary,
            "source_roots": graph.source_roots,
            "entry_points": graph.entry_points,
            "languages": graph.languages,
            "total_lines": graph.total_lines,
            "evidence_source": "local_mirror",
            "mirror_commit_sha": mirror.local_evidence_sha,
        }
        existing.category = evidence_classes[0] if evidence_classes else "MISSING_EVIDENCE"
        existing.verified_at = datetime.now(UTC)
        result["persisted"] = True
    else:
        evidence = CapabilityEvidenceRecord(
            id=new_id(),
            capability_id=None,  # set by caller if linking
            project_id=None,
            source_type="local_deep_evidence",
            source_location=repo.full_name,
            artifact=repo.name,
            category=evidence_classes[0] if evidence_classes else "MISSING_EVIDENCE",
            summary="; ".join(summary_parts),
            confidence=overall_confidence,
            sensitivity="INTERNAL",
            verified_at=datetime.now(UTC),
            private=True,
            branch=repo.default_branch,
            commit_sha=mirror.remote_commit_sha,
            evidence_source="local_mirror",
            files_discovered=len(graph.all_files),
            files_inspected=graph.total_impl_files + graph.total_test_files,
            source_files_inspected=graph.total_impl_files,
            test_files_inspected=graph.total_test_files,
            build_files_inspected=graph.total_build_files,
            docs_inspected=graph.total_docs_files,
            deep_review_status=deep_status,
            coverage_limitations=limitations,
            test_quality="TESTS_DISCOVERED" if graph.total_test_files > 0 else None,
            build_quality="BUILD_CONFIG_PRESENT" if graph.total_build_files > 0 else None,
            runtime_quality="RUNTIME_ENTRYPOINT_PRESENT" if graph.entry_points else "STATIC_ONLY",
            evidence_independence=EvidenceIndependence.INDEPENDENT_IMPLEMENTATION,
            implementation_details={
                "architecture_signals": graph_dict.get("architecture_signals", []),
                "unique_modules": graph_dict.get("unique_classes", []),
                "contradictions": graph.contradictions,
                "maturity_assessment": maturity,
                "reproducibility": reproducibility,
                "confidence_dimensions": confidence,
                "subsystems": subsystem_summary,
                "source_roots": graph.source_roots,
                "entry_points": graph.entry_points,
                "languages": graph.languages,
                "total_lines": graph.total_lines,
                "evidence_source": "local_mirror",
                "mirror_commit_sha": mirror.local_evidence_sha,
            },
        )
        session.add(evidence)
        result["persisted"] = True

    await session.flush()
    return result


async def run_full_local_deep_pass(
    session: AsyncSession,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Run local deep evidence analysis on all selected repositories.

    Returns a comprehensive report with per-repo analysis and portfolio summary.
    """
    from growthos.intelligence.github_portfolio import (
        cluster_families,
        select_deep_analysis,
    )
    from growthos.services.portfolio_census import _repo_payload

    repos = list((await session.execute(select(RepositoryEvidence))).scalars().all())
    if not repos:
        return {"error": "No repository evidence found. Run census first.", "repos_analyzed": 0}

    # Select repos for deep analysis
    payloads = [_repo_payload(r) for r in repos]
    fams = cluster_families(payloads)
    selected_names = set(select_deep_analysis(payloads, fams, max_count=8))
    selected_repos = [r for r in repos if r.full_name in selected_names]

    results: list[dict[str, Any]] = []
    for repo in selected_repos:
        r = await run_local_deep_analysis(session, repo, force=force)
        results.append(r)

    # Portfolio summary
    total_impl = 0
    total_test = 0
    total_lines = 0
    maturity_dist: dict[str, int] = {}
    all_subsystems: dict[str, dict[str, str]] = {}
    deep_statuses: dict[str, str] = {}

    for r in results:
        analysis = r.get("analysis", {})
        if not analysis:
            continue
        graph = analysis.get("graph", {})
        total_impl += graph.get("total_impl_files", 0)
        total_test += graph.get("total_test_files", 0)
        total_lines += graph.get("total_lines", 0)
        mat = analysis.get("maturity", "UNKNOWN")
        maturity_dist[mat] = maturity_dist.get(mat, 0) + 1
        deep_statuses[r["full_name"]] = analysis.get("deep_review_status", "UNKNOWN")
        for s in graph.get("subsystems", []):
            cat = s.get("category", "unknown")
            if cat not in all_subsystems:
                all_subsystems[cat] = {"name": s.get("name", cat), "repos": []}
            all_subsystems[cat]["repos"].append(r["full_name"])

    return {
        "repos_analyzed": len([r for r in results if r.get("analysis")]),
        "repos_failed": len([r for r in results if r.get("error")]),
        "results": results,
        "portfolio_summary": {
            "total_implementation_files": total_impl,
            "total_test_files": total_test,
            "total_lines": total_lines,
            "maturity_distribution": maturity_dist,
            "subsystems_detected": len(all_subsystems),
            "subsystems": all_subsystems,
            "deep_review_statuses": deep_statuses,
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }


# ---------------------------------------------------------------------------
# Capability recommendation rebuild
# ---------------------------------------------------------------------------


async def rebuild_capability_recommendations(
    session: AsyncSession,
) -> dict[str, Any]:
    """Recompute machine recommendations from repaired local evidence.

    Does NOT change founder state. Only updates recommended_decision,
    recommendation_reason, and recommendation_confidence on each CapabilityCanon.
    """
    capabilities = list(
        (await session.execute(
            select(CapabilityCanon).where(
                CapabilityCanon.status.notin_(["FOUNDER_CONFIRMED", "RETIRED"])
            )
        )).scalars().all()
    )

    # Gather all evidence records
    all_evidence = list(
        (await session.execute(
            select(CapabilityEvidenceRecord).where(
                CapabilityEvidenceRecord.source_type == "local_deep_evidence"
            )
        )).scalars().all()
    )

    # Build per-repo evidence lookup
    repo_evidence: dict[str, list[dict[str, Any]]] = {}
    for ev in all_evidence:
        loc = ev.source_location
        if loc not in repo_evidence:
            repo_evidence[loc] = []
        details = ev.implementation_details or {}
        repo_evidence[loc].append({
            "summary": ev.summary,
            "confidence": ev.confidence,
            "maturity": details.get("maturity_assessment", "UNKNOWN"),
            "impl_files": ev.source_files_inspected,
            "test_files": ev.test_files_inspected,
            "subsystems": details.get("subsystems", {}),
            "architectures": details.get("architecture_signals", []),
            "deep_review_status": ev.deep_review_status,
            "evidence_source": ev.evidence_source,
            "branch": ev.branch,
            "commit_sha": ev.commit_sha,
        })

    recommendations: dict[str, dict[str, Any]] = {}

    for cap in capabilities:
        sources = cap.related_completed_work or []
        linked_evidence = []
        for src in sources:
            if src in repo_evidence:
                linked_evidence.extend(repo_evidence[src])

        if not linked_evidence:
            # Check if any evidence mentions capability-related terms
            cap_name_lower = cap.name.lower()
            for _loc, evs in repo_evidence.items():
                for ev in evs:
                    subsystems = ev.get("subsystems", {})
                    for cat, _info in subsystems.items():
                        if any(term in cap_name_lower for term in cat.split("_")):
                            linked_evidence.append(ev)
                            break

        # Compute recommendation
        if not linked_evidence:
            rec = "REQUEST_MORE_EVIDENCE"
            reason = "No local deep evidence linked to this capability"
            confidence = 0.1
        else:
            avg_confidence = sum(e["confidence"] for e in linked_evidence) / len(linked_evidence)
            total_impl = sum(e["impl_files"] for e in linked_evidence)
            total_test = sum(e["test_files"] for e in linked_evidence)
            has_complete = any(e["deep_review_status"] == "DEEP_REVIEW_COMPLETE" for e in linked_evidence)

            if total_impl >= 10 and total_test >= 5 and avg_confidence >= 0.5 and has_complete:
                rec = "KEEP"
                reason = f"Strong evidence: {total_impl} impl files, {total_test} test files, avg confidence {avg_confidence:.2f}"
                confidence = min(0.9, avg_confidence + 0.1)
            elif total_impl >= 5 and avg_confidence >= 0.3:
                rec = "KEEP"
                reason = f"Moderate evidence: {total_impl} impl files, avg confidence {avg_confidence:.2f}"
                confidence = avg_confidence
            elif total_impl >= 2:
                rec = "REQUEST_MORE_EVIDENCE"
                reason = f"Limited evidence: {total_impl} impl files, avg confidence {avg_confidence:.2f}"
                confidence = avg_confidence
            else:
                rec = "WITHHOLD_BY_CRITIC"
                reason = f"Insufficient implementation evidence: {total_impl} files"
                confidence = 0.2

        # Check for evidence completeness across linked repos
        complete_count = sum(1 for e in linked_evidence if e["deep_review_status"] == "DEEP_REVIEW_COMPLETE")
        completeness = f"{complete_count}/{len(linked_evidence)} repos COMPLETE" if linked_evidence else "0 repos linked"

        # Update capability
        prev_rec = cap.recommended_decision
        cap.recommended_decision = rec
        cap.recommendation_reason = reason
        cap.recommendation_confidence = confidence
        cap.deep_review_completeness = {
            "local_analysis": True,
            "linked_repos": len(linked_evidence),
            "complete_reviews": complete_count,
            "completeness": completeness,
        }

        recommendations[cap.name] = {
            "previous": prev_rec,
            "new": rec,
            "reason": reason,
            "confidence": confidence,
            "completeness": completeness,
        }

    await session.flush()
    return {
        "capabilities_reviewed": len(capabilities),
        "recommendations": recommendations,
    }
