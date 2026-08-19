# Changelog

## 0.4.1 — 2026-08-18

Capability Ascension milestone 1 — the Foundry moves from infrastructure to
creation capability (FOUNDATION GENESIS COMPLETE / CAPABILITY ASCENSION
ACTIVE):

- **Structured Blender intelligence**: 15 schema-validated high-level ops
  (scene/mesh/material/rig/animation/camera/render/asset) with validation,
  error handling, session .blend chaining, and structured output; Blender
  5.x layered-action API compatibility; structural GLB validator.
- **Animation observability**: loop-continuity QA (pixel diff + PSNR over
  rendered endpoints), foot-slide velocity heuristic, turntable -> H.264
  motion preview videos.
- **Asset Resolver**: 13 resolution modes x 9 factors with flag-driven
  policy and hard rules (unknown-license external is blocking).
- **Asset Vault**: content-addressed immutable IDs, lineage, provenance,
  duplicate detection, previews, search, license guards.
- **Requirement discovery**: production dependency graphs for 7 product
  kinds (creature entity expands to 19 nodes / 27 edges / 12 disciplines).
- **Quality models + ladder**: 6 disciplines with checkable dimensions;
  BLOCKOUT -> SIGNATURE transition gates.
- **Capability Ascension Register**: all 53 capabilities audited with
  missing-executable/observation/evaluation/verification and next actions.
- **Failure-path tests**: pixel-diff, GLB validator, rollback guard,
  resolver license block, vault license guard, routing mutation, broken-loop
  probe — every gate proven to catch its failure path.
- **First L5 capabilities (5)**: pixel-diff, blender-bridge, animation-qa,
  global-sync, rollback — enforced by l5_evidence.py with independent review
  record and documented limitations. Baseline now L0:1 L2:3 L3:19 L4:25 L5:5.

## 0.4.0 — 2026-08-18

Media-toolchain migration (from the reference workspace, verified in place):

- Fixed tool detection for installer-path ImageMagick/Inkscape/Blender
  (`resolve_tool` falls back to known `Program Files` locations when PATH
  misses them); enabled real `magick compare -metric AE` pixel diff with
  ffmpeg PSNR fallback, ImageMagick SVG rasterization fallback, and the
  Blender bridge.
- Wired the media toolchain (image/vector/video/audio) into
  `scripts/validate/system_regression.py` as a first-class regression gate.
- Replaced dead root `tools/` shells with a pointer to `scripts/media/vtmedia/`.

Genesis deployment (corrected global architecture):

- Strengthened the global deployment mechanism: `sync_to_claude.py` now takes
  a timestamped pre-sync backup, records a deployment manifest (version +
  sha256 inventory), supports `--dry-run`, `--rollback`, `--list`, and stale
  `11vt-*` detection; syncs skills, agents, and the capability-system docs.
- Added `validate_capability_installation.py` (repo-owned) for the global
  `~/.claude` install: repo-derived expectations, CLAUDE.md pointer, secret
  scan, 9Router discovery + chat smoke.
- Replaced the shallow name-existence trigger check with a real routing
  evaluation (`routing_eval.py`): coverage, overtrigger, and dangling-route
  checks, mutation-tested.
- Added the capability ontology (`config/capability-ontology.json`, 13 domains
  / 49 capabilities) with L0-L5 maturity and an evidence-gated validator
  (`ontology_check.py`); baseline L0:1 L2:4 L3:23 L4:21.
- Ported the Foundry gap register into the canonical repo with statuses.
- Deployed globally (deployments `20260818-203656` / `20260818-203830`):
  verified from a clean unrelated project that Claude auto-discovers 20 global
  skills + 8 agents and the entrypoint, through a healthy 9Router; rollback
  round-trip proven.

## 0.3.0 — 2026-08-15

- Added `11vt-creative-production` as modular creative-production operating skill.
- Added specialist agents: Creative Director, Art Director, Experience Designer, Motion Director, Technical Artist, Asset Director, Visual QA Director.
- Expanded `11vt-design-director` with anti-generic aesthetic gates, visual evidence discipline, escalation ladder, and stronger visual QA checklist.
- Expanded `11vt-independent-reviewer` to require rendered visual evidence for UI-facing work.
- Expanded `11vt-capability-entrypoint` routing for high-fidelity creative, game presentation, 3D/rendering, audiovisual, typography, and visual QA tasks.
- Added creative-production architecture doc, visual evidence requirements, project visual canon template, asset protocol, and visual QA rubric.
- Expanded project template with design system, asset pipeline, visual canon directory, and manifest canon pointers.
- Expanded trigger and behavioral evaluations for creative-production activation and non-overtriggering.
- Updated sync tooling to sync both skills and agents.

## 0.2.1 — 2026-08-15

- Added `11vt-capability-entrypoint` as universal Founder-intent routing skill.
- Added user-level `~/.claude/CLAUDE.md` pointer so new chats can find 11vatedTech canonical capabilities.
- Registered capability entrypoint in canonical capability registry.

## 0.2.0 — 2026-08-15

- Created canonical version-controlled 11vatedTech Claude System repository.
- Added internal plugin layout with skills, reviewer agent, hooks, and validation helpers.
- Added project bootstrap, product lifecycle, release engineering, manifest/evidence/review workflow.
- Added stack-neutral product repository template.
- Added regression, bootstrap fixture, manifest validation, and 9Router benchmark tooling.

## 0.1.0 — 2026-08-15

- Created Phase I global 11vatedTech skills and sourced 9Router skills in user Claude installation.
