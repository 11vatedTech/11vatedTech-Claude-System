# Ashwake Environment Apprenticeship Phase 2 — Professional Research Pack

Date: 2026-08-21
Status: research evidence for apprenticeship phase. Principles only. No design imitation. No final environment selection.

Accepted hypotheses:

- `CINDERWORKS_ABBEY` — current leading hypothesis, not proven winner.
- `EMBER_HOSPICE` — accepted hypothesis.
- `FALLEN_SUN_ORCHARD` — accepted hypothesis.

## Decision use

This pack gates Phase 2 work: build comparable VISDEV, blockouts, lighting/material/state labs, captures, specialist review, and Founder review before production direction selection.

## A. Environment composition

### Principles

- Build one dominant read per view: large shape first, route second, story detail third.
- Use foreground / midground / background to make depth playable, not decorative.
- Player start must frame first landmark and first safe move.
- Landmarks require hierarchy: one primary per zone, secondary at decisions, tertiary at interaction range.
- Negative space protects focal target. Empty area is design tool, not missing art.
- Scale cues need human-sized anchors: doors, rails, beds, stairs, handles, carts, offerings, tools.
- Visual flow should point from spawn to first reliquary, then to second/third problem, without UI dependence.
- Grayscale focal read must pass before color scripting.

### Ashwake application

- Cinderworks: vertical furnace-cathedral axis, heat-channel flow, broken rose/apse landmark.
- Hospice: intimate ward axis, glass/partition sightlines, patient reliquary as close focal.
- Orchard: horizon-scale silhouettes, split sun tree / causeway / colossus route triangle.

### Failure tests

- 5-second thumbnail read: viewer identifies focal point, likely path, and original place function.
- Grayscale still: objective/path/hazard/state separate by value and shape.
- Landmark memory sketch after one run: player recalls start, primary landmark, climax, one route choice.

## B. Level design

### Principles

- Player start must show first safe floor, first traversable affordance, first landmark, and likely goal direction.
- Objective visibility must separate goal from path: show what player wants before exact route.
- Teach mechanic safely, repeat with variation, then add pressure.
- Escalation needs a readable ladder: orientation, teaching, test, pressure, release, climax, reward.
- Navigation needs landmark hierarchy and route rhythm, not breadcrumb dependence.
- Choice must be meaningful and recoverable: safe/long versus risky/short, high/low, exposed/covered.
- Recovery route is part of pacing. Failure should cost time/tension, not destroy comprehension.
- Climax must be established early, framed clearly, and paid off by visible environment transformation.

### Comparable blockout constants

- Same player movement speed and interaction metrics.
- Same objective count: three reliquaries.
- Same target run length band.
- Same no-HUD test.
- Same screenshot objective test.
- Same route roles: tutorial, rule confirmation, climax.
- Same capture set: spawn, landmark, first reliquary, safe, hostile, success, overview, walkthrough.

### Validation metrics

- First intentional move under 5 seconds.
- Player names plausible goal within 10 seconds.
- 70% viewer agreement on likely objective/path in 2-second still.
- Player reorients within 3 seconds after forced failure.
- Player resumes route within 20 seconds after recovery.

## C. Lighting

### Principles

- Motivated sources first; beauty second. Every light answers: what emits it, why still powered, what does it teach?
- Value hierarchy beats hue hierarchy. Route and state must survive grayscale.
- Key/fill/rim must be fiction-locked: aperture, furnace, lamp, diagnostic panel, eclipse, root, tube.
- Emissive materials can contribute to Lumen but tiny bright emissives can create noise/culling/view-dependence; use manual light support for gameplay readability.
- Lumen needs lighting-friendly geometry: separate walls/floors/ceilings, enough wall thickness, Surface Cache coverage, not only glowing planes.
- Atmosphere supports depth, but can destroy readability. Fog cannot hide next landmark beyond brief designed occlusion.
- Post process stabilizes look; it must not rescue bad lighting. Lock exposure/bloom before comparing variants.

