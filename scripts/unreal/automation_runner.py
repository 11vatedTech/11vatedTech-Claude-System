#!/usr/bin/env python3
"""Reusable Unreal Automation runner with log-file streaming, phase classification,
watchdog timeout, and machine-readable JSON results.

Key discovery (2026-08-20): UE 5.8 requires -ExecCmds="..." (equals-sign form).
Space-separated -ExecCmds "..." silently ignores the command.

Usage:
  python automation_runner.py --project <path> --tests <pattern> [--timeout 600] [--null-rhi]
  python automation_runner.py --project <path> --run-all [--timeout 3600] [--null-rhi]
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path
from typing import Any

LOG_PHASES = {
    "init": re.compile(r"LogInit:|LogEngine:|LogModuleManager:", re.I),
    "automation": re.compile(r"AutomationController|AutomationWorker|AutomationCommandLine|Automation:", re.I),
    "test": re.compile(r"Test Started|Test Completed|Test.*Result|BeginEvents|EndEvents", re.I),
    "error": re.compile(r"Error:|FATAL|panic|crash", re.I),
    "exit": re.compile(r"LogExit:|RequestExit|TestExit|Engine exit", re.I),
}

def classify_line(line: str) -> str:
    for phase, pat in LOG_PHASES.items():
        if pat.search(line):
            return phase
    return "runtime"

def find_latest_log(log_dir: Path) -> Path | None:
    """Find the most recently modified FoundryCalibration*.log file."""
    logs = sorted(log_dir.glob("FoundryCalibration*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None

def stream_log(log_path: Path, start_time: float, tail_only: bool = False) -> list[str]:
    """Read log file, return new lines since start_time or last N lines."""
    if not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return lines[-200:] if tail_only else lines
    except Exception:
        return []

def run_automation(
    project: Path,
    test_pattern: str | None = None,
    run_all: bool = False,
    timeout: int = 600,
    null_rhi: bool = True,
    extra_args: list[str] | None = None,
    engine_root: Path | None = None,
) -> dict[str, Any]:
    """Run Unreal automation tests and return structured results."""
    project = Path(project).resolve()
    if not engine_root:
        candidates = sorted(Path("C:/Program Files/Epic Games").glob("UE_*") if Path("C:/Program Files/Epic Games").exists() else [])
        if not candidates:
            return {"status": "ERROR", "error": "no_engine_root"}
        engine_root = candidates[-1]

    editor_cmd = engine_root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
    if not editor_cmd.exists():
        return {"status": "ERROR", "error": f"editor_not_found: {editor_cmd}"}

    # Build command — EQUALS-SIGN form is required for UE 5.8
    if run_all:
        exec_cmds = "Automation RunAll"
    elif test_pattern:
        exec_cmds = f"Automation RunTests {test_pattern}"
    else:
        return {"status": "ERROR", "error": "no_test_pattern_or_run_all"}

    # On Windows, subprocess.list2cmdline handles quoting.
    # Passing -ExecCmds="..." as a single arg causes double-quoting.
    # Instead, pass the raw form and let list2cmdline handle it.
    args = [
        str(editor_cmd),
        str(project),
        f"-ExecCmds={exec_cmds}",
        f"-TestExit=Automation Test Queue Empty",
        "-NoSound",
        "-NoSplash",
        "-Unattended",
        "-Messaging",
        "-log",
    ]
    if null_rhi:
        args.insert(4, "-NullRHI")
    if extra_args:
        args.extend(extra_args)

    log_dir = project.parent / "Saved" / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    test_results: list[dict[str, Any]] = []
    phase_counts: dict[str, int] = {}
    last_line = ""

    # Get existing log files before launch to detect the new one
    old_logs = set(p.name for p in log_dir.glob("FoundryCalibration*.log"))

    # Launch with NO pipe — let Unreal write to its own console
    # We read the log file instead for streaming
    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(project.parent),
    )

    log_path = None
    timed_out = False
    exit_code = None

    try:
        # Wait for log file to appear
        for _ in range(60):
            if time.monotonic() - started > timeout:
                timed_out = True
                break
            time.sleep(1)
            current_logs = set(p.name for p in log_dir.glob("FoundryCalibration*.log"))
            new_logs = current_logs - old_logs
            if new_logs:
                log_path = log_dir / sorted(new_logs, key=lambda p: (log_dir / p).stat().st_mtime)[0]
                break

        if not log_path:
            log_path = find_latest_log(log_dir)

        if log_path:
            last_offset = 0
            while proc.poll() is None:
                elapsed = time.monotonic() - started
                if elapsed > timeout:
                    timed_out = True
                    proc.kill()
                    break

                try:
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        f.seek(last_offset)
                        new_lines = f.readlines()
                        last_offset = f.tell()
                except Exception:
                    time.sleep(2)
                    continue

                for line in new_lines:
                    line = line.rstrip("\n\r")
                    if not line:
                        continue
                    phase = classify_line(line)
                    phase_counts[phase] = phase_counts.get(phase, 0) + 1
                    last_line = line

                    m = re.search(r"Test Completed\. Result=\{(\w+)\}.*Name=\{(.+?)\}.*Path=\{(.+?)\}", line)
                    if m:
                        test_results.append({
                            "result": m.group(1),
                            "name": m.group(2),
                            "path": m.group(3),
                            "elapsed_seconds": round(elapsed, 3),
                        })

                    if phase in ("test", "error", "exit", "automation"):
                        print(f"  [{elapsed:7.1f}s] [{phase}] {line}", file=sys.stderr)

                time.sleep(2)

        exit_code = proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        proc.wait(timeout=5)
    except Exception as e:
        proc.kill()
        return {"status": "ERROR", "error": str(e)}

    duration = round(time.monotonic() - started, 3)
    total_tests = len(test_results)
    passed = sum(1 for t in test_results if t["result"] == "Success")
    failed = sum(1 for t in test_results if t["result"] not in ("Success",))

    status = "PASS"
    if timed_out:
        status = "TIMEOUT"
    elif failed > 0:
        status = "FAIL"
    elif total_tests == 0:
        status = "NO_TESTS_FOUND"

    return {
        "schema_version": 1,
        "kind": "unreal-automation",
        "status": status,
        "project": str(project),
        "test_pattern": test_pattern or ("RunAll" if run_all else None),
        "engine_root": str(engine_root),
        "duration_seconds": duration,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "timeout_seconds": timeout,
        "total_tests": total_tests,
        "passed": passed,
        "failed": failed,
        "tests": test_results,
        "phase_counts": phase_counts,
        "last_line": last_line,
        "log_file": str(log_path) if log_path else None,
    }

def main() -> int:
    p = argparse.ArgumentParser(description="Unreal Automation Runner")
    p.add_argument("--project", type=Path, required=True, help="Path to .uproject")
    p.add_argument("--tests", type=str, default=None, help="Test name pattern")
    p.add_argument("--run-all", action="store_true", help="Run all registered tests")
    p.add_argument("--timeout", type=int, default=600, help="Timeout in seconds")
    p.add_argument("--null-rhi", action="store_true", default=True, help="Use NullRHI (default)")
    p.add_argument("--no-null-rhi", action="store_false", dest="null_rhi", help="Disable NullRHI")
    p.add_argument("--engine-root", type=Path, default=None, help="Explicit engine root")
    p.add_argument("--output", type=Path, default=None, help="Write JSON results to file")
    args = p.parse_args()

    result = run_automation(
        project=Path(args.project).absolute(),
        test_pattern=args.tests,
        run_all=args.run_all,
        timeout=args.timeout,
        null_rhi=args.null_rhi,
        engine_root=args.engine_root,
    )

    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    print(output_json)

    if args.output:
        out_path = Path(args.output).absolute()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output_json, encoding="utf-8")

    return 0 if result["status"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
