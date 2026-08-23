"""Host-side structured Blender operations bridge.

High-level operations (scene/mesh/material/rig/animation/camera/render/asset)
with:

- declared input schemas (validation before Blender is ever invoked)
- structured JSON output with explicit health
- host-side post-processing (GLB structural validation, loop pixel diff/PSNR)
- a real end-to-end op suite for regression

This is the structured layer above the raw Blender bridge: operations are
schema-shaped, validated, and testable — not arbitrary Python execution.
"""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path
from typing import Any, Callable

from .common import resolve_tool, run
from .blender_bridge import SCRIPT_DIR, _blender
from . import ffmpeg_tools, image_tools

OP_RUNNER = SCRIPT_DIR / "op_runner.py"

# op -> {param: (type, required)}
SCHEMAS: dict[str, dict[str, tuple[type, bool]]] = {
    "scene.create": {
        "world_color": (list, False), "objects": (list, False),
        "camera": (dict, False), "lights": (list, False),
    },
    "scene.parent": {"root": (str, True), "children": (list, True)},
    "scene.inspect": {"names": (list, False)},
    "lighting.construct": {"lights": (list, False), "world_strength": (float, False), "exposure": (float, False)},
    "pipeline.batch": {"operations": (list, True), "out_dir": (str, False), "save_blend": (str, False)},
    "mesh.analyze": {"names": (list, False)},
    "mesh.optimize": {"name": (str, True), "ratio": (float, False)},
    "mesh.surface_finish": {"name": (str, True), "smooth": (bool, False), "bevel_width": (float, False), "bevel_segments": (int, False)},
    "mesh.lathe": {"name": (str, True), "profile": (list, True), "segments": (int, False),
                    "location": (list, False)},
    "mesh.radial_array": {"name": (str, True), "count": (int, False)},
    "material.construct": {"name": (str, True), "base_color": (list, False),
                           "metallic": (float, False), "roughness": (float, False),
                           "emission": (list, False), "emission_strength": (float, False),
                           "textures": (list, False), "assign_to": (list, False)},
    "material.surface_variation": {"name": (str, True), "scale": (float, False),
                                    "detail": (float, False), "roughness_min": (float, False),
                                    "roughness_max": (float, False), "bump_strength": (float, False),
                                    "dark_color": (list, False), "light_color": (list, False)},
    "material.subsurface": {"name": (str, True), "base_color": (list, False),
                             "roughness": (float, False), "transmission": (float, False),
                             "ior": (float, False), "subsurface": (float, False),
                             "subsurface_color": (list, False), "emission": (list, False),
                             "emission_strength": (float, False), "clearcoat": (float, False),
                             "assign_to": (list, False)},
    "material.inspect": {},
    "material.noise_emission": {"name": (str, True), "scale": (float, False),
                                 "detail": (float, False), "strength_min": (float, False),
                                 "strength_max": (float, False), "assign_to": (list, False)},
    "rig.mechanical": {"name": (str, True), "bones": (list, True)},
    "rig.inspect": {},
    "animation.create_loop": {"name": (str, True), "frame_start": (int, False), "frame_end": (int, False),
                              "turns": (float, False), "axis": (str, False)},
    "animation.create_translation": {"name": (str, True), "frame_start": (int, False), "frame_end": (int, False),
                                     "distance": (float, False), "axis": (str, False)},
    "animation.float": {"name": (str, True), "frame_start": (int, False), "frame_end": (int, False),
                         "amplitude": (float, False), "cycles": (int, False), "sway_degrees": (float, False)},
    "animation.pulse": {"name": (str, True), "frame_start": (int, False), "frame_end": (int, False),
                         "amplitude": (float, False), "cycles": (int, False)},
    "animation.rotate": {"name": (str, True), "frame_start": (int, False), "frame_end": (int, False),
                          "turns": (float, False), "axis": (str, False)},
    "animation.inspect": {},
    "animation.loop_check": {"frame_start": (int, False), "frame_end": (int, False),
                             "resolution": (list, False), "samples": (int, False),
                             "contact_bone": (str, False), "slide_threshold": (float, False)},
    "camera.setup": {"x": (float, False), "y": (float, False), "z": (float, False),
                     "name": (str, False), "lens_mm": (float, False), "look_at": (list, False)},
    "camera.path": {"name": (str, False), "frame_start": (int, False), "frame_end": (int, False),
                     "radius": (float, False), "height": (float, False), "target": (list, False),
                     "sweep_degrees": (float, False), "start_angle": (float, False), "lens_mm": (float, False)},
    "render.preview": {"frame": (int, False), "resolution": (list, False),
                       "engine": (str, False), "samples": (int, False),
                       "denoising": (bool, False)},
    "render.sequence": {"frame_start": (int, False), "frame_end": (int, False),
                         "resolution": (list, False), "engine": (str, False), "samples": (int, False),
                         "denoising": (bool, False)},
    "render.turntable": {"target": (list, False), "radius": (float, False),
                         "height": (float, False), "frames": (int, False),
                         "resolution": (list, False), "samples": (int, False),
                         "camera": (dict, False), "denoising": (bool, False)},
    "asset.export_glb": {"out_path": (str, True), "use_selection": (bool, False)},
    "asset.ingest": {"path": (str, True)},
}

