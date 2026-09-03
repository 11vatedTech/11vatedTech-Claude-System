#!/usr/bin/env python3
"""11vatedTech Creative Studio Gates.

Operational validators for the four-layer Foundry studio path. These gates are
not taste simulators. They fail closed when required routing, concept,
reference, craft, resource, first-pixel, QA, review, finish, release, or memory
evidence is missing, generic, or unsupported.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

CREATIVE_CLASSES = {
    "CREATIVE_PRODUCT",
    "CREATIVE_ASSET",
    "GAME_CREATIVE",
    "VISUAL_SYSTEM",
    "CHARACTER",
    "CREATURE",
    "ENVIRONMENT",
    "INTERACTIVE_EXPERIENCE",
    "HYBRID_PRODUCTION",
}

GENERIC_TERMS = {
    "premium",
    "cinematic",
    "futuristic",
    "neon",
    "minimal",
    "luxury",
    "ai",
}

CONCEPT_REQUIRED = (
    "product_intent",
    "audience",
    "emotional_objective",
    "creative_thesis",
    "anti_generic_risk",
    "style_world_dna",
    "reference_principles",
    "signature_moments",
    "medium_candidates",
    "resource_strategy",
    "evidence_plan",
)

REFERENCE_REQUIRED = (
    "source",
    "purpose",
    "why_good",
    "transferable_principle",
    "must_not_copy",
    "own_thing_plan",
)

QUALITY_REQUIRED = (
    "first_pixel_review",
    "perceptual_qa",
    "independent_review",
    "professional_finish",
)

RELEASE_BLOCKERS = (
    "LICENSE_UNCLEAR",
    "PROTOTYPE_ASSET",
)


def load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_load_error": f"{type(exc).__name__}: {exc}"}
    return data if isinstance(data, dict) else {"_load_error": "root_not_object"}


def _missing(doc: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if field not in doc or doc.get(field) in (None, "", [], {})]


def classify_intent(intent: str) -> dict[str, Any]:
    text = intent.lower()
    classes: list[str] = []
    skills: list[str] = []
    agents: list[str] = []
    evidence: list[str] = []

    creative_hits = {
        "high-fidelity", "cinematic", "visual", "art direction", "brand", "identity",
        "motion", "typography", "asset", "shader", "webgl", "webgpu", "canvas", "3d",
        "character", "creature", "environment", "game feel", "vfx", "audio-reactive",
    }
    if any(hit in text for hit in creative_hits):
        classes.append("CREATIVE_PRODUCT")
        skills.extend(["11vt-creative-production", "11vt-design-director", "11vt-testing-verification"])
        agents.extend(["11vt-creative-director", "11vt-art-director", "11vt-visual-qa-director"])
        evidence.extend(["routing_stamp", "concept_gate", "first_visible_artifact", "rendered_evidence", "independent_review"])
    if any(hit in text for hit in ("asset", "resources", "itch.io", "license", "vault", "sourced")):
        classes.append("CREATIVE_ASSET")
        agents.append("11vt-asset-director")
        evidence.extend(["resource_strategy", "license_matrix", "asset_manifest"])
    if any(hit in text for hit in ("game", "gameplay", "playable", "mechanic", "game feel")):
        classes.append("GAME_CREATIVE")
        skills.append("11vt-game-development")
        evidence.extend(["playable_evidence", "feel_review"])
    if any(hit in text for hit in ("shader", "webgl", "webgpu", "canvas", "three", "3d", "blender", "unreal")):
        classes.append("HYBRID_PRODUCTION")
        agents.append("11vt-technical-artist")
        evidence.extend(["craft_mechanism_plan", "render_or_runtime_capture"])
    if any(hit in text for hit in ("character", "creature")):
        classes.append("CHARACTER")
        evidence.extend(["silhouette", "proportion", "identity_protection"])
    if any(hit in text for hit in ("environment", "world", "level")):
        classes.append("ENVIRONMENT")
        evidence.extend(["world_logic", "environment_readability"])
    if not classes:
        classes.append("NON_CREATIVE_ENGINEERING")
        skills.extend(["11vt-production-engineering", "11vt-testing-verification"])
        evidence.extend(["tests_or_runtime_evidence"])

    trivial_patterns = (r"\breadme\s+typo\b", r"\btypo\b", r"\bone-line\b", r"\bsmall\s+text\s+fix\b")
    trivial = any(re.search(pattern, text) for pattern in trivial_patterns)
    substantial_creative = bool(set(classes) & CREATIVE_CLASSES) and not trivial
    return {
        "schema_version": 1,
        "intent": intent,
        "task_classes": sorted(set(classes)),
        "substantial_creative": substantial_creative,
        "required_skills": sorted(set(skills)),
        "required_agents": sorted(set(agents)),
        "required_evidence": sorted(set(evidence)),
        "routing_stamp_required": substantial_creative,
        "concept_gate_required": substantial_creative,
        "first_pixel_required": substantial_creative,
    }


def route_stamp(intent: str, out: Path | None = None) -> dict[str, Any]:
    result = classify_intent(intent)
    result["kind"] = "creative-routing-stamp"
    result["decision"] = "CREATIVE_STUDIO_REQUIRED" if result["substantial_creative"] else "STANDARD_ROUTE"
    result["fail_closed_if_missing"] = [
        "concept_gate" if result["concept_gate_required"] else "",
        "first_pixel_review" if result["first_pixel_required"] else "",
        "rendered_evidence" if result["first_pixel_required"] else "",
    ]
    result["fail_closed_if_missing"] = [x for x in result["fail_closed_if_missing"] if x]
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def evaluate_concept(doc: dict[str, Any]) -> dict[str, Any]:
    blockers = []
    if doc.get("_load_error"):
        blockers.append("concept_document_unreadable")
    missing = _missing(doc, CONCEPT_REQUIRED)
    if missing:
        blockers.append("missing_concept_fields:" + ",".join(missing))
    thesis = str(doc.get("creative_thesis", "")).strip().lower()
    dna = json.dumps(doc.get("style_world_dna", ""), ensure_ascii=False).lower()
    thesis_words = set(re.findall(r"[a-z0-9-]+", thesis))
    if thesis_words and thesis_words.issubset(GENERIC_TERMS):
        blockers.append("generic_thesis_only")
    if len(thesis) < 40:
        blockers.append("creative_thesis_too_thin")
    if not dna or len(dna) < 80:
        blockers.append("style_world_dna_too_thin")
    if not doc.get("reference_principles"):
        blockers.append("reference_principles_missing")
    if not doc.get("resource_strategy"):
        blockers.append("resource_strategy_missing")
    return {
        "schema_version": 1,
        "kind": "concept-gate-evaluation",
        "decision": "PASS" if not blockers else "FAIL_CLOSED",
        "blockers": blockers,
        "required_before_broad_implementation": True,
        "non_substitution_rule": "A concept that could fit 100 unrelated products cannot pass.",
    }


def evaluate_references(doc: dict[str, Any]) -> dict[str, Any]:
    refs = doc.get("references", []) if isinstance(doc, dict) else []
    blockers: list[str] = []
    if not refs:
        blockers.append("no_references")
    for idx, ref in enumerate(refs):
        if not isinstance(ref, dict):
            blockers.append(f"reference_{idx}_not_object")
            continue
        missing = _missing(ref, REFERENCE_REQUIRED)
        if missing:
            blockers.append(f"reference_{idx}_missing:" + ",".join(missing))
    return {
        "schema_version": 1,
        "kind": "reference-gate-evaluation",
        "decision": "PASS" if not blockers else "FAIL_CLOSED",
        "blockers": blockers,
        "copying_policy": "Extract principles; do not copy protected visual identity.",
    }


def evaluate_craft_plan(doc: dict[str, Any]) -> dict[str, Any]:
    mediums = doc.get("mediums", []) if isinstance(doc, dict) else []
    blockers: list[str] = []
    if not mediums:
        blockers.append("no_mediums_selected")
    for idx, medium in enumerate(mediums):
        if not isinstance(medium, dict):
            blockers.append(f"medium_{idx}_not_object")
            continue
        if not medium.get("name"):
            blockers.append(f"medium_{idx}_name_missing")
        if not medium.get("mechanisms"):
            blockers.append(f"medium_{idx}_mechanisms_missing")
        if not medium.get("stages"):
            blockers.append(f"medium_{idx}_stages_missing")
        if medium.get("maturity_claim") in {"FINAL", "PRODUCTION", "SIGNATURE"} and "BLOCKOUT" in medium.get("stages", []):
            blockers.append(f"medium_{idx}_blockout_claimed_final")
    return {
        "schema_version": 1,
        "kind": "craft-mechanism-gate-evaluation",
        "decision": "PASS" if not blockers else "FAIL_CLOSED",
        "blockers": blockers,
        "rule": "Selected mechanisms must serve thesis; mechanism inventory is active but not over-triggered.",
    }


def evaluate_quality_bundle(doc: dict[str, Any]) -> dict[str, Any]:
    blockers = []
    missing = _missing(doc, QUALITY_REQUIRED)
    if missing:
        blockers.append("missing_quality_sections:" + ",".join(missing))
    first_pixel = doc.get("first_pixel_review") or {}
    if isinstance(first_pixel, dict):
        if not first_pixel.get("artifact"):
            blockers.append("first_pixel_artifact_missing")
        if first_pixel.get("classification") in {"GENERIC", "PRIMITIVE"} and not first_pixel.get("repair_performed"):
            blockers.append("weak_first_pixel_not_repaired")
    else:
        blockers.append("first_pixel_review_not_object")
    if not (doc.get("perceptual_qa") or {}).get("rendered_evidence"):
        blockers.append("rendered_evidence_missing")
    if (doc.get("independent_review") or {}).get("can_block") is not True:
        blockers.append("independent_review_not_blocking")
    if (doc.get("professional_finish") or {}).get("artifact_specific_corrections") in (None, [], ""):
        blockers.append("professional_finish_not_artifact_specific")
    return {
        "schema_version": 1,
        "kind": "quality-enforcement-evaluation",
        "decision": "PASS" if not blockers else "FAIL_CLOSED",
        "blockers": blockers,
        "claim_boundary": "Rendered evidence can support inspection; it does not mathematically prove taste.",
    }


def evaluate_release_assets(doc: dict[str, Any]) -> dict[str, Any]:
    assets = doc.get("assets", []) if isinstance(doc, dict) else []
    blockers: list[str] = []
    for idx, asset in enumerate(assets):
        if not isinstance(asset, dict):
            blockers.append(f"asset_{idx}_not_object")
            continue
        state = asset.get("asset_state")
        if asset.get("shipping_scope") is False or state == "REFERENCE_ONLY":
            continue
        license_state = asset.get("license_state")
        if state in RELEASE_BLOCKERS:
            blockers.append(f"asset_{idx}_blocked_state:{state}")
        if license_state in {"LICENSE_UNCLEAR", "UNKNOWN", "UNVERIFIED"}:
            blockers.append(f"asset_{idx}_license_unclear")
        if asset.get("attribution_required") and not asset.get("attribution_text"):
            blockers.append(f"asset_{idx}_attribution_missing")
        if asset.get("raw_source_exposed") and asset.get("redistribution") == "REDISTRIBUTION_RESTRICTED":
            blockers.append(f"asset_{idx}_forbidden_raw_source_exposure")
    return {
        "schema_version": 1,
        "kind": "release-asset-gate-evaluation",
        "decision": "PASS" if not blockers else "FAIL_CLOSED",
        "blockers": blockers,
        "rule": "No LICENSE_UNCLEAR or PROTOTYPE_ASSET may silently ship.",
    }


def terminal_matrix(evidence_dir: Path, out: Path | None = None) -> dict[str, Any]:
    criteria = [
        "RESEARCH_RELIABILITY", "CREATIVE_ROUTING", "CONCEPT_GATE", "REFERENCE_GATE",
        "ORIGINALITY_GATE", "CRAFT_MECHANISM_GATE", "RESOURCE_INTELLIGENCE", "ITCH_IO_PROVIDER",
        "LICENSE_INTELLIGENCE", "ASSET_VAULT", "SOURCE_ADAPT_CREATE", "RESOURCE_SURPASS",
        "PROTOTYPE_SHIPPING_BOUNDARY", "ASSET_SECURITY", "FIRST_PIXEL_REVIEW", "PERCEPTUAL_QA",
        "INDEPENDENT_REVIEW", "PROFESSIONAL_FINISH", "EXPERIENCE_MEMORY", "GENERALIZATION",
        "FIRST_PASS_QUALITY", "GLOBAL_DEPLOYMENT", "INTEGRATED_PRODUCT_PROOF",
    ]
    mapping = {
        "RESEARCH_RELIABILITY": evidence_dir / "research-unavailable-example.json",
        "CREATIVE_ROUTING": evidence_dir / "routing-stamp.json",
        "CONCEPT_GATE": evidence_dir / "concept-gate-result.json",
        "REFERENCE_GATE": evidence_dir / "reference-gate-result.json",
        "ORIGINALITY_GATE": evidence_dir / "originality-gate-result.json",
        "CRAFT_MECHANISM_GATE": evidence_dir / "craft-gate-result.json",
        "RESOURCE_INTELLIGENCE": evidence_dir / "itch-unreal-ui-kit-discovery.json",
        "ITCH_IO_PROVIDER": evidence_dir / "itch-unreal-ui-kit-discovery.json",
        "LICENSE_INTELLIGENCE": evidence_dir / "license-unclear-result.json",
        "ASSET_VAULT": evidence_dir / "asset-vault-query-result.json",
        "SOURCE_ADAPT_CREATE": evidence_dir / "source-adapt-create-result.json",
        "RESOURCE_SURPASS": evidence_dir / "resource-surpass-result.json",
        "PROTOTYPE_SHIPPING_BOUNDARY": evidence_dir / "release-asset-gate-result.json",
        "ASSET_SECURITY": evidence_dir / "resource-security-result.json",
        "FIRST_PIXEL_REVIEW": evidence_dir / "quality-gate-result.json",
        "PERCEPTUAL_QA": evidence_dir / "quality-gate-result.json",
        "INDEPENDENT_REVIEW": evidence_dir / "quality-gate-result.json",
        "PROFESSIONAL_FINISH": evidence_dir / "quality-gate-result.json",
        "EXPERIENCE_MEMORY": evidence_dir / "experience-memory-result.json",
        "GENERALIZATION": evidence_dir / "foundry-ascension-golden-tasks.json",
        "FIRST_PASS_QUALITY": evidence_dir / "integrated-demo-manifest.json",
        "GLOBAL_DEPLOYMENT": evidence_dir / "global-deployment-result.json",
        "INTEGRATED_PRODUCT_PROOF": evidence_dir / "integrated-demo-manifest.json",
    }
    rows: dict[str, Any] = {}
    for cid in criteria:
        path = mapping.get(cid)
        if path and path.exists():
            payload = load(path)
            decision = payload.get("decision")
            if decision in {"PASS", "CREATIVE_STUDIO_REQUIRED", "STANDARD_ROUTE", "CREATE_ORIGINAL", "VAULT_NOT_INITIALIZED"} or payload.get("status") == "PASS" or payload.get("ok") is True or payload.get("provider") == "ITCH_IO" or payload.get("shipping_allowed") is False or payload.get("requires_manual_review") is True:
                status = "PASS"
            elif payload.get("status") in {"LIVE_RESEARCH_UNAVAILABLE", "UNVERIFIED_DOMAIN_KNOWLEDGE"}:
                status = "GUARDED"
            else:
                status = "FAIL"
            rows[cid] = {"status": status, "evidence": str(path), "decision": decision or payload.get("status") or payload.get("provider")}
        else:
            rows[cid] = {"status": "NOT_PROVEN", "evidence": str(path) if path else "not_yet_mapped"}
    result = {
        "schema_version": 1,
        "kind": "ultimate-foundry-ascension-terminal-matrix",
        "rows": rows,
        "counts": {state: sum(row["status"] == state for row in rows.values()) for state in ("PASS", "GUARDED", "FAIL", "NOT_PROVEN")},
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="creative_studio_gates")
    sub = parser.add_subparsers(dest="cmd", required=True)
    route = sub.add_parser("route"); route.add_argument("intent"); route.add_argument("--out", type=Path)
    concept = sub.add_parser("concept"); concept.add_argument("json", type=Path); concept.add_argument("--out", type=Path)
    refs = sub.add_parser("references"); refs.add_argument("json", type=Path); refs.add_argument("--out", type=Path)
    craft = sub.add_parser("craft"); craft.add_argument("json", type=Path); craft.add_argument("--out", type=Path)
    quality = sub.add_parser("quality"); quality.add_argument("json", type=Path); quality.add_argument("--out", type=Path)
    release = sub.add_parser("release-assets"); release.add_argument("json", type=Path); release.add_argument("--out", type=Path)
    matrix = sub.add_parser("matrix"); matrix.add_argument("evidence_dir", type=Path); matrix.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    if args.cmd == "route":
        result = route_stamp(args.intent, args.out)
        code = 0
    elif args.cmd == "concept":
        result = evaluate_concept(load(args.json)); code = 0 if result["decision"] == "PASS" else 2
    elif args.cmd == "references":
        result = evaluate_references(load(args.json)); code = 0 if result["decision"] == "PASS" else 2
    elif args.cmd == "craft":
        result = evaluate_craft_plan(load(args.json)); code = 0 if result["decision"] == "PASS" else 2
    elif args.cmd == "quality":
        result = evaluate_quality_bundle(load(args.json)); code = 0 if result["decision"] == "PASS" else 2
    elif args.cmd == "release-assets":
        result = evaluate_release_assets(load(args.json)); code = 0 if result["decision"] == "PASS" else 2
    elif args.cmd == "matrix":
        result = terminal_matrix(args.evidence_dir, args.out); code = 0 if not result["counts"].get("FAIL") else 2
    else:
        raise AssertionError(args.cmd)
    if getattr(args, "out", None) and args.cmd not in {"route", "matrix"}:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
