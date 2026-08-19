# Quality Ladder

Artifact maturity is explicit and gated. Do not call a functional artifact
production quality; do not call a visual mockup a finished frontend; do not
call one successful run validation.

Machine-readable quality models: `config/quality-models.json`.

## Stages

| Stage | Meaning | Required to enter | Not yet |
|---|---|---|---|
| **BLOCKOUT** | Proves layout/scale/flow | Structure exists; placeholders allowed | No quality claims |
| **FUNCTIONAL** | Works end-to-end | Every user/player path executes; no blocking placeholder | Not "polished" or "production" |
| **COHERENT** | Reads as one product | Shared visual canon; consistent hierarchy, typography, motion grammar | Detail-level polish |
| **POLISHED** | Edges and states handled | All states/transitions reviewed; no visible rough edges in observed runs | Performance/provenance evidence |
| **PRODUCTION** | Release-grade | Performance budgets met; provenance/license recorded (Asset Vault); regression + QA evidence recorded | — |
| **SIGNATURE** | Recognizable product-specific identity | Anti-generic critique passed; identity visible without the logo; flagship-caliber execution | — |

## Transition gates

- **BLOCKOUT → FUNCTIONAL**: end-to-end run succeeds; blocking stubs replaced.
- **FUNCTIONAL → COHERENT**: cohesion audit passes (UI + assets + typography +
  motion + VFX + lighting + camera + audio feel like the same product).
- **COHERENT → POLISHED**: observed-runs review finds no rough edges; motion
  and states consistent.
- **POLISHED → PRODUCTION**: performance verified; every external asset has a
  vault record with known license; evidence ledger updated; regression green.
- **PRODUCTION → SIGNATURE**: independent review certifies recognizable
  product-specific identity; visual QA director + independent reviewer sign off.

## Evaluation discipline

- Mechanical checks are automated where possible (pixel diff, PSNR, loop
  continuity, foot-slide velocity, loudness, frame budgets).
- Artistic checks use rendered/video evidence and independent review — never
  screenshots alone for motion, and never memory alone for visuals.
- A capability's maturity (L0–L5) and an artifact's ladder stage are separate
  states; both are recorded and neither is inferred from the other.
