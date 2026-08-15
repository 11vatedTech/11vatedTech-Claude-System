---
name: 11vt-testing-verification
description: Testing and runtime verification workflow for 11vatedTech. Use when designing tests, validating changes, proving completion, launching apps, inspecting outputs/logs, browser testing, failure injection, or building verification plans.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Testing and Verification

Tests are not decoration. Completion requires executable evidence.

## Test types

Use appropriate mix:

- unit
- integration
- contract
- property-based
- fuzz
- regression
- browser/e2e
- visual
- concurrency
- stress
- failure-injection
- deterministic
- GPU
- performance benchmark

## Verification workflow

1. define claim being verified
2. identify actual user/system workflow
3. run build/type/lint checks where present
4. run targeted tests
5. run broader tests when justified
6. launch app or executable when relevant
7. inspect outputs/logs/browser console/artifacts
8. test failure/cancel/recovery paths where relevant
9. document what passed, failed, skipped, or blocked

## Completion rules

- `build passed` alone is not completion.
- `tests passed` alone may not verify runtime behavior.
- If verification cannot run, state exact blocker and remediation.
- Capture stable launch/validation procedures as project knowledge.

Use `references/verification-plan-template.md`.
