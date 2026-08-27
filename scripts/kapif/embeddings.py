#!/usr/bin/env python3
"""Versioned real embeddings and durable atom-vector lifecycle for KAPIF."""
from __future__ import annotations

import json
import os
import sqlite3
import struct
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "kapif" / "kapif.db"
NINEROUTER_URL = os.environ.get("NINEROUTER_URL", "http://127.0.0.1:20128")
EMBEDDING_MODEL = os.environ.get("KAPIF_EMBEDDING_MODEL", "openrouter/nvidia/llama-nemotron-embed-vl-1b-v2:free")
MAX_INPUT_CHARS = 512
TIMEOUT_S = 15

_PROVIDER_STATUS: dict[str, Any] = {
    "available": None,
    "model": EMBEDDING_MODEL,
    "declared_dims": None,
    "observed_dims": None,
    "last_probe": None,
    "last_error": None,
}


def _get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS atom_vectors (
            atom_id INTEGER PRIMARY KEY,
            embedding BLOB NOT NULL,
            model TEXT NOT NULL,
            model_version TEXT,
            dims INTEGER NOT NULL,
            corpus_version TEXT NOT NULL DEFAULT 'kapif-atom-v1',
            corpus_hash TEXT,
            text_hash TEXT,
            index_created_at TEXT NOT NULL DEFAULT (datetime('now')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(atom_id) REFERENCES atoms(id) ON DELETE CASCADE
        )
    """)
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(atom_vectors)").fetchall()}
    for name, definition in (
        ("model_version", "TEXT"),
        ("corpus_version", "TEXT NOT NULL DEFAULT 'kapif-atom-v1'"),
        ("corpus_hash", "TEXT"),
        ("text_hash", "TEXT"),
        ("index_created_at", "TEXT"),
    ):
        if name not in columns:
            conn.execute(f"ALTER TABLE atom_vectors ADD COLUMN {name} {definition}")
    conn.execute("""
        CREATE TRIGGER IF NOT EXISTS atom_vectors_cleanup
        AFTER DELETE ON atoms BEGIN
            DELETE FROM atom_vectors WHERE atom_id = old.id;
        END
    """)
    conn.commit()
    return conn


def _request(texts: list[str]) -> dict[str, Any]:
    payload = json.dumps({"model": EMBEDDING_MODEL, "input": texts if len(texts) > 1 else texts[0]}).encode()
    req = urllib.request.Request(f"{NINEROUTER_URL}/v1/embeddings", data=payload,
                                 headers={"Content-Type": "application/json"})
    start = time.time()
    with urllib.request.urlopen(req, timeout=TIMEOUT_S * (2 if len(texts) > 1 else 1)) as resp:
        data = json.loads(resp.read())
    embeddings = [item.get("embedding", []) for item in sorted(data.get("data", []), key=lambda x: x.get("index", 0))]
    dims = len(embeddings[0]) if embeddings and embeddings[0] else 0
    return {"embeddings": embeddings, "dimensions": dims, "model_used": data.get("model", EMBEDDING_MODEL),
            "latency": round(time.time() - start, 3)}


def _probe_provider() -> bool:
    try:
        result = _request(["KAPIF embedding capability probe"])
        dims = result["dimensions"]
        _PROVIDER_STATUS.update({"available": bool(dims), "observed_dims": dims,
                                 "last_probe": time.strftime("%Y-%m-%dT%H:%M:%S"), "last_error": None})
        return bool(dims)
    except Exception as exc:
        _PROVIDER_STATUS.update({"available": False, "last_probe": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                 "last_error": str(exc)[:300]})
        return False


def is_available() -> bool:
    return _probe_provider() if _PROVIDER_STATUS["available"] is None else bool(_PROVIDER_STATUS["available"])


def get_status() -> dict[str, Any]:
    return dict(_PROVIDER_STATUS)


def embed_text(text: str) -> list[float] | None:
    if not is_available():
        return None
    try:
        result = _request([text[:MAX_INPUT_CHARS]])
        vec = result["embeddings"][0] if result["embeddings"] else []
        _PROVIDER_STATUS["observed_dims"] = len(vec)
        return vec or None
    except Exception as exc:
        _PROVIDER_STATUS["last_error"] = str(exc)[:300]
        return None


def embed_batch(texts: list[str]) -> list[list[float] | None]:
    if not is_available():
        return [None] * len(texts)
    try:
        result = _request([text[:MAX_INPUT_CHARS] for text in texts])
        _PROVIDER_STATUS["observed_dims"] = result["dimensions"]
        return [(v if v else None) for v in result["embeddings"]] + [None] * max(0, len(texts) - len(result["embeddings"]))
    except Exception as exc:
        _PROVIDER_STATUS["last_error"] = str(exc)[:300]
        return [None] * len(texts)


def _vec_to_blob(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _blob_to_vec(blob: bytes) -> list[float]:
    return list(struct.unpack(f"{len(blob) // 4}f", blob))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _upsert_vector(conn: sqlite3.Connection, atom_id: int, text: str, vec: list[float], corpus_version: str = "kapif-atom-v1") -> None:
    import hashlib
    text_hash = hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()
    conn.execute("""
        INSERT INTO atom_vectors(atom_id, embedding, model, model_version, dims, corpus_version, corpus_hash, text_hash, index_created_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        ON CONFLICT(atom_id) DO UPDATE SET embedding=excluded.embedding, model=excluded.model,
          model_version=excluded.model_version, dims=excluded.dims, corpus_version=excluded.corpus_version,
          corpus_hash=excluded.corpus_hash, text_hash=excluded.text_hash, index_created_at=datetime('now')
    """, (atom_id, _vec_to_blob(vec), EMBEDDING_MODEL, _PROVIDER_STATUS.get("observed_dims"),
          len(vec), corpus_version, None, text_hash))


def store_embedding(atom_id: int, text: str) -> bool:
    vec = embed_text(text)
    if vec is None:
        return False
    conn = _get_conn()
    try:
        _upsert_vector(conn, atom_id, text, vec)
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def store_embeddings_batch(atoms: list[dict]) -> int:
    if not atoms or not is_available():
        return 0
    vectors = embed_batch([a.get("statement", "") for a in atoms])
    conn = _get_conn()
    stored = 0
    try:
        for atom, vec in zip(atoms, vectors):
            if vec:
                _upsert_vector(conn, int(atom["id"]), atom.get("statement", ""), vec)
                stored += 1
        conn.commit()
        return stored
    except Exception:
        conn.rollback()
        return 0
    finally:
        conn.close()


def delete_embedding(atom_id: int) -> bool:
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM atom_vectors WHERE atom_id=?", (atom_id,))
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


def index_all_atoms() -> dict[str, Any]:
    """Index all real KAPIF atoms and refresh stale/missing vectors."""
    if not is_available():
        return {"status": "SEMANTIC_PROVIDER_UNAVAILABLE", "eligible_atoms": 0, "vectors_generated": 0, "vectors_failed": 0}
    conn = _get_conn()
    try:
        atoms = [dict(row) for row in conn.execute("SELECT id, statement FROM atoms WHERE statement IS NOT NULL AND statement != ''").fetchall()]
        existing = {row["atom_id"]: row for row in conn.execute("SELECT atom_id, model, dims, text_hash FROM atom_vectors").fetchall()}
    finally:
        conn.close()
    import hashlib
    stale = []
    for atom in atoms:
        text_hash = hashlib.sha256(atom["statement"].encode('utf-8', errors='replace')).hexdigest()
        prior = existing.get(atom["id"])
        if prior is None or prior["model"] != EMBEDDING_MODEL or prior["text_hash"] != text_hash:
            stale.append(atom)
    generated = store_embeddings_batch(stale)
    return {"status": "PASS", "eligible_atoms": len(atoms), "vectors_generated": generated,
            "vectors_failed": len(stale) - generated, "dimensions": _PROVIDER_STATUS.get("observed_dims"),
            "model": EMBEDDING_MODEL, "index_size": len(atoms)}


def semantic_search_real(query: str, limit: int = 20) -> list[dict]:
    if not is_available():
        return []
    query_vec = embed_text(query)
    if query_vec is None:
        return []
    conn = _get_conn()
    try:
        rows = []
        for row in conn.execute("SELECT atom_id, embedding, model, dims FROM atom_vectors WHERE model=?", (EMBEDDING_MODEL,)).fetchall():
            sim = cosine_similarity(query_vec, _blob_to_vec(row["embedding"]))
            atom = conn.execute("SELECT * FROM atoms WHERE id=?", (row["atom_id"],)).fetchone()
            if atom:
                result = dict(atom)
                result["_semantic_score"] = round(sim, 6)
                result["_retrieval_method"] = "semantic"
                rows.append(result)
        rows.sort(key=lambda x: x["_semantic_score"], reverse=True)
        return rows[:limit]
    finally:
        conn.close()
