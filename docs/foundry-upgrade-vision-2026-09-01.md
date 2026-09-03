# Foundry Upgrade Vision — 2026-09-01

Status: PRECURSOR / PARTIAL. Founder selected **Enforcement-first** lift sequence and **Pin live search** for web research, but later approved the broader **Ultimate Creative Ceiling + Resource Intelligence** architecture as authoritative. This document remains historical failure evidence and an enforcement backbone precursor, not the final Foundry architecture.

---

## 1. Why this upgrade exists

The TCG Learning Atlas first pass was rejected as primitive/generic. The rebuild (real cards, five mechanic felts, card reader, proven browser evidence) passed. The difference was **directive**, not capability: when told to follow the canon, the machine produced non-generic work. When left to the default path, it bypassed the entire creative-production pipeline and shipped exactly the anti-generic list.

A one-off directive is not reliability. The upgrade exists to make high-fidelity the **default, enforced outcome** — not the prompted outcome.

## 2. Research that grounded this

Four independent investigations ran in parallel on 2026-09-01:

| Track | Method | Sets |
|---|---|---|
| Foundry audit | Read every skill, agent, validator, hook, docs | Enforcement map, seams, evidence gaps |
| Creative ceiling | 2026 web/studio-grade interaction standards + tech | 5-layer craft threshold, technique map, 8 reference classes |
| Regression diagnosis | Git archaeology of TCG repo | 7 ranked root causes, all PROCESS |
| Toolchain inventory | Probed live machine (GPU, Python, Blender, ComfyUI, 9Router, model weights) | Tool matrix, priority unlock list |

Key cross-cutting findings:

- **The Foundry's enforced gates are all infrastructure gates** (hooks, asset-pipeline internals, ontology bookkeeping, routing regex, media toolchain). Creative quality is 100% advisory prose that a model can skip at every stage.
- **Every anti-generic check that could fail closed is unwired or self-declared.** `visual_evidence_evaluator.py`, `frontend_quality_contract.py`, `visual_evidence_check.py`, `independent_creative_review.py` run only inside the Foundry's own ascension fixtures against self-authored test data — never against a product's real rendered DOM/pixels.
- **The entrypoint routing ladder is prose with an escape hatch** ("only if visual work matters" — a model self-judgment) and no product ever records a routing decision.
- **Creative enforcement roles are not executable.** Art Director and Visual QA Director agents have no Write/Edit tools; Motion Director has no Bash. The two roles with authority to enforce quality cannot modify anything.
- **Agent memory is empty.** `.claude/agent-memory/` holds 7 directories, no content. Every product re-derives the anti-generic lesson from scratch.
- **Reference and type libraries don't exist.** `references/` are instruction prose; `DESIGN_SYSTEM.md` and `project-visual-canon-template.md` are blank scaffolds. No curated reference gallery, no type set.
- **Web research is a soft dependency that silently degrades.** This session's web-search gateway returned empty bodies, so the ceiling agent wrote from domain knowledge under the label "cited." This is a first-class process defect (see §7).
- **The rebuild's screenshot fallback was absent** — "visually inspected" was claimed on DOM/accessibility inspection, not pixels, because Browser pane was hidden and the record honestly named the gap. The discipline has no headless-screenshot fallback.
- **All 29 TCG cards' rights are still open** — production launch requires publisher permissions, API terms, caching, attribution (recorded, not resolved).

## 3. The ceiling — where capability should surpass

Jaw-dropping, elegant, meaningful work is a **craft threshold in five layers**, all of which must clear simultaneously. Holy pixels are layer 5, not the point.

### Layer 1 — One motion/easing system
Not a tween library. One canonical timing vocabulary: spring/easing curves, stagger orchestration, duration coherence, material-accurate physics feel. Every motion reads as "made by one hand."

### Layer 2 — Editorial composition that survives motion
Layout is the art: oversized type, grid tension, intentional white space, tuned tracking/leading. WebGL is layered on top as accent, never as the layout itself. Variable fonts; type is treated as artwork.

### Layer 3 — Light and depth that read as matter
Physically plausible lighting: soft shadows, AO, bloom tuned near zero, DOF, environment reflection. Restraint is the craft signal — vertex-count showboating reads as amateur to the exact audience the Foundry wants to impress.

### Layer 4 — Scroll/interaction as choreography, not trigger
Smooth-click-composition (Lenis-grade), ScrollTrigger timelines, camera dolly, image-sequence scrub, reveal grammar, sound-reactive moments. The page behaves like a film, not a feed.

