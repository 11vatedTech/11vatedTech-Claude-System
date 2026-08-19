from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from shutil import which
from .common import ensure_dir, run, sha256_file


def inspect_svg(path: Path) -> dict[str, Any]:
    rec = {"path": str(path), "exists": path.exists()}
    if not path.exists(): return rec
    rec.update({"bytes": path.stat().st_size, "sha256": sha256_file(path)})
    try:
        root = ET.parse(path).getroot()
        rec["root"] = root.tag
        rec["width"] = root.attrib.get("width")
        rec["height"] = root.attrib.get("height")
        rec["viewBox"] = root.attrib.get("viewBox")
        rec["elements"] = sum(1 for _ in root.iter())
        text = path.read_text(encoding="utf-8", errors="ignore")
        rec["has_remote_refs"] = "http://" in text or "https://" in text
        rec["valid"] = root.tag.endswith("svg")
    except Exception as exc:
        rec["valid"] = False
        rec["error"] = type(exc).__name__ + ": " + str(exc)
    return rec


def make_svg(path: Path) -> dict[str, Any]:
    ensure_dir(path.parent)
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
  <defs>
    <linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop stop-color="#0b1020"/><stop offset="1" stop-color="#ffd166"/></linearGradient>
  </defs>
  <rect width="1600" height="900" fill="#07070d"/>
  <path d="M180 700 C 420 140, 760 100, 1420 210" fill="none" stroke="url(#g)" stroke-width="48" stroke-linecap="round"/>
  <circle cx="420" cy="360" r="132" fill="#67d9ff" fill-opacity="0.78"/>
  <text x="160" y="180" fill="#fff8e8" font-size="96" font-family="Arial, sans-serif" font-weight="700">11VT VECTOR</text>
</svg>'''
    path.write_text(svg, encoding="utf-8")
    return inspect_svg(path)


def rasterize(svg: Path, out_png: Path, width: int = 1600) -> dict[str, Any]:
    ensure_dir(out_png.parent)
    if which("inkscape"):
        return run(["inkscape", str(svg), "--export-type=png", f"--export-filename={out_png}", f"--export-width={width}"], timeout=90)
    return {"error": "inkscape_missing", "availability": "MISSING"}
