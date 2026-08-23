# 11vatedTech Claude System — Current State

**Last updated:** 2026-08-22
**State:** FOUNDATION GENESIS COMPLETE / CAPABILITY ASCENSION ACTIVE
**Active milestone:** Global Creative / Experience / Frontend Intelligence Ascension — Ashwake frozen; three professional institutes, maturity contract, resource packs, mission compiler, apprenticeship transfer gate, model role tasks, truth audit, and semantic repository expansion active

## System Status

| Component | Status | Evidence |
|---|---|---|
| Global 11vatedTech Foundry | Operational and globally synced | `scripts/install/sync_to_claude.py`, canonical regression |
| 9Router | Chat/core healthy; root registry degraded | `artifacts/unreal/health/9router-degraded-diagnostics.json` |
| Unreal Engine | 5.8.0 installed; Editor/Cmd/UAT/Build detected | `artifacts/unreal/health/ue-5.8-health-toolchain.json` |
| Windows C++ game toolchain | Proven | MSVC 14.44, MSBuild, linker, Windows SDK; `foundry-compile-evidence.json` |
| .NET Framework 4.8 SDK | Installed | `C:\Program Files (x86)\Windows Kits\NETFXSDK\4.8\` (Include/um, Lib/um verified; detection scripts updated) |
| Unreal Editor target | Compiles PASS | `FoundryCalibrationEditor` target builds successfully with MSVC 14.44 + .NET 4.8 SDK |
| Capability Ontology | 92 scoped capabilities | `config/capability-ontology.json`, `ontology_check.py` |
| Maturity baseline | L0:1 / L1:1 / L2:17 / L3:42 / L4:26 / L5:5 | `scripts/validate/ontology_check.py` |
| Capability truth audit | 24 theoretical / 6 scripted / 45 operational / 10 verified / 0 production-proven | `config/capability-truth-audit.json` |
| Global gap register | Top 10 ranked; first three selected for execution | `config/capability-gap-register.json` |
| Ashwake | Frozen as `CALIBRATION_FIXTURE_001` | `artifacts/flagship/ASHWAKE-FREEZE.md` |

## Current course correction

Ashwake served as a calibration instrument. Its technically valid but human-visible creative failures are retained in `artifacts/flagship/ASHWAKE-LESSON-EXTRACTION.json` and the Unreal human-playtest evidence. No further environment selection, review-board polish, level expansion, or product development is active. Future work must improve reusable global Foundry capability or run a bounded regression.

The current global capability delta is demonstrated by:

- `scripts/validate/capability_truth_audit.py`: explicit actual-state classification rather than ontology/documentation claims.
- `scripts/validate/mission_value_gate.py`: rejects unbounded frozen-fixture work with `STOP_AND_REPLAN`.
- `scripts/validate/visual_evidence_evaluator.py`: rejects known black-void/test-chamber/state-color-only/debug-HUD patterns while preserving independent-review requirements.
- `scripts/validate/model_router.py`: selects roles from measured Golden Task evidence; no universal model claim.
- `scripts/repo/multilang_semantic_intelligence.py`: Python, TypeScript/JavaScript, and C++ lexical index baseline; no LSP/type-resolution claim.
- `config/maturity-and-knowledge-contract.json`: independent maturity axes and evergreen versus just-in-time knowledge policy.
- `config/resource-packs/`: source-grounded frontend/UI/UX, art direction/lookdev, and semantic engineering curricula.
- `scripts/ascension/mission_compiler.py`: outcome intent expands into disciplines, tools, evidence, model roles, and stop conditions.
- `scripts/validate/creative_micro_lab.py`: bounded practice requires causal critique, repair, independent review, and unseen transfer.
- `scripts/validate/frontend_quality_contract.py`: frontend evidence contract rejects score-only quality claims.

## Unreal vertical slice: Ashwake — The Last Reliquary

Three original concepts were scored; **Ashwake / Emberveil** was selected for
player fantasy, mechanical depth, visual identity, coverage, and calibration
value. The traceable design brief and 18-node / 21-edge production graph are
in `artifacts/unreal/calibration/`.

Proven:

- Original game-design trace with player fantasy, verbs, loop, state,
  attunement mechanic, challenge, accessibility, and implementation links.
- Native C++ game target compiles successfully with MSVC 14.44.
- Real Unreal map authoring, Emberveil GLB import, Niagara calibration, audio
  import, and native DataValidation on the authoring project.
- Nine Unreal Foundry regression tests pass, including runtime observation,
  native test discovery, and package prerequisite diagnostics.
- The packaged game launches, mounts cooked IoStore/Pak content, loads
  `/Game/Calibration/Maps/EmberveilCalibration`, runs gameplay BeginPlay,
  spawns three reliquary actors, and cycles the state machine in both NullRHI
  smoke and real-RHI outside-editor playtest.
- .NET Framework 4.8 SDK installed at non-standard path
  `C:\Program Files (x86)\Windows Kits\NETFXSDK\4.8\`. Detection scripts
  (`build_pipeline.py`, `unreal_intelligence.py`) updated to scan both paths.
- **Editor target compiles successfully.** `FoundryCalibrationEditor` builds
  with MSVC 14.44 + .NET 4.8 SDK. SwarmInterface resolves.
- **FoundryCalibration game module loads at runtime.** `UnrealEditor-FoundryCalibration.dll`
  loaded successfully in `UnrealEditor-Cmd.exe` (verified 2026-08-20, log line 1204).
- **Native automation test execution PASS.** `FoundryCalibration.Gameplay.GameStateTransitions`
  discovered, executed, and returned `Result={Success}` (evidence:
  `artifacts/unreal/health/gamestate-transitions-evidence.json`).
- **Automation harness syntax resolved.** UE 5.8 requires `-ExecCmds="..."` (equals-sign
  form), not `-ExecCmds "..."` (space form). Space form silently ignores the command.
- **BuildCookRun package PASS.** Archive created at
  `artifacts/unreal/calibration/Packaged/Ashwake`; verification finds two executables
  and 60 staged files.
- **LOOSE_CONTENT_ASSET_REGISTRY_FAILURE resolved naturally by cook/stage.** Cooked runtime
  mounts `global.utoc` and `FoundryCalibration-Windows.pak`; no `FBufferReaderBase::Serialize`
  loose-content crash remains.
- **Runtime map load PASS.** Packaged executable enters `EmberveilCalibration` and records
  `ASHWAKE_MAP_BEGINPLAY` / `ASHWAKE_GAMEPLAY_BEGIN` (evidence:
  `artifacts/unreal/health/packaged-runtime-map-load-evidence.json`).
- **Gameplay smoke PASS.** Three reliquary actors spawn and state cycle logs prove
  Reading → SafeWindow → Hostile → Reading behavior (evidence:
  `artifacts/unreal/health/packaged-gameplay-smoke-evidence.json`).
- **Gauntlet PASS.** `UE.BootTest` runs packaged Win64 Development client, loads map,
  loads premade AssetRegistry, exits with code 0 (evidence:
  `artifacts/unreal/health/gauntlet-boot-evidence.json`).
- **Unreal Insights trace PASS.** Packaged trace captured at
  `artifacts/unreal/health/traces/ashwake-packaged.utrace` (37.8MB).
- **Outside-editor playtest PASS.** Real D3D12 RHI launch, map BeginPlay, gameplay Begin,
  three reliquaries, state cycling, no fatal error (evidence:
  `artifacts/unreal/health/outside-editor-playtest-evidence.json`).
- **Packaged Ashwake content-fidelity contract PASS.** Final robust package
  `ashwake-vfxactive-robust-1787287516561` built, verified, launched through success and
  failure gameplay scenarios, and passed AUTHORING / EDITOR / COOK / STAGE_ARCHIVE / RUNTIME
  for all 9 required assets with 0 failures and 0 runtime reference warnings (evidence:
  `artifacts/unreal/health/ashwake-vfxactive-robust-1787287516561-package.json`,
  `artifacts/unreal/health/ashwake-vfxactive-robust-1787287516561-package-verify.json`,
  `artifacts/unreal/health/ashwake-vfxactive-robust-1787287516561-gameplay-scenario.json`,
  `artifacts/unreal/health/ashwake-vfxactive-robust-1787287516561-content-contract-cooked.json`).
- **Runtime audiovisual proof PASS.** Packaged D3D12 runtime emits structured input causality,
  success/failure/restart, `AUDIO_PLAYING`, `ANIMATION_PLAYING`, and `VFX_STATE` markers.
  `NS_Emberveil_Attune` is cook-safe and reports `active=true` with state payloads
  (`spawn_rate`, `energy`, `color`) in success and failure runs.
- **Reusable Unreal Foundry reliability hardening PASS.** Regression coverage now includes
  Windows path resolution, multi-stage content contract good/bad cases, exit classification,
  successful-exit precedence over transient tool noise, and bad-runtime rejection (evidence:
  `scripts/validate/unreal_foundry_reliability_tests.py`).

Known open content gaps:

- None for the packaged Ashwake content-fidelity contract covered by
  `artifacts/unreal/calibration/ashwake-required-assets.json`.

Not proven:

- Visual/game-design review from a human playtest session.

## Ashwake Environment Apprenticeship Phase 2

Status: specialist synthesis complete; no final production direction selected.

Current designations:

- `CINDERWORKS_ABBEY`: CURRENT LEADING HYPOTHESIS, not proven winner.
- `EMBER_HOSPICE`: accepted hypothesis.
- `FALLEN_SUN_ORCHARD`: accepted hypothesis.

Evidence preserved:

- Professional research, VISDEV packs, blind packets, and interim memo in `docs/evidence/ashwake/environment-apprenticeship-phase-2/`.
- UE 5.8 packaged blockout/lab evidence in `artifacts/unreal/health/ashwake-environment-apprenticeship-phase2-evidence.json`.
- Capture automation in `scripts/unreal/ashwake_environment_phase2_capture.py`.
- Specialist synthesis in `docs/evidence/ashwake/environment-apprenticeship-phase-2/specialist-review-synthesis.md`.

Specialist synthesis:

- Immediate vertical-slice risk reducer: `CINDERWORKS_ABBEY`.
- Emotional/storytelling challenger: `EMBER_HOSPICE`.
- Long-term world-image challenger: `FALLEN_SUN_ORCHARD`.
- No averaged winner; final art selection remains blocked.

Still required before selection:

- Founder blind review (package ready — see Phase 3 below).
- Human no-HUD navigation comprehension (protocol prepared; human session pending).

## Ashwake Environment Apprenticeship Phase 3

Status: blind evidence package COMPLETE (`READY_FOR_FOUNDER_REVIEW`); **no final production direction selected**.

Blind alias rule:

- Concepts frozen behind `OPTION_A` / `OPTION_B` / `OPTION_C`.
- Founder-facing records contain aliases only; identity map is private at
  `docs/evidence/ashwake/environment-apprenticeship-phase-3/private/blind-alias-map.json`
  and stays confidential until review completes.

Evidence produced (all 33/33 runs PASS):

- Equivalent blockout captures across 11 review states per option
  (SPAWN → FIRST_LANDMARK → … → ENVIRONMENT_OVERVIEW), all No-HUD
  (`artifacts/unreal/health/ashwake-environment-apprenticeship-phase3-evidence.json`,
  founder index: `docs/evidence/ashwake/environment-apprenticeship-phase-3/founder-package/evidence-index.json`).
- Silent walkthrough MP4 per option plus grayscale/desaturated captures of
  SPAWN / SAFE_WINDOW / HOSTILE / ONE_COAL_RESTORED with value-structure metrics
  (mean/stdev, black crush, midtone occupancy, highlight clipping, center/border separation).
- Material lookdev: 5 materials × 3 lights × 3 options, all readability gates PASS,
  contact sheets, plus 5 minimal audio state prototypes per option
  (`founder-package/material-audio-index.json`).
- Representative performance proxy per option: fog/particle/glass/emissive-band/
  geometry/Lumen/audio proxies, Unreal Insights `.utrace`, UAT game-thread timer export,
  and CsvProfiler frame-time stats (median ≈ 37–43 ms in editor mode). All three classify
  `EASY TO OPTIMIZE`; proxy exposes architectural risk only, not final optimization proof
  (`founder-package/performance-proxy-index.json`).
- Blind review entry point: `founder-package/review-guide.md` (14 questions + viewing protocol).

Runtime capture notes (non-obvious constraints):

- Smart App Control on this machine blocks newly packaged unsigned exes. Runtime evidence
  therefore runs through Epic-signed `UnrealEditor.exe` in `-game` mode with the freshly
  built project DLL; `AshwakeVisualProofExit` now delays exit ~1.2 s so the queued PNG flushes.
- Editor-mode boots log a bystander `Started CrashReportClient` line; the crash classifier
  was narrowed so this does not false-fail runs (`scripts/unreal/runtime_evidence.py`).

Still required before selection:

- Founder responses to the 14 questions in the review guide.
- Human no-HUD comprehension session (metrics list prepared in evidence index).
- Post-review only: experience-capital update, golden tasks, final selection gate.

## Validation commands

```bash
python scripts/validate/system_regression.py
python scripts/validate/unreal_foundry_tests.py
python scripts/validate/unreal_foundry_reliability_tests.py
python scripts/unreal/unreal_intelligence.py health
python scripts/unreal/build_pipeline.py package artifacts/unreal/calibration/FoundryCalibration.uproject --archive artifacts/unreal/calibration/Packaged/Ashwake
python scripts/unreal/ashwake_gameplay_scenario.py artifacts/unreal/calibration/Packaged/Ashwake/Windows/FoundryCalibration/Binaries/Win64/FoundryCalibration.exe --out artifacts/unreal/health/ashwake-gameplay-scenario.json
python scripts/unreal/content_contract_validator.py artifacts/unreal/calibration/ashwake-required-assets.json --project artifacts/unreal/calibration/FoundryCalibration.uproject --editor-load --cooked --archive-root artifacts/unreal/calibration/Packaged/Ashwake/Windows --stage-root artifacts/unreal/calibration/Saved/StagedBuilds_Ashwake --runtime-log artifacts/unreal/health/ashwake-gameplay-scenario-runs/<success-run>/complete-runtime.log --runtime-log artifacts/unreal/health/ashwake-gameplay-scenario-runs/<failure-run>/complete-runtime.log --quality-evidence artifacts/unreal/health/ashwake-gameplay-scenario.json --quality-evidence <package-verify.json> --quality-evidence <package.json> --out artifacts/unreal/health/ashwake-content-contract-cooked.json
```

The canonical regression is green while explicitly reporting:
`FOUNDRY CORE: PASS; MODEL REGISTRY: DEGRADED`.
