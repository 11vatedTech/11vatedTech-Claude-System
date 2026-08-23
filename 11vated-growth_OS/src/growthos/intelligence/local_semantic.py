"""Local Semantic Analysis — filesystem-aware source evidence analysis.

Replaces API-based regex sampling with local mirror traversal. Inspects:
- filesystem structure and source roots
- language-aware source parsing (AST where practical, conservative regex fallback)
- imports/dependencies
- class/function/module relationships
- test references and coverage
- entry points and runtime targets
- build definitions
- architecture docs
- contradictions (roadmap vs implementation)

The analysis is deterministic and never calls external LLMs.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FileAnalysis:
    """Analysis result for a single source file."""
    rel_path: str
    lang: str
    line_count: int = 0
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    async_functions: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    architecture_signals: list[str] = field(default_factory=list)
    test_framework_signals: list[str] = field(default_factory=list)
    roadmap_signals: list[str] = field(default_factory=list)
    impl_signal_count: int = 0
    test_signal_count: int = 0
    roadmap_signal_count: int = 0
    evidence_classes: list[str] = field(default_factory=list)
    is_test_file: bool = False
    is_entry_point: bool = False
    is_build_config: bool = False
    is_docs: bool = False


@dataclass
class SubsystemProfile:
    """A detected subsystem with its implementation evidence."""
    name: str
    category: str  # e.g. "agent_loop", "planner", "tool_registry"
    implementation_files: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    classes: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    status: str = "NOT_FOUND"  # IMPLEMENTED_AND_TESTED / IMPLEMENTED_PARTIAL_TEST / etc.


@dataclass
class ImplementationGraph:
    """Cross-file implementation evidence graph."""
    source_roots: list[str] = field(default_factory=list)
    test_directories: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    build_configs: list[str] = field(default_factory=list)
    all_files: list[str] = field(default_factory=list)
    file_analyses: list[FileAnalysis] = field(default_factory=list)
    subsystems: list[SubsystemProfile] = field(default_factory=list)
    total_classes: int = 0
    total_functions: int = 0
    total_impl_files: int = 0
    total_test_files: int = 0
    total_docs_files: int = 0
    total_build_files: int = 0
    total_lines: int = 0
    contradictions: list[str] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Language-aware parsing
# ---------------------------------------------------------------------------

# File extensions mapped to languages
_EXT_LANG: dict[str, str] = {
    ".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript/React",
    ".js": "JavaScript", ".jsx": "JavaScript/React",
    ".rs": "Rust", ".go": "Go", ".cs": "C#", ".cpp": "C++",
    ".c": "C", ".h": "C/C++", ".java": "Java",
}

_ENTRY_PATTERNS = [
    re.compile(r"^if\s+__name__\s*==\s*['\"]__main__['\"]", re.MULTILINE),
    re.compile(r"^(?:export\s+)?default\s+(?:async\s+)?function", re.MULTILINE),
    re.compile(r"^fn\s+main\s*\(", re.MULTILINE),
    re.compile(r"^func\s+main\s*\(\)", re.MULTILINE),
    re.compile(r"static\s+void\s+Main\s*\(", re.MULTILINE),
]

_BUILD_CONFIG_NAMES = {
    "Makefile", "CMakeLists.txt", "Cargo.toml", "build.gradle", "build.gradle.kts",
    "pom.xml", "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "tsconfig.json", "vite.config.ts", "vite.config.js", "webpack.config.js",
    "next.config.js", "next.config.mjs", "rollup.config.js", "esbuild.config.js",
    "Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".github",
    "justfile", "Taskfile.yml", "meson.build",
}

_DOC_EXTS = {".md", ".rst", ".txt"}
_TEST_DIR_MARKERS = {"test", "tests", "__tests__", "spec", "specs", "test_*"}
_TEST_FILE_MARKERS = {"test_", "_test", ".test.", ".spec.", "test.", "spec."}

_ARCH_KEYWORDS: dict[str, list[str]] = {
    "api_surface": ["api", "router", "endpoint", "route", "handler"],
    "middleware": ["middleware", "interceptor"],
    "database": ["database", "db", "migration", "schema"],
    "authentication": ["auth", "oauth", "jwt", "session", "login"],
    "event_system": ["event", "emitter", "listener", "hook", "callback"],
    "plugin_system": ["plugin", "extension", "addon", "registry"],
    "adapter_pattern": ["adapter", "connector", "bridge"],
    "factory_pattern": ["factory", "builder", "create"],
    "pipeline": ["pipeline", "workflow", "orchestrat"],
    "graph_architecture": ["graph", "node", "edge", "vertex"],
    "tensor_processing": ["tensor", "matrix", "ndarray", "gpu", "cuda"],
    "scheduler": ["scheduler", "cron", "periodic", "interval"],
    "queue_system": ["queue", "worker", "job", "task"],
    "websocket": ["websocket", "ws", "real-time"],
    "grpc": ["grpc", "protobuf"],
    "background_worker": ["worker", "background", "daemon", "asyncio.create_task"],
    "caching": ["cache", "lru", "memoize", "redis"],
}


def _detect_lang(rel_path: str) -> str:
    ext = Path(rel_path).suffix.lower()
    return _EXT_LANG.get(ext, "Unknown")


def _is_test_path(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    for part in parts:
        if part.lower() in _TEST_DIR_MARKERS or part.lower().startswith("test_"):
            return True
    name = Path(rel_path).name.lower()
    return any(m in name for m in _TEST_FILE_MARKERS)


def _is_build_config(rel_path: str) -> bool:
    name = Path(rel_path).name
    return name in _BUILD_CONFIG_NAMES or (rel_path.startswith(".github/") and name.endswith((".yml", ".yaml")))


def _is_docs(rel_path: str) -> bool:
    return Path(rel_path).suffix.lower() in _DOC_EXTS


def _detect_entry_points(content: str) -> bool:
    return any(pat.search(content) for pat in _ENTRY_PATTERNS)


def _detect_architecture(content: str, rel_path: str) -> list[str]:
    signals: list[str] = []
    text_lower = content.lower()
    for category, keywords in _ARCH_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                signals.append(category)
                break
    return signals


# ---------------------------------------------------------------------------
# Python AST parsing (safe, deterministic)
# ---------------------------------------------------------------------------


def _parse_python_file(content: str, rel_path: str) -> FileAnalysis:
    """Parse a Python file using the stdlib AST module."""
    analysis = FileAnalysis(rel_path=rel_path, lang="Python")
    analysis.line_count = len(content.splitlines())

    try:
        tree = ast.parse(content)
    except (SyntaxError, ValueError):
        return analysis

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            analysis.classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            analysis.functions.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            analysis.async_functions.append(node.name)
            analysis.functions.append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis.imports.append(alias.name)
            elif node.module:
                analysis.imports.append(node.module)

    analysis.impl_signal_count = len(analysis.classes) + len(analysis.functions)
    return analysis


# ---------------------------------------------------------------------------
# Generic regex-based parsing (fallback for non-Python files)
# ---------------------------------------------------------------------------

_JS_CLASS_RE = re.compile(r"\bclass\s+(\w+)")
_JS_FUNC_RE = re.compile(r"(?:export\s+)?(?:const|let|var|function)\s+(\w+)\s*[=(]")
_JS_IMPORT_RE = re.compile(r"""(?:import\s+.*?from\s+['"]([^'"]+)['"]|require\s*\(\s*['"]([^'"]+)['"]\s*\))""")
_RUST_STRUCT_RE = re.compile(r"(?:pub\s+)?(?:struct|enum|trait)\s+(\w+)")
_RUST_FN_RE = re.compile(r"(?:pub\s+)?fn\s+(\w+)")
_GO_FUNC_RE = re.compile(r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)")
_CSHARP_RE = re.compile(r"(?:public|private|protected|internal)\s+(?:class|struct|interface)\s+(\w+)")


def _parse_generic_file(content: str, rel_path: str, lang: str) -> FileAnalysis:
    """Regex-based parsing for non-Python source files."""
    analysis = FileAnalysis(rel_path=rel_path, lang=lang)
    analysis.line_count = len(content.splitlines())

    if lang in ("TypeScript", "TypeScript/React", "JavaScript", "JavaScript/React"):
        analysis.classes = _JS_CLASS_RE.findall(content)
        analysis.functions = _JS_FUNC_RE.findall(content)
        for m in _JS_IMPORT_RE.finditer(content):
            analysis.imports.append(m.group(1) or m.group(2) or "")
    elif lang == "Rust":
        analysis.classes = _RUST_STRUCT_RE.findall(content)
        analysis.functions = _RUST_FN_RE.findall(content)
    elif lang == "Go":
        analysis.functions = _GO_FUNC_RE.findall(content)
    elif lang in ("C#",):
        analysis.classes = _CSHARP_RE.findall(content)
    elif lang in ("C++", "C"):
        analysis.classes = _JS_CLASS_RE.findall(content)

    analysis.impl_signal_count = len(analysis.classes) + len(analysis.functions)
    return analysis


# ---------------------------------------------------------------------------
# File analysis dispatcher
# ---------------------------------------------------------------------------


def analyze_file(rel_path: str, content: str) -> FileAnalysis:
    """Analyze a single file, dispatching to language-appropriate parser."""
    lang = _detect_lang(rel_path)

    if lang == "Python":
        analysis = _parse_python_file(content, rel_path)
    elif lang != "Unknown":
        analysis = _parse_generic_file(content, rel_path, lang)
    else:
        analysis = FileAnalysis(rel_path=rel_path, lang=lang)
        analysis.line_count = len(content.splitlines())

    # Common enrichment
    analysis.is_test_file = _is_test_path(rel_path)
    analysis.is_entry_point = _detect_entry_points(content)
    analysis.is_build_config = _is_build_config(rel_path)
    analysis.is_docs = _is_docs(rel_path)
    analysis.architecture_signals = _detect_architecture(content, rel_path)

    # Roadmap/contradiction detection
    text_lower = content.lower()
    roadmap_terms = ["todo", "fixme", "hack", "placeholder", "not yet implemented",
                     "planned", "future", "roadmap", "coming soon", "wip",
                     "will be", "phase 2", "not implemented"]
    for term in roadmap_terms:
        if term in text_lower:
            analysis.roadmap_signals.append(term)
    analysis.roadmap_signal_count = len(analysis.roadmap_signals)

    # Test framework signals
    test_terms = ["pytest", "unittest", "jest", "vitest", "mocha", "cargo test",
                  "describe(", "it(", "test(", "expect(", "assert("]
    for term in test_terms:
        if term in content:
            analysis.test_framework_signals.append(term)
    analysis.test_signal_count = len(analysis.test_framework_signals)

    # Evidence class classification
    if analysis.impl_signal_count >= 3:
        analysis.evidence_classes.append("DIRECT_IMPLEMENTATION")
    if analysis.is_test_file and analysis.test_signal_count > 0:
        analysis.evidence_classes.append("TEST_EVIDENCE")
    if analysis.is_build_config:
        analysis.evidence_classes.append("BUILD_EVIDENCE")
    if analysis.is_entry_point:
        analysis.evidence_classes.append("RUNTIME_EVIDENCE")
    if analysis.is_docs:
        analysis.evidence_classes.append("DOCUMENTATION")
    if analysis.roadmap_signal_count > 2 and analysis.impl_signal_count < 3:
        analysis.evidence_classes.append("DOCUMENTED_CLAIM")

    return analysis


# ---------------------------------------------------------------------------
# Subsystem detection
# ---------------------------------------------------------------------------


@dataclass
class SubsystemDetector:
    """Configurable detector for project subsystems."""
    name: str
    category: str
    file_patterns: list[str] = field(default_factory=list)
    class_name_patterns: list[str] = field(default_factory=list)
    function_patterns: list[str] = field(default_factory=list)
    import_patterns: list[str] = field(default_factory=list)


# Common subsystem detectors for GrowthOS-relevant projects
SubsystemDetectors = [
    SubsystemDetector("Agent Loop", "agent_loop",
                      file_patterns=["loop", "agent"],
                      class_name_patterns=["AgentLoop", "AgentRunner", "AgentExecutor"]),
    SubsystemDetector("Planner", "planner",
                      file_patterns=["plan"],
                      class_name_patterns=["Planner", "TaskPlanner", "PlanExecutor"]),
    SubsystemDetector("Executor", "executor",
                      file_patterns=["exec", "run"],
                      class_name_patterns=["Executor", "TaskExecutor", "RunExecutor"]),
    SubsystemDetector("Tool Registry", "tool_registry",
                      file_patterns=["tool", "registry"],
                      class_name_patterns=["ToolRegistry", "ToolManager", "ToolBox"]),
    SubsystemDetector("Ollama Client", "ollama",
                      file_patterns=["ollama", "llm", "model"],
                      class_name_patterns=["OllamaClient", "Ollama", "ModelClient"]),
    SubsystemDetector("Memory", "memory",
                      file_patterns=["memory", "store", "context"],
                      class_name_patterns=["Memory", "ConversationMemory", "ContextStore"]),
    SubsystemDetector("Permissions", "permissions",
                      file_patterns=["perm", "auth", "access"],
                      class_name_patterns=["Permission", "PermissionManager", "AccessControl"]),
    SubsystemDetector("Diff System", "diff",
                      file_patterns=["diff", "patch"],
                      class_name_patterns=["DiffSystem", "DiffEngine", "PatchManager"]),
    SubsystemDetector("Model Router", "model_router",
                      file_patterns=["router", "model", "routing"],
                      class_name_patterns=["ModelRouter", "ModelSelector", "Router"]),
    SubsystemDetector("Conversation", "conversation",
                      file_patterns=["conversation", "chat", "session"],
                      class_name_patterns=["Conversation", "ChatSession", "ThreadManager"]),
    SubsystemDetector("Hooks/Watchers", "hooks",
                      file_patterns=["hook", "watch", "listener"],
                      class_name_patterns=["Hook", "Watcher", "HookManager"]),
    SubsystemDetector("CLI/TUI", "cli",
                      file_patterns=["cli", "tui", "terminal", "command"],
                      class_name_patterns=["CLI", "TUI", "CommandRunner"]),
    SubsystemDetector("Scheduler", "scheduler",
                      file_patterns=["schedul", "cron", "timer"],
                      class_name_patterns=["Scheduler", "CronJob", "TaskScheduler"]),
    SubsystemDetector("API Surface", "api",
                      file_patterns=["api", "route", "endpoint", "server"],
                      class_name_patterns=["App", "Server", "Router", "FastAPI", "Flask"]),
    SubsystemDetector("Database Layer", "database",
                      file_patterns=["db", "database", "model", "migration", "schema"],
                      class_name_patterns=["Database", "DB", "Session", "Repository"]),
    SubsystemDetector("Event System", "event_system",
                      file_patterns=["event", "emitter", "signal"],
                      class_name_patterns=["EventEmitter", "EventBus", "SignalManager"]),
    SubsystemDetector("Pipeline/Workflow", "pipeline",
                      file_patterns=["pipeline", "workflow", "orchestrat"],
                      class_name_patterns=["Pipeline", "Workflow", "Orchestrator"]),
    SubsystemDetector("Tensor/Processing", "tensor",
                      file_patterns=["tensor", "matrix", "graph_exec", "compute"],
                      class_name_patterns=["Tensor", "ComputeGraph", "GraphExecutor"]),
    SubsystemDetector("Game/Sprite Runtime", "game_runtime",
                      file_patterns=["sprite", "game", "entity", "render"],
                      class_name_patterns=["Sprite", "GameLoop", "Entity", "Renderer"]),
    SubsystemDetector("Motion/Sensor", "motion",
                      file_patterns=["motion", "sensor", "tracking", "gesture"],
                      class_name_patterns=["MotionTracker", "SensorClient", "GestureEngine"]),
    SubsystemDetector("Accessibility", "accessibility",
                      file_patterns=["access", "a11y", "adapt"],
                      class_name_patterns=["Accessibility", "Adaptation", "A11yManager"]),
]


def _detect_subsystems(
    graph: ImplementationGraph,
) -> list[SubsystemProfile]:
    """Detect subsystems from the implementation graph."""
    subsystems: list[SubsystemProfile] = []

    for detector in SubsystemDetectors:
        impl_files: list[str] = []
        test_files: list[str] = []
        classes_found: list[str] = []
        functions_found: list[str] = []
        entry_points: list[str] = []

        for fa in graph.file_analyses:
            # Check file path patterns
            path_match = any(
                pat in fa.rel_path.lower()
                for pat in detector.file_patterns
            )

            # Check class/function name patterns
            class_match = any(
                cn.lower() in [c.lower() for c in fa.classes]
                for cn in detector.class_name_patterns
            )
            func_match = any(
                fn.lower() in [f.lower() for f in fa.functions]
                for fn in detector.function_patterns
            ) if detector.function_patterns else False

            if path_match or class_match or func_match:
                if fa.is_test_file:
                    test_files.append(fa.rel_path)
                elif not fa.is_docs and not fa.is_build_config:
                    impl_files.append(fa.rel_path)
                    classes_found.extend(c for c in fa.classes if any(cn.lower() == c.lower() for cn in detector.class_name_patterns))
                    functions_found.extend(f for f in fa.functions if any(fn.lower() == f.lower() for fn in detector.function_patterns))
                if fa.is_entry_point:
                    entry_points.append(fa.rel_path)

        if impl_files or test_files:
            # Determine status
            if impl_files and test_files:
                status = "IMPLEMENTED_AND_TESTED"
            elif impl_files:
                status = "IMPLEMENTED_UNTESTED"
            else:
                status = "TESTS_ONLY"

            subsystems.append(SubsystemProfile(
                name=detector.name,
                category=detector.category,
                implementation_files=impl_files,
                test_files=test_files,
                entry_points=entry_points,
                classes=classes_found,
                functions=functions_found,
                status=status,
            ))

    return subsystems


# ---------------------------------------------------------------------------
# Full repository analysis
# ---------------------------------------------------------------------------


async def analyze_mirror_locally(
    mirror_path: str | Path,
    *,
    max_files: int = 500,
    max_file_size: int = 100_000,
    include_tests: bool = True,
    include_docs: bool = False,
    include_build: bool = True,
) -> ImplementationGraph:
    """Perform a full local semantic analysis of a mirrored repository.

    Walks the filesystem, analyzes source files, builds an implementation
    graph, and detects subsystems. No external API calls.
    """
    root = Path(mirror_path)
    graph = ImplementationGraph()

    if not root.exists():
        return graph

    # Discover all files
    all_files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip .git and hidden directories
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in {"node_modules", "__pycache__", "venv", ".venv", "dist", "build", "target"}]
        for fname in filenames:
            if fname.startswith(".") or fname.endswith((".pyc", ".pyo", ".class", ".o", ".so")):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            all_files.append(rel)
            if len(all_files) >= max_files:
                break
        if len(all_files) >= max_files:
            break

    all_files.sort()
    graph.all_files = all_files

    # Detect source roots
    dir_counts: dict[str, int] = {}
    for f in all_files:
        parts = f.split(os.sep)
        if len(parts) >= 2:
            root_dir = parts[0]
            if not root_dir.startswith(".") and root_dir not in {"node_modules", "__pycache__", "dist", "build", "target"}:
                dir_counts[root_dir] = dir_counts.get(root_dir, 0) + 1

    graph.source_roots = [d for d, c in sorted(dir_counts.items(), key=lambda x: -x[1]) if c >= 3][:10]

    # Detect test directories
    test_dirs: set[str] = set()
    for f in all_files:
        parts = f.split(os.sep)
        for i, part in enumerate(parts):
            if part.lower() in _TEST_DIR_MARKERS:
                test_dir = os.sep.join(parts[:i + 1])
                test_dirs.add(test_dir)
    graph.test_directories = sorted(test_dirs)

    # Detect languages
    lang_counts: dict[str, int] = {}
    for f in all_files:
        lang = _detect_lang(f)
        if lang != "Unknown":
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
    graph.languages = lang_counts

    # Analyze individual files
    file_analyses: list[FileAnalysis] = []
    total_impl = 0
    total_test = 0
    total_docs = 0
    total_build = 0
    total_lines = 0
    total_classes = 0
    total_functions = 0
    contradictions: list[str] = []

    for rel_path in all_files:
        # Filter by type
        is_test = _is_test_path(rel_path)
        is_doc = _is_docs(rel_path)
        is_build = _is_build_config(rel_path)

        if is_test and not include_tests:
            continue
        if is_doc and not include_docs:
            continue
        if is_build and not include_build:
            continue

        # Skip binary files
        lang = _detect_lang(rel_path)
        if lang == "Unknown" and not is_build and not is_doc:
            continue

        # Read file
        full_path = root / rel_path
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue

        if len(content) > max_file_size:
            content = content[:max_file_size] + "\n... [truncated]"

        # Analyze
        fa = analyze_file(rel_path, content)
        file_analyses.append(fa)

        total_lines += fa.line_count
        total_classes += len(fa.classes)
        total_functions += len(fa.functions)

        if fa.is_test_file:
            total_test += 1
        elif fa.is_docs:
            total_docs += 1
        elif fa.is_build_config:
            total_build += 1
        elif fa.impl_signal_count > 0:
            total_impl += 1

        # Detect contradictions
        if fa.roadmap_signal_count > 3 and fa.impl_signal_count < 2:
            contradictions.append(f"{rel_path}: {fa.roadmap_signal_count} roadmap claims but only {fa.impl_signal_count} implementation signals")

    # Entry points
    entry_points = [fa.rel_path for fa in file_analyses if fa.is_entry_point]
    build_configs = [fa.rel_path for fa in file_analyses if fa.is_build_config]

    # Detect subsystems
    graph.file_analyses = file_analyses
    graph.entry_points = entry_points
    graph.build_configs = build_configs
    graph.total_classes = total_classes
    graph.total_functions = total_functions
    graph.total_impl_files = total_impl
    graph.total_test_files = total_test
    graph.total_docs_files = total_docs
    graph.total_build_files = total_build
    graph.total_lines = total_lines
    graph.contradictions = contradictions
    graph.subsystems = _detect_subsystems(graph)

    return graph


def graph_to_dict(graph: ImplementationGraph) -> dict[str, Any]:
    """Serialize an ImplementationGraph to a JSON-safe dictionary."""
    return {
        "source_roots": graph.source_roots,
        "test_directories": graph.test_directories,
        "entry_points": graph.entry_points,
        "build_configs": graph.build_configs,
        "file_count": len(graph.all_files),
        "languages": graph.languages,
        "total_classes": graph.total_classes,
        "total_functions": graph.total_functions,
        "total_impl_files": graph.total_impl_files,
        "total_test_files": graph.total_test_files,
        "total_docs_files": graph.total_docs_files,
        "total_build_files": graph.total_build_files,
        "total_lines": graph.total_lines,
        "contradictions": graph.contradictions,
        "subsystems": [
            {
                "name": s.name,
                "category": s.category,
                "status": s.status,
                "implementation_files": s.implementation_files[:10],
                "test_files": s.test_files[:10],
                "entry_points": s.entry_points[:5],
                "classes": s.classes[:10],
                "functions": s.functions[:10],
            }
            for s in graph.subsystems
        ],
        "architecture_signals": list({
            sig for fa in graph.file_analyses for sig in fa.architecture_signals
        })[:20],
        "unique_classes": list({
            c for fa in graph.file_analyses for c in fa.classes
        })[:50],
    }


def compute_graph_confidence(graph: ImplementationGraph) -> dict[str, float]:
    """Compute independent confidence dimensions from a local analysis graph."""
    impl = min(1.0, 0.15 + 0.08 * graph.total_impl_files) if graph.total_impl_files else 0.0
    test = min(1.0, 0.3 * graph.total_test_files) if graph.total_test_files else 0.0
    build = 0.5 if graph.total_build_files > 0 else 0.0
    runtime = 0.7 if graph.entry_points else 0.0

    # Reproducibility based on test coverage + build presence
    if graph.total_test_files > 0 and graph.total_build_files > 0:
        repro = 0.9
    elif graph.total_test_files > 0:
        repro = 0.6
    elif graph.total_build_files > 0:
        repro = 0.4
    else:
        repro = 0.2

    # Delivery: based on maturity signals
    has_api = any("api" in s for s in {
        sig for fa in graph.file_analyses for sig in fa.architecture_signals
    })
    has_db = any("database" in s for s in {
        sig for fa in graph.file_analyses for sig in fa.architecture_signals
    })
    delivery = 0.2
    if has_api:
        delivery += 0.3
    if has_db:
        delivery += 0.2
    if graph.total_test_files > 0:
        delivery += 0.2
    delivery = min(1.0, delivery)

    return {
        "implementation": round(impl, 3),
        "testing": round(test, 3),
        "build": round(build, 3),
        "runtime": round(runtime, 3),
        "reproducibility": round(repro, 3),
        "delivery": round(delivery, 3),
    }
