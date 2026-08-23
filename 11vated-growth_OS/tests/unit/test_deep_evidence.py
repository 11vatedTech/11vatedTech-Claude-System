"""Unit tests for portfolio deep evidence analysis."""

from __future__ import annotations

from growthos.intelligence.deep_evidence import (
    EvidenceClass,
    analyze_file_content,
    synthesize_deep_evidence,
)
from growthos.intelligence.github_portfolio import (
    GitHubHealthState,
    GitHubProfileClient,
    _redact_token,
    select_deep_files,
)


class TestFileContentAnalysis:
    """Tests for single-file content analysis."""

    def test_detects_class_definitions(self):
        content = """\
class SpriteManager:
    def __init__(self):
        self.sprites = []

    def update(self):
        for sprite in self.sprites:
            sprite.render()
"""
        result = analyze_file_content(content, "sprite_manager.py", "Python")
        assert EvidenceClass.DIRECT_IMPLEMENTATION in result["evidence_classes"]
        assert result["implementation_signals"] >= 3

    def test_detects_async_def(self):
        content = """\
async def process_sprites(sprites):
    for s in sprites:
        await s.update()

async def render_frame():
    pass
"""
        result = analyze_file_content(content, "engine.py", "Python")
        assert result["implementation_signals"] >= 2

    def test_detects_test_framework(self):
        content = """\
import pytest

def test_sprite_creation():
    sprite = Sprite("hero.png")
    assert sprite.width > 0

def test_sprite_update():
    sprite = Sprite("hero.png")
    sprite.update(dt=0.016)
    assert sprite.position != (0, 0)
"""
        result = analyze_file_content(content, "test_sprite.py", "Python")
        assert EvidenceClass.TEST_EVIDENCE in result["evidence_classes"]
        assert result["test_signals"] >= 2

    def test_detects_roadmap_claims(self):
        content = """\
# GPU acceleration will be added in phase 2
# Planned: support for multiple sprite sheets
# TODO: implement collision detection
# Coming soon: particle effects
"""
        result = analyze_file_content(content, "ROADMAP.md", None)
        assert result["roadmap_signals"] >= 3

    def test_detects_architecture_signals(self):
        content = """\
class APIRouter:
    def __init__(self):
        self.middleware = []
        self.database = DatabaseConnection()
        self.cache = CacheLayer()

    def handle_request(self, request):
        for mw in self.middleware:
            request = mw.process(request)
        return self.database.query(request)
"""
        result = analyze_file_content(content, "router.py", "Python")
        assert "API surface" in result["architecture_signals"]
        assert "database layer" in result["architecture_signals"]

    def test_rust_functions(self):
        content = """\
pub fn process_sprites(sprites: &mut Vec<Sprite>) {
    for sprite in sprites.iter_mut() {
        sprite.update();
    }
}

pub struct GameState {
    pub entities: Vec<Entity>,
    pub dt: f32,
}
"""
        result = analyze_file_content(content, "game.rs", "Rust")
        assert result["implementation_signals"] >= 1

    def test_empty_file(self):
        result = analyze_file_content("", "empty.py", "Python")
        assert result["implementation_signals"] == 0
        assert result["test_signals"] == 0

    def test_truncation_handled(self):
        content = "x = 1\n" * 10000
        result = analyze_file_content(content, "big.py", "Python")
        assert result["line_count"] == 10000


