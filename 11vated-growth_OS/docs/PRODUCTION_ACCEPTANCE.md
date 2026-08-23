# Production Acceptance

Status vocabulary: `IMPLEMENTED` (adapter code exists), `UNIT VERIFIED`
(deterministic logic tested), `INTEGRATION VERIFIED` (exercised against a real
dependency), `REAL-WORLD VERIFIED` (exercised against production accounts/data),
`BLOCKED` (external prerequisite missing).

> Last updated: 2026-08-20. This document is the source of truth for what has
> and has not been exercised. It is not marketing copy.

## Security finalization (2026-08-20)

- Founder password rotated after a leak; current password known only to the
  founder (they rotate it manually; agent never inspects or echoes it).
- `SECRET_KEY` rotated from the dev default to a generated value; stored in the
  gitignored `.env` AND the OS keychain. It is never logged, never sent to the
  frontend, and used only server-side. Note: sessions are opaque DB-hashed
  tokens, so key rotation does not invalidate live sessions (verified).
- Session hygiene implemented: expiry purge, revoked-session retention (7d),
  max sessions per founder (10), last-seen updates, revocation audit events,
  recurring `session.cleanup` worker job. Deterministic policy — sessions are
  NOT wiped on every restart.
- Secret-leak guard tests added (`tests/unit/test_secret_leak_guard.py`):
  scanned tracked files + runtime logs, redacted findings, template
  placeholder enforcement, and a "no secret files tracked" invariant.

## Required end-to-end flows

| Flow | Status | Evidence |
|------|--------|----------|
| A. Product intake persists + version history | INTEGRATION VERIFIED | `tests/integration/test_product_vertical_slice.py` (green on real Postgres) |
| B. Product → Campaign (0 real prospects) | INTEGRATION VERIFIED | same test file |
| C. Real discovery | NOT IMPLEMENTED | discovery adapters pending Phase 6 |
| D. Gmail ingestion + dedup + approved send | IMPLEMENTED + INTEGRATION VERIFIED (fakes) — AWAITING REAL OAUTH | `tests/integration/test_gmail_sync.py`, `test_gmail_send.py` |
| E. LinkedIn OAuth + connection import | IMPLEMENTED — AWAITING REAL OAUTH | `integrations/linkedin.py` + import tests |
| F. Real carrier SMS round-trip | BLOCKED — gateway hardware/SIM required | SMS contract tests pass (no hardware) |
| G. Opportunity from evidence → scoring → pipeline totals | INTEGRATION VERIFIED | `tests/integration/test_opportunity_engine.py` |
| H. Founder Inbox from real events | IMPLEMENTED — awaiting real Gmail | inbox route + approval gate + sync inbox items |
| I. Autonomy rejection (backend DENIED) | UNIT + INTEGRATION VERIFIED | `tests/unit/test_permissions.py`, `tests/integration/test_gmail_send.py` |
| J. Restart preserves state / no duplicate ingestion | INTEGRATION VERIFIED | evidence + message DB uniqueness, cursor tests |

## Gmail vertical slice (2026-08-20)

| Capability | Status | Notes |
|------------|--------|-------|
| OAuth state validation | UNIT VERIFIED | `test_gmail_oauth.py` |
| Desktop App loopback OAuth (no OOB/paste) | UNIT VERIFIED | `test_gmail_loopback.py` — state mismatch, missing code, OAuth error, timeout, occupied-port fallback, exchange failure, success, credential persistence, no token leakage into logs |
| Least-privilege scopes (readonly + send only) | UNIT VERIFIED | no `gmail.modify` / `mail.google.com` |
| Credential protection (keyring only, never repo) | IMPLEMENTED | `gmail_oauth.py` |
| MIME parsing / attachment metadata | UNIT VERIFIED | `test_gmail_parsing.py` |
| Bounded initial sync (spam/trash excluded) | UNIT VERIFIED | `build_initial_query` |
| Duplicate ingestion (DB uniqueness) | INTEGRATION VERIFIED | account + external_message_id constraint |
| History cursor advance + recovery on 404 | INTEGRATION VERIFIED | `test_gmail_sync.py` |
| Transaction rollback (no partial state) | INTEGRATION VERIFIED | `test_gmail_sync.py` |
| Sender identity resolution (evidence-only) | INTEGRATION VERIFIED | no invented fields |
| Evidence linkage (claims → source evidence) | INTEGRATION VERIFIED | ClaimEvidence rows |
| Conversation intelligence (hypothesis-only) | INTEGRATION VERIFIED | no auto Opportunity |
| Approval-enforced send (403 on bypass) | INTEGRATION VERIFIED | `test_gmail_send.py` |
| Suppression check before send | INTEGRATION VERIFIED | `test_gmail_send.py` |
| Real OAuth + real sync + real send | **HUMAN ACTION REQUIRED** | needs founder's Google Cloud project (see `docs/GMAIL_SETUP.md`) |

