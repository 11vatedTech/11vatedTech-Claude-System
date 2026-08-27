#!/usr/bin/env python3
"""Verify physical global installation hashes for KAPIF reusable modules."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GLOBAL = Path.home() / ".claude" / "11vatedtech" / "capability-system"
RELATIVE = [
    "scripts/kapif/__init__.py", "scripts/kapif/data_layer.py", "scripts/kapif/db.py",
    "scripts/kapif/fts_index.py", "scripts/kapif/embeddings.py", "scripts/kapif/hybrid_retrieval.py",
    "scripts/kapif/professional_extractor.py", "scripts/kapif/llm_extractor.py",
    "scripts/kapif/model_intelligence.py", "scripts/kapif/model_tournaments.py",
    "scripts/kapif/visual_intelligence.py", "scripts/kapif/canon_pipeline.py",
    "scripts/kapif/security.py", "scripts/kapif/mission_compiler.py",
    "config/foundry-failure-patterns.json", "config/M002-truth-correction.json",
]


def sha(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run() -> dict[str, Any]:
    rows = []
    for rel in RELATIVE:
        source = ROOT / rel
        installed = GLOBAL / rel
        source_hash = sha(source)
        installed_hash = sha(installed)
        rows.append({"relative": rel, "source": str(source), "installed": str(installed),
                     "source_sha256": source_hash, "installed_sha256": installed_hash,
                     "match": bool(source_hash and source_hash == installed_hash)})
    result = {"schema_version": 1, "kind": "kapif-global-hash-proof",
              "global_root": str(GLOBAL), "status": "PASS" if all(r["match"] for r in rows) else "FAIL",
              "files": rows}
    out = ROOT / "artifacts" / "kapif" / "m002.1" / "global-hash-proof.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
