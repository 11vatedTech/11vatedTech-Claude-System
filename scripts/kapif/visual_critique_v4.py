"""
KAPIF M002.1 -- Professional Visual Critique V4.

Controlled before/after or A/B pairs where the changed design variable is
KNOWN before execution. The model never sees the hidden answer.

Contract per critique: OBSERVATION / CAUSE / IMPACT / REPAIR / CONFIDENCE /
SPECULATION. Scoring is keyword-grounded against the known intervention
variable plus pairwise selection direction. Eloquence is not scored.

Pair schema: (pair_id, discipline, label_a, path_a, label_b, path_b,
              known_intervention, cause_keywords)
"""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

import requests

from PIL import Image, ImageDraw

ART = Path("artifacts")
OUT_DIR = Path("artifacts/kapif/m002.1/runs-critique-v4")
OLLAMA = "http://127.0.0.1:11434"

PAIRS = [
    ("c1", "COMPOSITION", "comp-c-original", "composition-lab/comp-c-original.png",
     "comp-c-repaired", "composition-lab/comp-c-repaired.png",
     "Two-column split on a ~40-word paragraph removed; reverted to single column for reading flow.",
     ["column", "single", "multi", "split", "readab", "flow"]),
    ("c2", "COMPOSITION/LAYOUT", "transfer-wrong", "composition-lab/transfer-wrong.png",
     "transfer-repaired", "composition-lab/transfer-repaired.png",
     "Layout transfer defect repaired (eye jump, paragraph break restored).",
     ["column", "break", "flow", "align", "spacing", "jump"]),
    ("c3", "lighting", "flat", "lighting-lab/renders/lighting_A_flat.png",
     "key_fill", "lighting-lab/renders/lighting_C_key_fill.png",
     "Flat lighting replaced with key + fill for depth and separation.",
     ["flat", "key", "fill", "contrast", "depth", "shade", "light"]),
    ("c4", "value", "lowkey", "lighting-lab/renders/lighting_D_lowkey.png",
     "highkey", "lighting-lab/renders/lighting_E_highkey.png",
     "Low-key vs high-key value treatment shift.",
     ["key", "bright", "dark", "exposure", "contrast", "value"]),
    ("c5", "material", "defective_ceramic", "material-lab/renders/diag_ceramic_too_metallic.png",
     "correct_ceramic", "material-lab/renders/mat_ceramic.png",
     "Ceramic material too metallic; specular response corrected.",
     ["metall", "specular", "rough", "reflect", "ceramic", "gloss"]),
    ("c6", "material", "glass_no_transmission", "material-lab/renders/diag_glass_no_transmission.png",
     "correct_glass", "material-lab/renders/mat_dirty_glass.png",
     "Glass lost transmission; refraction/transmission restored.",
     ["transmission", "refract", "glass", "transparent", "opaque"]),
    ("c7", "material", "rubber_too_glossy", "material-lab/renders/diag_rubber_too_glossy.png",
     "correct_rubber", "material-lab/renders/mat_rubber_polymer.png",
     "Rubber was too glossy; roughness/softness corrected.",
     ["gloss", "rough", "soft", "sheen", "matte"]),
    ("c8", "material", "metal_too_diffuse", "material-lab/renders/diag_metal_too_diffuse.png",
     "correct_metal", "material-lab/renders/mat_aged_steel.png",
     "Metal read as diffuse plastic; metal specular response restored.",
     ["metal", "specular", "diffuse", "sheen", "highlight", "plastic"]),
    ("c9", "material", "wrong_bump", "material-lab/renders/diag_wrong_scale_bump.png",
     "correct_wood", "material-lab/renders/mat_painted_wood.png",
     "Bump scale was wrong; surface relief/texture corrected.",
     ["bump", "relief", "normal", "texture", "scale", "grain"]),
    ("c10", "vfx", "vfx_frame_1", "vfx-lab/renders/frames_magical/frame_0001.png",
     "vfx_frame_33", "vfx-lab/renders/frames_magical/frame_0033.png",
     "VFX/animation state progressed (motion state advanced).",
     ["motion", "anim", "frame", "progress", "move", "particle"]),
    ("c11", "character_id", "reference", "character-identity/reference.png",
     "primitive_proxy", "character-identity/primitive_proxy.png",
     "Generic primitive proxy replaces the authored character; silhouette/proportions/markings lost.",
     ["silhouette", "proxy", "generic", "proportion", "simple", "primitive", "sphere", "capsule", "cone", "detail"]),
    ("c12", "character_id", "reference", "character-identity/reference.png",
     "identity_preserving", "character-identity/identity_preserving.png",
     "Identity-preserving representation keeps silhouette, markings and palette.",
     ["silhouette", "preserv", "faithful", "match", "consistent", "marking", "ident"]),
]

