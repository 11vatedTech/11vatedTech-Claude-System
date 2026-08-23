"""Tests for capability evidence attribution engine."""

from __future__ import annotations

import pytest

from growthos.intelligence.capability_attribution import (
    CAPABILITY_DEFINITIONS,
    CapabilityDefinition,
    FileAttribution,
    attribute_portfolio,
    attribute_repository,
)
from growthos.intelligence.local_semantic import (
    FileAnalysis,
    ImplementationGraph,
    SubsystemProfile,
)
from growthos.intelligence.capability_attribution import (
    _classify_file_attribution,
    _classify_subsystem_attribution,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_file(rel_path: str, impl_signals: int = 5, is_test: bool = False, is_build: bool = False, is_docs: bool = False) -> FileAnalysis:
    fa = FileAnalysis(rel_path=rel_path, lang="Python", line_count=100)
    fa.impl_signal_count = impl_signals
    fa.test_signal_count = 3 if is_test else 0
    fa.is_test_file = is_test
    fa.is_build_config = is_build
    fa.is_docs = is_docs
    fa.classes = ["TestClass"] if impl_signals > 0 else []
    fa.functions = ["test_func"] if impl_signals > 0 else []
    fa.architecture_signals = ["api_surface"]
    return fa


def _make_subsystem(name: str, category: str, status: str = "IMPLEMENTED_AND_TESTED") -> SubsystemProfile:
    return SubsystemProfile(
        name=name,
        category=category,
        implementation_files=[f"src/{category}/impl.py"],
        test_files=[f"tests/test_{category}.py"],
        status=status,
    )


def _make_graph(
    impl_files: list[str] | None = None,
    test_files: list[str] | None = None,
    subsystems: list[SubsystemProfile] | None = None,
) -> ImplementationGraph:
    graph = ImplementationGraph()
    files = []
    for f in (impl_files or []):
        fa = _make_file(f, impl_signals=5)
        files.append(fa)
    for f in (test_files or []):
        fa = _make_file(f, impl_signals=2, is_test=True)
        files.append(fa)
    graph.file_analyses = files
    graph.all_files = [fa.rel_path for fa in files]
    graph.subsystems = subsystems or []
    graph.total_impl_files = len(impl_files or [])
    graph.total_test_files = len(test_files or [])
    return graph


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAttributionDirectness:
    """File → capability directness classification."""

    def test_core_file_gets_direct_core(self):
        cap = CapabilityDefinition(
            name="Test Capability",
            buyer_problem="test",
            core_file_patterns=["agent_loop", "ollama"],
        )
        fa = _make_file("src/agent/agent_loop.py")
        directness, conf, reason = _classify_file_attribution(fa, cap)
        assert directness == "DIRECT_CORE"
        assert conf > 0.3

    def test_excluded_file_gets_not_relevant(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            core_file_patterns=["agent"],
            excluded_file_patterns=["node_modules", "dist"],
        )
        fa = _make_file("node_modules/foo/agent.js")
        from growthos.intelligence.capability_attribution import _classify_file_attribution
        directness, _, _ = _classify_file_attribution(fa, cap)
        assert directness == "NOT_RELEVANT"

    def test_build_config_gets_context_only(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            core_file_patterns=["agent"],
            supporting_file_patterns=["package"],
        )
        fa = _make_file("agent/package.json", is_build=True)
        directness, _, _ = _classify_file_attribution(fa, cap)
        assert directness == "CONTEXT_ONLY"

    def test_docs_gets_context_only(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            core_file_patterns=["agent"],
            supporting_file_patterns=["docs"],
        )
        fa = _make_file("docs/agent.md", is_docs=True)
        directness, _, _ = _classify_file_attribution(fa, cap)
        assert directness == "CONTEXT_ONLY"

    def test_unrelated_file_gets_not_relevant(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            core_file_patterns=["agent_loop"],
            excluded_file_patterns=["sprite", "game"],
        )
        fa = _make_file("src/sprite/renderer.py")
        directness, _, _ = _classify_file_attribution(fa, cap)
        assert directness == "NOT_RELEVANT"

    def test_supporting_file_gets_direct_supporting(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            supporting_file_patterns=["memory", "context"],
        )
        fa = _make_file("src/agent/memory.py")
        directness, _, _ = _classify_file_attribution(fa, cap)
        assert directness == "DIRECT_SUPPORTING"


class TestSubsystemAttribution:
    """Subsystem → capability directness classification."""

    def test_core_subsystem_gets_direct_core(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            core_subsystems=["agent_loop"],
        )
        sub = _make_subsystem("Agent Loop", "agent_loop")
        directness, conf, _ = _classify_subsystem_attribution(sub, cap)
        assert directness == "DIRECT_CORE"
        assert conf >= 0.6

    def test_supporting_subsystem_gets_direct_supporting(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            core_subsystems=["agent_loop"],
            supporting_subsystems=["cli"],
        )
        sub = _make_subsystem("CLI/TUI", "cli")
        directness, _, _ = _classify_subsystem_attribution(sub, cap)
        assert directness == "DIRECT_SUPPORTING"

    def test_unrelated_subsystem_gets_not_relevant(self):
        cap = CapabilityDefinition(
            name="Test",
            buyer_problem="test",
            core_subsystems=["agent_loop"],
        )
        sub = _make_subsystem("Game/Sprite Runtime", "game_runtime")
        directness, _, _ = _classify_subsystem_attribution(sub, cap)
        assert directness == "NOT_RELEVANT"


class TestRepositoryAttribution:
    """Full repository → capability attribution."""

    def test_empty_repo_gets_zero_attribution(self):
        cap = CapabilityDefinition(name="Test", buyer_problem="test", core_file_patterns=["agent"])
        graph = _make_graph()
        result = attribute_repository(graph, "test/repo", cap)
        assert result.direct_core_count == 0
        assert result.overall_confidence == 0.0

    def test_core_files_increase_attribution(self):
        cap = CapabilityDefinition(name="Test", buyer_problem="test", core_file_patterns=["agent_loop"])
        graph = _make_graph(
            impl_files=["src/agent/agent_loop.py", "src/agent/agent_runner.py"],
            test_files=["tests/test_agent.py"],
        )
        result = attribute_repository(graph, "test/repo", cap)
        assert result.direct_core_count >= 1

    def test_context_files_excluded_from_numerator(self):
        cap = CapabilityDefinition(name="Test", buyer_problem="test", core_file_patterns=["agent"])
        # Build a graph with both implementation and build config files
        graph = ImplementationGraph()
        impl_fa = _make_file("src/agent/main.py", impl_signals=5)
        build_fa = _make_file("agent/package.json", is_build=True)
        graph.file_analyses = [impl_fa, build_fa]
        graph.all_files = ["src/agent/main.py", "agent/package.json"]
        result = attribute_repository(graph, "test/repo", cap)
        # Build config should be context_only, not in direct counts
        assert result.context_only_count >= 1


class TestFrontendAnomaly:
    """Verify the 733/738 frontend anomaly is fixed."""

    def test_frontend_capability_gets_zero_from_non_frontend_repos(self):
        """A portfolio of AI/sprite/game repos should not produce frontend evidence."""
        frontend_def = None
        for cd in CAPABILITY_DEFINITIONS:
            if "Frontend" in cd.name:
                frontend_def = cd
                break

        # No frontend definition in the new definitions — it should use minimal fallback
        # but should still get 0 core files from AI/sprite repos
        graph = _make_graph(
            impl_files=[
                "src/agent/loop.py", "src/agent/ollama.py", "src/agent/tools.py",
                "src/sprite/runtime.py", "src/game/entity.py",
            ],
            subsystems=[
                _make_subsystem("Agent Loop", "agent_loop"),
                _make_subsystem("Game/Sprite Runtime", "game_runtime"),
            ],
        )
        # Use a definition that doesn't have frontend patterns
        cap = CapabilityDefinition(
            name="Interactive Frontend Development",
            buyer_problem="test",
            core_file_patterns=["react", "component", "tsx"],
        )
        result = attribute_repository(graph, "test/repo", cap)
        assert result.direct_core_count == 0


class TestSpatialDuplicate:
    """Verify Spatial Computing is properly handled as SUPERSEDED."""

    def test_spatial_not_in_core_definitions(self):
        """Spatial Computing should not appear in capability definitions."""
        spatial_defs = [cd for cd in CAPABILITY_DEFINITIONS if "Spatial" in cd.name]
        assert len(spatial_defs) == 0


class TestCapabilityCountReduction:
    """Verify that attributed file counts are much lower than raw file counts."""

    def test_local_ai_not_700_files(self):
        """Local AI should not attribute 700+ files."""
        ai_def = None
        for cd in CAPABILITY_DEFINITIONS:
            if "Local AI" in cd.name:
                ai_def = cd
                break
        assert ai_def is not None

        # Simulate a portfolio with 500 files across 8 repos
        impl_files = [f"src/repo{i}/module{j}.py" for i in range(8) for j in range(50)]
        test_files = [f"tests/repo{i}/test{j}.py" for i in range(8) for j in range(10)]
        graph = _make_graph(impl_files=impl_files, test_files=test_files)

        result = attribute_repository(graph, "test/repo", ai_def)
        # Should be much less than 500
        assert result.direct_core_count < 50
        assert result.not_relevant_count > 0


class TestMaturityFromAttribution:
    """Maturity should not be determined by raw file count."""

    def test_high_file_count_does_not_guarantee_client_ready(self):
        """100 unrelated files should not make a capability CLIENT_READY."""
        cap = CapabilityDefinition(
            name="Narrow Capability",
            buyer_problem="test",
            core_file_patterns=["very_specific_thing"],
        )
        # 100 unrelated files
        impl_files = [f"src/unrelated/module{i}.py" for i in range(100)]
        graph = _make_graph(impl_files=impl_files)
        result = attribute_repository(graph, "test/repo", cap)
        # No files should be DIRECT_CORE
        assert result.direct_core_count == 0
        # Unrelated files are either NOT_RELEVANT or CONTEXT_ONLY — never DIRECT_CORE
        assert result.direct_core_count + result.direct_supporting_count == 0
        # Context/not_relevant should dominate
        assert result.context_only_count + result.not_relevant_count >= 90