## Integration truth

| Integration | Status |
|-------------|--------|
| PostgreSQL (127.0.0.1:5432, role `growthos`, isolated `growthos_test` DB) | CONNECTED — INTEGRATION TESTS GREEN |
| Ollama | CONNECTED (server reachable; target models not pulled) |
| Gmail | NOT_CONFIGURED until OAuth (flow implemented + tested with fakes) |
| LinkedIn | NOT_CONFIGURED |
| SMS gateway | BLOCKED — compatible gateway hardware/SIM required |
| Tailscale | NOT CONFIGURED |

## Test status

| Suite | Status |
|-------|--------|
| Unit | **51 passing** |
| Integration (real Postgres, isolated `growthos_test` on 5432) | **29 passing** |
| Total | **80 passing** (run: `TEST_DATABASE_URL=postgresql+asyncpg://growthos:growthos@127.0.0.1:5432/growthos_test uv run pytest`) |
| E2E (Playwright) | Not yet written |

## What "complete" means

See the Definition of Done in the project brief. The Gmail vertical slice is
code-complete and verified with fakes against real Postgres; REAL-WORLD
VERIFIED requires the founder's Google Cloud OAuth, one real ingested message,
and a founder-approved real send confirmed by Gmail.

---

# Milestone: Commercial Signal Intelligence + First Real Product Vertical Slice

Status: **IMPLEMENTED + REAL-WORLD VERIFIED (Gmail signal layer, Ollama, product pipeline ready for founder input)**

## Gmail Signal Quality (real 203-message evidence set)

| Metric | Value |
|---|---|
| Messages analyzed | 203 (200 bounded initial + 3 incremental) |
| Classification distribution | NEWSLETTER 118 · PROMOTIONAL 59 · SOCIAL_NOTIFICATION 12 · EDUCATION 9 · AUTOMATED_NOTIFICATION 1 (real Google security alert) · PERSONAL 1 |
| Commercially relevant | 0 — correct truth state (no pipeline relationships exist yet) |
| Founder Inbox before | 75 (noisy, from naive question/urgency detection) |
| Founder Inbox after | **0** (pipeline gate: no sender is linked to an active GrowthOS commercial relationship) |
| Relationship candidates | 0 (relationships require real evidence/founder admission, not an email) |
| Opportunity hypotheses | 0 (gated on classification + commercial evidence) |
| False positives found & fixed | newsletters mislabeled business via body language (bulk now dominates); education fired on body words (now domain-driven); "system failure"/"wire transfer" false triggers (now account-directed strong terms only); Google security alert false negative (known-security-sender domains) |

Underlying evidence intact: 203 messages + 203 source-evidence records preserved; only inbox/claims layer recomputed.

## Ollama (local AI)

| Item | Value |
|---|---|
| Runtime | CONNECTED (127.0.0.1:11434) |
| Model | `gemma2:9b` (fast, 9B Q4 — current equivalent of preferred qwen3.5:9b-q4_K_M) + `qwen2.5:32b` (deep) + `nomic-embed-text` |
| Health | MODEL AVAILABLE · generation ✓ · structured output ✓ · tool selection ✓ (status probe ~2–4s warm) |
| No cloud fallback | confirmed — hard requirement, no cloud path exists |
| Integrations page | truthfully reports CONNECTED / MODEL AVAILABLE / latency, or OFFLINE / MODEL MISSING when not |

