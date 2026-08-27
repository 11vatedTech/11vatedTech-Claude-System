"""
KAPIF M002.1 -- Visual Intelligence Council.

A bounded role-routing layer over existing evidence and providers (NOT a new
inference framework). For a given visual role it:
  1. Gathers deterministic evidence machines can measure directly (so the VLM
     interprets rather than invents measurements).
  2. Resolves the role's preferred / backup / local_fallback models from a
     measured role registry.
  3. Runs the critic(s) with a grounded OBSERVATION / CAUSE / IMPACT / REPAIR
     / CONFIDENCE / SPECULATION contract.
  4. Synthesizes only observations supported by deterministic evidence or
     stated as SPECULATION.

Role confidence levels: LOW / PROVISIONAL / MODERATE / HIGH.
"""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "model-role-registry-vision.json"
CONFIG_PATH = CONFIG

DEFAULT_ROLES = [
    "VISUAL_GROUNDING", "UI_LAYOUT_GROUNDING", "TYPOGRAPHY_CRITIQUE",
    "UI_UX_CRITIQUE", "COMPOSITION_CRITIQUE", "ART_DIRECTION_CRITIQUE",
    "CHARACTER_REFERENCE_ANALYSIS", "CHARACTER_IDENTITY_CRITIQUE",
    "MATERIAL_LIGHTING_CRITIQUE", "3D_TECHNICAL_ART_CRITIQUE",
    "MOTION_ANIMATION_CRITIQUE", "VFX_CRITIQUE", "TEMPORAL_VISUAL_GROUNDING",
]


def load_registry() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {"roles": {}, "as_of": None}


def save_registry(reg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(reg, indent=2), encoding="utf-8")


def ensure_roles(measured: dict | None = None):
    reg = load_registry()
    changed = False
    for role in DEFAULT_ROLES:
        if role not in reg["roles"]:
            reg["roles"][role] = {
                "preferred": None,
                "backup": None,
                "local_fallback": None,
                "benchmark_n": 0,
                "success_n": 0,
                "failure_n": 0,
                "accuracy": None,
                "hallucination_rate": None,
                "latency_median_s": None,
                "hardware_cost": None,
                "confidence": "LOW",
                "last_benchmarked": None,
                "known_failures": [],
            }
            changed = True
    if measured:
        for role, info in measured.items():
            if role in reg["roles"]:
                reg["roles"][role].update(info)
                changed = True
    if changed:
        save_registry(reg)
    return reg


def deterministic_evidence(path: str) -> dict:
    """Facts a machine can measure -- never ask a VLM to invent these."""
    p = Path(path)
    im = Image.open(p)
    im.load()
    w, h = im.size
    g = im.convert("L")
    px = list(g.getdata())
    n = len(px)
    mean = sum(px) / n
    hist = [0] * 256
    for v in px:
        hist[v] += 1
    black_frac = sum(hist[:9]) / n
    white_frac = sum(hist[248:]) / n
    return {
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        "width": w,
        "height": h,
        "orientation": "LANDSCAPE" if w > h else ("PORTRAIT" if h > w else "SQUARE"),
        "mean_luminance": round(mean / 255.0, 3),
        "std_luminance": round((sum((v - mean) ** 2 for v in px) / n) ** 0.5 / 255.0, 3),
        "black_crush_frac": round(black_frac, 3),
        "highlight_clip_frac": round(white_frac, 3),
        "bytes": p.stat().st_size,
    }


def resolve_role(role: str) -> dict:
    reg = load_registry()
    entry = reg["roles"].get(role, {})
    return {
        "role": role,
        "preferred": entry.get("preferred"),
        "backup": entry.get("backup"),
        "local_fallback": entry.get("local_fallback"),
        "confidence": entry.get("confidence", "LOW"),
        "last_benchmarked": entry.get("last_benchmarked"),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        reg = ensure_roles(measured=None)
        print(json.dumps(reg, indent=2))
    else:
        reg = ensure_roles(measured=None)
        print("roles:", len(reg["roles"]))
        for role in DEFAULT_ROLES:
            print(" ", role, "->", resolve_role(role))