# Flagship Calibration — Creative Brief

Project: **EMBERVEIL** — an interactive presentation of an original living
spirit entity. A calibration instrument for the Foundry: it must force
creative direction, asset planning, 3D production, materials, rigging,
animation, VFX, lighting, camera, motion, real-time presentation, visual QA,
provenance, and independent criticism to operate together on one artifact.

## Creative thesis

**Concept.** Emberveil is a warden-spirit of dying fires: a floating glass
bell that contains a living ember core. It gathers the last warmth of
neglected hearths and carries it somewhere it will be seen. It is not a ghost
and not a machine — an artificial organism of glass, brass, and held heat.

**Emotional intent.** Quiet devotion with a hidden flare. The viewer should
feel warmth, patience, and a moment of startling ignition.

**Visual thesis.** *Contained fire.* Warmth is never loose — it lives inside
a disciplined glass vessel and only escapes as deliberate sparks. Discipline
of form + volatility of light.

**Shape language.** Primary silhouette: a **capsule/bell** (the vessel) with a
**flame** (the core) and a **trailing comet line** (the sparks). Secondary
shapes: brass filigree arcs that read as "wings/guard" folded around the bell.
Circles (vessel), flame teardrops (core), thin arcs (filigree). No hard
squares.

**Material language.** Warm frosted glass (subsurface scatter, high
transmission, low roughness on the rim), a hot ember core (blackbody emission,
noise-driven), aged brass filigree (metallic, low roughness, dark patina), and
a soft ground disc of polished basalt for the presentation.

**Color philosophy.** Warm end of the spectrum only: ember orange (#ff7a1a),
core gold (#ffd166), glass amber (#ffb347), deep warm shadow (#1a0e05), and a
single cold accent — a faint blue rim light (#67d9ff at low intensity) to make
the warmth read as warm. 70/30 rule: 70% warm dark, 30% ember light.

**Lighting philosophy.** Motivated by the entity itself: the ember core is the
key light. A soft warm key from the core, a cool low-intensity rim from behind
to separate silhouette, and a gentle fill from the ground bounce.

**Motion language.** Slow, held, weightless-but-deliberate. The vessel floats
with a long low-frequency bob; the core flickers with fast high-frequency
noise; sparks drift and die on curves. Signature action: **the Ignition** — a
slow swell, a held breath, then a burst of sparks and a ring of light.

**VFX language.** Ember particles: small, warm, short-lived, gravity-affected,
with a soft additive glow. They are the only "escape" of the contained fire.

**Camera language.** One slow orbiting dolly that never rushes the entity;
framing keeps the full silhouette readable against negative space. A gentle
push-in during the Ignition.

**Interaction language.** The presentation responds to the viewer's presence:
camera parallax follows the pointer, and a hover/click triggers the Ignition.
Reduced-motion mode disables the parallax.

**Audio language (justified, minimal).** A low warm drone bed with a soft
ember crackle, swelling at the Ignition. Synthesized locally (ffmpeg) —
provenance recorded.

**Anti-references.** No default gradient backgrounds, no generic dashboard
cards, no stock icons, no default fonts, no primitive cube/sphere hero, no
unmodified downloaded assets, no "AI demo" sheen.

**Signature qualities.** (1) The bell-vessel silhouette. (2) The ember core
that flickers with real noise. (3) The deliberate spark trails. (4) The
Ignition moment. If the bell, the core, and the sparks were removed, the
artifact should be unrecognizable — that is the identity test.

## Concept exploration (3 materially different directions)

| | Direction A — **Emberveil** | Direction B — Verdant Clockwork | Direction C — Nebula Moth |
|---|---|---|---|
| Silhouette | bell + flame + comet trail | round + angular gear contrast | triangle + arc wings |
| Proportion | tall capsule, narrow base | squat, dense | wide, flat |
| Material | glass + brass + ember | brass + moss + oiled wood | crystal + star core |
| Movement | float + flicker + ignition burst | slow gear-turn idle, mechanical | wing-fold flash, drifting |
| Personality | guardian of dying fires | patient gardener | navigator of forgotten light |
| World relation | hearth, warmth, devotion | overgrown machinery | night sky, refraction |
| Presentation | floating on basalt, sparks | pedestal in moss, gear dust | dark void, refracting light |

**Selection: Direction A — Emberveil.** Strongest silhouette contrast (bell vs
flame vs trail), richest material narrative (glass/ember/brass), clearest
signature moment (Ignition), and the most achievable high-fidelity production
in this calibration window. B risks reading as generic steampunk; C risks
reading as generic "space butterfly". A's discipline-of-form + volatility-of-
light thesis is the most distinctive.

## Production approach

- **Hero asset**: authored procedurally in Blender via the structured op API
  (lathe the glass bell, radial-array the brass filigree, build the ember core
  from a distorted icosphere, animate float + flicker + ignition). Not a
  primitive; not a downloaded model.
- **Materials**: glass (SSS/transmission), ember (emissive + noise), brass
  (metallic PBR).
- **Runtime**: Three.js/WebGL loads the exported GLB, plays the animations via
  AnimationMixer, adds real-time ember particles, motivated lighting, camera
  parallax, and the Ignition interaction — with the visual identity carried by
  custom typography, color, and motion, not a dashboard.
- **Evidence**: turntable + cinematic renders, ffmpeg-encoded clips, animation
  QA metrics, vault provenance, cohesion audit, independent review.

## Quality ladder targets

- Hero asset: BLOCKOUT -> FUNCTIONAL -> COHERENT -> POLISHED -> PRODUCTION.
- Runtime presentation: BLOCKOUT -> FUNCTIONAL -> COHERENT -> POLISHED.
- SIGNATURE is the aspiration for the identity (bell + core + sparks + Ignition
  recognizable without the logo); it is claimed only if the cohesion audit and
  independent review support it.
