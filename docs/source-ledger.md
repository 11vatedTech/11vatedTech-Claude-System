# 11vatedTech Source Ledger

Last updated: 2026-08-15

## Adopted external capabilities

Source repository: https://github.com/decolua/9router
Observed `master` revision: `699edac3273e13d4744bc46f6082618f08560702`
Observed license: MIT

| Skill | Source repository | Revision | License | Purpose | Installed scope | Modifications | Security notes | Evaluation status |
|---|---|---|---|---|---|---|---|---|
| 9router | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | 9Router setup and capability index | user/global | none | Markdown skill only; no installer executed; no secrets stored | installed, health endpoint verified |
| 9router-chat | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | 9Router chat/code generation | user/global | none | cURL examples require key; key not stored | installed, `/v1/models` discovered, chat smoke passed |
| 9router-image | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | Image generation | user/global | none | Writes output files only when user requests generation | installed, image models discovered |
| 9router-tts | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | Text-to-speech | user/global | none | Writes audio output only when requested | installed, TTS models discovered |
| 9router-embeddings | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | Embeddings/RAG/vector search | user/global | none | Sends text to configured 9Router providers | installed, embedding discovery passed, free-model smoke passed |
| 9router-web-search | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | Web search through 9Router | user/global | none | Network access through configured providers | installed, no web models available at discovery time |
| 9router-web-fetch | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | URL fetch to markdown/text/html | user/global | none | Fetches external URLs through configured providers | installed, no web models available at discovery time |
| 9router-stt | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | Speech-to-text | user/global | none | Sends audio to configured provider; no models at discovery time | installed, STT category empty |
| 9router-video | https://github.com/decolua/9router | `699edac3273e13d4744bc46f6082618f08560702` | MIT | Async video generation | user/global | none | May require connected xAI account/provider; output download only when requested | installed, endpoint not job-tested |

## Reviewed but not adopted wholesale

| Source | Status | Reason |
|---|---|---|
| https://github.com/anthropics/claude-plugins-official | inspected | Official marketplace exists; Apache-2.0 repo; plugin entries may include MCP servers/commands/hooks/external services, so no blind bulk install |
| bundled `claude-api` skill | used as guidance only | Official current API/Managed Agents guidance loaded; no files copied |
| Anthropic bundled/available skills (`frontend-design`, `pdf`, `docx`, `xlsx`, `pptx`, `security-review`, `dataviz`) | preserved as available skills | Already available through Claude Code; no duplicate custom skill needed |

## Update method

1. Re-query upstream repository or marketplace.
2. Inspect diff before adoption.
3. Re-run security gate: scripts, hooks, MCP, commands, dependencies, network, filesystem, credentials, destructive behavior.
4. Update installed file only after review.
5. Record revision, modifications, and validation status here.

## Known ledger gaps

- 9Router skills were installed from `master` raw URLs. Future updates should pin/fetch exact raw URLs by commit SHA before modifying local copies.


## Phase II pinning status

Canonical repo stores local copies under `plugin/skills/9router*` and records tested revision `699edac3273e13d4744bc46f6082618f08560702`. Use `scripts/update/compare_pinned_sources.py` to verify copies against pinned raw GitHub content before updating.
