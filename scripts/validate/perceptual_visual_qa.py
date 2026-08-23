#!/usr/bin/env python3
"""Perceptual visual QA for rendered evidence.

Structural render success is not perceptual readability. This diagnostic layer
measures luminance distribution, black crush, highlight clipping, subject
occupancy, central-vs-background separation, and composition bounds. Metrics
are diagnostic evidence for review, not an artistic quality claim.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "media"))
from vtmedia.common import resolve_tool, run  # type: ignore


def _magick(path: Path, args: list[str]) -> str:
    exe = resolve_tool("magick")
    if not exe:
        raise RuntimeError("magick_not_found")
    result = run([exe, str(path), *args], timeout=90)
    if result.get("returncode") != 0:
        raise RuntimeError((result.get("stderr") or "magick_failed")[-400:])
    return (result.get("stdout") or "").strip()


def _mean(path: Path, crop: str | None = None) -> float:
    args = []
    if crop:
        args += ["-crop", crop, "+repage"]
    args += ["-colorspace", "Gray", "-format", "%[fx:mean]", "info:"]
    return float(_magick(path, args))


def _fraction_above(path: Path, threshold: str) -> float:
    return float(_magick(path, ["-colorspace", "Gray", "-threshold", threshold, "-format", "%[fx:mean]", "info:"]))


def _bbox(path: Path, threshold: str = "65%") -> dict | None:
    raw = _magick(path, ["-colorspace", "Gray", "-threshold", threshold, "-trim", "-format", "%wx%h%O", "info:"])
    match = re.fullmatch(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", raw)
    if not match:
        return None
    w, h, x, y = int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))
    return {"x": x, "y": y, "width": w, "height": h}


def analyze(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "status": "FAIL", "failures": ["missing_image"], "warnings": []}
    dims_raw = _magick(path, ["-format", "%wx%h", "info:"])
    dm = re.fullmatch(r"(\d+)x(\d+)", dims_raw)
    width, height = (int(dm.group(1)), int(dm.group(2))) if dm else (0, 0)
    mean = _mean(path)
    black_crush = 1.0 - _fraction_above(path, "8%")
    highlight_clip = _fraction_above(path, "95%")
    central = _mean(path, "50%x70%+25%+15%")
    corner = _mean(path, "12%x12%+0+0")
    separation = central - corner
    bbox = _bbox(path, "65%")
    occupancy = ((bbox["width"] * bbox["height"]) / (width * height)) if bbox and width and height else 0.0
    failures: list[str] = []
    warnings: list[str] = []
    if mean < 0.045 or black_crush > 0.97:
        failures.append("severe_underexposure_or_blank_frame")
    elif mean < 0.09 or black_crush > 0.90:
        warnings.append("black_crush_subject_may_be_unreadable")
    if central < 0.06 or separation < 0.025:
        warnings.append("low_subject_background_separation")
    if occupancy < 0.025:
        warnings.append("subject_occupancy_too_small")
    elif occupancy > 0.88:
        warnings.append("subject_or_threshold_occupancy_too_large")
    if highlight_clip > 0.25:
        warnings.append("highlight_clipping_may_hide_material_response")
    return {
        "path": str(path),
        "dimensions": [width, height],
        "luminance": {
            "mean": round(mean, 6),
            "central_mean": round(central, 6),
            "corner_mean": round(corner, 6),
            "subject_background_separation": round(separation, 6),
            "black_crush_fraction_below_8_percent": round(black_crush, 6),
            "highlight_clip_fraction_above_95_percent": round(highlight_clip, 6),
        },
        "composition": {"threshold": "65% luminance (bright subject diagnostic)", "subject_bbox": bbox, "subject_occupancy": round(occupancy, 6)},
        "failures": failures,
        "warnings": warnings,
        "status": "FAIL" if failures else "WARN" if warnings else "PASS",
        "interpretation": "diagnostic metrics require human/professional visual review; they do not prove artistic quality",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--strict", action="store_true", help="return nonzero on diagnostic failures")
    args = parser.parse_args()
    records = []
    for image in args.images:
        try:
            record = analyze(image)
        except Exception as exc:
            record = {"path": str(image), "status": "FAIL", "failures": [f"qa_error:{type(exc).__name__}:{exc}"], "warnings": []}
        records.append(record)
        print(f"{record['status']:4} {image} failures={len(record.get('failures', []))} warnings={len(record.get('warnings', []))}")
    report = {"schema_version": 1, "tool": "perceptual_visual_qa", "records": records,
              "ok": not any(r.get("failures") for r in records)}
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 1 if args.strict and not report["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
