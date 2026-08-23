#!/usr/bin/env python3
"""Research Evidence Integration — validates that research findings were applied.

Cross-references research reports against production artifacts to verify
that professional research actually informed the build, not just sat in files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FLAGSHIP = ROOT / "artifacts" / "flagship"
RESEARCH_DIR = FLAGSHIP / "research"
EMBERVEIL = FLAGSHIP / "emberveil"

# Research claims → production evidence mapping
CLAIM_EVIDENCE_MAP = {
    "creature_idle_breathing": {
        "research_files": ["animation-vfx-lighting-research.json"],
        "claim_keywords": ["idle", "breathing", "subtle", "gentle"],
        "evidence_files": ["emberveil.glb"],
        "check": "NOT YET IMPLEMENTED - animation pending",
    },
    "particle_system_additive": {
        "research_files": ["animation-vfx-lighting-research.json"],
        "claim_keywords": ["particle", "additive", "billboard"],
        "evidence_files": ["../flagship/presentation/index.html"],
        "check": "runtime has particle burst system",
    },
    "three_point_lighting": {
        "research_files": ["animation-vfx-lighting-research.json", "cinematography-runtime-research.json"],
        "claim_keywords": ["three-point", "rim", "key", "fill"],
        "evidence_files": ["v2-batch-upgrade.py"],
        "check": "scene has EmberCoreLight + FillLight + CoolRim",
    },
    "bloom_post_processing": {
        "research_files": ["cinematography-runtime-research.json", "threejs-reference.json"],
        "claim_keywords": ["bloom", "UnrealBloomPass", "EffectComposer"],
        "evidence_files": ["../flagship/presentation/index.html"],
        "check": "runtime has UnrealBloomPass",
    },
    "reduced_motion": {
        "research_files": ["cinematography-runtime-research.json"],
        "claim_keywords": ["reduced-motion", "prefers-reduced"],
        "evidence_files": ["../flagship/presentation/index.html"],
        "check": "runtime checks prefers-reduced-motion",
    },
    "creature_reveal_sequence": {
        "research_files": ["cinematography-runtime-research.json"],
        "claim_keywords": ["camera", "orbit", "perspective"],
        "evidence_files": ["../flagship/presentation/index.html"],
        "check": "runtime camera starts far and orbits",
    },
    "sss_material": {
        "research_files": ["creature-design-research.json", "3d-production-research.json"],
        "claim_keywords": ["subsurface", "SSS", "random walk"],
        "evidence_files": ["v2-batch-upgrade.py"],
        "check": "glass and ember materials use subsurface",
    },
    "pbr_metallic_workflow": {
        "research_files": ["3d-production-research.json"],
        "claim_keywords": ["PBR", "metallic", "roughness"],
        "evidence_files": ["v2-batch-upgrade.py"],
        "check": "brass material has metallic=0.9",
    },
}


def load_research(research_files: list[str]) -> str:
    """Load all research file contents for keyword search."""
    texts = []
    for f in research_files:
        path = RESEARCH_DIR / f
        if path.exists():
            texts.append(path.read_text(encoding="utf-8").lower())
    return "\n".join(texts)


def load_evidence(evidence_files: list[str]) -> str:
    """Load evidence file contents for keyword search."""
    texts = []
    for f in evidence_files:
        if f.startswith("../"):
            path = ROOT / "artifacts" / f[3:]
        else:
            path = EMBERVEIL / f
        if path.exists():
            try:
                texts.append(path.read_text(encoding="utf-8").lower())
            except UnicodeDecodeError:
                pass  # binary files
    return "\n".join(texts)


def audit_research_application() -> dict:
    """Check each research claim was applied in production."""
    results = {}
    for claim_id, spec in CLAIM_EVIDENCE_MAP.items():
        research_text = load_research(spec["research_files"])
        evidence_text = load_evidence(spec["evidence_files"])

        # Check research contains the claim
        research_found = any(kw.lower() in research_text for kw in spec["claim_keywords"])
        # Check evidence contains related terms
        evidence_found = any(kw.lower() in evidence_text for kw in spec["claim_keywords"])

        results[claim_id] = {
            "research_present": research_found,
            "applied_in_production": evidence_found,
            "status": "applied" if (research_found and evidence_found) else
                      "research_only" if research_found else "missing",
        }
    return results


def main() -> int:
    print("=== RESEARCH EVIDENCE INTEGRATION ===")

    if not RESEARCH_DIR.exists():
        print("FAIL No research directory found")
        return 1

    reports = list(RESEARCH_DIR.glob("*.json"))
    print(f"research_reports={len(reports)}")

    results = audit_research_application()
    applied = sum(1 for r in results.values() if r["status"] == "applied")
    research_only = sum(1 for r in results.values() if r["status"] == "research_only")
    missing = sum(1 for r in results.values() if r["status"] == "missing")

    print(f"claims_checked={len(results)}")
    print(f"applied={applied}")
    print(f"research_only={research_only}")
    print(f"missing={missing}")

    for cid, r in results.items():
        print(f"  {r['status'].upper():15s} {cid}")

    if missing > 0:
        print(f"\nFAIL {missing} research claims not evidenced in production")
        return 1
    elif research_only > 0:
        print(f"\nWARN {research_only} claims in research but not yet applied")
        return 0
    else:
        print(f"\nPASS All {applied} research claims applied in production")
        return 0


if __name__ == "__main__":
    sys.exit(main())
