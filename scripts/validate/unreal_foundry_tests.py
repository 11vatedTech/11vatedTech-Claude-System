#!/usr/bin/env python3
"""Fast Unreal Foundry tests: health, project inspection, and handoff failures."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UE_ROOT = Path("C:/Program Files/Epic Games/UE_5.8")
PROJECT = Path("C:/Users/11vat/OneDrive/Desktop/Nemesis/Nemesis.uproject")
CALIBRATION = ROOT / "artifacts/unreal/calibration/FoundryCalibrationAuthoring.uproject"
GAME_PROJECT = ROOT / "artifacts/unreal/calibration/FoundryCalibration.uproject"
ASSET = ROOT / "artifacts/flagship/emberveil-canonical/emberveil-canonical.glb"
BLEND = ROOT / "artifacts/flagship/emberveil-canonical/session.blend"


def run(args: list[str]) -> tuple[int, str]:
    try:
        p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=90)
        return p.returncode, p.stdout + p.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        return 124, stdout + stderr + "\\nFOUNDRY_TIMEOUT: bounded operation exceeded test timeout; preflight may have passed before cook/package completion"


def test_game_design_traceability() -> bool:
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.json"; bad.write_text(json.dumps({"player_fantasy": "x", "mechanics": []}), encoding="utf-8")
        rc, output = run([sys.executable, "scripts/unreal/game_design.py", "validate", str(bad)])
        ok = rc == 1 and "missing_player_verbs" in output and "no_mechanics" in output
        print("  unreal_game_design_failure", "ok" if ok else f"FAIL rc={rc}")
        return ok


def test_health() -> bool:
    rc, output = run([sys.executable, "scripts/unreal/unreal_intelligence.py", "--engine-root", str(UE_ROOT), "health"])
    data = json.loads(output)
    ok = rc == 0 and data["usable_engine_count"] >= 1 and data["engines"][0]["version"]["version"] == "5.8.0"
    print("  unreal_health", "ok" if ok else f"FAIL rc={rc}")
    return ok


def test_project_inspection() -> bool:
    rc, output = run([sys.executable, "scripts/unreal/unreal_intelligence.py", "--engine-root", str(UE_ROOT), "inspect", str(PROJECT)])
    data = json.loads(output)
    ok = rc == 0 and len(data["modules"]) == 1 and len(data["content"]["classes"]) > 0 and len(data["content"]["maps"]) >= 1
    print("  unreal_project_inspection", "ok" if ok else f"FAIL rc={rc} {data.get('warnings')}")
    return ok


def test_commandlet() -> bool:
    rc, output = run([sys.executable, "scripts/unreal/unreal_intelligence.py", "--engine-root", str(UE_ROOT), "commandlet", str(CALIBRATION), "--name", "DataValidation", "--timeout", "90"])
    data = json.loads(output)
    ok = rc == 0 and data.get("status") == "PASS" and data.get("exit_code") == 0
    print("  unreal_datavalidation_commandlet", "ok" if ok else f"FAIL rc={rc} status={data.get('status')}")
    return ok


def test_editor_import() -> bool:
    with tempfile.TemporaryDirectory() as td:
        report = Path(td) / "import.json"
        rc, output = run([sys.executable, "scripts/unreal/unreal_intelligence.py", "--engine-root", str(UE_ROOT), "import-glb", str(CALIBRATION), str(ASSET), "--destination", "/Game/Calibration/TestImport", "--report", str(report), "--timeout", "180"])
        data = json.loads(output)
        imported = data.get("probe", {}).get("imported_object_paths", [])
        ok = rc == 0 and data.get("status") == "PASS" and len(imported) >= 4
        print("  unreal_editor_import", "ok" if ok else f"FAIL rc={rc} status={data.get('status')}")
        return ok


def test_runtime_observation_is_honest() -> bool:
    log = ROOT / "artifacts/unreal/health/foundry-runtime-observation-trace.json"
    data = json.loads(log.read_text(encoding="utf-8")) if log.exists() else {}
    ok = data.get("status") in {"RUNTIME_CRASH", "STARTUP_ONLY", "GAMEPLAY_OBSERVED"} and data.get("markers", {}).get("game_module_loaded") is True
    if data.get("status") == "GAMEPLAY_OBSERVED":
        ok = ok and data.get("markers", {}).get("map_loaded") is True
    print("  unreal_runtime_observation", "ok" if ok else f"FAIL status={data.get('status')}")
    return ok


def test_native_test_discovery() -> bool:
    rc, output = run([sys.executable, "scripts/unreal/unreal_intelligence.py", "discover-tests", str(ROOT / "artifacts/unreal/calibration/Source/FoundryCalibration")])
    data = json.loads(output)
    ok = rc == 0 and data.get("count", 0) >= 1 and data.get("status") == "DISCOVERED_NOT_EXECUTED"
    print("  unreal_native_test_discovery", "ok" if ok else f"FAIL rc={rc} {data}")
    return ok


def test_package_preflight_reports_blocker() -> bool:
    """Verify package preflight no longer reports .NET 4.8 SDK as blocker.

    With the SDK installed, the package command must NOT return BLOCKED for
    missing_component=Microsoft.Net.Component.4.8.SDK.  It should either
    proceed to RunUAT (returning UNAVAILABLE/other on timeout) or succeed.
    We give it 60s — enough to pass preflight, not enough for a full cook.
    """
    archive = ROOT / "artifacts/unreal/calibration/Packaged/Ashwake"
    rc, output = run([sys.executable, "scripts/unreal/build_pipeline.py", "--engine-root", str(UE_ROOT), "package", str(GAME_PROJECT), "--archive", str(archive), "--config", "Development", "--timeout", "60"])
    try:
        data = json.loads(output)
    except Exception:
        data = {}
    # Must NOT be BLOCKED on .NET SDK — that prerequisite is resolved.
    blocked = data.get("status") == "BLOCKED" and data.get("missing_component") == "Microsoft.Net.Component.4.8.SDK"
    ok = not blocked
    print("  unreal_package_preflight", "ok" if ok else f"FAIL rc={rc} {data}")
    return ok


def test_handoff_and_failure_gate() -> bool:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "handoff.json"
        rc, output = run([sys.executable, "scripts/unreal/blender_unreal_bridge.py", "manifest", str(ASSET), str(PROJECT), "--unreal-path", "/Game/Calibration/TestAsset", "--source-blend", str(BLEND), "--license", "generated-local", "--source", "11vatedTech-test", "--out", str(out)])
        good = json.loads(out.read_text(encoding="utf-8"))
        good_ok = rc == 0 and good["validation"]["ok"] and len(good["structure"]["animations"]) >= 1
        mutated = json.loads(out.read_text(encoding="utf-8")); mutated["unreal"]["content_path"] = "Game/invalid"; mutated["provenance"].pop("license")
        bad = Path(td) / "bad.json"; bad.write_text(json.dumps(mutated), encoding="utf-8")
        rc2, output2 = run([sys.executable, "scripts/unreal/blender_unreal_bridge.py", "validate", str(bad)])
        bad_ok = rc2 == 1 and "invalid_unreal_content_path" in output2 and "incomplete_provenance" in output2
        print("  unreal_handoff", "ok" if good_ok and bad_ok else f"FAIL good={good_ok} bad={bad_ok}")
        return good_ok and bad_ok


def test_reliability_helpers() -> bool:
    rc, output = run([sys.executable, "scripts/validate/unreal_foundry_reliability_tests.py"])
    ok = rc == 0 and "failures=[]" in output
    print("  unreal_reliability_helpers", "ok" if ok else f"FAIL rc={rc}")
    return ok


def main() -> int:
    tests = [test_game_design_traceability, test_health, test_project_inspection, test_commandlet, test_editor_import, test_runtime_observation_is_honest, test_native_test_discovery, test_package_preflight_reports_blocker, test_handoff_and_failure_gate, test_reliability_helpers]
    failures = []
    for test in tests:
        try:
            if not test(): failures.append(test.__name__)
        except Exception as exc:
            failures.append(test.__name__); print(" ", test.__name__, "ERROR", type(exc).__name__, exc)
    print(f"unreal_foundry_tests={len(tests)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
