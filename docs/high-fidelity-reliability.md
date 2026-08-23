# High-Fidelity Reliability

High-fidelity reliability is the Foundry's ability to repeatedly recognize, produce, measure, review, reject, repair, and verify professional-quality human-facing work.

Engineering maturity does not transfer to creative maturity.

## Three independent axes

| Axis | Scale | Meaning |
|---|---|---|
| Engineering Maturity | E0–E5 | Does the system work, build, run, validate, and ship under governance? |
| Creative Maturity | C0–C6 | Does the product look, feel, communicate, and cohere at intended professional quality? |
| Fidelity Reliability | R0–R5 | Can the Foundry detect weak fidelity, repair it, protect it from regression, and confirm improvement with independent/human evidence? |

## Non-inheritance law

- Packaged build PASS does not imply game quality PASS.
- Valid GLB does not imply 3D art quality PASS.
- Niagara system active does not imply VFX quality PASS.
- Animation playing does not imply animation quality PASS.
- Audio playing does not imply audio quality PASS.
- Screenshot captured does not imply art direction PASS.
- Human can complete game does not imply game design PASS.

## Evidence classes

| Class | Answers |
|---|---|
| AUTOMATED | correctness, reproducibility, metrics, contracts |
| SPECIALIST_AI | discipline-specific critique from primary evidence |
| INDEPENDENT_AI | separate-context adversarial review; builder cannot self-certify |
| FOUNDER | authoritative ambition and human product verdict |
| HUMAN_PLAYTESTER | comprehension, feel, enjoyment, confusion, behavior |

## Ashwake baseline

Ashwake Human Playtest #1 proved the packaged game runs and the automated runtime/content pipeline is meaningful for engineering. It also proved that engineering success was ahead of creative maturity.

Baseline evidence:

- `artifacts/unreal/calibration/evidence/human-playtest-001/human-playtest-evidence.json`
- `artifacts/unreal/calibration/evidence/human-playtest-001/visual-failure-analysis.json`
- `artifacts/unreal/calibration/evidence/human-playtest-001/quality-debt-register.json`
- `artifacts/unreal/calibration/evidence/human-playtest-001/ashwake-quality-contract.json`

Current assessment:

- Engineering: E4
- Visual experience: C2
- Environment: C1
- Fidelity reliability: R2

## Blockers to POLISHED

- major black crush in player-critical regions
- test-environment presentation
- clipped primary subject
- generic/debug HUD
- missing or unreadable interaction-state language
- primitive VFX state language
- unreadable black-blob hero form
- broken or weightless animation
- missing/perceptually unverified audio
- no independent/human evidence for human-facing flagship build

## Gate

Run:

```bash
python scripts/validate/high_fidelity_reliability.py
```

System regression includes this gate. It fails if High-Fidelity Reliability model, Experience Foundry architecture, golden tasks, or Ashwake human baseline evidence are missing or overclaim creative maturity.
