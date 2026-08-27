#!/usr/bin/env python3
"""
KAPIF Canon Pipeline — repaired state machine with:
- Idempotent schema migration
- Explicit state transitions (no state-jump bypasses)
- Atomic promotion (transaction)
- Golden task policy by knowledge class
- Correct taint semantics (extraction != trust)
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from .db import get_conn, execute, commit
from .data_layer import get_atom_with_sources, search_atoms, store_contradiction, store_atom, link_atom_source, store_snapshot

ROOT = Path(__file__).resolve().parents[2]

# ═══════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════

PROMOTION_STATES = [
    "CANDIDATE",
    "EVIDENCE_VALIDATED",
    "CONTRADICTION_CHECKED",
    "SCOPE_VERIFIED",
    "VERSION_VERIFIED",
    "INDEPENDENTLY_VERIFIED",
    "GOLDEN_TASK_PASSED",    # only for knowledge classes requiring it
    "CANONICAL",
]

CANCEL_STATES = [
    "SUPERSEDED",
    "RETRACTED",
    "CONTESTED",
    "VERSION_EXPIRED",
    "REVALIDATION_REQUIRED",
    "EVIDENCE_FAILED",
    "VERSION_FAILED",
    "VERIFICATION_FAILED",
]

VALID_TRANSITIONS = {
    "CANDIDATE":            ["EVIDENCE_VALIDATED", "EVIDENCE_FAILED"],
    "EVIDENCE_VALIDATED":   ["CONTRADICTION_CHECKED"],
    "CONTRADICTION_CHECKED":["SCOPE_VERIFIED"],
    "SCOPE_VERIFIED":       ["VERSION_VERIFIED", "VERSION_FAILED"],
    "VERSION_VERIFIED":     ["INDEPENDENTLY_VERIFIED", "VERIFICATION_FAILED"],
    "INDEPENDENTLY_VERIFIED":["GOLDEN_TASK_PASSED", "CANONICAL"],
    "GOLDEN_TASK_PASSED":   ["CANONICAL"],
    "CANONICAL":            ["SUPERSEDED", "RETRACTED", "CONTESTED", "VERSION_EXPIRED", "REVALIDATION_REQUIRED"],
}

# Golden task policy: which knowledge classes require behavioral proof
GOLDEN_TASK_POLICY = {
    "NORMATIVE":              False,  # authoritative evidence sufficient
    "RESEARCH_SUPPORTED":     False,
    "PRODUCTION_PRACTICE":    True,
    "PRACTITIONER_HEURISTIC": True,
    "FOUNDRY_PRINCIPLE":      True,
    "FOUNDRY_EXPERIENCE":     True,
    "TOOL_CAPABILITY":        True,   # behavior matters
    "PROCEDURE":              True,
    "DESIGN_PATTERN":         True,
    "VERSION_FACT":           False,  # version evidence sufficient
    "LICENSE_FACT":           False,
    "PERFORMANCE_FACT":       True,   # measurement required
    "FAILURE_PATTERN":        True,
    "TRADEOFF":               True,
    "OPEN_QUESTION":          False,  # not canon-eligible
}

# ═══════════════════════════════════════════
# IDEMPOTENT SCHEMA MIGRATION
# ═══════════════════════════════════════════

_MIGRATION_VERSION = 2

def _get_schema_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("PRAGMA user_version").fetchone()
        return row[0] if row else 0
    except Exception:
        return 0

def migrate_canon_schema():
    """Idempotent schema migration for canon tables."""
    conn = get_conn()
    
    # Base tables (always idempotent via IF NOT EXISTS)
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS canon_promotions (
        id INTEGER PRIMARY KEY,
        atom_id INTEGER REFERENCES atoms(id),
        state TEXT DEFAULT 'CANDIDATE',
        validator TEXT,
        validation_evidence TEXT,
        contradiction_check_result TEXT,
        scope_check_result TEXT,
        version_check_result TEXT,
        golden_task_id TEXT,
        golden_task_required INTEGER DEFAULT 0,
        golden_task_result TEXT,
        independent_verifier TEXT,
        verification_verdict TEXT,
        promoted_at TEXT,
        superseded_by INTEGER REFERENCES atoms(id),
        retraction_reason TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS canon_revisions (
        id INTEGER PRIMARY KEY,
        atom_id INTEGER REFERENCES atoms(id),
        promotion_id INTEGER,
        previous_state TEXT,
        new_state TEXT,
        reason TEXT,
        changed_by TEXT,
        changed_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS canon (
        atom_id INTEGER PRIMARY KEY,
        promoted_at TEXT,
        validator TEXT,
        confidence TEXT,
        knowledge_class TEXT,
        superseded_at TEXT,
        retracted_at TEXT
    );
    """)
    
    # Idempotent column migrations inspect the live schema.  user_version is
    # advisory only because older installations may have partial migrations.
    def columns(table: str) -> set[str]:
        return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}

    for table, migrations in {
        "canon_promotions": [
            ("verification_verdict", "TEXT"),
            ("independent_verifier", "TEXT"),
            ("golden_task_required", "INTEGER DEFAULT 0"),
            ("golden_task_result", "TEXT"),
            ("scope_check_result", "TEXT"),
            ("version_check_result", "TEXT"),
        ],
        "canon": [
            ("knowledge_class", "TEXT"),
            ("superseded_at", "TEXT"),
            ("retracted_at", "TEXT"),
        ],
        "canon_revisions": [("promotion_id", "INTEGER")],
    }.items():
        existing = columns(table)
        for col, typedef in migrations:
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}")

    conn.execute(f"PRAGMA user_version = {_MIGRATION_VERSION}")
    conn.commit()


