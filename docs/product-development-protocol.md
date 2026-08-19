# Product Development Protocol

Lifecycle: DISCOVER → RESEARCH → CHALLENGE → SPECIFY → ARCHITECT → PLAN → IMPLEMENT → INTEGRATE → VERIFY → REVIEW → HARDEN → RELEASE → CANONIZE.

Use work contracts for substantial work. Use evidence ledger for completion claims. Use independent review for high-risk or release-bound changes. Update canon only with durable verified facts.

## Creative-production overlays

When product success depends on visual identity, interaction feel, motion, assets, 3D/rendering, audiovisual polish, or high-fidelity presentation, add creative gates to the lifecycle.

### DISCOVER / RESEARCH

- Define audience, emotional objective, brand posture, usage context, and visual non-goals.
- Research direct and adjacent references when visual vocabulary or tooling matters.
- Extract principles; do not clone brands, layouts, IP, or assets.

### CHALLENGE / SPECIFY

- Challenge weak concepts before implementation.
- Establish concept, narrative, eye path, hierarchy, material language, lighting/depth, motion language, asset needs, and 2–5 signature moments.
- Decide whether `docs/design/` visual canon is required.

### ARCHITECT / PLAN

- Select medium deliberately: CSS, SVG, Canvas, WebGL/WebGPU, Three.js, raster/vector, video/audio, generated assets, or procedural systems.
- Identify asset pipeline, licensing/provenance, performance budget, accessibility constraints, and reduced-motion behavior.

### IMPLEMENT / INTEGRATE

- Build real states, not screenshot-only facades.
- Treat placeholder primitives, concept art, and low-detail assets as scaffolding unless art direction explicitly says otherwise.

### VERIFY / REVIEW

- Run actual application when previewable.
- Inspect desktop, mobile, and intermediate/tablet when layout matters.
- Interact with important states and transitions.
- Check console/network/server health and accessibility tree.
- Compare against visual canon.
- Run Visual QA critique and fix issues before visual completion claim.

### RELEASE / CANONIZE

- Record visual evidence in `docs/evidence/`.
- Update `docs/design/` canon with verified, durable visual rules.
- Disclose remaining limitations: missing assets, untested viewports, model/tooling constraints, scaffolding.
