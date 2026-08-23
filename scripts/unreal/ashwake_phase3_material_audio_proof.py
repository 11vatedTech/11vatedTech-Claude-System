#!/usr/bin/env python3
"""Generate Ashwake Phase 3 material lookdev and audio-direction proof.

Founder-facing outputs use aliases only. Private report retains concept-specific labels.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import math
import random
import wave
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageStat

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ALIAS_MAP = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/private/blind-alias-map.json"
DEFAULT_CAPTURE_ROOT = ROOT / "artifacts/unreal/health/ashwake-environment-apprenticeship-phase3/material-audio-proof"
DEFAULT_PRIVATE_OUT = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/private/material-audio-proof.json"
DEFAULT_PUBLIC_OUT = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/founder-package/material-audio-index.json"

LIGHTS = {
    "NEUTRAL_LIGHT": {"ambient": 0.68, "direction": (0.0, -0.2, 1.0), "color": (236, 232, 220), "rim": 0.16},
    "GRAZING_LIGHT": {"ambient": 0.42, "direction": (-0.85, -0.18, 0.22), "color": (255, 226, 184), "rim": 0.46},
    "PRODUCTION_LIGHT": {"ambient": 0.50, "direction": (-0.45, -0.35, 0.66), "color": (255, 182, 100), "rim": 0.28},
}

MATERIALS: dict[str, list[dict[str, Any]]] = {
    "CINDERWORKS_ABBEY": [
        {"name": "soot brass", "class": "metal", "base": (92, 62, 33), "roughness": 0.62, "metallic": 0.9, "grain": "scratched", "emissive": 0.0},
        {"name": "heat-aged iron", "class": "metal", "base": (58, 54, 50), "roughness": 0.48, "metallic": 0.95, "grain": "pitted", "emissive": 0.05},
        {"name": "basalt", "class": "stone", "base": (42, 39, 36), "roughness": 0.86, "metallic": 0.0, "grain": "porous", "emissive": 0.0},
        {"name": "furnace ceramic", "class": "ceramic", "base": (126, 102, 76), "roughness": 0.68, "metallic": 0.0, "grain": "cracked", "emissive": 0.08},
        {"name": "dirty refractive glass", "class": "glass", "base": (82, 100, 96), "roughness": 0.22, "metallic": 0.0, "grain": "streaked", "emissive": 0.0},
    ],
    "EMBER_HOSPICE": [
        {"name": "aged sacred metal", "class": "metal", "base": (104, 82, 54), "roughness": 0.58, "metallic": 0.85, "grain": "scratched", "emissive": 0.0},
        {"name": "life-support glass membrane", "class": "glass", "base": (88, 118, 108), "roughness": 0.18, "metallic": 0.0, "grain": "streaked", "emissive": 0.08},
        {"name": "ceramic", "class": "ceramic", "base": (168, 154, 132), "roughness": 0.56, "metallic": 0.0, "grain": "cracked", "emissive": 0.0},
        {"name": "ritual textile surface", "class": "textile", "base": (116, 84, 64), "roughness": 0.92, "metallic": 0.0, "grain": "woven", "emissive": 0.0},
        {"name": "ash residue", "class": "ash-soot", "base": (55, 52, 48), "roughness": 0.98, "metallic": 0.0, "grain": "powder", "emissive": 0.0},
    ],
    "FALLEN_SUN_ORCHARD": [
        {"name": "volcanic soil", "class": "stone", "base": (62, 54, 44), "roughness": 0.94, "metallic": 0.0, "grain": "porous", "emissive": 0.0},
        {"name": "charred organic material", "class": "organic", "base": (42, 34, 26), "roughness": 0.82, "metallic": 0.0, "grain": "fibrous", "emissive": 0.02},
        {"name": "luminous seed surface", "class": "heated-emissive", "base": (192, 118, 38), "roughness": 0.34, "metallic": 0.1, "grain": "veined", "emissive": 0.72},
        {"name": "ash-coated stone", "class": "ash-soot", "base": (118, 112, 98), "roughness": 0.9, "metallic": 0.0, "grain": "powder", "emissive": 0.0},
        {"name": "heat-reactive vegetation", "class": "organic", "base": (64, 74, 48), "roughness": 0.76, "metallic": 0.0, "grain": "veined", "emissive": 0.18},
    ],
}

AUDIO_STATES = ["AMBIENCE", "READING_PULSE", "SAFE_SIGNAL", "HOSTILE_SIGNAL", "SUCCESS_RESPONSE"]


def normalize(v: tuple[float, float, float]) -> tuple[float, float, float]:
    mag = math.sqrt(sum(x * x for x in v)) or 1.0
    return tuple(x / mag for x in v)


def procedural_height(width: int, height: int, material: dict[str, Any], seed: int) -> Image.Image:
    rng = random.Random(seed)
    img = Image.new("L", (width, height), 128)
    pix = img.load()
    for y in range(height):
        for x in range(width):
            noise = rng.randint(-26, 26)
            band = int(18 * math.sin((x * 0.035) + seed) + 10 * math.sin((y * 0.041) + seed * 0.3))
            val = 128 + noise + band
            grain = material["grain"]
            if grain == "scratched" and (x + rng.randint(0, 18)) % 31 == 0:
                val += 70
            elif grain == "pitted" and rng.random() < 0.018:
                val -= 90
            elif grain == "porous" and rng.random() < 0.05:
                val -= 42
            elif grain == "cracked" and (abs(math.sin((x + y + seed) * 0.032)) > 0.985):
                val -= 82
            elif grain == "streaked" and (x + seed) % 47 < 3:
                val += 54
            elif grain == "woven":
                val += 24 if (x // 9 + y // 7) % 2 == 0 else -18
            elif grain == "powder" and rng.random() < 0.11:
                val += rng.randint(-60, 24)
            elif grain == "fibrous":
                val += int(42 * math.sin((x * 0.08) + math.sin(y * 0.05)))
            elif grain == "veined" and abs(math.sin((x * 0.025) + (y * 0.053) + seed)) > 0.94:
                val += 85
            pix[x, y] = max(0, min(255, val))
    return img.filter(ImageFilter.GaussianBlur(radius=0.45))


def render_material(material: dict[str, Any], light: dict[str, Any], out_path: Path, seed: int) -> dict[str, Any]:
    w, h = 640, 420
    height = procedural_height(w, h, material, seed)
    hpix = height.load()
    base = material["base"]
    ldx, ldy, ldz = normalize(light["direction"])
    ambient = float(light["ambient"])
    rim = float(light["rim"])
    lcolor = light["color"]
    rough = float(material["roughness"])
    metallic = float(material["metallic"])
    emissive = float(material["emissive"])
    contrast_boost = 1.0 + (rough * 0.22) + (metallic * 0.14)
    out = Image.new("RGB", (w, h))
    opix = out.load()
    for y in range(h):
        vgrad = 0.92 + 0.16 * (1.0 - (y / max(1, h - 1)))
        for x in range(w):
            hl = hpix[max(0, x - 1), y] / 255.0
            hr = hpix[min(w - 1, x + 1), y] / 255.0
            hu = hpix[x, max(0, y - 1)] / 255.0
            hd = hpix[x, min(h - 1, y + 1)] / 255.0
            nx, ny, nz = normalize(((hl - hr) * 3.2, (hu - hd) * 3.2, 1.0))
            ndotl = max(0.0, nx * ldx + ny * ldy + nz * ldz)
            backlight = max(0.0, -nx * ldx - ny * ldy + nz * max(0.2, ldz * 0.35))
            spec = max(0.0, ndotl) ** (8.0 + (1.0 - rough) * 90.0) * (0.12 + metallic * 0.55 + (1.0 - rough) * 0.2)
            hval = hpix[x, y] / 255.0
            soot = 0.82 + (hval - 0.5) * contrast_boost
            fill = ambient + ndotl * 0.72 + backlight * rim
            occlusion_lift = 18.0 + rough * 18.0
            r = occlusion_lift + base[0] * soot * fill * vgrad + lcolor[0] * spec + base[0] * emissive * (0.6 + hval)
            g = occlusion_lift + base[1] * soot * fill * vgrad + lcolor[1] * spec + base[1] * emissive * (0.6 + hval)
            b = occlusion_lift + base[2] * soot * fill * vgrad + lcolor[2] * spec + base[2] * emissive * (0.6 + hval)
            opix[x, y] = (max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))
    gray_pre = ImageOps.grayscale(out)
    pre_stat = ImageStat.Stat(gray_pre)
    if pre_stat.stddev[0] < 22.0:
        lift = int(max(0.0, 22.0 - pre_stat.stddev[0]) * 3.2)
        out = ImageOps.autocontrast(out, cutoff=0.2)
        if lift:
            overlay = Image.new("RGB", out.size, (lift, lift, lift))
            out = Image.blend(out, overlay, 0.08)
    # Add simple shape mask cue: material swatch on slab plus rounded sample disc.
    draw = ImageDraw.Draw(out, "RGBA")
    draw.rectangle((0, h - 58, w, h), fill=(0, 0, 0, 72))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path)
    gray = ImageOps.grayscale(out)
    stat = ImageStat.Stat(gray)
    hist = gray.histogram()
    total = w * h
    record = {
        "path": str(out_path),
        "bytes": out_path.stat().st_size,
        "width": w,
        "height": h,
        "material_class": material["class"],
        "roughness": rough,
        "metallic": metallic,
        "emissive": emissive,
        "light": next(k for k, v in LIGHTS.items() if v is light),
        "value_mean": round(stat.mean[0], 2),
        "value_stdev": round(stat.stddev[0], 2),
        "black_fraction_lt20": round(sum(hist[:20]) / total, 4),
        "highlight_fraction_ge245": round(sum(hist[245:]) / total, 4),
        "readability_gate": "FAIL" if stat.stddev[0] < 14 or sum(hist[:20]) / total > 0.45 or sum(hist[245:]) / total > 0.16 else "PASS",
    }
    return record


def make_contact_sheet(images: list[Path], out_path: Path, title: str) -> dict[str, Any]:
    thumbs = []
    for img_path in images:
        with Image.open(img_path) as img:
            thumb = img.convert("RGB")
            thumb.thumbnail((220, 150))
            tile = Image.new("RGB", (240, 190), (18, 18, 18))
            tile.paste(thumb, ((240 - thumb.width) // 2, 8))
            ImageDraw.Draw(tile).text((10, 164), img_path.stem[:28], fill=(210, 210, 210))
            thumbs.append(tile)
    cols = 5
    rows = max(1, math.ceil(len(thumbs) / cols))
    sheet = Image.new("RGB", (cols * 240, rows * 190 + 42), (10, 10, 10))
    ImageDraw.Draw(sheet).text((12, 12), title, fill=(235, 235, 235))
    for i, tile in enumerate(thumbs):
        sheet.paste(tile, ((i % cols) * 240, 42 + (i // cols) * 190))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return {"path": str(out_path), "exists": out_path.exists(), "bytes": out_path.stat().st_size}


def synth_audio(direction: str, state: str, out_path: Path, seconds: float = 3.0, sample_rate: int = 48000) -> dict[str, Any]:
    base = {
        "CINDERWORKS_ABBEY": 74.0,
        "EMBER_HOSPICE": 58.0,
        "FALLEN_SUN_ORCHARD": 66.0,
    }[direction]
    mult = {
        "AMBIENCE": 1.0,
        "READING_PULSE": 1.5,
        "SAFE_SIGNAL": 2.0,
        "HOSTILE_SIGNAL": 2.4,
        "SUCCESS_RESPONSE": 3.0,
    }[state]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * sample_rate)
    samples = bytearray()
    for n in range(frames):
        t = n / sample_rate
        pulse = 0.45 + 0.55 * math.sin(2 * math.pi * (0.55 if state != "HOSTILE_SIGNAL" else 2.7) * t)
        if state == "HOSTILE_SIGNAL":
            pulse *= 0.65 + 0.35 * math.sin(2 * math.pi * 11.0 * t)
        if state == "SUCCESS_RESPONSE":
            pulse = min(1.0, t / 0.8) * (0.8 + 0.2 * math.sin(2 * math.pi * 0.4 * t))
        tone = math.sin(2 * math.pi * base * mult * t) * 0.35
        overtone = math.sin(2 * math.pi * base * mult * 2.01 * t) * 0.12
        noise = math.sin(2 * math.pi * (base * 0.37) * t + math.sin(t * 9.0)) * 0.08
        val = (tone + overtone + noise) * pulse * 0.45
        sample = int(max(-1.0, min(1.0, val)) * 32767)
        samples += int(sample).to_bytes(2, byteorder="little", signed=True)
    with wave.open(str(out_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples)
    return {"path": str(out_path), "exists": out_path.exists(), "bytes": out_path.stat().st_size, "seconds": seconds, "state": state}


def public_record(private: dict[str, Any]) -> dict[str, Any]:
    return {
        "alias": private["alias"],
        "material_id": private.get("material_id"),
        "material_class": private.get("material_class"),
        "light": private.get("light"),
        "path": private.get("path"),
        "readability_gate": private.get("readability_gate"),
        "value_mean": private.get("value_mean"),
        "value_stdev": private.get("value_stdev"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--alias-map", type=Path, default=DEFAULT_ALIAS_MAP)
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE_ROOT)
    parser.add_argument("--private-out", type=Path, default=DEFAULT_PRIVATE_OUT)
    parser.add_argument("--public-out", type=Path, default=DEFAULT_PUBLIC_OUT)
    args = parser.parse_args()

    alias_data = json.loads(args.alias_map.read_text(encoding="utf-8"))
    aliases: dict[str, str] = alias_data["aliases"]
    material_records: list[dict[str, Any]] = []
    audio_records: list[dict[str, Any]] = []
    sheets: list[dict[str, Any]] = []

    for alias, direction in aliases.items():
        alias_root = args.capture_root / alias
        founder_root = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/founder-package" / alias / "material-audio"
        images_for_sheet: list[Path] = []
        for idx, material in enumerate(MATERIALS[direction], start=1):
            material_id = f"MATERIAL_{idx:02d}"
            for light_name, light in LIGHTS.items():
                out_path = founder_root / "materials" / light_name.lower() / f"{material_id.lower()}.png"
                seed_src = f"{direction}|{material['name']}|{light_name}".encode("utf-8")
                seed = int.from_bytes(hashlib.sha256(seed_src).digest()[:4], byteorder="little")
                rec = render_material(material, light, out_path, seed=seed)
                rec.update({"alias": alias, "direction_private": direction, "material_private_name": material["name"], "material_id": material_id})
                material_records.append(rec)
                images_for_sheet.append(out_path)
        sheets.append({"alias": alias, **make_contact_sheet(images_for_sheet, founder_root / "material-contact-sheet.png", f"{alias} material lookdev")})
        for state in AUDIO_STATES:
            out_path = founder_root / "audio" / f"{state.lower()}.wav"
            rec = synth_audio(direction, state, out_path)
            rec.update({"alias": alias, "direction_private": direction})
            audio_records.append(rec)

    material_gate = "PASS" if all(r.get("readability_gate") == "PASS" for r in material_records) else "FAIL"
    public = {
        "schema_version": 1,
        "kind": "ashwake-phase3-founder-material-audio-index",
        "date": "2026-08-21",
        "status": "PASS" if material_gate == "PASS" and all(a.get("exists") for a in audio_records) else "FAIL",
        "selection_status": "NO_FINAL_PRODUCTION_DIRECTION_SELECTED",
        "identity_rule": "Founder-facing records use aliases only.",
        "materials": [public_record(r) for r in material_records],
        "material_contact_sheets": sheets,
        "audio": [{k: v for k, v in a.items() if k not in {"direction_private"}} for a in audio_records],
        "evaluation_prompts": {
            "material_differentiation": ["Can viewer distinguish metal, stone, glass, organic, heated/emissive, ash/soot without labels?", "Do important materials collapse into same dark response under production light?"],
            "audio_direction": ["Is ambience distinct?", "Does safe signal teach opportunity?", "Does hostile signal warn before punishment?", "Does success response feel aligned with world?", "Is fatigue risk low?"],
        },
    }
    private = {
        "schema_version": 1,
        "kind": "ashwake-phase3-private-material-audio-proof",
        "date": "2026-08-21",
        "status": public["status"],
        "alias_map_private": str(args.alias_map),
        "materials": material_records,
        "audio": audio_records,
        "public_out": str(args.public_out),
        "claim_limits": ["Procedural material renders are lookdev studies, not final production shaders.", "Audio WAVs are minimal sonic language prototypes, not final mix."],
    }
    args.private_out.parent.mkdir(parents=True, exist_ok=True)
    args.public_out.parent.mkdir(parents=True, exist_ok=True)
    args.private_out.write_text(json.dumps(private, indent=2, ensure_ascii=False), encoding="utf-8")
    args.public_out.write_text(json.dumps(public, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": public["status"], "private_out": str(args.private_out), "public_out": str(args.public_out)}, indent=2))
    return 0 if public["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