def init_canon_tables():
    """Initialize canon tables with migration."""
    migrate_canon_schema()


# ═══════════════════════════════════════════
# STATE TRANSITION HELPERS
# ═══════════════════════════════════════════

def _valid_transition(promotion_id: int, required_from: str | list[str], new_state: str) -> bool:
    """Validate and execute state transition. Returns False if blocked."""
    if isinstance(required_from, str):
        required_from = [required_from]
    
    conn = get_conn()
    row = conn.execute("SELECT state FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row:
        return False
    
    current = row["state"]
    if current not in required_from:
        return False
    
    allowed = VALID_TRANSITIONS.get(current, [])
    if new_state not in allowed:
        return False
    
    conn.execute(
        "UPDATE canon_promotions SET state=?, updated_at=datetime('now') WHERE id=?",
        (new_state, promotion_id)
    )
    conn.commit()
    return True


def _record_revision(conn: sqlite3.Connection, promotion_id: int, atom_id: int,
                     prev_state: str, new_state: str, reason: str, changed_by: str):
    """Record state change in revision history."""
    conn.execute(
        "INSERT INTO canon_revisions(atom_id, promotion_id, previous_state, new_state, reason, changed_by) VALUES (?,?,?,?,?,?)",
        (atom_id, promotion_id, prev_state, new_state, reason, changed_by)
    )


# ═══════════════════════════════════════════
# PUBLIC API — ONE STEP AT A TIME
# ═══════════════════════════════════════════

def promote_candidate(atom_id: int, validator: str = "kapif-extractor") -> int:
    """Register an atom as a canon candidate. Always starts at CANDIDATE.
    
    Returns: promotion_id or -1 if atom lacks source provenance.
    Note: No caller-supplied state injection.
    """
    atom = get_atom_with_sources(atom_id)
    if not atom or not atom.get("sources"):
        return -1
    
    conn = get_conn()
    atom_type = atom.get("atom_type", "UNKNOWN")
    golden_required = int(GOLDEN_TASK_POLICY.get(atom_type, False))
    cur = conn.execute(
        "INSERT INTO canon_promotions(atom_id, state, validator, golden_task_required) VALUES (?, 'CANDIDATE', ?, ?)",
        (atom_id, validator, golden_required)
    )
    conn.commit()
    return cur.lastrowid


def validate_evidence(promotion_id: int, validator: str,
                      result: str = "PASS", evidence: str = "") -> bool:
    """Step 1: Evidence validation — source provenance intact AND result is PASS.
    
    FAIL/PARTIAL/UNSUPPORTED block advancement.
    Requires state == CANDIDATE.
    """
    conn = get_conn()
    row = conn.execute("SELECT state, atom_id FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row or row["state"] != "CANDIDATE":
        return False
    
    # Evidence result must be positive
    if result.upper() not in ("PASS", "SUPPORTED"):
        _record_revision(conn, promotion_id, row["atom_id"], "CANDIDATE", "EVIDENCE_FAILED",
                        f"result={result}: {evidence}", validator)
        conn.execute(
            "UPDATE canon_promotions SET state='EVIDENCE_FAILED', validator=?, validation_evidence=?, updated_at=datetime('now') WHERE id=?",
            (validator, f"result={result}: {evidence}", promotion_id)
        )
        conn.commit()
        return False
    
    # Source must exist
    atom = get_atom_with_sources(row["atom_id"])
    if not atom or not atom.get("sources"):
        return False
    
    _record_revision(conn, promotion_id, row["atom_id"], "CANDIDATE", "EVIDENCE_VALIDATED",
                    evidence, validator)
    conn.execute(
        "UPDATE canon_promotions SET state='EVIDENCE_VALIDATED', validator=?, validation_evidence=?, updated_at=datetime('now') WHERE id=?",
        (validator, evidence, promotion_id)
    )
    conn.commit()
    return True


def check_contradictions(promotion_id: int) -> dict[str, Any]:
    """Step 2: Search for contradictions. Requires state == EVIDENCE_VALIDATED.
    
    Separates: relations, potential_conflicts, confirmed_contradictions.
    COMPLEMENTS does NOT cause has_contradictions=true.
    """
    conn = get_conn()
    row = conn.execute("SELECT state, atom_id FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row or row["state"] != "EVIDENCE_VALIDATED":
        return {"status": "BLOCKED", "detail": f"requires EVIDENCE_VALIDATED, got {row['state'] if row else 'NOT_FOUND'}"}
    
    atom = get_atom_with_sources(row["atom_id"])
    statement = atom.get("statement", "") if atom else ""
    
    similar = search_atoms(statement[:60], limit=10)
    relations = []
    potential_conflicts = []
    confirmed_contradictions = []
    unresolved_consequential = []

    for other in similar:
        if other["id"] == row["atom_id"]:
            continue
        other_atom = get_atom_with_sources(other["id"])
        relation = classify_relation(atom or {}, other_atom or other)
        item = {
            "other_atom": other["id"],
            "other_statement": other.get("statement", "")[:160],
            "classification": relation,
        }
        if relation == "CONTRADICTS":
            confirmed_contradictions.append(item)
        elif relation == "INSUFFICIENT_EVIDENCE":
            unresolved_consequential.append(item)
        elif relation in ("COMPLEMENTS", "DIFFERENT_SCOPE", "DIFFERENT_VERSION", "AGREES"):
            relations.append(item)
        else:
            potential_conflicts.append(item)

    # Similarity is only candidate generation. Complementary facts and
    # different scoped/versioned values are relations, not contradictions.
    has_blocking_issue = bool(confirmed_contradictions or unresolved_consequential)
    result = {
        "relations": relations,
        "potential_conflicts": potential_conflicts,
        "confirmed_contradictions": confirmed_contradictions,
        "unresolved_consequential_uncertainty": unresolved_consequential,
        "has_contradictions": bool(confirmed_contradictions),
        "blocking": has_blocking_issue,
    }
    new_state = "CONTESTED" if has_blocking_issue else "CONTRADICTION_CHECKED"

    _record_revision(conn, promotion_id, row["atom_id"], "EVIDENCE_VALIDATED", new_state,
                    json.dumps(result), "kapif-contradiction-engine")
    conn.execute(
        "UPDATE canon_promotions SET state=?, contradiction_check_result=?, updated_at=datetime('now') WHERE id=?",
        (new_state, json.dumps(result), promotion_id)
    )
    conn.commit()

    return {"status": "PASS" if not has_blocking_issue else "BLOCKED", **result,
            "new_state": new_state}


def verify_scope(promotion_id: int, scope_evidence: str = "") -> bool:
    """Step 3: Scope verification. Requires state == CONTRADICTION_CHECKED.
    
    Atom must have discipline or scope defined.
    """
    conn = get_conn()
    row = conn.execute("SELECT state, atom_id FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row or row["state"] != "CONTRADICTION_CHECKED":
        return False
    
    atom = get_atom_with_sources(row["atom_id"])
    if not atom or (not atom.get("discipline") and not atom.get("scope")):
        return False
    
    _record_revision(conn, promotion_id, row["atom_id"], "CONTRADICTION_CHECKED", "SCOPE_VERIFIED",
                    scope_evidence or atom.get("discipline", ""), "kapif-scope-verifier")
    
    conn.execute(
        "UPDATE canon_promotions SET state='SCOPE_VERIFIED', scope_check_result=?, updated_at=datetime('now') WHERE id=?",
        (scope_evidence or atom.get("discipline", ""), promotion_id)
    )
    conn.commit()
    return True


def verify_version(promotion_id: int, version_context: str = "") -> bool:
    """Step 4: Version verification. Requires state == SCOPE_VERIFIED.
    
    VERSION_FACT atoms require explicit version context.
    """
    conn = get_conn()
    row = conn.execute("SELECT state, atom_id FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row or row["state"] != "SCOPE_VERIFIED":
        return False
    
    atom = get_atom_with_sources(row["atom_id"])
    if atom.get("atom_type") == "VERSION_FACT" and not version_context:
        conn.execute(
            "UPDATE canon_promotions SET state='VERSION_FAILED', version_check_result='version-sensitive atom requires version context', updated_at=datetime('now') WHERE id=?",
            (promotion_id,)
        )
        conn.commit()
        return False
    
    _record_revision(conn, promotion_id, row["atom_id"], "SCOPE_VERIFIED", "VERSION_VERIFIED",
                    version_context or "non-version-sensitive", "kapif-version-verifier")
    
    conn.execute(
        "UPDATE canon_promotions SET state='VERSION_VERIFIED', version_check_result=?, updated_at=datetime('now') WHERE id=?",
        (version_context or "non-version-sensitive", promotion_id)
    )
    conn.commit()
    return True


def independent_verify(promotion_id: int, verifier: str,
                       verdict: str = "SUPPORTED") -> bool:
    """Step 5: Independent verification. Requires state == VERSION_VERIFIED.
    
    Only SUPPORTED/LIKELY_SUPPORTED advance. All others block.
    Uses separate model/context from extractor.
    """
    conn = get_conn()
    row = conn.execute("SELECT state, atom_id FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row or row["state"] != "VERSION_VERIFIED":
        return False
    
    if verdict.upper() not in ("SUPPORTED", "LIKELY_SUPPORTED"):
        _record_revision(conn, promotion_id, row["atom_id"], "VERSION_VERIFIED", "VERIFICATION_FAILED",
                        f"verdict={verdict}", verifier)
        conn.execute(
            "UPDATE canon_promotions SET state='VERIFICATION_FAILED', independent_verifier=?, verification_verdict=?, updated_at=datetime('now') WHERE id=?",
            (verifier, verdict, promotion_id)
        )
        conn.commit()
        return False
    
    _record_revision(conn, promotion_id, row["atom_id"], "VERSION_VERIFIED", "INDEPENDENTLY_VERIFIED",
                    f"verdict={verdict}", verifier)
    
    conn.execute(
        "UPDATE canon_promotions SET state='INDEPENDENTLY_VERIFIED', independent_verifier=?, verification_verdict=?, updated_at=datetime('now') WHERE id=?",
        (verifier, verdict, promotion_id)
    )
    conn.commit()
    return True


def golden_task_pass(promotion_id: int, golden_task_id: str, result: str = "PASS") -> bool:
    """Step 6 (conditional): Golden task pass. Requires state == INDEPENDENTLY_VERIFIED.
    
    Required for knowledge classes: PRODUCTION_PRACTICE, FOUNDRY_PRINCIPLE, etc.
    """
    conn = get_conn()
    row = conn.execute("SELECT state, atom_id FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row or row["state"] != "INDEPENDENTLY_VERIFIED":
        return False
    
    if result.upper() != "PASS":
        return False
    
    _record_revision(conn, promotion_id, row["atom_id"], "INDEPENDENTLY_VERIFIED", "GOLDEN_TASK_PASSED",
                    f"task={golden_task_id}, result={result}", "kapif-golden-task")
    
    conn.execute(
        "UPDATE canon_promotions SET state='GOLDEN_TASK_PASSED', golden_task_id=?, golden_task_result=?, updated_at=datetime('now') WHERE id=?",
        (golden_task_id, result, promotion_id)
    )
    conn.commit()
    return True


def promote_to_canon(promotion_id: int) -> bool:
    """Final step: Promote to CANONICAL. ATOMIC — state + canon insert in one transaction.
    
    Requires state == INDEPENDENTLY_VERIFIED or GOLDEN_TASK_PASSED.
    Checks golden_task_required policy.
    If required and absent: BLOCKS.
    """
    conn = get_conn()
    row = conn.execute("SELECT state, atom_id, golden_task_id FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    if not row:
        return False
    
    required_states = ("INDEPENDENTLY_VERIFIED", "GOLDEN_TASK_PASSED")
    if row["state"] not in required_states:
        return False
    
    # Check the policy captured at candidate registration. This prevents a
    # later policy edit from silently changing an in-flight promotion.
    atom = get_atom_with_sources(row["atom_id"])
    atom_type = atom.get("atom_type", "UNKNOWN") if atom else "UNKNOWN"

    # PRODUCTION GUARD: reject benchmark/evaluation fixtures from canon
    provenance_class = (atom or {}).get("provenance_class", None)
    if provenance_class in ("EVALUATION_FIXTURE", "BENCHMARK_ONLY"):
        _record_revision(conn, promotion_id, row["atom_id"], row["state"],
                        "BLOCKED", "benchmark fixture rejected", "kapif-canon-pipeline")
        return False
    policy_row = conn.execute("SELECT golden_task_required, golden_task_id, golden_task_result FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    gt_required = bool(policy_row["golden_task_required"])
    if gt_required and (row["state"] != "GOLDEN_TASK_PASSED" or policy_row["golden_task_result"] != "PASS"):
        return False

    # ATOMIC: single transaction
    try:
        conn.execute("BEGIN")
        
        # Update promotion state
        updated = conn.execute(
            "UPDATE canon_promotions SET state='CANONICAL', promoted_at=datetime('now'), updated_at=datetime('now') WHERE id=? AND state IN ('INDEPENDENTLY_VERIFIED','GOLDEN_TASK_PASSED')",
            (promotion_id,)
        )
        if updated.rowcount != 1:
            raise RuntimeError("canonical state transition affected zero rows")

        # Insert into canon table. Failure rolls back the state transition.
        inserted = conn.execute(
            "INSERT OR REPLACE INTO canon(atom_id, promoted_at, validator, confidence, knowledge_class) VALUES (?, datetime('now'), ?, 'VALIDATED', ?)",
            (row["atom_id"], "kapif-canon-pipeline", atom_type)
        )
        if inserted.rowcount != 1:
            raise RuntimeError("canon insert affected zero rows")
        
        _record_revision(conn, promotion_id, row["atom_id"], row["state"], "CANONICAL",
                        "atomic promotion", "kapif-canon-pipeline")
        
        conn.execute("COMMIT")
        return True
    except Exception:
        conn.execute("ROLLBACK")
        return False


def supersede_atom(atom_id: int, new_atom_id: int, reason: str) -> bool:
    """Mark a canonical atom as SUPERSEDED by new knowledge."""
    conn = get_conn()
    conn.execute(
        "UPDATE canon_promotions SET state='SUPERSEDED', superseded_by=?, retraction_reason=?, updated_at=datetime('now') WHERE atom_id=? AND state='CANONICAL'",
        (new_atom_id, reason, atom_id)
    )
    conn.execute(
        "UPDATE canon SET superseded_at=datetime('now') WHERE atom_id=?", (atom_id,)
    )
    conn.commit()
    return True


# ═══════════════════════════════════════════
# BYPASS TEST SUITE
# ═══════════════════════════════════════════

def run_canon_bypass_suite() -> dict[str, Any]:
    """Run adversarial state-jump tests. Expected: all BLOCK."""
    init_canon_tables()
    
    results = []
    
    # We need a real atom with sources to test against    # Create minimal fixture
    snap_id = store_snapshot(
        url="https://test.example.com/bypass",
        content=b"bypass test content",
        normalized="bypass test content normalized",
        adapter="test",
        http_status=200
    )
    atom_id = store_atom("FACT", "Test bypass atom", "test-discipline", confidence="UNVERIFIED")
    link_atom_source(atom_id, snap_id)
    
    # Test 1: validate_evidence from non-CANDIDATE state
    pid = promote_candidate(atom_id, "test")
    validate_evidence(pid, "test", "PASS")
    # Now in EVIDENCE_VALIDATED — trying to validate again should fail
    r1 = validate_evidence(pid, "test", "PASS")
    results.append({"test": "validate_evidence_from_wrong_state", "blocked": not r1})
    
    # Test 2: check_contradictions from CANDIDATE (should fail — needs EVIDENCE_VALIDATED)
    pid2 = promote_candidate(atom_id, "test")
    r2 = check_contradictions(pid2)
    results.append({"test": "check_contradictions_from_candidate", "blocked": r2.get("status") == "BLOCKED"})
    
    # Test 3: verify_scope from CANDIDATE
    pid3 = promote_candidate(atom_id, "test")
    r3 = verify_scope(pid3)
    results.append({"test": "verify_scope_from_candidate", "blocked": not r3})
    
    # Test 4: verify_version from CANDIDATE
    pid4 = promote_candidate(atom_id, "test")
    r4 = verify_version(pid4)
    results.append({"test": "verify_version_from_candidate", "blocked": not r4})
    
    # Test 5: independent_verify from CANDIDATE
    pid5 = promote_candidate(atom_id, "test")
    r5 = independent_verify(pid5, "test")
    results.append({"test": "independent_verify_from_candidate", "blocked": not r5})
    
    # Test 6: promote_to_canon from CANDIDATE
    pid6 = promote_candidate(atom_id, "test")
    r6 = promote_to_canon(pid6)
    results.append({"test": "promote_to_canon_from_candidate", "blocked": not r6})
    
    # Test 7: promote_candidate with arbitrary state (should always be CANDIDATE)
    pid7 = promote_candidate.__wrapped__(atom_id, "test") if hasattr(promote_candidate, '__wrapped__') else promote_candidate(atom_id, "test")
    conn = get_conn()
    state7 = conn.execute("SELECT state FROM canon_promotions WHERE id=?", (pid7,)).fetchone()
    results.append({"test": "no_state_injection", "blocked": state7 and state7["state"] == "CANDIDATE"})
    
    # Test 8: wrong-state verification attempt
    pid8 = promote_candidate(atom_id, "test")
    r8a = independent_verify(pid8, "test", "SUPPORTED")  # CANDIDATE → should fail
    r8b = independent_verify(pid8, "test", "UNSUPPORTED")  # CANDIDATE → should fail
    results.append({"test": "independent_verify_wrong_state", "blocked": not r8a and not r8b})
    
    # Test 9: validate_evidence with FAIL result
    pid9 = promote_candidate(atom_id, "test")
    r9 = validate_evidence(pid9, "test", "FAIL", "evidence insufficient")
    state9 = conn.execute("SELECT state FROM canon_promotions WHERE id=?", (pid9,)).fetchone()
    results.append({"test": "validate_evidence_blocks_on_fail",
                    "blocked": not r9 and state9["state"] == "EVIDENCE_FAILED"})
    
    all_pass = all(r["blocked"] for r in results)
    
    return {
        "suite": "canon_bypass_v1",
        "tests": results,
        "total": len(results),
        "passed": sum(1 for r in results if r["blocked"]),
        "all_pass": all_pass,
    }


def run_valid_canon_path() -> dict[str, Any]:
    """Run one complete valid end-to-end canon promotion."""
    init_canon_tables()
    
    snap_id = store_snapshot(
        url="https://test.example.com/valid",
        content=b"valid path test content",
        normalized="valid path test content normalized",
        adapter="test",
        http_status=200
    )
    atom_id = store_atom("FACT", "Test valid canon path atom", "test-discipline",
                         confidence="UNVERIFIED", scope="test-scope")
    link_atom_source(atom_id, snap_id)
    
    path = []
    
    # Step 1: CANDIDATE
    pid = promote_candidate(atom_id, "test-extractor")
    state = get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()["state"]
    path.append({"step": "promote_candidate", "state": state})
    
    # Step 2: EVIDENCE_VALIDATED
    ok = validate_evidence(pid, "test-evidence-validator", "PASS", "source provenance intact")
    state = get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()["state"]
    path.append({"step": "validate_evidence", "state": state, "ok": ok})
    
    # Step 3: CONTRADICTION_CHECKED
    cr = check_contradictions(pid)
    state = get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()["state"]
    path.append({"step": "check_contradictions", "state": state})
    
    # Step 4: SCOPE_VERIFIED
    ok = verify_scope(pid, "test-discipline")
    state = get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()["state"]
    path.append({"step": "verify_scope", "state": state, "ok": ok})
    
    # Step 5: VERSION_VERIFIED
    ok = verify_version(pid, "v1.0")
    state = get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()["state"]
    path.append({"step": "verify_version", "state": state, "ok": ok})
    
    # Step 6: INDEPENDENTLY_VERIFIED
    ok = independent_verify(pid, "test-verifier-model", "SUPPORTED")
    state = get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()["state"]
    path.append({"step": "independent_verify", "state": state, "ok": ok})
    
    # Step 7: CANONICAL (atomic)
    ok = promote_to_canon(pid)
    state = get_conn().execute("SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()["state"]
    canon = get_conn().execute("SELECT * FROM canon WHERE atom_id=?", (atom_id,)).fetchone()
    path.append({"step": "promote_to_canon", "state": state, "ok": ok, "canon_exists": canon is not None})
    
    final_state = state
    canon_present = canon is not None
    
    return {
        "path": path,
        "final_state": final_state,
        "canon_inserted": canon_present,
        "success": final_state == "CANONICAL" and canon_present,
    }


def promotion_stats() -> dict[str, int]:
    """Get counts by state."""
    conn = get_conn()
    cur = conn.execute("SELECT state, COUNT(*) as cnt FROM canon_promotions GROUP BY state")
    return {row["state"]: row["cnt"] for row in cur.fetchall()}


def quality_metrics() -> dict[str, Any]:
    """Get quality metrics from canon data."""
    conn = get_conn()
    stats = promotion_stats()
    total = sum(stats.values())
    canonical = stats.get("CANONICAL", 0)
    failed = stats.get("EVIDENCE_FAILED", 0) + stats.get("VERSION_FAILED", 0) + stats.get("VERIFICATION_FAILED", 0)
    
    return {
        "total_promotions": total,
        "canonical": canonical,
        "failed": failed,
        "success_rate": canonical / total if total > 0 else 0,
        "by_state": stats,
    }


def get_canonical_atoms(limit: int = 50) -> list[dict]:
    """Get all canonical atoms."""
    conn = get_conn()
    cur = conn.execute("""
        SELECT c.*, a.statement, a.atom_type, a.discipline 
        FROM canon c JOIN atoms a ON c.atom_id = a.id 
        WHERE c.superseded_at IS NULL 
        ORDER BY c.promoted_at DESC LIMIT ?
    """, (limit,))
    return [dict(row) for row in cur.fetchall()]


# ═══════════════════════════════════════════
# TANT SEMANTICS (Section 8)
# ═══════════════════════════════════════════

# Trust states: extraction does NOT reduce trust
TRUST_STATES = [
    "RAW_EXTERNAL",              # Original untrusted content
    "UNTRUSTED_DERIVATIVE",       # Extracted candidate — still untrusted
    "SCHEMA_VALIDATED",           # Passed schema validation — still untrusted
    "EVIDENCE_VERIFIED",          # Passed independent verification
    "CANON_ELIGIBLE",             # Passed all canon gates
    "CANONICAL_FOR_SCOPE",        # Promoted to canon for defined scope
]


# ═══════════════════════════════════════════
# CONTRADICTION CLASSIFICATION (Section 7)
# ═══════════════════════════════════════════

CONTRADICTION_CLASSES = [
    "AGREES",
    "COMPLEMENTS",
    "DIFFERENT_SCOPE",
    "DIFFERENT_VERSION",
    "CONTRADICTS",
    "INSUFFICIENT_EVIDENCE",
]


def classify_relation(atom_a: dict, atom_b: dict) -> str:
    """Classify the relationship between two atoms.
    
    Returns one of: AGREES, COMPLEMENTS, DIFFERENT_SCOPE, DIFFERENT_VERSION, 
    CONTRADICTS, INSUFFICIENT_EVIDENCE
    """
    stmt_a = atom_a.get("statement", "").lower()
    stmt_b = atom_b.get("statement", "").lower()
    
    # Compare subjects (first 5 words)
    words_a = set(stmt_a.split()[:5])
    words_b = set(stmt_b.split()[:5])
    subject_overlap = len(words_a & words_b)
    
    if subject_overlap < 2:
        return "INSUFFICIENT_EVIDENCE"
    
    # Check for numeric values
    import re
    nums_a = set(re.findall(r'(\d+\.?\d*)\s*(?:px|pt|ms|s|%|css)', stmt_a))
    nums_b = set(re.findall(r'(\d+\.?\d*)\s*(?:px|pt|ms|s|%|css)', stmt_b))
    
    if nums_a and nums_b:
        if nums_a == nums_b:
            return "AGREES"
        # Numeric difference is not contradiction. Explicit scope/version
        # differences are classified; otherwise remain complementary until a
        # semantic verifier establishes incompatible assertions.
        scope_a = atom_a.get("scope", "") or atom_a.get("discipline", "")
        scope_b = atom_b.get("scope", "") or atom_b.get("discipline", "")
        version_a = atom_a.get("version_dependency", "")
        version_b = atom_b.get("version_dependency", "")
        if scope_a != scope_b:
            return "DIFFERENT_SCOPE"
        if version_a != version_b and (version_a or version_b):
            return "DIFFERENT_VERSION"
        return "COMPLEMENTS"
    
    # Same topic, no conflicting numbers
    if stmt_a == stmt_b:
        return "AGREES"
    
    return "COMPLEMENTS"
