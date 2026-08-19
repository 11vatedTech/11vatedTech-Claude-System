from __future__ import annotations

import time
from pathlib import Path
from typing import Any
from .common import file_record, write_json


def manifest(job_id: str, intent: str, outputs: list[Path], inputs: list[Path] | None = None, toolchain: list[dict[str, Any]] | None = None, generation: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "job_id": job_id,
        "created_at_local": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "intent": intent,
        "cost_policy": "free_local_default_no_paid_generation",
        "inputs": [file_record(p, role="input") for p in (inputs or [])],
        "outputs": [file_record(p, role="output") for p in outputs],
        "toolchain": toolchain or [],
        "generation": generation or {"used_ai": False},
        "validation": {"passed": all(p.exists() for p in outputs), "checks": []},
    }


def write_manifest(path: Path, data: dict[str, Any]) -> Path:
    return write_json(path, data)
