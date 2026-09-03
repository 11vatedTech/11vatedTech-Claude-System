#!/usr/bin/env python3
"""
Foundry Mission — stable programmatic mission entrypoint.
Receives Founder intent and resolves: disciplines, tools, models, knowledge, evidence requirements.
Does not replace Claude conversation. Proves the system has a stable execution boundary.
"""
from __future__ import annotations
import json, sys, time, subprocess, hashlib, os, uuid, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "config" / "product-portfolio-registry.json"
EXPERIENCE_DIR = ROOT / "artifacts" / "experiences"


def resolve_product(intent: str) -> dict[str, Any] | None:
    """Resolve a registered product by canonical name, ID, or explicit alias.
    
    Matching strategy:
    1. Exact substring: product name/ID is a substring of the query
    2. Word overlap: any significant word from the product name/ID appears in the query
    3. Alias match: explicit alias matches
    """
    if not REGISTRY_PATH.exists():
        return None
    products = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")).get("products", [])
    query = intent.casefold()
    # Stop words that don't help identify products
    stop_words = {'the', 'a', 'an', 'is', 'are', 'for', 'and', 'or', 'of', 'to', 'in', 'on', 'at', 'by', 'with', 'from', 'review', 'inspect', 'check', 'look', 'analyze', 'assess', 'evaluate'}
    query_words = set(w for w in query.split() if len(w) > 2 and w not in stop_words)
    for product in products:
        terms = [product.get("product_id", ""), product.get("name", "")]
        terms.extend(product.get("aliases", []))
        # Strategy 1: substring match (original)
        if any(term and term.casefold() in query for term in terms):
            return product
        # Strategy 2: word overlap
        for term in terms:
            if not term:
                continue
            term_words = set(w for w in term.casefold().split() if len(w) > 2)
            if term_words & query_words:
                return product
    return None

def resolve_disciplines(intent: str) -> list[str]:
    """Map intent keywords to Foundry disciplines."""
    intent_lower = intent.lower()
    disciplines = []
    keyword_map = {
        "frontend": ["frontend", "ui", "ux", "web", "html", "css", "react", "nextjs", "component"],
        "character_identity": ["character", "pumkit", "concept art", "identity", "silhouette", "mascot"],
        "3d": ["3d", "blender", "mesh", "model", "render", "glb", "glTF"],
        "animation": ["animation", "rigging", "motion", "keyframe", "skeleton"],
        "vfx": ["vfx", "particle", "simulation", "niagara", "effect"],
        "game_dev": ["game", "unreal", "ue5", "gameplay", "level"],
        "software_engineering": ["code", "refactor", "bug", "test", "api", "database", "architecture"],
        "research": ["research", "investigate", "analyze", "compare", "survey"],
        "product_strategy": ["product", "pricing", "market", "launch", "audience", "competitive"],
        "commercial_intelligence": ["revenue", "customer", "pipeline", "crm", "sales"],
        "creative_direction": ["art direction", "visual style", "palette", "typography", "composition"],
        "security": ["security", "vulnerability", "auth", "encryption", "audit"],
        "documentation": ["docs", "documentation", "readme", "spec", "adr"],
    }
    for disc, keywords in keyword_map.items():
        if any(kw in intent_lower for kw in keywords):
            disciplines.append(disc)
    return disciplines or ["general"]

def resolve_models(disciplines: list[str]) -> dict[str, str]:
    """Select model roles based on disciplines."""
    model_map = {
        "frontend": {"critic": "gemini-3.7-flash", "challenger": "haiku-4.5", "grounding": "qwen3-vl-8b"},
        "character_identity": {"critic": "gemini-3.7-flash", "challenger": "haiku-4.5", "grounding": "qwen3-vl-8b"},
        "3d": {"critic": "gemini-3.7-flash", "grounding": "qwen3-vl-8b"},
        "software_engineering": {"orchestrator": "claude", "analysis": "codestral-22b"},
        "research": {"orchestrator": "claude", "web": "tavily"},
        "product_strategy": {"orchestrator": "claude", "research": "web-search"},
    }
    models = {"orchestrator": "claude"}
    for disc in disciplines:
        if disc in model_map:
            models.update(model_map[disc])
    return models

