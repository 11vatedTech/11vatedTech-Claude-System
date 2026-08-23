"""Unit tests for the GitHub portfolio evidence census (pure, deterministic)."""

from __future__ import annotations

from growthos.intelligence.github_portfolio import (
    classify_repository,
    cluster_families,
    family_overlap_note,
    repo_stem,
    score_repository,
    select_deep_analysis,
)


def _meta(name: str, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "name": name,
        "full_name": f"owner/{name}",
        "html_url": f"https://github.com/owner/{name}",
        "description": "",
        "topics": [],
        "visibility": "public",
        "archived": False,
        "fork": False,
        "default_branch": "main",
        "language": None,
        "size": 0,
        "stargazers_count": 0,
        "pushed_at": None,
    }
    base.update(overrides)
    return base


def test_empty_repo_is_empty_or_minimal() -> None:
    result = classify_repository(_meta("empty"), [".gitignore", "LICENSE"])
    assert result["empty_or_minimal"] is True
    assert result["evidence_strength"] == "EMPTY_OR_MINIMAL"


def test_readme_only_is_documentation_only() -> None:
    result = classify_repository(_meta("docs-only", size=5), ["README.md"])
    assert result["readme_present"] is True
    assert result["source_present"] is False
    assert result["evidence_strength"] == "DOCUMENTATION_ONLY"


def test_source_and_readme_is_implementation_present() -> None:
    result = classify_repository(
        _meta("impl", size=200, language="Python"),
        ["README.md", "src/main.py", "app/core.py"],
    )
    assert result["source_present"] is True
    assert result["evidence_strength"] == "IMPLEMENTATION_PRESENT"


def test_tests_ci_and_releases_escalate_strength() -> None:
    tree = [
        "README.md", "src/main.py", "tests/test_main.py",
        ".github/workflows/ci.yml", "docs/architecture.md",
    ]
    base = classify_repository(_meta("strong", size=500, language="Python"), tree)
    assert base["evidence_strength"] == "BUILD_EVIDENCE_PRESENT"

    with_release = classify_repository(
        _meta("strong", size=500, language="Python"), tree, releases_present=True
    )
    assert with_release["evidence_strength"] == "STRONG_CAPABILITY_EVIDENCE"


def test_score_rewards_more_evidence() -> None:
    minimal = classify_repository(_meta("minimal"), ["README.md"])
    strong = classify_repository(
        _meta("strong", size=500, language="Python", stargazers_count=5),
        ["README.md", "src/main.py", "tests/test_main.py", ".github/workflows/ci.yml"],
        releases_present=True,
    )
    minimal_score, _ = score_repository(minimal)
    strong_score, breakdown = score_repository(strong)
    assert strong_score > minimal_score
    assert breakdown["implementation_depth"] > 0
    assert breakdown["test_evidence"] > 0


def test_repo_stem_clusters_lineage_variants() -> None:
    # GSPL/Paradigm variants collapse to one family root each.
    assert repo_stem("GSPL-Sprites") == "gspl"
    assert repo_stem("GSPL_AI") == "gspl"
    assert repo_stem("GSPL") == "gspl"
    assert repo_stem("Paradigm") == "paradigm"
    assert repo_stem("paradigm-sprites") == "paradigm"
    # Version/suffix words are dropped; generic words don't form their own root.
    assert repo_stem("My-App-v2") == "my"
    assert repo_stem("My-App-api") == "my"
    assert repo_stem("thing") == "thing"


def test_cluster_families_groups_same_lineage() -> None:
    repos = [
        {"name": "my-app", "full_name": "o/my-app", "topics": ["web"], "languages": ["TypeScript"], "score": 0.6},
        {"name": "my-app-v2", "full_name": "o/my-app-v2", "topics": ["web", "react"], "languages": ["TypeScript"], "score": 0.8},
        {"name": "game-engine", "full_name": "o/game-engine", "topics": ["game"], "languages": ["GDScript"], "score": 0.5},
    ]
    families = cluster_families(repos)
    # my-app and my-app-v2 share a stem -> one family; game-engine is separate.
    assert len(families) == 2


def test_family_overlap_note_only_for_multi_member() -> None:
    single = [{"name": "a"}]
    multi = [{"name": "a"}, {"name": "a-v2"}]
    assert family_overlap_note(single) is None
    note = family_overlap_note(multi)
    assert note and "ONE evidence family" in note


def test_select_deep_analysis_is_bounded_and_diverse() -> None:
    repos = [
        {"name": f"repo{i}", "full_name": f"o/repo{i}", "topics": [], "languages": [], "score": 0.1 * i}
        for i in range(1, 21)
    ]
    families = cluster_families(repos)
    selected = select_deep_analysis(repos, families, max_count=8)
    assert len(selected) <= 8
    assert len(set(selected)) == len(selected)