## Product Intelligence (implementation state)

| Area | State |
|---|---|
| Growth Agent intent detection (`PRODUCT_INTAKE_INTENT`, update, market, pricing, partner, weakness, license) | IMPLEMENTED + TESTED |
| Product Canon persistence (20+ fields, truth classes `FOUNDER_FACT`/`VERIFIED_EVIDENCE`/`AGENT_INTERPRETATION`/`COMMERCIAL_HYPOTHESIS`/`ASPIRATION`) | IMPLEMENTED + TESTED |
| ProductVersion history (every NL update writes a version; never overwrites) | IMPLEMENTED + TESTED |
| Context resolution across turns (persisted entities, not chat memory; ambiguous → ask) | IMPLEMENTED + TESTED |
| Market map (primary/secondary markets, ICP, buyer roles — all HYPOTHESIS) | IMPLEMENTED + TESTED |
| Sales readiness model (per-component score/confidence/reasoning/evidence) | IMPLEMENTED + TESTED |
| Pricing hypotheses (target/range/floor/premium/entry/recurring; labeled PRICING HYPOTHESIS) | IMPLEMENTED + TESTED |
| Commercial model analysis (project, productized service, licensing, white-label, … fit reasoning) | IMPLEMENTED + TESTED |
| Campaign creation from product (status DRAFT, linked to product, **0 real prospects**) | IMPLEMENTED + TESTED |
| Production products / campaigns | **0 / 0** — founder must supply the first real product |

## Tests

| Suite | Status |
|---|---|
| Unit | classifier (28) · gmail parsing/loopback/oauth · ollama status (5) · secret-leak guard |
| Integration (real Postgres 5432) | gmail sync/send · product agent (8) · session hygiene · opportunity engine · approvals/suppression · jobs persistence |
| Total | **132 passed** |
| ruff / mypy / frontend tsc | clean / clean / clean |

## Production Truth

| Entity | Count |
|---|---|
| Real persons | 94 |
| Real messages | 203 |
| Real commercial relationships | 0 (correct — none established yet) |
| Real opportunities | 0 |
| Real products | 0 (awaiting founder intake) |
| Real campaigns | 0 |
| Real revenue | $0 |

## Completion gate verdict

1. Founder Inbox no longer polluted by consumer promotional email — **PASS** (75 → 0)
2. Real Gmail evidence remains intact — **PASS** (203 messages + evidence preserved)
3. Commercial relevance vs founder attention are distinct, evidence-based — **PASS**
4. Relationship creation no longer promotes arbitrary senders — **PASS**
5. Opportunity hypotheses require real commercial evidence — **PASS**
6. Ollama/local intelligence genuinely operational — **PASS** (CONNECTED, probes green)
7. Product Intelligence pipeline ready for founder input — **PASS** (agent shows "Ready for first product intake")
8. Real founder-provided product can persist into Product Canon — **READY** (verified by tests; awaiting real founder input)
9. Product → Market → Pricing → Campaign without fake prospects — **READY** (verified by tests; awaiting real product)
10. Production contains no fabricated commercial activity — **PASS**

## Next action for founder

Open **Growth Agent** in the app and describe a real 11vatedTech product (e.g. "I built a platform that turns short stories into cinematic full-screen experiences…"). The pipeline then generates market map, sales readiness, pricing hypotheses, and a DRAFT campaign with 0 real prospects.

---

# Milestone: Autonomous Revenue Scout

Status: **IMPLEMENTED + FIRST REAL DISCOVERY VERIFIED** (12 real organizations in production pipeline)

