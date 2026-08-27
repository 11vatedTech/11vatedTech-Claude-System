#!/usr/bin/env python3
"""Durable FTS5 migration and behavioral lexical search for KAPIF."""
from __future__ import annotations

import sqlite3
from typing import Any

from .db import get_conn, execute, commit

FTS_COLUMNS = ("statement", "discipline", "atom_type", "scope", "conditions", "exceptions")


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _ensure_atom_columns(conn: sqlite3.Connection) -> list[str]:
    """Add columns required by the FTS contract without deleting atom data."""
    added: list[str] = []
    columns = _table_columns(conn, "atoms")
    for name, definition in (
        ("conditions", "TEXT"),
        ("exceptions", "TEXT"),
    ):
        if name not in columns:
            conn.execute(f"ALTER TABLE atoms ADD COLUMN {name} {definition}")
            added.append(name)
    return added


def _fts_signature(conn: sqlite3.Connection) -> set[str]:
    try:
        return {row["name"] for row in conn.execute("PRAGMA table_info(atoms_fts)").fetchall()}
    except sqlite3.DatabaseError:
        return set()


def _drop_sync_triggers(conn: sqlite3.Connection) -> None:
    for name in ("atoms_fts_ai", "atoms_fts_ad", "atoms_fts_au"):
        conn.execute(f"DROP TRIGGER IF EXISTS {name}")


def _rebuild_virtual_table(conn: sqlite3.Connection) -> bool:
    """Recreate FTS when its schema or external-content index is incompatible."""
    signature = _fts_signature(conn)
    usable = False
    if signature and set(FTS_COLUMNS).issubset(signature):
        try:
            # A stale external-content FTS index can report the expected
            # columns while SQLite still considers its index malformed.
            conn.execute("SELECT count(*) FROM atoms_fts").fetchone()
            usable = True
        except sqlite3.DatabaseError:
            usable = False
    if usable:
        return False
    conn.execute("DROP TABLE IF EXISTS atoms_fts")
    conn.execute(
        "CREATE VIRTUAL TABLE atoms_fts USING fts5(" + ", ".join(FTS_COLUMNS) + ", content='atoms', content_rowid='id')"
    )
    return True


def init_fts() -> dict[str, Any]:
    """Run the idempotent FTS migration and return migration evidence.

    This works against both a fresh database and an existing M002 database.
    Existing atoms, sources, and canon rows are retained.
    """
    conn = get_conn()
    conn.execute("BEGIN")
    try:
        added_columns = _ensure_atom_columns(conn)
        _drop_sync_triggers(conn)
        recreated = _rebuild_virtual_table(conn)
        conn.execute("""
            CREATE TRIGGER atoms_fts_ai AFTER INSERT ON atoms BEGIN
                INSERT INTO atoms_fts(rowid, statement, discipline, atom_type, scope, conditions, exceptions)
                VALUES (new.id, new.statement, COALESCE(new.discipline,''), new.atom_type,
                        COALESCE(new.scope,''), COALESCE(new.conditions,''), COALESCE(new.exceptions,''));
            END
        """)
        conn.execute("""
            CREATE TRIGGER atoms_fts_ad AFTER DELETE ON atoms BEGIN
                INSERT INTO atoms_fts(atoms_fts, rowid, statement, discipline, atom_type, scope, conditions, exceptions)
                VALUES ('delete', old.id, old.statement, COALESCE(old.discipline,''), old.atom_type,
                        COALESCE(old.scope,''), COALESCE(old.conditions,''), COALESCE(old.exceptions,''));
            END
        """)
        conn.execute("""
            CREATE TRIGGER atoms_fts_au AFTER UPDATE ON atoms BEGIN
                INSERT INTO atoms_fts(atoms_fts, rowid, statement, discipline, atom_type, scope, conditions, exceptions)
                VALUES ('delete', old.id, old.statement, COALESCE(old.discipline,''), old.atom_type,
                        COALESCE(old.scope,''), COALESCE(old.conditions,''), COALESCE(old.exceptions,''));
                INSERT INTO atoms_fts(rowid, statement, discipline, atom_type, scope, conditions, exceptions)
                VALUES (new.id, new.statement, COALESCE(new.discipline,''), new.atom_type,
                        COALESCE(new.scope,''), COALESCE(new.conditions,''), COALESCE(new.exceptions,''));
            END
        """)
        # External-content FTS5 indexes must be rebuilt through the FTS5
        # control row. Direct DELETE/INSERT operations can leave a newly
        # created or legacy index reporting "database disk image is malformed".
        conn.execute("INSERT INTO atoms_fts(atoms_fts) VALUES ('rebuild')")
        conn.commit()
        return {
            "status": "PASS",
            "added_atom_columns": added_columns,
            "fts_recreated": recreated,
            "triggers_recreated": True,
            "existing_atoms_preserved": True,
        }
    except Exception:
        conn.rollback()
        raise


def rebuild_fts() -> dict[str, Any]:
    """Rebuild indexed contents while preserving the FTS schema and triggers."""
    conn = get_conn()
    conn.execute("INSERT INTO atoms_fts(atoms_fts) VALUES ('rebuild')")
    conn.commit()
    return {"status": "PASS", "reindexed": conn.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]}


def fts_search(query: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """FTS5/BM25 search; fallback is explicitly classified, never called semantic."""
    conn = get_conn()
    try:
        cur = conn.execute("""
            SELECT a.*, bm25(atoms_fts) AS bm25_score FROM atoms a
            JOIN atoms_fts ON a.id = atoms_fts.rowid
            WHERE atoms_fts MATCH ? ORDER BY bm25_score LIMIT ? OFFSET ?
        """, (query, limit, offset))
        return [dict(r) for r in cur.fetchall()]
    except sqlite3.DatabaseError:
        cur = conn.execute("""
            SELECT *, 0.0 AS bm25_score FROM atoms
            WHERE statement LIKE ? OR discipline LIKE ? OR atom_type LIKE ?
            ORDER BY id DESC LIMIT ? OFFSET ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", limit, offset))
        rows = [dict(r) for r in cur.fetchall()]
        for row in rows:
            row["_retrieval_degraded"] = True
            row["_retrieval_degraded_reason"] = "FTS5_UNAVAILABLE"
        return rows


def fts_count(query: str) -> int:
    try:
        return execute("SELECT COUNT(*) AS c FROM atoms_fts WHERE atoms_fts MATCH ?", (query,)).fetchone()["c"]
    except sqlite3.DatabaseError:
        return 0


try:
    init_fts()
except Exception:
    # Import must remain safe before a partially-created database is initialized.
    pass
