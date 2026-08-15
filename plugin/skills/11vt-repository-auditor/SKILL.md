---
name: 11vt-repository-auditor
description: Rigorous repository audit workflow for 11vatedTech. Use for repo health checks, codebase audits, technical debt discovery, release readiness review, dead code/stub/TODO scans, dependency review, or architecture risk assessment.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Repository Auditor

Audit evidence, not vibes.

## Scope

Evaluate:

- architecture and dependency graph
- dead code and duplicate systems
- incomplete implementations, TODO/FIXME, stubs
- commented-out code and generated-file misuse
- compiler/type/lint suppressions
- hidden build artifacts
- missing/flaky tests
- race conditions and ownership problems
- resource leaks
- API/schema mismatches
- security weaknesses
- dependency vulnerabilities
- performance risks
- packaging and reproducibility
- documentation drift
- release readiness

## Workflow

1. inventory repository structure
2. identify language/tooling/build/test paths
3. map major modules and boundaries
4. search for incompleteness markers
5. inspect dependency/security surface
6. run available checks where safe
7. verify selected findings against code
8. rank by severity and remediation value
9. provide validation commands

## Finding contract

Each finding must include:

- severity
- evidence
- affected files
- root cause
- remediation
- validation procedure

Use `references/audit-report-template.md` for durable audit reports.
