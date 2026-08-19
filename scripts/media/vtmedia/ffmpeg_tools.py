from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from .common import ensure_dir, run, write_json


def probe(input_path: Path, out_json: Path | None = None) -> dict[str, Any]:
    result = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(input_path)], timeout=60)
    data = {"command": result["argv"], "returncode": result.get("returncode"), "stderr": result.get("stderr", "")}
    try:
        data["ffprobe"] = json.loads(result.get("stdout") or "{}")
    except json.JSONDecodeError:
        data["raw_stdout"] = result.get("stdout", "")
    if out_json:
        write_json(out_json, data)
    return data


def make_test_video(out_path: Path, seconds: int = 2, size: str = "1280x720", fps: int = 24) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate={fps}",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
        "-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out_path)
    ], timeout=120)


def make_test_audio(out_path: Path, seconds: int = 2) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=550:sample_rate=48000", "-t", str(seconds), "-c:a", "pcm_s16le", str(out_path)], timeout=60)


def transcode(input_path: Path, out_path: Path) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-i", str(input_path), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out_path)], timeout=180)


def thumbnail(input_path: Path, out_path: Path, timestamp: str = "00:00:01") -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-ss", timestamp, "-i", str(input_path), "-frames:v", "1", str(out_path)], timeout=60)


def contact_sheet(input_path: Path, out_path: Path, cols: int = 4, rows: int = 3) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    frames = cols * rows
    return run(["ffmpeg", "-y", "-i", str(input_path), "-vf", f"fps={frames}/2,scale=320:-1,tile={cols}x{rows}", "-frames:v", "1", str(out_path)], timeout=90)


def normalize_audio(input_path: Path, out_path: Path) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-i", str(input_path), "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", str(out_path)], timeout=90)


def waveform(input_path: Path, out_path: Path, size: str = "1280x240") -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-i", str(input_path), "-filter_complex", f"showwavespic=s={size}:colors=#67d9ff", "-frames:v", "1", str(out_path)], timeout=60)


def image_sequence_to_video(pattern: str, out_path: Path, fps: int = 24) -> dict[str, Any]:
    """Assemble a numbered image sequence (e.g. turntable-%03d.png) into an
    H.264 motion-preview video. This is how animation/VFX evidence becomes
    observable motion instead of screenshots."""
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-framerate", str(fps), "-i", pattern,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)], timeout=180)


def resize_image(input_path: Path, out_path: Path, width: int) -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-i", str(input_path), "-vf", f"scale={width}:-1:flags=lanczos", str(out_path)], timeout=60)


def highres_test(out_path: Path, size: str = "4096x4096") -> dict[str, Any]:
    ensure_dir(out_path.parent)
    return run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"mandelbrot=size={size}:rate=1", "-frames:v", "1", "-pix_fmt", "rgb48le", str(out_path)], timeout=120)
