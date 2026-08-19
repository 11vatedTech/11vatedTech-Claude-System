from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Any
from .common import ensure_dir, resolve_tool, run, sha256_file


def png_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()[:32]
    if data.startswith(b"\x89PNG\r\n\x1a\n") and data[12:16] == b"IHDR":
        return struct.unpack(">II", data[16:24])
    return None


def inspect_image(path: Path) -> dict[str, Any]:
    rec = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return rec
    rec.update({"bytes": path.stat().st_size, "sha256": sha256_file(path), "suffix": path.suffix.lower()})
    if path.suffix.lower() == ".png":
        dims = png_dimensions(path)
        if dims:
            rec["width"], rec["height"] = dims
    return rec


def magick_available() -> bool:
    return resolve_tool("magick") is not None


def _magick(argv: list[str], timeout: int = 120) -> dict[str, Any]:
    exe = resolve_tool("magick")
    if not exe:
        return {"error": "magick_missing", "argv": argv}
    return run([exe, *argv], timeout=timeout)


def make_gradient(out_path: Path, width: int = 1024, height: int = 768) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    r = _magick(["-size", f"{width}x{height}", "gradient:#0b1020-#ffd166", "-colorspace", "sRGB", str(out_path)], timeout=60)
    if r.get("returncode") == 0 and out_path.exists():
        return r
    return run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"gradients=size={width}x{height}:c0=0x0b1020:c1=0xffd166", "-frames:v", "1", str(out_path)], timeout=60)


def alpha_test(out_path: Path, width: int = 512, height: int = 512) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    r = _magick(["-size", f"{width}x{height}", "xc:none", "-fill", "#67d9ffaa", "-draw", "circle 256,256 256,48", str(out_path)], timeout=60)
    if r.get("returncode") == 0 and out_path.exists():
        return r
    return run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black@0.0:size={width}x{height}", "-vf", "format=rgba,drawbox=x=96:y=96:w=320:h=320:color=0x67d9ffaa:t=fill", "-frames:v", "1", str(out_path)], timeout=60)


def compare_images(base: Path, current: Path, diff_out: Path | None = None) -> dict[str, Any]:
    """Real pixel diff via `magick compare -metric AE`, with ffmpeg PSNR and
    hash-only fallbacks in that order of fidelity."""
    exe = resolve_tool("magick")
    if exe:
        ensure_dir(diff_out.parent) if diff_out else None
        args = [exe, "compare", "-metric", "AE", str(base), str(current)]
        args += [str(diff_out)] if diff_out else ["null:"]
        r = run(args, timeout=60)
        m = re.search(r"(\d+)", r.get("stderr") or "")
        ae = int(m.group(1)) if m else None
        return {
            "mode": "imagemagick_absolute_error",
            "absolute_error": ae,
            "command": r,
            "passed": r.get("returncode") in (0, 1),
            "visual_equivalence_claim": ae == 0,
        }
    if resolve_tool("ffmpeg"):
        r = run(["ffmpeg", "-i", str(base), "-i", str(current), "-lavfi", "psnr", "-f", "null", "-"], timeout=60)
        m = re.search(r"average:([\d.eE+-]+|inf)", r.get("stderr") or "")
        raw = m.group(1) if m else None
        db = None if raw in (None, "inf") else float(raw)
        return {
            "mode": "ffmpeg_psnr",
            "psnr_db": db,
            "command": r,
            "passed": r.get("returncode") == 0,
            "visual_equivalence_claim": db is None,
        }
    b, c = sha256_file(base), sha256_file(current)
    return {"mode": "hash_only", "base_sha256": b, "current_sha256": c, "equal": b == c, "visual_equivalence_claim": False}


def contact_sheet(images: list[Path], out_path: Path) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    exe = resolve_tool("magick")
    if exe:
        return run([exe, *[str(p) for p in images], "-thumbnail", "320x240", "-background", "#111111", "-gravity", "center", "+smush", "8", str(out_path)], timeout=90)
    # ffmpeg fallback for first image only
    if images:
        return run(["ffmpeg", "-y", "-i", str(images[0]), str(out_path)], timeout=60)
    return {"error": "no images"}
