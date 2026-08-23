# Emberveil Calibration Failure Report

Date: 2026-08-19
State: **FOUNDATION GENESIS COMPLETE / CAPABILITY ASCENSION ACTIVE**
Artifact quality: **COHERENT**, not POLISHED, PRODUCTION, or SIGNATURE.

Emberveil is a calibration instrument. Its purpose is to expose where the
Foundry substitutes structural validity for perceptual and artistic quality.

## Evidence produced

- Canonical persistent structured batch: 46 operations, one Blender process.
- Valid GLB: 342KB, 13 meshes, 18 nodes, 4 materials, 4 authored animation clips.
- Mechanical control rig: 3-bone vessel/core/filigree hierarchy; controls are not
  yet skinned to deforming geometry.
- Materials: glass transmission/subsurface, noisy emissive core, brass procedural
  colour/roughness/bump variation, basalt procedural variation.
- Motivated light rig: core point key, warm area key/bounce, cool separation,
  atmospheric top light, documented in the batch report.
- Environment: authored basalt shrine, ash ring, radial pillars.
- Encoded evidence: 24-frame turntable and 72-frame cinematic sequence.
- Runtime: canonical GLB loads in Three.js; all 4 clips play concurrently;
  420 ambient embers and click ignition are observable.
- Runtime observation: 1280x800 SwiftShader, hero loaded, 4 active animations,
  zero console messages, zero failed requests.
- Perceptual diagnostic: selected beauty/turntable/cinematic/runtime frames pass
  the current diagnostic thresholds. This is not an artistic approval.
- Independent review: separate Gemini-family model through 9Router, using a
  runtime screenshot and factual evidence bundle, verdict COHERENT, confidence
  0.95.

## What the Foundry did well

1. Preserved provenance and separated the project artifact from reusable tools.
2. Rebuilt the artifact through registered structured operations rather than a
   permanent arbitrary-Python fallback.
3. Found and fixed the Blender session-chain corruption by adding a persistent
   batch boundary.
4. Detected the real v1/v2 material-loss regression with the new GLB variant gate.
5. Produced a complete material-bearing animated GLB rather than selecting a
   render-only or animation-only variant.
6. Added runtime observation that proves loading, animation, particles, console,
   and network state instead of inferring them from source.
7. Kept infrastructure L5 claims separate from production-domain maturity.

## What still looked primitive or below professional standard

The independent review rejected promotion beyond COHERENT:

- Hero silhouette still reads as lathed geometry and can show faceting in the
  runtime still; smoothing was implemented, but the review shows that topology,
  normals, and visual inspection remain insufficiently governed.
- The surface remains procedurally simple: no authored texture images, decals,
  edge-wear masks, UV texture set, or validated detail scale.
- The shrine/environment gives grounding but remains a sparse ring-and-pillar
  presentation rather than a fully authored world with storytelling depth.
- Runtime VFX now has soft ember sprites and bloom, but lacks turbulence,
  motion stretch, heat distortion, volumetric interaction, and a fully authored
  ignition performance.
- The cool rim light is technically motivated and documented, but the reviewer
  still found its scene origin visually disconnected.
- The rig has purposeful controls but no skinning/deformation or constraint/range
  stress evidence.
- No audio layer was produced; this remains an explicit unresolved product gap.
- Typography is legible and intentional, but the runtime still needs a broader
  responsive/presentation benchmark than the single desktop observation.

## What required workarounds

- Blender state had to move from chained subprocesses to a single structured
  batch because background `open_mainfile` corrupted scene contents.
- The runtime required an import map for CDN modules and a corrected GLB hierarchy
  handling path; observation caught both failures.
- Headless Chrome does not provide a meaningful FPS measurement under SwiftShader;
  runtime animation state is valid, but GPU performance remains unverified.
- The perceptual subject mask is a bright-subject diagnostic, not a semantic
  segmentation or art-director judgment.

## What could not be verified

- Professional material realism across calibrated lighting environments.
- Deformation quality, because the mechanical rig is not skinned.
- Audio synchronization and mix quality, because audio is absent.
- GPU frame budget and mobile performance.
- A blinded multi-shot professional composition benchmark.
- Video-level acting, weight, anticipation, and ignition performance review by
  the independent model; review input included a still plus production facts.

## Systemic classification and repairs

| Finding | Root class | Foundry repair | Status |
|---|---|---|---|
| Hero unreadability was previously accepted | EVALUATION GAP | perceptual luminance, black-crush, separation, and occupancy diagnostics | implemented; needs calibration |
| v2 dropped materials while adding animation | PIPELINE GAP | GLB variant diff gate + mutation/failure evidence | implemented and tested |
| Animation QA existed without animation creation | CAPABILITY GAP | pulse/float/rotation structured production ops + runtime clip observability | implemented at L3 |
| Blender subprocess chaining destroyed meshes | TOOL GAP | persistent structured batch boundary | implemented and exercised |
| Surface variation was absent | TOOL GAP | structured noise emission and colour/roughness/bump variation ops | implemented; artistry remains open |
| Rigging was only a parent hierarchy | CAPABILITY GAP | mechanical armature operation and inspection | implemented at L3; skinning open |
| Repository intelligence was grep-level | CAPABILITY GAP | Python AST index, symbol/reference/architecture/impact/requirement queries and golden tasks | implemented at L3; language coverage open |
| Cohesion PASS was too shallow | QUALITY-MODEL GAP | canonical artifact evidence, runtime observation, perceptual QA, independent review record | improved; reviewer still rejects higher ladder stage |

