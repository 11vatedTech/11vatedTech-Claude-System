"""Targeted, local-only deep evidence analysis for capability proposals."""
from __future__ import annotations

import re
import subprocess
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from growthos.domain.models_capability import CapabilityEvidenceRecord, ProjectEvidenceRecord
from growthos.domain.models_scout import CapabilityCanon

_SECRET = re.compile(r"(?i)(password|secret|token|api[_-]?key|private[_-]?key|connection.?string)")


def sanitize_commercial_text(text: str) -> str:
    """Keep commercial summaries free of paths, secrets, and private internals."""
    text = re.sub(r"(?i)(password|secret|token|api[_-]?key|private[_-]?key|connection.?string)\s*[:=]\s*[^\s]+", "[internal detail omitted]", text)
    text = _SECRET.sub("[internal detail omitted]", text)
    text = re.sub(r"[A-Za-z]:\\[^\s]+", "[private project reference]", text)
    text = re.sub(r"https?://[^\s]*:[^\s]*@", "https://[private remote omitted]", text)
    return text[:2000]


def _git(path: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _files(path: Path) -> list[Path]:
    skip = {".git", "build", "node_modules", ".venv", "__pycache__"}
    found: list[Path] = []
    with suppress(OSError):
        for item in path.rglob("*"):
            if item.is_file() and not any(part in skip or part.startswith("build") for part in item.relative_to(path).parts):
                found.append(item)
    return found


def _classify(file: Path, rel: str) -> str:
    lower = rel.lower()
    if "test" in lower or "spec" in lower:
        return "RUNTIME_EVIDENCE" if any(x in lower for x in ("integration", "e2e", "runtime", "smoke")) else "TEST_EVIDENCE"
    if any(x in lower for x in ("cmake", "build", "release", "artifact")):
        return "BUILD_EVIDENCE"
    if any(x in lower for x in ("readme", "docs", "openspec", "architecture")):
        return "DOCUMENTED_CLAIM"
    return "DIRECT_IMPLEMENTATION"


def analyze_project(project: ProjectEvidenceRecord) -> dict[str, Any]:
    path = Path(project.path)
    all_files = _files(path)
    classes: dict[str, list[str]] = {}
    sensitive_count = 0
    for file in all_files:
        rel = str(file.relative_to(path))
        category = _classify(file, rel)
        if _SECRET.search(file.name) or file.suffix.lower() in {".env", ".pem", ".key"}:
            sensitive_count += 1
            continue
        classes.setdefault(category, []).append(rel)
    source_text = " ".join(classes.get("DIRECT_IMPLEMENTATION", []) + classes.get("DOCUMENTED_CLAIM", []))
    sprite_terms = [x for x in ("sprite", "living", "entity", "transform", "damage", "heal", "animation", "render", "asset", "compiler", "runtime") if x in source_text.lower()]
    frontend_terms = [x for x in ("react", "typescript", "frontend", "browser", "component", "css", "web") if x in source_text.lower()]
    runtime_status = "RUNTIME_PARTIAL" if classes.get("RUNTIME_EVIDENCE") else "STATIC_ONLY"
    runtime_commands = [x for x in ("ctest", "pytest", "npm test", "dotnet test", "cmake --build") if _git(path, "grep", "-n", x) is not None]
    return {
        "analyzed_at": datetime.now(UTC).isoformat(),
        "evidence_counts": {key: len(value) for key, value in classes.items()},
        "evidence_samples": {key: value[:20] for key, value in classes.items()},
        "sprite_system_terms": sprite_terms,
        "frontend_terms": frontend_terms,
        "runtime_status": runtime_status,
        "runtime_commands": runtime_commands,
        "sensitive_files_omitted": sensitive_count,
        "contradictions": ["No customer deployment or external delivery record was found in the inspected repository evidence."],
        "missing": ["Founder confirmation", "independent customer delivery evidence", "production client runtime evidence"],
        "reproducibility": "MEDIUM" if len(classes.get("DIRECT_IMPLEMENTATION", [])) > 10 and classes.get("TEST_EVIDENCE") else "UNKNOWN",
        "client_deliverability": "prototype engagement plausible; production delivery not established",
    }


def capability_review( name: str, deep: dict[str, Any]) -> dict[str, Any]:
    is_sprite = "sprite" in name.lower()
    direct = min(0.85, 0.35 + 0.08 * len(deep.get("sprite_system_terms", []) if is_sprite else deep.get("frontend_terms", [])))
    runtime = 0.65 if deep.get("runtime_status") == "RUNTIME_VERIFIED" else 0.35 if deep.get("runtime_status") == "RUNTIME_PARTIAL" else 0.15
    reproducibility_label = str(deep.get("reproducibility") or "UNKNOWN")
    repro = {"HIGH": 0.85, "MEDIUM": 0.6, "LOW": 0.3, "UNKNOWN": 0.15}.get(reproducibility_label, 0.15)
    delivery = min(0.8, (direct + runtime + repro) / 3)
    commercial = 0.35 if is_sprite else 0.15
    recommendation = "CONFIRM_AFTER_EDIT" if is_sprite and direct >= 0.5 else "REJECT"
    return {
        "implementation_confidence": round(direct, 2), "runtime_confidence": round(runtime, 2),
        "reproducibility_confidence": round(repro, 2), "delivery_confidence": round(delivery, 2),
        "commercial_relevance_confidence": commercial, "evidence_coverage": deep.get("evidence_counts", {}),
        "recommended_maturity": "PROTOTYPE_PROVEN" if runtime >= 0.3 else "EXPERIMENTAL",
        "recommended_decision": recommendation,
        "recommendation_reason": "Direct implementation and test evidence support a narrow prototype capability; client and production evidence remain absent." if is_sprite else "The inspected frontend evidence appears to support project UI, not an independent commercial frontend capability.",
        "supporting_evidence": deep.get("evidence_samples", {}), "contradicting_evidence": deep.get("contradictions", []), "missing_evidence": deep.get("missing", []),
        "reproducibility": deep.get("reproducibility"), "client_deliverability": deep.get("client_deliverability"),
        "external_summary": sanitize_commercial_text("A narrowly scoped prototype capability grounded in an inspected interactive software project; customer scope, delivery maturity, and production readiness require founder confirmation." if is_sprite else "This project includes supporting operator UI, but does not independently establish a general commercial frontend capability."),
    }


async def deepen_capability(session: AsyncSession, capability: CapabilityCanon) -> dict[str, Any]:
    project = (await session.execute(select(ProjectEvidenceRecord).where(ProjectEvidenceRecord.name == "GSPL-Sprites"))).scalar_one_or_none()
    if project is None:
        raise ValueError("GSPL-Sprites project evidence is not available")
    deep = analyze_project(project)
    review = capability_review(capability.name, deep)
    profile = dict(project.intelligence_profile or {})
    profile["deep_capability_review"] = review
    project.intelligence_profile = profile
    capability.proof_evidence = [{"project": project.name, "review": review["recommendation_reason"], "evidence_coverage": review["evidence_coverage"], "status": "REQUEST_MORE_EVIDENCE"}]
    capability.limitations = [*capability.limitations, "No independent customer delivery or production deployment evidence established."]
    evidence = CapabilityEvidenceRecord(id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"growthos:deep:{capability.id}:{project.evidence_hash}")), capability_id=capability.id, project_id=project.id, source_type="local_repository_deep_review", source_location="project evidence reference", artifact="deep evidence analysis", category="DIRECT_IMPLEMENTATION", summary=sanitize_commercial_text(review["recommendation_reason"]), confidence=review["implementation_confidence"], sensitivity="INTERNAL", verified_at=datetime.now(UTC), private=True)
    session.add(evidence)
    await session.flush()
    return {"capability_id": capability.id, "name": capability.name, "project": project.name, "deep_evidence": deep, "review": review}