CRITIQUE_TEMPLATE = (
    "You are a professional visual critic. Two images are provided: IMAGE A and IMAGE B.\n"
    "Compare them and answer ONLY with a JSON object:\n"
    '{"worse":"A|B|EQUAL","observation":"specific visible differences",'
    '"cause":"most likely design cause","impact":"effect on hierarchy/legibility/orientation/identity/emotion/interaction/quality",'
    '"repair":"specific change that addresses the cause","confidence":"HIGH|MEDIUM|LOW",'
    '"speculation":"anything not directly visible"}\n'
    "Rules: observation must name only things actually visible. Do not invent details. Output ONLY the JSON."
)
CRITIQUE_HASH = hashlib.sha256(CRITIQUE_TEMPLATE.encode()).hexdigest()


def ensure_character_images():
    d = ART / "character-identity"
    d.mkdir(parents=True, exist_ok=True)
    ref = d / "reference.png"
    proxy = d / "primitive_proxy.png"
    keep = d / "identity_preserving.png"
    if all(p.exists() for p in (ref, proxy, keep)):
        return
    ref = str(ref); proxy = str(proxy); keep = str(keep)
    W, H = 640, 640
    # reference: designed creature (crested warden bird with markings)
    im = Image.new("RGB", (W, H), (14, 16, 20))
    dr = ImageDraw.Draw(im)
    dr.polygon([(320, 200), (250, 480), (320, 560), (390, 480)], fill=(38, 46, 58))
    dr.polygon([(300, 212), (330, 190), (360, 215), (355, 172), (335, 158), (310, 178)], fill=(60, 72, 84))
    dr.polygon([(250, 330), (150, 300), (120, 360), (180, 410), (200, 380)], fill=(28, 34, 36))
    dr.polygon([(390, 350), (440, 340), (455, 385)], fill=(28, 34, 36))
    dr.polygon([(300, 540), (280, 600), (305, 620), (318, 590), (335, 622), (350, 598), (320, 540)], fill=(60, 56, 40))
    dr.polygon([(310, 400), (320, 430), (330, 400)], fill=(255, 166, 58))
    dr.ellipse([240, 500, 270, 515], fill=(202, 152, 96))
    dr.ellipse([360, 470, 390, 485], fill=(202, 152, 96))
    dr.ellipse([328, 205, 344, 221], fill=(255, 214, 130))
    im.save(str(ref))
    # identity-preserving: same identity anchors, shaded + textured
    im2 = Image.new("RGB", (W, H), (14, 16, 20))
    dr = ImageDraw.Draw(im2)
    dr.polygon([(250, 480), (300, 560), (390, 480), (320, 150), (250, 330)], fill=(46, 54, 50))
    dr.polygon([(302, 210), (330, 188), (358, 150), (353, 175), (312, 160), (288, 178)], fill=(70, 84, 54))
    dr.polygon([(250, 330), (180, 420), (120, 360), (180, 410), (200, 380)], fill=(36, 44, 46))
    dr.polygon([(330, 350), (440, 340), (455, 385)], fill=(36, 44, 46))
    dr.polygon([(300, 540), (285, 600), (308, 618), (330, 588), (352, 620), (365, 596), (320, 540)], fill=(64, 60, 44))
    dr.polygon([(292, 404), (300, 424), (310, 404)], fill=(255, 130, 30))
    dr.polygon([(316, 402), (326, 432), (338, 402)], fill=(255, 170, 50))
    dr.ellipse([236, 338, 272, 518], outline=(214, 160, 100), width=6)
    dr.ellipse([364, 460, 394, 490], outline=(214, 160, 100), width=6)
    dr.ellipse([322, 200, 342, 222], fill=(255, 216, 132))
    im2.save(str(keep))
    # primitive proxy: generic sphere body + cone head + capsule base
    im3 = Image.new("RGB", (W, H), (14, 16, 20))
    dr = ImageDraw.Draw(im3)
    dr.ellipse([270, 320, 390, 440], fill=(70, 74, 76))
    dr.polygon([(300, 250), (360, 250), (330, 180)], fill=(84, 88, 92))
    dr.rounded_rectangle([230, 420, 410, 460], radius=14, fill=(48, 52, 56))
    dr.ellipse([336, 218, 352, 234], fill=(10, 10, 12))
    im3.save(str(proxy))
    print("character images written")


