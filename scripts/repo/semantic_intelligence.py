#!/usr/bin/env python3
"""Semantic repository intelligence using Python's standard AST.

This is intentionally a real semantic layer above grep, not an LSP claim. It
indexes definitions, references, imports, and source evidence, then exposes
controlled queries for architecture, symbol tracing, impact, and requirement
coverage. Unsupported languages and parse failures remain explicit.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from pathlib import Path

EXCLUDED = {".git", "node_modules", "__pycache__", ".venv", "artifacts"}


def module_name(path: Path, root: Path) -> str:
    rel = path.relative_to(root).with_suffix("")
    return ".".join(rel.parts)


def index_tree(root: Path) -> dict:
    root = root.resolve()
    files, parse_errors = {}, []
    for path in sorted(root.rglob("*.py")):
        if any(part in EXCLUDED for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        record = {"path": rel, "module": module_name(path, root), "symbols": [], "references": [], "imports": [], "lines": len(text.splitlines())}
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError as exc:
            record["parse_error"] = f"line {exc.lineno}: {exc.msg}"
            parse_errors.append({"path": rel, "error": record["parse_error"]})
            files[rel] = record
            continue
        class Visitor(ast.NodeVisitor):
            def __init__(self): self.scope = []
            def visit_FunctionDef(self, node):
                q = ".".join([record["module"], *self.scope, node.name])
                record["symbols"].append({"name": node.name, "qualified": q, "kind": "function", "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno)})
                self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
            visit_AsyncFunctionDef = visit_FunctionDef
            def visit_ClassDef(self, node):
                q = ".".join([record["module"], *self.scope, node.name])
                record["symbols"].append({"name": node.name, "qualified": q, "kind": "class", "line": node.lineno, "end_line": getattr(node, "end_lineno", node.lineno)})
                self.scope.append(node.name); self.generic_visit(node); self.scope.pop()
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Load): record["references"].append({"name": node.id, "line": node.lineno})
                self.generic_visit(node)
            def visit_Import(self, node):
                record["imports"].extend(alias.name for alias in node.names); self.generic_visit(node)
            def visit_ImportFrom(self, node):
                if node.module: record["imports"].append(node.module); record["imports"].extend(f"{node.module}.{a.name}" for a in node.names)
                self.generic_visit(node)
        Visitor().visit(tree)
        files[rel] = record
    all_symbols = [s for f in files.values() for s in f["symbols"]]
    return {"schema_version": 1, "root": str(root), "language": "python-ast", "file_count": len(files), "symbol_count": len(all_symbols), "files": files, "parse_errors": parse_errors}


def load(index: Path) -> dict:
    return json.loads(index.read_text(encoding="utf-8"))


def symbols(doc: dict, query: str) -> list[dict]:
    out = []
    for file in doc.get("files", {}).values():
        for symbol in file.get("symbols", []):
            if query.lower() in symbol["name"].lower() or query.lower() in symbol["qualified"].lower():
                out.append({"file": file["path"], **symbol})
    return out


def references(doc: dict, query: str) -> list[dict]:
    return [{"file": f["path"], **ref} for f in doc.get("files", {}).values() for ref in f.get("references", []) if ref["name"] == query]


def architecture(doc: dict) -> dict:
    modules = []
    edges = []
    known = {f["module"] for f in doc.get("files", {}).values()}
    for f in doc.get("files", {}).values():
        modules.append({"module": f["module"], "file": f["path"], "symbols": len(f.get("symbols", []))})
        for imported in sorted(set(f.get("imports", []))):
            target = imported if imported in known else ".".join(imported.split(".")[:2])
            if target in known and target != f["module"]: edges.append({"from": f["module"], "to": target})
    return {"modules": modules, "edges": edges}


def requirement(doc: dict, query: str) -> dict:
    terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", query) if len(t) > 2]
    hits = []
    root = Path(doc["root"])
    for file in doc.get("files", {}).values():
        text = (root / file["path"]).read_text(encoding="utf-8", errors="replace").lower()
        score = sum(text.count(term) for term in terms)
        if score: hits.append({"file": file["path"], "score": score, "symbols": file.get("symbols", [])})
    return {"query": query, "terms": terms, "hits": sorted(hits, key=lambda x: (-x["score"], x["file"]))}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("index"); p.add_argument("root", type=Path); p.add_argument("--out", type=Path, required=True)
    for name in ("symbol", "references", "architecture", "impact", "requirement"):
        p = sub.add_parser(name); p.add_argument("index", type=Path); p.add_argument("query", nargs="?")
    args = parser.parse_args()
    if args.command == "index":
        doc = index_tree(args.root); args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(doc, indent=2), encoding="utf-8"); print(json.dumps({k: doc[k] for k in ("file_count", "symbol_count", "parse_errors")}, indent=2)); return 0
    doc = load(args.index)
    if args.command == "symbol": result = {"query": args.query, "definitions": symbols(doc, args.query or "")}
    elif args.command == "references": result = {"query": args.query, "references": references(doc, args.query or "")}
    elif args.command == "architecture": result = architecture(doc)
    elif args.command == "requirement": result = requirement(doc, args.query or "")
    else:
        defs = symbols(doc, args.query or ""); result = {"query": args.query, "definitions": defs, "references": references(doc, defs[0]["name"] if defs else args.query or "")}
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
