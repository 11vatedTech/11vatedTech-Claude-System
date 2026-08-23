#!/usr/bin/env python3
"""Run packaged Ashwake gameplay scenarios and verify input-to-state evidence."""
from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from runtime_evidence import run_unreal_process

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = ROOT / "artifacts/unreal/calibration/Packaged/Ashwake/Windows/FoundryCalibration/Binaries/Win64/FoundryCalibration.exe"
DEFAULT_OUT = ROOT / "artifacts/unreal/health/ashwake-gameplay-scenario.json"
LOG_WARNING_PATTERN = re.compile(r"(Failed to find object|SkipPackage|Can't find file|LogStreaming: Warning|LogUObjectGlobals: Warning)", re.I)
REFERENCE_TOKENS = ["/Game/Calibration/VFX", "/Game/Calibration/Audio", "emberveil-canonical11vt"]

SCENARIOS = {
    "success": {
        "args": [],
        "required_markers": [
            "event=INPUT_PROOF_BEGIN",
            "event=PLAYER_INPUT",
            "event=INPUT_ACTION_TRIGGERED",
            "action=Attune",
            "event=INTERACTION_QUERY",
            "event=GAMEPLAY_RULE",
            "event=INTERACTION_ACCEPTED",
            "event=SUCCESS",
            "event=RESTART",
            "INPUT_PROOF_COMPLETE Result=SuccessAndRestart",
            "event=VFX_STATE",
            "event=AUDIO_PLAYING",
            "event=ANIMATION_PLAYING",
        ],
        "forbidden_markers": ["event=INTERACTION_REJECTED", "event=FAILURE"],
    },
    "failure": {
        "args": ["-AshwakeInputProofFailure"],
        "required_markers": [
            "event=INPUT_PROOF_BEGIN",
            "event=PLAYER_INPUT",
            "event=INPUT_ACTION_TRIGGERED",
            "action=Attune",
            "event=INTERACTION_QUERY",
            "event=GAMEPLAY_RULE",
            "event=INTERACTION_REJECTED",
            "event=FAILURE",
            "event=RESTART",
            "INPUT_PROOF_COMPLETE Result=FailureAndRestart",
            "event=VFX_STATE",
            "event=AUDIO_PLAYING",
            "event=ANIMATION_PLAYING",
        ],
        "forbidden_markers": ["event=INTERACTION_ACCEPTED", "event=SUCCESS"],
    },
}


def runtime_reference_warnings(text: str) -> list[str]:
    warnings = []
    for line in text.splitlines():
        if LOG_WARNING_PATTERN.search(line) and any(token in line for token in REFERENCE_TOKENS):
            warnings.append(line.strip())
    return warnings[-50:]


def run_scenario(name: str, executable: Path, log_root: Path, timeout: int) -> dict[str, Any]:
    spec = SCENARIOS[name]
    run_id = f"ashwake-{name}-{uuid.uuid4().hex[:12]}"
    run_dir = log_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unreal.log"

    command = [
        str(executable),
        "-unattended",
        "-nop4",
        "-nosplash",
        "-stdout",
        "-FullStdOutLogOutput",
        "-windowed",
        "-ResX=1280",
        "-ResY=720",
        "-AshwakeInputProof",
        "-AshwakeInputProofExit",
        f"-FoundryRunId={run_id}",
        f"-FoundryScenario={name}",
        *spec["args"],
    ]

    evidence = run_unreal_process(command, executable.parent, timeout, log_path, expected_controlled_shutdown=True, fallback_log_roots=[executable.parents[2] / "Saved" / "Logs"])
    text = evidence["complete_log_text"]
    primary_text = Path(evidence["requested_log"]).read_text(encoding="utf-8", errors="replace") if evidence["requested_log_exists"] else text
    markers = {marker: marker in primary_text for marker in spec["required_markers"]}
    structured_events = len(re.findall(r"LogFoundryEvent:", primary_text))
    warnings = runtime_reference_warnings(text)
    counts = {
        "input_events": len(re.findall(r"LogFoundry: INPUT_RECEIVED|event=INPUT_ACTION_TRIGGERED", primary_text)),
        "gameplay_commands": len(re.findall(r"LogFoundry: GAMEPLAY_COMMAND|event=GAMEPLAY_RULE", primary_text)),
        "accepted_interactions": len(re.findall(r"LogFoundry: INTERACTION_ACCEPTED|event=INTERACTION_ACCEPTED", primary_text)),
        "rejected_interactions": len(re.findall(r"LogFoundry: INTERACTION_REJECTED|event=INTERACTION_REJECTED", primary_text)),
        "state_changes": len(re.findall(r"LogFoundry: STATE_CHANGED|event=STATE_CONSEQUENCE", primary_text)),
        "vfx_state": len(re.findall(r"LogFoundry: VFX_STATE|event=VFX_STATE", primary_text)),
        "audio_playing": len(re.findall(r"LogFoundry: AUDIO_PLAYING|event=AUDIO_PLAYING", primary_text)),
        "animation_playing": len(re.findall(r"LogFoundry: ANIMATION_PLAYING|event=ANIMATION_PLAYING", primary_text)),
        "structured_events": structured_events,
    }
    forbidden_markers = {marker: marker in primary_text for marker in spec.get("forbidden_markers", [])}
    marker_contract_passed = all(markers.values()) and not any(forbidden_markers.values()) and structured_events > 0 and f"run_id={run_id}" in primary_text
    status = "PASS" if evidence["exit_classification"]["classification"] in {"NORMAL_EXIT", "CONTROLLED_TEST_SHUTDOWN"} and evidence["requested_log_exists"] and marker_contract_passed and not warnings else "FAIL"
    report = {
        "name": name,
        "status": status,
        "run_id": run_id,
        "run_dir": str(run_dir),
        "log": evidence["requested_log"],
        "log_status": evidence["requested_log_status"],
        "exit_code": evidence["exit_code"],
        "exit_classification": evidence["exit_classification"],
        "execution_state": evidence["execution_state"],
        "duration_seconds": evidence["duration_seconds"],
        "command": evidence["command"],
        "markers": markers,
        "forbidden_markers": forbidden_markers,
        "marker_contract_passed": marker_contract_passed,
        "counts": counts,
        "runtime_reference_warnings": warnings,
        "stdout_path": evidence["stdout_path"],
        "stderr_path": evidence["stderr_path"],
        "complete_log_path": evidence["complete_log_path"],
        "stdout_tail": evidence["stdout_tail"],
        "stderr_tail": evidence["stderr_tail"],
        "timed_out": evidence["timed_out"],
        "process_tree_state": evidence["process_tree_state"],
    }
    (run_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    executable = args.executable.resolve()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    log_dir = args.out.parent
    if not executable.exists():
        report = {
            "schema_version": 1,
            "kind": "ashwake-packaged-gameplay-scenario",
            "status": "UNAVAILABLE",
            "error": "executable_missing",
            "executable": str(executable),
        }
    else:
        log_dir = args.out.parent / "ashwake-gameplay-scenario-runs"
        results = [run_scenario(name, executable, log_dir, args.timeout) for name in ("success", "failure")]
        report = {
            "schema_version": 1,
            "kind": "ashwake-packaged-gameplay-scenario",
            "status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL",
            "executable": str(executable),
            "scenarios": results,
        }

    text = json.dumps(report, indent=2, ensure_ascii=False)
    args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
