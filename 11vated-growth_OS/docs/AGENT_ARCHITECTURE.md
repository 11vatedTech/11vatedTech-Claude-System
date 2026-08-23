# 11vated Growth Intelligence — Agent Architecture

The central agent, "11vated Growth Intelligence", operates across the
commercial graph. Its fundamental question:

> What valuable problem does this person or organization have that 11vatedTech
> can genuinely solve, and what is the highest-value professional path toward
> creating that value and developing the relationship?

## Components

1. **Model provider** (`integrations/ollama.py`) — a swappable interface over
   Ollama. Fast route `qwen3.5:9b`, deep-analysis route `qwen2.5:32b`,
   embeddings `qwen3-embedding:0.6b`. Every request logs model, purpose,
   evidence IDs, structured output, latency, and failure state.
2. **Structured output** — the model returns JSON validated against Pydantic
   schemas; retries once with the validation error as feedback.
3. **Tool runtime** — commercial tools (research, classify, draft, score) are
   ordinary services with deterministic guards.
4. **Memory retrieval** — evidence-linked: the agent reads `source_evidence`,
   `intelligence_claim`, the product canon, and the network graph.
5. **Policy gate** — every consequential tool call passes
   `security.approvals.authorize_action` (see `AUTONOMY_POLICY.md`).

## Natural networking

The agent recognizes non-sales roles (referral source, agency partner,
white-label partner, founder peer, distribution partner, etc.) and maintains a
**Relationship Thesis** per meaningful relationship. Relationship strength
derives only from real events (replies, meetings, referrals, completed work,
silence) — never an arbitrary percentage.

## Founder command plane

Natural-language commands arrive via the PWA, Gmail, or SMS (when hardware
exists) and are resolved to the same commercial context. High-risk actions
require dashboard confirmation regardless of channel.
