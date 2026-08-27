#!/usr/bin/env python3
"""
KAPIF Mission Knowledge Packet Compiler.

Compiles compact research packets for specific missions.
Does NOT dump hundreds of documents into Claude — aims for high information density.

Each packet contains:
  mission, research questions, relevant canon, fresh external evidence,
  important external experience, Foundry experience, contradictions,
  version-sensitive facts, tool/model constraints, confidence, citations, unknowns.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .data_layer import search_atoms, get_atom_with_sources, stats as db_stats
from .knowledge_extractor import detect_contradictions

# Epistemic classes a mission packet may present as established knowledge.
# Anything outside these is excluded from "relevant_atoms" so CANON_DRAFT /
# UNVALIDATED_NORMATIVE_CANDIDATE can never surface as professional truth.
PACKET_ELIGIBLE_CLASSES = {
    "CANONICAL",
    "VALIDATED_EXTERNAL_EVIDENCE",
    "PRODUCTION_PRACTICE",
    "PRACTITIONER_HEURISTIC",
    "FOUNDRY_PRINCIPLE",
}


HEURISTIC_ATOM_TYPES = {"PRACTITIONER_HEURISTIC", "HEURISTIC"}
PRINCIPLE_ATOM_TYPES = {"FOUNDRY_PRINCIPLE", "PRINCIPLE", "FOUNDRY_EXPERIENCE"}
NORMATIVE_ATOM_TYPES = {"FACT", "NORMATIVE", "PERFORMANCE_FACT", "PROCEDURE", "TOOL_CAPABILITY", "VERSION_FACT", "TOOL_LIMITATION", "TRADEOFF"}


def epistemic_class(atom: dict) -> str:
    """Production epistemic classifier for a knowledge atom.

    Order of precedence:
      1. provenance_class (e.g. EVALUATION_FIXTURE) if set explicitly.
      2. canon membership -> CANONICAL.
      3. validated external evidence (source-linked + validated confidence).
      4. heuristic / principle atom types keep their explicit class.
      5. normative-looking atoms without validation -> UNVALIDATED_NORMATIVE_CANDIDATE.
      6. everything else without validation -> CANON_DRAFT.
    """
    pc = (atom.get("provenance_class") or "").strip()
    if pc in ("EVALUATION_FIXTURE", "BENCHMARK_ONLY"):
        return "EVALUATION_FIXTURE"
    if pc:
        return pc
    # canon membership is decided by the canon table, not by atom_type
    if atom.get("in_canon"):
        return "CANONICAL"
    atom_type = (atom.get("atom_type") or "").strip().upper()
    if atom_type in HEURISTIC_ATOM_TYPES:
        return "PRACTITIONER_HEURISTIC"
    if atom_type in PRINCIPLE_ATOM_TYPES:
        return "FOUNDRY_PRINCIPLE"
    confidence = (atom.get("confidence") or "").strip().upper()
    if atom.get("sources"):
        if confidence in ("VALIDATED", "VERIFIED", "SUPPORTED", "LIKELY_SUPPORTED"):
            return "VALIDATED_EXTERNAL_EVIDENCE"
    if atom_type in NORMATIVE_ATOM_TYPES:
        return "UNVALIDATED_NORMATIVE_CANDIDATE"
    return "CANON_DRAFT"


def filter_packet_atoms(atoms: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split atoms into packet-eligible (labeled) and excluded (draft/candidate)."""
    eligible, excluded = [], []
    for a in atoms:
        cls = epistemic_class(a)
        a = dict(a)
        a["epistemic_class"] = cls
        if cls in PACKET_ELIGIBLE_CLASSES:
            eligible.append(a)
        else:
            excluded.append(a)
    return eligible, excluded


def compile_research_questions(intent: str) -> list[str]:
    """Generate explicit research questions from mission intent."""
    lower = intent.lower()
    questions = []

    # Version-sensitive questions
    if any(t in lower for t in ["unreal", "blender", "niagara", "python", "node", "penpot", "pixelorama"]):
        questions.append("What are the current version and breaking changes for the relevant tools?")

    if any(t in lower for t in ["license", "commercial", "comply"]):
        questions.append("What are the exact license terms and commercial conditions?")

    if any(t in lower for t in ["performance", "optimize", "fast", "fps", "memory"]):
        questions.append("What are the known performance constraints and optimization strategies?")

    if any(t in lower for t in ["vfx", "niagara", "particle", "effect"]):
        questions.append("What are the professional VFX design principles and common failure patterns?")

    if any(t in lower for t in ["frontend", "ui", "design", "interface", "visual",
                                "navigation", "responsive", "accessible", "a11y",
                                "web", "site", "layout", "page"]):
        questions.append("What are the relevant design principles, accessibility requirements, and professional patterns?")

    if any(t in lower for t in ["accessible", "accessibility", "a11y", "wcag", "contrast", "target size", "reduced motion"]):
        questions.append("What are the current WCAG 2.2 normative requirements and browser support for the relevant accessibility features?")

    if any(t in lower for t in ["responsive", "navigation", "mobile", "viewport", "breakpoint"]):
        questions.append("What are the professional responsive navigation patterns and their interaction/accessibility trade-offs?")

    if any(t in lower for t in ["performance", "optimize", "fast", "fps", "memory", "lcp", "inp", "cls", "core web vitals"]):
        questions.append("What are the known performance constraints and optimization strategies?")

    if any(t in lower for t in ["sprite", "pixel", "2d", "animation"]):
        questions.append("What are the professional pixel-art/sprite animation principles and pipeline constraints?")

    if any(t in lower for t in ["3d", "model", "mesh", "topology", "material", "pbr"]):
        questions.append("What are the professional 3D modeling/material/lookdev standards and constraints?")

    # Always add
    questions.append("What has changed recently that could affect this approach?")
    questions.append("What professional failure patterns exist in this domain?")

    return questions[:8]


