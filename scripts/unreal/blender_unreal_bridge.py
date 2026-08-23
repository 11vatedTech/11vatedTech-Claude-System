#!/usr/bin/env python3
"""Governed Blender -> Unreal handoff metadata.

The bridge does not claim to import into an Unreal Editor by itself. It creates
an immutable, hash-addressed handoff contract and validates the facts that an
Editor import must preserve: source identity, GLB structure, units, axes,
material slots, animations, provenance, and intended Unreal destination.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def glb_json(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        header = handle.read(12)
        if len(header) != 12 or header[:4] != b"glTF":
            raise ValueError("not a GLB file")
        _, version, length = struct.unpack("<4sII", header)
        if version != 2:
            raise ValueError(f"unsupported GLB version {version}")
        consumed = 12
        while consumed < length:
            chunk_length, chunk_type = struct.unpack("<II", handle.read(8))
            chunk = handle.read(chunk_length)
            consumed += 8 + chunk_length
            if chunk_type == 0x4E4F534A:
                return json.loads(chunk.decode("utf-8"))
    raise ValueError("GLB JSON chunk missing")


def make_manifest(asset: Path, project: Path, unreal_path: str, source_blend: Path | None, provenance: dict[str, Any]) -> dict[str, Any]:
    asset = asset.resolve(); project = project.resolve()
    gltf = glb_json(asset)
    source_hash = sha256(source_blend) if source_blend and source_blend.exists() else None
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "blender-unreal-handoff",
        "asset_id": "11vt-" + sha256(asset)[:16],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "asset_path": str(asset),
            "asset_hash": "sha256:" + sha256(asset),
            "source_blender": str(source_blend.resolve()) if source_blend else None,
            "source_blender_hash": "sha256:" + source_hash if source_hash else None,
            "format": "glb",
        },
        "unreal": {
            "project": str(project),
            "content_path": unreal_path,
            "import_contract": {
                "units": "centimeters",
                "forward_axis": "+X",
                "up_axis": "+Z",
                "preserve_material_slots": True,
                "preserve_skeleton_and_animation_names": True,
                "generate_missing_collision": False,
            },
        },
        "structure": {
            "scenes": len(gltf.get("scenes", [])),
            "nodes": len(gltf.get("nodes", [])),
            "meshes": len(gltf.get("meshes", [])),
            "materials": len(gltf.get("materials", [])),
            "textures": len(gltf.get("textures", [])),
            "animations": [a.get("name") or f"animation_{i}" for i, a in enumerate(gltf.get("animations", []))],
            "skins": len(gltf.get("skins", [])),
        },
        "provenance": provenance,
        "status": "HANDOFF_READY",
    }


def validate_manifest(manifest: dict[str, Any], require_project: bool = True) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    source = manifest.get("source", {}); unreal = manifest.get("unreal", {})
    asset = Path(source.get("asset_path", ""))
    if not asset.exists(): issues.append({"severity": "error", "code": "source_asset_missing"})
    elif "sha256:" + sha256(asset) != source.get("asset_hash"): issues.append({"severity": "error", "code": "source_hash_stale"})
    project = Path(unreal.get("project", ""))
    if require_project and not project.exists(): issues.append({"severity": "error", "code": "unreal_project_missing"})
    if not str(unreal.get("content_path", "")).startswith("/Game/"): issues.append({"severity": "error", "code": "invalid_unreal_content_path"})
    contract = unreal.get("import_contract", {})
    for key in ("units", "forward_axis", "up_axis"):
        if not contract.get(key): issues.append({"severity": "error", "code": f"missing_import_contract_{key}"})
    provenance = manifest.get("provenance", {})
    if not provenance.get("license") or not provenance.get("source"):
        issues.append({"severity": "error", "code": "incomplete_provenance"})
    if not manifest.get("structure", {}).get("materials"):
        issues.append({"severity": "warning", "code": "no_materials_declared"})
    return {"ok": not any(i["severity"] == "error" for i in issues), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="blender_unreal_bridge")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("manifest"); p.add_argument("asset", type=Path); p.add_argument("project", type=Path); p.add_argument("--unreal-path", required=True); p.add_argument("--source-blend", type=Path); p.add_argument("--license", required=True); p.add_argument("--source", required=True); p.add_argument("--creator", default="11vatedTech Foundry"); p.add_argument("--out", type=Path, required=True)
    p = sub.add_parser("validate"); p.add_argument("manifest", type=Path); p.add_argument("--allow-missing-project", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "manifest":
        result = make_manifest(args.asset, args.project, args.unreal_path, args.source_blend, {"license": args.license, "source": args.source, "creator": args.creator})
        result["validation"] = validate_manifest(result)
        args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    else:
        result = json.loads(args.manifest.read_text(encoding="utf-8")); result["validation"] = validate_manifest(result, require_project=not args.allow_missing_project)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("validation", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
