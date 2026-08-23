"""Tests for Evidence Mirror — safety, path escape, lifecycle, Git non-mutation."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from growthos.intelligence.evidence_mirror import (
    _detect_source_roots,
    _validate_mirror_path,
    _validate_not_source_tree,
    _validate_owner_repo,
)
from growthos.intelligence.local_semantic import (
    FileAnalysis,
    _detect_architecture,
    _detect_entry_points,
    _detect_lang,
    _is_build_config,
    _is_docs,
    _is_test_path,
    analyze_file,
    compute_graph_confidence,
)

# ---------------------------------------------------------------------------
# Mirror safety tests
# ---------------------------------------------------------------------------


class TestOwnerRepoValidation:
    def test_valid_owner_repo(self):
        """Valid owner/repo passes."""
        _validate_owner_repo("11vatedTech", "Nexus")

    def test_slash_in_owner_rejected(self):
        """Owner with slash is rejected (path escape)."""
        with pytest.raises(ValueError, match="Invalid owner"):
            _validate_owner_repo("evil/owner", "repo")

    def test_backslash_in_owner_rejected(self):
        with pytest.raises(ValueError, match="Invalid owner"):
            _validate_owner_repo("evil\\owner", "repo")

    def test_dotdot_in_owner_rejected(self):
        with pytest.raises(ValueError, match="Invalid owner"):
            _validate_owner_repo("..", "repo")

    def test_slash_in_repo_rejected(self):
        with pytest.raises(ValueError, match="Invalid repo"):
            _validate_owner_repo("owner", "evil/repo")

    def test_backslash_in_repo_rejected(self):
        with pytest.raises(ValueError, match="Invalid repo"):
            _validate_owner_repo("owner", "evil\\repo")

    def test_dotdot_in_repo_rejected(self):
        with pytest.raises(ValueError, match="Invalid repo"):
            _validate_owner_repo("owner", "..")


class TestMirrorPathValidation:
    def test_path_under_root_passes(self, tmp_path):
        """A path under the mirror root passes."""
        root = tmp_path / "mirrors"
        root.mkdir()
        mirror_path = root / "github" / "owner" / "repo"
        mirror_path.mkdir(parents=True)
        # Patch _mirror_root to return our tmp root
        with patch("growthos.intelligence.evidence_mirror._mirror_root", return_value=root):
            _validate_mirror_path(mirror_path)

    def test_path_escape_rejected(self, tmp_path):
        """A path outside the mirror root is rejected."""
        root = tmp_path / "mirrors"
        root.mkdir()
        escape_path = tmp_path / "evil" / "path"
        escape_path.mkdir(parents=True)
        with patch("growthos.intelligence.evidence_mirror._mirror_root", return_value=root), pytest.raises(ValueError, match="escapes root"):
                _validate_mirror_path(escape_path)


class TestSourceTreeValidation:
    def test_source_tree_path_rejected(self, tmp_path):
        """A path inside the GrowthOS source tree is rejected."""
        with patch("growthos.intelligence.evidence_mirror.Path.cwd", return_value=tmp_path):
            # Create a path that is inside cwd
            inner_path = tmp_path / "subdir"
            inner_path.mkdir()
            with pytest.raises(ValueError, match="inside GrowthOS source tree"):
                _validate_not_source_tree(inner_path)


class TestSourceRootDetection:
    def test_detects_src_as_root(self):
        files = ["src/main.py", "src/utils.py", "src/core.py", "README.md"]
        roots = _detect_source_roots(files)
        assert "src" in roots

    def test_detects_multiple_roots(self):
        files = [
            "src/a.py", "src/b.py", "src/c.py",
            "lib/x.rs", "lib/y.rs",
            "test/t1.py",
        ]
        roots = _detect_source_roots(files)
        assert "src" in roots
        assert "lib" in roots

    def test_ignores_hidden_dirs(self):
        files = [".git/config", ".github/workflows/ci.yml"]
        roots = _detect_source_roots(files)
        assert ".git" not in roots
        assert ".github" not in roots

    def test_empty_files(self):
        assert _detect_source_roots([]) == []


class TestLanguageDetection:
    def test_python(self):
        assert _detect_lang("src/main.py") == "Python"

    def test_typescript(self):
        assert _detect_lang("src/app.ts") == "TypeScript"

    def test_rust(self):
        assert _detect_lang("src/lib.rs") == "Rust"

    def test_unknown(self):
        assert _detect_lang("README") == "Unknown"

    def test_csharp(self):
        assert _detect_lang("Program.cs") == "C#"

    def test_cpp(self):
        assert _detect_lang("main.cpp") == "C++"


# ---------------------------------------------------------------------------
# File path classification tests
# ---------------------------------------------------------------------------


class TestFilePathClassification:
    def test_test_path_detection(self):
        assert _is_test_path("tests/test_main.py")
        assert _is_test_path("src/test_utils.py")
        assert _is_test_path("src/utils.test.ts")
        assert _is_test_path("src/utils.spec.ts")
        assert not _is_test_path("src/main.py")

    def test_build_config_detection(self):
        assert _is_build_config("package.json")
        assert _is_build_config("pyproject.toml")
        assert _is_build_config("Cargo.toml")
        assert _is_build_config("Makefile")
        assert _is_build_config("Dockerfile")
        assert _is_build_config(".github/workflows/ci.yml")
        assert not _is_build_config("src/main.py")

    def test_docs_detection(self):
        assert _is_docs("README.md")
        assert _is_docs("docs/architecture.rst")
        assert _is_docs("CHANGELOG.txt")
        assert not _is_docs("src/main.py")


# ---------------------------------------------------------------------------
# Entry point detection
# ---------------------------------------------------------------------------


class TestEntryPointDetection:
    def test_python_main(self):
        assert _detect_entry_points('if __name__ == "__main__":\n    main()')

    def test_js_export_default(self):
        assert _detect_entry_points("export default function main() {}")

    def test_rust_main(self):
        assert _detect_entry_points("fn main() {")

    def test_go_main(self):
        assert _detect_entry_points("func main() {}")

    def test_no_entry_point(self):
        assert not _detect_entry_points("x = 1\nprint(x)")


# ---------------------------------------------------------------------------
# Architecture signal detection
# ---------------------------------------------------------------------------


class TestArchitectureDetection:
    def test_api_surface(self):
        signals = _detect_architecture("router = Router()\napp.add_route('/api/v1', handler)", "api.py")
        assert "api_surface" in signals

    def test_database(self):
        signals = _detect_architecture("from sqlalchemy import create_engine\ndb = connect()", "db.py")
        assert "database" in signals

    def test_event_system(self):
        signals = _detect_architecture("event_emitter.emit('data', payload)", "events.py")
        assert "event_system" in signals

    def test_pipeline(self):
        signals = _detect_architecture("pipeline = Pipeline([step1, step2])", "pipeline.py")
        assert "pipeline" in signals

    def test_no_signals(self):
        signals = _detect_architecture("x = 42\nprint(x)", "simple.py")
        assert len(signals) == 0


# ---------------------------------------------------------------------------
# Python AST parsing
# ---------------------------------------------------------------------------


class TestPythonASTParsing:
    def test_classes_and_functions(self):
        content = """