def infer_pair(model, path_a, path_b):
    imgs = [
        base64.b64encode(Path(path_a).read_bytes()).decode(),
        base64.b64encode(Path(path_b).read_bytes()).decode(),
    ]
    r = requests.post(
        f"{OLLAMA}/api/generate",
        json={
            "model": model,
            "prompt": CRITIQUE_TEMPLATE,
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


def parse_critique(raw):
    s = (raw or "").strip()
    if s.startswith("```"):
        s = s.split("```")[1] if "```" in s else s
        s = s.strip("json\n ")
    a, b = s.find("{"), s.rfind("}")
    obj = None
    if a != -1 and b > a:
        try:
            obj = json.loads(s[a : b + 1])
        except Exception:
            obj = None
    if obj and {"worse", "observation", "cause", "impact", "repair"} <= set(obj):
        return obj
    # fallback: regex extraction for prose responses
    import re

    out = {}
    pat = re.compile(r'"?(worse|observation|cause|impact|repair|confidence|speculation)"?\s*[:=]\s*"([^"]{2,300})"', re.I)
    for m in pat.finditer(s):
        out.setdefault(m.group(1).lower(), m.group(2).strip())
    if not out.get("worse") or not out.get("cause"):
        return None
    return out


def score_pair(pair, crit):
    keywords = pair[7]
    cause = (crit.get("cause") or "").lower()
    repair = (crit.get("repair") or "").lower()
    obs = (crit.get("observation") or "").lower()
    worse = (crit.get("worse") or "").strip().upper().replace("IMAGE ", "")
    # In this dataset the FIRST label/path is always the defective/before variant.
    return {
        "worse": worse,
        "worse_valid": worse in ("A", "B", "EQUAL"),
        "cause_keyword_hit": any(k in cause for k in pair[7]),
        "repair_keyword_hit": any(k in repair for k in pair[7] + ["fix", "correct", "adjust", "improv", "increase", "reduce", "add"]),
        "observation_has_visible": any(k in obs for k in ["left", "right", "image", "first", "second", "one", "two", "brighter", "darker", "larger", "smaller", "flat", "gloss", "rough", "sharp", "column", "frame", "black", "white", "light"]),
        "confidence": (crit.get("confidence") or "").upper(),
        "confidence_valid": (crit.get("confidence") or "").upper() in ("HIGH", "MEDIUM", "LOW"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    ensure_character_images()
    out_file = OUT_DIR / f"critique-{args.model.replace(':', '_')}.json"
    out = {"model": args.model, "template_hash": CRITIQUE_HASH, "pairs": {}}
    if out_file.exists():
        out = json.loads(out_file.read_text(encoding="utf-8"))

    for pair in PAIRS:
        pid = pair[0]
        if args.resume and pid in out["pairs"]:
            r = out["pairs"][pid]
            # re-run only if raw is empty or failed to parse
            if r.get("status") == "OK" and (r.get("raw") or "").strip() and r.get("parsed"):
                continue
            if r.get("status") == "OK" and (r.get("raw") or "").strip():
                # re-parse attempt with better extraction
                rec = r
                rec["parsed"] = parse_critique(rec["raw"])
                if rec["parsed"]:
                    rec["score"] = score_pair(pair, rec["parsed"])
                out["pairs"][pid] = rec
                out_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
                print(f"{pid} reparsed", flush=True)
                continue
        if args.score_only:
            continue
        r = infer_pair(args.model, ART / pair[3], ART / pair[5])
        rec = {"pair_id": pid, "discipline": pair[1], "known_intervention": pair[6], **r}
        if r["status"] == "OK":
            rec["parsed"] = parse_critique(r["raw"])
            if rec["parsed"]:
                rec["score"] = score_pair(pair, rec["parsed"])
        out["pairs"][pid] = rec
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"{pid} {pair[1]} {r['status']}", flush=True)

    if args.score_only:
        print("score-only requires pairs already present; no-op")
    print("DONE", out_file)


if __name__ == "__main__":
    main()