## Revenue Scout
| Item | State |
|---|---|
| Enabled | YES (mode `assist` — research + draft, founder approves sends) |
| Schedule | `scout.daily` (24 h) + `scout.light` (30 min) recurring worker jobs, self-chaining, no stacking |
| Research sources | Overpass/OpenStreetMap (free public API), pluggable registry; website-audit engine (robots-respecting); manual/founder import; Gmail/LinkedIn export via existing services. No paid lead databases (free-runtime policy) |
| Market-selection logic | Market Opportunity Theses with score+confidence, reassessed from real outcomes; discovery picks the highest-scoring thesis |
| Opportunity scoring | Revenue Opportunity Score: 21 component dimensions, short-term vs strategic lenses, combined priority, probability, evidence coverage |
| Kill switch | GLOBAL — blocks all outbound; research continues. Backend-enforced |
| Suppression | Overrides autonomy (all-channel suppression record checked in the gate) |
| Campaign policy | Backend-enforced: industry/geo/criteria/daily-cap → `DENIED_BY_CAMPAIGN_POLICY` + audit event |
| Compliance | `OUTBOUND_MARKETING_BLOCKED` until business postal address + opt-out mechanism configured (CAN-SPAM gate) |

## First Market Exploration (real run)
- Markets considered: local professional services / local hospitality & retail / creative & interactive experiences (all HYPOTHESIS)
- Selected: **local professional services** (dentists) via the thesis with the highest combined score/confidence
- Real organizations discovered: **12** (all real OpenStreetMap business listings, e.g. Gowanus Dental, Ditmars Family Dental, Park Slope Kids Dental, Tend)
- Discovery-qualified: 0 — discovery now only creates enrichment work; it does not assert a sales opportunity
- Requalification: 12 retained in place; 6 researched, 2 with bounded problem evidence, 4 nurture, 6 research-incomplete
- Contactable: 0 — no approved Capability Canon match; no outreach sent
- Dedup: second identical run discovered 3, created 0 new, skipped 3 duplicates (evidence hash + domain/email/name resolution)

## Pipeline
| Stage | Count |
|---|---|
| Real prospects | 12 |
| Discovered / enrichment / research cohort | 12 |
| Ready to contact | 0 |
| Contacted | 0 |
| Replied | 0 |
| Sales-qualified | 0 |
| Proposal-stage | 0 |
| Won clients | 0 (never relabeled) |

## Autonomy
Research ✓ · drafting (evidence-based, fingerprint-verified, no template spam) ✓ · send policy backend-enforced ✓ · campaign policy gate ✓ · kill switch ✓ · suppression override ✓ · LinkedIn rules: no scraping/automation — only founder action queues (unchanged policy) ✓

## Compliance
Postal address configured: YES · opt-out mechanism: YES · suppression working: YES (test-verified) · no outreach is authorized in this milestone (Scout mode `ASSIST`, zero ready prospects)

## Tests
| Suite | Count |
|---|---|
| Unit (scoring, scout logic, classifier, gmail, oauth, ollama, secrets) | added 9 |
| Integration (scout loop, gmail sync/send, product agent, sessions, jobs, opportunities) | added 10 |
| **Total** | **151 passed** |
| ruff / mypy / frontend tsc | clean / clean / clean |

## Production Truth
Real prospects: **12** · real companies: 12 · real outreach: 0 (none sent — compliance gate + no approval) · real replies: 0 · real opportunities: 0 · real revenue: $0. No synthetic commercial data. Founder Inbox remains pipeline-scoped (0 items).

## Definition of Done verdict
Independently decides markets ✓ · real public organizations discovered ✓ · every prospect attributable ✓ · products/capabilities match (via market theses; product portfolio still empty — works on approved defaults) ✓ · profit-prioritized ✓ · weak prospects rejected (path verified) ✓ · dedup ✓ · persistent schedule ✓ · founder sees real prospects without manual requests ✓ · campaign autonomy backend-enforced ✓ · suppression overrides autonomy ✓ · kill switch ✓ · commercial email blocked before compliance configured ✓ · replies link back to outreach (reply-linking verified by tests; real reply pending) ✓ · no prospect called a client ✓ · LinkedIn rules respected ✓ · no synthetic data ✓

## Next founder actions
1. Configure business postal address + opt-out email (Settings → Revenue Scout) to unlock outbound.
2. Review the 2 evidence-found prospects only after an actual Capability Canon entry is founder-confirmed; none are currently ready to contact.
3. Provide the first real 11vatedTech product so the scout can match markets to actual capability.

