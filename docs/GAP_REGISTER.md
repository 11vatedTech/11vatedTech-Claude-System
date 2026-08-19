# Foundry Gap Register

Gaps are recorded only where there is evidence. Status reflects the last
verification (2026-08-18, Genesis session). This file is the authoritative
register; the reference workspace copy is superseded.

| # | Gap | Evidence | Impact | Status |
|---|-----|----------|--------|--------|
| 1 | Tool detection ignores `C:\Program Files` installs | Doctor used `shutil.which` only; reported ImageMagick, Inkscape, Blender as `missing` though all three are installed | Real pixel diff, SVG rasterization, and the Blender bridge were silently disabled | **Fixed** in 0.4.0 (`resolve_tool` + `WINDOWS_TOOL_HINTS`); doctor now reports all three PASS |
| 2 | `compare_images` degraded to hash-only when ImageMagick undetected | Code path returned `visual_equivalence_claim: False` | No real visual regression possible | **Fixed** in 0.4.0 (`magick compare -metric AE` with parsed absolute error; ffmpeg PSNR fallback) |
| 3 | SVG rasterization had no Inkscape-free fallback | `vector_tools.rasterize` returned `inkscape_missing` and failed `vector-test` | Vector test suite could not pass on this machine | **Fixed** in 0.4.0 (ImageMagick fallback; verified end-to-end, Inkscape provider PASS) |
| 4 | Media toolchain not part of the regression gate | `system_regression.py` never ran `scripts/media/11vt_media.py` | A broken media layer would not fail CI | **Fixed** in 0.4.0 (`check_media` gate runs image/vector/video/audio) |
| 5 | `VERSION` (0.2.1) diverged from `CHANGELOG.md` (0.3.0) | Both files inspected | False version signal | **Fixed** in 0.4.0 (VERSION = CHANGELOG = 0.4.0) |
| 6 | Root `tools/` directory was dead, unreferenced shells | `tools/__init__.py` empty; `tools/elevenvt_media` only a version string; no imports anywhere | Abandoned duplicate structure | **Fixed** in 0.4.0 (replaced with `tools/README.md` pointer) |
| 7 | Routing evaluation is shallow | `skill_trigger_eval.py` only checked that expected skill *names exist* | Routing regressions not detected | **Fixed** in 0.4.0 (`scripts/validate/routing_eval.py`: coverage, overtrigger, dangling-route checks; mutation-tested) |
| 8 | Local generative media absent | ComfyUI / whisper / piper not installed; Blender now available | STT/TTS/upscale/generation remain degraded-by-design | **Open** (documented degraded in ontology L0/L2, not faked) |
| 9 | Global `~/.claude/11vatedtech/capability-system` docs drifted from repo | Dry-run sync reported 5 stale capability-system files | Global capability records could contradict the repo | **Fixed** in 0.4.0 (deployment manifest + sync now covers capability-system; drift detected and corrected) |
| 10 | Global deployment had no backup/manifest/rollback | `sync_to_claude.py` overwrote in place with `dirs_exist_ok=True`, no record | A bad sync could not be rolled back | **Fixed** in 0.4.0 (timestamped backup, deployment manifest, `--dry-run`, `--rollback`, `--list`, stale detection) |
| 11 | Capability ontology and maturity baseline were prose-only | No machine-readable capability inventory with maturity levels | Maturity claims could not be verified | **Fixed** in 0.4.0 (`config/capability-ontology.json` + `scripts/validate/ontology_check.py`: every provider resolves, every evidence pointer exists) |