# ops that run in a persistent scene (must be chained in one Blender session)
SCENE_OPS = {
    "scene.create", "scene.parent", "scene.inspect", "mesh.analyze", "mesh.optimize",
    "mesh.lathe", "mesh.radial_array", "mesh.surface_finish", "lighting.construct",
    "material.construct", "material.subsurface", "material.surface_variation", "material.noise_emission", "material.inspect", "rig.mechanical", "rig.inspect",
    "animation.create_loop", "animation.create_translation", "animation.float", "animation.pulse", "animation.rotate",
    "animation.inspect", "animation.loop_check",
    "camera.setup", "camera.path", "render.preview", "render.turntable",
    "render.sequence", "asset.export_glb", "asset.ingest",
}


def validate(op: str, params: dict) -> list[str]:
    errors = []
    if op not in SCHEMAS:
        return [f"unknown_op {op}"]
    for param, (typ, required) in SCHEMAS[op].items():
        if param not in params:
            if required:
                errors.append(f"missing_required_param {param}")
            continue
        value = params[param]
        matches = isinstance(value, typ)
        if typ is float and isinstance(value, (int, float)):
            matches = True  # JSON ints are valid floats
        if not matches:
            errors.append(f"param_type_mismatch {param} expected {typ.__name__}")
    return errors


def glb_validate(path: Path) -> dict[str, Any]:
    """Structural GLB validation per the glTF 2.0 binary container spec:
    12-byte header, JSON chunk, optional BIN chunk, correct lengths."""
    rec: dict[str, Any] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        return rec
    data = path.read_bytes()
    rec["bytes"] = len(data)
    if len(data) < 20:
        rec.update({"valid": False, "error": "too_short_for_glb_header"})
        return rec
    magic, version, length = struct.unpack("<III", data[:12])
    rec["magic"] = hex(magic)
    rec["version"] = version
    rec["declared_length"] = length
    if magic != 0x46546C67:
        rec.update({"valid": False, "error": "bad_magic_not_glTF"})
        return rec
    if version != 2:
        rec.update({"valid": False, "error": f"unsupported_gltf_version {version}"})
        return rec
    if length != len(data):
        rec.update({"valid": False, "error": f"length_mismatch declared={length} actual={len(data)}"})
        return rec
    chunk0_len, chunk0_type = struct.unpack("<II", data[12:20])
    if chunk0_type != 0x4E4F534A:  # JSON
        rec.update({"valid": False, "error": "first_chunk_not_json"})
        return rec
    json_bytes = data[20:20 + chunk0_len]
    try:
        gltf = json.loads(json_bytes.decode("utf-8"))
    except Exception as exc:
        rec.update({"valid": False, "error": f"json_parse_failed {exc}"})
        return rec
    rec["json_chunk_bytes"] = chunk0_len
    rec["asset_version"] = gltf.get("asset", {}).get("version")
    rec["mesh_count"] = len(gltf.get("meshes", []))
    rec["node_count"] = len(gltf.get("nodes", []))
    rec["material_count"] = len(gltf.get("materials", []))
    rec["animation_count"] = len(gltf.get("animations", []))
    rec["has_bin"] = False
    offset = 20 + chunk0_len
    if offset < len(data):
        bin_len, bin_type = struct.unpack("<II", data[offset:offset + 8])
        rec["has_bin"] = bin_type == 0x004E4942
        rec["bin_chunk_bytes"] = bin_len if rec["has_bin"] else None
        if rec["has_bin"] and offset + 8 + bin_len > len(data):
            rec.update({"valid": False, "error": "bin_chunk_overflows_file"})
            return rec
    rec["valid"] = True
    return rec


