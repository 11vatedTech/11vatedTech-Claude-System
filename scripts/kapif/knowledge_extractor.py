#!/usr/bin/env python3
"""
KAPIF Knowledge Atom Extractor.

Extracts atomic typed objects from normalized content:
FACT, PRINCIPLE, PROCEDURE, CONSTRAINT, FAILURE_PATTERN, DIAGNOSTIC, TRADEOFF,
TOOL_CAPABILITY, TOOL_LIMITATION, VERSION_FACT, LICENSE_FACT, PERFORMANCE_FACT,
DESIGN_PATTERN, ANTI_PATTERN, REFERENCE_PRINCIPLE, EXTERNAL_EXPERIENCE, OPEN_QUESTION.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from .data_layer import (
    link_atom_source,
    store_atom,
    store_contradiction,
    store_experience,
    get_atom_with_sources,
    search_atoms,
)


def extract_atoms(normalized_text: str, adapter: str = "generic",
                  discipline: str = "general", snapshot_id: int = -1) -> list[dict]:
    """Extract atomic knowledge from normalized text using regex patterns + heuristics.

    This is the initial lexical extractor. In production, an LLM-backed extractor
    would provide substantially higher quality. But the architecture supports it:
    the extractor interface is the same; only the implementation changes.
    """
    atoms: list[dict] = []
    text = normalized_text

    # ── Version facts ──
    ver_patterns = [
        r"(version|v)\s*(\d+\.\d+(?:\.\d+)?)",
        r"(released|published|updated)\s+(\d{4}-\d{2}-\d{2})",
        r"(Python|Node|Blender|Unreal)\s+(\d+\.\d+(?:\.\d+)?)",
    ]
    for pat in ver_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            atoms.append({"type": "VERSION_FACT", "statement": m.group(0).strip()[:500],
                          "discipline": discipline})

    # ── License facts ──
    lic_patterns = [
        r"(licensed under|license[: ]*)\s*([A-Z][A-Za-z0-9 .+\-]+(?:License|\.0))",
        r"(Apache\s*2\.0|MIT|GPL[\-\s]?[23]\.0|BSD[\-\s]?[23][\-\s]?Clause|MPL[\-\s]?2\.0|CC0)",
        r"(open source|free software|proprietary|commercial license)",
    ]
    for pat in lic_patterns:
        for m in re.finditer(pat, text, re.IGNORECASE):
            atoms.append({"type": "LICENSE_FACT", "statement": m.group(0).strip()[:500],
                          "discipline": discipline})

    # ── Tool capabilities ──
    tool_pats = [
        r"((?:Blender|Unreal|Unreal Engine|Unity|Godot|Maya|Houdini|Substance|Photoshop|Illustrator|Figma|Penpot|Pixelorama|ComfyUI|Three\.js|React|Vue|Svelte|Next\.js|Node\.js|Python|Rust|C\+\+|TypeScript).{5,150}(?:supports|provides|allows|enables|can|features|capable))",
    ]
    for pat in tool_pats:
        for m in re.finditer(pat, text, re.IGNORECASE):
            atoms.append({"type": "TOOL_CAPABILITY", "statement": m.group(0).strip()[:500],
                          "discipline": discipline})

    # ── Constraints / Limitations ──
    limit_pats = [
        r"((?:does not (?:support|allow|work|handle)|cannot|limited to|maximum|minimum|requires at least|only works).{10,300})",
    ]
    for pat in limit_pats:
        for m in re.finditer(pat, text, re.IGNORECASE):
            atoms.append({"type": "TOOL_LIMITATION", "statement": m.group(0).strip()[:500],
                          "discipline": discipline})

    # ── Performance facts ──
    perf_pats = [
        r"((?:VRAM|memory|latency|throughput|FPS|frame time|milliseconds|nanoseconds|GB|MB|GHz).{5,200}(?:\d+\s*(?:GB|MB|ms|fps|%)))",
    ]
    for pat in perf_pats:
        for m in re.finditer(pat, text, re.IGNORECASE):
            atoms.append({"type": "PERFORMANCE_FACT", "statement": m.group(0).strip()[:500],
                          "discipline": discipline})

    # ── Principles ──
    principle_pats = [
        r"((?:key principle|core concept|fundamental|best practice|rule of thumb|golden rule|the most important).{10,300})",
    ]
    for pat in principle_pats:
        for m in re.finditer(pat, text, re.IGNORECASE):
            atoms.append({"type": "PRINCIPLE", "statement": m.group(0).strip()[:500],
                          "discipline": discipline})

    # ── Failure patterns ──
    failure_pats = [
        r"((?:common (?:mistake|pitfall|error|failure|bug)|avoid|don't|never|do not|watch out for|be careful).{10,300})",
    ]
    for pat in failure_pats:
        for m in re.finditer(pat, text, re.IGNORECASE):
            atoms.append({"type": "FAILURE_PATTERN", "statement": m.group(0).strip()[:500],
                          "discipline": discipline})

    # ── Store atoms ──
    stored = []
    for a in atoms[:50]:  # Cap per source
        atom_id = store_atom(
            atom_type=a["type"],
            statement=a["statement"],
            discipline=a.get("discipline", discipline),
            confidence="UNVERIFIED",
        )
        if snapshot_id > 0:
            link_atom_source(atom_id, snapshot_id)
        a["atom_id"] = atom_id
        stored.append(a)

    return stored


def extract_experience(normalized_text: str, snapshot_id: int = -1) -> dict[str, Any]:
    """Extract structured professional experience from postmortem/breakdown content.

    Looks for patterns: attempt → failure → diagnosis → repair → outcome.
    """
    text = normalized_text

    # Heuristic extraction
    context = ""
    goal = ""
    failure = ""
    diagnosis = ""
    repair = ""
    outcome = ""

    # Context: what project/team
    ctx_m = re.search(r"((?:team|studio|project|company|we|I)\s.{10,200}?(?:built|created|developed|worked on|shipped))", text, re.IGNORECASE)
    if ctx_m:
        context = ctx_m.group(0)[:500]

    # Goal
    goal_m = re.search(r"(?:goal|objective|wanted to|needed to|aim was|target)\s.{10,200}", text, re.IGNORECASE)
    if goal_m:
        goal = goal_m.group(0)[:500]

    # Failure
    fail_m = re.search(r"((?:problem|issue|bug|broke|failed|crashed|didn't work|wasn't working|encountered).{10,300})", text, re.IGNORECASE)
    if fail_m:
        failure = fail_m.group(0)[:500]

    # Diagnosis
    diag_m = re.search(r"((?:root cause|turned out|discovered|realized|found that|investigated|traced).{10,300})", text, re.IGNORECASE)
    if diag_m:
        diagnosis = diag_m.group(0)[:500]

    # Repair
    repair_m = re.search(r"((?:fixed|solved|resolved|changed|switched to|replaced|refactored|rewrote|patched).{10,300})", text, re.IGNORECASE)
    if repair_m:
        repair = repair_m.group(0)[:500]

    # Outcome
    outcome_m = re.search(r"((?:result|outcome|after|ended up|learned|lesson|takeaway).{10,300})", text, re.IGNORECASE)
    if outcome_m:
        outcome = outcome_m.group(0)[:500]

    has_enough = bool(context or goal or failure or repair)
    if not has_enough:
        return {"extracted": False, "reason": "insufficient_experience_patterns"}

    exp_id = store_experience(
        snapshot_id=snapshot_id,
        context=context, goal=goal,
        failure=failure, diagnosis=diagnosis,
        repair=repair, outcome=outcome,
    )

    return {
        "extracted": True,
        "experience_id": exp_id,
        "context": context,
        "goal": goal,
        "failure": failure,
        "diagnosis": diagnosis,
        "repair": repair,
        "outcome": outcome,
    }


def detect_contradictions() -> list[dict]:
    """Detect contradictions between known atoms (simple text overlap approach).

    In production, this would use semantic comparison via LLM review.
    For now, detects explicit contradictions like 'supports X' vs 'does not support X'.
    """
    contradictions = []
    # Find atoms where one asserts capability and another denies it
    capability_atoms = search_atoms("support provides allows enables", limit=50)
    limitation_atoms = search_atoms("does not cannot limited to", limit=50)

    for ca in capability_atoms:
        ca_text = ca.get("statement", "").lower()
        for la in limitation_atoms:
            la_text = la.get("statement", "").lower()
            # Simple: check if same tool/version mentioned
            ca_tools = set(re.findall(r"(blender|unreal|python|node|react|penpot|comfyui)", ca_text))
            la_tools = set(re.findall(r"(blender|unreal|python|node|react|penpot|comfyui)", la_text))
            if ca_tools & la_tools and ca["id"] != la["id"]:
                cid = store_contradiction(
                    ca["id"], la["id"],
                    explanation=f"Potential contradiction: capability vs limitation claim",
                )
                contradictions.append({
                    "id": cid,
                    "atom_a": ca["statement"][:100],
                    "atom_b": la["statement"][:100],
                })

    return contradictions[:20]  # Limit