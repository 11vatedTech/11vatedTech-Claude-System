#!/usr/bin/env python3
"""Golden tasks for the dependency-free semantic repository index."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "repo"))
from semantic_intelligence import architecture, index_tree, references, requirement, symbols  # type: ignore


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "fixture"
        (root / "app").mkdir(parents=True)
        (root / "tests").mkdir()
        (root / "app/core.py").write_text('''def parse_manifest(text):\n    """Parse the product manifest contract."""\n    return text.strip()\n''', encoding="utf-8")
        (root / "app/api.py").write_text('''from app.core import parse_manifest\n\ndef create_product(raw):\n    return parse_manifest(raw)\n''', encoding="utf-8")
        (root / "tests/test_api.py").write_text('''from app.api import create_product\n\ndef test_manifest_contract():\n    assert create_product(" product ") == "product"\n''', encoding="utf-8")
        doc = index_tree(root)
        checks = {}
        checks["definition_trace"] = any(x["file"] == "app/core.py" and x["name"] == "parse_manifest" for x in symbols(doc, "parse_manifest"))
        refs = references(doc, "parse_manifest")
        checks["reference_trace"] = {r["file"] for r in refs} == {"app/api.py"}
        arch = architecture(doc)
        checks["architecture_edge"] = {tuple((e["from"], e["to"])) for e in arch["edges"]} >= {("app.api", "app.core")}
        impact = {r["file"] for r in references(doc, "create_product")}
        checks["impact_trace"] = "tests/test_api.py" in impact
        checks["requirement_trace"] = any(h["file"] == "app/core.py" for h in requirement(doc, "manifest contract")["hits"])
        checks["parse_errors_explicit"] = doc["parse_errors"] == [] and doc["file_count"] == 3
        result = {"schema_version": 1, "task": "python_ast_repository_intelligence", "checks": checks, "ok": all(checks.values()), "limitations": ["Python only", "name references are lexical AST references, not type-resolved LSP references", "dynamic imports and generated code remain unknown"]}
        out = ROOT / "artifacts" / "repository-intelligence" / "semantic-golden-tasks.json"
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("REPO_SEMANTIC_GOLDEN", "PASS" if result["ok"] else "FAIL", checks)
        return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