## Current maturity decision

Do **not** elevate broad `3d-production`, `animation`, `vfx`, `cinematic`,
`visual-design`, or `cohesion` to L5. The new production capabilities remain
L2/L3/L4 according to the ontology. Existing L5 entries remain infrastructure
or governance capabilities only.

## Next frontier

The highest-leverage unresolved work is a real authored ignition performance
with skinned/articulated deformation, richer material/environment detail,
VFX motion QA, audio provenance and synchronization, and a blinded multi-shot
professional review benchmark. Semantic repository intelligence should expand
beyond Python AST to TypeScript/tree-sitter/LSP only when repository evidence
justifies the provider.

## Unreal Game Studio vertical-slice calibration

The next calibration selected **Ashwake — The Last Reliquary** from three
original concepts. This exposed a separate production boundary:

- **Easy/proven:** UE 5.8 discovery, MSVC 14.44 game-target compilation, map
  authoring, GLB import, Niagara asset creation, audio import, and native
  DataValidation on the authoring project.
- **Implemented but not proven in play:** Enhanced Input construction, C++
  player movement/camera, explicit run-state machine, timed relic challenge,
  HUD, authored map, and a native automation test source.
- **What failed:** the unstaged game target did not reach map/gameplay. Runtime
  observation recorded loose-content asset-registry/IO failure before map load.
  The Editor target and BuildCookRun then hit the concrete missing
  `Microsoft.Net.Component.4.8.SDK` / `NetFxSDK` prerequisite in
  `SwarmInterface`.
- **What was attempted:** the existing Visual Studio Build Tools installation
  was inspected; MSVC, linker, MSBuild, and Windows SDK were confirmed. The
  exact component-only modification command was offered through elevation and
  denied, so no installation or package success is claimed.
- **What cannot yet be verified:** native test execution, input/game-feel
  behavior, AI/system challenge in play, Gauntlet, Insights analysis, runtime
  visual QA, independent game-design review, packaged build, and outside-Editor
  play.

This is classified as a **TOOL GAP + PIPELINE GAP + EVALUATION GAP**, not as a
playable-game success. The Foundry now has bounded runtime observation and
package preflight so this failure is repeatable, visible, and regression-tested.
The next repair is to restore the existing Build Tools .NET SDK prerequisite,
then rerun Editor-target compilation, cook/package, native automation, and
actual playtest before any Unreal maturity promotion.

## Continuation verification — 2026-08-19

The requested post-install verification did **not** confirm that the SDK is
installed on this machine. `vswhere -requires Microsoft.Net.Component.4.8.SDK`
returned no instance, the NETFXSDK registry keys were absent, no `NETFXSDKDir`
payload or SDK files were found, and `UnrealBuildTool` still failed Editor-target
compilation with the same `SwarmInterface`/`NetFxSDK` error. Package preflight
therefore remains **BLOCKED**, not READY. The exact evidence is stored in
`artifacts/unreal/health/vertical-slice-verification-20260819.json`.

The existing game target was rebuilt after correcting a real local tool defect:
`FoundryCalibration.Build.cs` was missing the `Niagara` dependency, causing
`NiagaraComponent.h` and generated Niagara reflection symbols to fail. The
`FoundryCalibration` Development game target now compiles successfully.

The native test `FoundryCalibration.Gameplay.GameStateTransitions` was executed
through the new bounded Unreal automation operation, not merely discovered. It
returned `BLOCKED_MODULE`: the Editor command line could not load the
`FoundryCalibration` module because the Editor target remains uncompiled. This is
not a test pass.

The separate loose-content failure was reproduced with the rebuilt game target
under `-nullrhi`. It is an Unreal premade Asset Registry read failure followed by
`ReaderPos + Num <= ReaderSize` on `IOThreadPool #2`, before map load. Disabling
asset-registry cache reads did not bypass that premade registry requirement. A
separate Editor -game run against the authoring project loaded
`/Game/Calibration/Maps/EmberveilCalibration` cleanly, proving the map/content
path is viable but not proving gameplay because that project has no C++ game
module. The reusable runtime observer now classifies these states separately:
`LOOSE_CONTENT_ASSET_REGISTRY_FAILURE`, `MAP_LOADED_NO_GAMEPLAY`, and
`GAMEPLAY_OBSERVED`, and records the correct Editor/cooked-package diagnosis.

The Foundry still cannot claim native-test execution, player-controlled runtime,
scenario play, Gauntlet, Insights analysis, packaged build, or outside-Editor
play. The next action remains genuine SDK discoverability verification followed
by Editor compilation and BuildCookRun; no engine or prerequisite bypass was
used.
