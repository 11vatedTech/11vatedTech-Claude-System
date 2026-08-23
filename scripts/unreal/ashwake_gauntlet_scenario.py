#!/usr/bin/env python3
"""Run Ashwake gameplay through Gauntlet and verify gameplay-specific evidence."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from runtime_evidence import classify_exit
from windows_env import foundry_subprocess_env, unreal_arg_path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT = ROOT / "artifacts/unreal/calibration/FoundryCalibration.uproject"
DEFAULT_BUILD = ROOT / "artifacts/unreal/calibration/Packaged/Ashwake/Windows"
DEFAULT_OUT = ROOT / "artifacts/unreal/health/ashwake-gauntlet-gameplay-scenario.json"
DEFAULT_LOG_ROOT = ROOT / "artifacts/unreal/health/gauntlet-ashwake-gameplay"
MAP = "/Game/Calibration/Maps/EmberveilCalibration"
LOG_WARNING_PATTERN = re.compile(r"(Failed to find object|SkipPackage|Can't find file|LogStreaming: Warning|LogUObjectGlobals: Warning)", re.I)
REFERENCE_TOKENS = ["/Game/Calibration/VFX", "/Game/Calibration/Audio", "emberveil-canonical11vt"]

SCENARIOS = {
    "success": {
        "client_args": [],
        "required_markers": [
            "ASHWAKE_MAP_BEGINPLAY",
            "ASHWAKE_GAMEPLAY_BEGIN",
            "INPUT_PROOF_BEGIN",
            "INPUT_PROOF_SEND_KEY Key=E",
            "INPUT_RECEIVED Action=Attune",
            "GAMEPLAY_COMMAND Action=Attune",
            "INTERACTION_ACCEPTED",
            "PLAYER_SUCCESS",
            "INPUT_PROOF_SEND_KEY Key=R",
            "INPUT_RECEIVED Action=Restart",
            "RECOVERY_RESTART",
            "INPUT_PROOF_COMPLETE Result=SuccessAndRestart",
            "VFX_STATE",
            "AUDIO_PLAYING",
            "ANIMATION_PLAYING",
        ],
    },
    "failure": {
        "client_args": ["-AshwakeInputProofFailure"],
        "required_markers": [
            "ASHWAKE_MAP_BEGINPLAY",
            "ASHWAKE_GAMEPLAY_BEGIN",
            "INPUT_PROOF_BEGIN",
            "INPUT_PROOF_SEND_KEY Key=E",
            "INPUT_RECEIVED Action=Attune",
            "GAMEPLAY_COMMAND Action=Attune",
            "INTERACTION_REJECTED",
            "PLAYER_FAILURE",
            "INPUT_PROOF_SEND_KEY Key=R",
            "INPUT_RECEIVED Action=Restart",
            "RECOVERY_RESTART",
            "INPUT_PROOF_COMPLETE Result=FailureAndRestart",
            "VFX_STATE",
            "AUDIO_PLAYING",
            "ANIMATION_PLAYING",
        ],
    },
}


def engine_root(explicit: Path | None) -> Path:
    if explicit:
        return explicit
    env = os.environ.get("UNREAL_ENGINE_ROOT")
    if env:
        return Path(env)
    candidates = sorted(Path("C:/Program Files/Epic Games").glob("UE_*") if Path("C:/Program Files/Epic Games").exists() else [])
    if not candidates:
        raise FileNotFoundError("no Unreal engine root")
    return candidates[-1]


def runtime_reference_warnings(text: str) -> list[str]:
    warnings = []
    for line in text.splitlines():
        if LOG_WARNING_PATTERN.search(line) and any(token in line for token in REFERENCE_TOKENS):
            warnings.append(line.strip())
    return warnings[-50:]


def collect_logs(log_dir: Path, stdout: str, stderr: str) -> tuple[str, list[str]]:
    paths = [p for p in log_dir.rglob("*") if p.is_file() and p.suffix.lower() in {".log", ".txt"}]
    paths.sort(key=lambda p: p.stat().st_mtime)
    chunks = [stdout, stderr]
    read_paths = []
    for path in paths:
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
            read_paths.append(str(path))
        except OSError:
            continue
    return "\n".join(chunks), read_paths


def run_scenario(name: str, uat: Path, project: Path, build: Path, log_root: Path, configuration: str, timeout: int) -> dict[str, Any]:
    spec = SCENARIOS[name]
    run_id = f"ashwake-gauntlet-{name}-{uuid.uuid4().hex[:12]}"
    log_dir = log_root / f"{name}-{run_id}"
    log_dir.mkdir(parents=True, exist_ok=True)

    client_args = " ".join([
        MAP,
        "-AshwakeInputProof",
        "-AshwakeInputProofExit",
        "-NoSplash",
        *spec["client_args"],
    ])
    command = [
        str(uat),
        "RunUnreal",
        "-test=UnrealGame.DefaultTest",
        f"-project={unreal_arg_path(project)}",
        f"-Build={unreal_arg_path(build)}",
        "-Platform=Win64",
        f"-Configuration={configuration}",
        "-Packaged",
        "-Unattended",
        "-MaxDuration=90",
        "-ResX=1280",
        "-ResY=720",
        f"-LogDir={log_dir}",
        f"-ClientArgs={client_args} -FoundryRunId={run_id} -FoundryScenario=gauntlet_{name}",
    ]

    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=project.parent, capture_output=True, text=True, timeout=timeout, env=foundry_subprocess_env())
        timed_out = False
        exit_code = done.returncode
        stdout = done.stdout or ""
        stderr = done.stderr or ""
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

    text, logs = collect_logs(log_dir, stdout, stderr)
    primary_game_logs = [Path(path) for path in logs if Path(path).name == "FoundryCalibration_Client.log"]
    if primary_game_logs:
        count_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in primary_game_logs)
    else:
        count_text = text
    markers = {marker: marker in count_text for marker in spec["required_markers"]}
    structured_events = len(re.findall(r"LogFoundryEvent:", count_text))
    warnings = runtime_reference_warnings(text)
    counts = {
        "input_events": len(re.findall(r"LogFoundry: INPUT_RECEIVED", count_text)),
        "gameplay_commands": len(re.findall(r"LogFoundry: GAMEPLAY_COMMAND", count_text)),
        "accepted_interactions": len(re.findall(r"LogFoundry: INTERACTION_ACCEPTED", count_text)),
        "rejected_interactions": len(re.findall(r"LogFoundry: INTERACTION_REJECTED", count_text)),
        "state_changes": len(re.findall(r"LogFoundry: STATE_CHANGED", count_text)),
        "vfx_state": len(re.findall(r"LogFoundry: VFX_STATE", count_text)),
        "audio_playing": len(re.findall(r"LogFoundry: AUDIO_PLAYING", count_text)),
        "animation_playing": len(re.findall(r"LogFoundry: ANIMATION_PLAYING", count_text)),
    }
    gauntlet_passed = exit_code == 0 and ("result=Passed" in text or "Result: Passed" in text or "BUILD SUCCESSFUL" in text)
    exit_classification = classify_exit(exit_code, text, timed_out=timed_out, expected_controlled_shutdown=True)
    marker_contract_passed = all(markers.values()) and structured_events > 0 and f"run_id={run_id}" in count_text
    status = "PASS" if not timed_out and gauntlet_passed and marker_contract_passed and not warnings else "FAIL"
    return {
        "name": name,
        "status": status,
        "run_id": run_id,
        "exit_code": exit_code,
        "exit_classification": exit_classification,
        "duration_seconds": round(time.monotonic() - started, 3),
        "log_dir": str(log_dir),
        "logs": logs,
        "command": command,
        "gauntlet_passed": gauntlet_passed,
        "markers": markers,
        "marker_contract_passed": marker_contract_passed,
        "structured_events": structured_events,
        "counts": counts,
        "runtime_reference_warnings": warnings,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
        "timed_out": timed_out,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-root", type=Path)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--build", type=Path, default=DEFAULT_BUILD)
    parser.add_argument("--configuration", default="Development", choices=["Development", "Test", "Shipping"])
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--log-root", type=Path, default=DEFAULT_LOG_ROOT)
    args = parser.parse_args()

    root = engine_root(args.engine_root).resolve()
    uat = root / "Engine/Build/BatchFiles/RunUAT.bat"
    project = args.project.resolve()
    build = args.build.resolve()
    out = args.out.resolve()
    log_root = args.log_root.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    log_root.mkdir(parents=True, exist_ok=True)

    if not uat.exists():
        report = {"schema_version": 1, "kind": "ashwake-gauntlet-gameplay-scenario", "status": "UNAVAILABLE", "error": "uat_missing", "engine_root": str(root)}
    elif not project.exists():
        report = {"schema_version": 1, "kind": "ashwake-gauntlet-gameplay-scenario", "status": "UNAVAILABLE", "error": "project_missing", "project": str(project)}
    elif not build.exists():
        report = {"schema_version": 1, "kind": "ashwake-gauntlet-gameplay-scenario", "status": "UNAVAILABLE", "error": "build_missing", "build": str(build)}
    else:
        results = [run_scenario(name, uat, project, build, log_root, args.configuration, args.timeout) for name in ("success", "failure")]
        report = {
            "schema_version": 1,
            "kind": "ashwake-gauntlet-gameplay-scenario",
            "status": "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL",
            "engine_root": str(root),
            "project": str(project),
            "build": str(build),
            "configuration": args.configuration,
            "scenarios": results,
        }

    text = json.dumps(report, indent=2, ensure_ascii=False)
    out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
