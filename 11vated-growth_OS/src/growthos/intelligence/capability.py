"""Local-first Capability Intelligence.

Only configured roots are inspected. Repository source is never persisted or
sent to external services; the database receives hashes, paths, and summaries.
"""
from __future__ import annotations

import hashlib
import subprocess
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.enums import DeliveryMaturity
from growthos.domain.models_capability import (
    CapabilityEvidenceRecord,
    CapabilityPortfolioSnapshot,
    ProjectEvidenceRecord,
    TrustedRepositoryRoot,
)
from growthos.domain.models_scout import CapabilityCanon
from growthos.shared.ids import new_id

_SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
_BUILD_PREFIXES = ("build",)
_MANIFESTS = {"pyproject.toml", "package.json", "Cargo.toml", "go.mod", "pom.xml", "Makefile"}
_LANG_EXT = {".py": "Python", ".ts": "TypeScript", ".tsx": "TypeScript/React", ".js": "JavaScript", ".jsx": "JavaScript/React", ".rs": "Rust", ".go": "Go", ".cs": "C#", ".gd": "GDScript"}


def _run_git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _summary(readme: Path) -> str | None:
    if not readme.is_file():
        return None
    try:
        text = readme.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return None
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return " ".join(lines[:12])[:2000] or None


def discover_repositories(root: Path) -> list[Path]:
    """Return the authorized root itself or its immediate Git children only."""
    root = root.resolve()
    if not root.exists() or not root.is_dir():
        return []
    if (root / ".git").exists():
        return [root]
    try:
        candidates = [child for child in root.iterdir() if child.is_dir() and (child / ".git").exists()]
    except OSError:
        return []
    return sorted(candidates, key=lambda p: str(p).lower())


def validate_trusted_root(path: Path) -> tuple[bool, str]:
    """Validate an explicit root without permitting broad/system locations."""
    try:
        resolved = path.expanduser().resolve()
    except OSError as exc:
        return False, f"cannot resolve path: {exc}"
    if not resolved.is_dir():
        return False, "path is not a directory"
    if resolved == Path(resolved.anchor):
        return False, "system root is not an allowed trusted root"
    if len(resolved.parts) <= 3 or resolved.name.lower() in {"profile", "users", "desktop", "onedrive"}:
        return False, "root is too broad; choose a project/workspace directory"
    return True, str(resolved)


def inspect_repository(root_id: str, path: Path) -> dict[str, Any]:
    files: list[Path] = []
    languages: set[str] = set()
    manifests: list[str] = []
    source_dirs: set[str] = set()
    artifacts: list[str] = []
    digest = hashlib.sha256()
    try:
        for item in path.rglob("*"):
            if not item.is_file() or any(part in _SKIP for part in item.relative_to(path).parts):
                continue
            rel = item.relative_to(path)
            if rel.name in _MANIFESTS and not any(part.startswith(_BUILD_PREFIXES) for part in rel.parts):
                manifests.append(str(rel))
            if rel.parts and rel.parts[0] in {"src", "app", "apps", "packages", "lib", "tests", "docs"}:
                source_dirs.add(rel.parts[0])
            if rel.suffix.lower() in _LANG_EXT:
                languages.add(_LANG_EXT[rel.suffix.lower()])
            if rel.parts and (rel.parts[0] in {"dist", "release", "artifacts"} or rel.parts[0].startswith(_BUILD_PREFIXES)) and len(artifacts) < 50:
                artifacts.append(str(rel))
            if len(files) < 500:
                files.append(item)
            digest.update(str(rel).encode())
            with suppress(OSError):
                digest.update(str(item.stat().st_size).encode())
    except OSError:
        pass
    readme = next((path / name for name in ("README.md", "README.rst", "README.txt") if (path / name).exists()), None)
    test_count = sum(1 for f in files if "test" in f.parts or f.name.startswith("test_"))
    evidence_classes = []
    if any("test" in f.parts or f.name.startswith("test_") for f in files):
        evidence_classes.append("TEST_EVIDENCE")
    if manifests:
        evidence_classes.append("DIRECT_IMPLEMENTATION")
    if artifacts:
        evidence_classes.append("BUILD_EVIDENCE")
    if readme:
        evidence_classes.append("DOCUMENTED_CLAIM")
    return {
        "repository_root_id": root_id, "name": path.name, "path": str(path),
        "git_branch": _run_git(path, "branch", "--show-current"),
        "git_status": "clean" if _run_git(path, "status", "--porcelain") == "" else "modified",
        "remote_url": _run_git(path, "config", "--get", "remote.origin.url"),
        "readme_summary": _summary(readme) if readme else None,
        "languages": sorted(languages), "manifests": sorted(manifests),
        "source_directories": sorted(source_dirs), "test_summary": f"{test_count} test-like files observed" if test_count else None,
        "artifact_paths": artifacts[:50], "evidence_hash": digest.hexdigest(), "inspected_at": datetime.now(UTC),
        "evidence_classes": evidence_classes,
        "intelligence_profile": {
            "project_definition": (_summary(readme) if readme else None),
            "architecture": {"source_areas": sorted(source_dirs), "languages": sorted(languages), "manifests": sorted(manifests)},
            "testing": f"{test_count} test-like files observed" if test_count else None,
            "build": {"artifacts": artifacts[:20]},
            "known_limitations": ["Runtime/customer delivery evidence was not inferred from repository metadata."],
        },
    }


