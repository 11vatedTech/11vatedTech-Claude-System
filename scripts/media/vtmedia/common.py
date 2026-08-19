from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_ROOT = ROOT / "artifacts" / "creative-stack-validation"
CONFIG_PATH = ROOT / "config" / "creative-toolchain.json"


def now_slug() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> Path:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def which(name: str) -> str | None:
    return shutil.which(name)


def run(argv: list[str], timeout: int = 60, cwd: Path | None = None) -> dict[str, Any]:
    started = time.time()
    try:
        p = subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {
            "argv": argv,
            "returncode": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "elapsed_seconds": round(time.time() - started, 3),
        }
    except Exception as exc:
        return {"argv": argv, "error": type(exc).__name__ + ": " + str(exc), "elapsed_seconds": round(time.time() - started, 3)}


def run_shell(command: str, timeout: int = 60) -> dict[str, Any]:
    started = time.time()
    try:
        p = subprocess.run(command, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return {"command": command, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "elapsed_seconds": round(time.time() - started, 3)}
    except Exception as exc:
        return {"command": command, "error": type(exc).__name__ + ": " + str(exc), "elapsed_seconds": round(time.time() - started, 3)}


def command_summary(result: dict[str, Any], limit: int = 1200) -> dict[str, Any]:
    out = dict(result)
    for key in ("stdout", "stderr"):
        if key in out and isinstance(out[key], str) and len(out[key]) > limit:
            out[key] = out[key][:limit] + "...[truncated]"
    return out


def file_record(path: Path, role: str = "artifact", license: str = "generated-local") -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
        "role": role,
        "license": license,
    }


def system_base() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cwd": os.getcwd(),
    }
