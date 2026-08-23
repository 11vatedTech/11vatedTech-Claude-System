#!/usr/bin/env python3
"""Bounded apprenticeship and transfer evaluator.

The evaluator validates evidence shape and causal lesson transfer. It does not
judge taste itself; specialist, independent, and human review remain separate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = ("lab_id", "capability", "question", "before", "after", "critique", "repair", "transfer", "review")


def evaluate(doc: dict) -> dict:
    missing = [key for key in REQUIRED if not doc.get(key)]
    critique = doc.get("critique") or {}
    transfer = doc.get("transfer") or {}
    review = doc.get("review") or {}
    causal = all(critique.get(key) for key in ("symptom", "discipline", "cause", "evidence"))
    repair_is_action = bool(doc.get("repair", {}).get("action")) if isinstance(doc.get("repair"), dict) else bool(doc.get("repair"))
    transfer_observed = bool(transfer.get("observed"))
    independent = bool(review.get("independent"))
    human = bool(review.get("human"))
    blockers = []
    if missing:
        blockers.append("missing_required_evidence_fields")
    if not causal:
        blockers.append("critique_must_be_symptom_discipline_cause_evidence")
    if not repair_is_action:
        blockers.append("repair_action_missing")
    if not transfer_observed:
        blockers.append("unseen_transfer_not_observed")
    if not independent:
        blockers.append("independent_review_missing")
    experience = "P0_NONE"
    if not blockers:
        experience = "P4_INDEPENDENTLY_CRITIQUED_EXERCISE"
        if human:
            experience = "P5_REAL_PRODUCT_OR_HUMAN_VALIDATED_EXERCISE"
    elif causal and repair_is_action:
        experience = "P3_CONTROLLED_EXERCISE"
    return {
        "schema_version": 1,
        "kind": "creative-micro-lab-evaluation",
        "lab_id": doc.get("lab_id"),
        "capability": doc.get("capability"),
        "decision": "ADVANCE_EXPERIENCE" if not blockers else "HOLD_AND_RESEARCH_OR_REPAIR",
        "experience_state": experience,
        "blockers": blockers,
        "evidence": {
            "before": doc.get("before"),
            "after": doc.get("after"),
            "causal_critique": causal,
            "repair_action": repair_is_action,
            "transfer_observed": transfer_observed,
            "independent_review": independent,
            "human_review": human,
        },
        "limitations": [
            "schema evidence does not establish artistic excellence",
            "transfer must be judged against the actual unseen artifact",
            "human appeal, taste, emotion, and shipping confidence remain human-bound"
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.evidence.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["decision"] == "ADVANCE_EXPERIENCE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
