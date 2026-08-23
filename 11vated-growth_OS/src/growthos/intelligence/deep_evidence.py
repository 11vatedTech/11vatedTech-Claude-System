"""Portfolio Deep Evidence — multi-project verification before Capability Canon expansion.

For each selected repository, fetches actual README + key source files via the
GitHub API, extracts real implementation evidence (not README claims), classifies
evidence classes, and produces structured findings. Roadmap/TODO claims are
separated from implemented functionality.

Hard rules:
- README ≠ implementation proof
- Planned features ≠ implemented functionality
- Repository existence ≠ capability proof
- A transient rate limit never erases persisted evidence
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import growthos.domain.models  # noqa: F401
from growthos.domain.models_capability import (
    CapabilityEvidenceRecord,
    RepositoryEvidence,
)
from growthos.intelligence.github_portfolio import (
    GitHubProfileClient,
    select_deep_files,
)

# ---------------------------------------------------------------------------
# Evidence class labels
# ---------------------------------------------------------------------------

class EvidenceClass:
    DIRECT_IMPLEMENTATION = "DIRECT_IMPLEMENTATION"
    TEST_EVIDENCE = "TEST_EVIDENCE"
    BUILD_EVIDENCE = "BUILD_EVIDENCE"
    RUNTIME_EVIDENCE = "RUNTIME_EVIDENCE"
    RELEASE_EVIDENCE = "RELEASE_EVIDENCE"
    ARCHITECTURE_EVIDENCE = "ARCHITECTURE_EVIDENCE"
    DOCUMENTED_CLAIM = "DOCUMENTED_CLAIM"
    EXPERIMENTAL_EVIDENCE = "EXPERIMENTAL_EVIDENCE"
    CONTRADICTING_EVIDENCE = "CONTRADICTING_EVIDENCE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"


# ---------------------------------------------------------------------------
# Lightweight code analysis (no LLM — deterministic pattern matching)
# ---------------------------------------------------------------------------

# Patterns that suggest actual implementation vs documentation/claims
_IMPLEMENTATION_PATTERNS = [
    (r"\bclass\s+\w+[\s(:]", "class definition"),
    (r"\basync\s+def\s+\w+", "async function"),
    (r"\bdef\s+\w+\s*\(", "function definition"),
    (r"\bstruct\s+\w+", "struct definition"),
    (r"\bfn\s+\w+", "rust function"),
    (r"\bfunc\s+\w+", "go function"),
    (r"\bpublic\s+(static\s+)?(void|int|string|class)", "c#/java member"),
    (r"\bimport\s+\w+", "import statement"),
    (r"\bfrom\s+\w+\s+import", "python import"),
]

_TEST_PATTERNS = [
    (r"\b(test_|spec_|_test\.|_spec\.)", "test file naming"),
    (r"\b(describe|it|test|expect|assert)\s*\(", "test framework usage"),
    (r"\b(unittest|pytest|jest|vitest|mocha|ginkgo|cargo test)", "test framework reference"),
    (r"\bmock|stub|fixture|factory", "test infrastructure"),
]

_BUILD_PATTERNS = [
    (r"\b(build|compile|bundle|transpile|minify)", "build action"),
    (r"\b(docker|container|image|layer)", "containerization"),
    (r"\b(github.actions|workflow|ci|cd)", "CI/CD"),
    (r"npm\s+(run|build|test)|yarn\s+(build|test)|cargo\s+(build|test)", "build commands"),
]

_ROADMAP_PATTERNS = [
    (r"\b(todo|fixme|hack|xxx|placeholder|stub|not.?yet.?implemented)", "TODO/stub marker"),
    (r"\b(will\s+be|planned|future|roadmap|coming\s+soon|phase\s+\d)", "roadmap language"),
    (r"\b(not\s+implemented|unimplemented|wip|work.in.progress)", "incomplete marker"),
    (r"\b(supports?\s+coming|will\s+support|should\s+support)", "future capability"),
]


def _count_pattern_matches(text: str, patterns: list[tuple[str, str]]) -> list[tuple[str, int]]:
    """Count matches for each pattern category in source text."""
    results = []
    for pattern, label in patterns:
        count = len(re.findall(pattern, text, re.IGNORECASE))
        if count > 0:
            results.append((label, count))
    return results


def _extract_module_names(text: str, lang: str) -> list[str]:
    """Extract class/function/struct names from source code."""
    names: list[str] = []
    if lang in ("Python",):
        names.extend(re.findall(r"\bclass\s+(\w+)", text))
        names.extend(re.findall(r"\basync\s+def\s+(\w+)", text))
        names.extend(re.findall(r"\bdef\s+(\w+)\s*\(", text))
    elif lang in ("JavaScript", "TypeScript", "TypeScript/React", "JavaScript/React"):
        names.extend(re.findall(r"\bclass\s+(\w+)", text))
        names.extend(re.findall(r"\b(?:export\s+)?(?:const|let|var|function)\s+(\w+)", text))
    elif lang in ("C#",):
        names.extend(re.findall(r"\b(?:public|private|protected|internal)\s+(?:class|struct|interface)\s+(\w+)", text))
    elif lang in ("C++", "C"):
        names.extend(re.findall(r"\b(?:class|struct)\s+(\w+)", text))
    elif lang in ("Rust",):
        names.extend(re.findall(r"\b(?:pub\s+)?(?:struct|enum|trait|fn)\s+(\w+)", text))
    elif lang in ("Go",):
        names.extend(re.findall(r"\bfunc\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)", text))
    return names[:50]  # cap at 50


def _detect_architecture_signals(text: str, file_path: str) -> list[str]:
    """Detect architectural patterns from file content."""
    signals: list[str] = []
    text_lower = text.lower()

    arch_keywords = {
        "api": "API surface",
        "router": "routing layer",
        "middleware": "middleware",
        "database": "database layer",
        "repository": "repository pattern",
        "schema": "schema definition",
        "migration": "migration system",
        "worker": "background worker",
        "queue": "queue system",
        "cache": "caching layer",
        "auth": "authentication",
        "oauth": "OAuth integration",
        "websocket": "WebSocket",
        "grpc": "gRPC",
        "pipeline": "pipeline architecture",
        "graph": "graph architecture",
        "tensor": "tensor processing",
        "scheduler": "scheduling system",
        "event": "event system",
        "hook": "hook system",
        "plugin": "plugin system",
        "adapter": "adapter pattern",
        "factory": "factory pattern",
        "singleton": "singleton pattern",
        "dependency injection": "DI container",
    }

    for keyword, label in arch_keywords.items():
        if keyword in text_lower:
            signals.append(label)

    return list(set(signals))[:10]


# ---------------------------------------------------------------------------
# Deep evidence analysis for a single repository
# ---------------------------------------------------------------------------


def analyze_file_content(
    content: str,
    file_path: str,
    primary_language: str | None,
) -> dict[str, Any]:
    """Analyze a single file's content for implementation evidence.

    Returns structured analysis with evidence classes, module names,
    architecture signals, and roadmap claims.
    """
    evidence_classes: list[str] = []
    impl_matches = _count_pattern_matches(content, _IMPLEMENTATION_PATTERNS)
    test_matches = _count_pattern_matches(content, _TEST_PATTERNS)
    build_matches = _count_pattern_matches(content, _BUILD_PATTERNS)
    roadmap_matches = _count_pattern_matches(content, _ROADMAP_PATTERNS)

    total_impl = sum(count for _, count in impl_matches)
    total_test = sum(count for _, count in test_matches)
    total_roadmap = sum(count for _, count in roadmap_matches)

    if total_impl >= 3:
        evidence_classes.append(EvidenceClass.DIRECT_IMPLEMENTATION)
    if total_test > 1:
        evidence_classes.append(EvidenceClass.TEST_EVIDENCE)
    if total_roadmap > 2 and total_impl < 3:
        evidence_classes.append(EvidenceClass.DOCUMENTED_CLAIM)

    module_names = _extract_module_names(content, primary_language or "Python")
    arch_signals = _detect_architecture_signals(content, file_path)

    return {
        "file_path": file_path,
        "evidence_classes": evidence_classes,
        "implementation_signals": total_impl,
        "test_signals": total_test,
        "build_signals": sum(count for _, count in build_matches),
        "roadmap_signals": total_roadmap,
        "module_names": module_names,
        "architecture_signals": arch_signals,
        "impl_details": impl_matches,
        "roadmap_details": roadmap_matches,
        "line_count": len(content.splitlines()),
    }


# ---------------------------------------------------------------------------
# Repository-level deep evidence synthesis
# ---------------------------------------------------------------------------


def synthesize_deep_evidence(
    readme_analysis: dict[str, Any] | None,
    file_analyses: list[dict[str, Any]],
    repo_meta: dict[str, Any],
) -> dict[str, Any]:
    """Synthesize deep evidence findings across all analyzed files.

    Produces a structured report for one repository with:
    - implementation evidence (classes, functions, modules)
    - test evidence
    - build evidence
    - architecture patterns
    - contradictions (roadmap vs implementation)
    - maturity assessment
    """
    # Collect all module names across files
    all_modules: list[str] = []
    all_arch_signals: list[str] = []
    impl_files = 0
    test_files = 0
    total_impl_signals = 0
    total_test_signals = 0
    total_roadmap_signals = 0
    contradictions: list[str] = []

    for fa in file_analyses:
        all_modules.extend(fa.get("module_names", []))
        all_arch_signals.extend(fa.get("architecture_signals", []))
        if EvidenceClass.DIRECT_IMPLEMENTATION in fa.get("evidence_classes", []):
            impl_files += 1
        if EvidenceClass.TEST_EVIDENCE in fa.get("evidence_classes", []):
            test_files += 1
        total_impl_signals += fa.get("implementation_signals", 0)
        total_test_signals += fa.get("test_signals", 0)
        total_roadmap_signals += fa.get("roadmap_signals", 0)
        # Detect contradictions: files heavy on roadmap claims but light on implementation
        if fa.get("roadmap_signals", 0) > 3 and fa.get("implementation_signals", 0) < 2:
            contradictions.append(
                f"{fa.get('file_path', 'unknown')}: {fa.get('roadmap_signals', 0)} roadmap claims but only {fa.get('implementation_signals', 0)} implementation signals"
            )

    # Deduplicate
    unique_modules = list(dict.fromkeys(all_modules))
    unique_arch = list(dict.fromkeys(all_arch_signals))

    # Classify evidence strength
    evidence_classes_found: list[str] = []
    if impl_files > 0:
        evidence_classes_found.append(EvidenceClass.DIRECT_IMPLEMENTATION)
    if test_files > 0:
        evidence_classes_found.append(EvidenceClass.TEST_EVIDENCE)
    if repo_meta.get("ci_build_present"):
        evidence_classes_found.append(EvidenceClass.BUILD_EVIDENCE)
    if repo_meta.get("releases_present"):
        evidence_classes_found.append(EvidenceClass.RELEASE_EVIDENCE)
    if repo_meta.get("architecture_docs_present"):
        evidence_classes_found.append(EvidenceClass.ARCHITECTURE_EVIDENCE)
    if total_roadmap_signals > 0:
        evidence_classes_found.append(EvidenceClass.DOCUMENTED_CLAIM)
    if contradictions:
        evidence_classes_found.append(EvidenceClass.CONTRADICTING_EVIDENCE)

    # Maturity assessment
    maturity = "EXPERIMENTAL"
    if impl_files >= 3 and test_files >= 1:
        maturity = "PROTOTYPE_PROVEN"
    if impl_files >= 5 and test_files >= 3 and repo_meta.get("releases_present"):
        maturity = "INTERNAL_PROVEN"
    if impl_files >= 8 and test_files >= 5 and repo_meta.get("ci_build_present") and repo_meta.get("releases_present"):
        maturity = "CLIENT_READY"

    # Reproducibility
    reproducibility = "LOW"
    if repo_meta.get("tests_present") and repo_meta.get("ci_build_present"):
        reproducibility = "MEDIUM"
    if repo_meta.get("tests_present") and repo_meta.get("ci_build_present") and repo_meta.get("releases_present"):
        reproducibility = "HIGH"

    # Commercial readiness signal
    has_api_surface = any("API surface" in s or "routing layer" in s for s in unique_arch)
    has_database = any("database" in s.lower() for s in unique_arch)
    has_auth = any("authentication" in s.lower() or "OAuth" in s for s in unique_arch)

    # Confidence dimensions
    impl_confidence = min(1.0, 0.2 + 0.1 * impl_files) if impl_files else 0.0
    test_confidence = min(1.0, 0.3 * test_files) if test_files else 0.0
    build_confidence = 0.5 if repo_meta.get("ci_build_present") else 0.0
    runtime_confidence = 0.7 if repo_meta.get("releases_present") else 0.0
    reproducibility_confidence = {"HIGH": 0.9, "MEDIUM": 0.6, "LOW": 0.2}[reproducibility]

    # README content analysis (if available)
    readme_findings: list[str] = []
    if readme_analysis:
        if readme_analysis.get("roadmap_signals", 0) > 2:
            readme_findings.append(
                f"README contains {readme_analysis['roadmap_signals']} roadmap/future-claim signals"
            )
        if readme_analysis.get("implementation_signals", 0) > 5:
            readme_findings.append(
                "README contains substantial implementation detail (may be documentation-as-code)"
            )

    return {
        "files_analyzed": len(file_analyses),
        "implementation_files": impl_files,
        "test_files": test_files,
        "total_implementation_signals": total_impl_signals,
        "total_test_signals": total_test_signals,
        "total_roadmap_signals": total_roadmap_signals,
        "unique_modules": unique_modules[:30],
        "architecture_signals": unique_arch[:15],
        "evidence_classes": evidence_classes_found,
        "contradictions": contradictions,
        "readme_findings": readme_findings,
        "maturity_assessment": maturity,
        "reproducibility": reproducibility,
        "has_api_surface": has_api_surface,
        "has_database": has_database,
        "has_auth": has_auth,
        "confidence_dimensions": {
            "implementation": round(impl_confidence, 3),
            "testing": round(test_confidence, 3),
            "build": round(build_confidence, 3),
            "runtime": round(runtime_confidence, 3),
            "reproducibility": round(reproducibility_confidence, 3),
        },
    }


# ---------------------------------------------------------------------------
# Full deep analysis pipeline
# ---------------------------------------------------------------------------


async def analyze_repository_deep(
    client: GitHubProfileClient,
    repo: RepositoryEvidence,
    *,
    max_requests: int = 12,
) -> dict[str, Any]:
    """Perform a deep evidence analysis on one repository.

    Fetches README + selected files from the GitHub API, analyzes content,
    and returns structured findings. Does NOT persist — caller decides.

    ``max_requests`` caps the number of GitHub API calls made for this
    repository.  The budget is: 1 (tree) + 1 (readme) + (max_requests − 2)
    source files.  A budget of 12 gives 10 source files — enough for a
    meaningful signal with the unauthenticated 60 req/hr limit.
    """
    import base64

    full_name = repo.full_name
    branch = repo.default_branch or "main"
    requests_used = 0
    result: dict[str, Any] = {
        "full_name": full_name,
        "name": repo.name,
        "primary_language": repo.primary_language,
        "census_evidence_strength": repo.evidence_strength,
        "census_score": repo.evidence_value_score,
        "files_analyzed": 0,
        "requests_used": 0,
        "budget_exhausted": False,
        "error": None,
    }

    try:
        # 1) File tree — costs 1 request
        tree_paths = await client.get_tree(full_name, branch)
        requests_used += 1
        if client.rate_limited:
            result["error"] = "Rate limited during tree fetch"
            result["budget_exhausted"] = True
            result["requests_used"] = requests_used
            return result
        if not tree_paths:
            result["error"] = "No file tree available (possibly empty or rate-limited)"
            result["requests_used"] = requests_used
            return result

        # Select files for deep analysis (limited by budget)
        deep_files = select_deep_files(tree_paths)
        source_budget = max(0, max_requests - 2)  # tree + readme already counted

        # 2) README — costs 1 request
        readme_analysis = None
        readme_content = await client.get_readme(full_name)
        requests_used += 1
        if readme_content:
            try:
                decoded = base64.b64decode(readme_content).decode("utf-8", errors="replace")
                if len(decoded) > 20_000:
                    decoded = decoded[:20_000] + "\n... [truncated]"
                readme_analysis = analyze_file_content(decoded, "README.md", repo.primary_language)
            except Exception:
                readme_analysis = None

        # 3) Source files — each costs 1 request, up to source_budget
        file_analyses: list[dict[str, Any]] = []
        for file_path in deep_files:
            if len(file_analyses) >= source_budget:
                break
            if client.rate_limited:
                result["budget_exhausted"] = True
                break
            if file_path.lower().endswith((".md", ".rst", ".txt")):
                continue  # README already handled
            content = await client.get_file_content(full_name, file_path, ref=branch)
            requests_used += 1
            if content:
                try:
                    decoded = base64.b64decode(content).decode("utf-8", errors="replace")
                    if len(decoded) > 50_000:
                        decoded = decoded[:50_000] + "\n... [truncated]"
                    analysis = analyze_file_content(decoded, file_path, repo.primary_language)
                    file_analyses.append(analysis)
                except Exception:
                    continue

        result["files_analyzed"] = len(file_analyses)
        result["readme_analysis"] = readme_analysis
        result["file_analyses"] = file_analyses
        result["requests_used"] = requests_used

        # Synthesize findings
        synthesis = synthesize_deep_evidence(readme_analysis, file_analyses, {
            "primary_language": repo.primary_language,
            "ci_build_present": repo.ci_build_present,
            "releases_present": repo.releases_present,
            "tests_present": repo.tests_present,
            "architecture_docs_present": repo.architecture_docs_present,
            "source_present": repo.source_present,
        })
        result["synthesis"] = synthesis

    except Exception as exc:
        result["error"] = f"Deep analysis failed: {type(exc).__name__}"

    result["requests_used"] = requests_used
    return result


async def run_portfolio_deep_evidence(
    session: AsyncSession,
    *,
    client: GitHubProfileClient | None = None,
    limit: int = 8,
    max_requests_per_repo: int = 10,
) -> dict[str, Any]:
    """Run deep evidence analysis on all repositories selected for deep analysis.

    Fetches actual file contents from GitHub, performs lightweight code analysis,
    and produces structured evidence findings. Does NOT auto-confirm capabilities.

    The function is budget-aware: it tracks how many GitHub API requests have
    been consumed and stops before exceeding the rate limit.  Repos already
    analysed in a prior run (with ≥ 3 source files) are skipped unless the
    caller explicitly re-runs.
    """
    client = client or GitHubProfileClient()

    # Find all repos
    repos = list((await session.execute(select(RepositoryEvidence))).scalars().all())

    if not repos:
        return {"error": "No repository evidence found. Run census first.", "repos_analyzed": 0}

    # Determine which repos to deeply analyze (use the selection algorithm)
    from growthos.intelligence.github_portfolio import (
        cluster_families,
        select_deep_analysis,
    )
    from growthos.services.portfolio_census import _repo_payload
    payloads = [_repo_payload(r) for r in repos]
    fams = cluster_families(payloads)
    selected_names = set(select_deep_analysis(payloads, fams, max_count=limit))
    selected_repos = [r for r in repos if r.full_name in selected_names]

    # Skip repos that already have deep evidence (≥ 3 source files analysed)
    existing = list((
        await session.execute(
            select(CapabilityEvidenceRecord).where(
                CapabilityEvidenceRecord.source_type == "github_deep_evidence"
            )
        )
    ).scalars().all())
    already_done: set[str] = set()
    for e in existing:
        # Heuristic: if summary mentions ≥ 3 implementation files
        if e.summary and "implementation files" in (e.summary or ""):
            already_done.add(e.source_location or "")

    # Filter to repos that still need analysis
    repos_to_analyze = [
        r for r in selected_repos
        if r.full_name not in already_done
    ]

    # Budget-aware analysis
    results: list[dict[str, Any]] = []
    total_requests = 0
    budget_remaining = 50  # stay well within the 60/hr unauthenticated limit

    for repo in repos_to_analyze:
        if budget_remaining < max_requests_per_repo:
            # Not enough budget for a meaningful pass on this repo
            results.append({
                "full_name": repo.full_name,
                "name": repo.name,
                "error": "Skipped — insufficient API budget",
                "budget_exhausted": True,
                "files_analyzed": 0,
            })
            continue

        analysis = await analyze_repository_deep(
            client, repo, max_requests=max_requests_per_repo,
        )
        used = analysis.get("requests_used", 0)
        total_requests += used
        budget_remaining -= used
        results.append(analysis)

        if client.rate_limited:
            # Stop making more requests
            break

    # Also include already-analysed repos in summary (from earlier runs)
    for repo in selected_repos:
        if repo.full_name in already_done:
            results.append({
                "full_name": repo.full_name,
                "name": repo.name,
                "error": None,
                "files_analyzed": -1,  # marker: from prior run
                "from_prior_run": True,
            })

    # Compute portfolio-level summary
    all_modules: list[str] = []
    all_arch: list[str] = []
    maturity_counts: dict[str, int] = {}
    total_impl = 0
    total_test = 0
    total_roadmap = 0
    total_contradictions = 0
    for r in results:
        synth = r.get("synthesis", {})
        all_modules.extend(synth.get("unique_modules", []))
        all_arch.extend(synth.get("architecture_signals", []))
        mat = synth.get("maturity_assessment")
        if mat:
            maturity_counts[mat] = maturity_counts.get(mat, 0) + 1
        total_impl += synth.get("implementation_files", 0)
        total_test += synth.get("test_files", 0)
        total_roadmap += synth.get("total_roadmap_signals", 0)
        total_contradictions += 1 if synth.get("contradictions") else 0

    unique_modules = list(dict.fromkeys(all_modules))
    unique_arch = list(dict.fromkeys(all_arch))

    # Report health
    health = client.health_report()

    return {
        "repos_analyzed": len([r for r in results if not r.get("from_prior_run")]),
        "repos_from_prior_run": len([r for r in results if r.get("from_prior_run")]),
        "results": results,
        "portfolio_summary": {
            "unique_modules": unique_modules[:50],
            "unique_architecture_signals": unique_arch[:20],
            "maturity_distribution": maturity_counts,
            "total_implementation_files": total_impl,
            "total_test_files": total_test,
            "total_roadmap_signals": total_roadmap,
            "repos_with_contradictions": total_contradictions,
        },
        "github_health": health,
        "total_api_requests": total_requests,
        "budget_remaining": budget_remaining,
        "timestamp": datetime.now(UTC).isoformat(),
    }
