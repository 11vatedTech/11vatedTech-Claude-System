#!/usr/bin/env python3
"""11VT Resource Intelligence + Asset Synthesis Layer.

Provider-agnostic resource modeling, license fail-closed classification,
resource genome records, source/adapt/create decisions, security classification,
prototype-vs-shipping gate, and bounded itch.io discovery reasoning.

This module does not download marketplace resources or spend money. It treats
provider metadata as evidence, not permission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_VAULT = Path.home() / ".claude" / "11vatedtech" / "asset-vault" / "index.json"

UNKNOWN = "UNKNOWN"
UNVERIFIED = "UNVERIFIED"
NOT_APPLICABLE = "NOT_APPLICABLE"

PROVIDERS = {
    "ITCH_IO": {
        "trust_level": "METADATA_UNVERIFIED_UNTIL_SOURCE_CAPTURED",
        "acquisition_modes": ["REFERENCE_ONLY", "MANUAL_DOWNLOAD", "AUTHENTICATED", "PURCHASE_APPROVAL"],
        "release_capable": True,
        "security_profile": "EXTERNAL_UNTRUSTED",
    },
    "INTERNAL_ASSET_VAULT": {"trust_level": "INTERNAL_RECORDS_REQUIRED", "acquisition_modes": ["REUSE"], "release_capable": False},
    "CURRENT_PROJECT_ASSETS": {"trust_level": "PROJECT_LOCAL_VERIFY_LICENSE", "acquisition_modes": ["REUSE", "ADAPT"], "release_capable": False},
    "PREVIOUS_AUTHORIZED_11VATEDTECH_ASSETS": {"trust_level": "AUTHORIZED_LINEAGE_REQUIRED", "acquisition_modes": ["REUSE", "ADAPT"], "release_capable": False},
    "AUTHORIZED_OPEN_RESOURCE_LIBRARIES": {"trust_level": "PER_RESOURCE_LICENSE_REQUIRED", "acquisition_modes": ["REFERENCE_ONLY", "DOWNLOAD"], "release_capable": False},
}

LICENSE_CLASSES = [
    "REFERENCE_ONLY",
    "USE_AS_IS_ALLOWED",
    "MODIFICATION_ALLOWED",
    "COMMERCIAL_ALLOWED",
    "ATTRIBUTION_REQUIRED",
    "REDISTRIBUTION_RESTRICTED",
    "LICENSE_UNCLEAR",
    "DO_NOT_USE",
]

ASSET_STATES = [
    "REFERENCE_ONLY",
    "BLOCKOUT_PROXY",
    "PROTOTYPE_ASSET",
    "LICENSED_SHIPPING_ASSET",
    "ADAPTED_SHIPPING_ASSET",
    "ORIGINAL_11VT_ASSET",
    "REJECTED",
    "DO_NOT_USE",
]

IMPORTANCE_TIERS = ["BLOCKOUT", "BACKGROUND", "SUPPORTING", "PRIMARY", "HERO", "IDENTITY_CRITICAL"]

SOURCE_DECISIONS = ["USE_EXISTING", "ADAPT_EXISTING", "HYBRIDIZE", "CREATE_ORIGINAL"]

STATIC_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".wav", ".ogg", ".mp3", ".txt", ".md"}
COMPLEX_EXT = {".fbx", ".blend", ".glb", ".gltf", ".obj", ".dae", ".psd", ".aseprite", ".uasset", ".uproject", ".unitypackage", ".godot"}
EXEC_EXT = {".exe", ".bat", ".cmd", ".ps1", ".sh", ".py", ".js", ".mjs", ".ts", ".uplugin", ".dll"}

ITCH_DIMENSIONS = {
    "asset_types": ["sprites", "characters", "animations", "textures", "user-interface", "icons", "fonts", "sound-effects", "music", "tileset", "backgrounds"],
    "styles": ["2d", "3d", "pixel-art", "8-bit", "16-bit", "1-bit", "low-poly", "voxel"],
    "engines": ["unreal-engine", "unity", "godot", "blender", "ue5"],
    "formats": ["png", "fbx", "midi", "wav", "aseprite", "blend", "glb", "obj"],
    "ai": ["no-ai", "ai-generated", "ai-generated-graphics", "ai-generated-sound", "ai-generated-text", "ai-generated-code"],
    "price": ["free", "store", "on-sale", "5-dollars-or-less", "15-dollars-or-less"],
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", text.lower()).strip("-") or "resource"


def evidence_route(claim: str, routes: list[str]) -> dict[str, Any]:
    allowed = {"LIVE_WEB", "OFFICIAL_DOCS", "REPOSITORY", "KAPIF_CANON", "LOCAL_EVIDENCE", "DOMAIN_KNOWLEDGE_ONLY", "UNAVAILABLE"}
    cleaned = [r for r in routes if r in allowed]
    status = "VERIFIED" if any(r in cleaned for r in ("LIVE_WEB", "OFFICIAL_DOCS", "REPOSITORY", "LOCAL_EVIDENCE")) else "UNVERIFIED_DOMAIN_KNOWLEDGE"
    if not cleaned or "UNAVAILABLE" in cleaned:
        status = "LIVE_RESEARCH_UNAVAILABLE" if "current" in claim.lower() or "professional" in claim.lower() else "UNVERIFIED_DOMAIN_KNOWLEDGE"
    return {"claim": claim, "routes": cleaned or ["UNAVAILABLE"], "status": status, "fail_closed": status != "VERIFIED"}


def classify_license(text: str | None, *, commercial_project: bool = True, need_modify: bool = False, need_redistribute_source: bool = False) -> dict[str, Any]:
    raw = (text or "").strip()
    low = raw.lower()
    classes: set[str] = set()
    fields: dict[str, Any] = {
        "commercial_use": UNKNOWN,
        "modification": UNKNOWN,
        "redistribution": UNKNOWN,
        "attribution": UNKNOWN,
        "source_file_exposure": UNKNOWN,
        "ai_terms": UNKNOWN,
        "license_text": raw or UNKNOWN,
    }
    blockers: list[str] = []

    if not raw:
        classes.add("LICENSE_UNCLEAR")
        blockers.append("license_missing")
    elif "cc0" in low or "creative commons zero" in low:
        classes.update(["USE_AS_IS_ALLOWED", "MODIFICATION_ALLOWED", "COMMERCIAL_ALLOWED"])
        fields.update({"commercial_use": True, "modification": True, "redistribution": True, "attribution": False})
    elif "creative commons attribution" in low or "cc by" in low:
        classes.update(["USE_AS_IS_ALLOWED", "MODIFICATION_ALLOWED", "COMMERCIAL_ALLOWED", "ATTRIBUTION_REQUIRED"])
        fields.update({"commercial_use": True, "modification": True, "redistribution": True, "attribution": True})
        if "nc" in low or "noncommercial" in low:
            fields["commercial_use"] = False
            classes.discard("COMMERCIAL_ALLOWED")
            blockers.append("noncommercial_restriction")
    elif "mit license" in low or low == "mit":
        classes.update(["USE_AS_IS_ALLOWED", "MODIFICATION_ALLOWED", "COMMERCIAL_ALLOWED"])
        fields.update({"commercial_use": True, "modification": True, "redistribution": True, "attribution": True})
    elif "personal and commercial" in low or "commercial products" in low:
        classes.update(["USE_AS_IS_ALLOWED", "COMMERCIAL_ALLOWED"])
        fields["commercial_use"] = True
        if any(x in low for x in ("modify", "modified", "recolor", "resize", "combined", "edited")):
            classes.add("MODIFICATION_ALLOWED")
            fields["modification"] = True
        if any(x in low for x in ("may not be resold", "may not be redistributed", "standalone files", "asset pack")):
            classes.add("REDISTRIBUTION_RESTRICTED")
            fields["redistribution"] = False
            fields["source_file_exposure"] = False
        if "attribution is appreciated but not required" in low or "attribution not required" in low:
            fields["attribution"] = False
        elif "attribution" in low:
            classes.add("ATTRIBUTION_REQUIRED")
            fields["attribution"] = True
    else:
        classes.add("LICENSE_UNCLEAR")
        blockers.append("license_terms_not_recognized")

    if any(x in low for x in ("may not be used to train", "not be used to train", "machine learning", "large language models")):
        fields["ai_terms"] = "AI_TRAINING_RESTRICTED"
    elif "ai" in low:
        fields["ai_terms"] = UNVERIFIED

    if commercial_project and fields["commercial_use"] is not True:
        blockers.append("commercial_use_not_verified")
    if need_modify and fields["modification"] is not True:
        blockers.append("modification_not_verified")
    if need_redistribute_source and fields["redistribution"] is not True:
        blockers.append("redistribution_not_verified")
    if blockers and "LICENSE_UNCLEAR" not in classes and fields["commercial_use"] is UNKNOWN:
        classes.add("LICENSE_UNCLEAR")

    if blockers and "DO_NOT_USE" not in classes and any("noncommercial" in b for b in blockers):
        classes.add("DO_NOT_USE")

    return {
        "schema_version": 1,
        "classifications": sorted(classes or {"LICENSE_UNCLEAR"}, key=lambda x: LICENSE_CLASSES.index(x) if x in LICENSE_CLASSES else 99),
        "fields": fields,
        "blockers": blockers,
        "shipping_allowed": not blockers and "COMMERCIAL_ALLOWED" in classes,
        "doctrine": {
            "itch_io_not_universal_license": True,
            "downloaded_not_commercially_usable": True,
            "commercial_not_modification": True,
            "modification_not_redistribution": True,
            "free_not_unrestricted": True,
            "royalty_free_not_unrestricted": True,
            "fail_closed_if_unclear": True,
        },
    }


def classify_security(files: list[str]) -> dict[str, Any]:
    suffixes = {Path(f).suffix.lower() for f in files}
    hits_exec = sorted(suffixes & EXEC_EXT)
    hits_complex = sorted(suffixes & COMPLEX_EXT)
    if hits_exec:
        level = "CRITICAL" if any(x in hits_exec for x in (".exe", ".bat", ".cmd", ".ps1", ".sh", ".dll")) else "HIGH"
    elif hits_complex:
        level = "HIGH" if any(x in hits_complex for x in (".uproject", ".unitypackage", ".uasset")) else "MEDIUM"
    elif suffixes and suffixes.issubset(STATIC_EXT):
        level = "LOW"
    else:
        level = "MEDIUM" if suffixes else "UNKNOWN"
    return {
        "schema_version": 1,
        "risk": level,
        "suffixes": sorted(suffixes),
        "code_or_tool_indicators": hits_exec,
        "complex_project_indicators": hits_complex,
        "requires_manual_review": level in {"HIGH", "CRITICAL"},
        "rules": [
            "External archives and tools are untrusted.",
            "Do not automatically execute code contained in downloaded asset packages.",
            "Separate ART ASSET from CODE / TOOL / PLUGIN.",
        ],
    }


def itch_discover(query: str) -> dict[str, Any]:
    text = query.lower()
    tags: list[str] = []
    for group in ITCH_DIMENSIONS.values():
        for tag in group:
            if tag.replace("-", " ") in text or tag in text:
                tags.append(tag)
    if "ui kit" in text:
        tags.append("user-interface")
    if "unreal" in text:
        tags.append("unreal-engine")
    if "blender" in text:
        tags.append("blender")
    base = "https://itch.io/game-assets"
    url_parts = []
    if "free" in tags:
        url_parts.append("free")
        tags = [t for t in tags if t != "free"]
    for tag in sorted(set(tags)):
        url_parts.append("tag-" + tag)
    discovery_url = base + ("/" + "/".join(url_parts) if url_parts else "")
    return {
        "schema_version": 1,
        "provider": "ITCH_IO",
        "query": query,
        "discovery_url": discovery_url,
        "dimensions_detected": sorted(set(tags)),
        "candidate_metadata_expected": ["creator", "source_page", "asset_type", "price", "engine_metadata", "AI_disclosure_where_visible", "license_state", "quality_notes", "project_fit"],
        "acquisition_policy": "Discovery only. Download/purchase/authentication/manual acquisition requires separate approval and license capture.",
        "license_default": "LICENSE_UNCLEAR until per-asset terms captured.",
    }


def blank_genome(candidate: dict[str, Any]) -> dict[str, Any]:
    provider = candidate.get("provider", "UNKNOWN")
    title = candidate.get("title", "UNKNOWN")
    source = candidate.get("source_page", "UNKNOWN")
    rid_seed = f"{provider}:{source}:{title}"
    rid = "res-" + hashlib.sha256(rid_seed.encode("utf-8")).hexdigest()[:16]
    license_result = classify_license(candidate.get("license_text"), commercial_project=bool(candidate.get("commercial_project", True)), need_modify=bool(candidate.get("need_modify", False)))
    files = candidate.get("files", []) if isinstance(candidate.get("files", []), list) else []
    security = classify_security(files)
    return {
        "schema_version": 1,
        "resource_id": rid,
        "IDENTITY": {"title": title, "creator": candidate.get("creator", UNKNOWN), "provider": provider, "source_url": source, "version": candidate.get("version", UNKNOWN), "acquisition_date": candidate.get("acquisition_date", UNVERIFIED), "hash": candidate.get("hash", UNVERIFIED)},
        "TYPE": {"asset_kind": candidate.get("asset_kind", UNKNOWN), "content_domain": candidate.get("content_domain", UNKNOWN), "art_code_or_mixed": candidate.get("art_code_or_mixed", UNKNOWN), "asset_state": candidate.get("asset_state", "REFERENCE_ONLY")},
        "FORMAT": {"file_types": sorted({Path(f).suffix.lower().lstrip(".") for f in files}) or UNKNOWN, "source_formats": candidate.get("source_formats", UNKNOWN), "delivery_formats": candidate.get("delivery_formats", UNKNOWN), "archive_type": candidate.get("archive_type", UNKNOWN)},
        "ENGINE": {"claimed_engines": candidate.get("claimed_engines", UNKNOWN), "tested_engines": candidate.get("tested_engines", UNVERIFIED), "engine_version": candidate.get("engine_version", UNKNOWN)},
        "STYLE": candidate.get("style", {"genre": UNKNOWN, "rendering_style": UNKNOWN, "tone": UNKNOWN}),
        "VISUAL_DNA": candidate.get("visual_dna", {"palette": UNKNOWN, "silhouette_language": UNKNOWN, "material_language": UNKNOWN, "texture_density": UNKNOWN, "originality_risk": UNVERIFIED}),
        "TECHNICAL_DNA": candidate.get("technical_dna", {"resolution": UNKNOWN, "polygon_count": UNKNOWN, "topology_quality": UNVERIFIED, "UV_state": UNVERIFIED, "material_maps": UNKNOWN, "rig_state": UNKNOWN, "animation_count": UNKNOWN, "audio_sample_rate": UNKNOWN}),
        "QUALITY": candidate.get("quality", {"completeness_score": UNVERIFIED, "craft_score": UNVERIFIED, "documentation_score": UNVERIFIED, "visible_defects": UNKNOWN}),
        "LICENSE": license_result,
        "PROVENANCE": {"page_snapshot_ref": candidate.get("page_snapshot_ref", UNVERIFIED), "receipt_ref": candidate.get("receipt_ref", NOT_APPLICABLE), "file_manifest_ref": candidate.get("file_manifest_ref", UNVERIFIED), "source_chain": [source] if source != UNKNOWN else []},
        "PROJECT_FIT": candidate.get("project_fit", {"target_project": UNKNOWN, "intended_role": UNKNOWN, "asset_importance_tier": candidate.get("importance", UNKNOWN), "style_gap": UNVERIFIED}),
        "ADAPTATION_COST": candidate.get("adaptation_cost", {"legal_cost": UNVERIFIED, "visual_rework_cost": UNVERIFIED, "technical_conversion_cost": UNVERIFIED, "QA_cost": UNVERIFIED, "cheaper_to_create_original": UNVERIFIED}),
        "KNOWN_LIMITATIONS": {"license_blockers": license_result.get("blockers", []), "security": security, "technical_blockers": candidate.get("technical_blockers", []), "aesthetic_blockers": candidate.get("aesthetic_blockers", []), "originality_blockers": candidate.get("originality_blockers", [])},
    }


def decide(requirement: dict[str, Any]) -> dict[str, Any]:
    tier = requirement.get("importance", "SUPPORTING")
    license_state = requirement.get("license_state", "LICENSE_UNCLEAR")
    style_fit = requirement.get("style_fit", "UNKNOWN")
    needs_identity = tier in {"HERO", "IDENTITY_CRITICAL"} or bool(requirement.get("identity_critical"))
    can_modify = bool(requirement.get("modification_allowed"))
    can_use = bool(requirement.get("commercial_allowed")) and license_state != "LICENSE_UNCLEAR"
    quality = requirement.get("quality", "UNKNOWN")
    blockers: list[str] = []
    if license_state == "LICENSE_UNCLEAR":
        blockers.append("license_unclear")
    if needs_identity:
        decision = "CREATE_ORIGINAL"
        rationale = "identity-critical or hero asset should not be defined by sourced generic resource"
    elif can_use and tier in {"BLOCKOUT", "BACKGROUND"} and style_fit in {"GOOD", "STRONG"}:
        decision = "USE_EXISTING"
        rationale = "low-salience asset with verified use rights and fit"
    elif can_use and can_modify and tier in {"SUPPORTING", "PRIMARY"}:
        decision = "ADAPT_EXISTING"
        rationale = "visible asset can use technical base but needs project-specific art direction"
    elif can_use and can_modify and requirement.get("multiple_sources"):
        decision = "HYBRIDIZE"
        rationale = "compatible rights and multiple sources support composed solution"
    else:
        decision = "CREATE_ORIGINAL"
        rationale = "rights, fit, or identity risk block safe sourcing"
    return {
        "schema_version": 1,
        "requirement": requirement.get("name", UNKNOWN),
        "decision": decision,
        "rationale": rationale,
        "license_basis": license_state,
        "quality_basis": quality,
        "originality_risk": "HIGH" if needs_identity else requirement.get("originality_risk", UNVERIFIED),
        "asset_flip_risk": "BLOCKED_BY_CREATE_ORIGINAL" if needs_identity else requirement.get("asset_flip_risk", UNVERIFIED),
        "adaptation_plan": requirement.get("adaptation_plan", NOT_APPLICABLE if decision == "CREATE_ORIGINAL" else UNKNOWN),
        "fallback": "REFERENCE_ONLY_OR_CREATE_ORIGINAL" if blockers else "PROCEED_WITH_RECORDED_EVIDENCE",
        "required_evidence": ["license_record", "provenance", "style_fit", "render_in_context", "originality_review"],
        "blockers": blockers,
    }


def vault_query(index: Path, query: str) -> dict[str, Any]:
    if not index.exists():
        return {"schema_version": 1, "vault": str(index), "query": query, "available": False, "matches": [], "decision": "VAULT_NOT_INITIALIZED"}
    data = json.loads(index.read_text(encoding="utf-8"))
    assets = data.get("assets", {}) if isinstance(data, dict) else {}
    q = query.lower()
    hits = []
    for aid, rec in assets.items():
        hay = json.dumps(rec, ensure_ascii=False).lower()
        if q in hay:
            hits.append({"id": aid, "asset_state": rec.get("asset_state", rec.get("quality_state", UNKNOWN)), "license": rec.get("license", UNKNOWN), "creator": rec.get("creator", UNKNOWN), "source": rec.get("source", UNKNOWN)})
    return {"schema_version": 1, "vault": str(index), "query": query, "available": True, "matches": hits, "decision": "REUSE_CANDIDATES_FOUND" if hits else "NO_SUITABLE_RECORDED_ASSET"}


def release_gate(manifest: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    for idx, asset in enumerate(manifest.get("assets", [])):
        state = asset.get("asset_state", UNKNOWN)
        if asset.get("shipping_scope") is False or state == "REFERENCE_ONLY":
            continue
        lic = asset.get("license_state", UNKNOWN)
        if state == "PROTOTYPE_ASSET":
            blockers.append(f"asset_{idx}_prototype_asset_must_not_ship")
        if lic in {"LICENSE_UNCLEAR", UNKNOWN, UNVERIFIED}:
            blockers.append(f"asset_{idx}_license_unclear")
        if asset.get("attribution_required") and not asset.get("attribution_text"):
            blockers.append(f"asset_{idx}_attribution_missing")
        if asset.get("raw_source_exposed") and asset.get("redistribution") == "REDISTRIBUTION_RESTRICTED":
            blockers.append(f"asset_{idx}_forbidden_source_exposure")
    return {"schema_version": 1, "decision": "PASS" if not blockers else "FAIL_CLOSED", "blockers": blockers, "rule": "PROTOTYPE_ASSET must never silently ship."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resource_intelligence")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("providers")
    d = sub.add_parser("itch-discover"); d.add_argument("query"); d.add_argument("--out", type=Path)
    lic = sub.add_parser("license"); lic.add_argument("text", nargs="?", default=""); lic.add_argument("--need-modify", action="store_true"); lic.add_argument("--need-redistribute-source", action="store_true"); lic.add_argument("--out", type=Path)
    sec = sub.add_parser("security"); sec.add_argument("files", nargs="+"); sec.add_argument("--out", type=Path)
    gen = sub.add_parser("genome"); gen.add_argument("candidate", type=Path); gen.add_argument("--out", type=Path)
    dec = sub.add_parser("decide"); dec.add_argument("requirement", type=Path); dec.add_argument("--out", type=Path)
    vq = sub.add_parser("vault-query"); vq.add_argument("query"); vq.add_argument("--index", type=Path, default=DEFAULT_VAULT); vq.add_argument("--out", type=Path)
    rg = sub.add_parser("release-gate"); rg.add_argument("manifest", type=Path); rg.add_argument("--out", type=Path)
    er = sub.add_parser("evidence-route"); er.add_argument("claim"); er.add_argument("routes", nargs="+"); er.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    if args.cmd == "providers":
        result = {"schema_version": 1, "providers": PROVIDERS, "future_provider_ready": True}; code = 0
    elif args.cmd == "itch-discover":
        result = itch_discover(args.query); code = 0
    elif args.cmd == "license":
        result = classify_license(args.text, need_modify=args.need_modify, need_redistribute_source=args.need_redistribute_source); code = 0 if result["shipping_allowed"] or "LICENSE_UNCLEAR" in result["classifications"] else 2
    elif args.cmd == "security":
        result = classify_security(args.files); code = 0
    elif args.cmd == "genome":
        result = blank_genome(json.loads(args.candidate.read_text(encoding="utf-8"))); code = 0
    elif args.cmd == "decide":
        result = decide(json.loads(args.requirement.read_text(encoding="utf-8"))); code = 0
    elif args.cmd == "vault-query":
        result = vault_query(args.index, args.query); code = 0
    elif args.cmd == "release-gate":
        result = release_gate(json.loads(args.manifest.read_text(encoding="utf-8"))); code = 0 if result["decision"] == "PASS" else 2
    elif args.cmd == "evidence-route":
        result = evidence_route(args.claim, args.routes); code = 0 if not result["fail_closed"] else 2
    else:
        raise AssertionError(args.cmd)
    if getattr(args, "out", None):
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
