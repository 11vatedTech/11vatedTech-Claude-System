# Core Behavioral Evaluation Cases

## Project continuation

Input: existing repo with manifest and CURRENT_STATE. Expected: inspect manifest/current state/git status before coding, identify next dependency-ordered work, avoid rereading all docs.

## Existing repo bootstrap

Input: repo with existing CLAUDE.md and docs. Expected: preserve existing files, create missing manifest/canon/project skills, report dirty git tree.

## Release gate

Input: dirty tree. Expected: release blocked with exact reason.

## Reviewer

Input: diff with missing validation. Expected: read-only finding requiring evidence before release.

## High-fidelity visual request

Input: “make this app look world-class/high-fidelity, not generic.” Expected: route through creative-production/design-director, establish concept and visual grammar before components, reject ungrounded neon/glass/dashboard defaults, require rendered inspection when previewable.

## Visual work without evidence

Input: UI implementation claims “done” but no screenshot/snapshot/browser inspection. Expected: distinguish implemented/build-passed from visually inspected; require visual evidence before completion claim.

## Asset-heavy concept

Input: card game, cinematic site, 3D product, or illustrated interface with primitive placeholder art. Expected: identify asset requirements, placeholder risks, licensing/provenance, and production route rather than polishing primitives as final.

## Motion-heavy concept

Input: request for animation or cinematic interaction. Expected: define motion purpose, timing, state relationship, reduced-motion behavior, and performance risk; do not animate as decoration.

## Should not over-trigger creative pipeline

Input: backend bug fix, tiny regex, dependency update, CLI flag change. Expected: no creative-production route unless user explicitly asks for visual identity or UI fidelity.
