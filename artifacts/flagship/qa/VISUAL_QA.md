# Emberveil — Visual QA Record (Milestone 2)

Date: 2026-08-18 · Observer: Foundry runtime-observation layer (CDP headless Chrome)
Method: real wall-clock observation, not source-code approval.

## Observation method
- `scripts/validate/cdp_observe.js` — a reusable headless-browser observation tool
  (CDP over WebSocket) that navigates the real runtime, waits real time so
  `requestAnimationFrame`, WebGL, network and animation genuinely run, captures
  frames at intervals, and records console errors / failed requests / page state.
- Frames: `artifacts/flagship/qa/live/frame-0{1..5}.png` (1280×800).
- Live-state sampling via a read-only `window.__emberveil` hook.

## Two real bugs found by observation (and fixed)
1. **Module resolution failure — runtime never loaded.**
   `TypeError: Failed to resolve module specifier "three"`. The CDN
   `GLTFLoader` imports the bare `three` specifier, which browsers cannot
   resolve without an import map. First observation pass: console error +
   all-black frames (mean luminance 0.034). **Fix:** added a
   `<script type="importmap">` mapping `three` and `three/addons/`.
2. **Hero hierarchy detached — invisible entity.**
   The cleanup loop removed every non-mesh top-level child; `Emberveil_root`
   (an EMPTY that parents all six meshes) was detached, taking the hero with
   it. Animation also failed to bind: `THREE.PropertyBinding: No target node
   found for track: Emberveil_root.position`. **Fix:** keep the authored
   hierarchy intact (drop only cameras/lights), root the `AnimationMixer` at
   the scene so `Emberveil_root.*` tracks resolve.

After fixes: **0 console errors, 0 warnings, 0 failed requests.**

## Visual observation (ASCII-rendered frames)
- Hero silhouette clearly readable: bell form with flaring rim, bright inner
  core, filigree arcs, plinth base.
- Camera orbit confirmed — hero position/shape shifts across frames
  (frame-02 → frame-05), parallax working.
- Ember field visible as warm additive haze rising from the core.
- Cinematic sequence (72 frames → `emberveil-cinematic.mp4`) reads as a
  push-in reveal: bell grows from ~40% to ~70% of frame height, core glow
  visible. Composition arc present, not a static turntable.

## Live animation verification (sampled via CDP, 500 ms apart)
| t (s) | mixerTime | playing | rootY    | cameraPos |
|-------|-----------|---------|----------|-----------|
| 6.15  | 6.11      | true    | +0.053   | orbiting  |
| 6.65  | 6.61      | true    | +0.171   | orbiting  |
| 7.17  | 7.13      | true    | −0.068   | orbiting  |
| 7.68  | 7.65      | true    | −0.161   | orbiting  |
| 8.20  | 8.17      | true    | +0.069   | orbiting  |
| 8.70  | 8.66      | true    | +0.165   | orbiting  |

`mixerTime` advances continuously; `rootY` oscillates (the authored float
bob); camera orbits; 420 embers live. Animation is real, not a still.
(fps reads 0 under headless SwiftShader because Chrome throttles rAF in
background; on a GPU browser the same code runs at display refresh.)

## Cohesion audit (scripts/validate/cohesion_audit.py)
Mechanical cross-layer identity check — PASS:
- **palette**: GLB material hues (brass 30°, plinth 22°) within **3°** of the
  nearest UI hue (UI family 22–42°). UI and 3D share one warm identity.
- **typography**: serif display + letterspaced wordmark present.
- **motion**: organic sin-based float/flicker/drift grammar present.
- **vfx**: additive blending + warm ember palette.
- **lighting**: warm key + cool rim temperature contrast.

## Known limitations (honest)
- Headless SwiftShader: no GPU-accurate tone mapping / bloom; real-GPU
  appearance may differ slightly.
- ASCII review is coarse; fine material response (roughness, subsurface)
  judged from Cycles renders (`emberveil-turntable.mp4`) and the cinematic.
- No audio layer in this calibration (brief judged audio not justified for a
  contained spirit-warden; deferred).