### Six controlled variants

1. Emissive-dominant.
2. Motivated key/fill.
3. Environment-bounce dominant.
4. Volumetric atmosphere.
5. Readable low-key cinematic.
6. Altered value hierarchy.

### Lighting acceptance gates

- Next objective readable in 5 seconds from each route beat.
- Timing state readable in grayscale.
- No key gameplay object depends on tiny emissive mesh alone.
- No black void backgrounds on traversable route.
- No uniform orange wash.
- No bloom-only readability.
- Deep blacks preserve silhouettes and floor edges.
- Lumen debug views show no major coverage gaps on gameplay-critical surfaces.

## D. Environment art

### Principles

- Architectural grammar precedes props.
- Modular kits need snap discipline, human scale, silhouette variety, and rule-based interruption.
- Prop hierarchy: landmark/focal, functional anchors, story evidence, texture scatter.
- Environmental storytelling needs event chain: original purpose, catastrophe/change, current condition, human trace.
- Material variation follows cause: heat, touch, weather, ash, water, sacred/care/agriculture use.
- Repetition avoidance comes from rhythm, damage logic, material zones, silhouette breaks, and route occlusion; not noise everywhere.
- Representative vertical slice proves workflow before scaling.

### Material role model

- Primary structural material.
- Heat-touched material.
- Human-contact material.
- Sacred/care/agriculture material.
- Decay/intrusion material.
- Focal anomaly material.

### Prop removal test

Remove story/scatter props. Architecture must still read. Add story props back. Story sharpens, not changes completely.

## E. Gameplay readability

### Principles

- State communication cannot rely on color alone.
- Path communication uses value, silhouette, motion, sound, material response, route geometry, and practical light.
- Safe/dangerous areas need spatial affordance, not HUD label.
- Interaction affordance needs physical support: socket, cradle, clamp, pipe, root, chain, hand target.
- Player focus must remain on next decision, not equal-weight clutter.

### State-feedback experiment dimensions

- Lighting: intensity, source movement, shadow edge, value separation.
- Animation: pulse speed, breath rhythm, cable tremor, gauge movement, root convergence.
- Niagara/VFX: density, direction, shape, not particle spam.
- Material: emissive width, roughness response, soot/ash reveal, heat bloom.
- Audio: heartbeat, bell, duct cough, wind, pressure leak, flatline/reversal.
- Environment: route opens, panels move, roots glow, furnace breathes, ward stabilizes.
- UI: support only; never sole carrier.

## F. Unreal 5.8 workflow principles

### Blockout

- Build limited lab maps or command-line selectable blockouts. Keep greybox visibly greybox.
- Use primitive/static mesh blockouts for scale, collision, sightlines, and capture first.
- Use modular proxy kit pieces: wall, floor, stair, arch, cliff slab, vista blocker, route marker.
- Do not use polished lighting to hide weak geometry.

### Lumen

- Use dynamic GI/reflections for lighting labs.
- Test emissive-only versus emissive plus manual lights.
- Use Lumen debug views before visual claims.
- Compare Lumen quality/perf using `stat gpu`, Unreal Insights, and fixed cameras.

### Nanite

- Use for dense rocks/cliffs/ruins only when testing density/occlusion/VSM cost.
- Remember opaque/masked material constraints; morph targets unsupported.
- Nanite does not solve material/shader/translucency/instance cost.

### Landscape / PCG

- Landscape suits Orchard terrain labs; start small.
- PCG suits bounded rule tests for orchard rows, debris, ash scatter, vegetation ghosts.
- Expose density/slope/seed/exclusion parameters.
- Treat PCG as rule visualization until authored art pass exists.

### Niagara / audio

- Niagara should support readability: ash direction, embers, smoke, wind lines, hazard cues.
- Audio hooks should exist at blockout stage: bed, local emitter, transition, hazard cue, success/failure cue.
- Use deterministic triggers for validation.

### Capture automation