class TestEvidenceSynthesis:
    """Tests for repository-level evidence synthesis."""

    def test_strong_repository(self):
        file_analyses = [
            {
                "file_path": "main.py",
                "evidence_classes": [EvidenceClass.DIRECT_IMPLEMENTATION],
                "implementation_signals": 15,
                "test_signals": 0,
                "build_signals": 0,
                "roadmap_signals": 0,
                "module_names": ["SpriteManager", "GameState", "Entity"],
                "architecture_signals": ["API surface", "pipeline architecture"],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 200,
            },
            {
                "file_path": "test_main.py",
                "evidence_classes": [EvidenceClass.TEST_EVIDENCE],
                "implementation_signals": 0,
                "test_signals": 8,
                "build_signals": 0,
                "roadmap_signals": 0,
                "module_names": ["test_sprite_creation", "test_update"],
                "architecture_signals": [],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 100,
            },
            {
                "file_path": "test_api.py",
                "evidence_classes": [EvidenceClass.TEST_EVIDENCE],
                "implementation_signals": 0,
                "test_signals": 5,
                "build_signals": 0,
                "roadmap_signals": 0,
                "module_names": ["test_api_route"],
                "architecture_signals": [],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 80,
            },
        ]

        synthesis = synthesize_deep_evidence(
            None, file_analyses,
            {"primary_language": "Python", "ci_build_present": True,
             "releases_present": False, "tests_present": True,
             "architecture_docs_present": False, "source_present": True}
        )

        assert synthesis["implementation_files"] == 1
        assert synthesis["test_files"] == 2
        assert synthesis["reproducibility"] == "MEDIUM"
        assert synthesis["confidence_dimensions"]["implementation"] > 0.2
        assert synthesis["confidence_dimensions"]["testing"] > 0.2

    def test_readme_only_repository(self):
        readme = {
            "file_path": "README.md",
            "evidence_classes": [EvidenceClass.DOCUMENTED_CLAIM],
            "implementation_signals": 1,
            "test_signals": 0,
            "build_signals": 0,
            "roadmap_signals": 5,
            "module_names": [],
            "architecture_signals": [],
            "impl_details": [],
            "roadmap_details": [("roadmap language", 3)],
            "line_count": 100,
        }

        synthesis = synthesize_deep_evidence(
            readme, [],
            {"primary_language": None, "ci_build_present": False,
             "releases_present": False, "tests_present": False,
             "architecture_docs_present": False, "source_present": True}
        )

        assert synthesis["implementation_files"] == 0
        assert synthesis["maturity_assessment"] == "EXPERIMENTAL"
        assert len(synthesis["readme_findings"]) > 0

    def test_contradiction_detection(self):
        file_analyses = [
            {
                "file_path": "docs/future.md",
                "evidence_classes": [],
                "implementation_signals": 1,
                "test_signals": 0,
                "build_signals": 0,
                "roadmap_signals": 8,
                "module_names": [],
                "architecture_signals": [],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 50,
            },
        ]

        synthesis = synthesize_deep_evidence(
            None, file_analyses,
            {"primary_language": None, "ci_build_present": False,
             "releases_present": False, "tests_present": False,
             "architecture_docs_present": True, "source_present": True}
        )

        assert len(synthesis["contradictions"]) > 0

    def test_maturity_scales_with_evidence(self):
        file_analyses = [
            *[{
                "file_path": f"src/module_{i}.py",
                "evidence_classes": [EvidenceClass.DIRECT_IMPLEMENTATION],
                "implementation_signals": 5,
                "test_signals": 0,
                "build_signals": 0,
                "roadmap_signals": 0,
                "module_names": [f"Module{i}"],
                "architecture_signals": [],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 100,
            } for i in range(6)],
            *[{
                "file_path": f"tests/test_{i}.py",
                "evidence_classes": [EvidenceClass.TEST_EVIDENCE],
                "implementation_signals": 0,
                "test_signals": 4,
                "build_signals": 0,
                "roadmap_signals": 0,
                "module_names": [f"test_module_{i}"],
                "architecture_signals": [],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 50,
            } for i in range(4)],
        ]

        synthesis = synthesize_deep_evidence(
            None, file_analyses,
            {"primary_language": "Python", "ci_build_present": True,
             "releases_present": True, "tests_present": True,
             "architecture_docs_present": False, "source_present": True}
        )

        assert synthesis["implementation_files"] == 6
        assert synthesis["test_files"] == 4
        assert synthesis["maturity_assessment"] in ("INTERNAL_PROVEN", "CLIENT_READY")