class MyClass:
    def method(self):
        pass

async def async_func():
    pass

def regular_func():
    pass
"""
        analysis = analyze_file("test.py", content)
        assert "MyClass" in analysis.classes
        assert "method" in analysis.functions
        assert "async_func" in analysis.async_functions
        assert "regular_func" in analysis.functions
        assert analysis.impl_signal_count >= 3

    def test_imports_detected(self):
        content = """
import os
from pathlib import Path
from growthos.config import get_settings
"""
        analysis = analyze_file("test.py", content)
        assert "os" in analysis.imports
        assert "pathlib" in analysis.imports
        assert "growthos.config" in analysis.imports

    def test_syntax_error_handled(self):
        content = "def broken(\n    invalid syntax here"
        analysis = analyze_file("test.py", content)
        assert analysis.classes == []
        assert analysis.functions == []


# ---------------------------------------------------------------------------
# Generic parsing
# ---------------------------------------------------------------------------


class TestGenericParsing:
    def test_typescript_classes(self):
        content = """
class MyComponent extends React.Component {
    render() { return <div/>; }
}
const myFunc = () => {};
"""
        analysis = analyze_file("Component.tsx", content)
        assert "MyComponent" in analysis.classes
        assert "myFunc" in analysis.functions

    def test_rust_structs(self):
        content = """
