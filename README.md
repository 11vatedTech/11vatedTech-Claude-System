# 11vatedTech Claude System

Versioned product-development operating system for 11vatedTech Claude Code work.

**Status:** SYSTEM-READY / REQUIRES PRODUCT CALIBRATION

## Purpose

Turns 11vatedTech Claude capabilities into repeatable product development infrastructure: project bootstrap, manifest, canon, workflow gates, evidence, review, release, hooks, validation, and 9Router routing benchmarks.

## Layout

- `plugin/` — internal Claude Code plugin containing skills, reviewer agent, hooks, and helpers.
- `templates/product-repository/` — stack-neutral repository canon and `.claude` template.
- `scripts/` — install/update/doctor/validate/bootstrap tooling.
- `evaluations/` — trigger, behavioral, regression, and model-routing suites.
- `docs/` — registry, ledger, protocol, security model, update procedure.
- `tests/fixtures/` — disposable fixture area for bootstrap tests.

## Validate

```bash
python scripts/validate/system_regression.py
```

## Test plugin locally

```bash
claude --plugin-dir ./plugin
```

## Sync plugin skills to standalone user skills

```bash
python scripts/install/sync_to_claude.py
```

## Phase II Deliverables

- Internal plugin manifest validated with `claude plugin validate --strict`.
- Product repository template with manifest, canon, project skills, local verification, release gate, and evidence tooling.
- Deterministic hook guards and session status injection.
- Independent reviewer agent.
- Bootstrap fixture/idempotence/preservation tests.
- 9Router routing smoke benchmark and cached profile.

