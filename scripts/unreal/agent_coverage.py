#!/usr/bin/env python3
"""Audit Unreal Game Studio role coverage without manufacturing specialists."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROLES = {
    "game_director": ["11vt-creative-director", "11vt-game-development"],
    "systems_designer": ["11vt-experience-designer", "11vt-game-development"],
    "level_designer": ["11vt-experience-designer", "11vt-game-development"],
    "unreal_technical_director": ["11vt-technical-artist", "11vt-game-development"],
    "gameplay_engineer": ["11vt-production-engineering", "11vt-language-workflows"],
    "technical_artist": ["11vt-technical-artist"],
    "character_animation": ["11vt-motion-director", "11vt-technical-artist"],
    "niagara_vfx": ["11vt-technical-artist", "11vt-motion-director"],
    "rendering": ["11vt-technical-artist", "11vt-performance-security"],
    "audio": ["11vt-creative-production", "11vt-game-development"],
    "cinematics": ["11vt-motion-director", "11vt-creative-director"],
    "performance": ["11vt-performance-security"],
    "unreal_qa": ["11vt-testing-verification", "11vt-visual-qa-director"],
    "independent_game_review": ["11vt-independent-reviewer"],
}


def audit(root: Path) -> dict:
    repo_agents = root / "plugin/agents"
    repo_skills = root / "plugin/skills"
    if not repo_agents.exists() or not repo_skills.exists():
        # When synced globally, the capability-system lives below ~/.claude;
        # inspect the actual global providers rather than assuming repo layout.
        global_root = Path.home() / ".claude"
        repo_agents = global_root / "agents"
        repo_skills = global_root / "skills"
    agents = {p.stem for p in repo_agents.glob("*.md")}
    skills = {p.name for p in repo_skills.iterdir() if p.is_dir()} if repo_skills.exists() else set()
    roles = {}
    for role, candidates in ROLES.items():
        present = [name for name in candidates if name in agents or name in skills]
        roles[role] = {"providers": present, "status": "covered-by-existing-specialist" if present else "gap"}
    return {"schema_version": 1, "kind": "unreal-specialist-coverage", "agents": sorted(agents), "skills": sorted(skills), "roles": roles, "principle": "reuse existing specialists until a distinct Unreal evidence-backed responsibility justifies a new agent"}


def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2]); p.add_argument("--out", type=Path)
    args = p.parse_args(); result = audit(args.root)
    if args.out: args.out.parent.mkdir(parents=True, exist_ok=True); args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
