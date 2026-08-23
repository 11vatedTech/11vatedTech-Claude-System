# Operations

## Daily

```bash
uv run growthos doctor        # environment health
uv run growthos api           # API on 127.0.0.1:8000
uv run growthos worker        # persistent job worker
cd apps/web && pnpm dev       # PWA on :5173
```

## Database

```bash
uv run growthos setup database   # interactive role/db provisioning
uv run growthos migrate          # apply migrations
```

The production DB is `growthos`; tests use the isolated `growthos_test` DB.

## Local AI

```bash
uv run growthos setup ai         # inspect models
uv run growthos setup ai --pull  # pull qwen3.5:9b + qwen3-embedding:0.6b
```

## Remote access

Install Tailscale on the workstation and the founder phone; access GrowthOS at
the workstation's Tailscale IP. Never expose PostgreSQL/Ollama/workers
publicly.

## Integration health

Check `GET /api/v1/health/state` for real counts. Integration status is in
`docs/PRODUCTION_ACCEPTANCE.md`. Errors are surfaced in the Founder Inbox and
the job table (`/activity`), never hidden.
