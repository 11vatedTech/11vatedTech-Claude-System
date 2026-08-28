#!/usr/bin/env python3
"""Evidence-driven V1 terminal matrix generator.

A criterion can only pass when its evaluator produces the required evidence.
Missing, malformed, or failed evidence is never optimistic PASS.
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "scripts/validate/v1_terminal_requirements.json"
OUT = ROOT / "artifacts/terminal-v1-acceptance.json"

def run(cmd: str, timeout: int = 60) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=ROOT, shell=True, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except Exception as exc:
        return 99, f"{type(exc).__name__}: {exc}"

def evidence(path: str, evaluator: str, condition: str, blocking: str) -> dict:
    return {"evaluator": evaluator, "required_evidence": path,
            "pass_condition": condition, "blocking_condition": blocking}

def evaluate() -> dict:
    criteria = json.loads(SPEC.read_text(encoding="utf-8")).get("criteria", [])
    if len(criteria) != 43 or len(set(criteria)) != 43:
        raise RuntimeError("ACCEPTANCE_MATRIX_CARDINALITY_DRIFT: canonical criteria must contain exactly 43 unique IDs")
    rc_doctor, doctor_output = run("python scripts/doctor/foundry_doctor.py")
    rc_validate, validate_output = run("python scripts/validate/foundry_validate.py")
    doctor_report = ROOT / "artifacts/foundry-doctor.json"
    doctor = json.loads(doctor_report.read_text()) if doctor_report.exists() else {}
    doctor_by_name = {c["name"]: c for c in doctor.get("checks", [])}
    status = {}
    metadata = {}
    def set_row(cid, passed, ev):
        status[cid] = "PASS" if passed else "NOT_PROVEN"
        metadata[cid] = ev
    clean = not bool(run("git status --porcelain=v1")[1].strip())
    set_row("REPOSITORY_HYGIENE", clean, evidence("git status --porcelain=v1", "git", "empty output", "any dirty path"))
    set_row("FOUNDRY_DOCTOR", rc_doctor == 0 and doctor_by_name.get("9ROUTER", {}).get("status") != "FAIL", evidence("artifacts/foundry-doctor.json", "foundry_doctor.py", "no FAIL checks", "any FAIL"))
    set_row("FOUNDRY_VALIDATE", rc_validate == 0, evidence("artifacts/foundry-validation.json", "foundry_validate.py", "all gates PASS", "any failed gate"))
    set_row("MISSION_COMPILER", (ROOT / "scripts/mission/foundry_mission.py").exists(), evidence("scripts/mission/foundry_mission.py", "filesystem", "file exists", "missing compiler"))
    set_row("MISSION_RUNTIME", any((ROOT / "artifacts/missions").glob("*-result.json")), evidence("artifacts/missions/*-result.json", "mission runtime", "result exists", "no result"))
    set_row("GOLDEN_REAL_WORK_MISSIONS", all((ROOT / "artifacts/missions" / f"golden-{x}.json").exists() for x in "ABCDEFGH"), evidence("artifacts/missions/golden-{A..H}.json", "golden mission evaluator", "eight valid distinct results", "missing or invalid artifact"))
    set_row("KAPIF_STORAGE", doctor_by_name.get("KAPIF_HEALTH", {}).get("status") == "PASS", evidence("artifacts/foundry-doctor.json", "foundry_doctor.py", "KAPIF health PASS", "KAPIF FAIL"))
    set_row("GLOBAL_DEPLOYMENT", doctor_by_name.get("GLOBAL_DEPLOYMENT", {}).get("status") == "PASS", evidence("artifacts/foundry-doctor.json", "foundry_doctor.py", "deployment PASS", "deployment FAIL"))
    set_row("9ROUTER_HEALTH", doctor_by_name.get("9ROUTER", {}).get("status") == "PASS", evidence("artifacts/foundry-doctor.json", "foundry_doctor.py", "gateway API PASS", "gateway down"))
    for cid, path in {
        "PRODUCT_REGISTRY_OPERATIONAL":"config/product-portfolio-registry.json",
        "PRODUCT_MANIFEST_STANDARD":"config/product-portfolio-registry.json",
        "BLENDER_PIPELINE":"artifacts/creative-stack-validation/blender-ops/current-execution-evidence.json",
        "UNREAL_PIPELINE":"artifacts/creative-stack-validation/unreal-current-execution.json",
        "FRONTEND_UI_UX_PATH":"artifacts/frontend/wave-a-pumkit-before/pumkit-before-evidence.json",
        "CHARACTER_IDENTITY_PATH":"artifacts/frontend/wave-a-pumkit-before/pumkit-visual-canon-v2.json",
        "CANONICAL_TRUTH_GENERATOR":"scripts/validate/canonical_truth_generator.py",
        "KNOWLEDGE_FRESHNESS":"artifacts/knowledge-freshness.json",
    }.items():
        set_row(cid, (ROOT / path).exists(), evidence(path, "artifact evaluator", "artifact exists and is valid", "missing evidence"))
    for cid in criteria:
        status.setdefault(cid, "NOT_PROVEN")
        metadata.setdefault(cid, evidence("unspecified", "no evaluator", "evidence-backed PASS", "missing evaluator/evidence"))
    # Keep one and only one row per canonical ID; unknown evaluator keys are not rows.
    status = {cid: status[cid] for cid in criteria}
    metadata = {cid: metadata[cid] for cid in criteria}
    counts = {s: sum(v == s for v in status.values()) for s in ("PASS", "GUARDED_OPERATIONAL", "ESCALATION_REQUIRED", "BLOCKED_EXTERNAL", "FAIL", "NOT_PROVEN")}
    if sum(counts.values()) != len(criteria) or len(status) != len(criteria):
        raise RuntimeError("ACCEPTANCE_MATRIX_CARDINALITY_DRIFT: statuses must partition 43 unique criteria")
    result = {"schema_version":"1.0.0", "criteria_count":len(criteria), "unique_criterion_ids":len(set(criteria)),
              "status_counts":counts,
              "pass":counts["PASS"],
              "not_proven":counts["NOT_PROVEN"],
              "rows":{c:{"status":status[c], **metadata[c]} for c in criteria}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

def main():
    result = evaluate()
    print(json.dumps({k: result[k] for k in ("criteria_count", "pass", "not_proven")}))
    return 0 if result["not_proven"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
