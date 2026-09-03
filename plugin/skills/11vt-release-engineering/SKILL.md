---
name: 11vt-release-engineering
description: Release readiness and distribution workflow for 11vatedTech products. Use for release gates, clean checkout validation, versioning, artifacts, install/upgrade/uninstall checks, changelogs, licenses, checksums, rollback, or release evidence.
metadata:
  owner: 11vatedTech
  type: product-development-system
  version: "0.2.0"
---

# 11vatedTech Release Engineering

Release requires distributable evidence, not local success.

## Release gate

When applicable verify clean source state, version, locked dependencies, clean checkout build, full verification, security review, license review, artifacts, artifact smoke, installation, upgrade, uninstall, config defaults, no secrets, checksums, release notes, docs, and rollback procedure.

## Distribution principle

Choose release infrastructure from product requirements. Prefer free/open/self-hostable routes where viable. Do not make paid hosting mandatory by default.

Resource acquisition and release are separate trust domains. Never publish, upload, buy, authenticate, or expose secrets without explicit Founder authorization.

External-resource release gate:

- `PROTOTYPE_ASSET` must never silently ship.
- `LICENSE_UNCLEAR`, `UNKNOWN`, or `UNVERIFIED` shipping assets fail closed.
- Itch.io is not one license; every asset needs its own creator/source/version/license/commercial/modification/redistribution/attribution/AI-terms record.
- External archives, plugins, scripts, and tools are untrusted; do not execute code from asset packages automatically.
- Raw/paid marketplace resources stay outside Foundry source, public product repos, and Git history unless legally appropriate.
- `BUTLER_API_KEY` and all publishing credentials remain secret; itch.io/butler release needs separate explicit authorization.

Operational check when capability-system is available:

```bash
python ~/.claude/11vatedtech/capability-system/scripts/validate/creative_studio_gates.py release-assets artifacts/release/asset-manifest.json
```

## Evidence

Every release candidate needs evidence with commit SHA, platform, commands, artifacts, checksums, caveats, and approval state.
