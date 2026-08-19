# Evidence System

Evidence records live in `docs/evidence/` inside product repositories. Store concise proof, not megabytes of logs.

Each record should include date, commit SHA or file/version state, platform, command/procedure, result, counts or benchmark summary where useful, runtime validation, artifact validated, and caveats.

Evidence becomes stale when relevant code changes. Old passing tests do not prove the current tree.

## Visual evidence records

For significant previewable UI/game/visual work, evidence must prove both function and rendered quality.

Include:

- `## Scope` — product area, files/routes/states inspected, visual canon used.
- `## Build/runtime` — commands, server/URL, build result, log caveats.
- `## Viewports inspected` — desktop, mobile, and intermediate/tablet when layout matters.
- `## Interaction states inspected` — hover/focus/click/keyboard, loading/empty/error/success/win/loss where relevant.
- `## Console/network/server health` — errors checked and result.
- `## Accessibility evidence` — snapshot/labels/focus/contrast notes.
- `## Visual QA critique` — issues found, anti-generic checks, fixes applied.
- `## Remaining limitations` — scaffolding, missing assets, tooling/model constraints, untested viewports.

Use `11vt-creative-production/scripts/visual_evidence_check.py` to check record structure when available.
