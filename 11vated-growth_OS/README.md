# 11vatedTech GrowthOS

**Local-first commercial intelligence operating system for 11vatedTech.**

GrowthOS is an independent, self-owned operating system for product marketing,
relationship networking, client acquisition, sales, opportunity management,
founder communication, and revenue learning. It runs primarily on a Windows
workstation, uses open-source/local infrastructure, and requires no recurring
paid AI/API subscription for core operation.

It is **not** a CRM skin, chatbot, email generator, or lead scraper. It is a
complete operational system whose central question is:

> **What valuable problem does this person or organization have that
> 11vatedTech can genuinely solve — and what is the highest-value professional
> path toward creating that value and developing the relationship?**

## Truth architecture

Every claim in GrowthOS is one of four truth classes:

| Class | Meaning |
|-------|---------|
| `FACT` | Directly supplied or retrieved information |
| `OBSERVATION` | Something directly observable from evidence |
| `INFERENCE` | An agent conclusion derived from evidence |
| `HYPOTHESIS` | A commercial proposition not yet validated |

Inferences and hypotheses must link back to supporting evidence. Facts and
hypotheses can never silently merge.

## Zero mock data

Production contains **zero** fictional commercial data. An empty database
produces a polished empty system: 0 prospects, $0 pipeline, $0 revenue, an
empty inbox. Test fixtures are `TEST_ONLY` and never enter production storage.

## Tech stack

- **Frontend:** React + TypeScript (Vite), installable PWA
- **Backend:** Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic
- **Database:** PostgreSQL
- **Local AI:** Ollama (qwen3.5:9b target, qwen3-embedding:0.6b embeddings)
- **Integrations:** Gmail API (OAuth), LinkedIn official APIs + export import,
  self-hosted Android SMS gateway (no Twilio)

## Quick start

```bash
# Prerequisites: Python 3.12+, Node 20+, PostgreSQL 15+, Ollama
uv sync
uv run growthos doctor
uv run growthos setup database
uv run alembic upgrade head
uv run growthos api           # starts the API on http://127.0.0.1:8000
cd apps/web && pnpm install && pnpm dev   # starts the PWA
```

## Repository layout

```
apps/web            Founder-facing GrowthOS interface (PWA)
services/agent      Commercial reasoning and tool execution
services/workers    Scheduled jobs, ingestion, follow-up evaluation
services/sms-bridge SMS gateway adapter and founder command plane
services/research   Public-web and business reconnaissance
packages/domain     Canonical entities, enums, commercial state machines
packages/intelligence  Scoring, classification, evidence, confidence, inference
packages/integrations Gmail, LinkedIn, SMS, networking adapters
packages/security   Permissions, approval policies, auth, secret management
packages/shared     Shared schemas/types/utilities
infra               Docker/local infrastructure and deployment configuration
docs                Architecture, setup, integrations, threat model, acceptance
tests               Unit, integration, contract, security, persistence, E2E
```

## Status honesty

Integration status is reported with one of:

- `IMPLEMENTED` — adapter code exists
- `UNIT VERIFIED` — deterministic logic tested
- `INTEGRATION VERIFIED` — exercised against a real dependency
- `REAL-WORLD VERIFIED` — exercised against production accounts/data
- `BLOCKED` — external prerequisite missing

See `docs/PRODUCTION_ACCEPTANCE.md` for the live status matrix.

## Documentation

See `docs/ARCHITECTURE.md` for the system design and `docs/` for setup guides.

**11vatedTech owns and operates GrowthOS.** It does not depend on Base44 or any
application-building SaaS.
