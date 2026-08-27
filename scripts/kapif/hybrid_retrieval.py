#!/usr/bin/env python3
"""
KAPIF Hybrid Retrieval — combines FTS5 lexical, graph traversal,
semantic similarity, and authority/freshness reranking.

Vector similarity alone is insufficient. Hybrid retrieval must
outperform any single method on the golden set.
"""
from __future__ import annotations

import json
import math
import statistics
import time
from pathlib import Path
from typing import Any

from .fts_index import fts_search, fts_count
from .data_layer import get_atom_with_sources, search_atoms


# ── Retrieval golden set ──

GOLDEN_QUERIES = [
    ("dielectric Fresnel behavior material", ["PRINCIPLE", "FACT"]),
    ("why animation feels weightless timing spacing", ["PRINCIPLE", "FAILURE_PATTERN"]),
    ("responsive typography hierarchy editorial", ["PRINCIPLE", "DESIGN_PATTERN"]),
    ("Niagara particle overdraw GPU performance", ["TOOL_LIMITATION", "PERFORMANCE_FACT"]),
    ("sprite pivot jitter frame timing", ["FAILURE_PATTERN", "DIAGNOSTIC"]),
    ("Unreal Motion Matching memory tradeoff", ["TRADEOFF", "PERFORMANCE_FACT"]),
    ("MaterialX OpenPBR support version", ["TOOL_CAPABILITY", "VERSION_FACT"]),
    ("WCAG keyboard focus accessibility requirement", ["FACT", "CONSTRAINT"]),
    ("visual hierarchy without color value contrast", ["PRINCIPLE", "DESIGN_PATTERN"]),
    ("microdetail scale material surface aging", ["PRINCIPLE", "TRADEOFF"]),
]


def lexical_search(query: str, limit: int = 20) -> list[dict]:
    """FTS5 lexical search."""
    return fts_search(query, limit)


def semantic_search(query: str, limit: int = 20) -> list[dict]:
    """Real semantic search via 9Router embeddings.
    
    Returns atoms ranked by cosine similarity to query embedding.
    Returns empty list if embedding provider unavailable (no lexical fallback).
    """
    from .embeddings import semantic_search_real, is_available
    if not is_available():
        return []  # SEMANTIC_PROVIDER_UNAVAILABLE — no misleading fallback
    return semantic_search_real(query, limit)


def graph_traverse(atom_id: int, depth: int = 1) -> list[dict]:
    """Traverse evidence graph from an atom."""
    from .db import get_conn
    conn = get_conn()
    results = []

    for d in range(depth):
        if d == 0:
            atom = get_atom_with_sources(atom_id)
            if atom:
                results.append(atom)
        # Get related atoms via evidence edges
        cur = conn.execute("""
            SELECT a.* FROM atoms a
            JOIN evidence_edges e ON (e.to_atom_id = a.id OR e.from_atom_id = a.id)
            WHERE (e.from_atom_id = ? OR e.to_atom_id = ?) AND a.id != ?
            LIMIT 10
        """, (atom_id, atom_id, atom_id))
        for row in cur.fetchall():
            results.append(dict(row))
    return results


def hybrid_search(query: str, limit: int = 20,
                  lexical_weight: float = 0.4,
                  semantic_weight: float = 0.3,
                  freshness_boost: float = 0.2,
                  authority_boost: float = 0.1) -> list[dict]:
    """Combine FTS5 + semantic via Reciprocal Rank Fusion.

    RRF score = sum(weight / (k + rank)) across rank lists.
    Authority and freshness rerank relevance — they do not manufacture it.
    """
    t0 = time.time()
    K = 60  # RRF constant (standard)

    # Collect ranked lists
    lexical_results = lexical_search(query, limit * 2)
    semantic_results = semantic_search(query, limit)  # real or empty
    
    # Build rank maps: atom_id -> rank (1-indexed)
    lex_ranks = {}
    for i, r in enumerate(lexical_results):
        rid = r.get("id")
        if rid: lex_ranks[rid] = i + 1
    
    sem_ranks = {}
    for i, r in enumerate(semantic_results):
        rid = r.get("id")
        if rid: sem_ranks[rid] = i + 1
    
    # RRF fusion
    all_ids = set(lex_ranks.keys()) | set(sem_ranks.keys())
    rrf_scores = {}
    for aid in all_ids:
        score = 0.0
        if aid in lex_ranks:
            score += lexical_weight / (K + lex_ranks[aid])
        if aid in sem_ranks:
            score += semantic_weight / (K + sem_ranks[aid])
        rrf_scores[aid] = score
    
    # Build merged atom lookup
    atom_lookup = {}
    for r in lexical_results + semantic_results:
        rid = r.get("id")
        if rid and rid not in atom_lookup:
            atom_lookup[rid] = r
    
    # Apply freshness boost (does not create relevance, boosts existing)
    from datetime import datetime
    now = datetime.now()
    for aid in rrf_scores:
        r = atom_lookup.get(aid, {})
        created = r.get("created_at", "")
        if created:
            try:
                age_days = (now - datetime.fromisoformat(created.replace("Z", "+00:00"))).days
                rrf_scores[aid] *= (1.0 + max(0, 1.0 - age_days / 365) * freshness_boost)
            except Exception:
                pass
    
    # Sort by RRF score
    ranked_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    
    # Build result with scores and provenance
    merged = []
    for aid in ranked_ids[:limit]:
        r = atom_lookup.get(aid, {})
        r["_hybrid_score"] = round(rrf_scores[aid], 6)
        r["_rrf_lex_rank"] = lex_ranks.get(aid)
        r["_rrf_sem_rank"] = sem_ranks.get(aid)
        r["_retrieval_method"] = "hybrid_rrf"
        merged.append(r)
    
    elapsed = round(time.time() - t0, 3)
    for r in merged:
        r["_retrieval_time_s"] = elapsed

    return merged


