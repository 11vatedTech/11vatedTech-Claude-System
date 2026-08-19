# Changelog

## 0.4.0 — 2026-08-18

- Fixed tool detection for installer-path ImageMagick/Inkscape/Blender
  (`resolve_tool` falls back to known `Program Files` locations when PATH
  misses them); enabled real `magick compare -metric AE` pixel diff with
  ffmpeg PSNR fallback, ImageMagick SVG rasterization fallback, and the
  Blender bridge.
- Wired the media toolchain (image/vector/video/audio) into
  `scripts/validate/system_regression.py` as a first-class regression gate.
- Replaced dead root `tools/` shells with a pointer to `scripts/media/vtmedia/`.

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