### Layer 5 — Invisible DPR-3x + performance discipline
Crisp at 3x, 60fps, `prefers-reduced-motion` respected, lazy layers, no jank on throttled mobile. This is the "fine print" every savvy client and jury checks.

### Capability requirements to clear this ceiling
- WebGPU renderer with graceful WebGL2 fallback; Three.js WebGPURenderer, TSL node materials, compute passes. Runs fully client-side; no model downloads.
- GSAP + ScrollTrigger + Lenis; Motion One; custom spring lib.
- WAAPI / WebAudio / Tone.js procedural + reactive audio.
- Asset pipeline for web integration: upscaling (Real-ESRGAN), transparent extraction (rembg/SAM), palette/duotone grading (ImageMagick), image-sequence animation (ffmpeg), masking (Pillow/sharp), glTF/GLB embedding (Blender + gltf-transform + Draco), font licensing.
- **The foundry's actual edge**: generative + procedural + 3D + audio + integration. Already proven in part by THE OBSIDIAN SPIRE slice (9 media, one coherent world). The upgrade is to make this wired into *every* product build, not a one-off calibration.

### Reference classes to hit (targets, not clones)
1. Cinematic product microsite (scroll-camera choreography, product scrub, per-narrative-beat easing)
2. Type-led editorial system (oversized variable type, grid tension, whisper type, SVG grain)
3. Shader-art interactive poster (single dominant shader, pointer-reactive field, unique-frame-per-interaction)
4. Data-physical installation (data→matter, real-time particle systems, metamorphic transitions)
5. Game-adjacent narrative UI (camera, world-depth parallax, reactive HUD, progressive reveal)
6. Generative toolkit asset (meaning captured in a procedural generator that yields infinite coherent offspring)
7. Sound-reactive / synesthetic UI (visual system animates to a composed score)
8. Cinematic 3D narrative showcase (physically-plausible hero, layered parallax, tuned post)

The 2026 SOTD winners list is the hard-to-fake current evidence; re-verify with live search once the gateway is healthy (seam: search currently returns empty bodies).

## 4. Diagnosis — why first pass was generic

Seven ranked root causes, all **PROCESS** (the knowledge existed; nothing enforced the moment):

| # | Root cause | Type | Severity |
|---|---|---|---|
| 1 | Creative-production routing never invoked on first pass | Process | Critical |
| 2 | No hard concept gate before code | Process/Capability | Critical |
| 3 | Anti-generic gate is review-time only | Process | High |
| 4 | CLAUDE.md/product canon lack enforcement hooks | Process/Context | High |
| 5 | Asset protocol skipped; fictional assets used | Process | High |
| 6 | No git history / evidence trail | Process | Medium |
| 7 | Design-director non-negotiables not pre-build | Process | Medium |

Primary cause: first pass bypassed the entire creative-production pipeline and went straight to code. The definitions existed; the door was open.

## 5. The upgrade — Enforcement-first

Founder-selected: build the fidelity-enforcement backbone into the existing skills/agents so products fail closed on generic, with asset/type/reference/memory wired as canon. Implement in this phase order:

### Phase 1 — Routing stamp (fix #1, #4)
- `11vt-capability-entrypoint` records a machine-readable **routing decision** before any product repo file is created/modified.
- Creative-production candidates (visual identity, asset-heavy UI, anti-generic concern, high-fidelity frontend) **must** carry a routing stamp referencing an invoked creative session.
- Product `CLAUDE.md` + `11vt.project.yaml` gain a mandatory routing trigger line.

### Phase 2 — Concept gate before code (fix #2)
- For creative-production candidates, lifecycle enforces a **concept gate** between PLAN and IMPLEMENT: creative brief, composition/visual grammar, asset-reality check (real assets or explicit placeholder strategy).
- No implementation file until concept-gate evidence is committed.

### Phase 3 — Asset manifest gate (fix #5)
- Real-world asset products require a committed **asset manifest** (source URL/path, license status, local-cache strategy, attribution) before any `<img>` references a real asset.
- Replaces the post-hoc `assets-placeholder.txt` pattern with pre-build reality.

