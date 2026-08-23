#!/usr/bin/env python3
"""Capture Ashwake Environment Apprenticeship Phase 3 blind evidence.

Founder-facing outputs use OPTION_A/B/C only. Private reports may keep the
alias-to-direction map under docs/evidence/.../private.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import statistics
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from runtime_evidence import run_unreal_process

try:
    from PIL import Image, ImageOps, ImageStat
except Exception:  # pragma: no cover
    Image = None
    ImageOps = None
    ImageStat = None

ROOT = Path(__file__).resolve().parents[2]
# Smart App Control blocks newly packaged unsigned exes, so runtime evidence is
# captured through the Epic-signed UnrealEditor.exe running the project in -game
# mode with the freshly built project DLL (which contains all Phase 3 logic).
DEFAULT_EXE = Path(os.environ.get("UNREAL_ENGINE_ROOT", "C:/Program Files/Epic Games/UE_5.8")) / "Engine/Binaries/Win64/UnrealEditor.exe"
DEFAULT_PROJECT = ROOT / "artifacts/unreal/calibration/FoundryCalibration.uproject"
DEFAULT_ALIAS_MAP = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/private/blind-alias-map.json"
DEFAULT_CAPTURE_ROOT = ROOT / "artifacts/unreal/health/ashwake-environment-apprenticeship-phase3"
DEFAULT_OUT = ROOT / "artifacts/unreal/health/ashwake-environment-apprenticeship-phase3-evidence.json"
DEFAULT_PUBLIC_OUT = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/founder-package/evidence-index.json"
MAP = "/Game/Calibration/Maps/EmberveilCalibration"
REVIEW_STATES = [
    "SPAWN",
    "FIRST_LANDMARK",
    "APPROACH",
    "READING",
    "SAFE_WINDOW",
    "HOSTILE",
    "REJECTED_INTERACTION",
    "ACCEPTED_INTERACTION",
    "ONE_COAL_RESTORED",
    "FINAL_CLIMAX_DIRECTION",
    "ENVIRONMENT_OVERVIEW",
]
GRAYSCALE_STATES = ["SPAWN", "SAFE_WINDOW", "HOSTILE", "ONE_COAL_RESTORED"]
STATE_DEMO_STATES = ["READING", "SAFE_WINDOW", "HOSTILE", "ONE_COAL_RESTORED", "FAILURE"]
REQUIRED_MARKERS = [
    "ASHWAKE_MAP_BEGINPLAY",
    "ASHWAKE_GAMEPLAY_BEGIN",
    "ASHWAKE_ENVIRONMENT Direction=",
    "ASHWAKE_RELIQUARY_PLACED",
    "ASHWAKE_APPRENTICESHIP_LABS",
    "ASHWAKE_PHASE3_REVIEW_STATE",
    "VISUAL_PROOF_BEGIN",
    "SCREENSHOT_REQUESTED",
]
STATE_QUESTIONS = [
    "What do you think is happening?",
    "Is this safe, dangerous, opportunity, success, or failure?",
    "How confident are you?",
]
FOUNDER_QUESTIONS = [
    "Which world makes you most curious to explore?",
    "Which feels most original?",
    "Which feels most like a real place rather than a test level?",
    "Which relic interaction is easiest to understand?",
    "Which SAFE state is clearest?",
    "Which HOSTILE state is clearest?",
    "Which restoration event feels most meaningful?",
    "Which world has the strongest emotional identity?",
    "Which looks closest to professional game quality?",
    "Which feels like it could become a larger universe?",
    "Which one would you personally want to keep playing?",
    "What looks primitive in each?",
    "What confuses you in each?",
    "What would you combine, if anything?",
]


def png_info(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return info
    info["bytes"] = path.stat().st_size
    data = path.read_bytes()[:32]
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        info.update({"format": "png", "width": width, "height": height})
    else:
        info["format"] = "unknown"
    return info


def image_metrics(path: Path, grayscale_out: Path | None = None) -> dict[str, Any]:
    info = png_info(path)
    if not path.exists() or Image is None:
        info.update({"analysis_status": "UNAVAILABLE", "reason": "pillow_missing_or_image_missing"})
        return info
    with Image.open(path) as raw:
        img = raw.convert("RGB")
        gray = ImageOps.grayscale(img)
        if grayscale_out:
            grayscale_out.parent.mkdir(parents=True, exist_ok=True)
            gray.save(grayscale_out)
        stat = ImageStat.Stat(gray)
        values = list(gray.getdata())
        total = len(values) or 1
        hist = gray.histogram()
        blacks = sum(hist[:20]) / total
        shadows = sum(hist[20:70]) / total
        midtones = sum(hist[70:180]) / total
        highlights = sum(hist[180:245]) / total
        clipping = sum(hist[245:]) / total
        mean = stat.mean[0]
        stdev = stat.stddev[0]
        sorted_values = sorted(values)
        def pct(q: float) -> int:
            idx = min(len(sorted_values) - 1, max(0, int(q * (len(sorted_values) - 1))))
            return sorted_values[idx]
        # Center versus border contrast as crude subject/background separation proxy.
        w, h = gray.size
        center = gray.crop((w // 3, h // 3, 2 * w // 3, 2 * h // 3))
        border_mask = Image.new("L", gray.size, 0)
        border_values = []
        px = gray.load()
        bx = max(1, w // 8)
        by = max(1, h // 8)
        for y in range(h):
            for x in range(w):
                if x < bx or x >= w - bx or y < by or y >= h - by:
                    border_values.append(px[x, y])
        center_mean = ImageStat.Stat(center).mean[0]
        border_mean = statistics.mean(border_values) if border_values else mean
        info.update({
            "analysis_status": "PASS",
            "value_mean": round(mean, 2),
            "value_stdev": round(stdev, 2),
            "p05": pct(0.05),
            "p50": pct(0.50),
            "p95": pct(0.95),
            "black_crush_fraction_lt20": round(blacks, 4),
            "shadow_fraction_20_69": round(shadows, 4),
            "midtone_fraction_70_179": round(midtones, 4),
            "highlight_fraction_180_244": round(highlights, 4),
            "highlight_clipping_fraction_ge245": round(clipping, 4),
            "center_value_mean": round(center_mean, 2),
            "border_value_mean": round(border_mean, 2),
            "center_border_delta": round(abs(center_mean - border_mean), 2),
            "black_crush_gate": "FAIL" if blacks > 0.34 else "PASS",
            "highlight_clip_gate": "FAIL" if clipping > 0.08 else "PASS",
            "midtone_gate": "FAIL" if midtones < 0.18 else "PASS",
            "separation_gate": "FAIL" if abs(center_mean - border_mean) < 8.0 and stdev < 28.0 else "PASS",
        })
    return info


def run_runtime(executable: Path, run_dir: Path, direction: str, alias: str, state: str, timeout: int, no_hud: bool, performance_proxy: bool = False, shots: int = 1) -> dict[str, Any]:
    screenshot_dir = run_dir / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "runtime.log"
    args = [
        str(executable),
        str(DEFAULT_PROJECT.resolve()),
        MAP,
        "-game",
        "-unattended",
        "-nop4",
        "-nosplash",
        "-stdout",
        "-FullStdOutLogOutput",
        "-windowed",
        "-ResX=1280",
        "-ResY=720",
        f"-AshwakeEnvironmentDirection={direction}",
        "-AshwakeVisualProof",
        "-AshwakeVisualProofExit",
        f"-AshwakeVisualProofDir={screenshot_dir}",
        f"-AshwakeVisualProofShots={shots}",
        f"-AshwakePhase3ReviewState={state}",
        f"-FoundryScenario=environment_apprenticeship_phase3_{alias.lower()}_{state.lower()}",
        "-trace=default,frame,bookmark,cpu,loadtime,counters",
        f"-tracefile={run_dir / 'runtime.utrace'}",
        "-tracefiletrunc",
        "-csvCaptureFrames=180",
        "-csvCategories=FrameTime,Game,Rendering,RHI,GPU,CsvProfiler",
        "-csvGpuStats",
    ]
    if no_hud:
        args.append("-AshwakeNoHUD")
    if performance_proxy:
        args.append("-AshwakePhase3PerformanceProxy")
    result = run_unreal_process(args, executable.parent, timeout, log_path, expected_controlled_shutdown=True, fallback_log_roots=[DEFAULT_PROJECT.parent / "Saved" / "Logs"])
    text = result.get("complete_log_text", "")
    screenshots = [png_info(p) for p in sorted(screenshot_dir.glob("*.png"))]
    markers = {marker: marker in text for marker in REQUIRED_MARKERS}
    counts = {
        "screenshots_requested": len(re.findall(r"SCREENSHOT_REQUESTED", text)),
        "phase3_review_state": len(re.findall(r"ASHWAKE_PHASE3_REVIEW_STATE", text)),
        "performance_proxy": len(re.findall(r"ASHWAKE_PHASE3_PERFORMANCE_PROXY", text)),
        "reliquaries": len(re.findall(r"ASHWAKE_RELIQUARY_PLACED", text)),
        "lights": len(re.findall(r"ASHWAKE_LIGHT", text)),
        "material_studies": len(re.findall(r"Material study", text)),
        "state_studies": len(re.findall(r"State lab", text)),
        "audio_playing": len(re.findall(r"AUDIO_PLAYING", text)),
        "vfx_state": len(re.findall(r"VFX_STATE", text)),
    }
    screenshot_ok = len(screenshots) >= shots and all(s.get("format") == "png" and s.get("width") == 1280 and s.get("height") == 720 for s in screenshots[:shots])
    status = "PASS" if result.get("execution_state") == "SUCCESS" and all(markers.values()) and screenshot_ok and counts["reliquaries"] >= 3 and counts["material_studies"] >= 5 and counts["state_studies"] >= 5 else "FAIL"
    result.update({
        "alias": alias,
        "direction_private": direction,
        "state": state,
        "no_hud": no_hud,
        "performance_proxy": performance_proxy,
        "run_dir": str(run_dir),
        "screenshots": screenshots,
        "markers": markers,
        "counts": counts,
        "screenshot_ok": screenshot_ok,
        "status": status,
        "text_tail": text[-8000:],
    })
    return result


def make_video_from_images(images: list[Path], out_path: Path) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not images:
        return {"status": "SKIPPED", "reason": "no_images", "path": str(out_path)}
    list_path = out_path.with_suffix(".txt")
    lines = []
    for image in images:
        lines.append(f"file '{image.as_posix()}'")
        lines.append("duration 0.65")
    lines.append(f"file '{images[-1].as_posix()}'")
    list_path.write_text("\n".join(lines), encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_path), "-vf", "format=yuv420p", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)]
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return {"status": "PASS" if done.returncode == 0 and out_path.exists() else "FAIL", "command": cmd, "returncode": done.returncode, "stdout_tail": (done.stdout or "")[-2000:], "stderr_tail": (done.stderr or "")[-4000:], "path": str(out_path), "exists": out_path.exists(), "bytes": out_path.stat().st_size if out_path.exists() else 0}
    except Exception as exc:
        return {"status": "FAIL", "command": cmd, "error": f"{type(exc).__name__}: {exc}", "path": str(out_path)}


def write_player_path_diagram(path: Path, alias: str, thesis: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"""# {alias} Player Path Diagram\n\nConcept sentence: {thesis}\n\n```text\nSPAWN\n  -> FIRST LANDMARK\n  -> APPROACH\n  -> READING / first reliquary\n  -> SAFE WINDOW or HOSTILE state read\n  -> ACCEPTED / REJECTED interaction\n  -> ONE COAL RESTORED transformation\n  -> second / third objective continuation\n  -> FINAL / CLIMAX DIRECTION\n  -> ENVIRONMENT OVERVIEW\n```\n\nNo original concept identity revealed before Founder review.\n""", encoding="utf-8")


