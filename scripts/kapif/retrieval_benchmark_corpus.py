#!/usr/bin/env python3
"""Build a self-contained retrieval benchmark corpus.

Separates benchmark atoms from the production KAPIF database.
Each benchmark atom has a stable synthetic ID (not SQLite autoincrement).
The frozen relevance judgments reference stable atom_statement_contains text,
not production IDs.

This module creates an isolated SQLite database containing:
  - benchmark_atoms (stable benchmark_id + statement + metadata)
  - benchmark_fts (FTS5 index over benchmark atoms)
  - benchmark_vectors (optional embedding vectors)

The benchmark DB is ephemeral and rebuilt each run.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import statistics
import struct
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RETRIEVAL_SET_PATH = ROOT / "data" / "kapif" / "golden-sets" / "retrieval-golden-set.json"
EXTRACTION_SET_PATH = ROOT / "data" / "kapif" / "golden-sets" / "extraction-golden-set.json"

# Stable benchmark atoms derived from the extraction golden set.
# These provide the "ground truth corpus" for retrieval evaluation.
BENCHMARK_ATOMS = [
    # Frontend / Core Web Vitals
    {"benchmark_id": "bm-cwv-lcp", "statement": "Largest Contentful Paint (LCP) measures loading performance and should be 2.5 seconds or less for good user experience.", "atom_type": "PERFORMANCE_FACT", "discipline": "frontend", "scope": "web-performance", "source_url": "https://web.dev/articles/vitals"},
    {"benchmark_id": "bm-cwv-measure", "statement": "Core Web Vitals thresholds are evaluated at the 75th percentile of page loads measured in the field.", "atom_type": "PROCEDURE", "discipline": "frontend", "scope": "web-performance", "source_url": "https://web.dev/articles/vitals"},
    {"benchmark_id": "bm-cwv-inp", "statement": "Interaction to Next Paint (INP) measures responsiveness and should be 200 milliseconds or less.", "atom_type": "PERFORMANCE_FACT", "discipline": "frontend", "scope": "web-performance", "source_url": "https://web.dev/articles/vitals"},
    {"benchmark_id": "bm-cwv-cls", "statement": "Cumulative Layout Shift (CLS) measures visual stability and should be 0.1 or less.", "atom_type": "PERFORMANCE_FACT", "discipline": "frontend", "scope": "web-performance", "source_url": "https://web.dev/articles/vitals"},
    {"benchmark_id": "bm-css-contain", "statement": "CSS containment limits browser layout, style, and paint work to specific DOM subtrees.", "atom_type": "TOOL_CAPABILITY", "discipline": "frontend", "scope": "css", "source_url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment"},
    {"benchmark_id": "bm-css-layout", "statement": "contain: layout isolates an element's layout from the rest of the page.", "atom_type": "TOOL_CAPABILITY", "discipline": "frontend", "scope": "css", "source_url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment"},
    {"benchmark_id": "bm-svg-viewbox", "statement": "SVG viewBox defines the coordinate system for the graphic.", "atom_type": "TOOL_CAPABILITY", "discipline": "frontend", "scope": "svg", "source_url": "https://developer.mozilla.org/en-US/docs/Web/SVG/Element/svg"},
    {"benchmark_id": "bm-svg-resolution", "statement": "SVG graphics are resolution-independent and styleable with CSS.", "atom_type": "TOOL_CAPABILITY", "discipline": "frontend", "scope": "svg", "source_url": "https://developer.mozilla.org/en-US/docs/Web/SVG/Element/svg"},
    # Accessibility
    {"benchmark_id": "bm-wcag-target", "statement": "WCAG 2.2 SC 2.5.8 Target Size (Minimum) at Level AA requires target size of at least 24x24 CSS pixels.", "atom_type": "FACT", "discipline": "accessibility", "scope": "wcag-2.2", "source_url": "https://www.w3.org/TR/WCAG22/"},
    {"benchmark_id": "bm-wcag-contrast", "statement": "WCAG 2.2 SC 1.4.3 requires a contrast ratio of at least 4.5:1 for normal text at Level AA.", "atom_type": "FACT", "discipline": "accessibility", "scope": "wcag-2.2", "source_url": "https://www.w3.org/TR/WCAG22/"},
    {"benchmark_id": "bm-wcag-large-text", "statement": "Large text is defined as at least 18 point or 14 point bold for contrast purposes.", "atom_type": "FACT", "discipline": "accessibility", "scope": "wcag-2.2", "source_url": "https://www.w3.org/TR/WCAG22/"},
    {"benchmark_id": "bm-reduced-motion", "statement": "prefers-reduced-motion detects user preference for reduced non-essential animation.", "atom_type": "TOOL_CAPABILITY", "discipline": "accessibility", "scope": "css-media-queries", "source_url": "https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion"},
    # 3D Materials / PBR
    {"benchmark_id": "bm-fresnel", "statement": "The Fresnel effect causes surface reflectance to change based on viewing angle.", "atom_type": "PRINCIPLE", "discipline": "materials", "scope": "pbr", "source_url": "https://learnopengl.com/PBR/Theory"},
    {"benchmark_id": "bm-f0-dielectric", "statement": "Dielectric (non-metal) materials have a base reflectivity (F0) of approximately 0.04 at normal incidence.", "atom_type": "FACT", "discipline": "materials", "scope": "pbr", "source_url": "https://learnopengl.com/PBR/Theory"},
    {"benchmark_id": "bm-f0-metal", "statement": "Metallic materials have F0 values ranging from 0.5 to 1.0.", "atom_type": "FACT", "discipline": "materials", "scope": "pbr", "source_url": "https://learnopengl.com/PBR/Theory"},
    {"benchmark_id": "bm-energy-conservation", "statement": "Energy conservation is a fundamental principle of PBR: reflected plus absorbed light cannot exceed incoming light.", "atom_type": "PRINCIPLE", "discipline": "materials", "scope": "pbr", "source_url": "https://learnopengl.com/PBR/Theory"},
    {"benchmark_id": "bm-blender-agx", "statement": "Blender 4.0 replaced Filmic with AgX as the default display transform.", "atom_type": "VERSION_FACT", "discipline": "materials", "scope": "blender", "source_url": "https://docs.blender.org/manual/en/latest/render/color_management/"},
    {"benchmark_id": "bm-blender-agx-range", "statement": "AgX provides wider dynamic range and more natural highlight rolloff than Filmic.", "atom_type": "PERFORMANCE_FACT", "discipline": "materials", "scope": "blender", "source_url": "https://docs.blender.org/manual/en/latest/render/color_management/"},
    {"benchmark_id": "bm-cycles-gpu-tile", "statement": "Cycles GPU rendering is more efficient with larger tile sizes (256-512).", "atom_type": "PERFORMANCE_FACT", "discipline": "materials", "scope": "blender-cycles", "source_url": "https://docs.blender.org/manual/en/latest/render/cycles/"},
    {"benchmark_id": "bm-cycles-cpu-tile", "statement": "Cycles CPU rendering may perform better with smaller tile sizes (32-64).", "atom_type": "PERFORMANCE_FACT", "discipline": "materials", "scope": "blender-cycles", "source_url": "https://docs.blender.org/manual/en/latest/render/cycles/"},
    {"benchmark_id": "bm-glsl-mix", "statement": "GLSL mix() function blends two values using a factor between 0 and 1.", "atom_type": "PROCEDURE", "discipline": "materials", "scope": "glsl", "source_url": "https://thebookofshaders.com/05/"},
    # Game Engine / Unreal
    {"benchmark_id": "bm-niagara-gpu-cpu", "statement": "Niagara supports both GPU and CPU particle simulation.", "atom_type": "TOOL_CAPABILITY", "discipline": "game-engine", "scope": "unreal-niagara", "source_url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/niagara-particle-system"},
    {"benchmark_id": "bm-niagara-millions", "statement": "Niagara GPU simulation enables processing millions of particles in real-time.", "atom_type": "TOOL_CAPABILITY", "discipline": "game-engine", "scope": "unreal-niagara", "source_url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/niagara-particle-system"},
    {"benchmark_id": "bm-lumen-gi", "statement": "Lumen provides dynamic global illumination and reflections in Unreal Engine.", "atom_type": "TOOL_CAPABILITY", "discipline": "game-engine", "scope": "unreal-lumen", "source_url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination"},
    {"benchmark_id": "bm-lumen-bounces", "statement": "Lumen supports infinite bounces for indirect lighting.", "atom_type": "TOOL_CAPABILITY", "discipline": "game-engine", "scope": "unreal-lumen", "source_url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination"},
    {"benchmark_id": "bm-webgl-glsl", "statement": "WebGL uses GLSL shaders for GPU-based browser rendering.", "atom_type": "TOOL_CAPABILITY", "discipline": "vfx", "scope": "webgl", "source_url": "https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial"},
    {"benchmark_id": "bm-webgl-pipeline", "statement": "The vertex shader processes vertices and the fragment shader determines pixel colors in WebGL.", "atom_type": "PROCEDURE", "discipline": "vfx", "scope": "webgl", "source_url": "https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial"},
    # Typography
    {"benchmark_id": "bm-line-height", "statement": "For 12pt body text, 150% line height (18pt) is a reasonable default.", "atom_type": "PRINCIPLE", "discipline": "typography", "scope": "line-spacing", "source_url": "https://practicaltypography.com/line-spacing.html"},
    {"benchmark_id": "bm-type-scale", "statement": "A Major Third scale (1.250 ratio) produces moderate contrast between heading levels.", "atom_type": "PRINCIPLE", "discipline": "typography", "scope": "type-scale", "source_url": "https://typescale.com/"},
    {"benchmark_id": "bm-type-rhythm", "statement": "Type scales create visual rhythm and predictability in layout.", "atom_type": "PRINCIPLE", "discipline": "typography", "scope": "type-scale", "source_url": "https://typescale.com/"},
    # Color Science
    {"benchmark_id": "bm-display-p3", "statement": "Display P3 is an RGB color space for modern displays with wider gamut than sRGB.", "atom_type": "FACT", "discipline": "color-science", "scope": "css-color", "source_url": "https://www.w3.org/TR/css-color-4/"},
    {"benchmark_id": "bm-srgb-default", "statement": "sRGB is the default color space for web content.", "atom_type": "FACT", "discipline": "color-science", "scope": "css-color", "source_url": "https://www.w3.org/TR/css-color-4/"},
    # Software Engineering
    {"benchmark_id": "bm-sqlite-writers", "statement": "SQLite supports multiple concurrent readers but only one writer at a time.", "atom_type": "TOOL_LIMITATION", "discipline": "software-engineering", "scope": "sqlite", "source_url": "https://docs.python.org/3/library/sqlite3.html"},
    {"benchmark_id": "bm-sqlite-wal", "statement": "WAL mode in SQLite allows concurrent reads during write operations.", "atom_type": "TOOL_CAPABILITY", "discipline": "software-engineering", "scope": "sqlite", "source_url": "https://docs.python.org/3/library/sqlite3.html"},
    {"benchmark_id": "bm-asyncio", "statement": "Python asyncio enables concurrent programming using async/await syntax.", "atom_type": "TOOL_CAPABILITY", "discipline": "software-engineering", "scope": "python-asyncio", "source_url": "https://docs.python.org/3/library/asyncio.html"},
    {"benchmark_id": "bm-asyncio-loop", "statement": "The asyncio event loop manages coroutine scheduling, I/O events, and callbacks.", "atom_type": "PROCEDURE", "discipline": "software-engineering", "scope": "python-asyncio", "source_url": "https://docs.python.org/3/library/asyncio.html"},
    {"benchmark_id": "bm-git-rebase", "statement": "Interactive rebasing allows changing, reordering, and squashing commits.", "atom_type": "PROCEDURE", "discipline": "software-engineering", "scope": "git", "source_url": "https://git-scm.com/book/en/v2/Git-Tools-Interactive-Rebasing"},
    {"benchmark_id": "bm-git-shared", "statement": "Do not rebase commits already pushed to a shared repository.", "atom_type": "CONSTRAINT", "discipline": "software-engineering", "scope": "git", "source_url": "https://git-scm.com/book/en/v2/Git-Tools-Interactive-Rebasing"},
    {"benchmark_id": "bm-docker-multistage", "statement": "Multi-stage Docker builds reduce final image size by separating build and runtime stages.", "atom_type": "PROCEDURE", "discipline": "software-engineering", "scope": "docker", "source_url": "https://docs.docker.com/build/building/best-practices/"},
    {"benchmark_id": "bm-docker-cache", "statement": "Order Dockerfile instructions from least to most frequently changing to leverage build cache.", "atom_type": "PROCEDURE", "discipline": "software-engineering", "scope": "docker", "source_url": "https://docs.docker.com/build/building/best-practices/"},
    {"benchmark_id": "bm-http-429", "statement": "HTTP 429 indicates the client has exceeded the rate limit.", "atom_type": "FACT", "discipline": "software-engineering", "scope": "http", "source_url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429"},
    {"benchmark_id": "bm-retry-after", "statement": "The Retry-After header in a 429 response indicates when to retry.", "atom_type": "PROCEDURE", "discipline": "software-engineering", "scope": "http", "source_url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429"},
    # UX / Design
    {"benchmark_id": "bm-emergency-exit", "statement": "Users need clear emergency exits from unwanted states without extended processes.", "atom_type": "PRINCIPLE", "discipline": "ui-ux", "scope": "usability-heuristics", "source_url": "https://www.nngroup.com/articles/ten-usability-heuristics/"},
    {"benchmark_id": "bm-undo-redo", "statement": "Supporting undo and redo provides user control and freedom.", "atom_type": "PRINCIPLE", "discipline": "ui-ux", "scope": "usability-heuristics", "source_url": "https://www.nngroup.com/articles/ten-usability-heuristics/"},
    {"benchmark_id": "bm-5-users", "statement": "Testing with 5 users typically reveals about 85% of usability problems.", "atom_type": "TRADEOFF", "discipline": "research", "scope": "usability-testing", "source_url": "https://www.nngroup.com/articles/how-many-test-users/"},
]


def build_benchmark_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Create an isolated benchmark DB with atoms + FTS5."""
    if db_path is None:
        import tempfile
        db_path = Path(tempfile.mktemp(suffix=".db"))

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS benchmark_atoms (
            benchmark_id TEXT PRIMARY KEY,
            statement TEXT NOT NULL,
            atom_type TEXT,
            discipline TEXT,
            scope TEXT,
            source_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)

    # FTS5 virtual table over benchmark atoms
    try:
        conn.execute("DROP TABLE IF EXISTS benchmark_atoms_fts")
    except Exception:
        pass
    conn.execute("""
        CREATE VIRTUAL TABLE benchmark_atoms_fts USING fts5(
            benchmark_id, statement, atom_type, discipline, scope,
            content='benchmark_atoms', content_rowid='rowid'
        )
    """)

    # Populate atoms
    for atom in BENCHMARK_ATOMS:
        conn.execute(
            "INSERT OR REPLACE INTO benchmark_atoms(benchmark_id, statement, atom_type, discipline, scope, source_url) VALUES (?,?,?,?,?,?)",
            (atom["benchmark_id"], atom["statement"], atom["atom_type"], atom["discipline"], atom["scope"], atom["source_url"])
        )
    conn.commit()

    # Rebuild FTS using the FTS5 rebuild command (safe for external content)
    conn.execute("INSERT INTO benchmark_atoms_fts(benchmark_atoms_fts) VALUES ('rebuild')")
    conn.commit()

    return conn


