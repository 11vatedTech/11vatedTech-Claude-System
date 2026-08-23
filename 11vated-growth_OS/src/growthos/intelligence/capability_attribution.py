"""Capability Evidence Attribution Engine.

Determines which exact implementation files, subsystems, and test files
materially prove each commercial capability. Replaces the broad
``related_completed_work`` approach with precise per-file attribution.

A repository being generally relevant is not enough. A file counts as
capability evidence only when its implementation materially contributes
to the behavior represented by that capability.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from growthos.intelligence.local_semantic import (
    FileAnalysis,
    ImplementationGraph,
    SubsystemProfile,
)

# ---------------------------------------------------------------------------
# Capability definitions — what evidence each capability requires
# ---------------------------------------------------------------------------


@dataclass
class CapabilityDefinition:
    """Defines what evidence qualifies for a specific capability."""

    name: str
    buyer_problem: str
    # Subsystem categories that DIRECTLY implement this capability's core behavior
    core_subsystems: list[str] = field(default_factory=list)
    # File path patterns that indicate direct implementation of this capability
    core_file_patterns: list[str] = field(default_factory=list)
    # File path patterns that indicate SUPPORTING (not core) implementation
    supporting_file_patterns: list[str] = field(default_factory=list)
    # File path patterns that are EXCLUDED from this capability's evidence
    excluded_file_patterns: list[str] = field(default_factory=list)
    # Subsystem categories that are SUPPORTING but not core
    supporting_subsystems: list[str] = field(default_factory=list)
    # Architecture signals that contribute to this capability
    core_architecture_signals: list[str] = field(default_factory=list)
    # Languages that are primary for this capability
    primary_languages: list[str] = field(default_factory=list)
    # Minimum impl files for DIRECT_SUPPORTING (not just CONTEXT_ONLY)
    min_impl_for_supporting: int = 2
    # Commercial forms this capability can take
    commercial_forms: list[str] = field(default_factory=list)
    # What this capability explicitly does NOT cover
    explicit_limitations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Capability Definitions
# ---------------------------------------------------------------------------

CAPABILITY_DEFINITIONS: list[CapabilityDefinition] = [
    CapabilityDefinition(
        name="Interactive Sprite Runtime & Behavior Prototyping",
        buyer_problem="Studio needs custom sprite/character runtime with stateful behavior, transformations, and interactive prototypes",
        core_subsystems=["game_runtime"],
        core_file_patterns=["sprite", "entity", "game", "render", "behavior"],
        supporting_file_patterns=["transform", "state_machine", "animation", "interaction"],
        excluded_file_patterns=["node_modules", "dist", "build"],
        core_architecture_signals=[],
        primary_languages=[],
        commercial_forms=["prototype_engagement", "r_and_d_engagement", "character_system_prototyping"],
        explicit_limitations=[
            "Not full game development",
            "Not production middleware guarantees",
            "Not AAA pipeline integration",
            "Not broad engine support",
            "Not production-scale licensing",
        ],
    ),
    CapabilityDefinition(
        name="Local AI & Autonomous Agent Systems",
        buyer_problem="Organization needs local-first AI agent systems with planning, tool use, memory, and autonomous execution",
        # Core: only the actual AI agent subsystems
        core_subsystems=["agent_loop", "ollama", "planner"],
        core_file_patterns=["agent_loop", "agent_runner", "agent_executor", "ollama", "llm_client", "model_client"],
        supporting_file_patterns=["tool_registry", "tool_manager", "memory", "context_store", "model_router", "model_selector", "permission", "diff_system", "conversation", "session"],
        excluded_file_patterns=["node_modules", "dist", "build", "sprite", "game", "motion", "sensor"],
        supporting_subsystems=["executor", "tool_registry", "memory", "model_router", "permissions", "diff", "hooks", "conversation", "cli"],
        primary_languages=["Python"],
        commercial_forms=["local_ai_agent_development", "autonomous_system_prototyping", "ai_tool_integration"],
        explicit_limitations=[
            "Not cloud-hosted SaaS",
            "Not large-scale ML training",
            "Not production NLP pipelines",
        ],
    ),
    CapabilityDefinition(
        name="Multi-Device Interactive Experience Prototyping",
        buyer_problem="Studio needs motion-controlled interactive experience across phone+receiver+browser with safe-zone and accessibility",
        # Core: ONLY motion/sensor/tracking — nothing else
        core_subsystems=["motion"],
        core_file_patterns=["motion", "sensor", "tracking", "gesture", "safe_zone", "guardian", "pairing", "phone_client", "receiver"],
        supporting_file_patterns=["game_state", "latency", "diagnostic", "packet", "a11y", "adaptive_interface"],
        excluded_file_patterns=["node_modules", "dist", "build", "agent", "ollama", "llm", "model", "permission", "auth"],
        supporting_subsystems=["game_runtime"],
        primary_languages=["TypeScript", "JavaScript"],
        commercial_forms=["multi_device_prototyping", "interactive_experience_r_and_d"],
        explicit_limitations=[
            "Not full VR/AR production",
            "Not commercial hardware manufacturing",
            "Not large-scale multiplayer",
        ],
    ),
    CapabilityDefinition(
        name="Developer Tooling & Code Intelligence Systems",
        buyer_problem="Team needs AI-powered developer tools: code editing, project intelligence, diff workflows, workspace analysis",
        core_subsystems=["agent_loop", "diff", "tool_registry", "planner"],
        core_file_patterns=["diff", "patch", "code_edit", "workspace", "project_intelligence"],
        supporting_file_patterns=["file_mutation", "git_tooling", "test_runner", "code_generation"],
        excluded_file_patterns=["node_modules", "dist", "build", "sprite", "game", "motion", "sensor"],
        supporting_subsystems=["memory", "model_router", "permissions", "cli"],
        core_architecture_signals=["api_surface", "event_system"],
        primary_languages=["Python", "TypeScript"],
        commercial_forms=["ai_developer_tool_prototyping", "code_intelligence_systems"],
        explicit_limitations=[
            "Not full IDE development",
            "Not production code generation SaaS",
            "Not enterprise DevOps platform",
        ],
    ),
    CapabilityDefinition(
        name="Technical Asset Processing Pipeline Development",
        buyer_problem="Organization needs custom asset processing pipelines: graph execution, scheduling, tensor management, media orchestration",
        core_subsystems=["tensor", "scheduler", "pipeline"],
        core_file_patterns=["tensor", "graph_exec", "scheduler", "pipeline", "asset", "media", "compute"],
        supporting_file_patterns=["metrics", "inference", "cache", "queue"],
        excluded_file_patterns=["node_modules", "dist", "build", "agent", "ollama", "sprite", "game"],
        supporting_subsystems=["api", "database"],
        primary_languages=["Python", "Rust"],
        commercial_forms=["asset_pipeline_prototyping", "processing_system_r_and_d"],
        explicit_limitations=[
            "Not GPU runtime production",
            "Not full SpriteForge production",
            "Not media distribution platform",
        ],
    ),
    CapabilityDefinition(
        name="Business Workflow & Commercial Intelligence Software",
        buyer_problem="Business needs custom workflow automation, opportunity scoring, outreach management, and commercial intelligence systems",
        core_subsystems=["api", "database", "pipeline", "scheduler"],
        core_file_patterns=["workflow", "opportunity", "outreach", "business", "commercial", "intelligence", "prospect", "campaign"],
        supporting_file_patterns=["scoring", "discovery", "enrichment", "qualification"],
        excluded_file_patterns=["node_modules", "dist", "build", "agent", "ollama", "sprite", "game", "motion", "sensor"],
        supporting_subsystems=["event_system", "hooks", "cli"],
        core_architecture_signals=["api_surface", "database", "authentication", "pipeline", "scheduler"],
        primary_languages=["Python", "TypeScript"],
        commercial_forms=["business_workflow_systems", "commercial_intelligence_prototyping"],
        explicit_limitations=[
            "Not enterprise CRM replacement",
            "Not large-scale data warehouse",
            "Not production marketing automation SaaS",
        ],
    ),
]


# ---------------------------------------------------------------------------
# File → Capability attribution logic
# ---------------------------------------------------------------------------


def _file_matches_pattern(file_path: str, patterns: list[str]) -> bool:
    """Check if a file path matches any of the given patterns."""
    path_lower = file_path.lower()
    return any(pat.lower() in path_lower for pat in patterns)


def _is_excluded(file_path: str, excluded: list[str]) -> bool:
    """Check if a file is excluded from evidence."""
    return _file_matches_pattern(file_path, excluded)


def _classify_file_attribution(
    file_analysis: FileAnalysis,
    capability: CapabilityDefinition,
) -> tuple[str, float, str]:
    """Classify a single file's attribution to a capability.

    Returns (directness, confidence, reason).
    """
    path = file_analysis.rel_path

    # Excluded files
    if _is_excluded(path, capability.excluded_file_patterns):
        return ("NOT_RELEVANT", 0.0, "File excluded from this capability scope")

    # Build configs → CONTEXT_ONLY if relevant
    if file_analysis.is_build_config:
        if _file_matches_pattern(path, capability.core_file_patterns + capability.supporting_file_patterns):
            return ("CONTEXT_ONLY", 0.1, "Build configuration — provides context but no implementation evidence")
        return ("NOT_RELEVANT", 0.0, "Build config not relevant to this capability")

    # Documentation → CONTEXT_ONLY
    if file_analysis.is_docs:
        if _file_matches_pattern(path, capability.core_file_patterns + capability.supporting_file_patterns):
            return ("CONTEXT_ONLY", 0.1, "Documentation — provides context but no implementation evidence")
        return ("NOT_RELEVANT", 0.0, "Documentation not relevant to this capability")

    # Test files get classified separately
    if file_analysis.is_test_file:
        if _file_matches_pattern(path, capability.core_file_patterns):
            confidence = min(0.8, 0.3 + 0.1 * file_analysis.test_signal_count)
            return ("DIRECT_SUPPORTING", confidence, f"Test file validating core {capability.name} behavior")
        if _file_matches_pattern(path, capability.supporting_file_patterns):
            confidence = min(0.6, 0.2 + 0.1 * file_analysis.test_signal_count)
            return ("INDIRECT_SUPPORTING", confidence, "Test file for supporting subsystem")
        return ("NOT_RELEVANT", 0.0, "Test file not related to this capability")

    # Implementation files
    if file_analysis.impl_signal_count > 0:
        # Core file patterns
        if _file_matches_pattern(path, capability.core_file_patterns):
            confidence = min(0.9, 0.4 + 0.05 * file_analysis.impl_signal_count)
            return ("DIRECT_CORE", confidence, f"Core implementation file for {capability.name}")

        # Supporting file patterns
        if _file_matches_pattern(path, capability.supporting_file_patterns):
            confidence = min(0.7, 0.25 + 0.05 * file_analysis.impl_signal_count)
            return ("DIRECT_SUPPORTING", confidence, f"Supporting implementation for {capability.name}")

        # Check architecture signal alignment
        arch_overlap = set(file_analysis.architecture_signals) & set(capability.core_architecture_signals)
        if arch_overlap and file_analysis.impl_signal_count >= 3:
            confidence = min(0.5, 0.15 + 0.05 * file_analysis.impl_signal_count)
            return ("INDIRECT_SUPPORTING", confidence, f"Architecture signal ({', '.join(arch_overlap)}) relevant to capability")

        # Generic backend file — might be relevant if no other cap claims it more specifically
        if file_analysis.impl_signal_count >= 5 and not capability.primary_languages:
            return ("CONTEXT_ONLY", 0.05, "Generic implementation file — limited capability evidence")

    return ("NOT_RELEVANT", 0.0, "File does not materially contribute to this capability")


def _classify_subsystem_attribution(
    subsystem: SubsystemProfile,
    capability: CapabilityDefinition,
) -> tuple[str, float, str]:
    """Classify a subsystem's attribution to a capability."""
    cat = subsystem.category

    if cat in capability.core_subsystems:
        if subsystem.status == "IMPLEMENTED_AND_TESTED":
            return ("DIRECT_CORE", 0.85, f"Core subsystem '{subsystem.name}' — implemented and tested")
        if subsystem.status == "IMPLEMENTED_UNTESTED":
            return ("DIRECT_CORE", 0.65, f"Core subsystem '{subsystem.name}' — implemented but untested")
        if subsystem.status == "IMPLEMENTED_PARTIAL_TEST":
            return ("DIRECT_CORE", 0.75, f"Core subsystem '{subsystem.name}' — implemented with partial test coverage")
        return ("DIRECT_SUPPORTING", 0.4, f"Core subsystem '{subsystem.name}' — partially present")

    if cat in capability.supporting_subsystems:
        if subsystem.status in ("IMPLEMENTED_AND_TESTED", "IMPLEMENTED_PARTIAL_TEST"):
            return ("DIRECT_SUPPORTING", 0.5, f"Supporting subsystem '{subsystem.name}' — implemented")
        return ("INDIRECT_SUPPORTING", 0.25, f"Supporting subsystem '{subsystem.name}' — partial presence")

    # Check if any core keywords match the subsystem name/category
    for core_sys in capability.core_subsystems:
        if core_sys in cat or cat in core_sys:
            return ("INDIRECT_SUPPORTING", 0.2, f"Subsystem '{subsystem.name}' has keyword overlap with core subsystems")

    return ("NOT_RELEVANT", 0.0, f"Subsystem '{subsystem.name}' not relevant to this capability")