def resolve_tools(disciplines: list[str]) -> list[str]:
    """Select tools based on disciplines."""
    tool_map = {
        "frontend": ["playwright", "browser", "lighthouse"],
        "character_identity": ["image-analysis", "visual-canon"],
        "3d": ["blender", "render"],
        "software_engineering": ["git", "lsp", "test-runner"],
        "research": ["web-search", "kapiF-retrieval"],
        "game_dev": ["unreal-editor", "compile"],
    }
    tools = []
    for disc in disciplines:
        tools.extend(tool_map.get(disc, []))
    return list(set(tools)) or ["none-required"]

def resolve_knowledge(disciplines: list[str]) -> list[str]:
    """Select knowledge packs."""
    pack_map = {
        "frontend": ["frontend-engineering", "ui-ux-interaction", "typography-information-design"],
        "character_identity": ["two-d-art-illustration", "art-direction-visual-development"],
        "3d": ["three-d-modeling", "material-lookdev", "lighting-rendering"],
        "software_engineering": ["software-engineering", "architecture"],
        "product_strategy": ["product-strategy", "market-validation", "pricing"],
    }
    packs = []
    for disc in disciplines:
        packs.extend(pack_map.get(disc, []))
    return list(set(packs)) or ["general"]

def compile_mission(intent: str) -> dict[str, Any]:
    """Full mission compilation."""
    disciplines = resolve_disciplines(intent)
    return {
        "mission_id": f"MISSION-{uuid.uuid4().hex}",
        "intent": intent,
        "disciplines": disciplines,
        "models": resolve_models(disciplines),
        "tools": resolve_tools(disciplines),
        "knowledge_packs": resolve_knowledge(disciplines),
        "evidence_requirements": ["primary-evidence", "deterministic-facts"],
        "required_outputs": ["objective_output", "validated_evidence"],
        "validation": "foundry-validate",
        "escalation": "founder-review" if any(d in disciplines for d in ["frontend", "character_identity", "creative_direction"]) else "auto",
        "stop_conditions": ["objective-defects-resolved", "founder-approval"],
    }


