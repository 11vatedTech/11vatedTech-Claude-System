#!/usr/bin/env python3
"""
KAPIF Orchestrator — main entry point for knowledge acquisition missions.

Evergreen mode: maintain strategic knowledge (tool releases, standards, licenses, core canon).
Mission mode: triggered by actual Founder mission — acquires only what is needed.

Implements acquisition budgets, stale dependency propagation, and frontier discovery.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .adapters import get_adapter, ADAPTERS
from .knowledge_extractor import extract_atoms, extract_experience
from .mission_compiler import compile_packet, research_report
from .data_layer import (
    mark_stale, stats as db_stats, search_atoms, get_atom_with_sources,
)
from .adapter_interface import FetchResult

ROOT = Path(__file__).resolve().parents[2]


class AcquisitionBudget:
    """Rate-limited, bounded acquisition control."""

    def __init__(self, max_sources: int = 20, max_requests: int = 50,
                 max_wall_time_s: int = 300, max_storage_mb: int = 50):
        self.max_sources = max_sources
        self.max_requests = max_requests
        self.max_wall_time_s = max_wall_time_s
        self.max_storage_mb = max_storage_mb
        self.sources_used = 0
        self.requests_used = 0
        self.storage_used_mb = 0.0

    def can_proceed(self) -> bool:
        if self.sources_used >= self.max_sources:
            return False
        if self.requests_used >= self.max_requests:
            return False
        if self.storage_used_mb >= self.max_storage_mb:
            return False
        return True

    def record_fetch(self, result: FetchResult):
        self.requests_used += 1
        if result.snapshot_id > 0:
            self.sources_used += 1
            self.storage_used_mb += len(result.raw_bytes) / (1024 * 1024)


def run_mission_acquisition(intent: str, budget: AcquisitionBudget | None = None) -> dict[str, Any]:
    """Run mission-directed acquisition: compile questions → acquire → extract → packet."""
    if budget is None:
        budget = AcquisitionBudget(max_sources=10, max_requests=20)

    from .mission_compiler import compile_research_questions
    questions = compile_research_questions(intent)

    results = []
    for q in questions[:3]:  # Top 3 questions
        if not budget.can_proceed():
            break

        # Try Crossref
        try:
            adapter = get_adapter("crossref")
            discoveries = getattr(adapter, "discover", lambda *a, **kw: [])(q, rows=2)
            for d in discoveries[:2]:
                if not budget.can_proceed():
                    break
                doi = d.get("doi")
                if doi:
                    fr = adapter.fetch_work(doi)
                    budget.record_fetch(fr)
                    if fr.snapshot_id > 0:
                        atoms = extract_atoms(fr.normalized_text, "crossref",
                                             "research", fr.snapshot_id)
                        exp = extract_experience(fr.normalized_text, fr.snapshot_id)
                        results.append({"source": "crossref", "doi": doi, "atoms": len(atoms),
                                       "experience": exp.get("extracted", False)})
        except Exception:
            pass

        # Try GitHub
        try:
            adapter = get_adapter("github")
            # Search for repos matching the question
            discoveries = getattr(adapter, "discover_repo", lambda *a, **kw: [])(q, per_page=2)
            for d in discoveries[:2]:
                if not budget.can_proceed():
                    break
                parts = d.get("full_name", "").split("/")
                if len(parts) == 2:
                    fr = getattr(adapter, "fetch_readme")(parts[0], parts[1])
                    budget.record_fetch(fr)
                    if fr.snapshot_id > 0:
                        atoms = extract_atoms(fr.normalized_text, "github",
                                             "engineering", fr.snapshot_id)
                        results.append({"source": "github", "repo": d["full_name"],
                                       "atoms": len(atoms)})
        except Exception:
            pass

    # Compile final packet
    packet = compile_packet(intent, mission_id="kapif-mission")
    packet["acquisition_results"] = results
    packet["budget"] = {
        "sources_used": budget.sources_used,
        "requests_used": budget.requests_used,
        "storage_mb": round(budget.storage_used_mb, 2),
    }

    return packet


def propagate_stale(snapshot_id: int, reason: str) -> int:
    """Mark downstream knowledge stale when source changes."""
    # Find atoms linked to this snapshot
    from .data_layer import _connect
    conn = _connect()
    cur = conn.execute("""
        SELECT atom_id FROM atom_sources WHERE snapshot_id=?
    """, (snapshot_id,))
    atom_ids = [r["atom_id"] for r in cur.fetchall()]
    conn.close()

    count = 0
    for aid in atom_ids:
        mark_stale(snapshot_id, aid, reason)
        count += 1

    return count


def frontier_scan() -> list[dict]:
    """Check adopted tools for new releases/changes."""
    tools_to_watch = [
        ("Blender", "https://www.blender.org/download/"),
        ("Unreal Engine", "https://www.unrealengine.com/en-US/blog"),
        ("Python", "https://www.python.org/downloads/"),
        ("Node.js", "https://nodejs.org/en/blog/"),
    ]

    findings = []
    for tool_name, url in tools_to_watch:
        try:
            adapter = get_adapter("generic_web")
            fr = adapter.fetch(url)
            if fr.snapshot_id > 0:
                atoms = extract_atoms(fr.normalized_text, "generic_web",
                                     "engineering", fr.snapshot_id)
                findings.append({"tool": tool_name, "atoms_extracted": len(atoms)})
        except Exception as e:
            findings.append({"tool": tool_name, "error": str(e)[:100]})

    return findings


def get_research_report(intent: str) -> str:
    """High-level research report from mission intent."""
    packet = compile_packet(intent)
    return research_report(packet)


# ── CLI ──

def main():
    import argparse
    parser = argparse.ArgumentParser(description="KAPIF — Knowledge Acquisition & Professional Intelligence Fabric")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("stats", help="Database statistics")
    sub.add_parser("init", help="Initialize database")

    search_p = sub.add_parser("search", help="Search knowledge atoms")
    search_p.add_argument("query")

    compile_p = sub.add_parser("compile", help="Compile mission knowledge packet")
    compile_p.add_argument("intent")

    acquire_p = sub.add_parser("acquire", help="Run mission acquisition")
    acquire_p.add_argument("intent")

    sub.add_parser("frontier", help="Run frontier scan")
    sub.add_parser("contradictions", help="Detect contradictions")

    args = parser.parse_args()

    if args.command == "init":
        from .data_layer import init_db
        init_db()
        print("KAPIF database initialized.")

    elif args.command == "stats":
        stats = db_stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "search":
        atoms = search_atoms(args.query, limit=10)
        for a in atoms:
            print(f"[{a['atom_type']}] {a['statement'][:150]} ({a['confidence']})")

    elif args.command == "compile":
        packet = compile_packet(args.intent)
        print(research_report(packet))

    elif args.command == "acquire":
        packet = run_mission_acquisition(args.intent)
        print(research_report(packet))

    elif args.command == "frontier":
        findings = frontier_scan()
        for f in findings:
            print(f"{f['tool']}: {f.get('atoms_extracted', f.get('error'))}")

    elif args.command == "contradictions":
        from .knowledge_extractor import detect_contradictions
        conts = detect_contradictions()
        for c in conts:
            print(f"  A: {c['atom_a']}")
            print(f"  B: {c['atom_b']}")
            print()

    else:
        stats = db_stats()
        print(f"KAPIF Genesis v0.1.0")
        print(f"Atoms: {stats.get('atoms', 0)}, Sources: {stats.get('sources', 0)}")
        print(f"Snapshots: {stats.get('snapshots', 0)}, Contradictions: {stats.get('contradictions', 0)}")
        print(f"External experiences: {stats.get('external_experience', 0)}")


if __name__ == "__main__":
    main()