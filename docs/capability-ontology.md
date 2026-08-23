# Foundry Capability Ontology

The ontology is the machine-readable inventory of what the 11vatedTech Foundry
can actually do, who provides it, and how mature it is. It is the contract
behind "evidence, not claims": every capability must name a resolvable provider
and an evidence pointer.

- Machine-readable source of truth: `config/capability-ontology.json`
- Validator: `scripts/validate/ontology_check.py` (wired into the system
  regression gate)
- Scored baseline: `docs/maturity-baseline.md`

## Structure

```
domains[]                       # 16 capability domains
  └ capabilities[]              # 78 capabilities
      ├ providers[]             # kind: skill | agent | script | template |
      │                         #       tool | tool-degraded | 9router-endpoint
      ├ maturity                # L0..L5
      └ evidence[]              # file pointers that substantiate the claim
```

Provider kinds resolve as follows:

- `skill`  -> `plugin/skills/<name>/SKILL.md`
- `agent`  -> `plugin/agents/<name>.md`
- `script` / `template` -> path under the repo root
- `tool`   -> resolved at runtime via `vtmedia.common.resolve_tool`
  (PATH + known `Program Files` installs); a small allowlist of tools that are
  documented degraded (whisper/piper/comfyui/krita/gimp/kdenlive/audacity) do
  not fail the check
- `tool-degraded` -> present but intentionally degraded-by-design
- `9router-endpoint` -> answered live by the 9Router gateway

## L0–L5 maturity scale

| Level | Meaning |
|---|---|
| L0 | **UNAVAILABLE** — no provider or tooling present |
| L1 | **DETECTED** — provider/tooling present but unverified |
| L2 | **OPERATIONAL** — pipeline executes end-to-end on real artifacts |
| L3 | **VERIFIED** — automated tests exercise the pipeline |
| L4 | **INTEGRATED** — regression-gated and/or cross-capability evidence/provenance |
| L5 | **GOVERNED** — release-gated, versioned, rollback-capable, evaluation-covered |

A capability may only claim a level it can substantiate. Claims are checked by
`ontology_check.py` (provider resolution + evidence existence) and by the
regression gate.

## Domains

1. `intelligence-routing` — founder-intent routing, model routing
2. `research-evidence` — web research, evidence ledger
3. `architecture-engineering` — ADRs, production engineering, game development
4. `creative-production` — creative/art/experience/motion/technical/design direction
5. `visual-production-tooling` — raster, vector, video, audio, STT, TTS, image generation
6. `three-d-pipeline` — Blender bridge, structured scene authoring, GLB export
7. `asset-intelligence` — asset direction, provenance
8. `visual-qa` — pixel diff, PSNR, visual QA direction, independent review
9. `ascension-production-intelligence` — perceptual/composition QA, lighting, materials, environment, rigging, animation, VFX, cinematic, variant regression, cohesion
10. `repo-runtime-intelligence` — repository audit, status, environment doctor, GPU
11. `semantic-repository-intelligence` — AST index and repository golden tasks
12. `deployment-governance` — global sync, global validation, rollback
13. `evaluation-lab` — routing, behavioral, regression, bootstrap, manifest, model benchmark
14. `product-lifecycle` — bootstrap, lifecycle, release engineering, hooks
15. `foundry-maintenance` — skill foundry, documentation canon, core OS
16. `unreal-game-studio` — game-design traceability, C++ compile, gameplay architecture graphing, installed-engine health, static project intelligence, governed Blender handoff, Editor-Python GLB import, pre-import contract validation, bounded command-line surface, runtime-failure observation, native-test discovery, and package preflight

The Unreal entries remain intentionally narrow. Runtime observation and package
preflight do not imply playable game quality; source-level native-test discovery
does not imply test execution. Blueprint graph comprehension, game-feel quality,
Gauntlet, profiling analysis, and packaged-build readiness require their own
executable evidence.
