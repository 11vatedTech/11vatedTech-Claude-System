# GrowthOS Architecture

GrowthOS is a local-first commercial intelligence operating system for
11vatedTech. It is independent of Base44 and any application-building SaaS.

## Principles

1. **Deterministic systems before agent reasoning.** Calculations, permissions,
   dedup, state transitions, and suppression are ordinary tested software. The
   LLM reasons; the software governs.
2. **Source → evidence → intelligence.** Facts and observations are raw; every
   inference and hypothesis links back to evidence. Facts never silently become
   hypotheses.
3. **Zero mock commercial data.** An empty database is a polished empty system.
4. **Truthful status.** Capabilities are `IMPLEMENTED`, `UNIT VERIFIED`,
   `INTEGRATION VERIFIED`, `REAL-WORLD VERIFIED`, or `BLOCKED` — never inflated.

## Runtime topology

```
Founder phone (PWA)
   │  authenticated (Tailscale private network)
   ▼
apps/web  (React + TypeScript PWA)  ──►  apps/api  (FastAPI)
                                              │
   ┌──────────────────────────────────────────┼──────────────────────────┐
   │                                          │                          │
   ▼                                          ▼                          ▼
PostgreSQL                          services/workers               services/agent
(persistent state,                  (persistent job system:        (commercial reasoning
 migrations, FKs,                   retry/backoff/idempotency,      + tool execution)
 constraints, dedup)                dead-letter, scheduled jobs)
                                              │
                                    Ollama (local inference, no paid cloud AI)
```

Do not expose PostgreSQL, Ollama, workers, or admin ports publicly. Only the
authenticated GrowthOS application is remotely reachable (via Tailscale).

## Layering (Python package `growthos`)

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Domain | `growthos/domain` | Entities, enums, state machines (46 tables) |
| Intelligence | `growthos/intelligence` | Scoring, classification, evidence, confidence |
| Security | `growthos/security` | Auth, permissions, approvals, secrets, suppression, cost guard |
| Integrations | `growthos/integrations` | Ollama, Gmail, LinkedIn, SMS gateway |
| Workers | `growthos/workers` | Persistent job queue + worker loop |
| Services | `growthos/services` | Product/campaign/opportunity/revenue/inbox use cases |
| API | `growthos/api` | FastAPI routes, auth, CSRF, exception mapping |
| CLI | `growthos/cli` | `growthos doctor`, `setup`, `migrate`, `api`, `worker` |

The repository layout maps to the spec's `apps/`, `services/`, `packages/`,
`infra/`, `docs/`, `tests/` boundaries; the Python package consolidates the
service/package modules into one installable package with strong internal
module boundaries (a deliberate simplification for a solo-founder local
system).

## Data model

See [`COMMERCIAL_GRAPH.md`](COMMERCIAL_GRAPH.md). The schema uses:

- UUID primary keys, timestamps, foreign keys with cascades
- unique indexes for dedup (evidence content hash, external message IDs,
  integration event IDs, relationship pairs, suppression scopes)
- JSONB only for genuinely unstructured payloads (claims, canon lists,
  integration payloads); everything else is relational
- constrained VARCHAR enums (no native PG enum migration pain)

## Job system

Jobs are rows in `job` with `state` (pending/running/succeeded/failed/dead),
`scheduled_at`, `attempts`, `max_attempts`, `backoff_base_seconds`,
`idempotency_key`, `locked_by`, and `error`. Claiming is atomic via
`FOR UPDATE SKIP LOCKED`. Failures retry with exponential backoff and become
DEAD after `max_attempts`. This survives frontend reloads and server restarts.

## Autonomy

Every consequential operation flows through
`security.approvals.authorize_action`:

```
actor → action → target → policy → permission → approval → execution → audit
```

- AUTO: research, classification, drafting, product/market analysis, low-risk
  intelligence updates.
- APPROVAL: sending email/SMS, pricing, discounts, scope, delivery dates,
  proposals, LinkedIn publishing, contractual statements.
- DENY: scraping circumvention, botting, fake engagement, unknown actions.
- Dashboard-only: financial transfer, credential changes, deleting history,
  security configuration (SMS alone can never authorize these).

Every decision writes an `AgentAction` and an `AuditEvent`. Attempting to bypass
the UI still hits this gate.

## Truth classes

`source_evidence` holds raw FACT/OBSERVATION records (deduplicated by content
hash per source type). `intelligence_claim` holds INFERENCE/HYPOTHESIS claims
with confidence and links to evidence via `claim_evidence`.

## Local AI

`integrations.ollama` provides a `ModelProvider` interface (upgradable without
rewriting GrowthOS) backed by Ollama. Every request records model, purpose,
input evidence IDs, structured output, latency, and failure state in
`model_request`. Target models: `qwen3.5:9b` (fast), `qwen2.5:32b` (deep
analysis), `qwen3-embedding:0.6b` (embeddings). No cloud AI is called silently.
