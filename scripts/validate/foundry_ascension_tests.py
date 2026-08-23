#!/usr/bin/env python3
"""Focused regression tests for the first global capability ascension sprint."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
sys.path.insert(0, str(ROOT / "scripts" / "ascension"))
sys.path.insert(0, str(ROOT / "scripts" / "repo"))
from capability_truth_audit import classify  # type: ignore
from mission_value_gate import evaluate as evaluate_mission  # type: ignore
from model_router import choose  # type: ignore
from visual_evidence_evaluator import evaluate as evaluate_visual  # type: ignore
from multilang_semantic_intelligence import index_tree as index_multilang  # type: ignore
from creative_micro_lab import evaluate as evaluate_lab  # type: ignore
from frontend_quality_contract import evaluate as evaluate_frontend  # type: ignore
from mission_compiler import compile_intent  # type: ignore


def test_truth_does_not_inflate_skill():
    state, evidence = classify({"id": "x", "maturity": "L4", "providers": [{"kind": "skill", "name": "missing-skill"}], "evidence": []})
    return state == "THEORETICAL" and not evidence["executable_providers"]


def test_truth_detects_operational_script():
    state, evidence = classify({"id": "x", "maturity": "L3", "providers": [{"kind": "script", "name": "scripts/validate/foundry_ascension_tests.py"}], "evidence": ["scripts/validate/foundry_ascension_tests.py"]})
    return state == "OPERATIONAL" and bool(evidence["executable_providers"])


def test_mission_gate_stops_ashwake_drift():
    result = evaluate_mission({
        "mission_id": "bad-ashwake-work",
        "primary_objective": "improve Foundry",
        "active_milestone": "fixture polish",
        "non_goals": [],
        "stop_conditions": ["stop"],
        "task": {"description": "Continue Ashwake environment selection and review board polish"},
        "scores": {"global_capability_value": 1, "project_value": 5, "learning_value": 1, "time_compute_cost": 5, "redundancy": 5, "opportunity_cost": 5}
    })
    return result["decision"] == "STOP_AND_REPLAN" and "calibration_drift_detected" in result["blockers"]


def test_mission_gate_allows_bounded_regression():
    result = evaluate_mission({
        "mission_id": "good-regression",
        "primary_objective": "improve global visual evaluator",
        "active_milestone": "Golden Task",
        "non_goals": ["Ashwake polish"],
        "stop_conditions": ["one fixture run", "store report"],
        "task": {"description": "Run Ashwake screenshot through visual evaluator", "bounded_regression": True},
        "scores": {"global_capability_value": 5, "project_value": 1, "learning_value": 5, "time_compute_cost": 1, "redundancy": 1, "opportunity_cost": 1}
    })
    return result["decision"] == "ALLOW"


def test_visual_evaluator_rejects_known_bad_context():
    image = ROOT / "artifacts/flagship/qa/live/frame-01.png"
    if not image.exists():
        return False
    result = evaluate_visual([image], "black void, emissive core substitutes for lighting, primitive debug HUD")
    return result["maximum_supported_stage"] == "COHERENT" and "major_black_crush_in_player_critical_regions" in result["blockers"]


def test_visual_evaluator_separates_artistic_claim():
    image = ROOT / "artifacts/flagship/emberveil-canonical/preview/preview-frame-0048.png"
    if not image.exists():
        return False
    result = evaluate_visual([image], "")
    return result["artistic_quality"] == "REQUIRES_INDEPENDENT_REVIEW" and result["functional_validity"] == "UNASSESSED"


def test_multilang_index_covers_fixture():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "a.py").write_text("def py_fn():\\n    return 1\\n", encoding="utf-8")
        (root / "b.ts").write_text("export function tsFn() { return 1; }\\n", encoding="utf-8")
        (root / "c.cpp").write_text("class C {}; int run() { return 1; }\\n", encoding="utf-8")
        result = index_multilang(root)
        languages = set(result["languages"])
        return languages == {"python", "typescript-javascript", "cpp"} and result["symbol_count"] >= 3


def test_micro_lab_requires_transfer_and_review():
    fixture = ROOT / "artifacts/ascension/micro-labs/creative-lab-fixture.json"
    result = evaluate_lab(json.loads(fixture.read_text(encoding="utf-8")))
    return result["decision"] == "ADVANCE_EXPERIENCE" and result["experience_state"] == "P4_INDEPENDENTLY_CRITIQUED_EXERCISE"


def test_frontend_contract_accepts_complete_evidence():
    fixture = ROOT / "artifacts/ascension/micro-labs/frontend-quality-contract.json"
    result = evaluate_frontend(json.loads(fixture.read_text(encoding="utf-8")))
    return result["decision"] == "EVIDENCE_COMPLETE_NOT_ARTISTICALLY_CERTIFIED" and not result["blockers"]


def test_frontend_contract_rejects_score_only():
    result = evaluate_frontend({
        "product_character": "operations tool",
        "user_type": "analyst",
        "visual_thesis": "quiet dense work surface",
        "states": ["loading", "empty", "error", "success", "focus"],
        "viewports": ["mobile", "desktop"],
        "evidence": {"screenshots": ["desktop.png"], "accessibility_scan": {"axe_pass": True}, "performance_metrics": {"lcp": 1.2}, "lighthouse_score": 100}
    })
    return "lighthouse_cannot_certify_visual_or_ux_quality" in result["blockers"]


def test_mission_compiler_discovers_frontend_and_game_disciplines():
    result = compile_intent("Build a playable browser game with a responsive frontend UI")
    disciplines = set(result["required_disciplines"])
    return {"frontend-design", "game-design", "accessibility", "runtime-qa"}.issubset(disciplines) and len(result["evidence"]) >= 6


def test_model_router_uses_evidence():
    registry = {
        "model-a": {"code": {"passed": True, "latency_s": 9}, "debug": {"passed": False, "latency_s": 4}},
        "model-b": {"code": {"passed": True, "latency_s": 3}, "debug": {"passed": True, "latency_s": 5}, "repo": {"passed": True, "latency_s": 4}},
    }
    result = choose(registry, "builder")
    return result["selection"]["model"] == "model-b"


def main() -> int:
    tests = [
        ("truth_skill_not_inflated", test_truth_does_not_inflate_skill),
        ("truth_operational_script", test_truth_detects_operational_script),
        ("mission_gate_stops_drift", test_mission_gate_stops_ashwake_drift),
        ("mission_gate_allows_bounded_regression", test_mission_gate_allows_bounded_regression),
        ("visual_rejects_known_bad", test_visual_evaluator_rejects_known_bad_context),
        ("visual_separates_artistic_claim", test_visual_evaluator_separates_artistic_claim),
        ("multilang_index_covers_fixture", test_multilang_index_covers_fixture),
        ("model_router_uses_evidence", test_model_router_uses_evidence),
        ("micro_lab_requires_transfer_and_review", test_micro_lab_requires_transfer_and_review),
        ("frontend_contract_accepts_complete_evidence", test_frontend_contract_accepts_complete_evidence),
        ("frontend_contract_rejects_score_only", test_frontend_contract_rejects_score_only),
        ("mission_compiler_discovers_disciplines", test_mission_compiler_discovers_frontend_and_game_disciplines),
    ]
    failures = []
    for name, test in tests:
        try:
            ok = bool(test())
        except Exception as exc:
            ok = False
            print(f"{name}=ERROR:{type(exc).__name__}:{exc}")
        print(f"{name}={'PASS' if ok else 'FAIL'}")
        if not ok:
            failures.append(name)
    report = {"schema_version": 1, "kind": "foundry-ascension-golden-tasks", "tests": len(tests), "failures": failures, "ok": not failures}
    out = ROOT / "artifacts" / "ascension" / "foundry-ascension-golden-tasks.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"foundry_ascension_tests={len(tests)} failures={failures}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
