---
name: 11vt-creative-production
description: Creative-production organization for 11vatedTech. Use for high-fidelity visual products, games, cinematic sites, art direction, motion, asset strategy, 3D/rendering/shader choices, typography systems, screenshot critique, or when Founder demands work beyond generic AI UI.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "0.3.0"
---

# 11vatedTech Creative Production

This capability turns visual work into a small production studio, not a styling pass.

Use when product success depends on visual identity, art direction, interaction feel, motion, audiovisual polish, 3D/rendering quality, or asset production. Do not use for routine backend work, trivial admin screens, or tiny mechanical UI changes unless the Founder explicitly raises the fidelity bar.

## Core policy

Working is not finished. Styled is not designed. High resolution is not high fidelity. Effects are not art direction.

Visual completion requires a concept, coherent visual grammar, production-appropriate assets, purposeful motion, responsive composition, accessibility, performance discipline, rendered inspection, and critique-driven iteration.

## Anti-default aesthetic gate

Before building, detect weak AI defaults:

- generic purple/blue neon cyberpunk
- arbitrary glassmorphism
- endless rounded dashboard cards
- meaningless particles, blur blobs, glows, fake holograms, HUD trim
- circles/icons used because no real asset exists
- enormous hero text in empty space
- stock Tailwind grids, pills, uniform radii, generic cards
- primitive geometry standing in for final artwork

These are allowed only when concept justifies them. If visual plan could fit 100 unrelated AI-generated apps, reject it before coding.

## Production roles

Activate only roles needed for scope. One person may execute several roles in small work; substantial work should use subagents or staged review.

1. Creative Director — owns emotional objective, thesis, metaphor, audience, differentiation, signature moments, and challenge to weak concept.
2. Art Director — turns thesis into color, type, material, lighting, texture, image, shape, icon, framing, rhythm, and negative-space grammar.
3. Experience Designer — owns journey, hierarchy, content structure, interaction choreography, progressive disclosure, responsive behavior, accessibility, and pacing.
4. Motion Director — owns entrances, exits, transformations, camera/scroll choreography, hover/focus, idle states, and state communication.
5. Technical Artist — chooses CSS/SVG/Canvas/WebGL/WebGPU/Three.js/raster/vector/video/shader/simulation based on intended artifact, not convenience.
6. Rendering Specialist — when dimensional work matters, owns geometry, PBR materials, lighting, environment, camera, post-processing, optimization, and asset pipeline.
7. Asset Director — identifies needed illustrations, textures, sprites, icons, logos, 3D objects, masks, overlays, generated maps, and licensing/reproducibility constraints.
8. Typography Specialist — makes type personality, scale, tracking, leading, numeric style, labels, and editorial/kinetic composition part of artwork.
9. Visual QA Director — adversarial critic. Finds generic aesthetics, weak composition, fake depth, poor hierarchy, inconsistent spacing, visual noise, missing states, and unverified claims.

## Required sequence for significant visual work

1. Understand intended experience and constraints.
2. Research references when current or non-obvious visual language matters. Study adjacent fields; extract principles, do not clone.
3. Write or update project visual canon when identity matters.
4. Define concept, narrative, composition, hierarchy, material language, motion, lighting, depth, asset needs, and 2–5 signature moments.
5. Choose implementation media deliberately.
6. Build vertical slice or full implementation.
7. Run app, inspect rendered desktop/tablet/mobile when previewable.
8. Interact with important states and transitions.
9. Compare screenshots/snapshots against canon.
10. Run Visual QA critique. If weak, escalate concept/layout/assets/motion, not only padding/colors/shadows.
11. Repeat until acceptance gates pass or report remaining limitation honestly.

## Project visual canon

For important visual products, create concise canon under `docs/design/`. Use `references/project-visual-canon-template.md`. Do not create bureaucracy for trivial work.

## Verification contract

For previewable UI, do not claim visual completion without rendered evidence. Record viewports, interaction states, console/network/server health, accessibility snapshot, screenshots or inspected selectors, known caveats, and unresolved visual limitations.

Use:

- `references/creative-production-protocol.md`
- `references/project-visual-canon-template.md`
- `references/visual-qa-rubric.md`
- `references/asset-production-protocol.md`
- `scripts/visual_evidence_check.py`

## Cooperation

Pair with:

- `11vt-design-director` for frontend UI execution and browser visual QA.
- `11vt-game-development` for game loop, feel, camera, VFX/audio, frame budget.
- `11vt-research-intelligence` for reference-first design, tooling, licensing, current graphics tech.
- `11vt-9router-orchestrator` for model/modal discovery and avoiding silent routing degradation.
- `11vt-testing-verification` for runtime/build/browser evidence.
- `11vt-independent-reviewer` or `11vt-visual-qa-director` before handoff on substantial visual work.

## Failure behavior

If assets/tooling/model capability are missing, do not fake production quality with primitives. State limitation, choose strongest local/open path, and mark scaffolding as scaffolding. If first visual pass looks generic, redesign concept or asset strategy before decorative tweaks.
