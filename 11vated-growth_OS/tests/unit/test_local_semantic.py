"""Tests for Local Semantic Analysis — filesystem-aware source evidence analysis."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from growthos.intelligence.local_semantic import (
    FileAnalysis,
    ImplementationGraph,
    SubsystemProfile,
    _is_build_config,
    _is_docs,
    _is_test_path,
    analyze_file,
    analyze_mirror_locally,
    compute_graph_confidence,
    graph_to_dict,
)

# ---------------------------------------------------------------------------
# Python file analysis
# ---------------------------------------------------------------------------


class TestPythonAnalysis:
    def test_simple_class(self):
        content = "class Foo:\n    def bar(self):\n        pass\n"
        fa = analyze_file("src/foo.py", content)
        assert "Foo" in fa.classes
        assert "bar" in fa.functions
        assert fa.impl_signal_count >= 2
        assert fa.lang == "Python"

    def test_async_functions(self):
        content = "async def fetch():\n    pass\nasync def process():\n    pass\n"
        fa = analyze_file("src/async.py", content)
        assert "fetch" in fa.async_functions
        assert "process" in fa.async_functions
        assert len(fa.async_functions) == 2

    def test_imports(self):
        content = "import os\nfrom pathlib import Path\nimport json\n"
        fa = analyze_file("src/utils.py", content)
        assert "os" in fa.imports
        assert "pathlib" in fa.imports

    def test_syntax_error_graceful(self):
        content = "def broken(\n"
        fa = analyze_file("bad.py", content)
        assert fa.classes == []
        assert fa.impl_signal_count == 0
        assert fa.line_count == 1


class TestTypeScriptAnalysis:
    def test_class_and_function(self):
        content = "class Widget {\n  render() {}\n}\nconst init = () => {};\n"
        fa = analyze_file("Widget.tsx", content)
        assert "Widget" in fa.classes
        assert "init" in fa.functions
        assert fa.lang == "TypeScript/React"

    def test_imports(self):
        content = "import React from 'react';\nconst { useState } = require('react');\n"
        fa = analyze_file("Comp.tsx", content)
        assert len(fa.imports) >= 1


class TestRustAnalysis:
    def test_struct_and_fn(self):
        content = "pub struct Config {\n    name: String,\n}\npub fn new() -> Config {\n    Config { name: String::new() }\n}\n"
        fa = analyze_file("lib.rs", content)
        assert "Config" in fa.classes
        assert "new" in fa.functions


class TestGoAnalysis:
    def test_functions(self):
        content = "func main() {}\nfunc helper() {}\n"
        fa = analyze_file("main.go", content)
        assert "main" in fa.functions
        assert "helper" in fa.functions


# ---------------------------------------------------------------------------
# Test file / build config / docs detection
# ---------------------------------------------------------------------------


class TestFileClassification:
    def test_various_test_paths(self):
        assert _is_test_path("tests/test_core.py")
        assert _is_test_path("__tests__/utils.test.ts")
        assert _is_test_path("spec/parser_spec.rb")
        assert _is_test_path("src/core_test.py")
        assert not _is_test_path("src/core.py")

    def test_various_build_configs(self):
        assert _is_build_config("package.json")
        assert _is_build_config("pyproject.toml")
        assert _is_build_config("Cargo.toml")
        assert _is_build_config("Makefile")
        assert _is_build_config("Dockerfile")
        assert _is_build_config(".github/workflows/ci.yml")
        assert not _is_build_config("src/main.py")

    def test_various_doc_files(self):
        assert _is_docs("README.md")
        assert _is_docs("ARCHITECTURE.rst")
        assert _is_docs("notes.txt")
        assert not _is_docs("src/main.py")


# ---------------------------------------------------------------------------
# Mirror local analysis (filesystem)
# ---------------------------------------------------------------------------


class TestMirrorLocalAnalysis:
    @pytest.mark.asyncio
    async def test_analyze_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            graph = await analyze_mirror_locally(tmp)
            assert len(graph.all_files) == 0
            assert graph.total_impl_files == 0

    @pytest.mark.asyncio
    async def test_analyze_python_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Create a small Python project
            src = Path(tmp) / "src"
            src.mkdir()
            (src / "main.py").write_text(
                "class App:\n    def run(self):\n        pass\n\nif __name__ == '__main__':\n    App().run()\n"
            )
            (src / "utils.py").write_text(
                "def helper():\n    return 42\n"
            )
            tests = Path(tmp) / "tests"
            tests.mkdir()
            (tests / "test_main.py").write_text(
                "import pytest\n\ndef test_app():\n    assert True\n"
            )
            (Path(tmp) / "pyproject.toml").write_text("[project]\nname = 'test'\n")
            (Path(tmp) / "README.md").write_text("# Test Project\n")

            graph = await analyze_mirror_locally(tmp)
            assert len(graph.all_files) >= 4
            assert graph.total_impl_files >= 2
            assert graph.total_test_files >= 1
            assert graph.total_build_files >= 1
            assert "Python" in graph.languages
            assert graph.total_classes >= 1  # App class
            assert graph.total_functions >= 1  # run, helper

    @pytest.mark.asyncio
    async def test_analyze_with_subsystems(self):
        with tempfile.TemporaryDirectory() as tmp:
            agent_dir = Path(tmp) / "src" / "agent"
            agent_dir.mkdir(parents=True)
            (agent_dir / "loop.py").write_text(
                "class AgentLoop:\n    def run(self):\n        pass\n"
            )
            (agent_dir / "ollama_client.py").write_text(
                "class OllamaClient:\n    def query(self):\n        pass\n"
            )
            test_dir = Path(tmp) / "tests"
            test_dir.mkdir()
            (test_dir / "test_agent.py").write_text(
                "class TestAgentLoop:\n    def test_run(self):\n        pass\n"
            )

            graph = await analyze_mirror_locally(tmp)
            assert len(graph.subsystems) >= 1
            categories = [s.category for s in graph.subsystems]
            assert "agent_loop" in categories

    @pytest.mark.asyncio
    async def test_nonexistent_path(self):
        graph = await analyze_mirror_locally("/nonexistent/path/xyz")
        assert len(graph.all_files) == 0

    @pytest.mark.asyncio
    async def test_max_files_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            src.mkdir()
            for i in range(10):
                (src / f"mod{i}.py").write_text(f"class M{i}:\n    pass\n")

            graph = await analyze_mirror_locally(tmp, max_files=5)
            assert len(graph.all_files) <= 5


# ---------------------------------------------------------------------------
# Graph serialization
# ---------------------------------------------------------------------------


class TestGraphSerialization:
    def test_graph_to_dict(self):
        graph = ImplementationGraph()
        graph.all_files = ["a.py", "b.py"]
        graph.languages = {"Python": 2}
        graph.total_impl_files = 2
        graph.total_test_files = 0
        graph.total_lines = 50
        graph.subsystems = [
            SubsystemProfile(name="Agent Loop", category="agent_loop",
                             implementation_files=["a.py"], status="IMPLEMENTED_UNTESTED"),
        ]

        d = graph_to_dict(graph)
        assert d["file_count"] == 2
        assert d["languages"] == {"Python": 2}
        assert d["total_impl_files"] == 2
        assert len(d["subsystems"]) == 1
        assert d["subsystems"][0]["category"] == "agent_loop"

    def test_graph_to_dict_empty(self):
        graph = ImplementationGraph()
        d = graph_to_dict(graph)
        assert d["file_count"] == 0
        assert d["subsystems"] == []


# ---------------------------------------------------------------------------
# Confidence computation
# ---------------------------------------------------------------------------


class TestConfidenceComputationUnit:
    def test_empty_graph_confidence(self):
        graph = ImplementationGraph()
        conf = compute_graph_confidence(graph)
        assert conf["implementation"] == 0.0
        assert conf["testing"] == 0.0
        assert conf["build"] == 0.0

    def test_rich_graph_confidence(self):
        graph = ImplementationGraph()
        graph.total_impl_files = 10
        graph.total_test_files = 5
        graph.total_build_files = 2
        graph.entry_points = ["main.py"]
        graph.file_analyses = [
            _make_fa("api.py", arch=["api_surface", "database"]),
        ]
        conf = compute_graph_confidence(graph)
        assert conf["implementation"] > 0.5
        assert conf["testing"] > 0.5
        assert conf["build"] > 0.0
        assert conf["runtime"] > 0.0

    def test_mixed_graph(self):
        graph = ImplementationGraph()
        graph.total_impl_files = 3
        graph.total_test_files = 0
        graph.total_build_files = 1
        graph.entry_points = []
        conf = compute_graph_confidence(graph)
        assert 0.0 < conf["implementation"] < 1.0
        assert conf["testing"] == 0.0
        assert conf["build"] > 0.0
        assert conf["runtime"] == 0.0


def _make_fa(rel_path: str, arch: list[str] | None = None) -> FileAnalysis:
    """Helper to create a FileAnalysis with architecture signals."""
    fa = FileAnalysis(rel_path=rel_path, lang="Python")
    fa.architecture_signals = arch or []
    return fa
