"""
KAPIF M002.1 — Professional Visual Critique V5.

Counterbalanced A/B placement with structured cause taxonomy.
No positional leakage: ground_truth_worse is independent of A/B order.

Cause scoring uses EXACT class matching (not keyword substrings).
Pair scoring requires: OBSERVATION / CAUSE_CLASS / IMPACT / REPAIR / CONFIDENCE / SPECULATION.

Frozen seed ensures reproducible A/B ordering.
"""

import argparse
import base64
import hashlib
import json
import random
import sys
import time
from pathlib import Path

import requests

ART = Path("artifacts")
OUT_DIR = Path("artifacts/kapif/m002.1/runs-critique-v5")

# ── Cause taxonomy ──────────────────────────────────────────────
CAUSE_TAXONOMY = {
    "UI_HIERARCHY": ["hierarchy", "scale", "weight", "prominence", "visual weight"],
    "OCCLUSION": ["occlu", "overlay", "block", "cover", "hide", "obstruct"],
    "MISSING_CLOSE": ["close", "dismiss", "exit", "x button", "close button"],
    "NAVIGATION_DISCOVERABILITY": ["nav", "discover", "find", "access", "menu"],
    "STATE_AMBIGUITY": ["state", "selected", "active", "hover", "toggle", "pressed"],
    "SPACING_RELATIONSHIP": ["spacing", "gap", "padding", "margin", "breath"],
    "TYPOGRAPHIC_HIERARCHY": ["typography", "font", "size", "heading", "headline", "text weight"],
    "CONTRAST_LEGIBILITY": ["contrast", "legib", "readab", "color", "light", "dark"],
    "RESPONSIVE_REFLOW": ["responsive", "reflow", "breakpoint", "mobile", "resize", "overflow"],
    "DENSITY_OVERLOAD": ["density", "clutter", "cramped", "overcrowded", "packed"],
    "CONTENT_MISMATCH": ["mismatch", "inconsist", "mislead", "wrong", "doesn't match"],
    "MATERIAL_DEFECT": ["material", "shader", "surface", "rough", "gloss", "metallic", "specular"],
    "LIGHTING_FLAT": ["flat", "lighting", "depth", "shadow", "key light", "fill"],
    "SILHOUETTE_DEVIATION": ["silhouette", "shape", "outline", "proportion", "form"],
    "IDENTITY_LOSS": ["identity", "character", "generic", "primit", "proxy", "unique"],
    "COMPOSITION_BREACH": ["composition", "rule of thirds", "balance", "focal", "center"],
}

# ── Structured critique template ───────────────────────────────
CRITIQUE_TEMPLATE_V5 = """You are a professional visual critic evaluating two images (IMAGE_A and IMAGE_B).

You MUST return EXACTLY this JSON structure:
{
  "worse": "A" | "B" | "EQUAL",
  "observation": "what is visibly different between the two images",
  "cause_class": "one of: UI_HIERARCHY, OCCLUSION, MISSING_CLOSE, NAVIGATION_DISCOVERABILITY, STATE_AMBIGUITY, SPACING_RELATIONSHIP, TYPOGRAPHIC_HIERARCHY, CONTRAST_LEGIBILITY, RESPONSIVE_REFLOW, DENSITY_OVERLOAD, CONTENT_MISMATCH, MATERIAL_DEFECT, LIGHTING_FLAT, SILHOUETTE_DEVIATION, IDENTITY_LOSS, COMPOSITION_BREACH, OTHER",
  "impact": "effect on usability, legibility, hierarchy, identity, or quality",
  "repair": "specific change that addresses the identified cause",
  "confidence": "HIGH" | "MEDIUM" | "LOW",
  "speculation": "anything not directly visible in the images"
}

Rules:
- observation must name ONLY things actually visible. Do not invent details.
- cause_class must be EXACTLY one of the listed classes (or OTHER).
- Output ONLY the JSON object. No extra text.
"""

CRITIQUE_HASH_V5 = hashlib.sha256(CRITIQUE_TEMPLATE_V5.encode()).hexdigest()

# ── UI/UX-focused pairs with cause taxonomy ────────────────────
# (pair_id, discipline, cause_class, label_a, path_a, label_b, path_b,
#  known_intervention, ground_truth_worse)
# ground_truth_worse: which variant is defective INDEPENDENT of A/B order

