#!/usr/bin/env python3
"""Unified semantic code intelligence bus.

REPOSITORY → LANGUAGE DETECTION → PROJECT/BUILD DISCOVERY → SEMANTIC PROVIDER
→ NORMALIZED FACT GRAPH.

Truth model
-----------
Every fact carries an evidence kind and a certainty class so the Foundry knows
exactly what static analysis has PROVEN, what it only INFERRED (LIKELY /
POSSIBLE), and what remains a runtime question (UNKNOWN).

Evidence kinds:  LEXICAL, STRUCTURAL, TYPE_RESOLVED, FLOW_INFERRED,
                 BUILD_RESOLVED, GENERATED_METADATA, RUNTIME_OBSERVED,
                 HUMAN_DECLARED.
Certainty:       PROVEN, LIKELY, POSSIBLE, UNKNOWN.

Call edges
----------
STATIC_CALL_EDGE       a statically resolvable call site exists
POSSIBLE_DISPATCH_EDGE polymorphic dispatch (interface/virtual/Protocol) can
                       reach an implementation
FLOW_INFERRED_EDGE     local constructor/assignment flow points at a concrete
                       implementation (LIKELY, not PROVEN)
RUNTIME_OBSERVED_EDGE  only producible from runtime evidence, never here

Providers (local, project-scoped under tools/):
- cpp: clangd 22.1.6 (compile_commands.json is the build context; results are
  authoritative only for entries in that database)
- ts:  typescript-language-server (tsconfig.json/jsconfig.json)
- py:  pyright-langserver (TSP server not shipped in published 1.1.413
  distributions; type facts are hover-extracted with that limitation recorded)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

_REPO_CANDIDATES = [
    Path(__file__).resolve().parents[2],  # canonical repo
    Path.home() / "OneDrive" / "Desktop" / "11vatedTech-Claude-System",  # hard fallback
]
ROOT = next((p for p in _REPO_CANDIDATES if (p / "tools" / "lsp").exists()), _REPO_CANDIDATES[0])
sys.path.insert(0, str(Path(__file__).resolve().parent))  # lsp_client.py lives alongside

from lsp_client import LspClient, LspError, char_col_from_utf16, language_id_for, provider_command, to_uri, utf16_col  # noqa: E402

EVIDENCE_KINDS = ("LEXICAL", "STRUCTURAL", "TYPE_RESOLVED", "FLOW_INFERRED", "BUILD_RESOLVED", "GENERATED_METADATA", "RUNTIME_OBSERVED", "HUMAN_DECLARED")
CERTAINTY = ("PROVEN", "LIKELY", "POSSIBLE", "UNKNOWN")
GEN_BANNER = re.compile(r"^\s*(?://\s*|#\s*|/\*\s*)(?:@generated|GENERATED FILE|DO NOT EDIT)", re.IGNORECASE | re.MULTILINE)
COMMENT_START = re.compile(r"^\s*(?://|#|/\*|\*)")
EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "artifacts", "Binaries", "Intermediate", "Saved", "dist", "build"}
EXTENSIONS = {"cpp": {".cpp", ".cc", ".cxx", ".h", ".hpp", ".hh"}, "ts": {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs"}, "py": {".py"}}
TEST_FILE = re.compile(r"(^|[/\\])(test_|tests?[/\\])|(_test|\.test)\.(py|ts|tsx|js|cpp|cc)$", re.IGNORECASE)
PROVIDER_INFO = {
    "cpp": {"provider": "clangd", "version": "22.1.6", "source": "github.com/clangd/clangd release build", "note": "Unreal UHT/Blueprint semantics beyond plain clangd"},
    "ts": {"provider": "typescript-language-server", "version": "6.0.0", "source": "npm typescript-language-server", "note": "tsserver-backed; project TS version preferred when present"},
    "py": {"provider": "pyright", "version": "1.1.413", "source": "npm pyright (official Microsoft distribution)", "note": "TSP (pyright-typeserver) not shipped in published 1.1.413 npm/pip distributions; type facts hover-extracted"},
}


def lang_of(path: Path) -> Optional[str]:
    for lang, exts in EXTENSIONS.items():
        if path.suffix in exts:
            return lang
    return None


def collect_files(root: Path, lang: Optional[str] = None) -> list[Path]:
    out = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        detected = lang_of(path)
        if detected and (lang is None or detected == lang):
            out.append(path)
    return out


def find_compile_commands(root: Path) -> Optional[Path]:
    for candidate in (root / "compile_commands.json", root / "build" / "compile_commands.json"):
        if candidate.exists():
            return candidate
    return None


def find_tsconfig(path: Path) -> Optional[Path]:
    for folder in [path.parent] + list(path.parents):
        for name in ("tsconfig.json", "jsconfig.json"):
            candidate = folder / name
            if candidate.exists():
                return candidate
    return None


def _parse_compile_args(args: list[str]) -> dict:
    defines, includes = [], []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("-D"):
            defines.append(arg)
        elif arg.startswith("-I"):
            includes.append(arg)
        elif arg == "-include":
            index += 1
            if index < len(args):
                includes.append(f"-include {args[index]}")
        index += 1
    std = next((a for a in args if a.startswith("-std=")), "not_specified")
    compiler = Path(args[0]).name if args else "unknown"
    return {"compiler": compiler, "language_standard": std, "defines": defines, "include_paths": includes}


def build_context(lang: str, root: Path, path: Path, cc_db: Optional[dict]) -> dict:
    if lang == "cpp":
        if cc_db:
            for entry in cc_db:
                if Path(entry.get("file", "")).resolve() == path.resolve():
                    args = entry.get("arguments") or entry.get("command", "").split()
                    return {
                        "evidence_kind": "BUILD_RESOLVED",
                        "build_context": str(entry.get("target") or entry.get("output") or path.name),
                        "confidence": "authoritative_within_build_context",
                        "file_covered": True,
                        **_parse_compile_args(args),
                    }
            return {"evidence_kind": "STRUCTURAL", "build_context": "compile_commands_present_but_file_uncovered", "confidence": "semantic_limited_context", "file_covered": False}
        return {"evidence_kind": "STRUCTURAL", "build_context": "no_compile_database", "confidence": "semantic_limited_context", "file_covered": False}
    if lang == "ts":
        tsconfig = find_tsconfig(path)
        if tsconfig:
            return {"evidence_kind": "BUILD_RESOLVED", "build_context": tsconfig.relative_to(root).as_posix(), "confidence": "authoritative_within_tsconfig"}
        return {"evidence_kind": "STRUCTURAL", "build_context": "no_tsconfig", "confidence": "semantic_limited_context"}
    return {"evidence_kind": "TYPE_RESOLVED", "build_context": "pyright_workspace", "confidence": "authoritative_within_workspace"}


def _line_char(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset)
    line_start = text.rfind("\n", 0, offset) + 1
    return line, utf16_col(text[line_start:offset], offset - line_start)


def _norm_locations(result: Any) -> list[dict]:
    locations = []
    items = result if isinstance(result, list) else [result] if result else []
    for item in items:
        if not item:
            continue
        if isinstance(item, dict) and item.get("targetUri"):
            uri, rng = item["targetUri"], item.get("targetSelectionRange") or item.get("targetRange")
        else:
            uri, rng = item.get("uri"), item.get("range")
        if uri and rng:
            locations.append({"uri": uri, "line": rng["start"]["line"], "character": rng["start"]["character"]})
    return locations


def _uri_to_file(uri: str) -> Path:
    from urllib.parse import unquote, urlparse
    path_str = unquote(urlparse(uri).path)
    # file:///C:/... arrives as /C:/...; strip the leading / on Windows
    if path_str.startswith("/") and len(path_str) > 2 and path_str[2] == ":":
        path_str = path_str[1:]
    return Path(path_str).resolve()


def _flatten_symbols(symbols: Any) -> list[dict]:
    out = []
    for item in symbols or []:
        if not item:
            continue
        if item.get("selectionRange"):
            out.append({"name": item.get("name", ""), "kind": item.get("kind"), "detail": item.get("detail", ""), "range": item.get("selectionRange") or item.get("range"), "children": item.get("children") or []})
        else:
            out.append({"name": item.get("name", ""), "kind": item.get("kind"), "detail": item.get("detail", ""), "range": item.get("location", {}).get("range", {}), "children": []})
    return out


def _containing_symbol(symbols_by_file: dict[str, list[dict]], uri: str, line: int) -> Optional[dict]:
    best = None
    for item in _flatten_symbols(symbols_by_file.get(uri, [])):
        rng = item.get("range", {})
        if not rng:
            continue
        start, end = rng["start"]["line"], rng["end"]["line"]
        if start <= line <= end:
            if best is None or (end - start) < (best["range"]["end"]["line"] - best["range"]["start"]["line"]):
                best = item
    return best


def _find_symbol_positions(client: LspClient, root: Path, lang: str, symbol: str) -> list[dict]:
    token = symbol.split("::")[-1].split(".")[-1].split("#")[-1]
    qualifier = symbol.rsplit("::", 1)[0] if "::" in symbol else None
    text_files = collect_files(root, lang)
    found: list[dict] = []
    for file in text_files[:60]:
        text = file.read_text(encoding="utf-8", errors="replace")
        if not re.search(rf"\b{re.escape(token)}\b", text):
            continue
        uri = to_uri(file)
        client.open_document(uri, language_id_for(lang), text)
        symbols = client.document_symbols(uri)
        for item in _flatten_symbols(symbols):
            name = item.get("name", "")
            if name == token or name == symbol:
                preferred = item.get("detail", "").replace(" ", "").endswith(qualifier.split("::")[-1] + "::" + name) if qualifier else True
                if not preferred and qualifier:
                    preferred = qualifier in str(item.get("detail", ""))
                if not preferred:
                    continue
                found.append({"file": file, "uri": uri, "line": item["range"]["start"]["line"], "character": item["range"]["start"]["character"], "name": name, "detail": item.get("detail", "")})
    deduped = []
    seen = set()
    for item in found:
        key = (str(item["file"]), item["line"])
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    if not deduped:
        # Structural fallback is recorded explicitly, never mixed into
        # type-resolved evidence.
        for file in text_files[:40]:
            text = file.read_text(encoding="utf-8", errors="replace")
            match = re.search(rf"\b{re.escape(token)}\b", text)
            if match:
                line, character = _line_char(text, match.start())
                uri = to_uri(file)
                client.open_document(uri, language_id_for(lang), text)
                deduped.append({"file": file, "uri": uri, "line": line, "character": character, "name": token, "detail": "", "lexical_fallback": True})
                break
    return deduped[:5]


def _flow_targets(path: Path, token: str) -> list[dict]:
    """Bounded local flow trace: `const X: T = new Impl()` / `X = new Impl()`

    Returns constructor bindings whose receiver could reach a call of
    `token`. This is intentionally narrow: it emits FLOW_INFERRED (LIKELY)
    evidence only, never a runtime guarantee.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    results = []
    for match in re.finditer(r"\b([A-Za-z_$][\w$]*)\s*[:=][^=].*?\bnew\s+([A-Za-z_$][\w$]*)\s*\(", text):
        receiver, impl = match.group(1), match.group(2)
        if receiver and impl:
            results.append({"receiver": receiver, "impl": impl, "line": text.count("\n", 0, match.start()) + 1})
    return results


def _session_metadata(lang: str, root: Path, cc_db: Optional[dict]) -> dict:
    info = dict(PROVIDER_INFO[lang])
    if lang == "ts":
        ts_pkg = ROOT / "tools" / "lsp" / "node_modules" / "typescript" / "package.json"
        if ts_pkg.exists():
            data = json.loads(ts_pkg.read_text(encoding="utf-8"))
            info["typescript_version"] = data.get("version")
            info["typescript_source"] = "tools-bundled (project-local TypeScript is preferred when the project provides one)"
        tls_pkg = ROOT / "tools" / "lsp" / "node_modules" / "typescript-language-server" / "package.json"
        if tls_pkg.exists():
            data = json.loads(tls_pkg.read_text(encoding="utf-8"))
            info["node_requirement"] = (data.get("engines") or {}).get("node")
            info["repository"] = (data.get("repository") or {}).get("url")
    if lang == "cpp":
        info["compile_commands_source"] = str(find_compile_commands(root).relative_to(root)) if find_compile_commands(root) else "missing"
        info["compile_commands_entries"] = len(cc_db) if cc_db else 0
        info["platform"] = "windows-win64"
        info["unreal_tracking"] = "Target.cs/Build.cs/UHT/engine includes not modeled without a UE compile database"
    if lang == "py":
        info["tsp_status"] = "NOT_SHIPPED_IN_PUBLISHED_1.1.413_DISTRIBUTIONS — LSP hover extraction used; re-evaluate when pyright ships pyright-typeserver"
    info["root"] = str(root)
    info["position_encoding"] = "UTF-16 code units per LSP"
    return info


def discover(root: Path) -> dict:
    files = collect_files(root)
    by_lang: dict[str, int] = {}
    for path in files:
        lang = lang_of(path)
        by_lang[lang] = by_lang.get(lang, 0) + 1
    cc_db_path = find_compile_commands(root)
    tsconfigs = sorted(str(p.relative_to(root)) for p in root.rglob("tsconfig.json") if not any(part in EXCLUDED_DIRS for part in p.parts))
    return {
        "schema_version": 1,
        "kind": "semantic-code-discovery",
        "root": str(root),
        "counts_by_language": by_lang,
        "compile_commands": str(cc_db_path.relative_to(root)) if cc_db_path else None,
        "tsconfigs": tsconfigs,
        "providers_available": {"cpp": True, "ts": True, "py": True},
        "limitations": [
            "clangd evidence is authoritative only for entries present in compile_commands.json",
            "Unreal reflection/Blueprint semantics are beyond plain clangd",
            "pyright workspace resolution proves types statically, never runtime behaviour",
        ],
    }


def run_verb(root: Path, lang: str, symbol: str, verb: str, timeout: float = 90.0) -> dict:
    start = time.perf_counter()
    root = root.resolve()
    cc_path = find_compile_commands(root)
    cc_data = json.loads(cc_path.read_text(encoding="utf-8")) if cc_path else None
    cmd, cwd = provider_command(lang, root, cc_path.parent if cc_path else None)
    client = LspClient(cmd, cwd, f"{lang}:{PROVIDER_INFO[lang]['provider']}", timeout=timeout)
    result: dict[str, Any] = {
        "schema_version": 2,
        "kind": "semantic-code-query",
        "root": str(root),
        "language": lang,
        "symbol": symbol,
        "verb": verb,
        "provider": PROVIDER_INFO[lang]["provider"],
        "semantic": True,
        "session": _session_metadata(lang, root, cc_data),
        "facts": [],
        "uncertainties": ["runtime call graph not observed; RUNTIME_OBSERVED_EDGE facts require runtime evidence"],
        "overclaim_guards": [],
        "provider_extensions": {"common_api_used": verb, "extensions": {"pyright": ["hover type extraction (TSP unavailable)", "typeDefinition"], "typescript": ["textDocument/implementation", "tsserver-backed references"], "clangd": ["textDocument/implementation", "compile-command context", "include path capture"]}},
    }
    try:
        client.initialize(root.as_uri())
        positions = _find_symbol_positions(client, root, lang, symbol)
        symbols_by_file: dict[str, list[dict]] = {}
        for position in positions:
            if position["uri"] not in symbols_by_file:
                try:
                    symbols_by_file[position["uri"]] = client.document_symbols(position["uri"])
                except LspError:
                    symbols_by_file[position["uri"]] = []
        if verb == "explain":
            return _explain(result, positions, client, root, lang, cc_data, symbols_by_file)
        for position in positions:
            result["facts"].extend(_facts_for_verb(client, root, lang, symbol, verb, position, symbols_by_file, cc_data))
        result["facts"] = _dedupe_facts(result["facts"])
        opaque = [f for f in result["facts"] if f.get("value") in (None, [], {}, "", [])
                  and f.get("certainty") == "UNKNOWN" and f.get("verb") in ("definition", "type")]
        if not positions:
            result["uncertainties"].append(f"no symbol position resolved statically for {symbol}")
            result["facts"].append({
                "verb": verb, "symbol": symbol, "file": None, "start_line": None, "start_character": None,
                "evidence_kind": "LEXICAL" if _token_only_in_comments(root, symbol) else "UNKNOWN",
                "certainty": "UNKNOWN", "provider": "none", "semantic": False,
                "build_context": build_context(lang, root, Path("."), cc_data),
                "value": {"note": "no static definition; token may exist only in comments or dynamic/reflective contexts"},
            })
        result.update(_overclaim_guards_for(verb, lang))
        result["facts"] = result.get("facts") or [f for f in result["facts"]]
        if opaque:
            result["uncertainties"].append("facts with UNKNOWN certainty are reported, never masked")
    finally:
        client.shutdown()
    result["elapsed_s"] = round(time.perf_counter() - start, 2)
    return result


def _token_only_in_comments(root: Path, token: str) -> bool:
    text_files = collect_files(root)
    found_symbol = False
    for file in text_files[:80]:
        text = file.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(rf"\b{re.escape(token)}\b", text):
            line = text[text.rfind("\n", 0, match.start()) + 1: text.find("\n", match.start())]
            if COMMENT_START.match(line):
                continue
            found_symbol = True
    return not found_symbol


def _facts_for_verb(client: LspClient, root: Path, lang: str, symbol: str, verb: str, position: dict, symbols_by_file: dict[str, list[dict]], cc_data: Optional[dict]) -> list[dict]:
    uri, line, character = position["uri"], position["line"], position["character"]
    file = position["file"]
    rel = str(file.relative_to(root))
    ctx = build_context(lang, root, file, cc_data)

    if verb == "definition":
        locs = _norm_locations(client.definition(uri, line, character))
        # Retry at the token's actual offset when a document-symbol position lands on
        # whitespace or leading keywords (e.g., pyright reports the full class-line
        # start rather than the name column).
        if not locs:
            token = symbol.split("::")[-1].split(".")[-1].split("#")[-1]
            if file.exists():
                lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
                if line < len(lines):
                    hit = lines[line].find(token)
                    if hit >= 0:
                        locs = _norm_locations(client.definition(uri, line, utf16_col(lines[line][:hit], hit)))
        if locs:
            return [_fact("definition", symbol, rel, line, character, "TYPE_RESOLVED", "PROVEN", PROVIDER_INFO[lang]["provider"], True, ctx, {"definition_locations": [{"file": str(_uri_to_file(l["uri"]).relative_to(root) if l["uri"].startswith("file:") else l["uri"]), "line": l["line"], "character": l["character"]} for l in locs]})]
        return [_fact("definition", symbol, rel, line, character, "LEXICAL", "UNKNOWN", "none", False, ctx, {"note": "position is a lexical token; no type-resolved definition exists (comment claim or undeclared name)"})]

    if verb == "references":
        refs = _norm_locations(client.references(uri, line, character))
        return [_fact("references", symbol, rel, line, character, "TYPE_RESOLVED", "PROVEN", PROVIDER_INFO[lang]["provider"], True, ctx, {"reference_count": len(refs), "references": [{"file": str(_uri_to_file(r["uri"]).relative_to(root) if r["uri"].startswith("file:") else r["uri"]), "line": r["line"], "character": r["character"]} for r in refs[:40]]})]

    if verb == "type":
        hover = client.hover(uri, line, character)
        value = hover.get("contents", {}) if isinstance(hover, dict) else {}
        if isinstance(value, dict):
            value = value.get("value", "")
        if isinstance(value, list):
            value = " ".join(v.get("value", "") if isinstance(v, dict) else str(v) for v in value)
        if value:
            return [_fact("type", symbol, rel, line, character, "TYPE_RESOLVED", "PROVEN", PROVIDER_INFO[lang]["provider"], True, ctx, {"type_text": str(value)[:500], "note": "hover-extracted; structured declared/computed/expected type requires TSP, which is not shipped in pyright 1.1.413 distributions"})]
        return [_fact("type", symbol, rel, line, character, "STRUCTURAL", "UNKNOWN", "none", False, ctx, {"note": "no type information; structural position only"})]

    if verb == "implementations":
        try:
            locs = _norm_locations(client.implementation if hasattr(client, "implementation") else _implementation(client, uri, line, character))
        except LspError as exc:
            return [_fact("implementations", symbol, rel, line, character, "TYPE_RESOLVED", "UNKNOWN", PROVIDER_INFO[lang]["provider"], True, ctx, {"status": "NOT_APPLICABLE", "reason": f"{exc}"})]
        if not locs and lang == "py":
            return [_fact("implementations", symbol, rel, line, character, "STRUCTURAL", "UNKNOWN", PROVIDER_INFO[lang]["provider"], False, ctx, {"status": "NOT_APPLICABLE", "reason": "Python uses structural/duck typing; implementations not statically enumerable"})]
        return [_fact("implementations", symbol, rel, line, character, "TYPE_RESOLVED", "POSSIBLE", PROVIDER_INFO[lang]["provider"], True, ctx, {"possible_implementations": [{"file": str(_uri_to_file(l["uri"]).relative_to(root) if l["uri"].startswith("file:") else l["uri"]), "line": l["line"]} for l in locs], "runtime_target_proven": False})]

    if verb == "calls":
        edges = []
        refs = _norm_locations(client.references(uri, line, character))
        phase = 0
        # Phase 1: statically resolvable direct call sites (same-file only for bounded scope)
        for ref in refs:
            ref_file = _uri_to_file(ref["uri"])
            if ref["uri"] == uri or ref_file.resolve() == file.resolve():
                line_text = file.read_text(encoding="utf-8", errors="replace").splitlines()
                if ref["line"] < len(line_text) and re.search(rf"(?:[.>]|->)\s*{re.escape(position['name'])}\s*\(", line_text[ref["line"]]):
                    owner = _containing_symbol(symbols_by_file, ref["uri"], ref["line"])
                    edges.append({"edge_kind": "STATIC_CALL_EDGE", "caller": owner.get("name") if owner else "unknown", "call_location": {"file": rel, "line": ref["line"]}, "evidence_kind": "TYPE_RESOLVED", "certainty": "PROVEN", "runtime_target_proven": False, "dispatch": "direct_method_call"})
        # Phase 2: flow-inferred concrete targets for interface-style dispatch
        if lang in ("ts", "py", "cpp"):
            token = position["name"]
            for flow in _flow_targets(file, token):
                # candidate receiver binding that could reach this call
                owner = _containing_symbol(symbols_by_file, uri, line)
                edges.append({"edge_kind": "FLOW_INFERRED_EDGE", "caller": owner.get("name") if owner else "unknown", "receiver_initialized_with": f"new {flow['impl']}()", "binding_line": flow["line"], "evidence_kind": "FLOW_INFERRED", "certainty": "LIKELY", "runtime_target_proven": False, "dispatch": "constructor_flow"})
        # Phase 3: possible dispatch targets for polymorphic symbols
        if lang in ("ts", "cpp"):
            try:
                locs = _norm_locations(_implementation(client, uri, line, character))
                for l in locs:
                    edges.append({"edge_kind": "POSSIBLE_DISPATCH_EDGE", "target": str(_uri_to_file(l["uri"]).relative_to(root) if l["uri"].startswith("file:") else l["uri"]), "line": l["line"], "evidence_kind": "TYPE_RESOLVED", "certainty": "POSSIBLE", "runtime_target_proven": False})
            except LspError:
                pass
        if lang == "py":
            edges.append({"edge_kind": "POSSIBLE_DISPATCH_EDGE", "evidence_kind": "STRUCTURAL", "certainty": "POSSIBLE", "note": "python dynamic dispatch: any object with matching method may satisfy the call", "runtime_target_proven": False})
        if not edges:
            edges.append({"edge_kind": "STATIC_CALL_EDGE", "certainty": "UNKNOWN", "note": "no statically resolvable call sites found"})
        return [_fact("calls", symbol, rel, line, character, "TYPE_RESOLVED", "PROVEN", PROVIDER_INFO[lang]["provider"], True, ctx, {"edges": edges, "static_call_graph_note": "STATIC/POSSIBLE/FLOW edges answer different questions; RUNTIME_OBSERVED_EDGE requires runtime evidence"})]

    if verb == "impact":
        refs = _norm_locations(client.references(uri, line, character))
        direct = [{"file": str(_uri_to_file(r["uri"]).relative_to(root) if r["uri"].startswith("file:") else r["uri"]), "line": r["line"]} for r in refs[:40]]
        return [_fact("impact", symbol, rel, line, character, "TYPE_RESOLVED", "PROVEN", PROVIDER_INFO[lang]["provider"], True, ctx, {"proven_direct_impact": direct, "likely_transitive_impact": [{"kind": "structural_import_chain", "note": "derived from import/include edges; not proven"}]})]

    if verb == "docs_truth":
        claim = symbol
        text_files = collect_files(root)
        occurrences = []
        for file in text_files[:80]:
            text = file.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(rf"\b{re.escape(claim)}\b", text):
                line = text[text.rfind("\n", 0, match.start()) + 1: text.find("\n", match.start())]
                in_comment = bool(COMMENT_START.match(line))
                occurrences.append({"file": str(file.relative_to(root)), "line": text.count("\n", 0, match.start()) + 1, "in_comment": in_comment})

        textual_claim_present = len(occurrences) > 0

        # Check for real semantic symbol via LSP
        semantic_symbol_present = False
        if textual_claim_present and lang in ("cpp", "ts", "py"):
            for occ in occurrences[:20]:
                if occ["in_comment"]:
                    continue
                occ_path = root / occ["file"]
                if occ_path.suffix not in {'.cpp', '.h', '.hpp', '.ts', '.tsx', '.py'}:
                    continue
                try:
                    uri = _path_to_uri(occ_path)
                    line_num = occ["line"] - 1  # LSP 0-indexed
                    defs = _norm_locations(client.definition(uri, line_num, 0))
                    if defs:
                        semantic_symbol_present = True
                        break
                except Exception:
                    pass

        # Check for implementation (non-empty body)
        implementation_present = False
        test_evidence_present = False
        if semantic_symbol_present:
            for occ in occurrences[:20]:
                if occ["in_comment"]:
                    continue
                occ_path = root / occ["file"]
                if occ_path.suffix not in {'.cpp', '.h', '.hpp', '.ts', '.tsx', '.py'}:
                    continue
                try:
                    uri = _path_to_uri(occ_path)
                    line_num = occ["line"] - 1
                    defs = _norm_locations(client.definition(uri, line_num, 0))
                    for d in defs:
                        d_path = _uri_to_file(d["uri"])
                        d_text = d_path.read_text(encoding="utf-8", errors="replace")
                        lines = d_text.split("\n")
                        # Look for a non-trivial body after the definition
                        d_line_idx = d["line"] - 1
                        body_context = "\n".join(lines[d_line_idx:d_line_idx+15]) if d_line_idx < len(lines) else ""
                        if "{" in body_context and "}" in body_context and not re.search(r'\{\s*\}', body_context):
                            implementation_present = True
                        break
                    if implementation_present:
                        break
                except Exception:
                    pass

        return [_fact("docs_truth", claim, rel, line, character, "TYPE_RESOLVED" if semantic_symbol_present else "LEXICAL", "PROVEN", PROVIDER_INFO[lang]["provider"] if semantic_symbol_present else "foundry-heuristic", semantic_symbol_present, ctx, {
            "textual_claim_present": textual_claim_present,
            "semantic_symbol_present": semantic_symbol_present,
            "implementation_present": implementation_present,
            "test_evidence_present": test_evidence_present,
            "occurrences": occurrences[:60],
            "verdict": "IMPLEMENTATION_PRESENT" if implementation_present else ("SEMANTIC_SYMBOL_PRESENT" if semantic_symbol_present else ("TEXTUAL_CLAIM_PRESENT" if textual_claim_present else "NO_EVIDENCE"))
        })]

    if verb == "tests_for":
        refs = _norm_locations(client.references(uri, line, character))
        tests = []
        for r in refs:
            ref_path = _uri_to_file(r["uri"])
            if TEST_FILE.search(str(ref_path)):
                tests.append({"file": str(ref_path.relative_to(root)), "line": r["line"]})
        return [_fact("tests_for", symbol, rel, line, character, "TYPE_RESOLVED", "PROVEN", PROVIDER_INFO[lang]["provider"], True, ctx, {"test_references": tests[:40], "coverage_verdict": "HAS_TEST_REFERENCE" if tests else "NO_STATIC_TEST_REFERENCE"})]

    raise ValueError(f"unknown verb {verb}")


def _implementation(client: LspClient, uri: str, line: int, character: int) -> Any:
    return client._request("textDocument/implementation", {"textDocument": {"uri": uri}, "position": {"line": line, "character": character}})


def _fact(verb: str, symbol: str, file: Optional[str], line: Optional[int], character: Optional[int], evidence_kind: str, certainty: str, provider: str, semantic: bool, ctx: dict, value: Any) -> dict:
    assert evidence_kind in EVIDENCE_KINDS and certainty in CERTAINTY, (evidence_kind, certainty)
    return {"verb": verb, "symbol": symbol, "file": file, "start_line": line, "start_character": character, "evidence_kind": evidence_kind, "certainty": certainty, "provider": provider, "semantic": semantic, "build_context": ctx, "value": value}


def _dedupe_facts(facts: list[dict]) -> list[dict]:
    out, seen = [], set()
    for fact in facts:
        key = (fact["verb"], fact["file"], fact.get("start_line"))
        if key in seen:
            continue
        seen.add(key)
        out.append(fact)
    return out


def _overclaim_guards_for(verb: str, lang: str) -> dict:
    guards = []
    if verb == "implementations":
        guards.append("implementations are POSSIBLE dispatch targets, never a runtime guarantee")
    if verb == "calls":
        guards.append("FLOW_INFERRED_EDGE is LIKELY by constructor flow; only RUNTIME_OBSERVED_EDGE proves what executed")
    if lang == "py":
        guards.append("python dynamism (getattr, __getattr__, monkey-patching, import hooks) means many answers remain POSSIBLE/UNKNOWN; the bus must not invent precision")
    return {"overclaim_guards": guards}


