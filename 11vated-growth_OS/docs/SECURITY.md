# Security

## AuthN

Single-founder authentication. Argon2id password hashing. Opaque session tokens
stored as SHA-256 hashes in `session` (revocable), delivered via HttpOnly,
SameSite=Lax cookies (Secure in production). First-boot `POST /auth/bootstrap`
is refused once a founder exists.

## CSRF

Double-submit cookie: mutating requests must send `X-CSRF-Token` matching the
`growthos_csrf` cookie. The session cookie itself is SameSite=Lax.

## Secrets

No secrets in Git. OAuth refresh tokens and gateway API keys live in the OS
keychain (Windows Credential Manager) via `keyring`, with an encrypted file
fallback keyed by `SECRET_KEY`. OAuth client secrets are never placed in
frontend bundles.

## Least privilege

- Gmail scopes: read-only + modify (drafts/labels) + send (approval-gated).
- LinkedIn: only officially approved products/scopes; no scraping or botting.
- SMS gateway: API-key-authenticated local/private API; founder number allowlist.

## Autonomy + audit

Every consequential operation resolves through `authorize_action`, records an
`AgentAction`, and writes an `AuditEvent`. Backend enforcement means bypassing
the UI still fails.

## Network posture

Only the authenticated GrowthOS app is remotely reachable (Tailscale). Never
expose PostgreSQL, Ollama, workers, or admin ports. SQL is parameterized via
SQLAlchemy. Input is validated with Pydantic.

See [`THREAT_MODEL.md`](THREAT_MODEL.md).
