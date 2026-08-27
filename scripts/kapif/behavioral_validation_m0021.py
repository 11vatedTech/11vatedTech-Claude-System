#!/usr/bin/env python3
"""Primary behavioral evidence harness for KAPIF M002.1.

This runner deliberately reports NOT_RUN/BLOCKED instead of converting missing
runtime evidence into a structural pass. It uses an isolated temporary SQLite
installation for migration and lifecycle tests, then optionally benchmarks the
real corpus through the configured 9Router.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
SET_DIR = ROOT / "data" / "kapif" / "golden-sets"
OUT = ROOT / "artifacts" / "kapif" / "m002.1"


def _result(name: str, status: str, **evidence: Any) -> dict[str, Any]:
    return {"gate": name, "status": status, **evidence}


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_reference_evidence() -> dict[str, Any]:
    manifest_path = SET_DIR / "freeze-manifest.json"
    if not manifest_path.exists():
        return _result("frozen_reference_sets", "BLOCKED", reason="freeze manifest missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    checks = []
    for name, item in manifest.get("sets", {}).items():
        path = ROOT / item["path"]
        actual = _hash(path) if path.exists() else None
        checks.append({"name": name, "path": str(path), "expected": item.get("sha256"),
                       "actual": actual, "match": actual == item.get("sha256")})
    return _result("frozen_reference_sets", "PASS" if all(c["match"] for c in checks) else "FAIL", checks=checks)


def isolated_schema_and_fts() -> dict[str, Any]:
    """Exercise fresh and pre-M002 schemas without deleting the real database."""
    from kapif import db, data_layer
    from kapif.fts_index import init_fts, fts_search, rebuild_fts
    from kapif.canon_pipeline import init_canon_tables

    original = db.DB_PATH
    with tempfile.TemporaryDirectory(prefix="kapif-m0021-") as tmp:
        db.DB_PATH = Path(tmp) / "kapif.db"
        db.close_conn()
        try:
            # Fresh installation.
            data_layer.init_db()
            fresh_fts = init_fts()
            init_canon_tables()
            fresh_columns = {r["name"] for r in db.get_conn().execute("PRAGMA table_info(atoms)")}

            # Existing/pre-M002 fixture: deliberately omit exceptions and
            # canon verification columns, then rerun the same migrations.
            db.close_conn()
            legacy_path = Path(tmp) / "legacy.db"
            db.DB_PATH = legacy_path
            conn = db.get_conn()
            conn.executescript("""
              CREATE TABLE atoms (id INTEGER PRIMARY KEY, atom_type TEXT NOT NULL,
                statement TEXT NOT NULL, discipline TEXT, scope TEXT, conditions TEXT,
                confidence TEXT, version_dependency TEXT, created_at TEXT);
              CREATE TABLE canon_promotions (id INTEGER PRIMARY KEY, atom_id INTEGER,
                state TEXT, validator TEXT);
              CREATE TABLE canon_revisions (id INTEGER PRIMARY KEY, atom_id INTEGER,
                previous_state TEXT, new_state TEXT, reason TEXT, changed_by TEXT);
              CREATE TABLE canon (atom_id INTEGER PRIMARY KEY, promoted_at TEXT,
                validator TEXT, confidence TEXT);
              INSERT INTO atoms(id, atom_type, statement, discipline) VALUES
                (1, 'FACT', 'legacy preserved atom', 'test');
            """)
            conn.commit()
            legacy_fts = init_fts()
            init_canon_tables()
            columns = {r["name"] for r in conn.execute("PRAGMA table_info(atoms)")}
            promotion_columns = {r["name"] for r in conn.execute("PRAGMA table_info(canon_promotions)")}
            preserved = conn.execute("SELECT statement FROM atoms WHERE id=1").fetchone()[0]

            # Trigger behavior.
            cur = conn.execute("INSERT INTO atoms(atom_type, statement, discipline, scope, conditions, exceptions) VALUES (?,?,?,?,?,?)",
                               ("FACT", "fts lifecycle old text", "test", "scope", "old condition", "old exception"))
            atom_id = cur.lastrowid
            conn.commit()
            after_insert = bool(fts_search('"fts lifecycle old text"', limit=5))
            conn.execute("UPDATE atoms SET statement='fts lifecycle new text' WHERE id=?", (atom_id,))
            conn.commit()
            old_after_update = bool(fts_search('"fts lifecycle old text"', limit=5))
            new_after_update = bool(fts_search('"fts lifecycle new text"', limit=5))
            conn.execute("DELETE FROM atoms WHERE id=?", (atom_id,))
            conn.commit()
            after_delete = bool(fts_search('"fts lifecycle new text"', limit=5))
            rebuild = rebuild_fts()

            passed = (
                "exceptions" in fresh_columns and "exceptions" in columns and
                "verification_verdict" in promotion_columns and preserved == "legacy preserved atom" and
                after_insert and not old_after_update and new_after_update and not after_delete
            )
            return _result("schema_and_fts_behavior", "PASS" if passed else "FAIL",
                           fresh_migration=fresh_fts, legacy_migration=legacy_fts,
                           preserved_legacy_atom=preserved, trigger_trace={
                               "insert_visible": after_insert,
                               "old_text_after_update": old_after_update,
                               "new_text_after_update": new_after_update,
                               "new_text_after_delete": after_delete,
                           }, rebuild=rebuild)
        finally:
            db.close_conn()
            db.DB_PATH = original


def isolated_vector_lifecycle() -> dict[str, Any]:
    """Validate vector metadata/lifecycle using deterministic vectors locally."""
    from kapif import db, data_layer, embeddings
    original_db = db.DB_PATH
    original_embedding_db = embeddings.DB_PATH
    with tempfile.TemporaryDirectory(prefix="kapif-vectors-") as tmp:
        path = Path(tmp) / "vectors.db"
        db.DB_PATH = path
        embeddings.DB_PATH = path
        db.close_conn()
        try:
            data_layer.init_db()
            # Avoid a network call: this gate validates durable index behavior,
            # while provider quality is measured by the separate tournament.
            original_available = embeddings._PROVIDER_STATUS["available"]
            embeddings._PROVIDER_STATUS["available"] = True
            atom_id = data_layer.store_atom("FACT", "vector lifecycle original", "test")
            conn = embeddings._get_conn()
            vec = [1.0, 0.0, 0.0]
            embeddings._upsert_vector(conn, atom_id, "vector lifecycle original", vec)
            conn.commit()
            first = dict(conn.execute("SELECT atom_id, model, dims, corpus_version, text_hash FROM atom_vectors").fetchone())
            embeddings._upsert_vector(conn, atom_id, "vector lifecycle updated", [0.0, 1.0, 0.0])
            conn.commit()
            second = dict(conn.execute("SELECT atom_id, dims, text_hash FROM atom_vectors").fetchone())
            data_layer.delete_atom(atom_id)
            removed = conn.execute("SELECT COUNT(*) FROM atom_vectors WHERE atom_id=?", (atom_id,)).fetchone()[0] == 0
            passed = first["atom_id"] == atom_id and first["dims"] == 3 and first["corpus_version"] and second["text_hash"] != first["text_hash"] and removed
            return _result("vector_index_lifecycle", "PASS" if passed else "FAIL", first=first, refreshed=second, removed=removed)
        finally:
            embeddings._PROVIDER_STATUS["available"] = original_available
            embeddings.DB_PATH = original_embedding_db
            # _get_conn() owns a separate SQLite connection from kapif.db;
            # close it before TemporaryDirectory cleanup on Windows.
            try:
                conn.close()
            except (NameError, sqlite3.Error):
                pass
            db.close_conn()
            db.DB_PATH = original_db


def canon_trace() -> dict[str, Any]:
    from kapif import db, data_layer
    from kapif.canon_pipeline import (init_canon_tables, promote_candidate, validate_evidence,
                                      check_contradictions, verify_scope, verify_version,
                                      independent_verify, promote_to_canon)
    original = db.DB_PATH
    with tempfile.TemporaryDirectory(prefix="kapif-canon-") as tmp:
        db.DB_PATH = Path(tmp) / "canon.db"
        db.close_conn()
        try:
            data_layer.init_db()
            init_canon_tables()
            snap = data_layer.store_snapshot("https://example.test/canon", b"canon evidence", "canon evidence", "test", 200)
            atom = data_layer.store_atom("FACT", "A bounded canon claim", "testing", scope="test")
            data_layer.link_atom_source(atom, snap)
            pid = promote_candidate(atom, "test-extractor")
            trace = []
            def state():
                return db.get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()[0]
            trace.append({"function": "promote_candidate", "before": None, "after": state()})
            before = state(); blocked = not independent_verify(pid, "test-verifier", "SUPPORTED"); trace.append({"function": "independent_verify_wrong_state", "before": before, "return": not blocked, "after": state()})
            validate_evidence(pid, "test-evidence", "PASS", "source snapshot")
            check_contradictions(pid)
            verify_scope(pid, "testing scope")
            verify_version(pid, "v1")
            before = state(); verified = independent_verify(pid, "independent-verifier", "SUPPORTED"); trace.append({"function": "independent_verify", "before": before, "return": verified, "after": state()})
            before = state(); promoted = promote_to_canon(pid); canon_rows = db.get_conn().execute("SELECT COUNT(*) FROM canon WHERE atom_id=?", (atom,)).fetchone()[0]; trace.append({"function": "promote_to_canon", "before": before, "return": promoted, "after": state(), "canon_rows": canon_rows})
            passed = trace[1]["after"] == "CANDIDATE" and verified and promoted and trace[-1]["after"] == "CANONICAL" and canon_rows == 1
            return _result("canon_state_trace", "PASS" if passed else "FAIL", trace=trace)
        finally:
            db.close_conn(); db.DB_PATH = original


def run() -> dict[str, Any]:
    evidence = [frozen_reference_evidence()]
    try:
        evidence.extend([isolated_schema_and_fts(), isolated_vector_lifecycle(), canon_trace()])
    except Exception as exc:
        evidence.append(_result("isolated_behavioral_suite", "BLOCKED", error=f"{type(exc).__name__}: {exc}"))
    try:
        from kapif.security import taint_propagation_test
        taint = taint_propagation_test()
        evidence.append(_result("taint_propagation", "PASS" if taint.get("all_pass") else "FAIL", detail=taint))
    except Exception as exc:
        evidence.append(_result("taint_propagation", "BLOCKED", error=f"{type(exc).__name__}: {exc}"))
    summary = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0}
    for item in evidence:
        summary[item["status"]] = summary.get(item["status"], 0) + 1
    report = {"schema_version": 1, "kind": "m002.1-primary-behavioral-evidence", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "summary": summary, "evidence": evidence}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "behavioral-validation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
