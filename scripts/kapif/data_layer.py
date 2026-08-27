#!/usr/bin/env python3
"""KAPIF Data Layer — SQLite storage using safe connection manager."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .db import get_conn, execute, commit, close_conn, DB_PATH

ROOT = Path(__file__).resolve().parents[2]


def hash_content(content: bytes | str) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8", errors="replace")
    return hashlib.sha256(content).hexdigest()


def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY,
        source_id TEXT UNIQUE NOT NULL,
        canonical_url TEXT NOT NULL,
        source_class TEXT DEFAULT 'generic_web',
        adapter_type TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS snapshots (
        id INTEGER PRIMARY KEY,
        source_id INTEGER REFERENCES sources(id),
        canonical_url TEXT NOT NULL,
        retrieved_at TEXT NOT NULL,
        http_status INTEGER,
        etag TEXT,
        last_modified TEXT,
        content_hash TEXT NOT NULL,
        normalized_hash TEXT,
        adapter_type TEXT,
        adapter_version TEXT,
        robots_status TEXT,
        policy_decision TEXT,
        content_type TEXT,
        byte_length INTEGER,
        raw_path TEXT,
        UNIQUE(source_id, content_hash)
    );
    CREATE TABLE IF NOT EXISTS atoms (
        id INTEGER PRIMARY KEY,
        atom_type TEXT NOT NULL,
        statement TEXT NOT NULL,
        discipline TEXT,
        scope TEXT,
        conditions TEXT,
        exceptions TEXT,
        evidence_span TEXT,
        evidence_start INTEGER,
        evidence_end INTEGER,
        source_hash TEXT,
        extraction_model TEXT,
        model_version TEXT,
        extractor_version TEXT,
        confidence TEXT DEFAULT 'UNVERIFIED',
        version_dependency TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS atom_sources (
        id INTEGER PRIMARY KEY,
        atom_id INTEGER REFERENCES atoms(id),
        snapshot_id INTEGER REFERENCES snapshots(id),
        support_type TEXT DEFAULT 'ASSERTED_BY',
        UNIQUE(atom_id, snapshot_id, support_type)
    );
    CREATE TABLE IF NOT EXISTS evidence_edges (
        id INTEGER PRIMARY KEY,
        from_atom_id INTEGER REFERENCES atoms(id),
        to_atom_id INTEGER REFERENCES atoms(id),
        relation TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(from_atom_id, to_atom_id, relation)
    );
    CREATE TABLE IF NOT EXISTS contradictions (
        id INTEGER PRIMARY KEY,
        atom_a_id INTEGER REFERENCES atoms(id),
        atom_b_id INTEGER REFERENCES atoms(id),
        resolution TEXT DEFAULT 'UNRESOLVED',
        explanation TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS canon (
        id INTEGER PRIMARY KEY,
        atom_id INTEGER REFERENCES atoms(id) UNIQUE,
        promoted_at TEXT DEFAULT (datetime('now')),
        validator TEXT,
        confidence TEXT DEFAULT 'VALIDATED'
    );
    CREATE TABLE IF NOT EXISTS external_experience (
        id INTEGER PRIMARY KEY,
        source_snapshot_id INTEGER REFERENCES snapshots(id),
        context TEXT,
        goal TEXT,
        constraints TEXT,
        initial_approach TEXT,
        failure_observed TEXT,
        diagnosis TEXT,
        repair TEXT,
        outcome TEXT,
        tradeoff TEXT,
        transferable_principle TEXT,
        limitations TEXT,
        extracted_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS foundry_experience (
        id INTEGER PRIMARY KEY,
        atom_id INTEGER REFERENCES atoms(id),
        lab_id TEXT,
        outcome TEXT,
        evidence_path TEXT,
        recorded_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS stale_dependencies (
        id INTEGER PRIMARY KEY,
        snapshot_id INTEGER REFERENCES snapshots(id),
        atom_id INTEGER REFERENCES atoms(id),
        stale_reason TEXT,
        detected_at TEXT DEFAULT (datetime('now')),
        resolved_at TEXT
    );
    CREATE TABLE IF NOT EXISTS fetch_log (
        id INTEGER PRIMARY KEY,
        url TEXT NOT NULL,
        adapter TEXT,
        fetched_at TEXT DEFAULT (datetime('now')),
        http_status INTEGER,
        bytes_fetched INTEGER,
        cache_hit INTEGER DEFAULT 0,
        rate_limit_status TEXT,
        robots_status TEXT,
        policy_decision TEXT,
        retry_count INTEGER DEFAULT 0,
        error TEXT
    );
    """)
    # Existing installations may have the base table but not M002.1
    # provenance columns. Inspect the live schema instead of relying on a
    # database version integer.
    atom_columns = {row["name"] for row in conn.execute("PRAGMA table_info(atoms)").fetchall()}
    for name, definition in (
        ("exceptions", "TEXT"),
        ("evidence_span", "TEXT"),
        ("evidence_start", "INTEGER"),
        ("evidence_end", "INTEGER"),
        ("source_hash", "TEXT"),
        ("extraction_model", "TEXT"),
        ("model_version", "TEXT"),
        ("extractor_version", "TEXT"),
        ("provenance_class", "TEXT"),
    ):
        if name not in atom_columns:
            conn.execute(f"ALTER TABLE atoms ADD COLUMN {name} {definition}")
    conn.commit()


