#!/usr/bin/env python3
"""Capture Ashwake Environment Apprenticeship Phase 2 runtime blockout evidence."""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import time
from pathlib import Path
from typing import Any

from runtime_evidence import run_unreal_process

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = ROOT / "artifacts/unreal/calibration/Packaged/ashwake-env-apprenticeship-phase2/Windows/FoundryCalibration/Binaries/Win64/FoundryCalibration.exe"
DEFAULT_OUT = ROOT / "artifacts/unreal/health/ashwake-environment-apprenticeship-phase2-evidence.json"
DEFAULT_CAPTURE_ROOT = ROOT / "artifacts/unreal/health/ashwake-environment-apprenticeship-phase2"
MAP = "/Game/Calibration/Maps/EmberveilCalibration"
DIRECTIONS = ["CINDERWORKS_ABBEY", "EMBER_HOSPICE", "FALLEN_SUN_ORCHARD"]
REQUIRED_MARKERS = [
    "ASHWAKE_MAP_BEGINPLAY",
    "ASHWAKE_GAMEPLAY_BEGIN",
    "ASHWAKE_ENVIRONMENT Direction=",
    "ASHWAKE_RELIQUARY_PLACED",
    "ASHWAKE_APPRENTICESHIP_LABS",
    "INPUT_PROOF_BEGIN",
    "INPUT_PROOF_SEND_KEY Key=E",
    "INPUT_RECEIVED action=Attune",
    "GAMEPLAY_COMMAND action=Attune",
    "VISUAL_PROOF_BEGIN",
    "SCREENSHOT_REQUESTED",
]


def png_info(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return info
    info["bytes"] = path.stat().st_size
    data = path.read_bytes()[:32]
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        info.update({"format": "png", "width": width, "height": height})
    else:
        info["format"] = "unknown"
    return info


def marker_counts(text: str) -> dict[str, int]:
    patterns = {
        "environment_ready": r"ASHWAKE_ENVIRONMENT Direction=",
        "reliquary_placed": r"ASHWAKE_RELIQUARY_PLACED",
        "labs_ready": r"ASHWAKE_APPRENTICESHIP_LABS",
        "lighting_lights": r"ASHWAKE_LIGHT label=Lighting Variant",
        "material_studies": r"Material study ",
        "state_studies": r"State lab ",
        "screenshots_requested": r"SCREENSHOT_REQUESTED",
        "state_changes": r"RELIQUARY_STATE",
        "interaction_accepted": r"INTERACTION_ACCEPTED",
        "interaction_rejected": r"INTERACTION_REJECTED",
        "player_success": r"PLAYER_SUCCESS|INPUT_PROOF_COMPLETE Result=SuccessAndRestart",
        "player_failure": r"PLAYER_FAILURE|INPUT_PROOF_COMPLETE Result=FailureAndRestart",
    }
    return {name: len(re.findall(pattern, text)) for name, pattern in patterns.items()}


def run_direction(executable: Path, capture_root: Path, direction: str, mode: str, timeout: int, screenshots: int) -> dict[str, Any]:
    run_dir = capture_root / direction.lower() / mode
    screenshot_dir = run_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "runtime.log"
    args = [
        str(executable),
        MAP,
        "-unattended",
        "-nop4",
        "-nosplash",
        "-stdout",
        "-FullStdOutLogOutput",
        "-windowed",
        "-ResX=1280",
        "-ResY=720",
        f"-AshwakeEnvironmentDirection={direction}",
        "-AshwakeInputProof",
        "-AshwakeInputProofExit",
        "-AshwakeVisualProof",
        f"-AshwakeVisualProofDir={screenshot_dir}",
        f"-AshwakeVisualProofShots={screenshots}",
        f"-FoundryScenario=environment_apprenticeship_phase2_{direction.lower()}_{mode}",
    ]
    if mode == "failure":
        args.append("-AshwakeInputProofFailure")
    result = run_unreal_process(args, executable.parent, timeout, log_path, expected_controlled_shutdown=True, fallback_log_roots=[executable.parents[2] / "Saved" / "Logs"])
    text = result.get("complete_log_text", "")
    counts = marker_counts(text)
    markers = {marker: marker in text for marker in REQUIRED_MARKERS}
    screenshots_found = [png_info(path) for path in sorted(screenshot_dir.glob("*.png"))]
    required_screenshots = 1 if mode == "failure" else screenshots
    screenshot_ok = len(screenshots_found) >= required_screenshots and all(item.get("format") == "png" and item.get("width", 0) > 0 and item.get("height", 0) > 0 for item in screenshots_found)
    expected_mode_ok = counts["player_failure"] > 0 if mode == "failure" else counts["player_success"] > 0
    blockout_ok = counts["environment_ready"] >= 1 and counts["reliquary_placed"] >= 3 and counts["labs_ready"] >= 1 and counts["lighting_lights"] >= 6 and counts["material_studies"] >= 5 and counts["state_studies"] >= 5
    status = "PASS" if result.get("execution_state") == "SUCCESS" and all(markers.values()) and screenshot_ok and expected_mode_ok and blockout_ok else "FAIL"
    return {
        "direction": direction,
        "mode": mode,
        "status": status,
        "run_dir": str(run_dir),
        "command": result.get("command", args),
        "exit_classification": result.get("exit_classification"),
        "duration_seconds": result.get("duration_seconds"),
        "log": result.get("complete_log_path"),
        "markers": markers,
        "counts": counts,
        "screenshots": screenshots_found,
        "required_screenshots": required_screenshots,
        "screenshot_ok": screenshot_ok,
        "expected_mode_ok": expected_mode_ok,
        "blockout_ok": blockout_ok,
        "text_tail": text[-6000:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--screenshots", type=int, default=4)
    parser.add_argument("--mode", choices=["success", "failure", "both"], default="both")
    args = parser.parse_args()

    executable = args.executable.resolve()
    args.capture_root.mkdir(parents=True, exist_ok=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    if not executable.exists():
        report: dict[str, Any] = {
            "schema_version": 1,
            "kind": "ashwake-environment-apprenticeship-phase2-runtime-evidence",
            "status": "UNAVAILABLE",
            "error": "executable_missing",
            "executable": str(executable),
        }
    else:
        modes = ["success", "failure"] if args.mode == "both" else [args.mode]
        runs = [run_direction(executable, args.capture_root, direction, mode, args.timeout, args.screenshots) for direction in DIRECTIONS for mode in modes]
        report = {
            "schema_version": 1,
            "kind": "ashwake-environment-apprenticeship-phase2-runtime-evidence",
            "status": "PASS" if all(run["status"] == "PASS" for run in runs) else "FAIL",
            "date": "2026-08-21",
            "duration_seconds": round(time.time() - started, 3),
            "executable": str(executable),
            "map": MAP,
            "directions": DIRECTIONS,
            "modes": modes,
            "claim_limits": [
                "Evidence proves runtime-generated BLOCKOUT/lab execution, not final art quality.",
                "CINDERWORKS_ABBEY remains CURRENT_LEADING_HYPOTHESIS, not proven winner.",
                "Screenshots are comparable evidence inputs; human/specialist review still required before selection.",
            ],
            "runs": runs,
        }
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
