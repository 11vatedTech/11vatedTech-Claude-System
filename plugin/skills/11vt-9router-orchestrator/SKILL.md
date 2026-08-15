---
name: 11vt-9router-orchestrator
description: 11vatedTech 9Router orchestration capability. Use when routing tasks through 9Router, selecting models/capabilities, checking NINEROUTER_URL, using chat/image/TTS/STT/embeddings/search/fetch/video, or comparing available model options.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech 9Router Orchestrator

Use 9Router as a dynamic capability router, not a hardcoded model list.

## Safety

- Never print `NINEROUTER_KEY`.
- Do not embed credentials in scripts or skills.
- Check key presence by set/unset or length only.
- Query model discovery before choosing when task depends on actual local availability.
- Prefer free/local/private capabilities when viable and consistent with quality.

## Discovery endpoints

Base defaults to `NINEROUTER_URL` or `http://127.0.0.1:20128`.

- Health: `/api/health`
- Chat models: `/v1/models`
- Image: `/v1/models/image`
- TTS: `/v1/models/tts`
- Embeddings: `/v1/models/embedding`
- Web: `/v1/models/web`
- STT: `/v1/models/stt`
- Vision/image-to-text: `/v1/models/image-to-text`
- Metadata: `/v1/models/info?id=<model-id>`

## Routing criteria

When metadata exists, consider:

- modality
- context window
- reasoning quality
- coding quality
- latency
- local availability
- cost
- reliability
- fallback support
- privacy
- task complexity

## Task routing

- Architecture/deep reasoning: strongest reasoning model available.
- Coding: strongest repository-scale coding model available.
- Fast repetitive analysis: efficient model with enough quality.
- Visual ideation: image model.
- Visual analysis: vision/image-to-text model.
- Research: web search/fetch if available; otherwise normal web tools.
- Semantic retrieval: embedding model.
- Audio: TTS/STT models.
- Video: async video job flow when available.

## Multi-model intelligence

For important decisions, use multiple models for independent critique, but synthesize by evidence. Majority vote is not truth.

## Current observed environment on 2026-08-15

- Health endpoint responded `{"ok":true}` at localhost/127.0.0.1:20128.
- `/v1/models` returned 329 chat/combo entries.
- Image returned 4 models.
- TTS returned 5 models.
- Embeddings returned 8 models.
- Web returned 0 models.
- STT returned 0 models.
- Image-to-text returned 2 models.
- User settings route Anthropic traffic to `http://127.0.0.1:20128/v1` with non-secret token string `sk_9router`.

Use `references/routing-record-template.md` to document routing decisions.
