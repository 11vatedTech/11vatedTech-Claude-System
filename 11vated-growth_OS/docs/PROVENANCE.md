# Provenance

Reality is separated from reasoning using four truth classes:

| Class | Meaning | Stored as |
|-------|---------|-----------|
| FACT | directly supplied or retrieved information | `source_evidence` |
| OBSERVATION | directly observable from evidence | `source_evidence` |
| INFERENCE | agent conclusion derived from evidence | `intelligence_claim` |
| HYPOTHESIS | commercial proposition not yet validated | `intelligence_claim` |

## Rules

1. Raw evidence (`source_evidence`) may only be FACT or OBSERVATION. The
   service raises on INFERENCE/HYPOTHESIS.
2. Every INFERENCE/HYPOTHESIS links to supporting evidence via `claim_evidence`.
3. Raw evidence is never overwritten by an interpretation; re-ingestion dedups
   by (source type, content hash).
4. Product claims carry a `tag` (`FOUNDER_FACT`, `VERIFIED_EVIDENCE`,
   `AGENT_INTERPRETATION`, `COMMERCIAL_HYPOTHESIS`, `ASPIRATION`).
5. A hypothesis is promoted only through evidence, never silently.

Example: a source email sentence is a FACT; "strong buying signal" is an
INFERENCE; "possible custom frontend engagement" is a HYPOTHESIS — each linked
back to the source message.
