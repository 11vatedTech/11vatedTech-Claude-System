# Foundry Maturity Baseline

Baseline date: 2026-08-22 (updated during Global Capability Ascension)
System version: 0.7.0
Source of truth: `config/capability-ontology.json` (regenerate the report with
`python scripts/validate/ontology_check.py`).

## Distribution

| Level | Capabilities | Meaning |
|---|---|---|
| L0 | 1 | speech-to-text (no STT provider installed) |
| L1 | 1 | Unreal native test discovery (source-only) |
| L2 | 17 | web research, TTS, image generation, runtime VFX, Unreal compile/gameplay/runtime/package preflight, mission value gate, capability-gap discovery, Creative Intelligence Institute policy, maturity contract, frontend/game institutes, resource packs, mission compiler, creative apprenticeship, frontend quality contract |
| L3 | 42 | verified by automated tests, semantic, production, Unreal design/handoff/import, commandlet, truth-audit, visual-evidence, model-selection, multi-language baseline, and explicit creative/UX evidence contracts |
| L4 | 26 | regression-gated / integrated with provenance |
| L5 | 5 | governed infrastructure/governance only: implementation + real use + failure test + regression + independent review + documented limitations |

First L5 capabilities (enforced by `scripts/validate/l5_evidence.py`):
`pixel-diff`, `blender-bridge`, `animation-qa`, `global-sync`, `rollback`.
L5 is kept scarce by design; the review record (`docs/l5-review-record-2026-08-18.md`)
documents the evidence chain and limitations of each. No broad creative production domain (design/VFX/cinematic/audio/3D production) is L5 yet. The canonical Emberveil artifact is COHERENT and evidence-gated, not a claim of professional or signature quality.

## Truth audit and course correction

`config/capability-truth-audit.json` is the authoritative claim-control report for this milestone. It classifies 24 capabilities as theoretical, 6 scripted, 45 operational, 10 verified, and 0 production-proven. These states intentionally do not equal ontology maturity labels when the evidence does not support the claim.

Ashwake is frozen as `CALIBRATION_FIXTURE_001`; see `artifacts/flagship/ASHWAKE-FREEZE.md` and `artifacts/flagship/ASHWAKE-LESSON-EXTRACTION.json`. The top-ten global gap register is `config/capability-gap-register.json`.

The executable global improvements are covered by `scripts/validate/foundry_ascension_tests.py`: truth auditing, mission value/drift gating, known-bad visual evidence rejection, evidence-based model selection, a Python/TypeScript/JavaScript/C++ semantic indexing baseline, mission compilation, causal creative transfer, and frontend evidence contracts. The multi-language baseline is lexical and explicitly not LSP/type-resolved.

The current creative curriculum is intentionally bounded. `config/resource-packs/` records source-grounded knowledge and implementation consequences for frontend/UI/UX, art direction/lookdev, and semantic engineering. The micro-lab fixtures demonstrate evidence transfer and evidence-contract behavior; they do not certify artistic taste, exceptional UX, or human validation.

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
- **Ontology check**: 18 domains, 92 capabilities, every provider resolves when
  9Router is available, and every evidence pointer exists; production-domain L5 is mechanically distinct from infrastructure L5.
- **Creative / experience / frontend ascension**: independent maturity axes,
  three source-grounded resource packs, mission compiler, causal micro-lab
  transfer gate, and frontend quality contract are covered by 12 focused
  Golden Tasks; no broad creative or UX mastery claim is made.
- **Global deployment**: dry-run identified 5 stale capability-system files;
  validator confirms 29 skills, 8 agents, CLAUDE.md pointer, secret scan clean,
  9Router health and chat smoke PASS; complete `/v1/models` discovery is
  currently degraded by a provider DNS timeout, preserved in
  `artifacts/unreal/health/9router-status-20260819.json`.

## Deferred / degraded by design

- STT (L0): no whisper/STT provider installed; `9router-stt` returns 0 models.
- TTS (L2): 9Router exposes 5 TTS models; local voice pipeline is a placeholder.
- Image generation (L2): 9Router exposes 4 image models; generation is
  optional-not-default spend.
- **Flagship calibration**: Emberveil canonical batch produced a 611KB valid GLB with 13 meshes, 4 materials, 4 authored animation clips, 24-frame turntable, 72-frame cinematic, runtime observation, perceptual QA, and structural variant gate. These are L3/L4 production evidence, not L5 artistic evidence.
- **Semantic repository intelligence**: Python AST index covers 51 files/268 symbols; six controlled golden tasks pass. Python-only and lexical limitations remain.
- **Unreal Game Studio vertical slice**: Unreal Engine 5.8.0 is installed at `C:/Program Files/Epic Games/UE_5.8`, with Editor/Cmd/UAT/Build surfaces and relevant plugin families detected. Visual Studio 2022 Build Tools 17.14.37411.7, MSVC 14.44.35207, and Windows SDK 10.0.26100.0 are present; the game target C++ module compiles successfully. Three original concepts were scored and Ashwake/Emberveil selected. A traceable game-design brief and 18-node/21-edge production graph were generated. The bounded Unreal `DataValidation` commandlet passed on the authoring project; Editor Python/AssetTools imported the real GLB, Niagara calibration and audio import passed, and the native test source was discovered but not executed. Runtime observation classified the unstaged game target as failing before map load due loose-content asset-registry/IO failure. Editor target/cook/package are blocked by the missing `.NET Framework 4.8 SDK` required by SwarmInterface; the existing Build Tools modification was offered but denied, so no runtime-play or packaged-build claim is made.
- L5 (governed) for all capabilities: requires a release gate that blocks
  version bumps without green regression + evidence, which is the next Genesis
  milestone.