UI_UX_PAIRS = [
    # c1-c2: composition (reuse from V4)
    ("c1", "COMPOSITION", "COMPOSITION_BREACH",
     "comp-original", "composition-lab/comp-c-original.png",
     "comp-repaired", "composition-lab/comp-c-repaired.png",
     "Two-column split on paragraph removed; single column for reading flow.",
     "A"),  # original is worse
    ("c2", "COMPOSITION/LAYOUT", "COMPOSITION_BREACH",
     "transfer-wrong", "composition-lab/transfer-wrong.png",
     "transfer-repaired", "composition-lab/transfer-repaired.png",
     "Layout transfer defect repaired (eye jump, paragraph break restored).",
     "A"),  # wrong is worse

    # c3-c4: lighting
    ("c3", "LIGHTING", "LIGHTING_FLAT",
     "flat", "lighting-lab/renders/lighting_A_flat.png",
     "key_fill", "lighting-lab/renders/lighting_C_key_fill.png",
     "Flat lighting replaced with key + fill for depth and separation.",
     "A"),  # flat is worse
    ("c4", "VALUE", "CONTRAST_LEGIBILITY",
     "lowkey", "lighting-lab/renders/lighting_D_lowkey.png",
     "highkey", "lighting-lab/renders/lighting_E_highkey.png",
     "Low-key vs high-key value treatment shift.",
     "B"),  # highkey is worse (lost detail in bright areas)

    # c5-c9: material
    ("c5", "MATERIAL", "MATERIAL_DEFECT",
     "defective_ceramic", "material-lab/renders/diag_ceramic_too_metallic.png",
     "correct_ceramic", "material-lab/renders/mat_ceramic.png",
     "Ceramic material too metallic; specular response corrected.",
     "A"),
    ("c6", "MATERIAL", "MATERIAL_DEFECT",
     "glass_no_transmission", "material-lab/renders/diag_glass_no_transmission.png",
     "correct_glass", "material-lab/renders/mat_dirty_glass.png",
     "Glass lost transmission; refraction/transmission restored.",
     "A"),
    ("c7", "MATERIAL", "MATERIAL_DEFECT",
     "rubber_too_glossy", "material-lab/renders/diag_rubber_too_glossy.png",
     "correct_rubber", "material-lab/renders/mat_rubber_polymer.png",
     "Rubber was too glossy; roughness/softness corrected.",
     "A"),
    ("c8", "MATERIAL", "MATERIAL_DEFECT",
     "metal_too_diffuse", "material-lab/renders/diag_metal_too_diffuse.png",
     "correct_metal", "material-lab/renders/mat_aged_steel.png",
     "Metal read as diffuse plastic; metal specular response restored.",
     "A"),
    ("c9", "MATERIAL", "MATERIAL_DEFECT",
     "wrong_bump", "material-lab/renders/diag_wrong_scale_bump.png",
     "correct_wood", "material-lab/renders/mat_painted_wood.png",
     "Bump scale was wrong; surface relief/texture corrected.",
     "A"),

    # c10: VFX
    ("c10", "VFX", "OTHER",
     "vfx_frame_1", "vfx-lab/reads/frames_magical/frame_0001.png",
     "vfx_frame_33", "vfx-lab/reads/frames_magical/frame_0033.png",
     "VFX/animation state progressed (motion state advanced).",
     "B"),  # frame 1 is the earlier/less-complete state

    # c11-c12: character identity
    ("c11", "CHARACTER_ID", "IDENTITY_LOSS",
     "reference", "character-identity/reference.png",
     "primitive_proxy", "character-identity/primitive_proxy.png",
     "Generic primitive proxy replaces the authored character; silhouette/proportions/markings lost.",
     "B"),  # proxy is worse
    ("c12", "CHARACTER_ID", "SILHOUETTE_DEVIATION",
     "reference", "character-identity/reference.png",
     "identity_preserving", "character-identity/identity_preserving.png",
     "Identity-preserving representation keeps silhouette, markings and palette.",
     "B"),  # identity_preserving is slightly worse than reference but close

    # c13-c18: NEW UI/UX pairs from transfer lab
    ("c13", "UI_HIERARCHY", "UI_HIERARCHY",
     "transfer-wrong", "composition-lab/transfer-wrong.png",
     "transfer-repaired", "composition-lab/transfer-repaired.png",
     "Layout hierarchy disrupted by incorrect column split; single column restores reading order.",
     "A"),
    ("c14", "DENSITY", "DENSITY_OVERLOAD",
     "comp-original", "composition-lab/comp-c-original.png",
     "comp-repaired", "composition-lab/comp-c-repaired.png",
     "Dense two-column layout vs single column with breathing room.",
     "A"),
    ("c15", "SPACING", "SPACING_RELATIONSHIP",
     "transfer-wrong", "composition-lab/transfer-wrong.png",
     "transfer-repaired", "composition-lab/transfer-repaired.png",
     "Spacing relationships between elements disrupted in wrong version.",
     "A"),
    ("c16", "TYPOGRAPHY", "TYPOGRAPHIC_HIERARCHY",
     "comp-original", "composition-lab/comp-c-original.png",
     "comp-repaired", "composition-lab/comp-c-repaired.png",
     "Typography hierarchy affected by column split breaking text flow.",
     "A"),
    ("c17", "MATERIAL_CERAMIC", "MATERIAL_DEFECT",
     "defective_ceramic", "material-lab/renders/diag_ceramic_too_metallic.png",
     "correct_ceramic", "material-lab/renders/mat_ceramic.png",
     "Ceramic reads as metallic; roughness needs increase.",
     "A"),
    ("c18", "MATERIAL_GLASS", "MATERIAL_DEFECT",
     "glass_no_transmission", "material-lab/renders/diag_glass_no_transmission.png",
     "correct_glass", "material-lab/renders/mat_dirty_glass.png",
     "Glass opaque; transmission/refraction missing.",
     "A"),
]

