from pathlib import Path

from growthos.intelligence.capability import (
    discover_repositories,
    inspect_repository,
    propose_capabilities,
    validate_trusted_root,
)


def test_root_itself_is_a_repository(tmp_path: Path):
    repo = tmp_path / "GSPL-Sprites"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert discover_repositories(repo) == [repo]


def test_discovery_only_returns_git_repositories(tmp_path: Path):
    (tmp_path / "not-repo").mkdir()
    repo = tmp_path / "real-repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert discover_repositories(tmp_path) == [repo]


def test_inspection_persists_metadata_not_source(tmp_path: Path):
    repo = tmp_path / "growth"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("Interactive frontend and local AI agent", encoding="utf-8")
    (repo / "package.json").write_text("{}", encoding="utf-8")
    info = inspect_repository("root", repo)
    assert info["name"] == "growth"
    assert "package.json" in info["manifests"]
    assert "Interactive frontend" in info["readme_summary"]
    assert "source" not in info


def test_trusted_root_boundary_rejects_broad_directory(tmp_path: Path):
    broad = tmp_path / "profile"
    broad.mkdir()
    ok, reason = validate_trusted_root(broad)
    assert not ok
    assert "broad" in reason


def test_proposals_are_not_approved():
    proposals = propose_capabilities({"name": "x", "languages": ["TypeScript/React"], "manifests": ["package.json"], "source_directories": ["src"], "readme_summary": "frontend", "test_summary": None})
    assert proposals
    assert all(p["confidence"] < 1 for p in proposals)
