# 11vatedTech Claude System

Versioned product-development and creative-production operating system for 11vatedTech Claude Code work.

**Status:** FOUNDATION GENESIS COMPLETE / CAPABILITY ASCENSION ACTIVE

Three states are tracked separately and never conflated:

- **Foundation status** — global deployment, routing, regression, rollback (COMPLETE).
- **Capability maturity** — per-capability L0-L5 in `config/capability-ontology.json` (ascension register: `config/capability-ascension-register.json`).
- **Frontier gaps** — `docs/GAP_REGISTER.md`.

Infrastructure being green does NOT mean creation capabilities are production-proven. Ascension is complete only when substantial capabilities reach L5 (production-proven + evaluated + independently verified).

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

## Deploy to the global ~/.claude installation

The Foundry is global: it is developed here and deployed to
`C:/Users/11vat/.claude`, where every project discovers it automatically.

```bash
python scripts/install/sync_to_claude.py --dry-run   # report drift, write nothing
python scripts/install/sync_to_claude.py             # sync with backup + manifest
python scripts/install/sync_to_claude.py --list      # recorded deployments
python scripts/install/sync_to_claude.py --rollback <id>   # restore a deployment
python scripts/install/validate_capability_installation.py # verify the global install
```

Every sync writes a timestamped backup and a deployment manifest under
`~/.claude/11vatedtech/deployments/` before changing anything, so any
installation can be rolled back.

## Capability ontology & maturity

- `config/capability-ontology.json` — machine-readable ontology (18 domains, 92 capabilities) with L0-L5 maturity and resolvable providers.
- `scripts/validate/ontology_check.py` — evidence gate: every provider
  resolves, every evidence pointer exists.
- `docs/capability-ontology.md`, `docs/maturity-baseline.md` — scale and
  scored baseline.

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
