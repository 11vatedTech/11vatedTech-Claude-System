#!/usr/bin/env python3
"""High-Fidelity Reliability validator.

Engineering evidence is not creative evidence. This gate verifies that the
Foundry keeps those maturity axes separate, preserves human baseline evidence,
and blocks polished/production/signature claims when hard creative blockers are
open.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "high-fidelity-reliability.json"
EXPERIENCE = ROOT / "config" / "experience-foundry.json"
GOLDEN = ROOT / "evaluations" / "high-fidelity-reliability" / "golden-tasks.json"
ASHWAKE = ROOT / "artifacts" / "unreal" / "calibration" / "evidence" / "human-playtest-001"


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"missing:{path.relative_to(ROOT)}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return None, [f"invalid_json:{path.relative_to(ROOT)}:{type(exc).__name__}:{exc}"]
    if not isinstance(data, dict):
        return None, [f"not_object:{path.relative_to(ROOT)}"]
    return data, []


def require(condition: bool, failures: list[str], code: str) -> None:
    if not condition:
        failures.append(code)


def check_model(data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    require(data.get("model_id") == "HIGH_FIDELITY_RELIABILITY", failures, "model_id_not_high_fidelity_reliability")
    axes = data.get("axes", {})
    require(set(axes) >= {"engineering_maturity", "creative_maturity", "fidelity_reliability"}, failures, "missing_three_axes")
    require("C6" in axes.get("creative_maturity", {}), failures, "creative_axis_missing_signature")
    require("R5" in axes.get("fidelity_reliability", {}), failures, "reliability_axis_missing_r5")
    non_inheritance = data.get("non_inheritance_rules", [])
    for rule in [
        "PACKAGED_BUILD_PASS does not imply GAME_QUALITY_PASS",
        "NIAGARA_ACTIVE does not imply VFX_QUALITY_PASS",
        "AUDIO_PLAYING does not imply AUDIO_QUALITY_PASS",
    ]:
        require(rule in non_inheritance, failures, f"missing_non_inheritance_rule:{rule}")
    blockers = set(data.get("hard_blockers_to_polished", []))
    for blocker in [
        "major_black_crush_in_player_critical_regions",
        "test_environment_presentation",
        "primary_subject_clipping",
        "generic_or_debug_hud",
    ]:
        require(blocker in blockers, failures, f"missing_polished_blocker:{blocker}")
    evidence = data.get("evidence_classes", {})
    require("FOUNDER" in evidence and "HUMAN_PLAYTESTER" in evidence, failures, "missing_human_evidence_classes")
    return failures


def check_experience(data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    require(data.get("system_id") == "11VT_EXPERIENCE_FOUNDRY", failures, "experience_system_id_wrong")
    capital = data.get("professional_experience_capital", {})
    for key in ["KNOWLEDGE", "TOOL_ACCESS", "PRODUCTION_EXPERIENCE", "CRITICAL_EXPERIENCE", "MASTERED_CAPABILITY"]:
        require(key in capital, failures, f"missing_experience_capital:{key}")
    loop = data.get("loop", [])
    for step in ["PERFORM_CONTROLLED_EXERCISE", "FAIL_DIAGNOSE", "HUMAN_REVIEW", "CREATE_GOLDEN_TASK", "RETAIN_EXPERIENCE"]:
        require(step in loop, failures, f"missing_experience_loop_step:{step}")
    profiles = data.get("specialist_profiles", [])
    require(len(profiles) >= 5, failures, "too_few_specialist_profiles")
    require(any(p.get("id") == "lighting_specialist" for p in profiles), failures, "missing_lighting_specialist_profile")
    require(any(p.get("id") == "environment_level_specialist" for p in profiles), failures, "missing_environment_level_profile")
    return failures


def check_golden(data: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    tasks = data.get("tasks", [])
    require(len(tasks) >= 5, failures, "too_few_hfr_golden_tasks")
    by_id = {t.get("id"): t for t in tasks if isinstance(t, dict)}
    require("HFR-GT-001" in by_id, failures, "missing_black_void_golden_task")
    require("HFR-GT-002" in by_id, failures, "missing_test_chamber_golden_task")
    require("HFR-GT-003" in by_id, failures, "missing_state_color_only_golden_task")
    for task in tasks:
        require("POLISHED" in task.get("must_block", []), failures, f"golden_task_does_not_block_polished:{task.get('id')}")
        require(task.get("technical_status") == "PASS", failures, f"golden_task_must_be_technically_valid:{task.get('id')}")
    return failures


def check_ashwake_baseline() -> list[str]:
    failures: list[str] = []
    evidence, errs = load_json(ASHWAKE / "human-playtest-evidence.json")
    failures.extend(errs)
    debt, errs = load_json(ASHWAKE / "quality-debt-register.json")
    failures.extend(errs)
    analysis, errs = load_json(ASHWAKE / "visual-failure-analysis.json")
    failures.extend(errs)
    contract, errs = load_json(ASHWAKE / "ashwake-quality-contract.json")
    failures.extend(errs)
    if evidence:
        require(evidence.get("evidence_type") == "HUMAN_PLAYTEST_RUNTIME_SCREENSHOT", failures, "ashwake_wrong_evidence_type")
        require(evidence.get("classification") == "HIGH_FIDELITY_FAILURE_BASELINE_001", failures, "ashwake_wrong_baseline_classification")
        do_not_claim = set(evidence.get("do_not_claim", []))
        for claim in ["POLISHED", "PRODUCTION", "SIGNATURE", "game_quality_pass_from_runtime_pass"]:
            require(claim in do_not_claim, failures, f"ashwake_missing_do_not_claim:{claim}")
        quality_state = evidence.get("quality_state", {})
        require(quality_state.get("engineering_maturity") == "E4", failures, "ashwake_engineering_state_not_recorded")
        require(quality_state.get("fidelity_reliability") == "R2", failures, "ashwake_reliability_state_not_r2")
        creative = quality_state.get("creative_maturity", {})
        require(creative.get("environment") == "C1", failures, "ashwake_environment_not_c1")
    if debt:
        items = debt.get("items", [])
        require(len(items) >= 10, failures, "ashwake_too_few_quality_debt_items")
        critical_or_high = [i for i in items if i.get("severity") in {"critical", "high"} and i.get("status") == "OPEN"]
        require(len(critical_or_high) >= 6, failures, "ashwake_missing_open_critical_high_debt")
        require(any(i.get("discipline") == "lighting" for i in items), failures, "ashwake_debt_missing_lighting")
        require(any(i.get("discipline") == "environment_art" for i in items), failures, "ashwake_debt_missing_environment")
        require(any(i.get("discipline") == "state_feedback" for i in items), failures, "ashwake_debt_missing_state_feedback")
    if analysis:
        classes = set(analysis.get("failure_classes", []))
        for klass in ["VISUAL_QA_GAP", "ART_DIRECTION_GAP", "LIGHTING_INTELLIGENCE_GAP", "MATERIAL_INTELLIGENCE_GAP"]:
            require(klass in classes, failures, f"ashwake_analysis_missing_failure_class:{klass}")
    if contract:
        floor = contract.get("quality_floor", {}).get("before_human_playtest_2", [])
        require(any("environment readable" in x for x in floor), failures, "ashwake_contract_missing_environment_floor")
        require(any("safe and hostile" in x for x in floor), failures, "ashwake_contract_missing_state_floor")
    return failures


def main() -> int:
    failures: list[str] = []
    model, errs = load_json(CONFIG)
    failures.extend(errs)
    experience, errs = load_json(EXPERIENCE)
    failures.extend(errs)
    golden, errs = load_json(GOLDEN)
    failures.extend(errs)
    if model:
        failures.extend(check_model(model))
    if experience:
        failures.extend(check_experience(experience))
    if golden:
        failures.extend(check_golden(golden))
    failures.extend(check_ashwake_baseline())
    print(f"high_fidelity_reliability_failures={len(failures)}")
    for failure in failures:
        print("FAIL", failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