def propose_capabilities(project: dict[str, Any]) -> list[dict[str, Any]]:
    """Conservative rule-based proposals from actual manifests, languages, and docs."""
    corpus = " ".join([project.get("readme_summary") or "", *project.get("manifests", []), *project.get("source_directories", []), *project.get("languages", [])]).lower()
    proposals: list[dict[str, Any]] = []
    def add(name: str, definition: str, reason: str, category: str) -> None:
        proposals.append({"name": name, "definition": definition, "category": category, "reason": reason, "maturity": DeliveryMaturity.PROTOTYPE_PROVEN.value if project.get("test_summary") else DeliveryMaturity.EXPERIMENTAL.value, "confidence": 0.65 if project.get("test_summary") else 0.45})
    if "sprites" in corpus or "sprite" in corpus or "game" in corpus or "gdscript" in corpus:
        add("Interactive Sprite System Prototyping", "Prototype and extend interactive sprite-based systems where the project evidence demonstrates the behavior.", "Sprite/game-oriented source or documentation evidence was observed; this is intentionally narrower than full game development.", "interactive technology")
    if "cmake" in corpus or "cpp" in corpus or "c++" in corpus:
        add("Native Interactive Systems Prototyping", "Prototype performance-sensitive interactive systems in a native codebase when the specific implementation evidence supports it.", "Native build/source evidence was observed; customer delivery scope remains subject to founder review.", "interactive technology")
    if "react" in corpus or "typescript" in corpus or "frontend" in corpus:
        add("Interactive Frontend Development", "Build responsive interactive web interfaces from verified project evidence.", "TypeScript/React or frontend evidence was observed in the trusted repository.", "technical")
    if "fastapi" in corpus or "python" in corpus and "api" in corpus:
        add("Python API Systems", "Build and integrate Python-backed API services evidenced by the repository.", "Python API/framework evidence was observed.", "integration")
    if "ollama" in corpus or "local ai" in corpus or "agent" in corpus:
        add("Local AI Agent Integration", "Design local-first AI-assisted software workflows within verified runtime constraints.", "Local AI/agent evidence was observed in repository documentation or manifests.", "AI")
    return proposals


async def inspect_trusted_root(session: AsyncSession, root: TrustedRepositoryRoot) -> dict[str, Any]:
    projects = []
    proposals = []
    root.last_error = None
    root.last_scan_at = datetime.now(UTC)
    for path in discover_repositories(Path(root.path)):
        info = inspect_repository(root.id, path)
        existing = (await session.execute(select(ProjectEvidenceRecord).where(ProjectEvidenceRecord.path == info["path"]))).scalar_one_or_none()
        if existing is None:
            existing = ProjectEvidenceRecord(
                id=new_id(),
                **{key: value for key, value in info.items() if key != "evidence_classes"},
            )
            session.add(existing)
        else:
            for key, value in info.items():
                if key not in {"repository_root_id", "evidence_classes"}:
                    setattr(existing, key, value)
        await session.flush()
        project_proposals = propose_capabilities(info)
        for proposal in project_proposals:
            capability = (await session.execute(select(CapabilityCanon).where(CapabilityCanon.name == proposal["name"]))).scalar_one_or_none()
            if capability is None:
                capability = CapabilityCanon(id=new_id(), name=proposal["name"], definition=proposal["definition"], category=proposal["category"], maturity=proposal["maturity"], status="PROPOSED", external_claimable=False, entered_from="capability_intelligence", proof_evidence=[{"project": info["name"], "reason": proposal["reason"], "confidence": proposal["confidence"]}], related_completed_work=[info["name"]])
                session.add(capability)
                await session.flush()
            evidence = CapabilityEvidenceRecord(id=new_id(), capability_id=capability.id, project_id=existing.id, source_type="local_repository", source_location=info["path"], artifact=(info.get("readme_summary") or "")[:500], category=(info.get("evidence_classes") or ["EXPERIMENTAL_EVIDENCE"])[0], summary=proposal["reason"], confidence=proposal["confidence"], sensitivity="INTERNAL", verified_at=datetime.now(UTC), private=True)
            session.add(evidence)
            proposals.append({"capability_id": capability.id, "name": capability.name, "project": info["name"], "confidence": proposal["confidence"], "status": str(capability.status), "maturity": proposal["maturity"]})
        projects.append(info)
    await session.flush()
    return {"root": root.path, "projects": projects, "proposals": proposals}


async def portfolio_snapshot(session: AsyncSession) -> dict[str, Any]:
    rows = list((await session.execute(select(CapabilityCanon))).scalars().all())
    verified = [c for c in rows if str(c.status) in {"CapabilityStatus.FOUNDER_CONFIRMED", "CapabilityStatus.EVIDENCE_VERIFIED", "FOUNDER_CONFIRMED", "EVIDENCE_VERIFIED"} and c.external_claimable]
    proposed = [c for c in rows if c not in verified and str(c.status) not in {"CapabilityStatus.RETIRED", "RETIRED"}]
    payload = {"verified": [{"id": c.id, "name": c.name} for c in verified], "proposed": [{"id": c.id, "name": c.name} for c in proposed], "summary": f"{len(verified)} externally claimable capabilities and {len(proposed)} proposals; source code remains local."}
    session.add(CapabilityPortfolioSnapshot(id=new_id(), generated_at=datetime.now(UTC), summary=payload["summary"], verified_capability_ids=[c.id for c in verified], proposed_capability_ids=[c.id for c in proposed], demand_summary={}, private_source_count=len(rows)))
    await session.flush()
    return payload
