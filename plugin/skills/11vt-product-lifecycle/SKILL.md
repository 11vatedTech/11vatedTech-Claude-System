---
name: 11vt-product-lifecycle
description: Governing workflow for substantial 11vatedTech product development from discover through canonize. Use for continuing development, planning significant changes, enforcing quality gates, work contracts, lifecycle state, or avoiding premature coding.
metadata:
  owner: 11vatedTech
  type: product-development-system
  version: "0.2.0"
---

# 11vatedTech Product Lifecycle

DISCOVER → RESEARCH → CHALLENGE → SPECIFY → ARCHITECT → PLAN → IMPLEMENT → INTEGRATE → VERIFY → REVIEW → HARDEN → RELEASE → CANONIZE

Gates prevent premature coding, drift, fake completion, and lost decisions.

## Work contract trigger

For substantial work, define ID, objective, impact, acceptance criteria, affected systems, relevant architecture, known risks, validation strategy, and out-of-scope work before editing. Skip overhead for trivial edits.

## Definition of Done

Evaluate requirement, static quality, build, tests, integration, runtime, failure paths, regression, security, performance evidence, visual inspection, docs/canon, and evidence traceability. High-risk changes need independent review.

## Canonize

After verified substantial work, update `CURRENT_STATE.md` and evidence ledger with durable facts only. Do not paste transcripts. Do not claim production readiness before release gate.