def store_snapshot(url: str, content: bytes, normalized: str, adapter: str,
                   http_status: int, etag: str = "", last_modified: str = "",
                   policy_decision: str = "", robots_status: str = "",
                   content_type: str = "") -> int:
    conn = get_conn()
    source_id = url
    content_hash_str = hash_content(content)

    execute("INSERT OR IGNORE INTO sources(source_id, canonical_url, adapter_type) VALUES (?,?,?)",
            (source_id, url, adapter))

    cur = execute("SELECT id FROM sources WHERE source_id=?", (source_id,))
    source_row = cur.fetchone()
    if not source_row:
        return -1
    sid = source_row["id"]

    cur = execute("SELECT id FROM snapshots WHERE source_id=? AND content_hash=?",
                  (sid, content_hash_str))
    existing = cur.fetchone()
    if existing:
        conn.commit()
        return existing["id"]

    raw_path = str(ROOT / "data" / "kapif" / "snapshots" / f"{content_hash_str[:16]}.raw")
    Path(raw_path).parent.mkdir(parents=True, exist_ok=True)
    if not Path(raw_path).exists():
        Path(raw_path).write_bytes(content)

    execute("""INSERT INTO snapshots(source_id, canonical_url, retrieved_at, http_status,
        etag, last_modified, content_hash, adapter_type, robots_status,
        policy_decision, content_type, byte_length, raw_path)
        VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (sid, url, http_status, etag, last_modified, content_hash_str,
         adapter, robots_status, policy_decision, content_type, len(content), raw_path))
    snap_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    return snap_id


def store_atom(atom_type: str, statement: str, discipline: str = "",
               scope: str = "", confidence: str = "UNVERIFIED",
               version_dependency: str = "", conditions: str = "",
               exceptions: str = "", evidence_span: str = "",
               evidence_start: int | None = None, evidence_end: int | None = None,
               source_hash: str = "", extraction_model: str = "",
               model_version: str = "", extractor_version: str = "",
               provenance_class: str = "") -> int:
    conn = get_conn()
    execute("""INSERT INTO atoms(atom_type, statement, discipline, scope, conditions, exceptions,
        evidence_span, evidence_start, evidence_end, source_hash, extraction_model,
        model_version, extractor_version, confidence, version_dependency, provenance_class)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (atom_type, statement.strip(), discipline, scope, conditions, exceptions,
         evidence_span, evidence_start, evidence_end, source_hash, extraction_model,
         model_version, extractor_version, confidence, version_dependency, provenance_class))
    atom_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    return atom_id


def link_atom_source(atom_id: int, snapshot_id: int, support_type: str = "ASSERTED_BY"):
    conn = get_conn()
    execute("INSERT OR IGNORE INTO atom_sources(atom_id, snapshot_id, support_type) VALUES (?,?,?)",
            (atom_id, snapshot_id, support_type))
    conn.commit()


