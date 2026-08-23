#!/usr/bin/env python3
"""Capture current Ashwake packaged gameplay performance and visual evidence."""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import struct
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from runtime_evidence import run_unreal_process

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXE = ROOT / "artifacts/unreal/calibration/Packaged/Ashwake/Windows/FoundryCalibration/Binaries/Win64/FoundryCalibration.exe"
DEFAULT_PROJECT = ROOT / "artifacts/unreal/calibration/FoundryCalibration.uproject"
DEFAULT_OUT = ROOT / "artifacts/unreal/health/ashwake-performance-visual-evidence.json"
DEFAULT_CAPTURE_ROOT = ROOT / "artifacts/unreal/health/ashwake-performance-visual"
MAP = "/Game/Calibration/Maps/EmberveilCalibration"
LOG_WARNING_PATTERN = re.compile(r"(Failed to find|Failed to load|Can't find file|Soft Object Path|Missing package|SkipPackage|LogStreaming: Warning|LogUObjectGlobals: Warning)", re.I)
REFERENCE_TOKENS = ["/Game/Calibration", "Niagara", "SoundWave", "Animation", "SkeletalMesh", "Emberveil", "Calibration"]
REQUIRED_MARKERS = [
    "ASHWAKE_MAP_BEGINPLAY",
    "ASHWAKE_GAMEPLAY_BEGIN",
    "INPUT_PROOF_BEGIN",
    "INPUT_PROOF_SEND_KEY Key=E",
    "INPUT_RECEIVED action=Attune",
    "INTERACTION_QUERY",
    "GAMEPLAY_COMMAND action=Attune",
    "INTERACTION_ACCEPTED",
    "ASSET_RUNTIME_LOADED",
    "PLAYER_SUCCESS",
    "INPUT_PROOF_SEND_KEY Key=R",
    "INPUT_RECEIVED action=Restart",
    "RECOVERY_RESTART",
    "INPUT_PROOF_COMPLETE Result=SuccessAndRestart",
    "VFX_STATE",
    "AUDIO_PLAYING",
    "ANIMATION_PLAYING",
    "VISUAL_PROOF_BEGIN",
    "SCREENSHOT_REQUESTED",
    "VISUAL_PROOF_COMPLETE",
]


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


