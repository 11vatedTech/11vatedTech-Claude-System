#!/usr/bin/env python3
"""
Foundry Mission — stable programmatic mission entrypoint.
Receives Founder intent and resolves: disciplines, tools, models, knowledge, evidence requirements.
Does not replace Claude conversation. Proves the system has a stable execution boundary.
"""
from __future__ import annotations
import json, sys, time, subprocess, hashlib, os, uuid
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

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
        "validation": "foundry-validate",
        "escalation": "founder-review" if any(d in disciplines for d in ["frontend", "character_identity", "creative_direction"]) else "auto",
        "stop_conditions": ["objective-defects-resolved", "founder-approval"],
    }


def execute_mission(mission: dict[str, Any]) -> dict[str, Any]:
    """Execute a bounded deterministic mission; planning alone remains PLANNED."""
    started = time.time()
    evidence = []
    errors = []
    intent = mission["intent"]
    # Always capture the compiled plan and repository facts.
    evidence.append({"type": "mission_plan", "path": f"artifacts/{mission['mission_id']}.json"})
    target = None
    if "pumkit" in intent.lower():
        target = Path.home() / "OneDrive/Desktop/11vatedTech-Portfolio/Products/Frontend-Designs/Pumkit-Frontend-Design"
    elif "growthos" in intent.lower():
        target = Path.home() / "OneDrive/Desktop/11vatedTech-Portfolio/Products/GrowthOS"
    if target and target.exists():
        status = subprocess.run(["git", "-C", str(target), "status", "--porcelain=v1"], capture_output=True, text=True)
        head = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"], capture_output=True, text=True)
        evidence.append({"type":"repository_facts", "path":str(target), "head":head.stdout.strip(), "dirty":bool(status.stdout.strip()), "file_count":sum(1 for f in target.rglob('*') if f.is_file() and '.git' not in f.parts)})
    result = "COMPLETED_WITH_GUARDRAILS" if target and target.exists() else "ESCALATION_REQUIRED"
    return {"mission_id": mission["mission_id"], "intent": intent, "result": result, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "duration_seconds": round(time.time()-started,3), "evidence": evidence, "errors": errors, "fallbacks": ["deterministic_local_execution"], "decision": "review_output_before_mutation"}


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
        result_path.write_text(json.dumps(result, indent=2))
        print(f"Mission result: {result['result']}\nEvidence saved: {result_path}")

if __name__ == "__main__":
    main()
