# 11vatedTech Claude System

Versioned product-development and creative-production operating system for 11vatedTech Claude Code work.

**Status:** SYSTEM-READY / CREATIVE-PRODUCTION EXPANDED / REQUIRES PRODUCT CALIBRATION

## Purpose

Turns 11vatedTech Claude capabilities into repeatable development infrastructure: project bootstrap, manifest, canon, workflow gates, evidence, review, release, hooks, validation, 9Router routing benchmarks, and high-fidelity creative-production roles.

## Layout

- `plugin/` — internal Claude Code plugin containing skills, specialist agents, hooks, and helpers.
- `templates/product-repository/` — stack-neutral repository canon and `.claude` template.
- `scripts/` — install/update/doctor/validate/bootstrap tooling.
- `evaluations/` — trigger, behavioral, regression, and model-routing suites.
- `docs/` — registry, ledger, protocol, creative-production architecture, security model, update procedure.
- `tests/fixtures/` — disposable fixture area for bootstrap tests.

## Validate

```bash
python scripts/validate/system_regression.py
```

## Test plugin locally

```bash
claude --plugin-dir ./plugin
```

## Sync plugin skills and agents to standalone user install

```bash
python scripts/install/sync_to_claude.py
```

## Capability access

- `11vt-capability-entrypoint` is the universal Founder-intent entrypoint for new chats and normal work.
- The Founder should not need to remember skill names; Claude routes to minimum sufficient 11vatedTech capabilities.
- High-fidelity visual work routes through `11vt-creative-production`, `11vt-design-director`, and specialist agents as needed.
- User-level pointer: `C:/Users/11vat/.claude/CLAUDE.md`.

## Major deliverables

- Internal plugin manifest validated with `claude plugin validate --strict` / system regression.
- Product repository template with manifest, canon, project skills, local verification, release gate, evidence tooling, design system, asset pipeline, and visual canon directory.
- Deterministic hook guards and session status injection.
- Independent reviewer agent plus creative-production specialists.
- Bootstrap fixture/idempotence/preservation tests.
- 9Router routing smoke benchmark and cached profile.
- Creative-production architecture for concept, references, art direction, assets, motion, technical art, rendered evidence, and Visual QA.