def benchmark_fts(conn: sqlite3.Connection, queries: list[dict], k: int = 10) -> dict[str, Any]:
    """Run FTS5/BM25 retrieval benchmark."""
    rows = []
    latencies = []

    for item in queries:
        query = item.get("query", "")
        judgments = item.get("relevance_judgments", [])
        if not judgments:
            continue

        t0 = time.perf_counter()
        try:
            # Use OR matching for natural-language queries
            or_query = " OR ".join(query.split())
            cur = conn.execute("""
                SELECT a.benchmark_id, a.statement, bm25(benchmark_atoms_fts) AS score
                FROM benchmark_atoms a
                JOIN benchmark_atoms_fts fts ON a.rowid = fts.rowid
                WHERE benchmark_atoms_fts MATCH ?
                ORDER BY score LIMIT ?
            """, (or_query, k))
            hits = [dict(r) for r in cur.fetchall()]
        except Exception:
            hits = []
        latency = time.perf_counter() - t0
        latencies.append(latency)

        grades = _graded_hits(hits, judgments)
        m = _compute_metrics(grades, judgments, k)
        rows.append({"query": query, "hits": len(hits), **m, "latency_s": round(latency, 6)})

    return _aggregate("lexical", rows, latencies)


def benchmark_semantic(conn: sqlite3.Connection, queries: list[dict], k: int = 10) -> dict[str, Any]:
    """Run semantic vector retrieval benchmark."""
    from .embeddings import is_available, embed_text, cosine_similarity

    if not is_available():
        return {"method": "semantic", "status": "PROVIDER_UNAVAILABLE", "queries": 0}

    # Load all benchmark atoms and embed them
    all_atoms = [dict(r) for r in conn.execute("SELECT benchmark_id, statement FROM benchmark_atoms").fetchall()]
    if not all_atoms:
        return {"method": "semantic", "status": "EMPTY_CORPUS", "queries": 0}

    # Embed all atoms (batch)
    texts = [a["statement"] for a in all_atoms]
    from .embeddings import embed_batch
    atom_vecs = embed_batch(texts)

    # Build lookup
    vec_lookup = {}
    for atom, vec in zip(all_atoms, atom_vecs):
        if vec:
            vec_lookup[atom["benchmark_id"]] = vec

    if not vec_lookup:
        return {"method": "semantic", "status": "NO_VECTORS_GENERATED", "queries": 0}

    rows = []
    latencies = []

    for item in queries:
        query = item.get("query", "")
        judgments = item.get("relevance_judgments", [])
        if not judgments:
            continue

        t0 = time.perf_counter()
        q_vec = embed_text(query)
        if q_vec is None:
            latencies.append(time.perf_counter() - t0)
            rows.append({"query": query, "hits": 0, "recall_at_k": 0.0, "precision_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0, "latency_s": 0.0})
            continue

        # Score all atoms
        scored = []
        for aid, avec in vec_lookup.items():
            sim = cosine_similarity(q_vec, avec)
            scored.append((aid, sim))
        scored.sort(key=lambda x: x[1], reverse=True)

        # Build hit list with statements
        hits = []
        stmt_lookup = {a["benchmark_id"]: a["statement"] for a in all_atoms}
        for aid, sim in scored[:k]:
            hits.append({"benchmark_id": aid, "statement": stmt_lookup.get(aid, ""), "score": sim})

        latency = time.perf_counter() - t0
        latencies.append(latency)

        grades = _graded_hits(hits, judgments)
        m = _compute_metrics(grades, judgments, k)
        rows.append({"query": query, "hits": len(hits), **m, "latency_s": round(latency, 6)})

    return _aggregate("semantic", rows, latencies)


def benchmark_hybrid(conn: sqlite3.Connection, queries: list[dict], k: int = 10) -> dict[str, Any]:
    """Run hybrid RRF retrieval benchmark."""
    from .embeddings import is_available, embed_text, cosine_similarity, embed_batch

    rows = []
    latencies = []
    K_RRF = 60
    lex_weight = 0.4
    sem_weight = 0.6

    # Pre-embed all atoms if semantic available
    sem_available = is_available()
    vec_lookup = {}
    stmt_lookup = {}

    all_atoms = [dict(r) for r in conn.execute("SELECT benchmark_id, statement FROM benchmark_atoms").fetchall()]
    for a in all_atoms:
        stmt_lookup[a["benchmark_id"]] = a["statement"]

    if sem_available and all_atoms:
        texts = [a["statement"] for a in all_atoms]
        atom_vecs = embed_batch(texts)
        for atom, vec in zip(all_atoms, atom_vecs):
            if vec:
                vec_lookup[atom["benchmark_id"]] = vec

    for item in queries:
        query = item.get("query", "")
        judgments = item.get("relevance_judgments", [])
        if not judgments:
            continue

        t0 = time.perf_counter()

        # Lexical hits (OR matching for natural-language queries)
        try:
            or_query = " OR ".join(query.split())
            cur = conn.execute("""
                SELECT a.benchmark_id, a.statement, bm25(benchmark_atoms_fts) AS score
                FROM benchmark_atoms a
                JOIN benchmark_atoms_fts fts ON a.rowid = fts.rowid
                WHERE benchmark_atoms_fts MATCH ?
                ORDER BY score LIMIT ?
            """, (or_query, k * 2))
            lex_hits = [dict(r) for r in cur.fetchall()]
        except Exception:
            lex_hits = []

        lex_ranks = {h["benchmark_id"]: i + 1 for i, h in enumerate(lex_hits)}

        # Semantic hits
        sem_ranks = {}
        if sem_available and vec_lookup:
            q_vec = embed_text(query)
            if q_vec:
                scored = [(aid, cosine_similarity(q_vec, v)) for aid, v in vec_lookup.items()]
                scored.sort(key=lambda x: x[1], reverse=True)
                sem_ranks = {aid: i + 1 for i, (aid, _) in enumerate(scored[:k * 2])}

        # RRF fusion
        all_ids = set(lex_ranks.keys()) | set(sem_ranks.keys())
        rrf_scores = {}
        for aid in all_ids:
            score = 0.0
            if aid in lex_ranks:
                score += lex_weight / (K_RRF + lex_ranks[aid])
            if aid in sem_ranks:
                score += sem_weight / (K_RRF + sem_ranks[aid])
            rrf_scores[aid] = score

        ranked = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        hits = [{"benchmark_id": aid, "statement": stmt_lookup.get(aid, ""), "rrf_score": rrf_scores[aid]} for aid in ranked[:k]]

        latency = time.perf_counter() - t0
        latencies.append(latency)

        grades = _graded_hits(hits, judgments)
        m = _compute_metrics(grades, judgments, k)
        rows.append({"query": query, "hits": len(hits), **m, "latency_s": round(latency, 6)})

    return _aggregate("hybrid", rows, latencies)


# ── Scoring helpers ──

def _graded_hits(hits: list[dict], judgments: list[dict]) -> list[int]:
    grades = []
    for hit in hits:
        statement = hit.get("statement", "").lower()
        grade = 0
        for j in judgments:
            needle = j.get("atom_statement_contains", "").lower()
            if needle and needle in statement:
                grade = max(grade, int(j.get("grade", 0)))
        grades.append(grade)
    return grades


def _compute_metrics(grades: list[int], judgments: list[dict], k: int) -> dict[str, float]:
    relevant = {j["atom_statement_contains"].lower() for j in judgments if int(j.get("grade", 0)) > 0}
    retrieved_relevant = sum(1 for g in grades[:k] if g > 0)
    total_relevant = len(relevant)
    precision = retrieved_relevant / k if k else 0.0
    recall = retrieved_relevant / total_relevant if total_relevant else 0.0
    rr = 0.0
    for idx, g in enumerate(grades, 1):
        if g > 0:
            rr = 1.0 / idx
            break
    dcg = sum((2 ** g - 1) / math.log2(idx + 1) for idx, g in enumerate(grades[:10], 1))
    ideal = sorted([int(j.get("grade", 0)) for j in judgments], reverse=True)[:10]
    idcg = sum((2 ** g - 1) / math.log2(idx + 1) for idx, g in enumerate(ideal, 1))
    return {
        "recall_at_k": round(recall, 4),
        "precision_at_k": round(precision, 4),
        "mrr": round(rr, 4),
        "ndcg_at_k": round(dcg / idcg if idcg else 0.0, 4),
    }


def _aggregate(method: str, rows: list[dict], latencies: list[float]) -> dict[str, Any]:
    if not rows:
        return {"method": method, "status": "NO_QUERIES_WITH_JUDGMENTS", "queries": 0}
    ordered = sorted(latencies)
    p95_idx = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1))
    return {
        "method": method,
        "status": "PASS",
        "queries": len(rows),
        "recall_at_5": round(statistics.mean(r.get("recall_at_k", 0) for r in rows), 4),
        "recall_at_10": round(statistics.mean(r.get("recall_at_k", 0) for r in rows), 4),
        "precision_at_5": round(statistics.mean(r.get("precision_at_k", 0) for r in rows), 4),
        "mrr": round(statistics.mean(r.get("mrr", 0) for r in rows), 4),
        "ndcg_at_10": round(statistics.mean(r.get("ndcg_at_k", 0) for r in rows), 4),
        "latency_p50_s": round(ordered[len(ordered) // 2], 6) if ordered else 0,
        "latency_p95_s": round(ordered[p95_idx], 6) if ordered else 0,
        "results": rows,
    }


def run_full_benchmark() -> dict[str, Any]:
    """Run FTS + semantic + hybrid against the benchmark corpus."""
    if not RETRIEVAL_SET_PATH.exists():
        return {"status": "REFERENCE_SET_MISSING"}

    rel_data = json.loads(RETRIEVAL_SET_PATH.read_text(encoding="utf-8"))
    queries = rel_data.get("queries", [])
    queries_with_judgments = [q for q in queries if q.get("relevance_judgments")]

    print(f"Benchmark queries: {len(queries_with_judgments)} (of {len(queries)} total)")

    conn = build_benchmark_db()
    try:
        atom_count = conn.execute("SELECT COUNT(*) FROM benchmark_atoms").fetchone()[0]
        print(f"Benchmark corpus: {atom_count} atoms")

        lex = benchmark_fts(conn, queries_with_judgments)
        sem = benchmark_semantic(conn, queries_with_judgments)
        hyb = benchmark_hybrid(conn, queries_with_judgments)

        # Determine winner
        methods = {"lexical": lex, "semantic": sem, "hybrid": hyb}
        complete = all(m.get("status") == "PASS" for m in methods.values())
        has_hits = any(m.get("ndcg_at_10", 0) > 0 for m in methods.values())

        if complete and has_hits:
            winner = max(methods, key=lambda n: methods[n].get("ndcg_at_10", -1))
        else:
            winner = "NO_COMPLETE_WINNER"

        return {
            "status": "PASS" if complete and has_hits else "PARTIAL",
            "benchmark_corpus_atoms": atom_count,
            "queries_evaluated": len(queries_with_judgments),
            "methods": methods,
            "winner_by_ndcg_at_10": winner,
            "semantic_provider_used": sem.get("status") == "PASS",
        }
    finally:
        conn.close()
