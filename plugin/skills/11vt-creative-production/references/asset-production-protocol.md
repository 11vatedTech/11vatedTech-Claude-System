# Asset Production Protocol

## Asset strategy

Treat visual assets as first-class product artifacts. Before building final UI, list required assets and choose production route.

Asset classes:

- logo/wordmark/type treatment
- custom illustration or character/environment art
- SVG icons and diagrams
- sprites, masks, overlays, VFX sheets
- procedural textures and material maps
- 3D models, glTF/GLB, HDR/environment maps
- audio cues, loops, voice, foley
- video or animation plates
- generated concept references

## Source and license

For external assets, record:

- source URL or local path
- author/owner
- license
- commercial-use status
- attribution requirement
- modification allowance
- redistribution allowance
- whether asset is concept, placeholder, or final

Never assume scraped/search result media is usable. Prefer original, open, local, or generated assets with clear rights.

## Local/open production preference

Prefer reproducible local/open workflows when quality fits:

- SVG authored in code or vector tools
- procedural textures via scripts/shaders
- Blender for 3D models/material baking/renders
- FFmpeg for video/audio assembly
- image processing scripts for sprites/atlases/masks
- WebGL/Three.js for runtime-rendered scenes

Do not install massive dependencies blindly. Research need, license, size, platform fit, and security first.

## Placeholder policy

Mark scaffolding explicitly:

- temporary primitive geometry
- rough silhouettes
- low-detail icons
- concept art pasted as layout fill
- low-resolution textures
- unlicensed mock imagery

Before production-ready claim, replace or justify every placeholder.

## Asset manifest row

| Asset | Need | Final/placeholder | Medium | Source | License | Build step | Validation |
|---|---|---|---|---|---|---|---|