SEED = 42  # frozen seed for reproducible counterbalancing


def counterbalance_pairs(pairs, seed=SEED):
    """For each pair, create A/B and B/A presentations with deterministic randomization."""
    rng = random.Random(seed)
    balanced = []
    for pair in pairs:
        pid, disc, cause, la, pa, lb, pb, interv, gt_worse = pair
        # Randomly swap A/B assignment
        if rng.random() < 0.5:
            # Keep as-is
            balanced.append({
                "pair_id": f"{pid}_ab",
                "base_pair_id": pid,
                "discipline": disc,
                "cause_class": cause,
                "label_a": la, "path_a": pa,
                "label_b": lb, "path_b": pb,
                "known_intervention": interv,
                "ground_truth_worse": gt_worse,  # in A/B order
                "presentation": "A/B",
            })
            balanced.append({
                "pair_id": f"{pid}_ba",
                "base_pair_id": pid,
                "discipline": disc,
                "cause_class": cause,
                "label_a": lb, "path_a": pb,  # swapped
                "label_b": la, "path_b": pa,  # swapped
                "known_intervention": interv,
                "ground_truth_worse": "B" if gt_worse == "A" else "A",  # flipped
                "presentation": "B/A",
            })
        else:
            # Swap order
            balanced.append({
                "pair_id": f"{pid}_ba",
                "base_pair_id": pid,
                "discipline": disc,
                "cause_class": cause,
                "label_a": lb, "path_a": pb,
                "label_b": la, "path_b": pa,
                "known_intervention": interv,
                "ground_truth_worse": "B" if gt_worse == "A" else "A",
                "presentation": "B/A",
            })
            balanced.append({
                "pair_id": f"{pid}_ab",
                "base_pair_id": pid,
                "discipline": disc,
                "cause_class": cause,
                "label_a": la, "path_a": pa,
                "label_b": lb, "path_b": pb,
                "known_intervention": interv,
                "ground_truth_worse": gt_worse,
                "presentation": "A/B",
            })
    return balanced


def ensure_character_images():
    """Reuse V4 character images if they exist."""
    d = ART / "character-identity"
    if (d / "reference.png").exists():
        return
    # If not, import from V4
    sys.path.insert(0, str(Path(__file__).parent))
    from visual_critique_v4 import ensure_character_images as ensure_v4
    ensure_v4()


