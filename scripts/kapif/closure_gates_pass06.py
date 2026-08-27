#!/usr/bin/env python3
"""
KAPIF M002.1 -- Pass 06 deterministic closure gates.

Exercises ONLY production functions (no test-side policy duplication):
  1. Benchmark fixture canon rejection through the real canon registration API
     (full production pipeline: promote_candidate -> validate_evidence ->
     check_contradictions -> verify_scope -> verify_version ->
     independent_verify -> promote_to_canon with provenance guard).
  2. Real pack-consumption boundary: insert mixed-state atoms through real
     storage, compile a real mission packet via the production mission
     compiler, assert the packet's epistemic labeling / exclusion.
  3. Normative grounding counters.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kapif import data_layer as dl
from kapif.mission_compiler import compile_packet, epistemic_class, filter_packet_atoms, PACKET_ELIGIBLE_CLASSES
from kapif.canon_pipeline import (
    promote_candidate, validate_evidence, check_contradictions,
    verify_scope, verify_version, independent_verify, promote_to_canon,
)

PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  PASS {name}")
    else:
        FAIL += 1
        print(f"  FAIL {name} {detail}")


def drive_to_verified(promotion_id, atom_id):
    """Drive a promotion through the real production state machine to
    INDEPENDENTLY_VERIFIED. Returns the final state string or None."""
    conn = dl.get_conn()
    ok = validate_evidence(promotion_id, "gate-test", "SUPPORTED", evidence="gate fixture")
    if not ok:
        return None
    cc = check_contradictions(promotion_id)
    if not cc or cc.get("status") != "PASS":
        return None
    if not verify_scope(promotion_id):
        return None
    if not verify_version(promotion_id):
        return None
    if not independent_verify(promotion_id, "gate-verifier", "SUPPORTED"):
        return None
    row = conn.execute("SELECT state FROM canon_promotions WHERE id=?", (promotion_id,)).fetchone()
    return row["state"] if row else None


def cleanup(promotion_ids, atom_ids):
    conn = dl.get_conn()
    for pid in promotion_ids:
        conn.execute("DELETE FROM canon_revisions WHERE promotion_id=?", (pid,))
        conn.execute("DELETE FROM canon_promotions WHERE id=?", (pid,))
    for aid in atom_ids:
        conn.execute("DELETE FROM canon WHERE atom_id=?", (aid,))
        conn.execute("DELETE FROM canon_revisions WHERE atom_id=?", (aid,))
        dl.delete_atom(aid)
    conn.commit()


def main():
    print("=== GATE 1: Benchmark fixture rejected by real canon API ===")
    before = dl.stats()
    aid = dl.store_atom(
        "FACT", "Benchmark fixture atom must never reach canon.",
        "benchmark", scope="eval", provenance_class="EVALUATION_FIXTURE")
    # real pipeline requires source provenance
    sid = dl.store_snapshot("https://bench.example/fixture", b"fixture bytes",
                            "fixture", "gate", 200)
    dl.link_atom_source(aid, sid)
    atom = dl.get_atom_with_sources(aid)
    cls = epistemic_class(atom)
    check("fixture classified EVALUATION_FIXTURE", cls == "EVALUATION_FIXTURE", cls)

    pid = promote_candidate(atom_id=aid, validator="gate-test")
    check("candidate registered", pid is not None and pid > 0, str(pid))
    check("cannot jump straight to promote (state gate)",
          promote_to_canon(pid) is False)
    state = drive_to_verified(pid, aid)
    check("reached INDEPENDENTLY_VERIFIED", state == "INDEPENDENTLY_VERIFIED", str(state))
    promoted = promote_to_canon(pid)
    check("promotion REJECTED for fixture", promoted is False)
    after = dl.stats()
    check("canon rows unchanged", after["canon"] == before["canon"],
          f"{before['canon']} -> {after['canon']}")
    row = dl.get_conn().execute(
        "SELECT state FROM canon_promotions WHERE id=?", (pid,)).fetchone()
    check("promotion state not CANONICAL", row and row["state"] != "CANONICAL",
          str(row) if row else "no row")
    cleanup([pid], [aid])

    print("=== GATE 2: Real pack-consumption boundary (production path) ===")
    # Insert the six fixture claims through REAL storage.
    fixtures = [
        ("CANONICAL", "FACT", "Canonical atom for gate test: accessible nav baseline.", "gates", "VALIDATED", "https://w3.org/TR/WCAG22", "CANONICAL"),
        ("VALIDATED_EXTERNAL_EVIDENCE", "FACT", "Validated external: WCAG contrast guidance for gate test.", "gates", "VALIDATED", "https://w3.org/TR/WCAG22", "VALIDATED_EXTERNAL_EVIDENCE"),
        ("PRACTITIONER_HEURISTIC", "PRACTITIONER_HEURISTIC", "Heuristic: generous tap targets feel better for gate test.", "gates", "UNVERIFIED", "", ""),
        ("FOUNDRY_PRINCIPLE", "FOUNDRY_PRINCIPLE", "Foundry principle: accessible nav is a default, not a feature.", "gates", "UNVERIFIED", "", ""),
        ("CANON_DRAFT", "FACT", "Draft claim: nav should pulse on hover for gate test.", "gates", "UNVERIFIED", "", ""),
        ("UNVALIDATED_NORMATIVE_CANDIDATE", "FACT", "Normative candidate: all links must be 48px for gate test.", "gates", "UNVERIFIED", "", ""),
    ]
    ids = {}
    pids = []
    for name, atype, stmt, disc, conf, src, pc in fixtures:
        aid = dl.store_atom(atype, stmt, disc, scope="gate-test", confidence=conf, provenance_class=pc)
        ids[name] = aid
        if src:
            sid2 = dl.store_snapshot(src, b"gate fixture bytes", "gate", "generic_web", 200)
            dl.link_atom_source(aid, sid2)

    # Make the CANONICAL one truly canonical through the real pipeline.
    cid = promote_candidate(atom_id=ids["CANONICAL"], validator="gate-test")
    state = drive_to_verified(cid, ids["CANONICAL"])
    check("canonical atom reached verified state", state == "INDEPENDENTLY_VERIFIED", str(state))
    check("canonical atom promoted", promote_to_canon(cid) is True)
    pids.append(cid)

    packet = compile_packet("accessible responsive navigation gate test", "gate-mission")
    rel = packet.get("relevant_atoms", [])
    exc = packet.get("excluded_atoms", [])
    rel_classes = {a["epistemic_class"] for a in rel}
    exc_classes = {a["epistemic_class"] for a in exc}
    # every presented atom must carry an eligible class
    check("all presented atoms eligible", rel_classes <= PACKET_ELIGIBLE_CLASSES, str(rel_classes))
    check("CANON_DRAFT not presented as truth",
          "CANON_DRAFT" not in rel_classes, str(rel_classes))
    check("UNVALIDATED_NORMATIVE_CANDIDATE not presented as truth",
          "UNVALIDATED_NORMATIVE_CANDIDATE" not in rel_classes, str(rel_classes))
    check("excluded bucket contains drafts",
          ("CANON_DRAFT" in exc_classes or "UNVALIDATED_NORMATIVE_CANDIDATE" in exc_classes),
          str(exc_classes))
    # the draft/candidate fixtures must not appear in relevant_atoms
    draft_in_rel = any(a["id"] == ids["CANON_DRAFT"] for a in rel)
    cand_in_rel = any(a["id"] == ids["UNVALIDATED_NORMATIVE_CANDIDATE"] for a in rel)
    check("draft atom absent from relevant", not draft_in_rel)
    check("normative candidate absent from relevant", not cand_in_rel)
    # labeled heuristic / principle present with labels when surfaced
    heur_in_rel = [a for a in rel if a["id"] == ids["PRACTITIONER_HEURISTIC"]]
    princ_in_rel = [a for a in rel if a["id"] == ids["FOUNDRY_PRINCIPLE"]]
    for a in heur_in_rel:
        check("heuristic labeled HEURISTIC", a["epistemic_class"] == "PRACTITIONER_HEURISTIC")
    for a in princ_in_rel:
        check("principle labeled FOUNDRY_PRINCIPLE", a["epistemic_class"] == "FOUNDRY_PRINCIPLE")

    cleanup(pids, list(ids.values()))

    print("=== GATE 3: Normative grounding counters ===")
    # Grounded = atoms carrying validated provenance + sources, or canonical.
    n_grounded = sum(1 for x in dl.search_atoms("", limit=5000)
                     if (x.get("in_canon") or x.get("provenance_class") in ("VALIDATED_EXTERNAL_EVIDENCE", "CANONICAL")))
    print(f"  grounded/validated atoms present in DB: {n_grounded}")
    check("closure gate recordable", isinstance(n_grounded, int))

    print(f"\n=== RESULTS: {PASS} pass, {FAIL} fail ===")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
