# Foundry Maturity Baseline

Baseline date: 2026-08-18 · System version: 0.4.0
Source of truth: `config/capability-ontology.json` (regenerate the report with
`python scripts/validate/ontology_check.py`).

## Distribution

| Level | Capabilities | Meaning |
|---|---|---|
| L0 | 1 | speech-to-text (no STT provider installed) |
| L1 | 0 | — |
| L2 | 4 | web research, TTS, image generation, GLB asset export |
| L3 | 23 | verified by automated tests |
| L4 | 21 | regression-gated / integrated with provenance |
| L5 | 0 | no capability is release-gated end-to-end yet |

The system is a **L3/L4 baseline**: the majority of capabilities are verified
(L3) or regression-gated (L4). No capability has reached L5 (governed) — the
release-gate + versioned + evaluation-covered bar is the next frontier.

## Evidence anchors (this session)

- **Tool detection fixed**: `11vt_media.py doctor` now reports ImageMagick
  7.1.2-29, Inkscape 1.4.4, Blender 5.2.0 LTS, ffmpeg 8.1.2, nvidia-smi — all
  PASS (previously ImageMagick/Inkscape/Blender were MISSING).
- **Real pixel diff**: `magick compare -metric AE` ran against the resolved
  installer path, reporting 521,324 differing pixels between a 1024×768
  gradient and its 2048×1536 upscale (`visual_equivalence_claim: false`).
- **SVG rasterization**: `vector-test` PASS via Inkscape provider.
- **Blender bridge**: Cycles preview render PASS, `render.png` produced via the
  resolved Blender 5.2 path.
- **Media regression gate**: image/vector/video/audio all `ok` inside
  `system_regression.py`.
- **Routing evaluation**: 10 trigger cases, 6 rubric categories, 0 failures;
  mutation-tested against coverage gaps, overtriggers, and dangling routes.
- **Ontology check**: 13 domains, 49 capabilities, every provider resolves,
  every evidence pointer exists.
- **Global deployment**: dry-run identified 5 stale capability-system files;
  validator confirms 29 skills, 8 agents, CLAUDE.md pointer, secret scan clean,
  9Router healthy (329 models).

## Deferred / degraded by design

- STT (L0): no whisper/STT provider installed; `9router-stt` returns 0 models.
- TTS (L2): 9Router exposes 5 TTS models; local voice pipeline is a placeholder.
- Image generation (L2): 9Router exposes 4 image models; generation is
  optional-not-default spend.
- GLB export (L2): exporter script exists; not yet exercised in a live export.
- L5 (governed) for all capabilities: requires a release gate that blocks
  version bumps without green regression + evidence, which is the next Genesis
  milestone.
