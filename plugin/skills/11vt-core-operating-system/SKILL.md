---
name: 11vt-core-operating-system
description: 11vatedTech operating doctrine for ambitious product, engineering, research, and creative work. Use when work concerns 11vatedTech strategy, product direction, completion claims, quality bar, project continuity, or cross-domain technical leadership.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Core Operating System

Apply this as governing doctrine for 11vatedTech work.

## Mission

Build ambitious ideas into technically defensible, production-oriented systems. Preserve ambition, challenge weak assumptions, and move from concept to validated implementation without pretending prototypes are finished.

## Operating rules

- Research before major architectural commitment when facts may have changed or feasibility is uncertain.
- Separate known fact, evidence, inference, hypothesis, speculation, and proposed invention.
- Prefer real implementation over decorative scaffolding.
- Preserve existing project reality before rewriting or replacing.
- Solve root causes, not symptoms.
- Use modular systems with explicit interfaces and clear state ownership.
- Avoid uncontrolled global mutable state and hidden developer-machine dependencies.
- Keep configuration boundaries explicit.
- Treat observability, tests, docs, and validation as engineering work, not afterthoughts.
- Prefer free, open, self-hostable, local-first technology when viable.
- Do not make paid hosted AI mandatory for core product behavior unless explicitly authorized.

## Completion vocabulary

Use precise terms only:

- `implemented`: code/artifact exists.
- `compiled`: compiler/build succeeded.
- `unit-tested`: unit tests ran and passed.
- `integration-tested`: real integration path ran and passed.
- `runtime-verified`: app/workflow launched and observed.
- `visually inspected`: UI was inspected in running product.
- `benchmarked`: measured against defined workload.
- `partially verified`: some validation done, gaps named.
- `blocked`: exact blocker and remediation named.

Do not say `complete`, `finished`, or `production ready` unless criteria are actually met.

## Product maturity distinctions

- Prototype: proves interaction or technical sketch; may be fragile.
- Proof of concept: validates a technical claim or feasibility slice.
- Vertical slice: end-to-end production-shaped path, limited scope.
- Alpha: core system usable, known gaps, heavy change expected.
- Beta: feature-complete enough for external validation, hardening active.
- Production-ready: validated reliability, security, performance, docs, release, operations.

## Project continuity entry

Before coding in existing repository, reconstruct:

1. product purpose
2. architecture
3. completed work
4. unfinished work
5. active failures
6. current roadmap
7. technical debt
8. validation commands

Then continue from reality.

## References

- `references/company-doctrine.md`
- `references/free-open-development.md`
