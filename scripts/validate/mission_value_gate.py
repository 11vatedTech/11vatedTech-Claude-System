#!/usr/bin/env python3
"""Mission value and calibration-drift gate.

This is deliberately deterministic. It does not decide artistic merit; it
forces a mission to declare why a task advances the global Foundry and when the
work must stop. A task that primarily improves a frozen fixture is rejected
unless it is explicitly a bounded regression exercise.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED = ("mission_id", "primary_objective", "active_milestone", "non_goals", "stop_conditions", "task")
DIMENSIONS = ("global_capability_value", "project_value", "learning_value", "time_compute_cost", "redundancy", "opportunity_cost")


def evaluate(doc: dict) -> dict:
    missing = [key for key in REQUIRED if key not in doc]
    scores = doc.get("scores") or {}
    missing_scores = [key for key in DIMENSIONS if key not in scores]
    task = json.dumps(doc.get("task", {})).lower()
    frozen_fixture = any(name in task for name in ("ashwake", "emberveil"))
    bounded_regression = bool(doc.get("task", {}).get("bounded_regression", False))
    drift_signals = [
        "option_a", "option_b", "option_c", "environment selection", "review board",
        "level expansion", "audio polish", "more ash wake", "more ashwake"
    ]
    drift = [signal for signal in drift_signals if signal in task]
    blockers = []
    if missing:
        blockers.append("missing_required_mission_fields")
    if missing_scores:
        blockers.append("missing_value_scores")
    if frozen_fixture and not bounded_regression:
        blockers.append("frozen_fixture_work_requires_bounded_regression_declaration")
    if drift and not bounded_regression:
        blockers.append("calibration_drift_detected")
    if not doc.get("stop_conditions"):
        blockers.append("no_stop_condition")
    decision = "ALLOW" if not blockers else "STOP_AND_REPLAN"
    return {
        "schema_version": 1,
        "kind": "mission-value-gate",
        "decision": decision,
        "blockers": blockers,
        "missing_fields": missing,
        "missing_scores": missing_scores,
        "frozen_fixture_detected": frozen_fixture,
        "drift_signals": drift,
        "bounded_regression": bounded_regression,
        "scores": scores,
        "interpretation": "value scoring is a planning control, not proof that the resulting work is high quality"
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mission", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.mission.read_text(encoding="utf-8")))
    text = json.dumps(result, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if result["decision"] == "ALLOW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