def delete_atom(atom_id: int) -> bool:
    """Delete an atom and its source links; vector cleanup is explicit in embeddings."""
    conn = get_conn()
    try:
        conn.execute("DELETE FROM atom_sources WHERE atom_id=?", (atom_id,))
        cur = conn.execute("DELETE FROM atoms WHERE id=?", (atom_id,))
        conn.commit()
        return cur.rowcount == 1
    except Exception:
        conn.rollback()
        raise


def store_contradiction(atom_a: int, atom_b: int, explanation: str = "",
                        resolution: str = "UNRESOLVED") -> int:
    if atom_a > atom_b:
        atom_a, atom_b = atom_b, atom_a
    conn = get_conn()
    execute("INSERT INTO contradictions(atom_a_id, atom_b_id, explanation, resolution) VALUES (?,?,?,?)",
            (atom_a, atom_b, explanation, resolution))
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    return cid


def store_experience(snapshot_id: int, context: str, goal: str, constraints: str = "",
                     initial_approach: str = "", failure: str = "", diagnosis: str = "",
                     repair: str = "", outcome: str = "", tradeoff: str = "",
                     transferable_principle: str = "", limitations: str = "") -> int:
    conn = get_conn()
    execute("""INSERT INTO external_experience(source_snapshot_id, context, goal, constraints,
        initial_approach, failure_observed, diagnosis, repair, outcome, tradeoff,
        transferable_principle, limitations) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (snapshot_id, context, goal, constraints, initial_approach, failure,
         diagnosis, repair, outcome, tradeoff, transferable_principle, limitations))
    eid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    return eid


def mark_stale(snapshot_id: int, atom_id: int, reason: str):
    execute("INSERT INTO stale_dependencies(snapshot_id, atom_id, stale_reason) VALUES (?,?,?)",
            (snapshot_id, atom_id, reason))
    commit()


def log_fetch(url: str, adapter: str, http_status: int = 0, bytes_fetched: int = 0,
              cache_hit: bool = False, rate_limit_status: str = "", robots_status: str = "",
              policy_decision: str = "", retry_count: int = 0, error: str = ""):
    execute("""INSERT INTO fetch_log(url, adapter, http_status, bytes_fetched, cache_hit,
        rate_limit_status, robots_status, policy_decision, retry_count, error)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (url, adapter, http_status, bytes_fetched, int(cache_hit),
         rate_limit_status, robots_status, policy_decision, retry_count, error))
    commit()


def search_atoms(query: str, limit: int = 20) -> list[dict]:
    # Simple LIKE search (FTS to be added after stable DB). Canon membership
    # is joined so callers can apply epistemic filtering without a second query.
    conn = get_conn()
    try:
        cur = execute("""SELECT a.*, (c.atom_id IS NOT NULL) AS in_canon FROM atoms a
            LEFT JOIN canon c ON c.atom_id = a.id
            WHERE a.statement LIKE ? OR a.discipline LIKE ? OR a.atom_type LIKE ?
            ORDER BY a.id DESC LIMIT ?""",
            (f"%{query}%", f"%{query}%", f"%{query}%", limit))
    except Exception:
        cur = execute("SELECT a.*, 0 AS in_canon FROM atoms a ORDER BY a.id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    return rows


def get_atom_with_sources(atom_id: int) -> dict[str, Any]:
    conn = get_conn()
    cur = execute("SELECT * FROM atoms WHERE id=?", (atom_id,))
    row = cur.fetchone()
    atom = dict(row) if row else {}

    cur = execute("""SELECT s.* FROM snapshots s
        JOIN atom_sources aas ON s.id = aas.snapshot_id
        WHERE aas.atom_id=?""", (atom_id,))
    atom["sources"] = [dict(r) for r in cur.fetchall()]
    return atom


def stats() -> dict[str, int]:
    tables = ["sources", "snapshots", "atoms", "contradictions", "canon",
              "external_experience", "foundry_experience", "stale_dependencies", "fetch_log"]
    result = {}
    for t in tables:
        try:
            cur = execute(f"SELECT COUNT(*) as c FROM {t}")
            result[t] = cur.fetchone()["c"]
        except Exception:
            result[t] = 0
    return result


# Initialize on import
try:
    init_db()
except Exception:
    pass