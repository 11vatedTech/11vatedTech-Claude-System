# HELIOGRAPH — Independent Critique

*Reviewer role: external design reviewer. Did not build the interface. Reviewed screenshots, evidence capture, and builder's self-critique. Builder's self-scores were not visible during this review.*

---

## Agreements with Self-Critique

### Color contrast — CONFIRMED
The #6e6860 muted text is below AA threshold. This is the single correctable blocker. Agreed: LOW effort, HIGH impact. Fix immediately.

### Mobile decision data — STRONGER THAN STATED
The self-critique says mobile is "task failure risk." I'd strengthen this: on the 375px viewport, the astronomer cannot identify which observation window is which without tapping each row in sequence. The target name (AR 13354, AR 13352, etc.) is the primary identifying label. Hiding it behind an expand interaction turns a scanning task into a sequential discovery task. This is a usability defect, not just a responsive-design weakness.

### Confirmation animation — AGREED, plus one more
The confirmed state has no transitional animation. Additionally: the confirmation overlay appears below all rows rather than adjacent to the confirmed row. On mobile, this means the user scrolls past the remaining observation rows to see confirmation — losing spatial context. The confirmation should anchor to the row that was confirmed.

---

## Disagreements with Self-Critique

### "Detail/row visual merge" — DISAGREE
The self-critique says the selected row and detail panel merge visually. I disagree. The detail panel has a 1px border-top in `--divider` color, a raised surface (`#2c2927` vs `#242220`), and the chevron rotates 90° to amber. This is three visual signals. It's understated but functional. I'd keep this and spend effort elsewhere.

### "Product identity depth" — PARTIALLY DISAGREE
The self-critique says the interface "reads as dark mode data table rather than astronomical instrument panel." I see the opposite: the restraint IS the identity. Amber-on-dark, monospace data, serif labels, the confidence gauge as a thin horizontal bar rather than a circular gauge — these are instrument-panel conventions. What's missing isn't "more astronomy" — it's a stronger spatial vocabulary. The left-edge confirmed badge is the most instrument-like detail. More of that: edge markers, ruled lines, measurement-style annotations.

---

## Issues the Self-Critique Missed

### 1. Reading order on narrow viewports
On tablet and mobile, the remaining visible columns (time + confidence on mobile) are read left-to-right: time first, then the gauge. But on desktop with all columns visible, the left-to-right reading order is: time → target → confidence → instrument → priority → chevron. When tablet hides instrument+priority, and mobile hides target+instrument+priority, the remaining columns don't maintain the original reading order's intent. The gauge (column 3) moves to position 2, but it should arguably move to position 1 as a scannable quality signal.

**Discipline:** Responsive information architecture.

### 2. Priority encoding is exclusively color-based
The priority column uses an amber dot + text label. This is a color-only encoding for a critical decision variable. The dot size (8px) doesn't encode priority — P1, P2, and P3 dots are the same size. Color-only encoding is inaccessible to users with color vision deficiencies. The self-critique mentions the gauge "distracts" from the target but doesn't flag that priority relies entirely on hue.

**Discipline:** Information design / accessibility.

### 3. No empty/loading/error state evidence
The harness captured `default`, `focus`, `dark`, and `reduced_motion` but the HELIOGRAPH interface has no visible empty state, loading state, or error state. If the data endpoint fails or returns zero observation windows, the interface would silently show an empty container. This is a real gap for a professional planning tool.

**Discipline:** State design / resilience.

### 4. Font loading flash
Google Fonts (Crimson Text, JetBrains Mono) are loaded via `<link>` in the `<head>`. If fonts fail to load or load slowly, the fallback stack (Georgia → serif, Consolas → monospace) has different metrics. The interface may shift during font swap. The harness runs fast enough that fonts likely loaded, but this isn't guaranteed in slower network conditions.

**Discipline:** Performance / typography.

---

## Strengths the Self-Critique Undervalued

1. **The recommendation rationale section is genuinely useful.** Structured factors with positive/caution tags give the astronomer a quick summary before reading the full rationale paragraph. This is professional-caliber UX.

2. **The confidence gauge as a thin horizontal bar is an excellent choice.** Circular gauges are the default dashboard convention. The horizontal bar reads like a spectrographic measurement — it reinforces the instrument metaphor more than any color choice.

3. **The `--signal-green` confirmation color is restrained, not garish.** Many designs would use a bright green for "confirmed/selected." The subdued `#7a9e8f` communicates status without screaming. This is taste-level work.

4. **The UTC clock is live-updating.** The self-critique treats this as "auxiliary context" in the header but it's a genuine value-add for an astronomer coordinating multiple time-sensitive observations. Keep it.

---

## Repair Recommendations (Ranked)

1. **Color contrast** — Raise `--text-muted` from #6e6860 to at least #8c8478 (or higher to hit 4.5:1 on #242220).
2. **Mobile row recomposition** — Instead of hiding target column, create a two-tier mobile row: top tier = time + confidence, bottom tier = target (small) + instrument code. Keep priority dot visible.
3. **Priority encoding** — Add a non-color signal: P1 gets two dots, or a filled diamond vs empty circle, or a small numeric badge.
4. **Confirmation anchoring** — Move the confirmation overlay to appear inline below the confirmed row, not at the bottom of all rows.
5. **Confirmation animation** — Add a 300ms transition on the confirmed row: briefly pulse the left badge, then settle.
6. **Empty state** — Add a visible message when zero observation windows are available.
7. **Header proportion** — Reduce header padding/height on mobile from ~30% of viewport to ~15%.