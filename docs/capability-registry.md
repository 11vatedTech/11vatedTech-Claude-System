# 11vatedTech Claude Capability Registry

Last validated: 2026-08-15
Scope: user/global Claude Code capabilities unless noted.

## Architecture rule

- Global/user skills hold durable 11vatedTech operating methods.
- Project-specific facts stay inside each repository.
- Deep detail lives in references under each skill for progressive disclosure.
- Secrets stay in environment/configuration, never in skills.

## Capabilities

| Capability | Scope | Purpose | Source | Location | Dependencies | Trigger behavior | Evaluation status | Maintenance notes |
|---|---|---|---|---|---|---|---|---|
| 11vt-core-operating-system | global | Company doctrine, quality bar, completion vocabulary, continuity | custom | `~/.claude/skills/11vt-core-operating-system` | none | 11vatedTech strategy, quality bar, completion claims, continuity | static validated | Revisit when company doctrine changes |
| 11vt-research-intelligence | global | Technical/current research and invention analysis | custom | `~/.claude/skills/11vt-research-intelligence` | web/search tools when available | research, feasibility, prior art, current tech choices | static validated | Check official sources during use |
| 11vt-architecture-engineering | global | Product/software architecture and ADR workflow | custom | `~/.claude/skills/11vt-architecture-engineering` | repository read tools | major implementation, redesign, system boundaries, ADRs | static validated | Update templates from strong project usage |
| 11vt-production-engineering | global | Real implementation standard and failure handling | custom | `~/.claude/skills/11vt-production-engineering` | build/test tools per project | writing/reviewing real code, replacing stubs, hardening | static validated | Tighten anti-patterns from audits |
| 11vt-language-workflows | global | C++, Python, TypeScript workflow doctrine | custom | `~/.claude/skills/11vt-language-workflows` | language toolchains | C++/Python/TypeScript, CMake, packaging, type systems | static validated | Add language refs only when recurring need appears |
| 11vt-ai-ml-local-inference | global | AI/ML, model evaluation, local inference, ONNX/GPU planning | custom | `~/.claude/skills/11vt-ai-ml-local-inference` | GPU/runtime tools as project requires | model choice, local-first AI, embeddings, vision/speech, benchmarks | static validated | Keep runtime/tool docs current |
| 11vt-game-development | global | Game systems, loops, engine/tooling/rendering workflows | custom | `~/.claude/skills/11vt-game-development` | engine/project tooling | game mechanics, systems, pipelines, frame budgets | static validated | Add engine-specific knowledge only at project scope |
| 11vt-design-director | global | High-fidelity UI/UX, art direction, frontend visual QA | custom | `~/.claude/skills/11vt-design-director` | browser preview tools when available | UI design, visual polish, frontend fidelity, screenshots | static validated | Pair with first-party frontend-design/dataviz skills when useful |
| 11vt-repository-auditor | global | Repo audits and release-readiness findings | custom | `~/.claude/skills/11vt-repository-auditor` | read/search/build/test tools | audit, technical debt, TODO/stub/dependency/security scans | static validated | Calibrate severity from real audits |
| 11vt-testing-verification | global | Test planning and runtime verification | custom | `~/.claude/skills/11vt-testing-verification` | project test/build/preview tools | test design, validation, launch, inspect, prove claims | static validated | Capture project launch procedures in repo canon |
| 11vt-performance-security | global | Profiling/benchmarking plus threat modeling/security | custom | `~/.claude/skills/11vt-performance-security` | profilers/security tools as available | performance, security, release hardening, threat models | static validated | Split later only if trigger collisions appear |
| 11vt-documentation-canon | global | Durable docs/canon discipline | custom | `~/.claude/skills/11vt-documentation-canon` | none | README, ADRs, specs, handoffs, canon memory | static validated | Keep docs reality-based |
| 11vt-9router-orchestrator | global | Dynamic 9Router model/capability routing | custom | `~/.claude/skills/11vt-9router-orchestrator` | 9Router service | 9Router routing, model discovery, multimodal capabilities | runtime discovery validated | Re-query endpoints during use |
| 11vt-skill-foundry | global | Skill sourcing, creation, evaluation, maintenance | custom | `~/.claude/skills/11vt-skill-foundry` | file/search/web tools | create/audit/source/evaluate skills and registries | static validated | Review when Claude Code skill conventions change |
| 9router | global | 9Router setup and capability index | decolua/9router | `~/.claude/skills/9router` | running 9Router | mentions 9Router/NINEROUTER_URL/provider gateway | runtime health validated | Track upstream changes manually |
| 9router-chat | global | Chat/code generation through 9Router | decolua/9router | `~/.claude/skills/9router-chat` | 9Router chat models | chat, code generation, prompts through 9Router | runtime model list validated | Query `/v1/models` before model choice |
| 9router-image | global | Image generation through 9Router | decolua/9router | `~/.claude/skills/9router-image` | image models | text-to-image/image generation | discovery validated | Query `/v1/models/image` |
| 9router-tts | global | Text-to-speech through 9Router | decolua/9router | `~/.claude/skills/9router-tts` | TTS models | voiceover, narration, speech generation | discovery validated | Query `/v1/models/tts` |
| 9router-embeddings | global | Embeddings through 9Router | decolua/9router | `~/.claude/skills/9router-embeddings` | embedding models | RAG, semantic search, vector embeddings | discovery validated | Query `/v1/models/embedding` |
| 9router-web-search | global | Web search through 9Router | decolua/9router | `~/.claude/skills/9router-web-search` | web search models | web search via 9Router | installed; no models available 2026-08-15 | Re-check before use |
| 9router-web-fetch | global | URL fetch through 9Router | decolua/9router | `~/.claude/skills/9router-web-fetch` | web fetch models | scrape/fetch/read URL through 9Router | installed; no web models shown 2026-08-15 | Re-check before use |
| 9router-stt | global | Speech-to-text through 9Router | decolua/9router | `~/.claude/skills/9router-stt` | STT models | transcription/subtitles | installed; no models available 2026-08-15 | Re-check before use |
| 9router-video | global | Async video generation through 9Router | decolua/9router | `~/.claude/skills/9router-video` | video provider configured | text-to-video/image-to-video | installed; endpoint not runtime-tested | Requires provider capability/account |
| OpenSpec skills | global | Existing change/spec workflow | existing user install | `~/.claude/skills/openspec-*` | OpenSpec CLI | OpenSpec proposal/apply/sync/archive/explore | preserved, read-only inspected | Not modified |