def run_op(op: str, params: dict, out_dir: Path, timeout: int = 600,
           chain_blend: Path | None = None) -> dict[str, Any]:
    """Validate params, invoke the op in a headless Blender session, and
    post-process host-side metrics. `chain_blend` keeps scene ops chained in
    one persistent .blend across subdirectories."""
    errors = validate(op, params)
    if errors:
        return {"ok": False, "health": "FAILED", "op": op, "validation_errors": errors,
                "error": "validation_failed"}
    blender = _blender()
    if not blender:
        return {"ok": False, "health": "MISSING", "op": op, "error": "blender_not_found"}

    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    spec = {"op": op, "params": dict(params)}
    session_blend = (chain_blend or out_dir / "session.blend").resolve()
    if op in SCENE_OPS:
        spec["params"].setdefault("out_dir", str(out_dir))
        if session_blend.exists():
            spec["params"]["load_blend"] = str(session_blend)
        if op not in ("asset.ingest",):
            spec["params"]["save_blend"] = str(session_blend)
    spec_path = out_dir / f"{op.replace('.', '-')}-spec.json"
    result_path = out_dir / f"{op.replace('.', '-')}-result.json"
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    r = run([blender, "--background", "--factory-startup", "--python", str(OP_RUNNER), "--",
             str(spec_path), str(result_path)], timeout=timeout)
    if not result_path.exists():
        return {"ok": False, "health": "FAILED", "op": op,
                "error": f"blender_failed rc={r.get('returncode')}",
                "stderr_tail": (r.get("stderr") or "")[-500:]}
    result = json.loads(result_path.read_text(encoding="utf-8"))

    # host-side post-processing
    if op == "animation.loop_check" and result.get("ok"):
        first = Path(result.get("first_frame_png") or "")
        last = Path(result.get("last_frame_png") or "")
        if first.exists() and last.exists():
            cmp = image_tools.compare_images(first, last)
            result["loop_continuity"] = {
                "mode": cmp.get("mode"),
                "absolute_error": cmp.get("absolute_error"),
                "psnr_db": cmp.get("psnr_db"),
                "pixels_differ": (cmp.get("absolute_error") or 0) > 0,
                "seamless": (cmp.get("mode") == "imagemagick_absolute_error" and cmp.get("absolute_error") == 0)
                            or (cmp.get("mode") == "ffmpeg_psnr" and cmp.get("psnr_db") is None),
            }
    if op == "asset.export_glb" and result.get("ok"):
        result["glb_validation"] = glb_validate(Path(params["out_path"]))
        if not result["glb_validation"].get("valid"):
            result["ok"] = False
            result["health"] = "FAILED"
    return result