def infer_pair_ollama(model, path_a, path_b):
    """Run inference via Ollama."""
    imgs = [
        base64.b64encode(Path(path_a).read_bytes()).decode(),
        base64.b64encode(Path(path_b).read_bytes()).decode(),
    ]
    r = requests.post(
        "http://127.0.0.1:11434/api/generate",
        json={
            "model": model,
            "prompt": CRITIQUE_TEMPLATE_V5,
            "images": imgs,
            "stream": False,
            "keep_alive": "30m",
            "options": {"temperature": 0.0, "num_predict": 2048},
        },
        timeout=240,
    )
    if r.status_code != 200:
        return {"status": f"HTTP_{r.status_code}", "raw": r.text[:200]}
    return {"status": "OK", "raw": r.json().get("response", "")}


def infer_pair_9router(route, path_a, path_b):
    """Run inference via 9Router with SSE streaming support."""
    import os
    base = os.environ.get("NINEROUTER_URL", "http://127.0.0.1:20128")
    imgs_b64 = []
    for p in [path_a, path_b]:
        raw = Path(p).read_bytes()
        b64 = base64.b64encode(raw).decode()
        imgs_b64.append(f"data:image/png;base64,{b64}")

    payload = {
        "model": route,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": CRITIQUE_TEMPLATE_V5},
                {"type": "image_url", "image_url": {"url": imgs_b64[0]}},
                {"type": "image_url", "image_url": {"url": imgs_b64[1]}},
            ]}
        ],
        "temperature": 0.0,
        "max_tokens": 2048,
    }
    t0 = time.time()
    try:
        r = requests.post(
            f"{base}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=120,
        )
        if r.status_code != 200:
            return {"status": f"HTTP_{r.status_code}", "raw": r.text[:300]}

        # Parse SSE streaming response
        content_parts = []
        for line in r.iter_lines():
            if line:
                line = line.decode()
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            content_parts.append(delta["content"])
                    except Exception:
                        pass
        content = "".join(content_parts)
        latency = time.time() - t0
        return {"status": "OK", "raw": content, "latency": latency}
    except Exception as e:
        latency = time.time() - t0
        return {"status": f"ERROR_{type(e).__name__}", "raw": str(e)[:300], "latency": latency}


def parse_critique(raw):
    """Parse structured JSON critique from model response."""
    s = (raw or "").strip()
    # Strip markdown fences
    if "```" in s:
        parts = s.split("```")
        s = parts[1] if len(parts) > 1 else s
        s = s.strip("json\n ")
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b > a:
        try:
            obj = json.loads(s[a: b + 1])
            if {"worse", "observation", "cause_class", "impact", "repair"} <= set(obj):
                return obj
        except Exception:
            pass
    # Fallback: regex extraction
    import re
    out = {}
    for field in ["worse", "observation", "cause_class", "impact", "repair", "confidence", "speculation"]:
        pat = re.compile(rf'"{field}"\s*:\s*"([^"]{{1,500}})"', re.I)
        m = pat.search(s)
        if m:
            out[field] = m.group(1).strip()
    if out.get("worse") and out.get("cause_class"):
        return out
    return None


def score_pair(pair_info, crit):
    """Score against cause taxonomy and ground truth worse."""
    gt_worse = pair_info["ground_truth_worse"]
    worse = (crit.get("worse") or "").strip().upper().replace("IMAGE ", "")
    cause_class = (crit.get("cause_class") or "").strip().upper()

    # Normalize cause class
    cause_normalized = cause_class.replace(" ", "_").replace("-", "_")

    return {
        "worse": worse,
        "worse_correct": worse == gt_worse,
        "worse_valid": worse in ("A", "B", "EQUAL"),
        "cause_class": cause_normalized,
        "cause_class_valid": cause_normalized in CAUSE_TAXONOMY or cause_normalized == "OTHER",
        "cause_exact_match": cause_normalized == pair_info["cause_class"],
        "observation_grounding": bool(crit.get("observation", "").strip()),
        "repair_relevance": bool(crit.get("repair", "").strip()),
        "confidence_valid": (crit.get("confidence") or "").upper() in ("HIGH", "MEDIUM", "LOW"),
        "confidence": (crit.get("confidence") or "").upper(),
    }


