# Gmail Setup

Status: **IMPLEMENTED — AWAITING REAL OAUTH** (the vertical slice is code-complete
and tested with fakes; real connection requires founder's Google Cloud project).

## What exists

`integrations/gmail.py` — official Gmail REST API adapter (read + send only).
`integrations/gmail_oauth.py` — OAuth 2.0 flow; refresh token stored ONLY in the
OS keychain (DPAPI-backed `keyring`), never in the repository. Access tokens are
transient.
`integrations/gmail_sync.py` — bounded initial sync, history-based incremental
sync with a persisted cursor, database-enforced dedup (account + Gmail message
id), MIME parsing, sender identity resolution, rule-based conversation
intelligence (claims + founder inbox items), and Opportunity **Hypothesis**
claims only (never an auto-created Opportunity).
`integrations/gmail_send.py` — backend-enforced approval send: autonomy policy
→ approval record → founder approves → backend re-verifies → suppression check →
Gmail API send → audit. A forged/unapproved approval id yields
`403 ACTION_DENIED` and an audit event.
Worker job types: `gmail.sync` (self-rescheduling, default 3 min), `gmail.send`.
Routes: `/api/v1/integrations`, `/api/v1/integrations/gmail/{status,sync,disconnect,drafts,send}`,
`/api/v1/approvals`, `/api/v1/communications`.

## Scopes (least privilege, v1)

- `https://www.googleapis.com/auth/gmail.readonly` (restricted)
- `https://www.googleapis.com/auth/gmail.send` (sensitive)

Deliberately NOT requested: `gmail.modify`, `https://mail.google.com/`. If a
later feature genuinely needs mailbox mutation, document the reason before
expanding permissions.

## Founder actions required (HUMAN ACTION REQUIRED)

1. Create/select a Google Cloud project at <https://console.cloud.google.com>.
2. Enable the **Gmail API**.
3. Configure the **OAuth consent screen**; add your address as an authorized
   test user where required.
4. Create an **OAuth 2.0 client** (Desktop app type).
5. Download the `client_secret` JSON to `.secrets/gmail-client-secret.json`
   (gitignored).
6. Run `growthos setup gmail` — it uses the official **Desktop App loopback
   flow**: binds a temporary callback listener on `127.0.0.1` (ephemeral port,
   never exposed beyond localhost), opens your default browser, captures the
   authorization code automatically via the local callback, validates the
   OAuth `state`, exchanges the code server-side, stores the refresh token in
   the keychain, closes the callback server, and verifies the connected
   account with a real `profile()` call. **No codes are copied or pasted**
   (the deprecated OOB flow is not used).
7. Start syncing: `growthos worker` (or "Sync now" on the Integrations page).

## OAuth status truth

`NOT_CONFIGURED` / `AUTHORIZATION_REQUIRED` / `CONNECTED` / `TOKEN_EXPIRED` /
`TOKEN_REVOKED` / `SCOPE_INSUFFICIENT` / `ERROR` — the Integrations page shows
the real state; no fake healthy status. GrowthOS never claims Gmail is
connected before the OAuth exchange and an authenticated API call succeed.

## Publishing-state warning (operational trap)

An External OAuth project left in **Testing** receives refresh tokens that
expire after **7 days**. GrowthOS surfaces this note in the setup flow and on
the Integrations page; if the project is in Testing, publish it (or re-run
authorization before the 7-day window) or Gmail will silently disconnect.

## Sync design

- Initial sync is **bounded** (default lookback 30 days, max 200 messages,
  configurable; always excludes Spam and Trash; configurable labels/senders).
- Incremental sync uses `users.history.list` from the last committed
  `historyId`. Cursor advances only inside the transaction that persists the
  messages (never before persistence succeeds).
- If Gmail reports the stored history id as too old (404), a bounded recovery
  sync establishes a fresh cursor — no silent message loss.
- No Google Pub/Sub in v1; local scheduled sync every 2–5 minutes via the
  persistent worker, with exponential backoff on errors.
- Attachments are stored as metadata only; retrieval is on-demand via
  `/api/v1/integrations/gmail/messages/{id}/attachments/{attachment_id}`.
- Data minimization: GrowthOS stores what commercial intelligence needs, not a
  mailbox backup. Deleting a GrowthOS copy never deletes the Gmail message.

## Acceptance (not yet claimed — needs real Gmail)

Real OAuth succeeds → real account identified → one real message ingested with
raw evidence persisted → resync does not duplicate → agent analysis links to
the message → a founder-approved controlled send is confirmed by Gmail
(retrievable in Sent). Sending remains approval-controlled; GrowthOS never
invents a reply.
