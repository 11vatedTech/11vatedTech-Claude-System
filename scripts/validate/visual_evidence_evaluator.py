#!/usr/bin/env python3
"""Reusable visual evidence evaluator.

Combines the existing perceptual image diagnostics with explicit failure-pattern
checks from the high-fidelity reliability model. It reports structural,
perceptual, artistic, and cohesion states separately. It can reject known-bad
visual evidence without pretending to replace an independent art review.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
from perceptual_visual_qa import analyze  # type: ignore

PATTERNS = {
    "black_void": (r"black[_ -]?crush|black void|near[- ]?black|empty black", "major_black_crush_in_player_critical_regions"),
    "test_chamber": (r"checker|test chamber|empty room|floating hero|no environment", "test_environment_presentation"),
    "emissive_only": (r"emissive core|bright disc|red wash|yellow.*red", "emissive_core_substitutes_for_lighting"),
    "generic_hud": (r"debug[- ]?like|primitive hud|plain debug text|generic hud", "generic_or_debug_hud"),
    "state_color_only": (r"color only|yellow.*red|hue only|state communication mainly", "color_only_state_language"),
    "primitive_vfx": (r"particle spam|point[- ]?sprite|weak vfx|poor shape|poor timing", "vfx_artistic_qa_gap"),
}


def flatten_text(doc: object) -> str:
    if isinstance(doc, str):
        return doc
    return json.dumps(doc, ensure_ascii=False)


def evaluate(images: list[Path], context: str = "", max_stage: str = "POLISHED") -> dict:
    diagnostics = []
    for image in images:
        diagnostics.append(analyze(image))
    context_lower = context.lower()
    blockers = []
    matched = []
    for _, (pattern, label) in PATTERNS.items():
        if re.search(pattern, context_lower, re.I):
            matched.append(label)
            blockers.append(label)
    if any(record.get("failures") for record in diagnostics):
        blockers.append("perceptual_metric_failure")
    if any("low_subject_background_separation" in record.get("warnings", []) for record in diagnostics):
        blockers.append("low_subject_background_separation")
    if any("subject_occupancy_too_small" in record.get("warnings", []) for record in diagnostics):
        blockers.append("subject_occupancy_too_small")
    if any("subject_or_threshold_occupancy_too_large" in record.get("warnings", []) for record in diagnostics):
        blockers.append("composition_occupancy_warning")
    blockers = sorted(set(blockers))
    stages = ["BLOCKOUT", "FUNCTIONAL", "COHERENT", "POLISHED", "PRODUCTION", "SIGNATURE"]
    allowed_index = stages.index(max_stage) if max_stage in stages else 3
    if blockers:
        allowed_index = min(allowed_index, stages.index("COHERENT"))
    result = {
        "schema_version": 1,
        "kind": "visual-evidence-evaluation",
        "structural_validity": "EVIDENCE_PRESENT" if images and all(p.exists() for p in images) else "MISSING",
        "functional_validity": "UNASSESSED",
        "perceptual_quality": "BLOCKED" if blockers else "DIAGNOSTIC_PASS",
        "artistic_quality": "REQUIRES_INDEPENDENT_REVIEW",
        "product_cohesion": "UNASSESSED",
        "matched_failure_patterns": matched,
        "blockers": blockers,
        "maximum_supported_stage": stages[allowed_index],
        "diagnostics": diagnostics,
        "limitations": [
            "context pattern matching is a safety net, not semantic vision",
            "metrics do not establish composition, taste, originality, or game feel",
            "independent multimodal review and human evidence remain required"
        ]
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--context", default="")
    parser.add_argument("--context-file", type=Path)
    parser.add_argument("--max-stage", default="POLISHED")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    context = args.context
    if args.context_file:
        context += "\n" + args.context_file.read_text(encoding="utf-8", errors="replace")
    result = evaluate(args.images, context, args.max_stage)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not result["blockers"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