def _load_relevance_set() -> list[dict]:
    path = Path(__file__).resolve().parents[2] / "data" / "kapif" / "golden-sets" / "retrieval-golden-set.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("queries", [])


def _graded_hits(hits: list[dict], judgments: list[dict]) -> list[int]:
    grades = []
    for hit in hits:
        statement = hit.get("statement", "").lower()
        grade = 0
        for judgment in judgments:
            needle = judgment.get("atom_statement_contains", "").lower()
            if needle and needle in statement:
                grade = max(grade, int(judgment.get("grade", 0)))
        grades.append(grade)
    return grades


def _metrics(grades: list[int], judgments: list[dict], k: int) -> dict[str, float]:
    relevant = {j.get("atom_statement_contains", "").lower() for j in judgments if int(j.get("grade", 0)) > 0}
    retrieved_relevant = sum(1 for grade in grades[:k] if grade > 0)
    total_relevant = len(relevant)
    precision = retrieved_relevant / k if k else 0.0
    recall = retrieved_relevant / total_relevant if total_relevant else 0.0
    rr = 0.0
    for index, grade in enumerate(grades, 1):
        if grade > 0:
            rr = 1.0 / index
            break
    dcg = sum((2 ** grade - 1) / math.log2(index + 1) for index, grade in enumerate(grades[:10], 1))
    ideal = sorted([int(j.get("grade", 0)) for j in judgments], reverse=True)[:10]
    idcg = sum((2 ** grade - 1) / math.log2(index + 1) for index, grade in enumerate(ideal, 1))
    return {"precision_at_k": precision, "recall_at_k": recall, "mrr": rr,
            "ndcg_at_10": dcg / idcg if idcg else 0.0}