- Fixed resolution, cameras, exposure, bloom, anti-aliasing, render settings.
- Save PNGs/video and logs with command lines.
- Record hardware, resolution, Lumen/Nanite/PCG settings, asset counts.

## Required validation experiments

1. Five-second start read.
2. Two-second objective screenshot test.
3. No-HUD blind run.
4. Silent teaching run.
5. Choice legibility probe.
6. Recovery drill.
7. Beat pacing trace.
8. Landmark memory sketch.
9. Grayscale readability pass.
10. Lumen debug pass.
11. `profilegpu` / `stat unit` / Unreal Insights pass.
12. Muted and desaturated state-feedback review.

## Sources

- [Lumen Global Illumination and Reflections](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine)
- [Nanite Virtualized Geometry](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine)
- [Procedural Content Generation Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/procedural-content-generation-framework-in-unreal-engine)
- [World Partition](https://dev.epicgames.com/documentation/en-us/unreal-engine/world-partition-in-unreal-engine)
- [Movie Render Pipeline](https://dev.epicgames.com/documentation/en-us/unreal-engine/movie-render-pipeline-in-unreal-engine)
- [Landscape Outdoor Terrain](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-outdoor-terrain-in-unreal-engine)
- [Landscape Technical Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/landscape-technical-guide-in-unreal-engine)
- [Using Nanite with Landscapes](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-nanite-with-landscapes-in-unreal-engine)
- [Creating Visual Effects in Niagara](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-visual-effects-in-niagara-for-unreal-engine)
- [Audio in Unreal Engine 5](https://dev.epicgames.com/documentation/en-us/unreal-engine/audio-in-unreal-engine-5)
- [Material Inputs](https://dev.epicgames.com/documentation/en-us/unreal-engine/material-inputs-in-unreal-engine)
- [Instanced Materials](https://dev.epicgames.com/documentation/en-us/unreal-engine/instanced-materials-in-unreal-engine)
- [Unreal Insights](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-insights-in-unreal-engine)
- [Stat Commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine)
- [Testing and Optimizing Content](https://dev.epicgames.com/documentation/en-us/unreal-engine/testing-and-optimizing-your-content)
- [Valley of the Ancient Sample](https://dev.epicgames.com/documentation/en-us/unreal-engine/valley-of-the-ancient-sample-game-for-unreal-engine)
- [Electric Dreams Environment](https://dev.epicgames.com/documentation/en-us/unreal-engine/electric-dreams-environment-in-unreal-engine)
- [The Level Design Book: Blockout](https://book.leveldesignbook.com/process/blockout)
- [The Level Design Book: Layout](https://book.leveldesignbook.com/process/layout)
- [Dan Taylor — Ten Principles for Good Level Design](https://www.gamedeveloper.com/design/ten-principles-for-good-level-design)
- [Valve Developer Community — Loops](https://developer.valvesoftware.com/wiki/Loops_(level_design))
- [GDC Vault — What Happened Here? Environmental Storytelling](https://www.gdcvault.com/play/1012647/What-Happened-Here-Environmental-Storytelling)
- [GDC Vault — Skyrim's Modular Level Design](https://www.gdcvault.com/play/1014433/Skyrim-s-Modular-Level)
- [GDC Vault — Level Design in a Day](https://www.gdcvault.com/play/1022277/Level-Design-in-a-Day)
- [GDC Vault — The Vertical Slice Challenge](https://www.gdcvault.com/play/1022328/The-Vertical-Slice-Challenge)
- [GDC Vault — Making the World of Firewatch](https://www.gdcvault.com/play/1024140/Making-the-World-of-Firewatch)
- [80.lv — Modular Scene in UE4](https://80.lv/articles/001agt-004adk-005cg-modular-scene-in-ue4-blockout-vertex-paint-decals)
- [80.lv — Lighting Exercise in UE4](https://80.lv/articles/lighting-exercise-in-ue4-night-time-alleyway-with-neon-signs)
- [SIGGRAPH Advances 2022 — Lumen](https://advances.realtimerendering.com/s2022/index.html)
