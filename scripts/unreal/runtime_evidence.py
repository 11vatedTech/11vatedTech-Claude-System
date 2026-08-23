#!/usr/bin/env python3
"""Reusable runtime evidence capture and classification for Unreal Foundry."""
from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    from windows_env import foundry_subprocess_env, unreal_arg_path
except ImportError:  # pragma: no cover - supports package-style imports in tests
    from scripts.unreal.windows_env import foundry_subprocess_env, unreal_arg_path


EXIT_NORMAL = "NORMAL_EXIT"
EXIT_CONTROLLED = "CONTROLLED_TEST_SHUTDOWN"
EXIT_WATCHDOG = "WATCHDOG_TERMINATION"
EXIT_CRASH = "CRASH"
EXIT_FATAL = "FATAL_ENGINE_ERROR"
EXIT_UNKNOWN = "UNKNOWN_EXIT"

EXEC_SUCCESS = "SUCCESS"
EXEC_PRODUCT_FAILURE = "PRODUCT_FAILURE"
EXEC_TOOL_TRANSIENT_FAILURE = "TOOL_TRANSIENT_FAILURE"
EXEC_TOOL_RETRY_SUCCESS = "TOOL_RETRY_SUCCESS"
EXEC_TOOL_PERMANENT_FAILURE = "TOOL_PERMANENT_FAILURE"

FATAL_PATTERN = re.compile(r"(Fatal error|LowLevelFatalError|LogOutputDevice: Error:|LogCore: Error:|LogWindows: Error:|GPU crash)", re.I)
# Note: editor-mode boots always spawn "Started CrashReportClient (pid=...)" as a
# bystander process; only treat CrashReportClient as crash evidence when paired
# with an actual crash signature, which the other alternatives cover.
CRASH_PATTERN = re.compile(r"(Unhandled Exception|EXCEPTION_ACCESS_VIOLATION|LogCrashDebugHelper|ensure condition failed)", re.I)
TRANSIENT_TOOL_PATTERN = re.compile(r"(Connection reset|temporar(?:y|ily)|timed out|timeout waiting for tool|rate limit|HTTP 5\d\d|transport error|\bEPIPE\b|\bECONNRESET\b)", re.I)
CONTROLLED_PATTERN = re.compile(r"(RequestExitWithStatus\(0,\s*0|RequestExit\(|INPUT_PROOF_COMPLETE|VISUAL_PROOF_COMPLETE|Automation Test Queue Empty|Engine exit requested)", re.I)
NORMAL_PATTERN = re.compile(r"(LogExit: Exiting\.|Engine shut down|BUILD SUCCESSFUL|Result=Passed|result=Passed)", re.I)


def classify_exit(exit_code: int | None, text: str, timed_out: bool = False, expected_controlled_shutdown: bool = False) -> dict[str, Any]:
    fatal = bool(FATAL_PATTERN.search(text))
    crash = bool(CRASH_PATTERN.search(text))
    controlled = bool(CONTROLLED_PATTERN.search(text))
    normal = bool(NORMAL_PATTERN.search(text))
    if timed_out:
        classification = EXIT_WATCHDOG
    elif fatal:
        classification = EXIT_FATAL
    elif crash:
        classification = EXIT_CRASH
    elif exit_code == 0 and (normal or controlled or not text):
        classification = EXIT_NORMAL
    elif expected_controlled_shutdown and controlled and normal and not fatal and not crash:
        classification = EXIT_CONTROLLED
    elif controlled and normal and not fatal and not crash:
        classification = EXIT_CONTROLLED
    else:
        classification = EXIT_UNKNOWN
    return {
        "classification": classification,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "expected_controlled_shutdown": expected_controlled_shutdown,
        "has_controlled_shutdown_evidence": controlled,
        "has_normal_exit_evidence": normal,
        "has_fatal_engine_error": fatal,
        "has_crash_evidence": crash,
    }


def classify_execution_state(exit_info: dict[str, Any], stderr: str = "", stdout: str = "") -> str:
    classification = exit_info.get("classification")
    if classification in {EXIT_NORMAL, EXIT_CONTROLLED}:
        return EXEC_SUCCESS
    text = "\n".join([stdout or "", stderr or ""])
    if TRANSIENT_TOOL_PATTERN.search(text):
        return EXEC_TOOL_TRANSIENT_FAILURE
    return EXEC_PRODUCT_FAILURE


