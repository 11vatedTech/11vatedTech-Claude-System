#!/usr/bin/env python3
"""Build the concise global capability-gap register.

This intentionally ranks cross-project leverage rather than enumerating every
possible discipline. Scores are transparent and can be replaced by measured
history as the evaluation lab grows.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRUTH = ROOT / "config" / "capability-truth-audit.json"
LESSONS = ROOT / "artifacts" / "flagship" / "ASHWAKE-LESSON-EXTRACTION.json"
OUT = ROOT / "config" / "capability-gap-register.json"

CANDIDATES = [
    ("model-routing", "MODEL INTELLIGENCE", 5, "Many project disciplines depend on correct builder/reviewer/researcher selection."),
    ("ast-repository-index", "REPOSITORY INTELLIGENCE", 5, "Semantic impact and contract tracing reduce errors across every codebase."),
    ("perceptual-readability-qa", "MULTIMODAL CREATIVE INTELLIGENCE", 5, "Ashwake showed engineering PASS can coexist with human-visible failure."),
    ("mission-value-gate", "LONG-HORIZON EXECUTION", 5, "Prevents calibration drift and preserves the global objective."),
    ("web-research", "AUTONOMOUS RESEARCH", 5, "Unknown-unknown discovery is currently mostly procedural prompting."),
    ("founder-intent-routing", "CAPABILITY AUTO-SELECTION", 4, "Founder should describe outcomes, not name internal tools."),
    ("evidence-ledger", "EXPERIENCE / MEMORY", 4, "Causal lessons need durable evidence and reuse, not raw history."),
    ("visual-qa-direction", "QUALITY EVALUATION", 4, "Visual diagnostics still need explicit review and policy boundaries."),
    ("audio-processing", "TEMPORAL / AUDIO INTELLIGENCE", 3, "Audio evidence is validated structurally but not perceptually."),
    ("project-bootstrap", "PROJECT BOOTSTRAPPING", 3, "New repositories still require manual reconstruction and routing."),
]


def main() -> int:
    truth = json.loads(TRUTH.read_text(encoding="utf-8")) if TRUTH.exists() else {}
    by_id = {x["id"]: x for x in truth.get("capabilities", [])}
    lessons = json.loads(LESSONS.read_text(encoding="utf-8")) if LESSONS.exists() else {}
    lesson_gaps = {x.get("foundry_gap") for x in lessons.get("lessons", [])}
    gaps = []
    for rank, (cap_id, category, leverage, reason) in enumerate(CANDIDATES, 1):
        record = by_id.get(cap_id, {})
        gaps.append({
            "rank": rank,
            "capability": cap_id,
            "category": category,
            "truth_state": record.get("truth_state", "UNKNOWN"),
            "ontology_maturity": (record.get("evidence") or {}).get("ontology_maturity"),
            "global_leverage": leverage,
            "why_now": reason,
            "lesson_linked": bool(category.lower().replace(" ", "_") in lesson_gaps or cap_id in {"perceptual-readability-qa", "mission-value-gate"}),
            "next_proof": {
                "before": "tool/prose/evidence exists without a cross-project capability demonstration",
                "after": "small Golden Task passes with a machine-readable report and global deployment verification"
            }
        })
    report = {
        "schema_version": 1,
        "kind": "capability-gap-register",
        "date": "2026-08-22",
        "principle": "rank improvements by reusable global capability value, not fixture polish",
        "top_ten": gaps,
        "selected_first_three": ["model-routing", "ast-repository-index", "perceptual-readability-qa"],
        "drift_control": "Ashwake is frozen; only bounded regression changes are allowed",
    }
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(OUT), "selected_first_three": report["selected_first_three"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
