# Ashwake Environment Apprenticeship Phase 2 — Interim Selection Evidence Memo

Date: 2026-08-21
Status: interim. No final production direction selected.

## Current designations

- `CINDERWORKS_ABBEY`: CURRENT LEADING HYPOTHESIS, not proven winner.
- `EMBER_HOSPICE`: accepted hypothesis.
- `FALLEN_SUN_ORCHARD`: accepted hypothesis.

## Evidence now preserved

- Durable concept evidence: `docs/evidence/ashwake/environment-apprenticeship-phase-2/environment-concepts.json`
- Professional research pack: `docs/evidence/ashwake/environment-apprenticeship-phase-2/professional-research-pack.md`
- Three VISDEV packs: `docs/evidence/ashwake/environment-apprenticeship-phase-2/visdev-packs.md`
- Blind review packet: `docs/evidence/ashwake/environment-apprenticeship-phase-2/blind-review-packet.md`
- Runtime blockout capture report: `artifacts/unreal/health/ashwake-environment-apprenticeship-phase2-evidence.json`
- Capture automation: `scripts/unreal/ashwake_environment_phase2_capture.py`
- Runtime package: `artifacts/unreal/calibration/Packaged/ashwake-env-apprenticeship-phase2/`
- Specialist synthesis: `docs/evidence/ashwake/environment-apprenticeship-phase-2/specialist-review-synthesis.md`

## Runtime evidence summary

Package command:

```bash
python scripts/unreal/build_pipeline.py package artifacts/unreal/calibration/FoundryCalibration.uproject --archive artifacts/unreal/calibration/Packaged/ashwake-env-apprenticeship-phase2 --staging-dir artifacts/unreal/calibration/Saved/StagedBuilds_AshwakeEnvPhase2 --timeout 1800
```

Result: PASS.

Capture command:

```bash
python scripts/unreal/ashwake_environment_phase2_capture.py --timeout 180 --screenshots 4 --mode both
```

Result: PASS.

Per-direction evidence:

| Direction | Success run | Failure run | Required labs | Screenshots |
|---|---:|---:|---:|---:|
| CINDERWORKS_ABBEY | PASS | PASS | PASS | 4 success + 1 failure |
| EMBER_HOSPICE | PASS | PASS | PASS | 4 success + 1 failure |
| FALLEN_SUN_ORCHARD | PASS | PASS | PASS | 4 success + 1 failure |

Runtime claims proven:

- All three directions can spawn as selectable real-time blockouts through `-AshwakeEnvironmentDirection=...`.
- Each contains three embedded reliquary stations.
- Each contains blockout-only lighting, material, and state-feedback labs.
- Success and failure runtime modes execute with screenshots.
- Package and capture run under UE 5.8 packaged executable.

Runtime claims not proven:

- Final art quality.
- Human navigation comprehension.
- Best lighting variant.
- Material fidelity.
- VFX/audio final quality.
- Performance budget after real assets, fog, PCG, Nanite, or final materials.
- Founder preference.

## Tradeoff read, not vanity score

### Cinderworks Abbey

Strengths:

- Strongest immediate mechanic infrastructure.
- Heat-channel logic supports timing, route, and success response.
- Modular-kit path likely most controllable.
- Lighting can be value-disciplined inside bounded interior.

Blockers:

- Can collapse into generic dark cathedral plus orange cracks.
- Soot palette risks black crush.
- Must show civic heat-engine logic, not only sacred mood.

### Ember Hospice

Strengths:

- Strongest emotional metaphor: reliquary as patient.
- Physical support grammar naturally solves floating-relic issue.
- Set dressing can carry story through triage tags, masks, tubes, gauges, cradles.
- Failure can feel personal.

Blockers:

- Derivative risk near sci-fi horror/modern clinic.
- Animation/material burden higher.
- Glass/ward layout can confuse route affordance.

### Fallen Sun Orchard

Strengths:

- Strongest ownable world image and cosmology.
- Best success transformation potential: false dawn, roots, flora, weather, color.
- Strongest escape from test-chamber feeling.

Blockers:

- Highest proof burden: terrain, fog, particles, instancing, outdoor sightlines, performance.
- Vistas can overpower interactable reliquaries.
- Repeated organic rows risk disorientation or pattern noise.

## Completed after interim memo

1. Six specialist reviews completed: environment artist, level designer, lighting specialist, technical artist, game director, art director.
2. Specialist synthesis preserved in `docs/evidence/ashwake/environment-apprenticeship-phase-2/specialist-review-synthesis.md`.
3. Experience ledger and golden tasks updated for Phase 2 apprenticeship evidence.

## Required before final selection

1. Human no-HUD navigation tests.
2. Equivalent representative screenshots reviewed blind.
3. Short walkthrough video per option.
4. Lighting variant captures and grayscale review.
5. Material lookdev captures under controlled lighting.
6. State-feedback lab with muted/desaturated readability test.
7. Blind Founder comparison using `OPTION_A/B/C` packet.
8. Target camera/player metrics/frame budget definition.
9. Accessibility checks: colorblind, contrast, motion/flicker, audio cue fallback.
10. Representative performance proof after real assets, fog, particles, glass/translucency, PCG/Nanite, and final materials.

## Interim recommendation

Proceed to blind specialist review and Founder packet. Do not select production direction yet.

If forced to prioritize next evidence, test readability first:

- Cinderworks: desaturated heat-channel route read.
- Hospice: first-room empathy + glass route affordance.
- Orchard: 1.5-second landmark retention and fog/ash occlusion.