# ---------------------------------------------------------------------------
# Per-repository attribution
# ---------------------------------------------------------------------------


@dataclass
class FileAttribution:
    """Attribution of one file to one capability."""
    file_path: str
    subsystem: str | None
    evidence_type: str
    directness: str
    reason: str
    confidence: float
    symbol_name: str | None = None
    language: str | None = None
    line_count: int = 0
    has_validating_test: bool = False
    validating_test_path: str | None = None
    validates_subsystem: str | None = None


@dataclass
class CapabilityAttributionResult:
    """Complete attribution result for one capability from one repository."""
    capability_name: str
    repository: str
    branch: str | None = None
    commit_sha: str | None = None
    # File-level attributions
    file_attributions: list[FileAttribution] = field(default_factory=list)
    # Summary counts
    direct_core_count: int = 0
    direct_supporting_count: int = 0
    indirect_supporting_count: int = 0
    context_only_count: int = 0
    not_relevant_count: int = 0
    # Test attributions
    test_attributions: list[FileAttribution] = field(default_factory=list)
    attributed_test_count: int = 0
    # Aggregated confidence
    overall_confidence: float = 0.0
    # Subsystem attributions
    subsystem_attributions: list[tuple[str, str, float, str]] = field(default_factory=list)
    # Coverage
    total_repo_files: int = 0
    files_evaluated: int = 0
    files_excluded_as_context: int = 0
    files_excluded_as_irrelevant: int = 0