pub struct MyStruct {
    field: i32,
}
pub fn my_fn() {}
"""
        analysis = analyze_file("lib.rs", content)
        assert "MyStruct" in analysis.classes
        assert "my_fn" in analysis.functions

    def test_go_functions(self):
        content = """
func main() {}
func helper() {}
"""
        analysis = analyze_file("main.go", content)
        assert "main" in analysis.functions
        assert "helper" in analysis.functions

    def test_csharp_classes(self):
        content = """
public class MyService {
    public void DoWork() {}
}
"""
        analysis = analyze_file("Service.cs", content)
        assert "MyService" in analysis.classes


# ---------------------------------------------------------------------------
# Roadmap/contradiction detection
# ---------------------------------------------------------------------------


class TestRoadmapDetection:
    def test_roadmap_heavy_file(self):
        content = """
# TODO: implement this
# Will be available in phase 2
# Planned feature: advanced analytics
# Coming soon: mobile support
# Future: multi-tenant
"""
        analysis = analyze_file("docs/roadmap.md", content)
        assert analysis.roadmap_signal_count >= 3

    def test_implementation_heavy_file(self):
        content = """
class ServiceA:
    def run(self):
        pass

class ServiceB:
    def process(self):
        pass

class ServiceC:
    def validate(self):
        pass

def helper_one():
    pass

def helper_two():
    pass
"""
        analysis = analyze_file("core/service.py", content)
        assert analysis.impl_signal_count >= 5


# ---------------------------------------------------------------------------
# Evidence class classification
# ---------------------------------------------------------------------------


class TestEvidenceClassification:
    def test_impl_file_has_direct_implementation(self):
        content = """
class MyClass:
    def method(self):
        pass

def func():
    pass

class Another:
    pass
"""
        analysis = analyze_file("src/core.py", content)
        assert "DIRECT_IMPLEMENTATION" in analysis.evidence_classes

    def test_test_file_with_framework(self):
        content = """
import pytest

def test_something():
    assert True

def test_another():
    expect(1).toBe(1)