def run_batch(operations: list[dict[str, Any]], out_dir: Path, timeout: int = 900,
              save_blend: Path | None = None) -> dict[str, Any]:
    """Execute a validated sequence in one Blender process.

    This is the production-safe boundary for multi-op authoring: the caller
    can only name registered structured operations, while a single process
    preserves Blender state and prevents open_mainfile scene loss.
    """
    errors = []
    for index, item in enumerate(operations):
        op = item.get("op") if isinstance(item, dict) else None
        params = item.get("params", {}) if isinstance(item, dict) else {}
        errors.extend(f"batch[{index}] {e}" for e in validate(op, params))
    if errors:
        return {"ok": False, "health": "FAILED", "error": "batch_validation_failed", "validation_errors": errors}
    blender = _blender()
    if not blender:
        return {"ok": False, "health": "MISSING", "error": "blender_not_found"}
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    spec_path = out_dir / "pipeline-batch-spec.json"
    result_path = out_dir / "pipeline-batch-result.json"
    spec = {"op": "pipeline.batch", "params": {"operations": operations,
            "out_dir": str(out_dir), "save_blend": str(save_blend.resolve()) if save_blend else None}}
    spec_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
    r = run([blender, "--background", "--factory-startup", "--python", str(OP_RUNNER), "--",
             str(spec_path), str(result_path)], timeout=timeout)
    if not result_path.exists():
        return {"ok": False, "health": "FAILED", "error": f"blender_failed rc={r.get('returncode')}",
                "stderr_tail": (r.get("stderr") or "")[-1000:]}
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["process"] = {"returncode": r.get("returncode"), "elapsed_seconds": r.get("elapsed_seconds")}
    for item in result.get("results", {}).values():
        if item.get("op") == "asset.export_glb" and item.get("out_path"):
            item["glb_validation"] = glb_validate(Path(item["out_path"]))
            if not item["glb_validation"].get("valid"):
                item["ok"] = False
                item["health"] = "FAILED"
    result["failed"] = [name for name, item in result.get("results", {}).items() if not item.get("ok")]
    result["ok"] = not result["failed"]
    result["health"] = "PASS" if result["ok"] else "FAILED"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def _broken_loop_probe(out_dir: Path, chain_blend: Path) -> dict[str, Any]:
    """Failure-path probe: a half-rotation loop is NOT seamless; the QA must
    flag it. Returns ok=True only when the QA correctly detects the break."""
    create = run_op("animation.create_loop", {
        "name": "hero_block", "frame_start": 1, "frame_end": 48, "turns": 0.5, "axis": "Z",
    }, out_dir, chain_blend=chain_blend)
    if not create.get("ok"):
        return {**create, "note": "broken-loop probe setup failed"}
    check = run_op("animation.loop_check", {
        "frame_start": 1, "frame_end": 48, "resolution": [320, 180], "samples": 16,
    }, out_dir / "broken-loop", chain_blend=chain_blend)
    cont = check.get("loop_continuity", {})
    detected = cont.get("seamless") is False and (cont.get("absolute_error") or 0) > 0
    check["broken_loop_detected"] = detected
    check["ok"] = bool(detected)
    check["health"] = "PASS" if detected else "FAILED"
    return check


