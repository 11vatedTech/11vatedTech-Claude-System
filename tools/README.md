# tools/

This directory previously held empty, unreferenced scaffolding. The canonical
media toolchain lives in `scripts/media/`:

- `scripts/media/11vt_media.py` — CLI (`doctor`, `registry`, `image-test`,
  `vector-test`, `video-test`, `audio-test`, `highres-test`, `blender-test`,
  `suite`).
- `scripts/media/vtmedia/` — package: `common`, `doctor`, `image_tools`,
  `vector_tools`, `ffmpeg_tools`, `blender_bridge`, `provenance`.
- `scripts/validate/system_regression.py` — runs the media suite as a
  first-class regression gate.

No code should import from this directory.
