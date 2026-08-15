---
name: 11vt-documentation-canon
description: Documentation and canon management for 11vatedTech. Use for README, architecture docs, ADRs, roadmaps, validation specs, research reports, benchmark reports, audit reports, release notes, handoffs, or durable project knowledge.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Documentation and Canon

Docs must reflect reality. Never write aspirational documentation that claims implementation exists when it does not.

## Documentation types

Use appropriate artifact:

- README: current install/build/run/use
- architecture doc: system shape and boundaries
- ADR: durable decision and tradeoffs
- design spec: product/design intent and interaction model
- validation spec: how claims are proven
- testing strategy: test layers and ownership
- security model: assets, boundaries, mitigations
- research report: evidence, facts, inference, recommendation
- benchmark report: workload, baseline, result
- audit report: findings and remediation
- roadmap: ordered future work with dependencies
- changelog/release notes: user-visible changes
- handoff: current state, blockers, next actions

## Canon rules

- Store durable company principles globally.
- Store project-specific facts in that repository.
- Store transient session state only when it affects immediate continuation.
- Update docs when implementation changes behavior.
- Label unimplemented plans as planned, not shipped.
- Keep index compact; put deep detail in references.

## Completion criteria

Documentation is valid only when:

- commands match current project
- architecture matches current code
- feature status matches implementation
- validation status names what actually ran
- open questions and gaps remain visible

Use `references/canon-index-template.md` for project canon.