def execute_mission(mission: dict[str, Any]) -> dict[str, Any]:
    """Execute a bounded mission; discovery evidence alone cannot complete it."""
    started = time.time()
    evidence = []
    errors = []
    intent = mission["intent"]
    # Always capture the compiled plan and repository facts.
    evidence.append({"type": "mission_plan", "path": f"artifacts/{mission['mission_id']}.json"})
    product = resolve_product(intent)
    target = Path(product["repository"]["local_path"]) if product else None
    repository_facts = None
    if target and target.exists():
        status = subprocess.run(["git", "-C", str(target), "status", "--porcelain=v1"], capture_output=True, text=True)
        head = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], capture_output=True, text=True)
        repository_facts = {"type":"repository_facts", "path":str(target), "head":head.stdout.strip(), "dirty":bool(status.stdout.strip()), "file_count":sum(1 for f in target.rglob('*') if f.is_file() and '.git' not in f.parts)}
        evidence.append(repository_facts)
    if product:
        registry_record = {"type": "registry_resolution", "product_id": product["product_id"], "lifecycle": product.get("lifecycle"), "permissions": product.get("foundry_access", {})}
        evidence.append(registry_record)
        if "report" in intent.casefold() and "modif" in intent.casefold():
            sys.path.insert(0, str(ROOT / "scripts"))
            from kapif.mission_compiler import compile_packet
            packet = compile_packet(intent, mission_id=mission["mission_id"], disciplines=mission.get("disciplines", []))
            packet_path = ROOT / "artifacts" / "missions" / f"{mission['mission_id']}-kapif-packet.json"
            packet_path.parent.mkdir(parents=True, exist_ok=True)
            packet_path.write_text(json.dumps(packet, indent=2), encoding="utf-8")
            objective = {
                "product_id": product["product_id"],
                "name": product.get("name"),
                "repository": {**product.get("repository", {}), "live_head": repository_facts.get("head") if repository_facts else None, "live_dirty": repository_facts.get("dirty") if repository_facts else None},
                "lifecycle": product.get("lifecycle"),
                "revision": repository_facts.get("head") if repository_facts and repository_facts.get("head") else product.get("repository", {}).get("head"),
                "foundry_permissions": product.get("foundry_access", {}),
                "knowledge_packet": {
                    "path": str(packet_path),
                    "relevant_atoms": packet.get("relevant_atoms", []),
                    "excluded_atoms": packet.get("excluded_atoms", []),
                    "database_stats": packet.get("database_stats", {}),
                },
                "mutation_performed": False,
            }
            evidence.append({"type": "knowledge_packet", "path": str(packet_path), "relevant_atoms": len(packet.get("relevant_atoms", [])), "excluded_atoms": len(packet.get("excluded_atoms", []))})
            evidence.append({"type": "objective_output", "data": objective})
            evidence.append({"type": "validated_evidence", "checks": {
                "registry_resolved": True,
                "product_repository_known": bool(product.get("repository", {}).get("local_path")),
                "kapif_packet_compiled": True,
                "epistemic_filter_applied": "excluded_atoms" in packet,
                "no_product_mutation": True,
            }})
    required_outputs = mission.get("required_outputs", ["objective_output", "validated_evidence"])
    produced_outputs = [item["type"] for item in evidence if item.get("type") not in {"mission_plan", "repository_facts"}]
    missing_outputs = [item for item in required_outputs if item not in produced_outputs]
    result = "FAILED" if missing_outputs else "COMPLETED_WITH_GUARDRAILS"
    if missing_outputs:
        errors.append({"code": "REQUIRED_OUTPUT_MISSING", "outputs": missing_outputs})
    experience = {"experience_id": f"EXP-{uuid.uuid4().hex}", "mission_id": mission["mission_id"], "product": product.get("product_id") if product else None, "objective": intent, "evidence": evidence, "result": result, "limitations": errors, "models": mission.get("models", {}), "tools": mission.get("tools", []), "transferable_principle": "Discovery facts do not establish objective completion; bounded registry reports require objective output plus validated evidence."}
    EXPERIENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EXPERIENCE_DIR / f"{experience['experience_id']}.json").write_text(json.dumps(experience, indent=2), encoding="utf-8")
    return {"mission_id": mission["mission_id"], "intent": intent,
            "resolved_product": product.get("product_id") if product else None,
            "resolved_target": str(target) if target else None,
            "result": result, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "duration_seconds": round(time.time()-started,3), "evidence": evidence, "errors": errors, "fallbacks": ["deterministic_local_execution"], "decision": "review_output_before_mutation"}


def main():
    if len(sys.argv) < 2:
        print("Usage: foundry_mission.py <intent>")
        print("Example: foundry_mission.py 'review the Pumkit frontend for character fidelity'")
        sys.exit(1)

    execute_requested = "--execute" in sys.argv
    intent = " ".join(arg for arg in sys.argv[1:] if arg != "--execute")
    mission = compile_mission(intent)

    print("11VATEDTECH FOUNDRY MISSION")
    print(f"Intent: {intent}")
    print(f"Mission ID: {mission['mission_id']}")
    print(f"Disciplines: {', '.join(mission['disciplines'])}")
    print(f"Models: {json.dumps(mission['models'], indent=2)}")
    print(f"Tools: {', '.join(mission['tools'])}")
    print(f"Knowledge: {', '.join(mission['knowledge_packs'])}")
    print(f"Escalation: {mission['escalation']}")
    print(f"Validation: {mission['validation']}")

    # Save mission plan
    out = ROOT / "artifacts" / f"{mission['mission_id']}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mission, indent=2))
    print(f"\nMission plan saved: {out}")
    if execute_requested:
        result = execute_mission(mission)
        result_path = ROOT / "artifacts" / "missions" / f"{mission['mission_id']}-result.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        if result_path.exists():
            raise RuntimeError(f"Refusing duplicate mission result: {result_path.name}")
        payload = json.dumps(result, indent=2)
        fd, temporary = tempfile.mkstemp(prefix=f".{mission['mission_id']}-", suffix=".tmp", dir=result_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.link(temporary, result_path)
        except FileExistsError as exc:
            raise RuntimeError(f"Refusing duplicate mission result: {result_path.name}") from exc
        finally:
            try: os.unlink(temporary)
            except FileNotFoundError: pass
        print(f"Mission result: {result['result']}\nEvidence saved: {result_path}")

if __name__ == "__main__":
    main()
