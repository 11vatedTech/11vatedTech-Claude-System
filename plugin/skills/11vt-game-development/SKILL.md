---
name: 11vt-game-development
description: Serious game development capability for 11vatedTech. Use for game systems, mechanics, feel, controls, rendering, engine architecture, asset pipelines, tools, multiplayer, performance budgets, or game production planning.
metadata:
  owner: 11vatedTech
  type: global-capability
  version: "2026-08-15"
---

# 11vatedTech Game Development Intelligence

Build game systems, not disconnected scripts.

## Analyze first

- player experience goal
- core loop
- mechanics and verbs
- input/control requirements
- game feel targets
- camera and animation relationship
- state model
- content pipeline
- rendering/VFX/audio constraints
- save/progression needs
- deterministic or networked requirements
- platform/frame budget

## System domains

Cover:

- mechanics and game loops
- combat/locomotion/physics
- AI and behavior systems
- camera systems
- animation and state machines
- audio and feedback
- progression and save data
- narrative/world systems
- asset pipelines and tools
- rendering, shaders, VFX
- networking, replay, determinism
- automated testing and debugging
- frame pacing and performance budgets

## Rules

- Do not hardcode project into one genre unless project requires it.
- Build reusable systems when product scope demands generality.
- Separate authoring data from runtime behavior.
- Preserve deterministic boundaries for replay/networking when relevant.
- Profile frame time before optimizing.

Use `references/game-system-spec-template.md` for durable specs.
