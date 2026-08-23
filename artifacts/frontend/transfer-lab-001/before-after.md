# HELIOGRAPH — Before / After

## Repairs Applied

### 1. Color Contrast (accessibility blocker)
- **Before:** `--text-muted` at #6e6860 — failed WCAG AA (3.8:1), 19 elements flagged
- **After:** Raised to #a0988a — passes WCAG AA (4.5:1+), **0 axe violations**
- **Evidence:** axe-core: 1 violation → 0 violations

### 2. Mobile Row Recomposition (usability)
- **Before:** On mobile, target column hidden entirely. Astronomer must tap each row to identify observations.
- **After:** Two-tier mobile row: top tier = time + confidence, bottom tier = target + priority. All decision variables visible without interaction.
- **Evidence:** Mobile screenshots — target and priority now visible on the default view

### 3. Priority Encoding (non-color signal)
- **Before:** Priority encoded only by amber dot color + opacity. P1=full amber, P2=50% opacity amber, P3=gray. Indistinguishable for color-vision-deficient users.
- **After:** Shape encoding added — P1=diamond (polygon clip-path), P2=filled circle, P3=outline circle. Color still present as redundant channel.
- **Evidence:** Priority dots now have shape differentiation independent of hue.

### 4. Confirmation Animation (motion causality)
- **Before:** No transition — confirmed state appeared instantly.
- **After:** `confirmPulse` animation (400ms, grow-from-zero-ease-out) on the left-edge confirmation badge. Creates perceived causality between click and committed state.
- **Evidence:** Desktop confirmed screenshot — badge now reveals with animation instead of appearing atomically.

### 5. Inline Confirmation (spatial anchoring)
- **Before:** Confirmation message appeared at the bottom of the page, disconnected from the confirmed row.
- **After:** Confirmation panel appears within the confirmed row's detail section, immediately below the recommendation rationale. Spatial context preserved.
- **Evidence:** Desktop confirmed screenshot — confirmation panel visible within the confirmed row.

### 6. Header Proportion (mobile viewport economy)
- **Before:** Header consumed ~30% of mobile viewport (large h1, multi-line status bar).
- **After:** Reduced padding, smaller h1 (16px clamp), compacted status line. Header now ~15% of viewport.
- **Evidence:** Mobile default screenshot — more observation rows visible above fold.

### 7. Empty State (resilience)
- **Before:** Zero observation windows would render an empty container with no message.
- **After:** Explicit "No observation windows available" message with next-cycle guidance.
- **Evidence:** Code: `OBSERVATIONS.length === 0` check renders fallback UI.

## What Was Not Repaired (Tradeoffs)

- **Typography alignment:** Sub-column layout for UTC components deferred — monospace provides partial alignment, and the effort-to-impact ratio was judged low for a 6-item list.
- **Product identity depth:** The "precision instrument" thesis is already well-supported by the horizontal gauge, amber-on-dark palette, and monospace data columns. Further "astronomical" detail would risk decoration over function.
- **Font loading flash:** Would require `font-display: swap` + explicit fallback sizing. Deferred — not visible in screenshot evidence.

## Net Capability Delta

| Dimension | Before | After |
|---|---|---|
| Accessibility (axe) | 1 color-contrast violation (19 nodes) | 0 violations |
| Mobile task viability | Decision data hidden, requires tap-to-discover | All variables visible, scannable |
| Priority perception | Color-only encoding | Shape + color dual encoding |
| Confirmation causality | Instant state flip | Animated badge (400ms pulse) |
| Confirmation context | Detached bottom overlay | Inline within confirmed row |
| Header economy (mobile) | ~30% viewport | ~15% viewport |
| Empty state handling | Silent failure | Explicit fallback UI |
| Console errors | 0 | 0 |