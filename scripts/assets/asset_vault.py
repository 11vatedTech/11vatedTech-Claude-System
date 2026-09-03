#!/usr/bin/env python3
"""11vatedTech Asset Vault.

Lightweight content-addressed asset index built on a JSON store (prove the
information model before over-engineering storage). Every asset gets an
immutable ID derived from its content hash; master/derived lineage is
recorded explicitly so no random downloaded asset can enter a shipping build
without known rights.

Records support: immutable ID, semantic tags, visual tags, source, creator,
license, acquisition date, hashes, master asset, derived assets, processing
lineage, format, dimensions, texture/geometry/rig/animation info, runtime
variants, preview artifacts, quality state, project relationships.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INDEX = Path.home() / ".claude" / "11vatedtech" / "asset-vault" / "index.json"
DEFAULT_BLOBS = DEFAULT_INDEX.parent / "blobs"

LICENSES_KNOWN = {"cc0", "cc-by", "cc-by-sa", "cc-by-nc", "mit", "apache-2.0",
                  "unlicense", "proprietary", "generated-local", "unknown"}
SOURCES_KNOWN = {"internal", "external-download", "external-purchase", "capture",
                 "procedural", "generated", "contributed", "unknown"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def asset_id(sha: str) -> str:
    return "11vt-" + sha[:16]


def now_stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class Vault:
    def __init__(self, index_path: Path = DEFAULT_INDEX, blobs_dir: Path = DEFAULT_BLOBS):
        self.index_path = Path(index_path)
        self.blobs_dir = Path(blobs_dir)
        self.data: dict[str, Any] = {"schema_version": 1, "assets": {}}
        if self.index_path.exists():
            self.data = json.loads(self.index_path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    # ------------------------------------------------------------ inspection
    def _inspect(self, path: Path) -> dict[str, Any]:
        info: dict[str, Any] = {"bytes": path.stat().st_size, "suffix": path.suffix.lower()}
        sys.path.insert(0, str(ROOT / "scripts" / "media"))
        from vtmedia import image_tools
        if path.suffix.lower() == ".png":
            rec = image_tools.inspect_image(path)
            if rec.get("width"):
                info["width"], info["height"] = rec["width"], rec["height"]
        return info

    # ------------------------------------------------------------------ add
    def add(self, path: Path, *, tags: list[str] | None = None, source: str = "internal",
            creator: str = "unknown", license_: str = "unknown", project: str | None = None,
            master_id: str | None = None, lineage: list[str] | None = None,
            kind: str | None = None, quality: str = "raw") -> dict[str, Any]:
        path = Path(path)
        if not path.exists():
            return {"ok": False, "error": f"file_not_found {path}"}
        if source not in SOURCES_KNOWN:
            return {"ok": False, "error": f"unknown_source {source} (known: {sorted(SOURCES_KNOWN)})"}
        if license_ not in LICENSES_KNOWN:
            return {"ok": False, "error": f"unknown_license {license_} (known: {sorted(LICENSES_KNOWN)})"}

        sha = sha256_file(path)
        aid = asset_id(sha)
        existing = self.data["assets"].get(aid)
        if existing:
            if project and project not in existing.get("projects", []):
                existing["projects"] = sorted(existing.get("projects", []) + [project])
            self.save()
            return {"ok": True, "id": aid, "duplicate": True, "record": existing}

        blob = self.blobs_dir / f"{aid}{path.suffix.lower()}"
        self.blobs_dir.mkdir(parents=True, exist_ok=True)
        if not blob.exists():
            shutil.copy2(path, blob)

        record: dict[str, Any] = {
            "id": aid,
            "sha256": sha,
            "path_original": str(path),
            "blob": str(blob),
            "tags": sorted(set(tags or [])),
            "source": source,
            "creator": creator,
            "license": license_,
            "acquired": now_stamp(),
            "master_id": master_id,
            "derived_from_lineage": lineage or ([master_id] if master_id else []),
            "derived_assets": [],
            "kind": kind or path.suffix.lower().lstrip("."),
            "quality_state": quality,
            "inspection": self._inspect(path),
            "projects": [project] if project else [],
            "previews": [],
        }
        self.data["assets"][aid] = record
        if master_id and master_id in self.data["assets"]:
            self.data["assets"][master_id]["derived_assets"].append(aid)
        self.save()
        return {"ok": True, "id": aid, "duplicate": False, "record": record}

    # ---------------------------------------------------------------- query
    def find(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        q = query.lower()
        hits = []
        for rec in self.data["assets"].values():
            hay = " ".join([
                rec["id"], rec.get("kind", ""), rec.get("source", ""),
                rec.get("creator", ""), rec.get("license", ""),
                " ".join(rec.get("tags", [])), rec.get("path_original", ""),
            ]).lower()
            if q in hay:
                hits.append(self.summary(rec))
        return hits[:limit]

    @staticmethod
    def summary(rec: dict[str, Any]) -> dict[str, Any]:
        return {k: rec.get(k) for k in ("id", "kind", "tags", "source", "creator",
                                        "license", "quality_state", "master_id")}

    def dupes(self) -> list[list[str]]:
        groups: dict[str, list[str]] = {}
        for rec in self.data["assets"].values():
            groups.setdefault(rec["sha256"], []).append(rec["id"])
        return [ids for ids in groups.values() if len(ids) > 1]

    def lineage(self, aid: str) -> dict[str, Any]:
        rec = self.data["assets"].get(aid)
        if not rec:
            return {"ok": False, "error": "asset_not_found"}
        chain = []
        cur = rec
        while cur.get("master_id"):
            master = self.data["assets"].get(cur["master_id"])
            if not master:
                break
            chain.append({"id": master["id"], "license": master["license"],
                          "source": master["source"], "kind": master["kind"]})
            cur = master
        chain.reverse()
        return {"asset": aid, "ancestors": chain,
                "derived": rec.get("derived_assets", []),
                "lineage_depth": len(chain),
                "license_chain": [c["license"] for c in chain] + [rec["license"]]}

    def preview(self, aid: str, out_dir: Path | None = None) -> dict[str, Any]:
        rec = self.data["assets"].get(aid)
        if not rec:
            return {"ok": False, "error": "asset_not_found"}
        blob = Path(rec["blob"])
        if not blob.exists():
            return {"ok": False, "error": "blob_missing"}
        out_dir = Path(out_dir) if out_dir else self.blobs_dir.parent / "previews"
        out_dir.mkdir(parents=True, exist_ok=True)
        if blob.suffix.lower() in (".png", ".jpg", ".jpeg"):
            target = out_dir / f"{aid}-thumb.png"
            sys.path.insert(0, str(ROOT / "scripts" / "media"))
            from vtmedia import image_tools
            exe = None
            from vtmedia.common import resolve_tool
            exe = resolve_tool("magick")
            if exe:
                from vtmedia.common import run
                run([exe, str(blob), "-thumbnail", "320x", str(target)], timeout=60)
            else:
                from vtmedia import ffmpeg_tools
                ffmpeg_tools.resize_image(blob, target, 320)
            if target.exists():
                rec["previews"].append(str(target))
                self.save()
                return {"ok": True, "preview": str(target)}
            return {"ok": False, "error": "preview_generation_failed"}
        return {"ok": True, "preview": str(blob), "note": "no_visual_preview_for_kind"}

    def provenance(self, aid: str) -> dict[str, Any]:
        rec = self.data["assets"].get(aid)
        if not rec:
            return {"ok": False, "error": "asset_not_found"}
        return {"id": rec["id"], "source": rec["source"], "creator": rec["creator"],
                "license": rec["license"], "acquired": rec["acquired"],
                "master_id": rec["master_id"], "lineage": self.lineage(aid),
                "blob": rec["blob"], "sha256": rec["sha256"]}

    def stats(self) -> dict[str, Any]:
        assets = self.data["assets"]
        return {
            "asset_count": len(assets),
            "by_license": {lic: sum(1 for a in assets.values() if a["license"] == lic)
                           for lic in sorted({a["license"] for a in assets.values()})},
            "by_source": {src: sum(1 for a in assets.values() if a["source"] == src)
                          for src in sorted({a["source"] for a in assets.values()})},
            "duplicate_groups": len(self.dupes()),
            "unlicensed": sum(1 for a in assets.values() if a["license"] == "unknown"),
        }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="asset_vault")
    p.add_argument("--index", default=str(DEFAULT_INDEX), help="vault index JSON path")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("path"); a.add_argument("--tags", nargs="*", default=[])
    a.add_argument("--source", default="internal"); a.add_argument("--creator", default="unknown")
    a.add_argument("--license", default="unknown"); a.add_argument("--project", default=None)
    a.add_argument("--master", default=None); a.add_argument("--kind", default=None)
    a.add_argument("--quality", default="raw")
    f = sub.add_parser("find"); f.add_argument("query")
    d = sub.add_parser("dupes")
    l = sub.add_parser("lineage"); l.add_argument("id")
    pr = sub.add_parser("provenance"); pr.add_argument("id")
    pv = sub.add_parser("preview"); pv.add_argument("id"); pv.add_argument("--out", default=None)
    s = sub.add_parser("stats")
    args = p.parse_args(argv)

    vault = Vault(Path(args.index))
    if args.cmd == "add":
        r = vault.add(Path(args.path), tags=args.tags, source=args.source, creator=args.creator,
                      license_=args.license, project=args.project, master_id=args.master,
                      kind=args.kind, quality=args.quality)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    if args.cmd == "find":
        print(json.dumps(vault.find(args.query), indent=2, ensure_ascii=False)); return 0
    if args.cmd == "dupes":
        print(json.dumps(vault.dupes(), indent=2, ensure_ascii=False)); return 0
    if args.cmd == "lineage":
        print(json.dumps(vault.lineage(args.id), indent=2, ensure_ascii=False))
        return 0 if vault.lineage(args.id).get("ok", True) else 1
    if args.cmd == "provenance":
        print(json.dumps(vault.provenance(args.id), indent=2, ensure_ascii=False))
        return 0 if vault.provenance(args.id).get("ok", True) else 1
    if args.cmd == "preview":
        print(json.dumps(vault.preview(args.id, Path(args.out) if args.out else None), indent=2, ensure_ascii=False))
        return 0 if vault.preview(args.id, Path(args.out) if args.out else None).get("ok") else 1
    if args.cmd == "stats":
        print(json.dumps(vault.stats(), indent=2, ensure_ascii=False)); return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