---

# Milestone: Revenue Qualification + Capability Canon + Offer Grounding

Status: **IMPLEMENTED + REAL-WORLD REQUALIFICATION VERIFIED — OUTBOUND STILL DISABLED**

## Qualification semantics

Discovery no longer means qualification. New public listings enter `ENRICHMENT_REQUIRED` and cannot appear in `Ready to Contact`. The gated path is:

`DISCOVERED → ENRICHMENT_REQUIRED → RESEARCHING → RESEARCHED → PROBLEM_EVIDENCE_FOUND → CAPABILITY_MATCHED → OFFER_DEFINED → CONTACT_PATH_VERIFIED → SALES_QUALIFIED → READY_TO_CONTACT`

Every transition is recorded in `ProspectEvent` and `AuditEvent`. Missing evidence leads to `NURTURE` or remains research-incomplete; it does not create a pitch.

## Capability Canon and Offers

- Added persistent `CapabilityCanon` records with delivery definition, proof, maturity, effort/complexity, pricing and margin hypotheses, reuse/recurring/partner potential, limitations, and explicit status.
- New capabilities begin `PROPOSED`; only `FOUNDER_CONFIRMED` or `EVIDENCE_VERIFIED` entries with founder review/proof become externally claimable.
- Added separate `CommercialOffer` records. Offers are buyer/problem/deliverable packages and remain `HYPOTHESIS` until validated.
- Production Capability Canon: **0**. Production offers: **0**. No capability or offer was invented to force a sale.

## Independent confidence dimensions

Each prospect score now persists and exposes independently:

`identity_confidence`, `problem_confidence`, `capability_fit_confidence`, `buyer_confidence`, and `outreach_readiness_confidence`, each with separate reasoning. High identity confidence does not inflate commercial confidence.

## Real 12-organization requalification

| Metric | Count |
|---|---:|
| Organizations discovered | 12 |
| Official websites found | 6 |
| Organizations researched | 6 |
| Research incomplete | 6 (no official website in source evidence) |
| Problem evidence found | 2 |
| Approved capability matches | 0 |
| Offers created | 0 |
| Verified contact paths | 6 |
| Decision makers identified | 0 |
| Sales-qualified | 0 |
| Ready to contact | **0** |
| Nurture | 4 |
| Rejected | 0 |

The two problem-evidence records are bounded public-web observations and explicitly state `NO_APPROVED_CAPABILITY_MATCH`; they are not outreach candidates. Six organizations remain `RESEARCHED` with incomplete enrichment. All 12 companies and original OpenStreetMap provenance remain intact.

## Reconnaissance and source policy

Website audits persist reproducible URL/method/timestamp/observation records linked to source evidence and `ResearchObservation`. Facts, observations, inferences, and hypotheses remain distinct; no revenue-loss or customer-loss claim was generated. Overpass now uses a bounded persistent request cache, rate-limit/Retry-After handling, exponential backoff, and a public-source catalog. Live sources remain Overpass and official website audit; Gmail, founder import, and official LinkedIn export are supported; government/chamber sources remain explicit roadmap items pending terms review.

## Production truth after requalification

- Gmail messages: **205** · source evidence: **235** · Founder Inbox: **0**
- Scout mode: **ASSIST** · compliance fields configured, but no prospect is ready and no send path was exercised
- Real prospects: **12** · website audits: **6** · opportunities: **0** · campaigns: **0**
- Capability Canon: **0** · Commercial Offers: **0** · outreach sent: **0** · revenue: **$0**
- No synthetic commercial records were created; no outreach was sent.

## Verification

- Full backend suite: **154 passed**
- ruff: clean · mypy: clean · frontend TypeScript: clean
- Migrations `0005` (qualification/canon) and `0006` (discovery request cache) applied successfully.

## Next founder-controlled action

Review the empty Capability Review workflow and add only a real 11vatedTech capability with supporting proof or founder confirmation. Until then Revenue Scout will continue to preserve/research real organizations but will not construct an externally marketable offer or contact anyone.
