# L5 Review Record — 2026-08-18

Independent evidence audit for capabilities elevated to L5. Each entry lists
what was verified, the evidence trail, and the documented limitations. This
record is one of the six L5 requirements (enforced by
`scripts/validate/l5_evidence.py`).

Review method: evidence audit — every claim was re-derived from artifacts and
re-run gates, not from the capability registry's own text. Flagship releases
additionally require the `11vt-independent-reviewer` agent pass per the
system's own doctrine.

---

## pixel-diff — L5

- **Real implementation**: `magick compare -metric AE` via
  `scripts/media/vtmedia/image_tools.py`, resolved through `resolve_tool`
  (Program Files fallback). Verified running against the real installer path.
- **Real use**: image-test reports 521,324 differing pixels between a gradient
  and its upscale; loop-continuity QA uses it (AE=0 seamless, AE=586 broken).
- **Failure test**: `scripts/validate/failure_tests.py` proves two different
  images are flagged not-equivalent (visual_equivalence_claim=False).
- **Regression**: `media_gate` in system_regression.py.
- **Documented limitations**:
  - AE is a count, not a perceptual metric; identical AE ≠ perceptual
    equivalence. Use PSNR/SSIM for perceptual similarity and always pair with
    human/visual review for artistic judgment.
  - Requires ImageMagick 7; the ffmpeg PSNR fallback is lower fidelity.
  - `magick compare` returns code 1 for "images differ" — callers must treat
    returncode 1 as a valid (non-error) result.

## blender-bridge — L5

- **Real implementation**: 15 schema-validated structured ops
  (`blender_ops.py` + `op_runner.py`), session-.blend chaining, structured
  JSON output with explicit health.
- **Real use**: op suite produced a valid GLB (73,104 bytes, structurally
  validated), a Cycles preview render, an 8-frame turntable, a 1s H.264
  motion preview, and loop-QA frames.
- **Failure test**: corrupt/truncated GLB rejected by the structural
  validator; broken-loop detected by loop QA; Blender 5.x layered-action API
  handled (fcurves moved to layers/strips/channelbags).
- **Regression**: `blender_ops` gate in system_regression.py (SKIP, not silent
  pass, when Blender is absent).
- **Documented limitations**:
  - Structural GLB validation is a subset of the Khronos glTF-Validator; it
    checks container/chunk/JSON integrity, not full spec conformance. Install
    the Khronos validator for release-grade conformance.
  - Cycles renders at preview resolutions/samples are for QA, not final
    delivery; final renders need explicit quality settings.
  - Ops run per-session; state persists only through the session .blend.
  - GPU utilization during renders is not yet captured (open gap).

## animation-qa — L5

- **Real implementation**: loop-continuity QA (render first/last frames →
  pixel diff + PSNR) and a bone/object velocity foot-slide heuristic in
  `op_runner.py`; turntable → H.264 motion preview via ffmpeg.
- **Real use**: seamless 360° loop measured AE=0; drifting probe flagged
  (0.087/frame > threshold); broken half-rotation loop detected (AE=586).
- **Failure test**: `animation.broken_loop` probe asserts seamless=False is
  detected; `slide_probe` asserts the flag fires on drift.
- **Regression**: `blender_ops` gate.
- **Documented limitations**:
  - Loop continuity via endpoint pixel diff verifies *seamlessness*, not
    *quality of motion*. Pose/silhouette/timing/spacing are artistic checks
    that require video evidence and human/independent review.
  - Foot-slide heuristic is a single-contact-bone velocity threshold; it does
    not model contact phases, IK, or multi-contact feet. Use it as a screen,
    not a verdict.
  - Thresholds are global constants; per-rig calibration is a future step.

## global-sync — L5

- **Real implementation**: `sync_to_claude.py` with timestamped pre-sync
  backup, deployment manifest (version + sha256 inventory), `--dry-run`,
  `--rollback`, `--list`, stale `11vt-*` detection.
- **Real use**: two real deployments (20260818-203656, 20260818-203830) to
  `~/.claude`; verified from an unrelated blank project that Claude
  auto-discovers 20 global skills + 8 agents; global validator reports
  29 skills / 8 agents / pointer / no secrets / 9Router healthy.
- **Failure test**: `--rollback <nonexistent>` errors (no_manifest);
  unknown license/source rejected by the vault.
- **Regression**: `validate_capability_installation.py` (repo-owned) +
  failure tests.
- **Documented limitations**:
  - Sync does not manage `~/.claude/settings.json` or hooks; those remain
    manual to preserve working configuration.
  - Stale `11vt-*` removal requires `--prune` (never automatic).
  - Deployment manifests live under `~/.claude/11vatedtech/deployments/`;
    they are not versioned in the repo.

## rollback — L5

- **Real implementation**: `--rollback <id>` restores every managed file from
  the deployment's timestamped backup and marks the manifest rolled_back.
- **Real use**: round-trip executed — 42 files restored, old entrypoint
  verified, then re-applied.
- **Failure test**: unknown deployment id errors instead of silently
  succeeding.
- **Regression**: failure test wired into the regression gate.
- **Documented limitations**:
  - Rollback restores *managed* files (skills/agents/capability-system); it
    does not revert settings.json or manual edits.
  - Backups are on the same disk (OneDrive); a disk-level failure would take
    the backups too. Off-machine backup is a future step.
  - Rollback is a restore, not a diff-merge; concurrent manual edits to the
    same files between deploy and rollback are lost.

---

## Honest status

- L5 was 0 before this session; these five are now L5 with all six
  requirements. They were selected because their evidence chains are complete
  and their failure paths are proven.
- asset-export, asset-direction, asset-vault, regression-gate,
  global-validation remain L4 with complete failure tests, pending the same
  review discipline — L5 is kept scarce on purpose.
- The system still has no L5 *creative* capability (design, VFX, cinematic,
  audio); those are the next ascension frontier.
