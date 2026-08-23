# Testing

## Layers

- **Unit** (`tests/unit/`): deterministic logic only — no database. Always runs.
- **Integration** (`tests/integration/`): against an **isolated** test database
  (`TEST_DATABASE_URL`, default `growthos_test`). Skips cleanly when the DB is
  unreachable. Fixtures are `TEST_ONLY` and never touch production storage.
- **Contract** (`tests/contract/`): adapter protocol contracts (SMS webhook
  shape, integration payloads) without live services.
- **E2E** (`tests/e2e/`): Playwright against the real UI (to be added).

## Commands

```bash
uv sync                          # install backend deps
uv run pytest tests/unit -q      # unit tests
uv run pytest tests/integration -q   # integration (needs TEST_DATABASE_URL)
uv run ruff check src tests      # lint
uv run mypy src/growthos         # type check

cd apps/web && pnpm install && pnpm build   # frontend
```

## Isolation guarantee

Integration fixtures are created only inside `growthos_test`. The production
`growthos` database is never migrated, dropped, or seeded by the test suite.

## What's tested today

- pipeline / outreach / campaign state machines
- opportunity scoring + confidence degradation
- autonomy policy (AUTO / APPROVAL / DENY, SMS cannot authorize high-risk)
- suppression ledger
- cost guard (FREE_RUNTIME_POLICY)
- password hashing + strength policy
- job backoff, registry, claim/complete/retry/dead-letter (integration)
- evidence truth-class invariants + content-hash dedup
- SMS sender classification + reply composition (contract)
- LinkedIn connections CSV normalization
- product intake persistence + version history (integration)
- opportunity → scoring → revenue metrics (integration)
- approval request/decision + inbox creation (integration)
