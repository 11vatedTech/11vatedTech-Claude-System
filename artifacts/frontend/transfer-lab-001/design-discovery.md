# HELIOGRAPH — Design Discovery

## User Goal

An astronomer preparing the next observation window needs to quickly identify the best solar-observation opportunity from a set of scientifically ranked candidates, understand the rationale behind the recommendation, and confirm selection with confidence that no critical factor was missed.

## Critical Information

| Variable | Priority | Why |
|---|---|---|
| Time window (UTC start → end) | Primary | Scheduling is the core decision |
| Target region (active region #, coordinates) | Primary | What are we observing? |
| Atmospheric confidence (seeing, transparency) | Primary | Can we actually observe? |
| Instrument availability | High | What equipment is online? |
| Scientific priority score | High | Which observation matters most? |
| Solar activity indicators | Contextual | Is the target interesting right now? |
| Weather forecast summary | Situational | Will conditions hold? |

## Decision Hierarchy

1. Scan → which windows are viable?
2. Compare → which has the best combination of conditions + priority?
3. Inspect → why is this one recommended?
4. Confirm → select and lock in.

## Primary Action

**Select observation window** — the astronomer must commit to a specific UTC window.

## Secondary Actions

- Browse windows (scan, compare)
- Inspect details (tap/click to expand)
- Understand recommendation rationale

## Error Risk

- Selecting a window with degraded atmospheric conditions
- Missing an instrument conflict
- Confusion between UTC and local time
- Accidentally selecting without full information

## Information Density

Medium — 6 items is scannable but each carries 4–6 variables. The interface must support comparative reading without overload.

## Device Context

Desktop-first (observatory workstation), but tablet use at the telescope is plausible. Mobile use during remote monitoring is a real scenario.

---

## Experience Thesis

**Calibrated precision.** The interface should feel like a scientific instrument — deliberate, trustworthy, quiet. Every pixel has a measurement behind it. Confidence comes from clarity, not decoration.

## Visual Thesis

**Chromatic restraint with one deliberate signal color.** A dark, warm-neutral ground (not pure black — reminiscent of observatory dome interiors and dark-adapted vision). One signal color (amber-gold) for selection, priority, and active states — referencing heliographic instrumentation. Typography does the heavy lifting.

## Typographic Thesis

**Two families, one voice.** A monospace family for data (time, coordinates, instrument codes — things that should look like readings from an instrument). A restrained serif or humanist sans for labels, explanations, and UI text — things that should feel authored and trustworthy. Tabular numerals for all numeric data columns.

## Layout Thesis

**List-dominant with inline expansion.** The default view is a densely informative but scannable row-per-window list with aligned data columns. Selecting a window expands it inline with a detail panel that reveals the recommendation rationale — preserving context rather than navigating away.

## Color Thesis

| Role | Color |
|---|---|
| Ground | Warm dark neutral (#1a1817 → #242220) |
| Surface | Slightly lifted neutral (#2c2927) |
| Text primary | High-contrast warm off-white (#ede4d8) |
| Text secondary | Muted warm (#9c9488) |
| Signal (primary action / priority) | Amber-gold (#d4a843) |
| Signal (caution / degraded) | Muted coral (#c4785c) |
| Signal (good / confirmed) | Subdued green-teal (#7a9e8f) |
| Divider / rule | Low-contrast (#3a3632) |

## Motion Thesis

**Gravity and calibration.** Motion is subtle, deliberate, and physics-informed. Transitions feel like precision mechanisms — not playful bounces. Duration: 180–280ms. Easing: custom cubic-bezier approximating deceleration into place. No motion that delays task completion.

---

## Anti-References

- Neon-space dashboards (purple/cyan gradients, glow borders)
- Orbital graphics as decoration
- HUD-style reticles and crosshairs
- Fake coordinate readouts
- Glassmorphism cards
- Meaningless waveform animations
- "Futuristic" sci-fi typefaces
- Overuse of saturation to signal importance