class TestDeepFileSelection:
    """Tests for file selection for deep analysis."""

    def test_readme_first(self):
        paths = ["src/main.py", "README.md", "tests/test_main.py", "docs/arch.md"]
        selected = select_deep_files(paths)
        assert selected[0] == "README.md"

    def test_limits_output(self):
        paths = [f"src/file_{i}.py" for i in range(100)]
        selected = select_deep_files(paths, max_files=10)
        assert len(selected) <= 10

    def test_prefers_source_in_dirs(self):
        paths = ["README.md", "src/main.py", "lib/utils.ts", "random.js"]
        selected = select_deep_files(paths)
        assert "src/main.py" in selected

    def test_includes_tests(self):
        paths = ["README.md", "src/main.py", "tests/test_main.py"]
        selected = select_deep_files(paths)
        assert "tests/test_main.py" in selected


class TestGitHubHealth:
    """Tests for GitHub client health tracking."""

    def test_initial_state(self):
        client = GitHubProfileClient()
        assert client.health_state == GitHubHealthState.UNKNOWN
        assert client.token is None

    def test_health_report_no_secrets(self):
        client = GitHubProfileClient()
        report = client.health_report()
        assert report["has_token"] is False
        report_str = str(report)
        assert "Bearer" not in report_str
        assert "Authorization" not in report_str
        assert "ghp_" not in report_str

    def test_redact_token(self):
        text = "Token is ghp_abc123secret"
        token = "ghp_abc123secret"
        redacted = _redact_token(text, token)
        assert "ghp_abc123secret" not in redacted
        assert "REDACTED" in redacted

    def test_redact_none_token(self):
        text = "No secrets here"
        assert _redact_token(text, None) == text


class TestCredentialLeakPrevention:
    """Tests ensuring credentials never appear in outputs."""

    def test_health_report_never_includes_token(self):
        client = GitHubProfileClient()
        report = client.health_report()
        report_str = str(report)
        assert "Bearer" not in report_str
        assert "Authorization" not in report_str

    def test_evidence_never_includes_token(self):
        from growthos.services.portfolio_deep_evidence import _evidence_summary
        summary = _evidence_summary(
            {"full_name": "test/repo", "name": "repo"},
            {"files_analyzed": 5, "implementation_files": 3, "test_files": 1,
             "maturity_assessment": "PROTOTYPE_PROVEN", "reproducibility": "MEDIUM",
             "architecture_signals": ["API surface"], "contradictions": []}
        )
        assert "token" not in summary.lower()
        assert "password" not in summary.lower()
        assert "secret" not in summary.lower()

    def test_deep_confidence_computation(self):
        """Confidence should be weighted average of dimensions."""
        from growthos.services.portfolio_deep_evidence import _deep_confidence
        synthesis = {
            "confidence_dimensions": {
                "implementation": 1.0,
                "testing": 1.0,
                "build": 1.0,
                "runtime": 1.0,
                "reproducibility": 1.0,
            }
        }
        assert _deep_confidence(synthesis) == 1.0

        synthesis_zero = {
            "confidence_dimensions": {
                "implementation": 0.0,
                "testing": 0.0,
                "build": 0.0,
                "runtime": 0.0,
                "reproducibility": 0.0,
            }
        }
        assert _deep_confidence(synthesis_zero) == 0.0