def compute_aggregate(results):
    """Compute aggregate metrics across all scored pairs."""
    if not results:
        return {}
    total = len(results)
    worse_valid = sum(1 for r in results if r.get("worse_valid"))
    worse_correct = sum(1 for r in results if r.get("worse_correct"))
    cause_valid = sum(1 for r in results if r.get("cause_class_valid"))
    cause_exact = sum(1 for r in results if r.get("cause_exact_match"))
    obs_grounded = sum(1 for r in results if r.get("observation_grounding"))
    repair_rel = sum(1 for r in results if r.get("repair_relevance"))

    # Direction consistency: for same base_pair in A/B vs B/A, both should pick same variant
    by_base = {}
    for r in results:
        bid = r.get("base_pair_id", "")
        by_base.setdefault(bid, []).append(r)
    direction_consistent = 0
    direction_pairs = 0
    for bid, rs in by_base.items():
        if len(rs) >= 2:
            direction_pairs += 1
            w1, w2 = rs[0].get("worse"), rs[1].get("worse")
            if w1 == w2:
                direction_consistent += 1

    return {
        "total_pairs": total,
        "worse_valid_rate": worse_valid / total,
        "worse_accuracy": worse_correct / total,
        "cause_valid_rate": cause_valid / total,
        "cause_exact_accuracy": cause_exact / total,
        "observation_grounding_rate": obs_grounded / total,
        "repair_relevance_rate": repair_rel / total,
        "direction_consistency": direction_consistent / direction_pairs if direction_pairs else 0,
        "direction_pairs_evaluated": direction_pairs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="Ollama model name (local inference)")
    ap.add_argument("--route", help="9Router route name (remote inference)")
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    if not args.model and not args.route:
        print("ERROR: --model or --route required")
        sys.exit(1)

    ensure_character_images()
    backend = f"ollama-{args.model}" if args.model else f"9router-{args.route}"
    out_file = OUT_DIR / f"critique-v5-{backend.replace('/', '_').replace(':', '_')}.json"
    balanced = counterbalance_pairs(UI_UX_PAIRS)

    out = {
        "version": "v5",
        "model": args.model or args.route,
        "backend": "ollama" if args.model else "9router",
        "template_hash": CRITIQUE_HASH_V5,
        "seed": SEED,
        "cause_taxonomy": list(CAUSE_TAXONOMY.keys()),
        "pairs": {},
        "aggregate": {},
    }
    if out_file.exists():
        out = json.loads(out_file.read_text(encoding="utf-8"))

    scored = []
    for pair in balanced:
        pid = pair["pair_id"]
        if args.resume and pid in out["pairs"]:
            r = out["pairs"][pid]
            if r.get("status") == "OK" and r.get("parsed") and r.get("score"):
                scored.append(r["score"])
                continue
        if args.score_only:
            continue

        # Resolve image paths
        pa = ART / pair["path_a"]
        pb = ART / pair["path_b"]
        if not pa.exists() or not pb.exists():
            print(f"{pid} SKIP (missing image)", flush=True)
            continue

        if args.model:
            r = infer_pair_ollama(args.model, str(pa), str(pb))
        else:
            r = infer_pair_9router(args.route, str(pa), str(pb))

        rec = {
            "pair_id": pid,
            "base_pair_id": pair["base_pair_id"],
            "discipline": pair["discipline"],
            "presentation": pair["presentation"],
            "ground_truth_worse": pair["ground_truth_worse"],
            "known_intervention": pair["known_intervention"],
            **r,
        }
        if r["status"] == "OK":
            rec["parsed"] = parse_critique(r["raw"])
            if rec["parsed"]:
                rec["score"] = score_pair(pair, rec["parsed"])
                scored.append(rec["score"])

        out["pairs"][pid] = rec
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
        status_char = "OK" if rec.get("score", {}).get("worse_correct") else "MISS"
        print(f"{pid} [{pair['presentation']}] {status_char}", flush=True)

    out["aggregate"] = compute_aggregate(scored)
    out_file.write_text(json.dumps(out, indent=1), encoding="utf-8")

    agg = out["aggregate"]
    print(f"\n=== CRITIQUE V5 AGGREGATE ===")
    print(f"Pairs: {agg.get('total_pairs', 0)}")
    print(f"Worse accuracy: {agg.get('worse_accuracy', 0):.1%}")
    print(f"Cause exact accuracy: {agg.get('cause_exact_accuracy', 0):.1%}")
    print(f"Direction consistency: {agg.get('direction_consistency', 0):.1%}")
    print(f"Output: {out_file}")


if __name__ == "__main__":
    main()
