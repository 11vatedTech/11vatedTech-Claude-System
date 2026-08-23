# HELIOGRAPH — Professional Self-Critique

## Evidence Sources
- 24 screenshots across 6 states × 3 viewports
- axe-core scan (1 violation: color-contrast)
- Keyboard traversal baseline (Tab works, initial focus on first row DIV)
- 0 console errors, 0 network failures

---

## 1. VISUAL HIERARCHY

**Symptom:** The time column, target column, and confidence gauge compete for attention. On desktop, the eye lands in the middle of the row rather than at the primary decision variable.

**Discipline:** Visual hierarchy / information design.

**Likely Cause:** The confidence gauge (amber) and priority dot (amber) share the same signal color as the primary action. Since they appear in the scanning path before the detail section, they distract from the time→target→confidence reading order. Equal column widths (grid-template-columns: 1fr 140px 120px 140px 100px 48px) distribute visual weight evenly rather than proportionally to information importance.

**Evidence:** Desktop default screenshot — the confidence gauge draws the eye before the target name.

---

## 2. TYPOGRAPHY

**Symptom:** Monospace data columns lack tabular-numeral alignment within columns. The time column (`2026-08-24 06:45 UTC` / `2026-08-24 19:15 UTC`) has ragged right edge because time components aren't individually columned.

**Discipline:** Typography / information design.

**Likely Cause:** Single `col-time` div combines time and duration. The monospace font ensures character-level alignment, but varying UTC start lengths (one has a two-digit hour 06, another 19) means the eye must re-scan each row rather than relying on consistent column position. Tabular numerals aren't being exploited for their intended purpose — the data isn't laid out in sub-columns.

**Evidence:** Desktop default screenshot — times don't align to a consistent horizontal anchor for the UTC hour.

---

## 3. COMPOSITION

**Symptom:** The header area (HELIOGRAPH title + subtitle + status bar) consumes ~20% of desktop viewport height while providing auxiliary context only. On mobile, this proportion is worse.

**Discipline:** Composition / information density.

**Likely Cause:** The header was designed as a standalone brand/status block without measuring its proportion against the content it serves. The status line (UTC clock, system status, seeing, solar activity) is valuable but over-spaced as a multi-line flex container on narrow viewports.

**Evidence:** Mobile default screenshot — header occupies roughly 30% of the fold, pushing observation rows below the initial viewport.

---

## 4. COLOR

**Symptom:** The `--text-muted` color (#6e6860) used for durations, coordinates, footer, and status labels fails WCAG AA against `--surface` (#242220). Contrast ratio is approximately 3.8:1, below the 4.5:1 minimum for normal text of this size.

**Discipline:** Color / accessibility.

**Likely Cause:** The muted color was selected for aesthetic warmth and hierarchy reduction, but the perceptual "warmth" was prioritized over the actual luminance difference. The warm-neutral palette has inherently lower contrast than cool-neutrals at the same lightness level.

**Evidence:** axe-core flags 19 elements with insufficient color contrast. The `--text-muted` variable is applied to 7 distinct element classes.

---

## 5. RESPONSIVE DESIGN

**Symptom:** On tablet (768px), the instrument and priority columns are hidden. On mobile (375px), only time and confidence remain visible. The user must tap into a row to discover the target region and instrument — critical decision variables are hidden.

**Discipline:** Responsive design / information architecture.

**Likely Cause:** The responsive strategy hides columns rather than recomposing them. A better approach would restructure the row layout — perhaps a two-tier mobile row where primary decision data (time + target + confidence) appears on the visible tier and secondary data (instrument + priority) collapses into a compact accessory row, still visible without requiring expand interaction.

**Evidence:** Mobile default screenshot — only UTC time and a percentage gauge are visible per row. The astronomer cannot compare targets without tapping each row.

---

## 6. INTERACTION

**Symptom:** The selected/detail-open state lacks a clear "you are here" spatial anchor when the detail panel expands below the row.

**Discipline:** Interaction design.

**Likely Cause:** The expansion animation (detailExpand: fade+translateY) is subtle, which feels deliberate, but the selected row only gains a slightly warmer background (--surface-selected vs --surface-raised). The distinction between the expanded row and the detail panel it reveals is visually weak — the detail panel's top border (--divider, 1px) is the only structural separator.

**Evidence:** Desktop selected-detail-open screenshot — the detail panel and the selected row merge visually.

---

## 7. MOTION

**Symptom:** The detail expansion animation (220ms fade + 8px slide) is well-timed, but the confirmation transition has no intermediate state animation — it flips to confirmed immediately on click.

**Discipline:** Motion design.

**Likely Cause:** The confirm action triggers a DOM re-render with the confirmation badge + overlay appearing in a single paint. There's no "lock-in" animation bridging the intent (click) and the committed state.

**Evidence:** Desktop confirmed screenshot — the left-edge green badge and overlay appear simultaneously with no perceived causality.

---

## 8. PRODUCT IDENTITY

**Symptom:** The interface is visually distinct from a generic dashboard, but the typographic voice doesn't fully commit to the "precision instrument" thesis — JetBrains Mono and Crimson Text are strong choices, but they don't relate to astronomical instrumentation specifically.

**Discipline:** Art direction / product identity.

**Likely Cause:** The design discovery identified "scientific instrumentation" as the reference domain, but the visual language landed in "dark mode data table" rather than capturing specific characteristics of observatory instruments — panel-mounted labels, engraved markings, calibration grids, spectral line annotations.

**Evidence:** Desktop default screenshot — reads as "well-crafted dark data table" rather than "astronomical instrument panel."

---

## Priority Matrix

| Defect | Impact | Effort | Repair? |
|---|---|---|---|
| Color contrast (19 elements) | HIGH — accessibility blocker | LOW — CSS variable change | YES |
| Mobile hidden decision data | HIGH — task failure risk | MED — restructure row layout | YES |
| Visual hierarchy (gauge vs target) | MED — slows scanning | LOW — adjust color distribution | YES |
| No confirmation animation | MED — weak causality | LOW — add transition class | YES |
| Header proportion | LOW — learnable after first use | LOW — reduce spacing | YES |
| Typography alignment | LOW — monospace partially compensates | MED — sub-column layout | DEFER |
| Product identity depth | LOW — works, doesn't sing | HIGH — visual redesign | DEFER |
| Detail/row visual merge | LOW — still scannable | LOW — stronger separator | YES |