class TestBudgetAwareness:
    """Tests for rate-limit-aware deep analysis."""

    def test_max_requests_limits_source_files(self):
        """max_requests should cap source file fetches."""
        from unittest.mock import AsyncMock, MagicMock

        from growthos.domain.models_capability import RepositoryEvidence
        from growthos.intelligence.deep_evidence import analyze_repository_deep

        # Create a mock repo with a tree
        repo = MagicMock(spec=RepositoryEvidence)
        repo.full_name = "test/repo"
        repo.name = "repo"
        repo.primary_language = "Python"
        repo.default_branch = "main"
        repo.evidence_strength = "IMPLEMENTATION_PRESENT"
        repo.evidence_value_score = 0.5
        repo.ci_build_present = False
        repo.releases_present = False
        repo.tests_present = False
        repo.architecture_docs_present = False
        repo.source_present = True

        client = MagicMock()
        client.rate_limited = False
        client.get_tree = AsyncMock(return_value=["README.md", "a.py", "b.py", "c.py"])
        client.get_readme = AsyncMock(return_value="UmVhZG1l")  # base64 "Readme"
        client.get_file_content = AsyncMock(return_value="Y2xhc3MgRm9vOgogICAgcGFzcw==")  # base64 code

        import asyncio
        result = asyncio.run(analyze_repository_deep(client, repo, max_requests=3))

        # With max_requests=3: 1 tree + 1 readme + 1 source file
        assert result["requests_used"] <= 3
        assert result["files_analyzed"] <= 1  # only 1 source file possible

    def test_budget_exhausted_stops_fetching(self):
        """When budget is exhausted, remaining files should not be fetched."""
        from unittest.mock import AsyncMock, MagicMock

        from growthos.domain.models_capability import RepositoryEvidence
        from growthos.intelligence.deep_evidence import analyze_repository_deep

        repo = MagicMock(spec=RepositoryEvidence)
        repo.full_name = "test/repo"
        repo.name = "repo"
        repo.primary_language = "Python"
        repo.default_branch = "main"
        repo.evidence_strength = "IMPLEMENTATION_PRESENT"
        repo.evidence_value_score = 0.5
        repo.ci_build_present = False
        repo.releases_present = False
        repo.tests_present = False
        repo.architecture_docs_present = False
        repo.source_present = True

        client = MagicMock()
        client.rate_limited = True  # immediately rate limited
        client.get_tree = AsyncMock(return_value=["README.md", "a.py"])
        client.get_readme = AsyncMock(return_value=None)
        client.get_file_content = AsyncMock(return_value=None)

        import asyncio
        result = asyncio.run(analyze_repository_deep(client, repo, max_requests=5))

        assert result["budget_exhausted"] is True
        assert result["files_analyzed"] == 0

    def test_rate_limit_mid_fetch_stops(self):
        """If rate limit hits mid-fetch, remaining files are skipped."""
        from unittest.mock import AsyncMock, MagicMock

        from growthos.domain.models_capability import RepositoryEvidence
        from growthos.intelligence.deep_evidence import analyze_repository_deep

        repo = MagicMock(spec=RepositoryEvidence)
        repo.full_name = "test/repo"
        repo.name = "repo"
        repo.primary_language = "Python"
        repo.default_branch = "main"
        repo.evidence_strength = "IMPLEMENTATION_PRESENT"
        repo.evidence_value_score = 0.5
        repo.ci_build_present = False
        repo.releases_present = False
        repo.tests_present = False
        repo.architecture_docs_present = False
        repo.source_present = True

        call_count = 0

        def make_get_tree():
            async def get_tree(*a, **kw):
                return ["a.py", "b.py", "c.py"]
            return get_tree

        def make_get_file():
            async def get_file(*a, **kw):
                nonlocal call_count
                call_count += 1
                if call_count >= 2:
                    client.rate_limited = True
                return "Y2xhc3MgRm9vOgogICAgcGFzcw=="
            return get_file

        client = MagicMock()
        client.rate_limited = False
        client.get_tree = AsyncMock(return_value=["a.py", "b.py", "c.py"])
        client.get_readme = AsyncMock(return_value=None)
        client.get_file_content = AsyncMock(side_effect=make_get_file())

        import asyncio
        result = asyncio.run(analyze_repository_deep(client, repo, max_requests=6))

        # Should stop after rate limit is hit
        assert result["budget_exhausted"] is True
        assert result["files_analyzed"] < 3  # didn't finish all files