def discover_unknown_disciplines(intent: str) -> list[str]:
    """Unknown-unknown discovery: find potentially missing professional disciplines."""
    lower = intent.lower()
    suggestions = []

    # Map of adjacent concerns
    adjacency = {
        "game": ["game design", "level design", "environment art", "game feel", "player psychology"],
        "niagara": ["causality", "overdraw", "GPU profiling", "gameplay readability", "material interaction"],
        "unreal": ["game design", "level design", "collision", "LOD", "performance profiling"],
        "frontend": ["typography", "responsive design", "accessibility", "performance budget", "design tokens"],
        "3d": ["topology", "UV", "baking", "LOD", "collision", "technical art"],
        "vfx": ["causality", "overdraw", "GPU profiling", "gameplay readability", "material interaction"],
        "animation": ["rigging", "skinning", "motion matching", "pose quality", "timing principles"],
        "design": ["art direction", "composition", "color theory", "typography", "accessibility"],
        "sprite": ["pixel clusters", "palette economy", "subpixel", "readability at scale", "spritesheet packing"],
    }

    for keyword, suggestions_list in adjacency.items():
        if keyword in lower:
            for s in suggestions_list:
                if s not in lower:
                    suggestions.append(s)

    return suggestions[:5]


def compile_packet(intent: str, mission_id: str = "mission-packet",
                   disciplines: list[str] | None = None) -> dict[str, Any]:
    """Compile a Mission Knowledge Packet."""
    questions = compile_research_questions(intent)
    unknowns = discover_unknown_disciplines(intent)
    disciplines = disciplines or ["general"]

    # Search for relevant atoms, then apply the production epistemic filter
    raw_atoms = []
    search_terms = intent.split()[:10]
    for term in search_terms:
        if len(term) > 3:
            atoms = search_atoms(term, limit=5)
            for a in atoms:
                if a["id"] not in {ra["id"] for ra in raw_atoms}:
                    raw_atoms.append(a)

    relevant_atoms, excluded_atoms = filter_packet_atoms(raw_atoms)

    # Find contradictions
    contradictions = detect_contradictions()

    # DB stats
    stats = db_stats()

    return {
        "packet_id": mission_id,
        "compiled_at": datetime.now().isoformat(),
        "intent": intent,
        "research_questions": questions,
        "potentially_missing_disciplines": unknowns,
        "relevant_atoms": [
            {"id": a["id"], "type": a["atom_type"], "statement": a["statement"][:200],
             "confidence": a["confidence"], "discipline": a["discipline"],
             "epistemic_class": a["epistemic_class"]}
            for a in relevant_atoms[:15]
        ],
        "excluded_atoms": [
            {"id": a["id"], "type": a["atom_type"], "statement": a["statement"][:120],
             "epistemic_class": a["epistemic_class"],
             "excluded_reason": "not packet-eligible epistemic class"}
            for a in excluded_atoms[:15]
        ],
        "contradictions_detected": len(contradictions),
        "contradiction_samples": [
            {"atom_a": c["atom_a"], "atom_b": c["atom_b"]} for c in contradictions[:3]
        ],
        "database_stats": stats,
        "note": "KAPIF Genesis — knowledge atoms are initial lexical extractions. Professional depth improves as the system acquires and validates more sources.",
        "citation_guidance": "Every externally derived claim retains provenance to source snapshot + canonical source. Ask: WHERE DID WE LEARN THIS? WHEN WAS IT VERIFIED? WHAT VERSION DOES IT APPLY TO? WHAT CONTRADICTS IT? HAS THE FOUNDRY PRACTICED IT?",
    }


def research_report(packet: dict[str, Any]) -> str:
    """Format a packet as a readable report."""
    lines = [
        f"KAPIF Research Packet: {packet['packet_id']}",
        f"Compiled: {packet['compiled_at']}",
        f"Intent: {packet['intent']}",
        "",
        "RESEARCH QUESTIONS:",
    ]
    for q in packet.get("research_questions", []):
        lines.append(f"  - {q}")

    lines.append("")
    lines.append("POTENTIALLY MISSING DISCIPLINES:")
    for d in packet.get("potentially_missing_disciplines", []):
        lines.append(f"  - {d}")

    lines.append("")
    lines.append(f"RELEVANT KNOWLEDGE ATOMS ({len(packet.get('relevant_atoms', []))}):")
    for a in packet.get("relevant_atoms", []):
        lines.append(f"  [{a['type']}] {a['statement'][:120]} ({a['confidence']})")

    lines.append("")
    lines.append(f"CONTRADICTIONS: {packet.get('contradictions_detected', 0)}")
    lines.append(f"DATABASE: {packet.get('database_stats', {})}")

    return "\n".join(lines)