def _match_test_to_impl(
    test_path: str,
    impl_files: list[str],
    capability: CapabilityDefinition,
) -> tuple[bool, str | None, str | None]:
    """Try to match a test file to the implementation file it validates."""
    test_name = os.path.basename(test_path).lower()
    # Remove test prefixes/suffixes
    base_name = re.sub(r"^(test_|_test)", "", test_name)
    base_name = re.sub(r"(_test\.|_spec\.|\.test\.|\.spec\.)", ".", base_name)

    for impl_path in impl_files:
        impl_name = os.path.basename(impl_path).lower()
        # Direct name match (test_foo.py tests foo.py)
        if base_name in impl_name or impl_name.replace(".py", "") in base_name:
            return True, impl_path, None

    # Check directory-level match
    test_dir = os.path.dirname(test_path).lower()
    for impl_path in impl_files:
        impl_dir = os.path.dirname(impl_path).lower()
        if test_dir and impl_dir and (test_dir in impl_dir or impl_dir in test_dir) and _file_matches_pattern(impl_path, capability.core_file_patterns):
                return True, impl_path, None

    return False, None, None


def attribute_repository(
    graph: ImplementationGraph,
    repository_name: str,
    capability: CapabilityDefinition,
    *,
    branch: str | None = None,
    commit_sha: str | None = None,
) -> CapabilityAttributionResult:
    """Attribute files from a repository analysis graph to a specific capability.

    This is the core attribution function. It evaluates every file in the
    repository against the capability definition and classifies each as
    DIRECT_CORE, DIRECT_SUPPORTING, INDIRECT_SUPPORTING, CONTEXT_ONLY,
    or NOT_RELEVANT.
    """
    result = CapabilityAttributionResult(
        capability_name=capability.name,
        repository=repository_name,
        branch=branch,
        commit_sha=commit_sha,
        total_repo_files=len(graph.all_files),
    )

    # Phase 1: Classify subsystems
    for subsystem in graph.subsystems:
        directness, confidence, reason = _classify_subsystem_attribution(subsystem, capability)
        result.subsystem_attributions.append((subsystem.name, directness, confidence, reason))

    # Phase 2: Classify each file
    core_impl_files: list[str] = []

    for fa in graph.file_analyses:
        result.files_evaluated += 1
        directness, confidence, reason = _classify_file_attribution(fa, capability)

        if directness == "NOT_RELEVANT":
            result.not_relevant_count += 1
            continue
        if directness == "CONTEXT_ONLY":
            result.context_only_count += 1
            result.files_excluded_as_context += 1
            continue

        # Track core implementation files for test matching
        if directness == "DIRECT_CORE" and not fa.is_test_file:
            core_impl_files.append(fa.rel_path)

        attr = FileAttribution(
            file_path=fa.rel_path,
            subsystem=None,
            evidence_type="FILE_IMPLEMENTATION" if not fa.is_test_file else "TEST_VALIDATION",
            directness=directness,
            reason=reason,
            confidence=confidence,
            symbol_name=fa.classes[0] if fa.classes else (fa.functions[0] if fa.functions else None),
            language=fa.lang,
            line_count=fa.line_count,
        )

        if directness == "DIRECT_CORE":
            result.direct_core_count += 1
        elif directness == "DIRECT_SUPPORTING":
            result.direct_supporting_count += 1
        elif directness == "INDIRECT_SUPPORTING":
            result.indirect_supporting_count += 1

        if fa.is_test_file:
            result.test_attributions.append(attr)
            result.attributed_test_count += 1
            # Try to match test to implementation
            matched, impl_path, _ = _match_test_to_impl(fa.rel_path, core_impl_files, capability)
            if matched:
                attr.has_validating_test = True
                attr.validating_test_path = impl_path
        else:
            result.file_attributions.append(attr)

    # Phase 3: Match unattributed tests to attributed subsystems
    for subsystem in graph.subsystems:
        directness, confidence, _ = _classify_subsystem_attribution(subsystem, capability)
        if directness in ("DIRECT_CORE", "DIRECT_SUPPORTING"):
            for test_file in subsystem.test_files:
                # Check if this test is already attributed
                already = any(t.file_path == test_file for t in result.test_attributions)
                if not already:
                    attr = FileAttribution(
                        file_path=test_file,
                        subsystem=subsystem.name,
                        evidence_type="TEST_VALIDATION",
                        directness="DIRECT_SUPPORTING",
                        reason=f"Test for attributed subsystem '{subsystem.name}'",
                        confidence=min(0.7, confidence + 0.1),
                        has_validating_test=True,
                        validates_subsystem=subsystem.name,
                    )
                    result.test_attributions.append(attr)
                    result.attributed_test_count += 1
                    result.direct_supporting_count += 1

    # Phase 4: Compute overall confidence
    # Weight: direct core > direct supporting > indirect
    core_weight = 0.5
    support_weight = 0.3
    indirect_weight = 0.15
    test_weight = 0.05

    total_weighted = 0.0
    total_weight = 0.0

    if result.direct_core_count > 0:
        avg_core_conf = sum(
            a.confidence for a in result.file_attributions if a.directness == "DIRECT_CORE"
        ) / max(1, result.direct_core_count)
        total_weighted += avg_core_conf * core_weight
        total_weight += core_weight

    if result.direct_supporting_count > 0:
        avg_sup_conf = sum(
            a.confidence for a in (result.file_attributions + result.test_attributions)
            if a.directness == "DIRECT_SUPPORTING"
        ) / max(1, result.direct_supporting_count)
        total_weighted += avg_sup_conf * support_weight
        total_weight += support_weight

    if result.indirect_supporting_count > 0:
        avg_ind_conf = sum(
            a.confidence for a in result.file_attributions if a.directness == "INDIRECT_SUPPORTING"
        ) / max(1, result.indirect_supporting_count)
        total_weighted += avg_ind_conf * indirect_weight
        total_weight += indirect_weight

    if result.attributed_test_count > 0:
        test_conf = min(0.8, 0.3 + 0.05 * result.attributed_test_count)
        total_weighted += test_conf * test_weight
        total_weight += test_weight

    result.overall_confidence = round(total_weighted / max(0.01, total_weight), 3) if total_weight > 0 else 0.0

    return result


