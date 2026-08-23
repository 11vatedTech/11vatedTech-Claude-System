#!/usr/bin/env python3
"""Regression tests for reusable Unreal Foundry reliability helpers."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "unreal"))

from content_contract_validator import build_records, runtime_asset_loads, stage_summary  # noqa: E402
from runtime_evidence import classify_execution_state, classify_exit  # noqa: E402
from windows_env import foundry_subprocess_env, git_bash_to_windows, normalize_unreal_package_path, path_report, windows_to_git_bash  # noqa: E402


def test_windows_path_resolution() -> bool:
    env = foundry_subprocess_env({})
    ok = env.get("MSYS2_ARG_CONV_EXCL") == "*" and env.get("MSYS_NO_PATHCONV") == "1"
    ok = ok and git_bash_to_windows("/c/Users/Test/AppData") == "C:\\Users\\Test\\AppData"
    ok = ok and windows_to_git_bash("C:/Users/Test/AppData").startswith("/c/Users/Test")
    ok = ok and normalize_unreal_package_path("Calibration/VFX/NS_Test") == "/Game/Calibration/VFX/NS_Test"
    ok = ok and path_report("C:/Temp/Ashwake")["unreal_filesystem_arg"] == "C:/Temp/Ashwake"
    print("  windows_path_resolution", "ok" if ok else "FAIL")
    return ok


def _contract_records(tmp: Path, runtime_text: str) -> list[dict]:
    project_root = tmp / "Project"
    source = project_root / "Content" / "Calibration" / "VFX"
    source.mkdir(parents=True, exist_ok=True)
    (source / "NS_Test.uasset").write_bytes(b"asset")
    manifest = {"required_assets": [{"id": "test_vfx", "kind": "NiagaraSystem", "package_path": "/Game/Calibration/VFX/NS_Test", "object_path": "/Game/Calibration/VFX/NS_Test.NS_Test"}]}
    entries = {str((tmp / "Manifest_UFSFiles_Win64.txt").resolve()): ["FoundryCalibration/Content/Calibration/VFX/NS_Test.uasset"]}
    manifests = [{"path": str((tmp / "Manifest_UFSFiles_Win64.txt").resolve()), "source": "archive_root", "strength": 90, "mtime": 1}]
    editor = {"checks": [{"id": "test_vfx", "loaded": True, "loaded_class": "NiagaraSystem"}]}
    runtime = runtime_asset_loads(runtime_text)
    return build_records(manifest, project_root, entries, manifests, tmp / "Archive", None, editor, runtime, runtime_text, [], [])


def test_content_contract_good_and_bad() -> bool:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        good_text = "LogFoundry: ASSET_LOADED id=test_vfx object=/Game/Calibration/VFX/NS_Test.NS_Test expected_class=NiagaraSystem actual_class=NiagaraSystem loaded=true\nLogFoundry: VFX_STATE system=NS_Test state=Hostile component=Comp active=true spawn_rate=96.0 energy=1.00 color=(1.00,0.05,0.02,1.00)"
        good = _contract_records(tmp, good_text)
        good_ok = not good[0]["failure_reason"] and stage_summary(good)["RUNTIME"]["status"] == "PASS"
        bad = _contract_records(tmp, "LogFoundry: ASSET_LOADED id=test_vfx object=/Game/Calibration/VFX/NS_Test.NS_Test expected_class=NiagaraSystem actual_class=NiagaraSystem loaded=true")
        bad_ok = "RUNTIME_COMPONENT_INACTIVE" in bad[0]["failure_reason"] and stage_summary(bad)["RUNTIME"]["status"] == "FAIL"
    ok = good_ok and bad_ok
    print("  content_contract_good_bad", "ok" if ok else f"FAIL good={good_ok} bad={bad_ok}")
    return ok


def test_exit_classification() -> bool:
    normal = classify_exit(0, "LogExit: Exiting.")
    controlled = classify_exit(777003, "INPUT_PROOF_COMPLETE Result=SuccessAndRestart\nLogExit: Exiting.\nRequestExitWithStatus(0, 0", expected_controlled_shutdown=True)
    timeout = classify_exit(None, "", timed_out=True)
    fatal = classify_exit(0, "LowLevelFatalError something")
    ok = normal["classification"] == "NORMAL_EXIT" and controlled["classification"] == "CONTROLLED_TEST_SHUTDOWN" and timeout["classification"] == "WATCHDOG_TERMINATION" and fatal["classification"] == "FATAL_ENGINE_ERROR"
    print("  exit_classification", "ok" if ok else "FAIL")
    return ok


def test_execution_state_prefers_successful_engine_exit() -> bool:
    normal = classify_execution_state({"classification": "NORMAL_EXIT"}, stdout="LogDevObjectVersion:   FN-Main-InterchangePipeline (B69D2E47-E2A8-4003-BF77-18A492C4D899): 2")
    transient = classify_execution_state({"classification": "UNKNOWN_EXIT"}, stderr="transport error: ECONNRESET")
    product = classify_execution_state({"classification": "FATAL_ENGINE_ERROR"}, stdout="LowLevelFatalError something")
    ok = normal == "SUCCESS" and transient == "TOOL_TRANSIENT_FAILURE" and product == "PRODUCT_FAILURE"
    print("  execution_state_prefers_successful_engine_exit", "ok" if ok else f"FAIL normal={normal} transient={transient} product={product}")
    return ok


def test_validator_rejects_bad_runtime() -> bool:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        project = tmp / "Project"
        (project / "Content" / "Calibration" / "VFX").mkdir(parents=True)
        (project / "Content" / "Calibration" / "VFX" / "NS_Test.uasset").write_bytes(b"asset")
        uproject = project / "Test.uproject"
        uproject.write_text("{}", encoding="utf-8")
        manifest = tmp / "required.json"
        manifest.write_text(json.dumps({"required_assets": [{"id": "test_vfx", "kind": "NiagaraSystem", "package_path": "/Game/Calibration/VFX/NS_Test", "object_path": "/Game/Calibration/VFX/NS_Test.NS_Test"}]}), encoding="utf-8")
        runtime = tmp / "runtime.log"
        runtime.write_text("LogFoundry: ASSET_LOADED id=test_vfx object=/Game/Calibration/VFX/NS_Test.NS_Test expected_class=NiagaraSystem actual_class=NiagaraSystem loaded=true\n", encoding="utf-8")
        out = tmp / "out.json"
        rc = subprocess.run([sys.executable, str(ROOT / "scripts/unreal/content_contract_validator.py"), str(manifest), "--project", str(uproject), "--runtime-log", str(runtime), "--out", str(out)], cwd=ROOT, capture_output=True, text=True, timeout=30).returncode
        data = json.loads(out.read_text(encoding="utf-8"))
        ok = rc == 1 and data["status"] == "FAIL" and "RUNTIME_COMPONENT_INACTIVE" in data["asset_records"][0]["failure_reason"]
    print("  validator_rejects_bad_runtime", "ok" if ok else "FAIL")
    return ok


def main() -> int:
    tests = [test_windows_path_resolution, test_content_contract_good_and_bad, test_exit_classification, test_execution_state_prefers_successful_engine_exit, test_validator_rejects_bad_runtime]
    failures = []
    for test in tests:
        try:
            if not test():
                failures.append(test.__name__)
        except Exception as exc:
            failures.append(test.__name__)
            print(" ", test.__name__, "ERROR", type(exc).__name__, exc)
    print(f"unreal_foundry_reliability_tests={len(tests)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
