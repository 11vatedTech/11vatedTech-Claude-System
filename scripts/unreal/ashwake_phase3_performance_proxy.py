#!/usr/bin/env python3
"""Capture representative Ashwake Phase 3 performance-proxy evidence.

Founder-facing outputs use blind aliases only. Private report keeps direction labels.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from runtime_evidence import run_unreal_process

ROOT = Path(__file__).resolve().parents[2]
# Smart App Control blocks newly packaged unsigned exes; see
# ashwake_environment_phase3_capture.py for the editor -game rationale.
DEFAULT_EXE = Path(os.environ.get("UNREAL_ENGINE_ROOT", "C:/Program Files/Epic Games/UE_5.8")) / "Engine/Binaries/Win64/UnrealEditor.exe"
DEFAULT_PROJECT = ROOT / "artifacts/unreal/calibration/FoundryCalibration.uproject"
DEFAULT_ALIAS_MAP = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/private/blind-alias-map.json"
DEFAULT_CAPTURE_ROOT = ROOT / "artifacts/unreal/health/ashwake-environment-apprenticeship-phase3/performance-proxy"
DEFAULT_PRIVATE_OUT = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/private/performance-proxy.json"
DEFAULT_PUBLIC_OUT = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/founder-package/performance-proxy-index.json"
MAP = "/Game/Calibration/Maps/EmberveilCalibration"
REQUIRED_MARKERS = [
    "ASHWAKE_MAP_BEGINPLAY",
    "ASHWAKE_GAMEPLAY_BEGIN",
    "ASHWAKE_ENVIRONMENT Direction=",
    "ASHWAKE_RELIQUARY_PLACED",
    "ASHWAKE_APPRENTICESHIP_LABS",
    "ASHWAKE_PHASE3_REVIEW_STATE",
    "ASHWAKE_PHASE3_PERFORMANCE_PROXY",
    "VISUAL_PROOF_BEGIN",
    "SCREENSHOT_REQUESTED",
]


def engine_root(explicit: Path | None) -> Path | None:
    if explicit:
        return explicit
    env = os.environ.get("UNREAL_ENGINE_ROOT")
    if env:
        return Path(env)
    base = Path("C:/Program Files/Epic Games")
    candidates = sorted(base.glob("UE_*") if base.exists() else [])
    return candidates[-1] if candidates else None


def execute(command: list[str], cwd: Path, timeout: int) -> dict[str, Any]:
    started = time.monotonic()
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return {
            "status": "PASS" if done.returncode == 0 else "FAIL",
            "exit_code": done.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "command": command,
            "stdout_tail": (done.stdout or "")[-6000:],
            "stderr_tail": (done.stderr or "")[-6000:],
        }
    except Exception as exc:
        return {"status": "FAIL", "command": command, "duration_seconds": round(time.monotonic() - started, 3), "error": f"{type(exc).__name__}: {exc}"}


def run_proxy(executable: Path, alias: str, direction: str, run_dir: Path, timeout: int, shots: int, csv_frames: int) -> dict[str, Any]:
    screenshot_dir = run_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "runtime.log"
    trace_path = run_dir / "runtime.utrace"
    if trace_path.exists():
        trace_path.unlink()
    args = [
        str(executable),
        str(DEFAULT_PROJECT.resolve()),
        MAP,
        "-game",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-stdout",
        "-FullStdOutLogOutput",
        "-windowed",
        "-ResX=1280",
        "-ResY=720",
        f"-AshwakeEnvironmentDirection={direction}",
        "-AshwakeNoHUD",
        "-AshwakeVisualProof",
        "-AshwakeVisualProofExit",
        f"-AshwakeVisualProofDir={screenshot_dir}",
        f"-AshwakeVisualProofShots={shots}",
        "-AshwakePhase3PerformanceProxy",
        "-AshwakePhase3ReviewState=ENVIRONMENT_OVERVIEW",
        f"-FoundryScenario=environment_apprenticeship_phase3_{alias.lower()}_performance_proxy",
        "-trace=default,frame,bookmark,cpu,loadtime,counters",
        f"-tracefile={trace_path}",
        "-tracefiletrunc",
        f"-csvCaptureFrames={csv_frames}",
        # Default category set only: named sets like "FrameTime" are not valid
        # in 5.8 and abort CSV capture entirely.
        "-csvGpuStats",
    ]
    result = run_unreal_process(args, executable.parent, timeout, log_path, expected_controlled_shutdown=True, fallback_log_roots=[DEFAULT_PROJECT.parent / "Saved" / "Logs"])
    # The engine writes CsvProfiler output to %LOCALAPPDATA%\UnrealEngine\<ver>\Saved
    # \Profiling\CSV regardless of cwd; harvest the newest file into the run dir.
    csv_profiler_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local"))) / "UnrealEngine/5.8/Saved/Profiling/CSV"
    if csv_profiler_dir.exists():
        candidates = [p for p in csv_profiler_dir.glob("Profile*.csv") if p.stat().st_mtime >= time.time() - max(60, result.get("duration_seconds", 0) + 30) and p.stat().st_size > 0]
        if candidates:
            newest = max(candidates, key=lambda p: p.stat().st_mtime)
            harvested = run_dir / "csv-profiler.csv"
            shutil.copyfile(newest, harvested)
            result["csv_profiler"] = {"source": str(newest), "harvested": str(harvested), "bytes": harvested.stat().st_size}
    text = result.get("complete_log_text", "")
    counts = {
        "performance_proxy": len(re.findall(r"ASHWAKE_PHASE3_PERFORMANCE_PROXY", text)),
        "reliquaries": len(re.findall(r"ASHWAKE_RELIQUARY_PLACED", text)),
        "lights": len(re.findall(r"ASHWAKE_LIGHT", text)),
        "material_studies": len(re.findall(r"Material study", text)),
        "state_studies": len(re.findall(r"State lab", text)),
        "audio_playing": len(re.findall(r"AUDIO_PLAYING", text)),
        "vfx_state": len(re.findall(r"VFX_STATE", text)),
        "screenshots_requested": len(re.findall(r"SCREENSHOT_REQUESTED", text)),
    }
    markers = {marker: marker in text for marker in REQUIRED_MARKERS}
    screenshots = sorted(screenshot_dir.glob("*.png"))
    screenshot_records = [{"path": str(p), "exists": p.exists(), "bytes": p.stat().st_size if p.exists() else 0} for p in screenshots]
    trace = {"path": str(trace_path), "exists": trace_path.exists(), "bytes": trace_path.stat().st_size if trace_path.exists() else 0}
    result.update({
        "alias": alias,
        "direction_private": direction,
        "run_dir": str(run_dir),
        "trace": trace,
        "screenshots": screenshot_records,
        "markers": markers,
        "counts": counts,
        "risk_inputs": {
            "fog_particles_glass_materials_geometry_lumen_audio": counts["performance_proxy"] > 0,
            "representative_geometry_proxy_actors_logged": counts["performance_proxy"] > 0,
            "real_rhi_runtime_seconds": result.get("duration_seconds"),
        },
        "csv_profiler_stats": parse_csv_profiler(run_dir / "csv-profiler.csv") if (run_dir / "csv-profiler.csv").exists() else {"status": "UNAVAILABLE", "reason": "csv_profiler_not_harvested"},
    })
    result["status"] = "PASS" if result.get("execution_state") == "SUCCESS" and all(markers.values()) and trace["exists"] and trace["bytes"] > 0 and counts["performance_proxy"] >= 1 and counts["reliquaries"] >= 3 and len(screenshot_records) >= shots else "FAIL"
    return result


def export_timers(engine: Path | None, trace_path: Path, out_csv: Path, timeout: int) -> dict[str, Any]:
    if engine is None:
        return {"status": "UNAVAILABLE", "reason": "engine_root_missing"}
    uat = engine / "Engine/Build/BatchFiles/RunUAT.bat"
    if not uat.exists():
        return {"status": "UNAVAILABLE", "reason": "uat_missing", "path": str(uat)}
    if out_csv.exists():
        out_csv.unlink()
    command = [str(uat), "ExportTimerStatisticsFromUtrace", f"-TraceFile={trace_path}", f"-CSVFile={out_csv}", "-TimerRegion=*", "-MaxTimerCount=120", "-Threads=GameThread"]
    result = execute(command, trace_path.parent, timeout)
    result.update({"csv": str(out_csv), "csv_exists": out_csv.exists(), "csv_bytes": out_csv.stat().st_size if out_csv.exists() else 0})
    if out_csv.exists() and result.get("status") == "PASS":
        result["summary"] = parse_timer_csv(out_csv)
    return result


def parse_timer_csv(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        rows = list(csv.DictReader(handle))
    top = []
    for row in rows[:15]:
        top.append({k: row.get(k, "") for k in row.keys() if k in {"TimerName", "Name", "Count", "TotalInclusiveTime", "MaxInclusiveTime", "AverageInclusiveTime", "MedianInclusiveTime"}})
    return {"rows": len(rows), "top_game_thread_timers": top}


def parse_csv_profiler(path: Path) -> dict[str, Any]:
    """Extract frame-time stats from a CsvProfiler capture CSV."""
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            # CsvProfiler CSVs carry very wide stat columns; raise the parser cap.
            csv.field_size_limit(min(2**31 - 1, max(10 * 1024 * 1024, csv.field_size_limit())))
            rows = list(csv.DictReader(handle))
    except Exception as exc:
        return {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    if not rows:
        return {"status": "FAIL", "error": "no_rows"}
    def column(*names: str) -> list[float]:
        out: list[float] = []
        for row in rows:
            for name in names:
                raw = row.get(name)
                if raw is None:
                    continue
                try:
                    out.append(float(raw))
                    break
                except ValueError:
                    continue
        return out
    frames = column("FrameTime", "FrameTime_MS", "GameThreadTime")
    stats = {
        "rows": len(rows),
        "columns": sorted(rows[0].keys())[:24],
    }
    if frames:
        ordered = sorted(frames)
        stats.update({
            "frame_samples": len(frames),
            "frame_ms_median": round(ordered[len(ordered) // 2], 3),
            "frame_ms_p95": round(ordered[int(len(ordered) * 0.95)], 3),
            "frame_ms_max": round(max(ordered), 3),
        })
    return {"status": "PASS", **stats}


def classify_risk(run: dict[str, Any], timer: dict[str, Any]) -> str:
    if run.get("status") != "PASS":
        return "ARCHITECTURAL PERFORMANCE RISK"
    duration = float(run.get("duration_seconds") or 0.0)
    trace_mb = float(run.get("trace", {}).get("bytes") or 0) / (1024.0 * 1024.0)
    if duration > 75.0 or trace_mb > 120.0 or timer.get("status") not in {"PASS", "UNAVAILABLE"}:
        return "MODERATE RISK"
    return "EASY TO OPTIMIZE"


def public_run(run: dict[str, Any], timer: dict[str, Any], risk: str) -> dict[str, Any]:
    return {
        "alias": run.get("alias"),
        "status": run.get("status"),
        "run_dir": run.get("run_dir"),
        "trace": run.get("trace"),
        "screenshots": run.get("screenshots", []),
        "counts": run.get("counts", {}),
        "timer_export_status": timer.get("status"),
        "timer_csv": timer.get("csv"),
        "timer_summary": timer.get("summary"),
        "csv_profiler_stats": run.get("csv_profiler_stats"),
        "risk_classification": risk,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--alias-map", type=Path, default=DEFAULT_ALIAS_MAP)
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE_ROOT)
    parser.add_argument("--private-out", type=Path, default=DEFAULT_PRIVATE_OUT)
    parser.add_argument("--public-out", type=Path, default=DEFAULT_PUBLIC_OUT)
    parser.add_argument("--engine-root", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--analysis-timeout", type=int, default=240)
    # Six shots at the engine's 0.75 s screenshot cadence keeps the process
    # alive long enough for -csvCaptureFrames=120 to fill and flush before the
    # delayed visual-proof exit fires.
    parser.add_argument("--shots", type=int, default=6)
    parser.add_argument("--csv-frames", type=int, default=120)
    args = parser.parse_args()

    alias_data = json.loads(args.alias_map.read_text(encoding="utf-8"))
    aliases: dict[str, str] = alias_data["aliases"]
    engine = engine_root(args.engine_root)
    runs: list[dict[str, Any]] = []
    timers: list[dict[str, Any]] = []
    public_runs: list[dict[str, Any]] = []

    if not args.executable.exists():
        report = {"schema_version": 1, "kind": "ashwake-phase3-private-performance-proxy", "status": "UNAVAILABLE", "error": "executable_missing", "executable": str(args.executable)}
        args.private_out.parent.mkdir(parents=True, exist_ok=True)
        args.private_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    for alias, direction in aliases.items():
        run_dir = args.capture_root / alias.lower()
        run = run_proxy(args.executable.resolve(), alias, direction, run_dir, args.timeout, args.shots, args.csv_frames)
        runs.append(run)
        trace_path = Path(run.get("trace", {}).get("path", ""))
        timer = export_timers(engine, trace_path, run_dir / "game-thread-timers.csv", args.analysis_timeout) if trace_path.exists() else {"status": "SKIPPED", "reason": "trace_missing"}
        timer.update({"alias": alias, "direction_private": direction})
        timers.append(timer)
        public_runs.append(public_run(run, timer, classify_risk(run, timer)))

    public = {
        "schema_version": 1,
        "kind": "ashwake-phase3-founder-performance-proxy-index",
        "date": "2026-08-21",
        "status": "PASS" if all(r.get("status") == "PASS" for r in runs) else "FAIL",
        "selection_status": "NO_FINAL_PRODUCTION_DIRECTION_SELECTED",
        "identity_rule": "Founder-facing records use aliases only.",
        "runs": public_runs,
        "claim_limits": [
            "Performance proxy exposes architectural risk only; it is not final optimization proof.",
            "Do not reject a creatively superior option solely because an unoptimized proxy is heavier.",
        ],
    }
    private = {
        "schema_version": 1,
        "kind": "ashwake-phase3-private-performance-proxy",
        "date": "2026-08-21",
        "status": public["status"],
        "executable": str(args.executable),
        "engine_root": str(engine) if engine else None,
        "alias_map_private": str(args.alias_map),
        "runs": runs,
        "timer_exports": timers,
        "public_out": str(args.public_out),
    }
    args.private_out.parent.mkdir(parents=True, exist_ok=True)
    args.public_out.parent.mkdir(parents=True, exist_ok=True)
    args.private_out.write_text(json.dumps(private, indent=2, ensure_ascii=False), encoding="utf-8")
    args.public_out.write_text(json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": public["status"], "private_out": str(args.private_out), "public_out": str(args.public_out)}, indent=2))
    return 0 if public["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
