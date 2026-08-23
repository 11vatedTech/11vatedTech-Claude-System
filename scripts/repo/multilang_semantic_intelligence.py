#!/usr/bin/env python3
"""Lightweight multi-language repository intelligence.

Indexes definitions, imports/includes, and lexical references for common
11vatedTech languages without claiming type-resolved LSP semantics. It is a
portable baseline that can later be upgraded per language when a language
server/compiler database is available.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

EXCLUDED = {".git", "node_modules", "__pycache__", ".venv", "artifacts", "Binaries", "Intermediate", "Saved"}
EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".cpp", ".cc", ".c", ".h", ".hpp"}


def language(path: Path) -> str:
    if path.suffix == ".py":
        return "python"
    if path.suffix in {".ts", ".tsx", ".js", ".jsx"}:
        return "typescript-javascript"
    return "cpp"


def add_symbol(out: list[dict], name: str, kind: str, line: int, language_name: str) -> None:
    if name:
        out.append({"name": name, "kind": kind, "line": line, "language": language_name})


def parse_python(text: str, record: dict) -> None:
    try:
        tree = ast.parse(text, filename=record["path"])
    except SyntaxError as exc:
        record["parse_error"] = f"line {exc.lineno}: {exc.msg}"
        return
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            add_symbol(record["symbols"], node.name, "function", node.lineno, "python")
        elif isinstance(node, ast.ClassDef):
            add_symbol(record["symbols"], node.name, "class", node.lineno, "python")
        elif isinstance(node, ast.Import):
            record["imports"].extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            record["imports"].append(node.module)


def parse_regex(text: str, record: dict, lang: str) -> None:
    if lang == "typescript-javascript":
        patterns = [
            (r"\b(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", "function"),
            (r"\b(?:export\s+)?class\s+([A-Za-z_$][\w$]*)", "class"),
            (r"\b(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^\n]*\)\s*=>", "function"),
        ]
        imports = re.findall(r"\bimport\s+(?:[^;\n]+?\s+from\s+)?[\"']([^\"']+)[\"']|\brequire\(\s*[\"']([^\"']+)[\"']\s*\)", text)
        record["imports"].extend(next((value for value in pair if value), "") for pair in imports)
    else:
        patterns = [
            (r"\b(?:class|struct)\s+([A-Za-z_]\w*)", "class"),
            (r"\b(?:UCLASS|USTRUCT|UENUM)\b[^\n]*\n\s*(?:class|struct|enum)\s+([A-Za-z_]\w*)", "type"),
            (r"\b(?:[A-Za-z_]\w*[&*]?\s+)+([A-Za-z_]\w*)\s*\([^;{}\n]*\)\s*(?:const\s*)?\{", "function"),
        ]
        record["imports"].extend(re.findall(r"#include\s*[<\"]([^>\"]+)[>\"]", text))
    for pattern, kind in patterns:
        for match in re.finditer(pattern, text):
            line = text.count("\n", 0, match.start()) + 1
            add_symbol(record["symbols"], match.group(1), kind, line, lang)


def index_tree(root: Path) -> dict:
    root = root.resolve()
    files: dict[str, dict] = {}
    parse_errors = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in EXTENSIONS or any(part in EXCLUDED for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        lang = language(path)
        record = {"path": rel, "language": lang, "symbols": [], "references": [], "imports": [], "lines": len(text.splitlines())}
        if lang == "python":
            parse_python(text, record)
        else:
            parse_regex(text, record, lang)
        for symbol in record["symbols"]:
            record["references"].append({"name": symbol["name"], "line": symbol["line"], "kind": "definition"})
        defined_names = {symbol["name"] for symbol in record["symbols"]}
        tokens = re.findall(r"\b[A-Za-z_$][\w$]*\b", text)
        for name in sorted(set(tokens) - defined_names):
            count = len(re.findall(rf"\b{re.escape(name)}\b", text))
            if count > 1:
                record["references"].append({"name": name, "occurrences": count, "kind": "lexical"})
        files[rel] = record
        if record.get("parse_error"):
            parse_errors.append({"path": rel, "error": record["parse_error"]})
    edges = []
    known_stems = {Path(rel).stem for rel in files}
    for record in files.values():
        for imported in sorted(set(record["imports"])):
            stem = Path(imported).stem
            if stem in known_stems:
                edges.append({"from": record["path"], "import": imported, "to_stem": stem})
    return {
        "schema_version": 1,
        "kind": "multilang-semantic-repository-index",
        "root": str(root),
        "languages": sorted({record["language"] for record in files.values()}),
        "file_count": len(files),
        "symbol_count": sum(len(record["symbols"]) for record in files.values()),
        "files": files,
        "dependency_edges": edges,
        "parse_errors": parse_errors,
        "limitations": [
            "regex extraction for TypeScript/JavaScript/C++ is lexical, not parser- or type-resolved",
            "Python imports are recorded but dynamic imports and runtime wiring remain unknown",
            "use LSP/compiler databases for authoritative type, overload, macro, and generated-code queries"
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    doc = index_tree(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: doc[k] for k in ("languages", "file_count", "symbol_count", "parse_errors")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
