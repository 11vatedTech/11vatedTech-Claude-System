# Repository Boundary Audit — Milestone 1.1

**Date:** 2026-08-23  
**Purpose:** Classify every root-level directory and document nested-repository status before any topology changes.

## State Capture

```
HEAD:        90f798e
origin/main:  90f798e
Remote:       https://github.com/11vatedTech/11vatedTech-Claude-System.git
Branch:       main (clean, 0 ahead/behind)
```

## Nested Repository Flattening Incident

**Finding:** `11vated-growth_OS/.git` was removed during the previous push workflow.  
**Mechanism:** The push author discovered the nested repo had no remote and removed it to flatten into the Foundry commit.  
**Impact:** 11vated-growth_OS content is preserved in Foundry git history but original commit history, branches, and tags are lost.  
**Recovery:** No surviving copy found on any known path on this machine (Desktop, dev, projects, OneDrive root, worktrees).  

**Classification:** NESTED_REPOSITORY_FLATTENING + PROJECT_CONTENT_CONTAMINATES_FOUNDRY.

The content is preserved (files are tracked in the Foundry commit), but the repository boundary was violated. The Foundry should not house unrelated product source code.

## Root-Level Classification

| Directory/File | Classification | Evidence |
|---|---|---|
| `11vated-growth_OS/` | **PROJECT_SOURCE** | 11vatedTech product — API, web app, services, migrations. Not Foundry. |
| `Frontend-Designs/` | **PROJECT_SOURCE** | Pumkit frontend design work. Not Foundry. |
| `artifacts/` | **FOUNDRY_EVIDENCE** | Contains Ashwake calibration evidence, creative stack validation, asset vault. |
| `claude-backups/` | **FOUNDRY_FIXTURE** | Pre-ascension backup tars from sync_to_claude operations. |
| `config/` | **FOUNDRY_SOURCE** | Ontology, toolchain, registries, resource packs. |
| `docs/` | **FOUNDRY_SOURCE** | Architecture, protocols, evidence system. |
| `evaluations/` | **FOUNDRY_SOURCE** | Behavioral, regression, routing, trigger evaluations. |
| `plugin/` | **FOUNDRY_SOURCE** | Skills, agents, hooks — the deployable Foundry plugin. |
| `scripts/` | **FOUNDRY_SOURCE** | Install, validate, unreal, media, repo tools. |
| `templates/` | **FOUNDRY_SOURCE** | Product repository bootstrap template. |
| `tests/` | **FOUNDRY_SOURCE** | Disposable fixture area. |
| `tools/` | **FOUNDRY_FIXTURE** | Tool distributions (clangd, blender scripts, frontend tools). |
| `emberveil.glb` | **ACCIDENTAL_IMPORT** | 132-byte stub GLB at repo root. Should be in artifacts/flagship/. |
| `CHANGELOG.md` | **FOUNDRY_SOURCE** | |
| `CURRENT_STATE.md` | **FOUNDRY_SOURCE** | |
| `README.md` | **FOUNDRY_SOURCE** | |
| `VERSION` | **FOUNDRY_SOURCE** | |

## Proposed Boundary Repair

1. **Remove accidental import:** Move or delete `emberveil.glb` (132-byte stub) from repo root.
2. **Project directories:** `11vated-growth_OS/` and `Frontend-Designs/` must be relocated out of the Foundry repository. Options:
   - Move to a sibling directory outside the Foundry (`../11vated-growth_OS/`)
   - Extract to their own repositories
   - **Recommended:** Relocate to `../` (sibling of Foundry) and initialize independent repos when appropriate
3. **Foundry evidence:** Keep `artifacts/unreal/` and `artifacts/flagship/` as calibration evidence but guard against further project expansion
4. **Backups:** `claude-backups/` should be excluded from git (large tars) but kept on disk

## Git Safety

The previous push workflow performed `git add -A` into a workspace with:
- 26,445 files
- Unknown multi-GB untracked content (since filtered by gitignore)
- Nested repositories
- Force push to resolve unrelated histories

This must never recur. See `scripts/validate/git_safety_gate.py`.