def founder_sentence(direction: str) -> str:
    # Private mapping used to choose sentence; sentence itself avoids concept name.
    if direction == "CINDERWORKS_ABBEY":
        return "A sacred heat-infrastructure space where ancient coals must be restored by reading physical timing cues in the world."
    if direction == "EMBER_HOSPICE":
        return "A sacred care-space where failing coals are supported by ritual life-support systems and restored through readable pulse windows."
    return "A dead fire-landscape where coals behave like buried sun-seeds and restoration briefly changes the world around them."


def public_run(run: dict[str, Any]) -> dict[str, Any]:
    return {
        "alias": run.get("alias"),
        "state": run.get("state"),
        "no_hud": run.get("no_hud"),
        "status": run.get("status"),
        "run_dir": run.get("run_dir"),
        "screenshots": run.get("screenshots", []),
        "screenshot_ok": run.get("screenshot_ok"),
        "counts": {k: run.get("counts", {}).get(k) for k in ["screenshots_requested", "reliquaries", "lights", "material_studies", "state_studies"]},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--alias-map", type=Path, default=DEFAULT_ALIAS_MAP)
    parser.add_argument("--capture-root", type=Path, default=DEFAULT_CAPTURE_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--public-out", type=Path, default=DEFAULT_PUBLIC_OUT)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--states", nargs="*", default=REVIEW_STATES)
    parser.add_argument("--skip-runtime", action="store_true")
    args = parser.parse_args()

    alias_data = json.loads(args.alias_map.read_text(encoding="utf-8"))
    aliases: dict[str, str] = alias_data["aliases"]
    capture_root = args.capture_root.resolve()
    private_root = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/private"
    founder_root = ROOT / "docs/evidence/ashwake/environment-apprenticeship-phase-3/founder-package"
    capture_root.mkdir(parents=True, exist_ok=True)
    private_root.mkdir(parents=True, exist_ok=True)
    founder_root.mkdir(parents=True, exist_ok=True)

    started = time.time()
    runs: list[dict[str, Any]] = []
    image_analyses: list[dict[str, Any]] = []
    videos: list[dict[str, Any]] = []
    path_diagrams: list[str] = []
    no_hud_protocol = {
        "status": "READY_FOR_HUMAN",
        "rule": "Do not redesign after first blind human run until observations are recorded.",
        "metrics_to_record": ["time_to_first_landmark", "time_to_first_relic", "time_to_first_attempted_interaction", "correct_vs_incorrect_assumptions", "hesitation", "navigation_failures", "state_misunderstandings"],
    }

    if not args.executable.exists() and not args.skip_runtime:
        report = {"schema_version": 1, "kind": "ashwake-phase3-evidence", "status": "UNAVAILABLE", "error": "executable_missing", "executable": str(args.executable)}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1

    for alias, direction in aliases.items():
        alias_dir = capture_root / alias.lower()
        founder_alias_dir = founder_root / alias
        founder_alias_dir.mkdir(parents=True, exist_ok=True)
        sentence = founder_sentence(direction)
        write_player_path_diagram(founder_alias_dir / "player-path-diagram.md", alias, sentence)
        path_diagrams.append(str(founder_alias_dir / "player-path-diagram.md"))
        state_images: list[Path] = []

        if not args.skip_runtime:
            for state in args.states:
                no_hud = True
                performance_proxy = state == "ENVIRONMENT_OVERVIEW"
                run_dir = alias_dir / state.lower()
                run = run_runtime(args.executable.resolve(), run_dir, direction, alias, state, args.timeout, no_hud=no_hud, performance_proxy=performance_proxy, shots=1)
                runs.append(run)
                for shot in sorted((run_dir / "screenshots").glob("*.png")):
                    state_images.append(shot)
                    grayscale_out = founder_alias_dir / "grayscale" / f"{state.lower()}-{shot.name}"
                    metrics = image_metrics(shot, grayscale_out if state in GRAYSCALE_STATES else None)
                    metrics.update({"alias": alias, "state": state, "grayscale_output": str(grayscale_out) if state in GRAYSCALE_STATES else None})
                    image_analyses.append(metrics)
        video = make_video_from_images(state_images, founder_alias_dir / "walkthrough-silent-sample.mp4")
        video.update({"alias": alias})
        videos.append(video)

        (founder_alias_dir / "concept-sentence.md").write_text(f"# {alias}\n\n{sentence}\n", encoding="utf-8")
        (founder_alias_dir / "state-identification-form.md").write_text("# Blind State Identification\n\n" + "\n".join(f"- {q}" for q in STATE_QUESTIONS) + "\n", encoding="utf-8")

    public_index = {
        "schema_version": 1,
        "kind": "ashwake-phase3-founder-blind-package-index",
        "date": "2026-08-21",
        "status": "READY_FOR_FOUNDER_REVIEW" if runs and all(r.get("status") == "PASS" for r in runs) else "EVIDENCE_INCOMPLETE",
        "selection_status": "NO_FINAL_PRODUCTION_DIRECTION_SELECTED",
        "identity_rule": "OPTION identities hidden until Founder blind review completes.",
        "aliases": list(aliases.keys()),
        "package_root": str(founder_root),
        "questions": FOUNDER_QUESTIONS,
        "no_hud_protocol": no_hud_protocol,
        "public_runs": [public_run(r) for r in runs],
        "videos": videos,
        "path_diagrams": path_diagrams,
        "claim_limits": [
            "Evidence package is for Founder blind review; it does not select production direction.",
            "No-HUD captures are prepared for human comprehension testing; human behavior must be recorded during review.",
            "Material/light/performance proxies expose risk only; final art remains unproven.",
        ],
    }
    report = {
        "schema_version": 1,
        "kind": "ashwake-phase3-private-evidence",
        "date": "2026-08-21",
        "status": public_index["status"],
        "duration_seconds": round(time.time() - started, 3),
        "executable": str(args.executable),
        "alias_map_private": str(args.alias_map),
        "capture_root": str(capture_root),
        "runs": runs,
        "image_value_analyses": image_analyses,
        "videos": videos,
        "no_hud_protocol": no_hud_protocol,
        "public_package_index": str(args.public_out),
        "selection_status": "NO_FINAL_PRODUCTION_DIRECTION_SELECTED",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.public_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    args.public_out.write_text(json.dumps(public_index, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        print(json.dumps({"status": report["status"], "private_out": str(args.out), "public_out": str(args.public_out), "aliases": list(aliases.keys())}, indent=2))
    except UnicodeEncodeError:
        sys.stdout.buffer.write(json.dumps({"status": report["status"], "private_out": str(args.out), "public_out": str(args.public_out), "aliases": list(aliases.keys())}, indent=2).encode("utf-8", errors="replace"))
    return 0 if report["status"] == "READY_FOR_FOUNDER_REVIEW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
