#!/usr/bin/env python3
"""Audit professional pack claims without treating keyword matches as proof."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PACK_DIR = ROOT / "config" / "resource-packs"
OUT = ROOT / "artifacts" / "kapif" / "m002.1" / "pack-claim-audit.json"
PACKS = {
    "ART_DIRECTION_LOOKDEV_CORE": "art-direction-lookdev-core.json",
    "COMPOSITION_VALUE_COLOR_CORE": "composition-value-color-core.json",
    "TYPOGRAPHY_INFORMATION_DESIGN_CORE": "typography-information-design-core.json",
    "FRONTEND_UI_UX_CORE": "frontend-ui-ux-core.json",
    "UI_UX_INTERACTION_CORE": "ui-ux-interaction-core.json",
    "MOTION_DESIGN_CORE": "motion-design-core.json",
}
CANDIDATE_TERMS = re.compile(
    r"\b(must|minimum|maximum|requires|required|standard|official|optimal|always|never|"
    r"industry standard|best practice|recommended|\d+(?:\.\d+)?\s*(?:px|ms|s|%|:1|ch))\b",
    re.I,
)
NORMATIVE_CLASSES = {"NORMATIVE", "OFFICIAL_GUIDANCE"}


def _walk(value: Any, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def _claim_class(entry: dict[str, Any]) -> str:
    explicit = entry.get("knowledge_class") or entry.get("class")
    if explicit:
        return explicit
    if entry.get("source_evidence") == "MODEL_KNOWLEDGE":
        return "DRAFT_HEURISTIC"
    return "UNCLASSIFIED"


def audit_pack(pack_id: str, path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    source_urls = {s.get("url") for s in data.get("sources", []) if isinstance(s, dict) and s.get("url")}
    candidates = []
    significant = []
    grounded = 0
    primary_grounded = 0
    heuristic_only = 0
    open_questions = 0
    for location, text in _walk(data):
        if len(text) < 18:
            continue
        # Avoid counting metadata and prose that is not a claim.
        if location.endswith(".url") or location.endswith(".title") or location.endswith(".date"):
            continue
        if any(token in location for token in ("principle", "definition", "fact", "goal", "repair", "success", "transfers", "version", "description")):
            significant.append({"location": location, "claim": text})
        if CANDIDATE_TERMS.search(text):
            candidates.append({"location": location, "claim": text, "classification": "CANDIDATE_DISCOVERY_ONLY"})
    for entry in data.get("foundations", {}).values() if isinstance(data.get("foundations"), dict) else []:
        if not isinstance(entry, list):
            continue
        for item in entry:
            if not isinstance(item, dict):
                continue
            cls = _claim_class(item)
            if cls == "DRAFT_HEURISTIC":
                heuristic_only += 1
            if cls == "OPEN_QUESTION":
                open_questions += 1
            if item.get("source_ids") or item.get("source_url") or item.get("source_evidence") not in (None, "MODEL_KNOWLEDGE"):
                grounded += 1
            if item.get("source_authority") in ("W3C Recommendation", "W3C WAI", "WHATWG", "official"):
                primary_grounded += 1
    report = {
        "pack_id": pack_id,
        "status": data.get("status"),
        "research_needed": data.get("research_needed", True),
        "significant_claim_count": len(significant),
        "normative_candidate_count": len(candidates),
        "grounded_entry_count": grounded,
        "primary_source_grounded_entry_count": primary_grounded,
        "heuristic_only_count": heuristic_only,
        "open_question_count": open_questions,
        "declared_source_count": len(source_urls),
        "source_validation_status": "NOT_VALIDATED" if candidates else "NO_CANDIDATES_FOUND",
        "claims": candidates,
        "note": "Regex/term discovery is not normative validation; each normative claim requires exact authoritative support.",
    }
    return report


def run() -> dict[str, Any]:
    reports = [audit_pack(pack_id, PACK_DIR / filename) for pack_id, filename in PACKS.items()]
    result = {
        "schema_version": 1,
        "kind": "m002.1-pack-claim-audit",
        "audit_status": "CANDIDATE_INVENTORY_COMPLETE_SOURCE_VALIDATION_INCOMPLETE",
        "packs": reports,
        "governing_rule": "NORMATIVE claims require primary evidence; heuristics remain draft until grounded.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
