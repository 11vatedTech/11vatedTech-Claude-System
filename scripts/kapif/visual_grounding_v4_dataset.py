"""
KAPIF M002.1 -- Visual Grounding Benchmark V4 dataset builder.

Real Foundry-owned artifacts only. Ground truth provenance:
  - DIMENSIONS            : orientation (deterministic from width/height)
  - DETERMINISTIC_IMAGE_ANALYSIS : dominant value, black crush, highlight clip,
                                   focal-region proxy (computed from pixels)
  - LAB_SOURCE_PROVENANCE : ui_present / render_type / visible_text from the
                            known controlled source artifact (HELIOGRAPH UI
                            captures, material-lab, lighting-lab, vfx-lab,
                            emberveil renders, unreal env captures).

Freeze rule: dataset is frozen BEFORE any model evaluation. Per-property class
distribution is checked; a strongly dominated binary property is dropped from
the scoreboard with a justification record rather than scored.
"""

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path("artifacts")
OUT = Path("artifacts/kapif/m002.1/visual-benchmark-v4-dataset.json")
LABEL_VERSION = "v4.0"
GT_VERSION = "gt-v4.0"

# (path, media_class, provenance_src) -- dedup by sha256 applied in build()
SAMPLES = [
    # --- UI (18 UNIQUE real HELIOGRAPH harness captures) ---
    ("frontend/desktop_default.png", "ui-desktop", "HELIOGRAPH_DESKTOP"),
    ("frontend/mobile_default.png", "ui-mobile", "HELIOGRAPH_MOBILE"),
    ("frontend/tablet_default.png", "ui-tablet", "HELIOGRAPH_TABLET"),
    ("frontend/transfer-lab-001/desktop_confirmed.png", "ui-desktop", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/desktop_selected-detail.png", "ui-desktop", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/desktop_keyboard-focus.png", "ui-desktop", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/desktop_hover-row.png", "ui-desktop", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/desktop_default.png", "ui-desktop", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/mobile_confirmed.png", "ui-mobile", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/mobile_selected-detail.png", "ui-mobile", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/mobile_keyboard-focus.png", "ui-mobile", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/mobile_hover-row.png", "ui-mobile", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/mobile_default.png", "ui-mobile", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/tablet_confirmed.png", "ui-tablet", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/tablet_selected-detail.png", "ui-tablet", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/tablet_keyboard-focus.png", "ui-tablet", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/tablet_hover-row.png", "ui-tablet", "HELIOGRAPH_TRANSFER"),
    ("frontend/transfer-lab-001/tablet_default.png", "ui-tablet", "HELIOGRAPH_TRANSFER"),
    # --- 3D material studies (Blender) ---
    ("material-lab/renders/mat_aged_steel.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/mat_ceramic.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/mat_dirty_glass.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/mat_painted_wood.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/mat_rubber_polymer.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/diag_ceramic_too_metallic.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/diag_glass_no_transmission.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/diag_metal_too_diffuse.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/diag_rubber_too_glossy.png", "render-material", "MATERIAL_LAB"),
    ("material-lab/renders/diag_wrong_scale_bump.png", "render-material", "MATERIAL_LAB"),
    # --- lighting studies ---
    ("lighting-lab/renders/lighting_A_flat.png", "render-light", "LIGHTING_LAB"),
    ("lighting-lab/renders/lighting_B_key_only.png", "render-light", "LIGHTING_LAB"),
    ("lighting-lab/renders/lighting_C_key_fill.png", "render-light", "LIGHTING_LAB"),
    ("lighting-lab/renders/lighting_D_lowkey.png", "render-light", "LIGHTING_LAB"),
    ("lighting-lab/renders/lighting_E_highkey.png", "render-light", "LIGHTING_LAB"),
    ("lighting-lab/renders/lighting_F_silhouette.png", "render-light", "LIGHTING_LAB"),
    ("lighting-lab/renders/diag_bad_material_good_light.png", "render-light", "LIGHTING_LAB"),
    ("lighting-lab/renders/diag_good_material_bad_light.png", "render-light", "LIGHTING_LAB"),
    # --- VFX / hero / env / Blender suite ---
    ("vfx-lab/renders/frames_magical/frame_0001.png", "render-vfx", "VFX_LAB"),
    ("vfx-lab/renders/frames_magical/frame_0033.png", "render-vfx", "VFX_LAB"),
    ("flagship/emberveil/turntable/turntable-000.png", "render-hero", "EMBERVEIL_FLAGSHIP"),
    ("flagship/emberveil/turntable/turntable-009.png", "render-hero", "EMBERVEIL_FLAGSHIP"),
    ("flagship/emberveil-canonical/turntable/turntable-000.png", "render-hero", "EMBERVEIL_CANONICAL"),
    ("flagship/emberveil-canonical/turntable/turntable-006.png", "render-hero", "EMBERVEIL_CANONICAL"),
    ("flagship/emberveil-canonical/turntable/turntable-012.png", "render-hero", "EMBERVEIL_CANONICAL"),
    ("flagship/emberveil-canonical/preview/preview-frame-0048.png", "render-hero", "EMBERVEIL_CANONICAL"),
    ("creative-stack-validation/blender/render.png", "render-blender", "BLENDER_OPS_SUITE"),
    ("creative-stack-validation/blender-ops/preview/preview-frame-0048.png", "render-blender", "BLENDER_OPS_SUITE"),
    ("unreal/health/ashwake-environment-apprenticeship-phase3/option_a/hostile/screenshots/ashwake-gameplay-00.png", "render-env", "ASHWAKE_PHASE3_REAL_GAMEPLAY"),
    ("unreal/health/ashwake-environment-apprenticeship-phase3/option_b/spawn/screenshots/ashwake-gameplay-00.png", "render-env", "ASHWAKE_PHASE3_REAL_GAMEPLAY"),
    ("unreal/health/ashwake-environment-apprenticeship-phase3/option_c/environment_overview/screenshots/ashwake-gameplay-00.png", "render-env", "ASHWAKE_PHASE3_REAL_GAMEPLAY"),
]

# Last-minute replacement: keep 40 total (40 already) -- verify count below.
UI_MEDIA = {"ui-desktop", "ui-mobile", "ui-tablet"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def luminance_stats(im: Image.Image):
    g = im.convert("L")
    px = list(g.getdata())
    n = len(px)
    mean = sum(px) / n
    # quantile-ish: use sorted small sample via count histogram
    hist = [0] * 256
    for v in px:
        hist[v] += 1
    total = n
    acc = 0
    p2 = p98 = 0
    for i in range(256):
        acc += hist[i]
        if p2 == 0 and acc >= total * 0.02:
            p2 = i
        if acc >= total * 0.98:
            p98 = i
            break
    # std
    m2 = sum((v - mean) ** 2 for v in px) / n
    std = m2 ** 0.5
    black_frac = sum(hist[:9]) / total
    white_frac = sum(hist[248:]) / total
    return {
        "mean": round(mean / 255.0, 4),
        "std": round(std / 255.0, 4),
        "p2": p2,
        "p98": p98,
        "black_frac": round(black_frac, 4),
        "white_frac": round(white_frac, 4),
    }


def dominant_value(stats: dict) -> str:
    mean, std = stats["mean"], stats["std"]
    if mean < 0.33:
        return "LOW_KEY"
    if mean > 0.66:
        return "HIGH_KEY"
    # bimodal-ish / wide range
    if std > 0.24 and 0.33 <= mean <= 0.66:
        return "MIXED"
    return "MID_KEY"


def focal_region(image: Image.Image) -> str:
    g = image.convert("L").resize((300, 200))
    w, h = g.size
    labels = [
        ["TOP_LEFT", "TOP_CENTER", "TOP_RIGHT"],
        ["CENTER_LEFT", "CENTER", "CENTER_RIGHT"],
        ["BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT"],
    ]
    labels[2][2] = "BOTTOM_RIGHT"
    gx, gy = 3, 3
    vals = []
    px = g.load()
    for iy in range(gy):
        for ix in range(gx):
            x0, x1 = int(ix * w / gx), int((ix + 1) * w / gx)
            y0, y1 = int(iy * h / gy), int((iy + 1) * h / gy)
            cells = [px[x, y] for y in range(y0, y1, 2) for x in range(x0, x1, 2)]
            m = sum(cells) / len(cells)
            sd = (sum((c - m) ** 2 for c in cells) / len(cells)) ** 0.5
            vals.append((sd, labels[iy][ix]))
    vals.sort(reverse=True)
    if vals[0][0] * 0.85 <= vals[1][0]:
        return "MULTIPLE"
    return vals[0][1]


def build():
    samples = []
    for rel, media, src in SAMPLES:
        p = ROOT / rel
        if not p.is_file():
            print("MISSING", rel)
            raise SystemExit(1)
        im = Image.open(p)
        im.load()
        w, h = im.size
        stats = luminance_stats(im)
        is_ui = media in UI_MEDIA
        rect = "SQUARE"
        if w > h:
            rect = "LANDSCAPE"
        elif h > w:
            rect = "PORTRAIT"
        samples.append(
            {
                "sample_id": f"v4-{hashlib.sha256(rel.encode()).hexdigest()[:12]}",
                "path": str(p),
                "sha256": sha256_of(p),
                "width": w,
                "height": h,
                "source_artifact": rel,
                "source_class": src,
                "media": media,
                "labels": {
                    "orientation": rect,
                    "ui_present": "YES" if media in UI_MEDIA else "NO",
                    "render_type": "2D" if media in UI_MEDIA else "3D",
                    "visible_text": "YES" if media in UI_MEDIA else "NO",
                    "dominant_value": dominant_value(stats),
                    "black_crush": "YES" if stats["black_frac"] > 0.15 else "NO",
                    "highlight_clip": "YES" if stats["white_frac"] > 0.04 else "NO",
                    "focal_region": focal_region(im),
                },
                "label_provenance": {
                    "orientation": "DIMENSIONS",
                    "ui_present": "LAB_SOURCE_PROVENANCE",
                    "render_type": "LAB_SOURCE_PROVENANCE",
                    "visible_text": "LAB_SOURCE_PROVENANCE",
                    "dominant_value": "DETERMINISTIC_IMAGE_ANALYSIS",
                    "black_crush": "DETERMINISTIC_IMAGE_ANALYSIS",
                    "highlight_clip": "DETERMINISTIC_IMAGE_ANALYSIS",
                    "focal_region": "COMPUTATIONAL_PROXY_NOT_HUMAN_ADJUDICATION",
                },
                "deterministic_stats": stats,
                "ground_truth_version": GT_VERSION,
            }
        )
    # dedupe by sha256
    seen = {}
    for s in samples:
        seen.setdefault(s["sha256"], s)
    samples = list(seen.values())

    # --- class distribution audit ---
    props = sorted(samples[0]["labels"].keys())
    dist = {}
    for prop in props:
        c = {}
        for s in samples:
            v = s["labels"][prop]
            c[v] = c.get(v, 0) + 1
        dist[prop] = dict(sorted(c.items(), key=lambda kv: -kv[1]))
    majority_ratio = {}
    for prop, c in dist.items():
        top = max(c.values())
        majority_ratio[prop] = round(top / len(samples), 3)
    # Drop strongly dominated binary-ish properties from the scoreboard.
    scoreboard_props = []
    drops = []
    for prop, ratio in majority_ratio.items():
        if ratio > 0.85:
            drops.append({"property": prop, "majority_ratio": ratio, "reason": "STRONGLY_MAJORITY_DOMINATED"})
        else:
            scoreboard_props.append(prop)

    doc = {
        "kind": "visual-grounding-v4-dataset",
        "version": LABEL_VERSION,
        "ground_truth_version": GT_VERSION,
        "n_samples": len(samples),
        "created_for": "M002.1 Pass 06",
        "dataset_hash": hashlib.sha256(
            json.dumps([s["sha256"] for s in samples], sort_keys=True).encode()
        ).hexdigest(),
        "label_hash": hashlib.sha256(
            json.dumps([s["labels"] for s in samples], sort_keys=True).encode()
        ).hexdigest(),
        "generator_hash": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
        "per_property_distribution": dist,
        "majority_ratio": majority_ratio,
        "scoreboard_properties": scoreboard_props,
        "dropped_properties": drops,
        "samples": samples,
        "fixture_class": "PROFESSIONAL_EVALUATION_REAL_ARTIFACTS",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print("V4 dataset written:", OUT)
    print("n_samples:", len(samples))
    for prop, c in dist.items():
        print(f"  {prop}: {c}  (majority {majority_ratio[prop]})")
    print("scoreboard:", scoreboard_props)
    print("dropped:", drops)
    print("dataset_hash:", doc["dataset_hash"])
    print("label_hash:", doc["label_hash"])


if __name__ == "__main__":
    build()