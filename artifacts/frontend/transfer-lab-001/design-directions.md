# HELIOGRAPH — Three Design Directions

## Direction A — "Chronograph"

**Experience Thesis:** A precision instrument for astronomical scheduling. The interface behaves like a scientific chronograph — data is presented in aligned columns, interactions are mechanical and deliberate, and every visual element has a measurement purpose.

**Spatial Model:** List-dominant. Six rows, one per window, with data columns aligned for rapid horizontal scanning. Selecting a row expands it inline — the detail panel slides open beneath with recommendation rationale, preserving spatial context.

**Typography:** Monospace (JetBrains Mono) for all data columns — time, coordinates, instrument codes, confidence percentages. Serif (Crimson Text) for labels, headings, and explanatory prose. Tabular numerals throughout.

**Data Representation:** Numerical columns with consistent decimal alignment. Atmospheric confidence shown as a thin horizontal gauge (0–100%). Priority indicated by the signal-color density of a small indicator.

**Motion:** 220ms ease-out expansion. Detail panel slides down with deceleration. Confirmation transitions through a brief "lock" animation — the row transforms to a confirmed state.

**Strength:** Fastest comparative scanning. Most appropriate for the primary task.
**Risk:** May feel cold without the right typographic warmth.
**Anti-generic argument:** No cards, no grids, no dashboards — it reads like a scientific instrument log.

---

## Direction B — "Atlas"

**Experience Thesis:** A spatial map of observation opportunities. Windows are arranged in a 3×2 card grid (desktop) where position implies temporal sequence and size encodes priority. The astronomer navigates an information landscape.

**Spatial Model:** Card grid. Three columns, two rows of observation cards. The highest-priority window occupies the top-left position (primary reading gravity in LTR cultures). Cards expand into a modal/overlay for detail view.

**Typography:** Humanist sans-serif (Inter) for everything. Weight hierarchy (Regular → Medium → SemiBold) distinguishes data from labels. Consistent type scale.

**Data Representation:** Each card shows time (large), target region, confidence gauge (circular), and priority (card border thickness + subtle glow density). The grid itself communicates priority through position.

**Motion:** Cards scale subtly on hover. Modal slides up from card position. Confirmation dissolves the modal and transforms the card with a subdued confirmation treatment.

**Strength:** Visually engaging, good at-a-glance priority reading. Familiar card-based mental model.
**Risk:** Cards are less efficient for numeric comparison than aligned columns. Card grid may feel "generic app" without strong art direction.
**Anti-generic argument:** Card border thickness as priority encoding, monospace data within cards creates tension between organic layout and instrument precision.

---

## Direction C — "Spectrograph"

**Experience Thesis:** Time as space. A horizontal timeline visualization where each observation window is a positioned element along a UTC axis. Vertical position encodes atmospheric confidence — higher = better seeing. The relationship between windows becomes spatial and immediate.

**Spatial Model:** Timeline chart. A horizontal axis representing the upcoming observation period. Windows appear as positioned markers whose x-position encodes start time and whose width encodes duration. Y-position on a secondary track encodes confidence. Selecting a marker expands a detail drawer from the right edge.

**Typography:** Geometric sans (DM Sans) for UI, with monospace (IBM Plex Mono) for precise data readouts in the detail drawer. Large time labels anchor the timeline.

**Data Representation:** Position (x, y, width) carries information directly. Priority indicated by marker fill density. Instrument availability shown as small badges adjacent to markers. This is the most information-dense direction.

**Motion:** Markers respond to hover with subtle vertical lift (2px). Detail drawer slides from right. Confirmation animates the marker along a "lock" path.

**Strength:** Most innovative spatial encoding — time-to-space mapping is intuitive for temporal data. Highest information density.
**Risk:** Unfamiliar interaction model. Mobile adaptation challenging. May overcomplicate a six-item list.
**Anti-generic argument:** Resembles a scientific plot more than an application interface. Time is literally space — not metaphorical.

---

## Selection: Direction A — "Chronograph"

**Reasoning:** For an astronomer's primary task — rapidly comparing structured observation windows — the list-dominant, column-aligned layout provides the fastest cognitive access to decision variables. The precision-instrument metaphor aligns with the user's professional context (they already use scientific instrumentation). The design direction resists SaaS-generic conventions while remaining learnable. Typography-as-primary-design-material suits a text-and-numbers-dense interface.