# LinkedIn Setup

Status: **IMPLEMENTED — AWAITING REAL OAUTH / product approval**

## What exists

`integrations/linkedin.py` implements the official-API-only approach, the
connections-archive CSV importer (normalize name/company/position/date/email/
URL, dedup), and the capability matrix (see
[`LINKEDIN_CAPABILITY_MATRIX.md`](LINKEDIN_CAPABILITY_MATRIX.md)).

## Founder actions required

1. Create a LinkedIn developer application.
2. Request the products you actually need (e.g. Sign In with LinkedIn).
3. Configure redirect URIs.
4. Run `growthos setup linkedin --authorize` to store client credentials
   securely.
5. Enumerate the **actual** permissions granted (never assume).

## Connection import

Download your official LinkedIn connections archive, then:

```bash
growthos linkedin import-connections <file.csv>
```

This normalizes and deduplicates into the Network Graph and is the foundation
of networking intelligence.

## Prohibited

No authenticated-page scraping, no automated connection requests, no bulk DMs,
no fake engagement, no fake accounts. Founder-assisted LinkedIn actions are
queued as cards; the founder performs the action and GrowthOS records the
result afterward.
