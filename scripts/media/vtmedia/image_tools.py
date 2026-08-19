from __future__ import annotations

import struct
from pathlib import Path
from typing import Any
from .common import ensure_dir, run, sha256_file


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
    from shutil import which
    return which("magick") is not None


def make_gradient(out_path: Path, width: int = 1024, height: int = 768) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    if magick_available():
        return run(["magick", "-size", f"{width}x{height}", "gradient:#0b1020-#ffd166", "-colorspace", "sRGB", str(out_path)], timeout=60)
    return run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"gradients=size={width}x{height}:c0=0x0b1020:c1=0xffd166", "-frames:v", "1", str(out_path)], timeout=60)


def alpha_test(out_path: Path, width: int = 512, height: int = 512) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    if magick_available():
        return run(["magick", "-size", f"{width}x{height}", "xc:none", "-fill", "#67d9ffaa", "-draw", "circle 256,256 256,48", str(out_path)], timeout=60)
    return run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black@0.0:size={width}x{height}", "-vf", "format=rgba,drawbox=x=96:y=96:w=320:h=320:color=0x67d9ffaa:t=fill", "-frames:v", "1", str(out_path)], timeout=60)


def compare_images(base: Path, current: Path, diff_out: Path | None = None) -> dict[str, Any]:
    if magick_available() and diff_out:
        ensure_dir(diff_out.parent)
        r = run(["magick", "compare", "-metric", "AE", str(base), str(current), str(diff_out)], timeout=60)
        return {"mode": "imagemagick_absolute_error", "command": r, "passed": r.get("returncode") in (0, 1)}
    return {"mode": "hash_only", "base_sha256": sha256_file(base), "current_sha256": sha256_file(current), "equal": sha256_file(base) == sha256_file(current), "visual_equivalence_claim": False}


def contact_sheet(images: list[Path], out_path: Path) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    if magick_available():
        return run(["magick", *[str(p) for p in images], "-thumbnail", "320x240", "-background", "#111111", "-gravity", "center", "+smush", "8", str(out_path)], timeout=90)
    # ffmpeg fallback for first image only
    if images:
        return run(["ffmpeg", "-y", "-i", str(images[0]), str(out_path)], timeout=60)
    return {"error": "no images"}
