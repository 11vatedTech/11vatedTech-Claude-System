---
name: 11vt-production-engineering
description: Production implementation standards for 11vatedTech software. Use when writing or reviewing real code, replacing stubs, hardening features, configuring builds, or deciding whether work is truly implemented.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Production Engineering

Reject fake completeness.

## Do not present as final

- placeholder implementations
- fake backend responses
- dead navigation
- TODO-driven core paths
- swallowed exceptions
- silently ignored failures
- unnecessary `any`
- uncontrolled global mutable state
- hidden dependency on developer-machine state
- hardcoded config that belongs in runtime/build config
- architecture bypasses to make tests pass
- disabled lint/type/compiler checks without durable reason

## Prefer

- explicit contracts
- typed interfaces
- schema validation at boundaries
- dependency injection where useful
- RAII where useful
- deterministic ownership
- clear state machines
- reproducible builds
- semantic error types
- structured logging
- observability
- graceful failure
- bounded resources
- safe concurrency
- documented invariants

## Implementation loop

1. inspect local idioms
2. identify boundary and invariant
3. implement smallest real path
4. handle failure path
5. add or update tests
6. run executable verification
7. inspect runtime/logs where relevant
8. update docs if behavior changed

## Failure behavior

If blocked, report exact blocker, affected capability, remediation, and command/action required. Never pretend blocked step succeeded.