### Phase 4 — Evidence contract with pixels (fix #3, #6)
- Wire `frontend_quality_contract.py` + `visual_evidence_check.py` + `visual_evidence_evaluator.py` + `perceptual_visual_qa.py` into the **product flow**, not the foundry ascension mirror.
- Require a real screenshot artifact (headless fallback when Browser pane can't composite) before "visually inspected" is claimable.
- Commit-before-code: bootstrap produces at least one commit (manifest, routing, concept) before implementation.

### Phase 5 — Executable creative roles (fix #7)
- Grant Art Director + Visual QA Director **Write/Edit**; Motion Director **Bash**. The enforcement roles must be able to enforce.
- Add an independent creative review step that is per-product, not hardcoded to one fixture/model.

### Phase 6 — Canonical reference + type + motion-token system (elevate, not just gate)
- Curated **reference library** (image + principle cards) under `references/` so anti-generic reasoning has positive examples, not only rejection lists.
- **Type library**: commit licensed/OFL display faces so products stop guessing between system fonts; variable-font subsets.
- **Semantic design-token system**: tokens named by meaning (`signal-velocity`, `material-gravity`) not role (`color-1`), so "why" is hotwired into the build.
- **Motion-token system**: one canonical easing/spring/stagger vocabulary products consume.

### Phase 7 — Persistent agent memory (fix the throwaway lesson)
- Wire memory so the anti-generic lesson and per-world learnings persist across projects (align with Claude Code's `consolidate-memory` behavior). Empty `agent-memory/` is a designed loss.

### Phase 8 — Asset/toolchain unlocks (delivered after enforcement backbone, highest-leverage)
1. Fix Wan2.1-T2V local video (weights present; runtime fails on encoder/latent shape mismatch → run the RAW `run_wan.bat` path only, drop the diffusers variant). No download. ~17 min/frame-set.
2. Complete FLUX.2-klein-4B download (fits 8GB@FP8 in 12GB VRAM) — local SOTA image gen/editing, kills 9Router budget reliance.
3. Wire 9Router TTS (proven, free edge-tts/openrouter) into product pipelines — voiceover/narration at zero VRAM. Add `NINEROUTER_URL` to env.
4. Benchmark TripoSR (weights present, image→3D blockout, non-commercial — tag accordingly).
5. Stabilize ACE-Step polling (music proven; flaky timeout logic).
6. Install `wand` (single pip install) — ImageMagick python binding for scripted grade pipeline.
7. Fonts: self-host variable OFL display faces — highest frontend lever, free, no VRAM.
8. Re-run Blender rig/animate to move character chain off UNPROVEN.

Hardware/environment constraints (from live inventory): 12GB VRAM RTX 5070 Ti Laptop, 32GB RAM; 9Router live at `http://localhost:20128` (image/TTS/embeddings proven; video kind unsupported on this build, requires xAI account; STT no models). Wan2.1 raw weights present; ACE-Step env + 6 music mp3s already produced by API despite flaky polling.

## 6. Acceptance / definition of done for the upgrade

- A fresh product build that matches creative-production routing **cannot** ship an image without a routing stamp, concept gate, asset manifest, and screenshot evidence. The gates are fail-closed, not advisory.
- Art Director and Visual QA Director can write fixes; a per-product independent review runs before handoff.
- First-pass generic regression is impossible by construction: the pipeline routes, gates, and evidences before pixels land.
- Reference library, type library, semantic + motion tokens, and persistent memory exist under `references/` and are consumed by default.
- Web research pins live search + citation gate; memory-only work is labeled "unverified domain knowledge," never silently "cited."
- A benchmark product (TCG Learning Atlas) re-run shows the authored-real assets + choreographed motion + editorial composition + DPR/pixel evidence the first pass lacked.

## 7. Web-search defect (Founder-selected: pin live)

This session's web-search gateway returned empty bodies (`{ results: [] }`). The ceiling agent improvised domain knowledge under the label "cited." Founder decision: **first-class process defect**.

Enforcement:
- Research skill requires **live citations for current-trend, SOTD-level, or state-of-the-art claims**. When live fetch fails, the failure is surfaced as a routing blocker — the builder may either (a) retry/alternate gateway, or (b) explicitly label the claim "unverified domain knowledge," never present memory as cited.
- A **citation-verification gate** runs before output; memory-only work carries the unverified label in the artifact.

## 8. Phasing guardrail

Order matters: enforcement backbone (§5 Phase 1–7) ships first and is verified against a product before asset unlocks (§5 Phase 8) are layered on. Foundation absorbs and reaises the bar; widening without the backbone invites the same generic first pass.

## 9. Canonical status

This document is the plan. Execution begins after Founder approval of the phase order and after the enforcement backbone's first product proof. Existing reads that governed the plan:
- `CURRENT_STATE_MASTERY.md` — under-reports present capability (says Wan needs download / ACE-Step absent; both present-broken).
- `CURRENT_STATE.md` (foundry) — still PENDING the creative-council review on finished assets.