# Visual QA Checklist

Use before claiming UI work visually inspected.

## Evidence header

- Date:
- Project/version/commit:
- Runtime URL or artifact:
- Build command/result:
- Preview/server command/result:
- Screenshots/snapshots captured:
- Visual canon compared:

## Viewports

- Desktop inspected:
- Tablet/intermediate inspected:
- Mobile inspected:
- High-DPI/ultrawide caveat:
- Light/dark if applicable:
- Reduced-motion behavior:

## Structure and hierarchy

- Eye goes first to intended focal point.
- Foreground/middle/background relationship clear.
- Primary action visible and understandable.
- Supporting content does not compete with core task.
- Negative space intentional, not empty filler.
- Important states designed: loading, empty, error, disabled, success, win/loss if relevant.

## Anti-generic inspection

- No ungrounded generic neon/glass/dashboard/card aesthetic.
- No meaningless particles, blur blobs, glows, HUD trim, or icon circles.
- Typography carries product identity.
- Assets contribute meaning and are not placeholders posing as final.
- Screenshot would not plausibly belong to 100 unrelated AI-generated apps.
- Visual effects still make sense when tied to state/story/material.

## Typography

- Typeface choices match product personality.
- Scale, weight, width, tracking, leading, and line length deliberate.
- Labels/data/numbers readable and optically aligned.
- Responsive typography remains composed.

## Layout and spacing

- Grid/rhythm consistent where intended.
- Intentional asymmetry documented by composition, not accident.
- Alignment clean.
- No crowding or awkward dead zones.
- No overflow/clipping at tested viewports.

## Color, contrast, material

- Color roles clear.
- Contrast sufficient for text and controls.
- Lighting/material/depth coherent.
- Effects do not hide weak composition.
- Surfaces and shadows follow same light logic.

## Interaction and motion

- Hover/focus/active states visible.
- Keyboard path works.
- Motion communicates state, hierarchy, space, or emotion.
- Timing/easing feels intentional.
- Animations interrupt safely.
- Reduced-motion alternative preserves meaning.

## Accessibility

- Landmark/heading structure coherent.
- Controls named from user perspective.
- `aria-live` used only where useful.
- Color not sole carrier of meaning.
- Focus indicators visible.
- Touch targets usable on mobile.

## Runtime health

- Console errors:
- Network/server errors:
- Layout/performance obvious issues:
- Memory/frame-rate caveat if relevant:

## Critique

- What looks generic?
- What weakens product identity?
- What user action lacks clarity?
- What asset is still scaffolding?
- What should be removed, not polished?
- What requires conceptual escalation?

## Completion decision

- Functionally verified:
- Visually inspected:
- Visual QA issues fixed:
- Remaining limitations disclosed:
