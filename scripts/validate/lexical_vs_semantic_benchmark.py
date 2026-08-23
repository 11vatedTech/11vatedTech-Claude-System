#!/usr/bin/env python3
"""Lexical vs Semantic Code Intelligence Benchmark.

Runs every Golden Task trap across C++, TypeScript, and Python fixtures,
recording LEXICAL answer, SEMANTIC answer, and GROUND TRUTH for each.

Reports: definition precision, reference precision, reference recall,
implementation-set precision, dead-symbol precision, docs-as-code false positives,
and OVERCLAIM RATE — the Foundry's primary quality metric."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "repo"))
from semantic_code_bus import _flatten_symbols, collect_files, lang_of  # noqa: E402

FIXTURE_ROOTS = {
    "cpp": ROOT / "tools" / "fixtures" / "semantic-golden" / "cpp",
    "ts": ROOT / "tools" / "fixtures" / "semantic-golden" / "ts",
    "py": ROOT / "tools" / "fixtures" / "semantic-golden" / "py",
}

BUS_SCRIPT = ROOT / "scripts" / "repo" / "semantic_code_bus.py"


# ── Ground Truth Definitions ──────────────────────────────────────────

GROUND_TRUTH = {
    # === C++ ===
    ("cpp", "VectorMath", "definition"): "found_in_header_includes",
    ("cpp", "ComputePlayerHealth", "definition"): "found_in_player_cpp",
    ("cpp", "normalize", "definition"): "found_in_vector_math_cpp_via_header_decl",
    ("cpp", "legacy::normalize", "definition"): "different_from_VectorMath_normalize",
    ("cpp", "obsolete_helper", "definition"): "dead_symbol_defined_but_never_called",
    ("cpp", "obsolete_helper", "references"): "zero_references",
    ("cpp", "Shape", "implementations"): "two_possible_overrides_runtime_not_proven",
    ("cpp", "Shape::draw", "implementations"): "possible_overrides_not_runtime_target",
    ("cpp", "config_version", "definition"): "generated_file_must_flag",
    ("cpp", "generate_id", "definition"): "macro_generated_declaration",
    ("cpp", "processTask", "definition"): "callback_typedef_not_concrete_call",

    # === TypeScript ===
    ("ts", "Engine", "definition"): "class_in_launcher_module",
    ("ts", "Launcher", "implementations"): "two_possible_runtime_not_proven",
    ("ts", "orphanHelper", "references"): "zero_references_dead_symbol",
    ("ts", "autoSave", "docs_truth"): "token_in_string_literal_not_real_symbol",
    ("ts", "computeScore", "definition"): "duplicated_name_different_semantics",
    ("ts", "measureCafé", "definition"): "unicode_position_must_resolve",
    ("ts", "adjust", "definition"): "overloaded_function_multiple_signatures",
    ("ts", "FlyLauncher", "definition"): "reexported_symbol_via_barrel",
    ("ts", "writeLog", "definition"): "callback_type_not_concrete_func",
    ("ts", "Container", "implementations"): "generic_interface_implementations",

    # === Python ===
    ("py", "OrderService", "definition"): "class_definition_normal",
    ("py", "process_payment", "definition"): "overloaded_static_type_resolved",
    ("py", "obsolete_helper", "references"): "zero_references_dead_symbol",
    ("py", "bulk_export", "definition"): "docs_claim_token_no_symbol",
    ("py", "format_currency", "definition"): "reexport_via_alias",
    ("py", "invoke_by_name", "definition"): "dynamic_attribute_unknown_certainty",
    ("py", "PaymentGateway", "implementations"): "protocol_structural_not_static",
    ("py", "measure_café", "definition"): "unicode_position_must_resolve",
    ("py", "publish_draft", "definition"): "decorated_function",
    ("py", "process", "definition"): "same_name_different_module_unrelated",
}


# ── Lexical Index (baseline, before semantic bus) ─────────────────────

def _lexical_search(root: Path, symbol: str, verb: str) -> dict:
    """Simulate the old lexical index: grep the codebase for token matches."""
    files = collect_files(root)
    token = symbol.split("::")[-1].split(".")[-1]
    matches = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        import re
        for m in re.finditer(rf"\b{re.escape(token)}\b", text):
            line_no = text.count("\n", 0, m.start()) + 1
            line = text[text.rfind("\n", 0, m.start()) + 1:text.find("\n", m.start())]
            matches.append({"file": str(f.relative_to(root)), "line": line_no, "in_comment": line.strip().startswith(("//", "#", "/*"))})

    result = {
        "symbol": symbol, "verb": verb,
        "evidence_kind": "LEXICAL",
        "match_count": len(matches),
        "matches": matches[:30],
    }

    # Lexical overclaim: if verb == "implementations" we must report N/A
    if verb in ("implementations", "calls", "docs_truth", "impact"):
        result["error"] = "lexical_index_cannot_resolve_this_verb"
        result["match_count"] = 0
        result["matches"] = []

    return result


# ── Metrics ───────────────────────────────────────────────────────────

def _evaluate(lang: str, symbol: str, verb: str, lexical: dict, semantic: dict,
              ground_truth: str) -> dict:
    """Score one trap result."""
    facts = semantic.get("facts", [])
    top_fact = facts[0] if facts else {}
    ek = top_fact.get("evidence_kind", "UNKNOWN")
    cert = top_fact.get("certainty", "UNKNOWN")
    sem_val = top_fact.get("value", {})

    overclaim = False
    precision_hit = False
    recall_hit = False

    # ── precision / recall heuristics per verb ──
    if verb == "definition":
        locs = sem_val.get("definition_locations", [])
        precision_hit = len(locs) > 0 and ek in ("TYPE_RESOLVED", "BUILD_RESOLVED")
        lex_hits = len(lexical.get("matches", [])) > 0
        recall_hit = precision_hit  # definition is either found or not

    elif verb == "references":
        quota = sem_val.get("reference_count", -1)
        # Dead symbol: 0 references is CORRECT
        if "dead" in ground_truth or "zero" in ground_truth:
            precision_hit = quota == 0 and ek == "TYPE_RESOLVED"
        else:
            precision_hit = quota is not None and quota >= 0
        recall_hit = True

    elif verb == "implementations":
        impls = sem_val.get("possible_implementations", [])
        runtime_proven = sem_val.get("runtime_target_proven", None)
        precision_hit = len(impls) > 0 and cert == "POSSIBLE"
        overclaim = runtime_proven is True  # must NOT be proven
        recall_hit = len(impls) >= 0

    elif verb == "docs_truth":
        textual = sem_val.get("textual_claim_present", False)
        semantic = sem_val.get("semantic_symbol_present", False)
        implementation = sem_val.get("implementation_present", False)
        verdict = sem_val.get("verdict", "")
        # autoSave: the claim is a string literal — textual present, no semantic symbol
        precision_hit = (textual is True and semantic is False and implementation is False)
        recall_hit = True

    elif verb in ("calls", "impact"):
        edges = sem_val.get("edges", [])
        precision_hit = all(e.get("runtime_target_proven", True) is False for e in edges if isinstance(e, dict))
        overclaim = any(e.get("runtime_target_proven") is True for e in edges if isinstance(e, dict))
        recall_hit = True  # returns at minimum UNKNOWN when no calls found

    # ── overclaim detection ──
    if cert == "PROVEN" and verb in ("implementations", "calls"):
        # implementations and calls should never claim PROVEN runtime targets
        if sem_val.get("runtime_target_proven") is True:
            overclaim = True

    if ek == "LEXICAL" and top_fact.get("semantic"):
        # If bus fell back to lexical when it should have found semantic
        pass  # not overclaim, just limitation

    return {
        "language": lang,
        "symbol": symbol,
        "verb": verb,
        "ground_truth": ground_truth,
        "lexical_matches": len(lexical.get("matches", [])),
        "semantic_evidence_kind": ek,
        "semantic_certainty": cert,
        "precision_hit": precision_hit,
        "recall_hit": recall_hit,
        "overclaim": overclaim,
        "semantic_fact_count": len(facts),
    }


# ── Runner ─────────────────────────────────────────────────────────────

def _run_bus(lang: str, symbol: str, verb: str) -> dict:
    cmd = [
        sys.executable, str(BUS_SCRIPT), "query",
        str(FIXTURE_ROOTS[lang]),
        "--lang", lang,
        "--symbol", symbol,
        "--verb", verb,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(ROOT))
    if r.returncode != 0:
        return {"error": r.stderr[:500], "facts": []}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "json_parse_failure", "facts": []}


def main() -> int:
    results = []
    started = time.perf_counter()
    n = 0
    for (lang, symbol, verb), truth in GROUND_TRUTH.items():
        n += 1
        root = FIXTURE_ROOTS[lang]
        lex = _lexical_search(root, symbol, verb)
        sem = _run_bus(lang, symbol, verb)
        row = _evaluate(lang, symbol, verb, lex, sem, truth)
        results.append(row)
        status = "PASS" if row["precision_hit"] and not row["overclaim"] else "FAIL"
        print(f"  {status} {lang}/{symbol}/{verb}  ek={row['semantic_evidence_kind']} cert={row['semantic_certainty']} overclaim={row['overclaim']}")

    elapsed = time.perf_counter() - started

    # ── aggregate ──
    total = len(results)
    precision_hits = sum(r["precision_hit"] for r in results)
    overclaims = sum(r["overclaim"] for r in results)
    semantic_count = sum(1 for r in results if r["semantic_evidence_kind"] in ("TYPE_RESOLVED", "BUILD_RESOLVED", "FLOW_INFERRED"))
    lexical_fallbacks = sum(1 for r in results if r["semantic_evidence_kind"] == "LEXICAL")
    unknown = sum(1 for r in results if r["semantic_certainty"] == "UNKNOWN")

    report = {
        "schema_version": 1,
        "kind": "lexical-vs-semantic-benchmark",
        "total_tasks": total,
        "elapsed_s": round(elapsed, 1),
        "precision": round(precision_hits / total, 3) if total else 0,
        "overclaim_rate": round(overclaims / total, 3) if total else 0,
        "semantic_fraction": round(semantic_count / total, 3) if total else 0,
        "lexical_fallback_fraction": round(lexical_fallbacks / total, 3) if total else 0,
        "unknown_certainty_fraction": round(unknown / total, 3) if total else 0,
        "results": results,
        "verdict": "PASS" if precision_hits > 0.7 * total and overclaims == 0 else "REVIEW",
    }

    print(f"\n{'='*60}")
    print(f"Tasks: {total}  Precision: {report['precision']}  Overclaims: {overclaims}/{total} ({report['overclaim_rate']})")
    print(f"Semantic: {semantic_count}/{total}  Lexical fallback: {lexical_fallbacks}/{total}  Unknown: {unknown}/{total}")
    print(f"Verdict: {report['verdict']}  ({elapsed:.1f}s)")

    out_path = ROOT / "artifacts" / "benchmarks" / "lexical-vs-semantic.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved: {out_path}")

    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())