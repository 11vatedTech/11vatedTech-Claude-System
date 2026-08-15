---
name: 11vt-status
description: Fast 11vatedTech project status reconstruction. Use when entering a repo, continuing development, checking current milestone, validation freshness, manifest health, git state, or before deciding next work.
metadata:
  owner: 11vatedTech
  type: product-development-system
  version: "0.2.0"
---

# 11vatedTech Project Status

Rapidly reconstruct project reality without loading unnecessary context.

## Read order

1. `11vt.project.yaml`
2. concise `CLAUDE.md`
3. `CURRENT_STATE.md`
4. `git status --short` and branch
5. only canon docs relevant to active milestone

## Report

- product and maturity
- active milestone
- what works / does not work
- validation freshness
- dirty Git state
- next dependency-ordered work
- blockers
- whether deeper skills should load

Do not reread whole docs tree unless status points there.
