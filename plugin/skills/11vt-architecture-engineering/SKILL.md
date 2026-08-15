---
name: 11vt-architecture-engineering
description: Principal-level product/software architecture workflow for 11vatedTech. Use before major implementation, system redesign, technology selection, boundary definition, ADRs, APIs, state models, or product architecture.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Architecture Engineering

Architect from requirements and evidence, not favorite patterns.

## Pre-architecture inspection

Before major implementation, identify:

1. repository/product purpose
2. existing architecture
3. system boundaries
4. invariants
5. dependencies
6. data ownership
7. concurrency boundaries
8. lifecycle/state transitions
9. error boundaries
10. performance-critical paths
11. security boundaries
12. testing seams
13. deployment targets
14. future extension pressure

## Pattern discipline

Do not force microservices, ECS, event sourcing, clean architecture, DDD, CQRS, plugin systems, or message buses unless requirement pressure justifies them.

## ADR trigger

Create or update ADR when decision affects:

- module boundaries
- data ownership
- persistence
- external dependency
- concurrency model
- security boundary
- release/deployment model
- long-term extension path

## Architecture output

Include:

- requirements driving design
- rejected alternatives
- chosen boundaries
- interfaces/contracts
- state/data model
- error model
- security model
- performance budget
- testing strategy
- migration path
- validation plan

Use `references/adr-template.md` when writing ADRs.