def process_exists(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        if os.name == "nt":
            result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", f"Get-Process -Id {int(pid)} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id"], capture_output=True, text=True, timeout=10)
            return str(pid) in (result.stdout or "")
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def newest_unreal_saved_logs(executable: Path, started_epoch: float) -> list[str]:
    candidates: list[Path] = []
    roots = [executable.parents[2] / "Saved" / "Logs", executable.parent / "Saved" / "Logs"]
    for root in roots:
        if root.exists():
            candidates.extend(p for p in root.glob("*.log") if p.is_file() and p.stat().st_mtime >= started_epoch - 5)
    unique = sorted({p.resolve() for p in candidates}, key=lambda p: p.stat().st_mtime, reverse=True)
    return [str(p) for p in unique[:10]]


def run_unreal_process(
    args: list[str],
    cwd: Path,
    timeout: int,
    abslog: Path,
    expected_controlled_shutdown: bool = False,
    fallback_log_roots: list[Path] | None = None,
) -> dict[str, Any]:
    abslog = abslog.resolve()
    abslog.parent.mkdir(parents=True, exist_ok=True)
    if abslog.exists():
        abslog.unlink()
    command = [str(a) for a in args]
    if not any(str(a).lower().startswith("-abslog=") for a in command):
        command.append(f"-abslog={unreal_arg_path(abslog)}")
    started_monotonic = time.monotonic()
    started_epoch = time.time()
    started_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_epoch))
    pid: int | None = None
    timed_out = False
    stdout = ""
    stderr = ""
    exit_code: int | None = None
    try:
        proc = subprocess.Popen(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=foundry_subprocess_env())
        pid = proc.pid
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate(timeout=30)
            exit_code = proc.returncode
    except Exception as exc:
        stderr = f"{type(exc).__name__}: {exc}"
        exit_code = None
    ended_epoch = time.time()
    ended_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ended_epoch))
    requested_log_text = abslog.read_text(encoding="utf-8", errors="replace") if abslog.exists() else ""
    stdout_path = abslog.parent / "stdout.log"
    stderr_path = abslog.parent / "stderr.log"
    complete_log_path = abslog.parent / "complete-runtime.log"
    stdout_path.write_text(stdout or "", encoding="utf-8")
    stderr_path.write_text(stderr or "", encoding="utf-8")
    fallback_logs = []
    if fallback_log_roots:
        for root in fallback_log_roots:
            if root.exists():
                fallback_logs.extend(str(p) for p in root.glob("*.log") if p.is_file() and p.stat().st_mtime >= started_epoch - 5)
    combined = "\n".join(part for part in [requested_log_text, stdout or "", stderr or ""] if part)
    if not requested_log_text:
        for log in fallback_logs:
            try:
                combined += "\n" + Path(log).read_text(encoding="utf-8", errors="replace")
            except OSError:
                pass
    complete_log_path.write_text(combined, encoding="utf-8")
    log_status = "CREATED" if abslog.exists() else "LOG_PATH_NOT_CREATED"
    exit_info = classify_exit(exit_code, combined, timed_out=timed_out, expected_controlled_shutdown=expected_controlled_shutdown)
    process_tree_state = {"pid": pid, "running_after_capture": process_exists(pid)}
    return {
        "status": "PASS" if exit_info["classification"] in {EXIT_NORMAL, EXIT_CONTROLLED} else "FAIL",
        "execution_state": classify_execution_state(exit_info, stderr=stderr, stdout=stdout),
        "command": command,
        "cwd": str(cwd),
        "pid": pid,
        "start_time_utc": started_iso,
        "end_time_utc": ended_iso,
        "duration_seconds": round(time.monotonic() - started_monotonic, 3),
        "exit_code": exit_code,
        "exit_classification": exit_info,
        "process_tree_state": process_tree_state,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "complete_log_path": str(complete_log_path),
        "stdout_tail": (stdout or "")[-8000:],
        "stderr_tail": (stderr or "")[-8000:],
        "requested_log": str(abslog),
        "requested_log_exists": abslog.exists(),
        "requested_log_status": log_status,
        "fallback_logs": fallback_logs,
        "complete_log_text": combined,
        "text_tail": combined[-12000:],
        "timed_out": timed_out,
    }