"""
        analysis = analyze_file("tests/test_core.py", content)
        assert "TEST_EVIDENCE" in analysis.evidence_classes

    def test_build_config(self):
        content = '{"name": "my-app", "scripts": {"build": "tsc"}}'
        analysis = analyze_file("package.json", content)
        assert "BUILD_EVIDENCE" in analysis.evidence_classes


# ---------------------------------------------------------------------------
# Confidence computation
# ---------------------------------------------------------------------------


class TestConfidenceComputation:
    def test_empty_graph(self):
        from growthos.intelligence.local_semantic import ImplementationGraph
        graph = ImplementationGraph()
        conf = compute_graph_confidence(graph)
        assert conf["implementation"] == 0.0
        assert conf["testing"] == 0.0
        assert conf["build"] == 0.0
        assert conf["runtime"] == 0.0

    def test_rich_graph(self):
        from growthos.intelligence.local_semantic import (
            ImplementationGraph,
        )
        graph = ImplementationGraph()
        graph.total_impl_files = 10
        graph.total_test_files = 8
        graph.total_build_files = 3
        graph.entry_points = ["src/main.py"]
        graph.file_analyses = [
            FileAnalysis(rel_path="api.py", lang="Python",
                         architecture_signals=["api_surface", "database"]),
        ]
        conf = compute_graph_confidence(graph)
        assert conf["implementation"] > 0.5
        assert conf["testing"] > 0.5
        assert conf["build"] > 0.0
        assert conf["runtime"] > 0.0

    def test_impl_only_no_tests(self):
        from growthos.intelligence.local_semantic import ImplementationGraph
        graph = ImplementationGraph()
        graph.total_impl_files = 5
        graph.total_test_files = 0
        graph.total_build_files = 0
        conf = compute_graph_confidence(graph)
        assert conf["testing"] == 0.0
        assert conf["build"] == 0.0


# ---------------------------------------------------------------------------
# Subsystem detection
# ---------------------------------------------------------------------------


class TestSubsystemDetection:
    def test_agent_loop_detected(self):
        from growthos.intelligence.local_semantic import (
            ImplementationGraph,
        )
        graph = ImplementationGraph()
        graph.file_analyses = [
            FileAnalysis(
                rel_path="src/agent/loop.py", lang="Python",
                classes=["AgentLoop"], functions=["run_loop"],
                impl_signal_count=5, is_test_file=False,
            ),
            FileAnalysis(
                rel_path="tests/test_agent.py", lang="Python",
                classes=["TestAgentLoop"], functions=["test_run_loop"],
                impl_signal_count=2, is_test_file=True,
            ),
        ]
        from growthos.intelligence.local_semantic import _detect_subsystems
        subsystems = _detect_subsystems(graph)
        agent_subs = [s for s in subsystems if s.category == "agent_loop"]
        assert len(agent_subs) == 1
        assert agent_subs[0].status == "IMPLEMENTED_AND_TESTED"

    def test_ollama_detected(self):
        from growthos.intelligence.local_semantic import (
            ImplementationGraph,
            _detect_subsystems,
        )
        graph = ImplementationGraph()
        graph.file_analyses = [
            FileAnalysis(
                rel_path="src/ai/ollama_client.py", lang="Python",
                classes=["OllamaClient"], functions=["query"],
                impl_signal_count=3, is_test_file=False,
            ),
        ]
        subsystems = _detect_subsystems(graph)
        ollama_subs = [s for s in subsystems if s.category == "ollama"]
        assert len(ollama_subs) == 1
        assert ollama_subs[0].status == "IMPLEMENTED_UNTESTED"

    def test_no_subsystems_for_empty_graph(self):
        from growthos.intelligence.local_semantic import (
            ImplementationGraph,
            _detect_subsystems,
        )
        graph = ImplementationGraph()
        graph.file_analyses = []
        subsystems = _detect_subsystems(graph)
        assert len(subsystems) == 0# ---------------------------------------------------------------------------
# Git non-mutation verification
# ---------------------------------------------------------------------------


class TestGitNonMutation:
    @pytest.mark.asyncio
    async def test_verify_no_push_reflog_clean(self):
        """A clean reflog (no push) passes mutation check."""
        from growthos.intelligence.evidence_mirror import verify_no_remote_mutation

        with tempfile.TemporaryDirectory() as tmp:
            # Initialize a git repo
            import subprocess
            subprocess.run(["git", "init"], cwd=tmp, capture_output=True)
            (Path(tmp) / "test.txt").write_text("hello")
            subprocess.run(["git", "add", "."], cwd=tmp, capture_output=True)
            subprocess.run(["git", "commit", "-m", "init"], cwd=tmp, capture_output=True)

            mock_mirror = MagicMock()
            mock_mirror.full_name = "test/repo"
            mock_mirror.local_path = tmp

            result = await verify_no_remote_mutation(mock_mirror)
            assert result["no_push_reflog"] is True
            assert result["safe"] is True

    @pytest.mark.asyncio
    async def test_mirror_safety_basic(self):
        """Basic safety check passes for a valid mirror."""
        from growthos.intelligence.evidence_mirror import verify_mirror_safety

        with tempfile.TemporaryDirectory() as tmp:
            import subprocess
            subprocess.run(["git", "init"], cwd=tmp, capture_output=True)
            subprocess.run(
                ["git", "remote", "add", "origin", "https://github.com/test/repo.git"],
                cwd=tmp, capture_output=True,
            )

            mock_mirror = MagicMock()
            mock_mirror.full_name = "test/repo"
            mock_mirror.local_path = tmp
            mock_mirror.remote_url = "https://github.com/test/repo.git"

            result = await verify_mirror_safety(mock_mirror)
            assert result["path_exists"] is True
            assert result["has_git"] is True
            assert result["remote_matches"] is True
            assert result["no_uncommitted_changes"] is True