# ---------------------------------------------------------------------------
# Portfolio-level attribution
# ---------------------------------------------------------------------------


@dataclass
class PortfolioAttributionSummary:
    """Aggregated attribution across all repositories for one capability."""
    capability_name: str
    # Per-repo results
    repo_results: list[CapabilityAttributionResult] = field(default_factory=list)
    # Aggregated counts
    total_direct_core: int = 0
    total_direct_supporting: int = 0
    total_indirect_supporting: int = 0
    total_context_only: int = 0
    total_not_relevant: int = 0
    total_attributed_tests: int = 0
    total_validating_tests: int = 0
    # Independent repos with direct core evidence
    independent_core_repos: int = 0
    # Overall
    overall_confidence: float = 0.0
    # What evidence the founder sees
    evidence_numerator: str = ""
    evidence_denominator: str = ""


def attribute_portfolio(
    repo_graphs: dict[str, tuple[ImplementationGraph, str | None, str | None]],
    capability: CapabilityDefinition,
) -> PortfolioAttributionSummary:
    """Attribute an entire portfolio to one capability.

    Args:
        repo_graphs: {repo_name: (graph, branch, commit_sha)}
        capability: The capability definition to attribute against
    """
    summary = PortfolioAttributionSummary(capability_name=capability.name)

    for repo_name, (graph, branch, sha) in repo_graphs.items():
        result = attribute_repository(
            graph, repo_name, capability,
            branch=branch, commit_sha=sha,
        )
        summary.repo_results.append(result)

        summary.total_direct_core += result.direct_core_count
        summary.total_direct_supporting += result.direct_supporting_count
        summary.total_indirect_supporting += result.indirect_supporting_count
        summary.total_context_only += result.context_only_count
        summary.total_not_relevant += result.not_relevant_count
        summary.total_attributed_tests += result.attributed_test_count
        summary.total_validating_tests += sum(
            1 for t in result.test_attributions if t.has_validating_test
        )

        if result.direct_core_count > 0:
            summary.independent_core_repos += 1

    # Overall confidence: average of repos with direct core evidence, weighted
    repos_with_core = [r for r in summary.repo_results if r.direct_core_count > 0]
    if repos_with_core:
        summary.overall_confidence = round(
            sum(r.overall_confidence for r in repos_with_core) / len(repos_with_core), 3
        )
    else:
        # No direct core evidence — confidence from supporting only
        repos_with_support = [r for r in summary.repo_results if r.direct_supporting_count > 0]
        if repos_with_support:
            summary.overall_confidence = round(
                sum(r.overall_confidence for r in repos_with_support) / len(repos_with_support) * 0.5, 3
            )

    # Build evidence numerator/denominator
    total_evaluated = (
        summary.total_direct_core + summary.total_direct_supporting
        + summary.total_indirect_supporting + summary.total_context_only
        + summary.total_not_relevant
    )
    summary.evidence_numerator = (
        f"Direct core: {summary.total_direct_core} files | "
        f"Direct supporting: {summary.total_direct_supporting} files | "
        f"Indirect: {summary.total_indirect_supporting} files | "
        f"Attributed tests: {summary.total_attributed_tests} | "
        f"Validating tests: {summary.total_validating_tests} | "
        f"Independent repos with core evidence: {summary.independent_core_repos}"
    )
    summary.evidence_denominator = (
        f"Total files evaluated: {total_evaluated} | "
        f"Context-only excluded: {summary.total_context_only} | "
        f"Not relevant excluded: {summary.total_not_relevant} | "
        f"Repos analyzed: {len(summary.repo_results)}"
    )

    return summary
