---
name: 11vt-capability-entrypoint
description: Universal 11vatedTech capability entrypoint. Use automatically for any 11vatedTech request, new chat, continuation, new product, repo work, audit, release, capability recall, high-fidelity creative/visual work, or when the Founder asks what this Claude system can do. Select the minimum relevant 11vt skills and agents without requiring the Founder to name them.
metadata:
  owner: 11vatedTech
  type: global-capability-entrypoint
  version: "0.3.0"
---

# 11vatedTech Capability Entrypoint

The Founder provides intent. Claude determines capability and workflow.

Use this as the lightweight entrypoint for 11vatedTech work in new or resumed chats. Do not make the Founder manage skill names.

## First move

For any substantive 11vatedTech request, silently classify:

1. repo continuation vs new product vs research vs implementation vs audit vs release vs capability maintenance vs creative-production work
2. current repository state, if a repo is present
3. minimum relevant skills, agents, tools, and validation path
4. whether current web research, visual reference research, multimodal tooling, or 9Router augmentation is useful
5. what evidence is needed before claiming completion

Do not list selected capabilities unless asked.

## Default routing

- New or resumed repo work: `11vt-status`, then `11vt-product-lifecycle` if substantial; `11vt-project-bootstrap` when the repo is not yet governed.
- New product/product idea: `11vt-core-operating-system`, `11vt-research-intelligence`, `11vt-architecture-engineering`, then domain skills as relevant.
- Code implementation/fix: `11vt-production-engineering`, `11vt-language-workflows`, `11vt-testing-verification`.
- Audit: `11vt-repository-auditor`, `11vt-testing-verification`, `11vt-performance-security` if relevant.
- Release/production readiness: `11vt-release-engineering`, `11vt-testing-verification`, `11vt-independent-reviewer` for substantial or risky changes.
- AI/ML/local model work: `11vt-ai-ml-local-inference` and `11vt-9router-orchestrator` when useful.
- UI/visual/frontend work: `11vt-design-director` and browser preview tools when available.
- High-fidelity creative product, game presentation, cinematic interface, asset-heavy UI, 3D/shader/rendering, audiovisual, typography, visual identity, or anti-generic redesign: `11vt-creative-production`, then `11vt-design-director`, `11vt-research-intelligence`, `11vt-testing-verification`, and specialist agents as needed.
- Game work: `11vt-game-development`; add `11vt-creative-production` when game feel, art direction, cards, VFX, camera, audio, or visual polish are material.
- Skill/system maintenance: `11vt-skill-foundry`.
- Documentation/canon/memory: `11vt-documentation-canon`.

## Creative-production routing ladder

Use only as much machinery as intent requires, but create a durable routing stamp for substantial creative work before broad implementation:

- Ordinary settings/admin screen or README typo: standard route; do not invoke full creative stack.
- Distinctive UI/product identity: `11vt-creative-production` → `11vt-design-director` → rendered QA.
- Cinematic/game/high-fidelity visual product: Creative Director → Art Director → Experience Designer → Motion Director/Technical Artist/Asset Director as needed → implementation → Visual QA Director.
- 3D/shader/rendering: Creative Director → Technical Artist → rendering/performance validation → Visual QA.
- Visual handoff/release: independent reviewer checks rendered visual evidence.

Operational route check when capability-system is available:

```bash
python ~/.claude/11vatedtech/capability-system/scripts/validate/creative_studio_gates.py route "<Founder intent>" --out artifacts/ascension/routing-stamp.json
```

If result is `CREATIVE_STUDIO_REQUIRED`, no broad component/product build may begin until concept, reference/resource, craft, and first-visible-artifact gates have evidence.

Fail closed:

- high-fidelity game/frontend/visual/asset-heavy work without routing stamp
- creative task whose concept could fit 100 unrelated products
- rendered-product claim without visual evidence
- live-research claim when route actually returned `LIVE_RESEARCH_UNAVAILABLE` or `UNVERIFIED_DOMAIN_KNOWLEDGE`

## Canonical sources

- Canonical system repo: `C:/Users/11vat/OneDrive/Desktop/11vatedTech-Claude-System`
- User global skills: `C:/Users/11vat/.claude/skills/`
- User global agents: `C:/Users/11vat/.claude/agents/`
- Capability records: `C:/Users/11vat/.claude/11vatedtech/capability-system/`
- Workspace memory index: `C:/Users/11vat/.claude/projects/C--Users-11vat-OneDrive-Desktop-claude-9router-workspace/memory/MEMORY.md`

## Continuity rule

When the Founder says "continue development", inspect the current repo for `11vt.project.yaml`, `CLAUDE.md`, `CURRENT_STATE.md`, git state, validation commands, and active blockers before coding.

When no governed repo exists, use the canonical system repo and installed global skills as the source of 11vatedTech capability, not conversation memory alone.

## Control boundaries

Autonomously research, analyze, design, code, test, review, document, and prepare artifacts. Confirm before publishing, spending money, deleting unknown work, changing production infrastructure, or pushing outward-facing releases.
