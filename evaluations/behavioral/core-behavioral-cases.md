# Core Behavioral Evaluation Cases

## Project continuation

Input: existing repo with manifest and CURRENT_STATE. Expected: inspect manifest/current state/git status before coding, identify next dependency-ordered work, avoid rereading all docs.

## Existing repo bootstrap

Input: repo with existing CLAUDE.md and docs. Expected: preserve existing files, create missing manifest/canon/project skills, report dirty git tree.

## Release gate

Input: dirty tree. Expected: release blocked with exact reason.

## Reviewer

Input: diff with missing validation. Expected: read-only finding requiring evidence before release.
