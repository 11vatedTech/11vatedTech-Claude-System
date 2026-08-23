# Threat Model

Assets: commercial data, founder identity, OAuth tokens, AI reasoning, the
founder's time.

## Threats & mitigations

| Threat | Mitigation |
|--------|------------|
| OAuth token theft | OS keychain, never committed, never in frontend bundles |
| Session hijacking | HttpOnly + SameSite=Lax + Secure cookies, revocable sessions |
| CSRF | double-submit CSRF token on all mutating requests |
| Unauthorized agent action | backend policy engine, fail-closed unknown actions, audit |
| SMS spoofing / non-founder SMS | founder number allowlist + dashboard-only high-risk actions |
| Data loss on restart | PostgreSQL persistence, migrations, atomic job claiming |
| Duplicate ingestion | unique indexes + idempotency keys (messages, evidence, jobs) |
| Paid-service creep | FREE_RUNTIME_POLICY cost guard, fail-closed unknown connectors |
| Public exposure of infra | Tailscale-only app access; DB/Ollama never public |
| SQL injection | SQLAlchemy parameterization + Pydantic validation |
| Suppressed contacts re-contacted | suppression ledger consulted by every adapter |
| Bill shock / cloud AI | no silent cloud AI; Ollama is the default provider |

Residual risk: a compromised founder device can impersonate the founder —
mitigated by strong login, least-privilege scopes, and audit review.
