---
name: 11vt-research-intelligence
description: 11vatedTech research and invention-analysis workflow. Use for technical research, current-tool selection, feasibility checks, prior-art investigation, standards comparison, or when an answer could have changed.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Research Intelligence

Research must change decisions. Do not use web search as decoration.

## Source priority

1. official specifications
2. official documentation
3. upstream repositories
4. primary research papers
5. standards bodies
6. benchmarks
7. maintainers
8. reputable engineering analysis
9. community evidence when primary evidence is unavailable

## Research output contract

For non-trivial research, report:

- Facts
- Evidence with source links
- Inferences
- Unknowns
- Recommendation
- Architecture impact
- Validation experiments

## Evidence route contract

Every non-trivial or current claim must name one or more routes:

- `LIVE_WEB`
- `OFFICIAL_DOCS`
- `REPOSITORY`
- `KAPIF_CANON`
- `LOCAL_EVIDENCE`
- `DOMAIN_KNOWLEDGE_ONLY`
- `UNAVAILABLE`

Fail closed:

- If live/current research route fails, state `LIVE_RESEARCH_UNAVAILABLE`.
- If answer relies on memory or domain knowledge without source evidence, state `UNVERIFIED_DOMAIN_KNOWLEDGE`.
- Do not convert memory, prior session notes, or model knowledge into "researched" claims.
- Unknown means unknown; do not fabricate license rights, platform behavior, current counts, model capability, or trend evidence.

Operational check when capability-system is available:

```bash
python ~/.claude/11vatedtech/capability-system/scripts/assets/resource_intelligence.py evidence-route "<claim>" LIVE_WEB OFFICIAL_DOCS
```

## Technology comparison checklist

Compare:

- capability fit
- architecture
- maturity
- maintenance activity
- performance
- memory use
- GPU support
- platform support
- licensing
- dependencies
- deployment model
- security surface
- limitations
- known bugs
- ecosystem
- current trajectory
- lock-in risk
- open/local alternatives

## Invention research

For proposed inventions, investigate:

- prior art
- adjacent research
- existing products
- academic literature
- physical/math/computational constraints
- available open-source foundations
- novelty gaps
- failure modes
- experiments required for validation

Use `references/research-report-template.md` for durable research reports.
