"""Integration tests for portfolio deep evidence pass."""

from __future__ import annotations

import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from growthos.domain.models import (
    RepositoryEvidence,
)
from growthos.shared.ids import new_id

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TEST_DB_URL = os.environ.get(
    "GROWTHOS_TEST_DATABASE_URL",
    "postgresql+asyncpg://growthos:growthos@localhost:5434/growthos_test",
)


@pytest_asyncio.fixture
async def db_session():
    """Create a clean test database session."""
    engine = create_async_engine(TEST_DB_URL, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Import all models to register metadata
    import growthos.domain.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(growthos.domain.models.Base.metadata.create_all)

    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(growthos.domain.models.Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_test_repo(
    session: AsyncSession,
    full_name: str,
    *,
    source_present: bool = True,
    tests_present: bool = True,
    ci_build: bool = True,
    releases: bool = False,
    evidence_strength: str = "TEST_EVIDENCE_PRESENT",
    score: float = 0.5,
) -> RepositoryEvidence:
    """Create a minimal RepositoryEvidence row for testing."""
    repo = RepositoryEvidence(
        id=new_id(),
        profile_id="test-profile",
        owner="test-owner",
        name=full_name.split("/")[-1],
        full_name=full_name,
        html_url=f"https://github.com/{full_name}",
        description=f"Test repo {full_name}",
        topics=["test"],
        visibility="public",
        archived=False,
        fork=False,
        default_branch="main",
        primary_language="Python",
        languages=["Python"],
        size_kb=100,
        stargazers=0,
        readme_present=True,
        source_present=source_present,
        tests_present=tests_present,
        ci_build_present=ci_build,
        releases_present=releases,
        architecture_docs_present=False,
        empty_or_minimal=False,
        evidence_strength=evidence_strength,
        evidence_value_score=score,
        score_breakdown={},
        last_scanned_at=None,
    )
    session.add(repo)
    await session.flush()
    return repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDeepEvidenceAnalysis:
    """Tests for the deep evidence analysis pipeline."""

    @pytest.mark.asyncio
    async def test_analyze_file_content_implementation(self):
        """Verify implementation detection in Python code."""
        from growthos.intelligence.deep_evidence import EvidenceClass, analyze_file_content

        content = """
class SpriteManager:
    def __init__(self):
        self.sprites = []

    async def update(self):
        for sprite in self.sprites:
            sprite.render()

    def add_sprite(self, name: str):
        sprite = Sprite(name)
        self.sprites.append(sprite)
        return sprite
"""
        result = analyze_file_content(content, "manager.py", "Python")
        assert EvidenceClass.DIRECT_IMPLEMENTATION in result["evidence_classes"]
        assert result["implementation_signals"] > 3
        assert "SpriteManager" in result["module_names"]

    @pytest.mark.asyncio
    async def test_analyze_file_content_test(self):
        """Verify test detection."""
        from growthos.intelligence.deep_evidence import EvidenceClass, analyze_file_content

        content = """
import pytest
from manager import SpriteManager

def test_create_manager():
    mgr = SpriteManager()
    assert mgr is not None

def test_add_sprite():
    mgr = SpriteManager()
    sprite = mgr.add_sprite("hero")
    assert sprite is not None

def test_update():
    mgr = SpriteManager()
    mgr.add_sprite("hero")
    mgr.update()
"""
        result = analyze_file_content(content, "test_manager.py", "Python")
        assert EvidenceClass.TEST_EVIDENCE in result["evidence_classes"]
        assert result["test_signals"] > 3

    @pytest.mark.asyncio
    async def test_synthesize_strong_repo(self):
        """Verify synthesis of a strong repository with tests and CI."""
        from growthos.intelligence.deep_evidence import synthesize_deep_evidence

        file_analyses = [
            {
                "file_path": "src/main.py",
                "evidence_classes": ["DIRECT_IMPLEMENTATION"],
                "implementation_signals": 15,
                "test_signals": 0,
                "build_signals": 0,
                "roadmap_signals": 0,
                "module_names": ["App", "Router", "Handler"],
                "architecture_signals": ["API surface", "routing layer", "middleware"],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 300,
            },
            {
                "file_path": "tests/test_main.py",
                "evidence_classes": ["TEST_EVIDENCE"],
                "implementation_signals": 0,
                "test_signals": 10,
                "build_signals": 0,
                "roadmap_signals": 0,
                "module_names": ["test_app", "test_router"],
                "architecture_signals": [],
                "impl_details": [],
                "roadmap_details": [],
                "line_count": 150,
            },
        ]

        synthesis = synthesize_deep_evidence(
            None, file_analyses,
            {"primary_language": "Python", "ci_build_present": True,
             "releases_present": False, "tests_present": True,
             "architecture_docs_present": False, "source_present": True}
        )

        assert synthesis["implementation_files"] == 1
        assert synthesis["test_files"] == 1
        assert synthesis["maturity_assessment"] in ("PROTOTYPE_PROVEN", "INTERNAL_PROVEN")
        assert synthesis["confidence_dimensions"]["implementation"] > 0.2
        assert synthesis["confidence_dimensions"]["testing"] > 0.2
        assert "API surface" in synthesis["architecture_signals"]

    @pytest.mark.asyncio
    async def test_synthesize_roadmap_heavy_repo(self):
        """Verify that roadmap-heavy repos are correctly identified as weak."""
        from growthos.intelligence.deep_evidence import synthesize_deep_evidence

        file_analyses = [
            {
                "file_path": "docs/ROADMAP.md",
                "evidence_classes": ["DOCUMENTED_CLAIM"],
                "implementation_signals": 1,
                "test_signals": 0,
                "build_signals": 0,
                "roadmap_signals": 10,
                "module_names": [],
                "architecture_signals": [],
                "impl_details": [],
                "roadmap_details": [("roadmap language", 8)],
                "line_count": 200,
            },
        ]

        synthesis = synthesize_deep_evidence(
            None, file_analyses,
            {"primary_language": None, "ci_build_present": False,
             "releases_present": False, "tests_present": False,
             "architecture_docs_present": True, "source_present": True}
        )

        assert synthesis["implementation_files"] == 0
        assert synthesis["maturity_assessment"] == "EXPERIMENTAL"
        assert len(synthesis["contradictions"]) > 0


class TestFileSelection:
    """Tests for deep file selection."""

    def test_select_deep_files_priority(self):
        """README should come first, then config, then source, then test."""
        from growthos.intelligence.github_portfolio import select_deep_files

        paths = [
            "LICENSE",
            "src/main.py",
            "tests/test_main.py",
            "README.md",
            "pyproject.toml",
            ".github/workflows/ci.yml",
        ]
        selected = select_deep_files(paths)
        assert selected[0] == "README.md"
        assert "pyproject.toml" in selected

    def test_select_deep_files_limits(self):
        """Should respect max_files limit."""
        from growthos.intelligence.github_portfolio import select_deep_files

        paths = [f"src/module_{i}.py" for i in range(50)]
        selected = select_deep_files(paths, max_files=10)
        assert len(selected) == 10


class TestGitHubClient:
    """Tests for GitHub client health states."""

    def test_client_initialization(self):
        """Client initializes with correct health state."""
        from growthos.intelligence.github_portfolio import GitHubHealthState, GitHubProfileClient
        client = GitHubProfileClient()
        assert client.health_state == GitHubHealthState.UNKNOWN
        assert client.rate_limited is False
        assert client.auth_error is False

    def test_health_report_structure(self):
        """Health report contains expected fields without secrets."""
        from growthos.intelligence.github_portfolio import GitHubProfileClient
        client = GitHubProfileClient()
        report = client.health_report()
        assert "mode" in report
        assert "has_token" in report
        assert "rate_remaining" in report
        assert "token" not in str(report)
        assert "Bearer" not in str(report)


class TestProposalReassessment:
    """Tests for proposal reassessment logic."""

    @pytest.mark.asyncio
    async def test_frontend_reassessment_weak(self):
        """Frontend proposal with no frontend evidence should be rejected."""
        from growthos.services.portfolio_deep_evidence import _reassess_frontend

        deep_results = [
            {
                "name": "some-repo",
                "synthesis": {
                    "implementation_files": 1,
                    "total_roadmap_signals": 5,
                    "architecture_signals": ["database layer"],
                    "unique_modules": ["Database", "Query"],
                }
            }
        ]

        result = _reassess_frontend(deep_results)
        assert result["decision"] in ("REJECT", "NARROW")

    @pytest.mark.asyncio
    async def test_local_ai_reassessment_strong(self):
        """AI proposal with strong evidence should be kept."""
        from growthos.services.portfolio_deep_evidence import _reassess_local_ai

        deep_results = [
            {
                "name": "nexus",
                "synthesis": {
                    "implementation_files": 8,
                    "total_roadmap_signals": 1,
                    "architecture_signals": ["plugin system", "event system"],
                    "unique_modules": ["Agent", "LLM", "Brain", "Chat", "Model"],
                }
            },
            {
                "name": "atlas",
                "synthesis": {
                    "implementation_files": 6,
                    "total_roadmap_signals": 0,
                    "architecture_signals": ["adapter pattern"],
                    "unique_modules": ["Discovery", "Analysis", "Agent"],
                }
            },
            {
                "name": "gspl-agent",
                "synthesis": {
                    "implementation_files": 5,
                    "total_roadmap_signals": 2,
                    "architecture_signals": ["hook system"],
                    "unique_modules": ["Agent", "Tool", "Plugin"],
                }
            },
        ]

        result = _reassess_local_ai(deep_results)
        assert result["decision"] == "KEEP"
        assert len(result["evidence_support"]) >= 3


class TestNewCapabilityDiscovery:
    """Tests for new capability discovery from deep evidence."""

    def test_discovers_data_pipeline(self):
        """Should discover data pipeline capability from evidence."""
        from growthos.services.portfolio_deep_evidence import _discover_new_capabilities

        deep_results = [
            {
                "name": "scrape-engine",
                "synthesis": {
                    "unique_modules": ["Scraper", "Parser", "Extractor", "Pipeline"],
                    "architecture_signals": ["pipeline architecture"],
                }
            },
            {
                "name": "data-pipeline",
                "synthesis": {
                    "unique_modules": ["Ingest", "Transform", "Load"],
                    "architecture_signals": ["pipeline architecture"],
                }
            },
        ]

        new_caps = _discover_new_capabilities(deep_results)
        data_caps = [c for c in new_caps if "Data" in c["name"] or "Pipeline" in c["name"]]
        assert len(data_caps) > 0


class TestCredentialLeakPrevention:
    """Tests ensuring credentials never leak."""

    def test_evidence_summary_no_secrets(self):
        """Evidence summary should never contain secrets."""
        from growthos.intelligence.deep_evidence import _evidence_summary

        summary = _evidence_summary(
            {"full_name": "org/repo", "name": "repo"},
            {"files_analyzed": 5, "implementation_files": 3, "test_files": 1,
             "maturity_assessment": "PROTOTYPE_PROVEN", "reproducibility": "MEDIUM",
             "architecture_signals": ["API surface"], "contradictions": []}
        )
        assert "token" not in summary.lower()
        assert "password" not in summary.lower()
        assert "secret" not in summary.lower()

    def test_client_never_logs_token(self):
        """Client operations should never log the token."""
        from growthos.intelligence.github_portfolio import GitHubProfileClient
        client = GitHubProfileClient(token="ghp_SECRET123")
        report = client.health_report()
        assert "ghp_SECRET123" not in str(report)
        assert "SECRET123" not in str(report)