def op_suite(out_dir: Path, skip_render: bool = False) -> dict[str, Any]:
    """Real end-to-end production exercise: scene -> mesh -> material ->
    render -> turntable -> loop QA -> GLB export -> GLB validate -> ingest.
    Every op result is recorded; the suite fails if any op fails."""
    out_dir = Path(out_dir).resolve()
    chain_blend = out_dir / "session.blend"
    results: dict[str, Any] = {}
    def rec(name: str, fn: Callable[[], dict]) -> None:
        try:
            r = fn()
            if "ok" not in r:  # raw tool results (e.g. ffmpeg) carry returncode
                r["ok"] = r.get("returncode") == 0
                r["health"] = "PASS" if r["ok"] else "FAILED"
            results[name] = r
        except Exception as exc:
            results[name] = {"ok": False, "health": "FAILED", "error": f"{type(exc).__name__}: {exc}"}

    rec("scene.create", lambda: run_op("scene.create", {
        "world_color": [0.02, 0.02, 0.06],
        "objects": [
            {"type": "cube", "name": "hero_block", "size": 1.6, "location": [0, 0, 0.8]},
            {"type": "sphere", "name": "orb", "size": 0.6, "location": [1.8, 0.4, 0.6]},
            {"type": "plane", "name": "ground", "size": 12, "location": [0, 0, 0]},
        ],
        "camera": {"name": "Cam", "lens_mm": 50, "x": 5.5, "y": -6.5, "z": 3.2, "look_at": [0, 0, 0.8]},
        "lights": [{"type": "sun", "name": "Key", "x": 4, "y": -6, "z": 9, "energy": 3.0}],
    }, out_dir, chain_blend=chain_blend))
    rec("mesh.analyze", lambda: run_op("mesh.analyze", {}, out_dir, chain_blend=chain_blend))
    rec("material.construct", lambda: run_op("material.construct", {
        "name": "11vt_sigil_brass", "base_color": [0.85, 0.55, 0.1], "metallic": 0.9,
        "roughness": 0.35, "emission": [0.9, 0.4, 0.05], "emission_strength": 0.15,
        "assign_to": ["hero_block"],
    }, out_dir, chain_blend=chain_blend))
    rec("material.inspect", lambda: run_op("material.inspect", {}, out_dir, chain_blend=chain_blend))
    # animation observability: looping action + loop-continuity QA + foot-slide probes
    rec("animation.create_loop", lambda: run_op("animation.create_loop", {
        "name": "hero_block", "frame_start": 1, "frame_end": 48, "turns": 1.0, "axis": "Z",
    }, out_dir, chain_blend=chain_blend))
    rec("animation.loop_check", lambda: run_op("animation.loop_check", {
        "frame_start": 1, "frame_end": 48, "resolution": [320, 180], "samples": 16,
        "contact_bone": "orb",  # static object: expect NO foot-slide flag
    }, out_dir / "loop-qa", chain_blend=chain_blend))
    rec("animation.create_translation", lambda: run_op("animation.create_translation", {
        "name": "orb", "frame_start": 1, "frame_end": 24, "distance": 2.0, "axis": "X",
    }, out_dir, chain_blend=chain_blend))
    rec("animation.slide_probe", lambda: run_op("animation.loop_check", {
        "frame_start": 1, "frame_end": 24, "resolution": [160, 90], "samples": 8,
        "contact_bone": "orb",  # now drifting: expect foot-slide flag True
    }, out_dir / "slide-probe", chain_blend=chain_blend))
    rec("animation.broken_loop", lambda: _broken_loop_probe(out_dir, chain_blend))
    rec("animation.inspect", lambda: run_op("animation.inspect", {}, out_dir, chain_blend=chain_blend))
    if not skip_render:
        rec("render.preview", lambda: run_op("render.preview", {
            "resolution": [480, 270], "engine": "CYCLES", "samples": 24,
        }, out_dir / "preview", chain_blend=chain_blend))
        rec("render.turntable", lambda: run_op("render.turntable", {
            "target": [0, 0, 0.8], "radius": 5.5, "height": 1.6, "frames": 8,
            "resolution": [320, 180], "engine": "CYCLES", "samples": 16,
        }, out_dir / "turntable", chain_blend=chain_blend))
    rec("asset.export_glb", lambda: run_op("asset.export_glb", {
        "out_path": str(out_dir / "hero-scene.glb"),
    }, out_dir, chain_blend=chain_blend))
    rec("asset.ingest", lambda: run_op("asset.ingest", {
        "path": str(out_dir / "hero-scene.glb"),
    }, out_dir))
    # motion observability: assemble the turntable image sequence into a video
    turntable_dir = out_dir / "turntable"
    if (turntable_dir / "turntable-000.png").exists():
        rec("motion.preview_video", lambda: ffmpeg_tools.image_sequence_to_video(
            str(turntable_dir / "turntable-%03d.png"), out_dir / "turntable.mp4", fps=8))

    failed = [name for name, r in results.items() if not r.get("ok")]
    suite = {"op_count": len(results), "failed": failed, "passed": not failed,
             "results": results}
    (out_dir / "blender-op-suite.json").write_text(
        json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    return suite


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(prog="blender_ops")
    p.add_argument("--suite", action="store_true")
    p.add_argument("--out", default="artifacts/creative-stack-validation/blender-ops")
    p.add_argument("--skip-render", action="store_true")
    p.add_argument("op", nargs="?", default=None)
    p.add_argument("params", nargs="*", default=[])
    args = p.parse_args()
    out = Path(args.out)
    if args.suite:
        s = op_suite(out, skip_render=args.skip_render)
        print(json.dumps({k: v for k, v in s.items() if k != "results"}, indent=2, ensure_ascii=False))
        for name, r in s["results"].items():
            print(f"{name:22} {r.get('health')} {r.get('error', '')}")
        raise SystemExit(0 if s["passed"] else 1)
    if args.op:
        params = json.loads(" ".join(args.params)) if args.params else {}
        print(json.dumps(run_op(args.op, params, out), indent=2, ensure_ascii=False))
        raise SystemExit(0 if (run_op(args.op, params, out)).get("ok") else 1)
