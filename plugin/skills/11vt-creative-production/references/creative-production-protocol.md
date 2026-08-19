# Creative Production Protocol

## 1. Creative brief

Capture or infer:

- Product/job: what must experience accomplish?
- Audience: who is looking, playing, buying, trusting, or deciding?
- Emotional objective: what should they feel before, during, after?
- Brand posture: luxury, brutal, playful, sacred, technical, handmade, cinematic, editorial, toyetic, industrial, etc.
- World/materials: physical or cultural artifacts native to subject.
- Platform and context: device, environment, attention span, input modes.
- Constraints: stack, performance, accessibility, licensing, timeline, asset availability.
- Non-goals: aesthetics to avoid, references not to clone.

## 2. Reference-first reasoning

Use current research when visual field, tools, or licensing may have changed. Study direct and adjacent sources:

- games, cinematography, title sequences, architecture, museums/installations
- industrial design, fashion, editorial, packaging, physical materials
- data visualization, scientific imaging, film UI, musical instruments

Extract principles:

- composition moves
- lighting and material behavior
- color relationships
- typography behavior
- transition/camera behavior
- asset/detail density
- interaction pacing

Never clone brand layouts, IP, characters, or protected assets.

## 3. Design before components

Resolve before component implementation dominates:

- Concept: thesis in one sentence.
- Narrative: what user experiences.
- Composition: eye path and focal hierarchy.
- Visual hierarchy: dominant/supporting/background.
- Material language: what interface appears made from.
- Motion language: how world moves and why.
- Lighting: source, contrast, atmosphere.
- Depth: foreground/middle/background rules.
- Asset requirements: what cannot be represented with HTML/CSS primitives.
- Signature moments: 2–5 memorable interactions or views.

## 4. Medium selection

Choose medium by artifact need:

- CSS: layout, type, material framing, simple transitions.
- SVG: logos, crisp icons, masks, diagrams, scalable illustrations.
- Canvas: many particles/sprites, procedural 2D, pixel effects.
- WebGL/WebGPU/Three.js: camera, depth, shaders, instancing, real-time 3D.
- Raster: textured plates, painted art, photoreal inputs, complex surface detail.
- Video/audio: authored cinematic or rhythmic experiences.
- Generated assets: only with licensing/reproducibility documented.

Primitive geometry is scaffolding unless primitive language is explicit art direction.

## 5. Iteration loop

For significant visual work:

1. implement
2. build
3. launch actual app
4. inspect rendered output
5. inspect desktop
6. inspect mobile
7. inspect one intermediate viewport
8. interact with key states
9. inspect transitions/motion
10. compare against canon
11. run Visual QA critique
12. correct deficits
13. render again
14. repeat until acceptance gates pass

If result is weak after one iteration, escalate from component styling to layout, composition, visual grammar, art direction, asset strategy, or interaction model.

## 6. Completion language

- `Implemented`: code exists.
- `Built`: app compiles or artifact generated.
- `Functionally verified`: behavior checked.
- `Visually inspected`: rendered output inspected.
- `Production-ready visual`: canon-aligned, evidence recorded, Visual QA passed, no major scaffolding remains.

Never collapse these into one vague “done.”
