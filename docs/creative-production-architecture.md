# Creative Production Architecture

## Purpose

11vatedTech Claude now treats high-fidelity visual work as a modular creative-production organization, not a generic UI styling task.

The goal is to research, conceive, art-direct, engineer, render, observe, criticize, and iterate digital experiences until visual identity and production quality are evident in the rendered artifact.

## Capability map

| Capability | Owns | Trigger |
|---|---|---|
| `11vt-capability-entrypoint` | Founder-intent routing | Any substantive 11vatedTech task |
| `11vt-creative-production` | Creative-production lifecycle and acceptance gates | High-fidelity visual products, cinematic UI, games, 3D/rendering, asset-heavy work, anti-generic redesign |
| `11vt-design-director` | Frontend art direction execution and rendered visual QA | UI/UX, visual polish, responsive design, screenshots, design critique |
| `11vt-game-development` | Game loop/feel/systems/frame budget | Game projects, interactive mechanics |
| `11vt-research-intelligence` | Reference-first research and tooling/licensing investigation | Current design/tool/asset questions, prior art, source verification |
| `11vt-testing-verification` | Build/runtime/browser proof | Completion claims, previewable UI validation |
| `11vt-9router-orchestrator` | Model/modal discovery and routing risk | Model choice, multimodal generation/vision/TTS/STT/search/fetch |
| `11vt-independent-reviewer` | Release/handoff review | Substantial changes, risky changes, final review |

## Specialist agents

| Agent | Role |
|---|---|
| `11vt-creative-director` | Challenges weak concepts, defines thesis, emotion, references, differentiation, signature moments |
| `11vt-art-director` | Converts thesis into visual grammar: color, type, material, lighting, texture, motifs, framing |
| `11vt-experience-designer` | Owns journey, hierarchy, interactions, responsive behavior, accessibility, emotional pacing |
| `11vt-motion-director` | Owns motion language, choreography, microinteractions, camera/scroll, reduced-motion |
| `11vt-technical-artist` | Chooses rendering medium and pipeline: CSS/SVG/Canvas/WebGL/WebGPU/Three.js/shaders/procedural/video/audio |
| `11vt-asset-director` | Owns asset manifest, sourcing, production route, licensing/provenance, placeholder replacement |
| `11vt-visual-qa-director` | Adversarial rendered-output critique and visual evidence review |

Use minimum sufficient roles. Do not spawn full studio for trivial admin UI.

## Cooperation pattern

### Distinctive frontend product

`11vt-creative-production` → Creative Director → Art Director → Experience Designer → `11vt-design-director` implementation → browser preview evidence → Visual QA Director → fixes → independent reviewer if handoff/release.

### Game or interactive visual prototype

`11vt-game-development` + `11vt-creative-production` → Creative Director → Technical Artist/Motion Director/Asset Director as needed → implementation → runtime gameplay and visual inspection → Visual QA.

### 3D/rendering/shader work

Creative Director → Technical Artist → Rendering strategy → implementation with performance budget → rendered inspection → Visual QA → performance/security review if needed.

### Ordinary UI/task

Use normal engineering skills. Only activate design/creative capabilities when visual identity or UX quality matters.

## Project visual canon

Important visual products should create or maintain `docs/design/`:

- `VISUAL-CANON.md`
- `ART-DIRECTION.md`
- `MOTION-LANGUAGE.md`
- `MATERIAL-LANGUAGE.md`
- `TYPOGRAPHY.md`
- `ASSET-MANIFEST.md`
- `VISUAL-QA.md`

Use the template in `11vt-creative-production/references/project-visual-canon-template.md`. Keep canon concise and evidence-based.

## Visual verification

Previewable UI work must be inspected in the running application before visual completion claims.

Minimum evidence for significant visual work:

- build result
- server/runtime result
- desktop viewport inspection
- mobile viewport inspection
- one intermediate viewport when layout matters
- important interaction states
- console/network/server health
- accessibility snapshot or equivalent
- screenshot or selector-level style inspection
- comparison against visual canon
- Visual QA critique and correction notes

`11vt-creative-production/scripts/visual_evidence_check.py` validates structure of written visual evidence records.

## Hooks

Hooks remain deterministic safeguards only. They block destructive commands and protected secret paths. Subjective creative quality is not enforced by hooks because it requires rendered inspection and critique.

## 9Router/model routing

This environment routes Anthropic traffic through local 9Router settings. High-value creative direction, architecture, visual QA, and difficult implementation should prefer strongest available models and should not silently degrade to token-minimizing paths. Re-query 9Router capabilities when image, TTS, STT, video, vision, web search/fetch, or model-specific routing matters.

Known observed 2026-08-15 constraints: web and STT model discovery were empty; video endpoint not job-tested; image/TTS/embedding/image-to-text existed; chat model `11` was primary validated route.

## Extension rules

Add new skills only when recurring workflow needs specialized knowledge, repeatable method, deterministic automation, tool integration, project conventions, evaluation, or reusable references. Otherwise add a reference, project canon, script, or agent.

Future capabilities should include:

- trigger cases
- behavioral cases
- registry entry
- source/licensing notes if external
- validation command or manual audit notes