def execute(args: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        done = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        stdout = done.stdout or ""
        stderr = done.stderr or ""
        return {
            "status": "PASS" if done.returncode == 0 else "FAIL",
            "exit_code": done.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": stdout,
            "stderr": stderr,
            "stdout_tail": stdout[-8000:],
            "stderr_tail": stderr[-8000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = str(exc.stdout or "")
        stderr = str(exc.stderr or "")
        return {
            "status": "TIMEOUT",
            "exit_code": None,
            "duration_seconds": round(time.monotonic() - started, 3),
            "stdout": stdout,
            "stderr": stderr,
            "stdout_tail": stdout[-8000:],
            "stderr_tail": stderr[-8000:],
        }


def runtime_reference_warnings(text: str) -> list[str]:
    warnings = []
    for line in text.splitlines():
        if LOG_WARNING_PATTERN.search(line) and any(token in line for token in REFERENCE_TOKENS):
            warnings.append(line.strip())
    return warnings[-50:]


def runtime_asset_loads(text: str) -> list[dict[str, Any]]:
    checks = []
    pattern = re.compile(r"ASSET_RUNTIME_LOADED Id=(\S+) ObjectPath=(\S+) ExpectedClass=(\S+) ActualClass=(\S+) RuntimeLoadable=(\d+)")
    for match in pattern.finditer(text):
        expected = match.group(3)
        actual = match.group(4)
        loadable = match.group(5) == "1"
        checks.append({
            "id": match.group(1),
            "object_path": match.group(2),
            "expected_class": expected,
            "actual_class": actual,
            "runtime_loadable": loadable,
            "status": "PASS" if loadable and actual == expected else "FAIL",
        })
    return checks


def png_info(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()[:32]
    except OSError as exc:
        return {"path": str(path), "error": str(exc)}
    info: dict[str, Any] = {"path": str(path), "bytes": path.stat().st_size}
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        info.update({"format": "png", "width": width, "height": height})
    else:
        info["format"] = "unknown"
    return info


def newest_files(root: Path, suffixes: set[str], started_epoch: float) -> list[str]:
    if not root.exists():
        return []
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in suffixes and p.stat().st_mtime >= started_epoch - 2]
    files.sort(key=lambda p: p.stat().st_mtime)
    return [str(p) for p in files]


def has_fatal_runtime_failure(text: str) -> bool:
    fatal_pattern = re.compile(r"(Fatal error|Unhandled Exception|LogWindows: Error:|LogCore: Error:|LogOutputDevice: Error:|GPU crash|LowLevelFatalError)", re.I)
    return any(fatal_pattern.search(line) for line in text.splitlines())


def has_successful_controlled_shutdown(text: str) -> bool:
    return "INPUT_PROOF_COMPLETE Result=SuccessAndRestart" in text and "LogExit: Exiting." in text and "RequestExitWithStatus(0, 0" in text


def run_capture(executable: Path, capture_dir: Path, timeout: int, csv_frames: int, screenshot_count: int) -> dict[str, Any]:
    capture_dir.mkdir(parents=True, exist_ok=True)
    run_id = capture_dir.name if capture_dir.name else f"ashwake-visual-{uuid.uuid4().hex[:12]}"
    screenshot_dir = capture_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_path = capture_dir / "ashwake-performance-visual.log"
    trace_path = capture_dir / "ashwake-current-gameplay.utrace"
    if trace_path.exists():
        trace_path.unlink()

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
        "-AshwakeInputProof",
        "-AshwakeInputProofExit",
        f"-FoundryRunId={run_id}",
        "-FoundryScenario=performance_visual",
        "-ExecCmds=CSVProfile STOP",
        "-AshwakeVisualProof",
        f"-AshwakeVisualProofDir={screenshot_dir}",
        f"-AshwakeVisualProofShots={screenshot_count}",
        "-trace=default,frame,bookmark,cpu,loadtime,counters",
        f"-tracefile={trace_path}",
        "-tracefiletrunc",
        f"-csvCaptureFrames={csv_frames}",
        "-csvCategories=FrameTime,Game,Rendering,RHI,GPU,CsvProfiler",
        "-csvGpuStats",
    ]

    started_epoch = time.time()
    result = run_unreal_process(args, executable.parent, timeout, log_path, expected_controlled_shutdown=True, fallback_log_roots=[executable.parents[2] / "Saved" / "Logs"])
    text = result["complete_log_text"]
    markers = {marker: marker in text for marker in REQUIRED_MARKERS}
    warnings = runtime_reference_warnings(text)
    runtime_loads = runtime_asset_loads(text)
    counts = {
        "input_events": len(re.findall(r"LogFoundry: INPUT_RECEIVED", text)),
        "interaction_queries": len(re.findall(r"LogFoundry: INTERACTION_QUERY", text)),
        "gameplay_commands": len(re.findall(r"LogFoundry: GAMEPLAY_COMMAND", text)),
        "accepted_interactions": len(re.findall(r"LogFoundry: INTERACTION_ACCEPTED", text)),
        "state_changes": len(re.findall(r"LogFoundry: STATE_CHANGED", text)),
        "vfx_state": len(re.findall(r"LogFoundry: VFX_STATE", text)),
        "audio_playing": len(re.findall(r"LogFoundry: AUDIO_PLAYING", text)),
        "animation_playing": len(re.findall(r"LogFoundry: ANIMATION_PLAYING", text)),
        "screenshot_requested": len(re.findall(r"LogFoundry: SCREENSHOT_REQUESTED", text)),
    }
    csv_files = newest_files(executable.parents[2] / "Saved", {".csv"}, started_epoch)
    screenshots = [png_info(p) for p in sorted(screenshot_dir.glob("*.png"))]
    exit_ok = result["exit_code"] == 0
    fatal_runtime_failure = has_fatal_runtime_failure(text)
    if not exit_ok and has_successful_controlled_shutdown(text) and not fatal_runtime_failure:
        result["nonzero_exit_after_controlled_shutdown"] = True
    result.update({
        "run_id": run_id,
        "command": result.get("command", args),
        "log": str(log_path),
        "log_exists": log_path.exists(),
        "log_status": result.get("requested_log_status"),
        "trace": {"path": str(trace_path), "exists": trace_path.exists(), "bytes": trace_path.stat().st_size if trace_path.exists() else 0},
        "csv_files": csv_files,
        "screenshots": screenshots,
        "markers": markers,
        "counts": counts,
        "runtime_asset_loads": runtime_loads,
        "runtime_reference_warnings": warnings,
        "fatal_runtime_failure": fatal_runtime_failure,
        "controlled_shutdown": has_successful_controlled_shutdown(text),
        "text_tail": text[-8000:],
    })
    exit_ok = result.get("exit_classification", {}).get("classification") in {"NORMAL_EXIT", "CONTROLLED_TEST_SHUTDOWN"}
    runtime_ids = {check["id"] for check in runtime_loads if check["status"] == "PASS"}
    expected_runtime_ids = {"emberveil_attune_vfx", "ashwake_safe_window_audio", "ashwake_hostile_audio", "ashwake_attune_success_audio", "ashwake_attune_reject_audio", "emberveil_idle_animation", "emberveil_safe_animation", "emberveil_hostile_animation", "emberveil_success_animation"}
    screenshot_files_verified = len(screenshots) >= screenshot_count and all(s.get("format") == "png" and s.get("width", 0) > 0 and s.get("height", 0) > 0 for s in screenshots)
    result["screenshot_files_verified"] = screenshot_files_verified
    result["status"] = "PASS" if exit_ok and result.get("requested_log_exists") and all(markers.values()) and expected_runtime_ids.issubset(runtime_ids) and not warnings and trace_path.exists() and trace_path.stat().st_size > 0 and screenshot_files_verified else "FAIL"
    return result


def summarize_trace(engine: Path, trace_path: Path, out_dir: Path, timeout: int) -> dict[str, Any]:
    editor = engine / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    if not editor.exists():
        return {"status": "UNAVAILABLE", "error": "editor_cmd_missing", "path": str(editor)}
    before = {str(p) for p in out_dir.glob("ashwake-current-gameplay*.csv")}
    result = execute([str(editor), "-run=SummarizeTrace", f"-inputfile={trace_path}", "-unattended", "-nop4", "-nosplash", "-stdout", "-FullStdOutLogOutput"], out_dir, timeout)
    after = sorted(str(p) for p in out_dir.glob("ashwake-current-gameplay*.csv") if str(p) not in before or p.exists())
    result.update({"command": [str(editor), "-run=SummarizeTrace", f"-inputfile={trace_path}"], "csv_outputs": after})
    return result


def export_timer_stats(engine: Path, trace_path: Path, out_csv: Path, timeout: int) -> dict[str, Any]:
    uat = engine / "Engine/Build/BatchFiles/RunUAT.bat"
    if not uat.exists():
        return {"status": "UNAVAILABLE", "error": "uat_missing", "path": str(uat)}
    if out_csv.exists():
        out_csv.unlink()
    args = [str(uat), "ExportTimerStatisticsFromUtrace", f"-TraceFile={trace_path}", f"-CSVFile={out_csv}", "-TimerRegion=*", "-MaxTimerCount=200", "-Threads=GameThread"]
    result = execute(args, trace_path.parent, timeout)
    result.update({"command": args, "csv": str(out_csv), "csv_exists": out_csv.exists(), "csv_bytes": out_csv.stat().st_size if out_csv.exists() else 0})
    return result


def parse_timer_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "MISSING", "path": str(path)}
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as exc:
        return {"status": "FAIL", "path": str(path), "error": str(exc)}
    top = []
    for row in rows[:20]:
        top.append({k: row.get(k, "") for k in row.keys() if k in {"TimerName", "Name", "Count", "TotalInclusiveTime", "MaxInclusiveTime", "AverageInclusiveTime", "MedianInclusiveTime"}})
    return {"status": "PASS", "path": str(path), "rows": len(rows), "top_game_thread_timers": top}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine-root", type=Path)
    parser.add_argument("--executable", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--project", type=Path, default=DEFAULT_PROJECT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE_ROOT)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--analysis-timeout", type=int, default=240)
    parser.add_argument("--csv-frames", type=int, default=420)
    parser.add_argument("--screenshots", type=int, default=4)
    args = parser.parse_args()

    engine = engine_root(args.engine_root).resolve()
    executable = args.executable.resolve()
    capture_root = args.capture_root.resolve()
    run_dir = capture_root / str(int(time.time() * 1000))
    args.out.parent.mkdir(parents=True, exist_ok=True)

    if not executable.exists():
        report = {"schema_version": 1, "kind": "ashwake-performance-visual-evidence", "status": "UNAVAILABLE", "error": "executable_missing", "executable": str(executable)}
    else:
        capture = run_capture(executable, run_dir, args.timeout, args.csv_frames, args.screenshots)
        trace_path = Path(capture["trace"]["path"])
        summary = summarize_trace(engine, trace_path, run_dir, args.analysis_timeout) if trace_path.exists() else {"status": "SKIPPED", "reason": "trace_missing"}
        timer_csv = run_dir / "ashwake-game-thread-timers.csv"
        timers = export_timer_stats(engine, trace_path, timer_csv, args.analysis_timeout) if trace_path.exists() else {"status": "SKIPPED", "reason": "trace_missing"}
        timer_summary = parse_timer_stats(timer_csv)
        budgets = {
            "resolution": "1280x720",
            "real_rhi_required": True,
            "audio_required": True,
            "trace_required": True,
            "screenshots_required": args.screenshots,
            "runtime_reference_warnings_allowed": 0,
            "gameplay_markers_required": REQUIRED_MARKERS,
            "note": "Budgets are gate definitions for current evidence capture; no blind optimization claim made from trace existence alone.",
        }
        report = {
            "schema_version": 1,
            "kind": "ashwake-performance-visual-evidence",
            "status": "PASS" if capture["status"] == "PASS" and summary.get("status") == "PASS" and timers.get("status") == "PASS" and timer_summary.get("status") == "PASS" else "FAIL",
            "engine_root": str(engine),
            "executable": str(executable),
            "capture_dir": str(run_dir),
            "budgets": budgets,
            "capture": capture,
            "trace_summary": summary,
            "timer_export": timers,
            "timer_summary": timer_summary,
            "visual_review_required": True,
            "claim_limits": [
                "Current run proves real-RHI/audio gameplay capture and analyzable trace/CSV artifacts only.",
                "Screenshots are visual QA evidence inputs, not proof of artistic success by themselves.",
            ],
        }

    text = json.dumps(report, indent=2, ensure_ascii=False)
    args.out.write_text(text, encoding="utf-8")
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))
        sys.stdout.buffer.write(b"\n")
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
