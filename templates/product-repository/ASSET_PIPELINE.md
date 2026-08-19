# Asset Pipeline

Authoring, import, validation, generated assets, runtime packaging, licensing, and provenance.

## Asset manifest

| Asset | Purpose | Final/placeholder | Medium | Source | License | Build/export step | Validation |
|---|---|---|---|---|---|---|---|

## Source policy

- Record source and license for every external asset.
- Do not assume search-result media is usable.
- Keep source files when practical: SVG, layered raster, Blender, shader/procedural scripts, audio/video project files.
- Generated assets need prompt/model/provider/date, usage rights, seed/settings if available, and whether they are concept or final.

## Placeholder policy

Mark temporary assets explicitly:

- primitive geometry
- rough silhouettes
- low-resolution textures
- concept art used as layout filler
- unlicensed mock imagery
- generic icons not matched to product language

Production-ready visual claims require every placeholder to be replaced or justified by art direction.

## Export matrix

| Target | Size/format | Density variants | Compression | Runtime path | Notes |
|---|---|---|---|---|---|

## Validation

- Files load in app.
- No missing imports or broken paths.
- Compression does not destroy intended detail.
- High-DPI and mobile variants remain sharp.
- Accessibility alternatives exist when asset communicates meaning.
- Performance budget acceptable.