## Not installed intentionally

- Broad third-party plugin marketplace entries were not installed blindly.
- Official marketplace was inspected as source ecosystem; plugin installation left for explicit per-need adoption because plugins may add MCP servers, commands, hooks, dependencies, or paid services.


## Phase II Product Development System Additions

| Capability | Scope | Purpose | Location | Evaluation status |
|---|---|---|---|---|
| 11vt-capability-entrypoint | global/plugin | Universal access point that routes Founder intent to minimum sufficient 11vatedTech skills, agents, tools, research, and validation without requiring manual skill names | `plugin/skills/11vt-capability-entrypoint`, `~/.claude/skills/11vt-capability-entrypoint` | installed/accessibility validated |
| 11vt-status | global/plugin | Fast project state reconstruction and continuation entrypoint | `plugin/skills/11vt-status` | trigger/static validated |
| 11vt-project-bootstrap | global/plugin | Bootstrap/retrofit repos with manifest, canon, project skills, validation tooling | `plugin/skills/11vt-project-bootstrap` | fixture regression passed |
| 11vt-product-lifecycle | global/plugin | Discover-to-canonize governing workflow and Definition of Done | `plugin/skills/11vt-product-lifecycle` | trigger/static validated |
| 11vt-release-engineering | global/plugin | Release gates, artifacts, install/rollback evidence | `plugin/skills/11vt-release-engineering` | trigger/static validated |
| 11vt-independent-reviewer | global/plugin agent | Read-only independent review before release/handoff | `plugin/agents/11vt-independent-reviewer.md` | structural validated |
| deterministic hooks | plugin | Destructive command, secret path, and session-status guards | `plugin/hooks/` | hook regression passed |
| project manifest standard | template/tooling | Machine-readable operational index for product repos | `templates/product-repository/11vt.project.yaml`, `scripts/validate/manifest_validator.py` | validator regression passed |
| evidence ledger | template/tooling | Trace completion claims to concise validation records | `templates/product-repository/tools/11vt/evidence.py` | template validated |
