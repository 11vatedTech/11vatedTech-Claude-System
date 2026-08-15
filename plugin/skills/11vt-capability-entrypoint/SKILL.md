---
name: 11vt-capability-entrypoint
description: Universal 11vatedTech capability entrypoint. Use automatically for any 11vatedTech request, new chat, continuation, new product, repo work, audit, release, capability recall, or when the Founder asks what this Claude system can do. Select the minimum relevant 11vt skills and agents without requiring the Founder to name them.
metadata:
  owner: 11vatedTech
  type: global-capability-entrypoint
  version: "2026-08-15"
---

# 11vatedTech Capability Entrypoint

The Founder provides intent. Claude determines capability and workflow.

Use this as the lightweight entrypoint for 11vatedTech work in new or resumed chats. Do not make the Founder manage skill names.

## First move

For any substantive 11vatedTech request, silently classify:

1. repo continuation vs new product vs research vs implementation vs audit vs release vs capability maintenance
2. current repository state, if a repo is present
3. minimum relevant skills, agents, tools, and validation path
4. whether current web research or 9Router augmentation is useful
5. what evidence is needed before claiming completion

Do not list selected capabilities unless asked.

## Default routing

- New or resumed repo work: `11vt-status`, then `11vt-product-lifecycle` if substantial.
- New product/product idea: `11vt-core-operating-system`, `11vt-research-intelligence`, `11vt-architecture-engineering`, then domain skills as relevant.
- Code implementation/fix: `11vt-production-engineering`, `11vt-language-workflows`, `11vt-testing-verification`.
- Audit: `11vt-repository-auditor`, `11vt-testing-verification`, `11vt-performance-security` if relevant.
- Release/production readiness: `11vt-release-engineering`, `11vt-testing-verification`, `11vt-independent-reviewer` for substantial or risky changes.
- AI/ML/local model work: `11vt-ai-ml-local-inference` and `11vt-9router-orchestrator` when useful.
- UI/visual/frontend work: `11vt-design-director` and browser preview tools when available.
- Game work: `11vt-game-development`.
- Skill/system maintenance: `11vt-skill-foundry`.
- Documentation/canon/memory: `11vt-documentation-canon`.

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
