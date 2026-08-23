#!/usr/bin/env python3
"""Frontend quality contract evaluator.

It checks declared evidence and hard blockers; it does not replace browser or
human review. A Lighthouse or axe result alone cannot promote visual or UX
maturity.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = ("product_character", "user_type", "visual_thesis", "states", "viewports", "evidence")
REQUIRED_STATES = {"loading", "empty", "error", "success", "focus"}


def evaluate(doc: dict) -> dict:
    missing = [key for key in REQUIRED if not doc.get(key)]
    states = set(doc.get("states", []))
    viewports = set(doc.get("viewports", []))
    evidence = doc.get("evidence", {})
    blockers = []
    if missing:
        blockers.append("missing_frontend_contract_fields")
    if not REQUIRED_STATES.issubset(states):
        blockers.append("incomplete_state_inventory")
    if not {"mobile", "desktop"}.issubset(viewports):
        blockers.append("responsive_viewport_matrix_incomplete")
    if not evidence.get("screenshots"):
        blockers.append("rendered_screenshot_evidence_missing")
    if not evidence.get("keyboard_review"):
        blockers.append("manual_keyboard_review_missing")
    if not evidence.get("accessibility_scan"):
        blockers.append("automated_accessibility_evidence_missing")
    if not evidence.get("performance_metrics"):
        blockers.append("performance_evidence_missing")
    if evidence.get("lighthouse_score") is not None and evidence.get("lighthouse_score") >= 90 and not evidence.get("visual_review"):
        blockers.append("lighthouse_cannot_certify_visual_or_ux_quality")
    if evidence.get("axe_pass") is True and not evidence.get("keyboard_review"):
        blockers.append("axe_pass_does_not_replace_keyboard_review")
    return {
        "schema_version": 1,
        "kind": "frontend-quality-contract",
        "decision": "REVIEW_REQUIRED" if blockers else "EVIDENCE_COMPLETE_NOT_ARTISTICALLY_CERTIFIED",
        "blockers": sorted(set(blockers)),
        "axes": {
            "visual_design": "REQUIRES_PERCEPTUAL_REVIEW",
            "information_architecture": "REQUIRES_TASK_REVIEW",
            "interaction": "REQUIRES_RUNTIME_REVIEW",
            "responsive": "EVIDENCE_PRESENT" if {"mobile", "desktop"}.issubset(viewports) else "MISSING",
            "accessibility": "PARTIAL_AUTOMATION_PLUS_MANUAL_REQUIRED",
            "performance": "METRICS_PRESENT" if evidence.get("performance_metrics") else "MISSING"
        },
        "limitations": [
            "automated accessibility catches only a subset of WCAG issues",
            "Core Web Vitals are experience targets, not design scores",
            "visual identity and usability require rendered interaction and independent or human review"
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.contract.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["decision"] == "EVIDENCE_COMPLETE_NOT_ARTISTICALLY_CERTIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
