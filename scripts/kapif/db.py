#!/usr/bin/env python3
"""Thread-safe connection manager for KAPIF SQLite database."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "kapif" / "kapif.db"

_local = threading.local()


def get_conn() -> sqlite3.Connection:
    """Get or create a thread-local SQLite connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=10000")
        _local.conn = conn
    return _local.conn


def close_conn():
    """Close the thread-local connection."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute SQL with retry on lock."""
    conn = get_conn()
    for attempt in range(3):
        try:
            return conn.execute(sql, params)
        except sqlite3.OperationalError as e:
            if "locked" in str(e) and attempt < 2:
                import time
                time.sleep(0.1 * (2 ** attempt))
                continue
            raise


def commit():
    get_conn().commit()