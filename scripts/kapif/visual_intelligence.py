#!/usr/bin/env python3
"""
KAPIF Visual Reference Intelligence — governed visual-analysis pipeline.

Do NOT build a copyright-unsafe image hoard. Use lawfully accessible references.
Extract TRANSFERABLE DESIGN PRINCIPLES, not reproduction instructions.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .db import get_conn, execute, commit


# ── Visual reference record ──

@dataclass
class VisualReference:
    """Metadata for an analyzed visual reference."""
    source_url: str
    creator: str = ""
    studio: str = ""
    title: str = ""
    date: str = ""
    license_status: str = "UNKNOWN"  # ANALYSIS_ALLOWED, INTERNAL_REFERENCE_ONLY, etc.
    reference_purpose: str = ""
    reference_category: str = ""  # art_direction, frontend, typography, etc.
    image_hash: str = ""
    thumbnail_permission: bool = False
    analysis_model: str = ""
    analysis_model_version: str = ""
    analysis_date: str = ""
    extracted_principles: list[dict] = field(default_factory=list)
    what_not_to_copy: str = ""


USAGE_CLASSES = [
    "ANALYSIS_ALLOWED", "INTERNAL_REFERENCE_ONLY", "DERIVATIVE_USE_ALLOWED",
    "COMMERCIAL_ASSET_USE_ALLOWED", "ATTRIBUTION_REQUIRED", "UNKNOWN", "RESTRICTED",
]


# ── Professional visual analysis schema ──

VISUAL_DIMENSIONS = [
    "composition",
    "focal_hierarchy",
    "value_structure",
    "color_relationships",
    "shape_language",
    "silhouette",
    "typography",
    "grid",
    "spacing",
    "material_language",
    "lighting_language",
    "depth",
    "camera",
    "motion_language",
    "interaction_language",
    "visual_rhythm",
    "density",
    "style_coherence",
]

# What makes it distinctive (separate from literal description)
DISTINCTIVE_DIMENSIONS = [
    "what_makes_it_distinctive",
    "visual_thesis",
    "rule_breaking_choices",
    "unusual_combinations",
]


# ── Multimodal reviewer roles ──

REVIEWER_ROLES = {
    "art_direction": {
        "focus": "visual thesis, style coherence, creative direction, identity",
        "sample_questions": [
            "What is the visual thesis of this work?",
            "How do the design choices serve the intended emotional response?",
            "What rules does this design establish and where does it break them?",
        ],
    },
    "ui_design": {
        "focus": "interface hierarchy, affordance, clarity, visual system",
        "sample_questions": [
            "How does the visual hierarchy guide attention?",
            "How are interactive elements distinguished from static content?",
            "What is the density tradeoff — information per screen vs readability?",
        ],
    },
    "ux_screen": {
        "focus": "task flow, information scent, state visibility, error prevention",
        "sample_questions": [
            "Can the user understand what to do next?",
            "Is system state visible without explanation?",
            "What would fail first under real use?",
        ],
    },
    "composition": {
        "focus": "hierarchy, balance, rhythm, focal control, negative space",
        "sample_questions": [
            "How is the primary focal point established?",
            "What creates the rhythm of the composition?",
            "How does negative space contribute to clarity?",
        ],
    },
    "typography": {
        "focus": "type selection, hierarchy, measure, spacing, role assignment",
        "sample_questions": [
            "How are type roles assigned and distinguished?",
            "What makes the typographic hierarchy readable?",
            "How does type density serve the content purpose?",
        ],
    },
    "material": {
        "focus": "surface quality, light response, material distinction, consistency",
        "sample_questions": [
            "How do materials communicate function and history?",
            "Are material responses physically plausible where intended?",
            "What material language rules are consistently applied?",
        ],
    },
    "lighting": {
        "focus": "key light, fill, mood, visibility, focus direction",
        "sample_questions": [
            "How does lighting direct attention?",
            "What mood does the lighting strategy create?",
            "Is the lighting physically coherent?",
        ],
    },
    "sprite": {
        "focus": "clusters, silhouette, palette, animation readability, scale",
        "sample_questions": [
            "Is the silhouette readable at gameplay scale?",
            "How does the palette create form and depth?",
            "Does frame timing communicate weight and intent?",
        ],
    },
    "animation_frame": {
        "focus": "pose, timing, spacing, weight, anticipation, follow-through",
        "sample_questions": [
            "Is the pose readable as a still frame?",
            "Does the frame communicate the phase of motion?",
            "What indicates weight in this pose?",
        ],
    },
    "vfx_frame": {
        "focus": "causality, birth/life/death, readability, integration",
        "sample_questions": [
            "Is the cause of the effect visually clear?",
            "Can you distinguish birth, primary event, and dissipation?",
            "Does the effect integrate with the scene lighting?",
        ],
    },
}

# ── Visual reference pipeline ──


def store_visual_reference(ref: VisualReference) -> int:
    conn = get_conn()

    conn.executescript("""
    CREATE TABLE IF NOT EXISTS visual_references (
        id INTEGER PRIMARY KEY,
        source_url TEXT,
        creator TEXT, studio TEXT, title TEXT, date TEXT,
        license_status TEXT DEFAULT 'UNKNOWN',
        reference_purpose TEXT, reference_category TEXT,
        image_hash TEXT, thumbnail_permission INTEGER DEFAULT 0,
        analysis_model TEXT, analysis_model_version TEXT,
        analysis_date TEXT DEFAULT (datetime('now')),
        what_not_to_copy TEXT,
        extracted_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS visual_analysis_atoms (
        id INTEGER PRIMARY KEY,
        reference_id INTEGER REFERENCES visual_references(id),
        dimension TEXT NOT NULL,
        observation TEXT NOT NULL,
        principle TEXT,
        confidence TEXT DEFAULT 'UNVERIFIED',
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()

    image_hash = hashlib.sha256(
        f"{ref.source_url}{ref.title}{ref.date}".encode()
    ).hexdigest()[:16]

    cur = execute("""
        INSERT INTO visual_references(source_url, creator, studio, title, date,
            license_status, reference_purpose, reference_category, image_hash,
            thumbnail_permission, analysis_model, analysis_model_version, what_not_to_copy)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (ref.source_url, ref.creator, ref.studio, ref.title, ref.date,
          ref.license_status, ref.reference_purpose, ref.reference_category,
          image_hash, int(ref.thumbnail_permission),
          ref.analysis_model, ref.analysis_model_version, ref.what_not_to_copy))
    commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def store_visual_analysis(reference_id: int, dimension: str, observation: str,
                          principle: str = "", confidence: str = "UNVERIFIED") -> int:
    execute("""
        INSERT INTO visual_analysis_atoms(reference_id, dimension, observation, principle, confidence)
        VALUES (?,?,?,?,?)
    """, (reference_id, dimension, observation, principle, confidence))
    commit()
    return get_conn().execute("SELECT last_insert_rowid()").fetchone()[0]


def visual_analysis_schema() -> dict:
    """Return the visual analysis schema for use in prompts."""
    return {
        "dimensions": VISUAL_DIMENSIONS,
        "distinctive_dimensions": DISTINCTIVE_DIMENSIONS,
        "reviewer_roles": {
            role: info["focus"] for role, info in REVIEWER_ROLES.items()
        },
        "usage_classes": USAGE_CLASSES,
        "instruction": (
            "For each dimension, extract the TRANSFERABLE DESIGN PRINCIPLE, "
            "not a literal description. Do not generate reproduction instructions. "
            "What not to copy is as important as what to learn."
        ),
    }


# ── Temporal evidence schema ──


def temporal_evidence_schema() -> dict:
    """Schema for temporal observations (video, frame sequence, animation)."""
    return {
        "schema_version": 1,
        "observation_types": [
            "motion_phase",
            "contact_event",
            "timing_marker",
            "spacing_change",
            "anticipation_pose",
            "settle_point",
            "dissipation_event",
            "state_transition",
        ],
        "required_fields": {
            "timestamp_or_frame": "frame number or time offset",
            "event_type": "one of observation_types",
            "description": "what is observed",
            "significance": "why this matters professionally",
        },
        "note": "Full temporal intelligence deferred to later milestone. Schema established now for forward compatibility.",
    }


# ── Multimodal reviewer benchmark ──

def reviewer_benchmark_suite() -> dict:
    """Build a benchmark suite for multimodal reviewers."""
    return {
        "roles": list(REVIEWER_ROLES.keys()),
        "metrics": [
            "observation_accuracy",
            "visual_grounding",
            "causal_critique",
            "false_detail_hallucination",
            "repair_usefulness",
            "position_bias",
        ],
        "benchmark_queries": {
            "art_direction": [
                "Analyze the visual thesis of this design",
                "What makes this composition distinctive?",
                "How do the material and lighting choices serve the identity?",
            ],
            "ui_design": [
                "Evaluate the visual hierarchy",
                "How does typography create information structure?",
                "What is the density-readability trade?",
            ],
            "composition": [
                "Identify the primary focal path",
                "How does value structure create depth?",
                "What rhythm does the spacing create?",
            ],
            "typography": [
                "Analyze the type role assignment",
                "How does measure affect readability?",
                "What makes the hierarchy clear?",
            ],
            "sprite": [
                "Evaluate silhouette readability",
                "How does the palette create form?",
                "What does the frame timing communicate?",
            ],
        },
        "status": "SCHEMA_DEFINED — not yet executed against real multimodal models",
    }