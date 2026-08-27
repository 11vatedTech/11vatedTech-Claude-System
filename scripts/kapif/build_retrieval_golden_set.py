#!/usr/bin/env python3
"""
Build retrieval golden set with manually labeled relevance judgments.

30+ queries across 10 disciplines, each with:
- relevant atom source hashes (ground truth)
- graded relevance: 3=directly answers, 2=strongly useful, 1=adjacent, 0=irrelevant
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "kapif" / "golden-sets"

RETRIEVAL_GOLDEN = {
    "schema_version": 1,
    "kind": "retrieval_golden_set",
    "date": "2026-08-23",
    "total_queries": 32,
    "disciplines": [
        "frontend", "ui-ux", "art-direction", "materials",
        "animation", "vfx", "sprites", "unreal", "software-engineering", "research"
    ],
    "queries": [
        # ── Frontend ──
        {
            "query": "Core Web Vitals LCP threshold field measurement",
            "discipline": "frontend",
            "relevance_judgments": [
                {"atom_statement_contains": "LCP should be 2.5 seconds or less", "grade": 3, "reason": "Directly answers threshold and measurement context"},
                {"atom_statement_contains": "75th percentile of page loads", "grade": 3, "reason": "Directly answers field measurement methodology"},
                {"atom_statement_contains": "INP should be 200 milliseconds", "grade": 1, "reason": "Related performance metric but not LCP"}
            ]
        },
        {
            "query": "responsive typography hierarchy breakpoint behavior",
            "discipline": "frontend",
            "relevance_judgments": [
                {"atom_statement_contains": "Major Third scale", "grade": 2, "reason": "Provides type scale ratio useful for responsive hierarchy"},
                {"atom_statement_contains": "150% line height", "grade": 1, "reason": "Adjacent — line height relates to typography but not hierarchy"}
            ]
        },
        {
            "query": "CSS containment layout performance optimization",
            "discipline": "frontend",
            "relevance_judgments": [
                {"atom_statement_contains": "CSS containment limits browser layout", "grade": 3, "reason": "Directly answers containment purpose"},
                {"atom_statement_contains": "contain: layout isolates", "grade": 2, "reason": "Specific implementation detail, useful but narrow"}
            ]
        },
        # ── UI/UX ──
        {
            "query": "user freedom undo redo interaction pattern",
            "discipline": "ui-ux",
            "relevance_judgments": [
                {"atom_statement_contains": "clearly marked emergency exit", "grade": 3, "reason": "Directly addresses user control and freedom"},
                {"atom_statement_contains": "Support undo and redo", "grade": 3, "reason": "Specific pattern for user freedom"}
            ]
        },
        {
            "query": "touch event ordering mobile interaction sequence",
            "discipline": "ui-ux",
            "relevance_judgments": [
                {"atom_statement_contains": "touchstart, touchmove, touchend", "grade": 3, "reason": "Directly answers touch event order"},
                {"atom_statement_contains": "passive event listeners", "grade": 2, "reason": "Performance optimization relevant to touch handling"}
            ]
        },
        {
            "query": "usability testing five users diminishing returns",
            "discipline": "ui-ux",
            "relevance_judgments": [
                {"atom_statement_contains": "5 users reveals approximately 85%", "grade": 3, "reason": "Directly addresses the five-user finding"}
            ]
        },
        # ── Art Direction ──
        {
            "query": "visual hierarchy contrast budget focal point allocation",
            "discipline": "art-direction",
            "relevance_judgments": [
                {"atom_statement_contains": "visual hierarchy", "grade": 2, "reason": "Related concept but not about contrast budgets specifically"}
            ]
        },
        {
            "query": "color temperature spatial depth atmospheric perspective",
            "discipline": "art-direction",
            "relevance_judgments": [
                {"atom_statement_contains": "AgX provides wider dynamic range", "grade": 1, "reason": "Color science but not about spatial depth perception"}
            ]
        },
        # ── Materials ──
        {
            "query": "Fresnel effect dielectric F0 reflectance viewing angle",
            "discipline": "materials",
            "relevance_judgments": [
                {"atom_statement_contains": "Fresnel effect causes surface reflectance", "grade": 3, "reason": "Directly explains Fresnel"},
                {"atom_statement_contains": "base reflectivity (F0) of approximately 0.04", "grade": 3, "reason": "Directly provides F0 value for dielectrics"},
                {"atom_statement_contains": "Metals have F0 values ranging from 0.5 to 1.0", "grade": 2, "reason": "Complementary information about metals F0"}
            ]
        },
        {
            "query": "PBR energy conservation diffuse specular physical accuracy",
            "discipline": "materials",
            "relevance_judgments": [
                {"atom_statement_contains": "Energy conservation is a fundamental principle", "grade": 3, "reason": "Directly addresses energy conservation"},
                {"atom_statement_contains": "reflected (specular) plus absorbed (diffuse) cannot exceed", "grade": 3, "reason": "Defines the conservation constraint"}
            ]
        },
        {
            "query": "Blender Cycles tile size GPU CPU performance render",
            "discipline": "materials",
            "relevance_judgments": [
                {"atom_statement_contains": "GPU rendering is more efficient with larger tile", "grade": 3, "reason": "Directly addresses GPU tile size"},
                {"atom_statement_contains": "CPU rendering may perform better with smaller tile", "grade": 3, "reason": "Directly addresses CPU tile size"},
                {"atom_statement_contains": "AgX as the default display transform", "grade": 1, "reason": "Blender rendering related but about display, not tiles"}
            ]
        },
        {
            "query": "GLSL shader mix function gradient interpolation",
            "discipline": "materials",
            "relevance_judgments": [
                {"atom_statement_contains": "mix() function blends two values", "grade": 3, "reason": "Directly explains GLSL mix function"}
            ]
        },
        # ── Animation ──
        {
            "query": "prefers reduced motion accessibility non-essential animation",
            "discipline": "animation",
            "relevance_judgments": [
                {"atom_statement_contains": "prefers-reduced-motion detects user preference", "grade": 3, "reason": "Directly addresses the media query"}
            ]
        },
        {
            "query": "CSS SVG animation performance GPU acceleration browser",
            "discipline": "animation",
            "relevance_judgments": [
                {"atom_statement_contains": "passive event listeners improve scrolling", "grade": 1, "reason": "Performance-related but not animation-specific"},
                {"atom_statement_contains": "SVG graphics are resolution-independent", "grade": 1, "reason": "SVG related but not about animation performance"}
            ]
        },
        # ── VFX ──
        {
            "query": "Niagara particle GPU simulation million particles real-time",
            "discipline": "vfx",
            "relevance_judgments": [
                {"atom_statement_contains": "Niagara supports both GPU and CPU", "grade": 3, "reason": "Directly addresses GPU simulation capability"},
                {"atom_statement_contains": "GPU simulation enables processing millions", "grade": 3, "reason": "Directly addresses million-particle performance"}
            ]
        },
        {
            "query": "WebGL vertex fragment shader 3D rendering pipeline browser",
            "discipline": "vfx",
            "relevance_judgments": [
                {"atom_statement_contains": "vertex shader processes vertices", "grade": 3, "reason": "Directly explains WebGL shader pipeline"},
                {"atom_statement_contains": "WebGL uses GLSL shaders", "grade": 2, "reason": "Provides shader language context"}
            ]
        },
        # ── Sprites ──
        {
            "query": "pixel art sprite sheet frame animation timing",
            "discipline": "sprites",
            "relevance_judgments": []
        },
        {
            "query": "sprite pivot alignment pixel grid subpixel rendering",
            "discipline": "sprites",
            "relevance_judgments": []
        },
        # ── Unreal ──
        {
            "query": "Lumen global illumination dynamic bounces hardware ray tracing",
            "discipline": "unreal",
            "relevance_judgments": [
                {"atom_statement_contains": "Lumen provides dynamic global illumination", "grade": 3, "reason": "Directly addresses Lumen"},
                {"atom_statement_contains": "supports infinite bounces", "grade": 3, "reason": "Directly addresses bounce capability"},
                {"atom_statement_contains": "Hardware ray tracing can optionally be used", "grade": 2, "reason": "Complementary detail about HW RT"}
            ]
        },
        {
            "query": "Niagara data channels inter-system communication particle engine",
            "discipline": "unreal",
            "relevance_judgments": [
                {"atom_statement_contains": "data interfaces to communicate between particle", "grade": 2, "reason": "Addresses inter-system communication but not specifically data channels"}
            ]
        },
        # ── Software Engineering ──
        {
            "query": "SQLite WAL mode concurrent read write performance",
            "discipline": "software-engineering",
            "relevance_judgments": [
                {"atom_statement_contains": "WAL mode allows concurrent reads during writes", "grade": 3, "reason": "Directly addresses WAL concurrency"},
                {"atom_statement_contains": "multiple concurrent readers but only one writer", "grade": 2, "reason": "Provides constraint context"}
            ]
        },
        {
            "query": "Python asyncio concurrent programming async await coroutine",
            "discipline": "software-engineering",
            "relevance_judgments": [
                {"atom_statement_contains": "asyncio enables concurrent programming", "grade": 3, "reason": "Directly addresses asyncio capability"},
                {"atom_statement_contains": "event loop manages coroutine scheduling", "grade": 2, "reason": "Implementation detail useful for understanding"}
            ]
        },
        {
            "query": "Docker multi-stage build image optimization caching",
            "discipline": "software-engineering",
            "relevance_judgments": [
                {"atom_statement_contains": "Multi-stage Docker builds reduce final image", "grade": 3, "reason": "Directly addresses multi-stage builds"},
                {"atom_statement_contains": "Order Dockerfile instructions from least to most", "grade": 3, "reason": "Directly addresses build cache optimization"}
            ]
        },
        {
            "query": "git rebase interactive shared repository danger",
            "discipline": "software-engineering",
            "relevance_judgments": [
                {"atom_statement_contains": "Interactive rebasing allows changing", "grade": 2, "reason": "Explains rebase capability"},
                {"atom_statement_contains": "Do not rebase commits already pushed to shared", "grade": 3, "reason": "Directly addresses shared repo danger"}
            ]
        },
        {
            "query": "HTTP 429 rate limit Retry-After exponential backoff",
            "discipline": "software-engineering",
            "relevance_judgments": [
                {"atom_statement_contains": "HTTP 429 indicates", "grade": 3, "reason": "Directly defines 429"},
                {"atom_statement_contains": "Retry-After header indicates when to retry", "grade": 3, "reason": "Directly addresses retry behavior"}
            ]
        },
        {
            "query": "SVG viewBox coordinate system responsive scaling",
            "discipline": "software-engineering",
            "relevance_judgments": [
                {"atom_statement_contains": "SVG viewBox defines the coordinate system", "grade": 3, "reason": "Directly addresses viewBox"},
                {"atom_statement_contains": "SVG graphics are resolution-independent", "grade": 2, "reason": "Context about SVG scaling"}
            ]
        },
        # ── Research ──
        {
            "query": "design system token architecture component interface boundary",
            "discipline": "research",
            "relevance_judgments": []
        },
        {
            "query": "professional pack knowledge class normative practitioner heuristic",
            "discipline": "research",
            "relevance_judgments": []
        },
        {
            "query": "visual reference analysis composition shape language transferable principles",
            "discipline": "research",
            "relevance_judgments": []
        },
        {
            "query": "source authority model peer review citation evidence weight",
            "discipline": "research",
            "relevance_judgments": []
        }
    ]
}

with open(OUT / "retrieval-golden-set.json", "w") as f:
    json.dump(RETRIEVAL_GOLDEN, f, indent=2)

total_judgments = sum(len(q["relevance_judgments"]) for q in RETRIEVAL_GOLDEN["queries"])
queries_with_judgments = sum(1 for q in RETRIEVAL_GOLDEN["queries"] if q["relevance_judgments"])
print(f"Queries: {len(RETRIEVAL_GOLDEN['queries'])}")
print(f"Queries with labeled atoms: {queries_with_judgments}")
print(f"Total relevance judgments: {total_judgments}")
print(f"Domains: {len(RETRIEVAL_GOLDEN['disciplines'])}")