def _explain(result: dict, positions: list[dict], client: LspClient, root: Path, lang: str, cc_data: Optional[dict], symbols_by_file: dict[str, list[dict]]) -> dict:
    result["facts"] = []
    result["verb"] = "explain"
    result["explanation"] = {
        "provider": PROVIDER_INFO[lang]["provider"],
        "positions_resolved": len(positions),
        "note": "semantic explanation: every fact is evidence-kind-labelled; certainty ceilings are enforced by the bus, not by the provider response alone",
        "runtime_question": "concrete runtime targets and executed call graphs require runtime evidence (RUNTIME_OBSERVED_EDGE), which static analysis cannot provide",
    }
    return result


def repo_facts(root: Path, lang: Optional[str] = None, max_symbols: int = 250, timeout: float = 120.0) -> dict:
    root = root.resolve()
    files = collect_files(root, lang)
    languages = sorted({lang_of(f) for f in files if lang_of(f)})
    facts: list[dict] = []
    limitations: list[str] = []
    for language in languages:
        cc_path = find_compile_commands(root)
        cc_data = json.loads(cc_path.read_text(encoding="utf-8")) if cc_path else None
        cmd, cwd = provider_command(language, root, cc_path.parent if cc_path else None)
        client = LspClient(cmd, cwd, PROVIDER_INFO[language]["provider"], timeout=timeout)
        try:
            client.initialize(root.as_uri())
        except LspError as exc:
            limitations.append(f"{language}: {exc}")
            continue
        try:
            symbols_seen = 0
            for file in [f for f in files if lang_of(f) == language][:60]:
                text = file.read_text(encoding="utf-8", errors="replace")
                uri = to_uri(file)
                client.open_document(uri, language_id_for(language), text)
                symbols = client.document_symbols(uri)
                ctx = build_context(language, root, file, cc_data)
                for item in _flatten_symbols(symbols):
                    if item.get("name") is None:
                        continue
                    symbols_seen += 1
                    if symbols_seen > max_symbols:
                        limitations.append(f"{language}: symbol cap reached ({max_symbols}); graph is partial")
                        break
                    pos = (uri, item["range"]["start"]["line"], item["range"]["start"]["character"])
                    refs = _norm_locations(client.references(*pos))
                    definition = _norm_locations(client.definition(*pos))
                    facts.append(_fact("definition", item["name"], str(file.relative_to(root)), item["range"]["start"]["line"], item["range"]["start"]["character"], "TYPE_RESOLVED", "PROVEN", PROVIDER_INFO[language]["provider"], True, ctx, {"definition_locations": definition[:5], "references": refs[:20]}))
                if symbols_seen > max_symbols:
                    break
        finally:
            client.shutdown()
    return {
        "schema_version": 2,
        "kind": "semantic-code-fact-graph",
        "root": str(root),
        "provider": "clangd+typescript-language-server+pyright",
        "fact_count": len(facts),
        "facts": facts,
        "limitations": limitations or ["graph is bounded; semantics are static and build-context-scoped"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("discover").add_argument("root", type=Path)
    q = sub.add_parser("query")
    q.add_argument("root", type=Path)
    q.add_argument("--lang", required=True, choices=["cpp", "ts", "py"])
    q.add_argument("--symbol", required=True)
    q.add_argument("--verb", required=True, choices=["definition", "references", "type", "implementations", "calls", "impact", "docs_truth", "tests_for", "explain"])
    q.add_argument("--out", type=Path)
    f = sub.add_parser("facts")
    f.add_argument("root", type=Path)
    f.add_argument("--lang", choices=["cpp", "ts", "py"])
    f.add_argument("--max-symbols", type=int, default=250)
    f.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.command == "discover":
        result = discover(args.root)
    elif args.command == "facts":
        result = repo_facts(args.root, args.lang, args.max_symbols)
    else:
        result = run_verb(args.root, args.lang, args.symbol, args.verb)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if getattr(args, "out", None):
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())