def benchmark_retrieval(method: str = "hybrid", relevance_set: list[dict] | None = None) -> dict[str, Any]:
    """Benchmark against frozen graded relevance judgments, never atom types."""
    methods = {"lexical": lexical_search, "semantic": semantic_search, "hybrid": hybrid_search}
    fn = methods.get(method, hybrid_search)
    queries = relevance_set if relevance_set is not None else _load_relevance_set()
    if not queries:
        return {"method": method, "status": "REFERENCE_SET_UNAVAILABLE", "queries": 0}
    if method == "semantic":
        from .embeddings import is_available
        if not is_available():
            return {
                "method": method,
                "status": "PROVIDER_UNAVAILABLE",
                "queries": 0,
                "semantic_provider_used": False,
            }
    rows = []
    latencies = []
    for item in queries:
        query = item.get("query", "")
        judgments = item.get("relevance_judgments", [])
        t0 = time.perf_counter()
        hits = fn(query, limit=10)
        latency = time.perf_counter() - t0
        latencies.append(latency)
        grades = _graded_hits(hits, judgments)
        metrics = _metrics(grades, judgments, 5)
        metrics10 = _metrics(grades, judgments, 10)
        rows.append({"query": query, "hits": len(hits), "grades": grades,
                     "recall_at_10": metrics10["recall_at_k"],
                     "precision_at_5": metrics["precision_at_k"],
                     "recall_at_5": metrics["recall_at_k"],
                     "mrr": metrics["mrr"], "ndcg_at_10": metrics10["ndcg_at_10"],
                     "latency_s": round(latency, 6)})
    p95_index = max(0, min(len(latencies) - 1, math.ceil(len(latencies) * 0.95) - 1))
    ordered = sorted(latencies)
    return {"method": method, "status": "PASS", "queries": len(rows),
            "semantic_provider_used": method != "semantic" or bool(rows),
            "degraded": False,
            "recall_at_5": round(statistics.mean(r["recall_at_5"] for r in rows), 4),
            "recall_at_10": round(statistics.mean(r["recall_at_10"] for r in rows), 4),
            "precision_at_5": round(statistics.mean(r["precision_at_5"] for r in rows), 4),
            "mrr": round(statistics.mean(r["mrr"] for r in rows), 4),
            "ndcg_at_10": round(statistics.mean(r["ndcg_at_10"] for r in rows), 4),
            "latency_p50_s": round(ordered[len(ordered) // 2], 6),
            "latency_p95_s": round(ordered[p95_index], 6), "results": rows}


def benchmark_all_methods() -> dict[str, Any]:
    """Run FTS, semantic, and RRF on the exact same frozen relevance set.

    An incomplete comparison cannot produce a winner. Hybrid is explicitly
    degraded when its semantic input is unavailable.
    """
    relevance = _load_relevance_set()
    if not relevance:
        return {"status": "REFERENCE_SET_UNAVAILABLE", "winner": "NO_COMPLETE_WINNER"}
    methods = {name: benchmark_retrieval(name, relevance) for name in ("lexical", "semantic", "hybrid")}
    semantic_used = methods["semantic"].get("status") == "PASS"
    if not semantic_used:
        methods["hybrid"]["status"] = "PARTIAL"
        methods["hybrid"]["degraded"] = True
        methods["hybrid"]["degradation_reason"] = "SEMANTIC_PROVIDER_UNAVAILABLE"
    complete = all(methods[name].get("status") == "PASS" for name in ("lexical", "semantic", "hybrid"))
    has_judged_hits = any(
        methods[name].get("ndcg_at_10", 0.0) > 0.0
        for name in ("lexical", "semantic", "hybrid")
    )
    if complete and not has_judged_hits:
        complete = False
        for method in methods.values():
            method["status"] = "FAIL"
            method["failure_reason"] = "PRODUCTION_CORPUS_HAS_NO_JUDGED_HITS"
    winner = max(methods, key=lambda name: methods[name].get("ndcg_at_10", -1)) if complete else "NO_COMPLETE_WINNER"
    return {"status": "PASS" if complete else "PARTIAL", "relevance_queries": len(relevance), "methods": methods,
            "winner_by_ndcg_at_10": winner,
            "semantic_provider_used": semantic_used,
            "fusion_inputs": ["lexical", "semantic"] if semantic_used else ["lexical"],
            "degraded": not complete}



class EmbeddingProviderBenchmark:
    """Benchmark embedding providers for semantic retrieval."""

    CANDIDATES = {
        "sentence-transformers/all-MiniLM-L6-v2": {
            "dim": 384, "vram_approx_mb": 90, "license": "Apache 2.0",
            "local": True, "platforms": ["windows", "linux"],
        },
        "sentence-transformers/all-mpnet-base-v2": {
            "dim": 768, "vram_approx_mb": 420, "license": "Apache 2.0",
            "local": True, "platforms": ["windows", "linux"],
        },
        "BAAI/bge-small-en-v1.5": {
            "dim": 384, "vram_approx_mb": 130, "license": "MIT",
            "local": True, "platforms": ["windows", "linux"],
        },
        "intfloat/e5-small-v2": {
            "dim": 384, "vram_approx_mb": 130, "license": "MIT",
            "local": True, "platforms": ["windows", "linux"],
        },
        "9router-embeddings": {
            "dim": "varies", "vram_approx_mb": 0, "license": "varies",
            "local": False, "platforms": ["any"],
        },
    }

    def recommend(self, hardware_vram_gb: float = 10.0, prefer_local: bool = True) -> str:
        """Recommend best embedding provider for hardware context."""
        best = None
        for name, info in self.CANDIDATES.items():
            if prefer_local and not info["local"]:
                continue
            if info["vram_approx_mb"] / 1024 > hardware_vram_gb * 0.5:
                continue
            if info.get("dim") == "varies":
                continue
            if best is None or info["vram_approx_mb"] < best["vram_approx_mb"]:
                best = {"name": name, **info}
        if best:
            return best["name"]
        return "sentence-transformers/all-MiniLM-L6-v2"  # Default fallback


def embedding_benchmark_report() -> dict:
    bench = EmbeddingProviderBenchmark()
    reco = bench.recommend(hardware_vram_gb=10.0, prefer_local=True)
    return {
        "recommendation": reco,
        "candidates": [
            {"name": k, **v} for k, v in EmbeddingProviderBenchmark.CANDIDATES.items()
        ],
        "hardware_context": "RTX 5070 Ti 12GB, ~10GB available",
        "caveat": "Not yet installed or benchmarked on actual hardware. Recommendation based on VRAM analysis.",
    }