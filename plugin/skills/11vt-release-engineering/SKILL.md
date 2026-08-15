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

## Evidence

Every release candidate needs evidence with commit SHA, platform, commands, artifacts, checksums, caveats, and approval state.
