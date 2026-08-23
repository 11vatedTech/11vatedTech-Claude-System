#!/usr/bin/env python3
"""Compare two GLB variants for accidental production regressions.

This is a structural gate, not an artistic review. It prevents an asset
upgrade from silently trading one subsystem for another (for example, adding
animation while dropping the glass material).
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path


def gltf_json(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError("glb_too_short")
    magic, version, declared = struct.unpack("<III", data[:12])
    if magic != 0x46546C67 or version != 2 or declared != len(data):
        raise ValueError("invalid_glb_container")
    chunk_len, chunk_type = struct.unpack("<II", data[12:20])
    if chunk_type != 0x4E4F534A:
        raise ValueError("first_chunk_not_json")
    return json.loads(data[20:20 + chunk_len].decode("utf-8"))


def names(doc: dict, key: str) -> list[str]:
    return [item.get("name", f"<{key}-{i}>") for i, item in enumerate(doc.get(key, []))]


def compare(baseline: Path, candidate: Path) -> dict:
    base, cur = gltf_json(baseline), gltf_json(candidate)
    keys = ["nodes", "meshes", "materials", "animations", "textures", "images"]
    counts = {key: {"baseline": len(base.get(key, [])), "candidate": len(cur.get(key, []))} for key in keys}
    missing = {key: sorted(set(names(base, key)) - set(names(cur, key))) for key in keys}
    added = {key: sorted(set(names(cur, key)) - set(names(base, key))) for key in keys}
    regressions = []
    for key in keys:
        if counts[key]["candidate"] < counts[key]["baseline"]:
            regressions.append(f"{key}_count_decreased")
        if missing[key]:
            regressions.append(f"{key}_lost:{','.join(missing[key])}")
    # An asset that has any animation in the baseline must not lose all clips;
    # this catches the v1/v2 Emberveil failure directly.
    if counts["animations"]["baseline"] > 0 and counts["animations"]["candidate"] == 0:
        regressions.append("all_animation_clips_lost")
    return {
        "schema_version": 1,
        "baseline": str(baseline),
        "candidate": str(candidate),
        "counts": counts,
        "missing_names": missing,
        "added_names": added,
        "regressions": regressions,
        "ok": not regressions,
        "interpretation": "structural regression result; material and animation presence do not prove perceptual quality",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    try:
        report = compare(args.baseline, args.candidate)
    except Exception as exc:
        report = {"ok": False, "regressions": [f"comparison_error:{type(exc).__name__}:{exc}"]}
    print(json.dumps(report, indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 1 if args.strict and not report.get("ok") else 0


if __name__ == "__main__":
    raise SystemExit(main())
