# Multimodal 9Router Benchmark — Transfer Lab 001

## Evidence Set

### Primary Evidence (from Transfer Lab 001)

| ID | Type | Source | Description |
|---|---|---|---|
| HLG-DESK-DEF | Screenshot | HELIOGRAPH initial, desktop default | 6 observation rows, full columns |
| HLG-DESK-SEL | Screenshot | HELIOGRAPH initial, desktop selected-detail | Row expanded with detail panel |
| HLG-MOB-DEF | Screenshot | HELIOGRAPH initial, mobile default | Mobile view, columns hidden |
| HLG-DESK-REP | Screenshot | HELIOGRAPH repaired, desktop default | Repaired with contrast fix, priority shapes |
| HLG-MOB-REP | Screenshot | HELIOGRAPH repaired, mobile default | Two-tier mobile row |
| HLG-DESK-CONF | Screenshot | HELIOGRAPH repaired, desktop confirmed | Inline confirmation, pulse badge |
| CON-DESK-DEF | Screenshot | Conservation queue, desktop default | Transfer component, different visual language |

### Preserved Foundry Evidence

| ID | Type | Source | Description |
|---|---|---|---|
| FW-SMOKE-DEF | Screenshot | Frontend smoke test, desktop default | Generic page with card + form |
| FW-SMOKE-MOB | Screenshot | Frontend smoke test, mobile default | Generic page, narrow viewport |

---

## Benchmark Roles

### Frontend Visual Critic
**Tasks:** Detect visual defects in screenshots. Identify hierarchy problems, contrast issues, composition weaknesses, typographic flaws.
**Evidence Required:** Screenshots (PNG).
**Primary Metric:** Defect precision + defect recall.

### UX Critic
**Tasks:** Evaluate task completion path. Identify interaction barriers, confusion points, information architecture problems.
**Evidence Required:** Screenshots + interaction evidence.
**Primary Metric:** Causal diagnosis accuracy + repair specificity.

### Art Director
**Tasks:** Evaluate visual identity, style coherence, originality. Identify generic patterns, cliché usage, weak art-direction language.
**Evidence Required:** Screenshots.
**Primary Metric:** Specificity of critique + false-positive rate.

---

## Task Definitions

### Task 1: Defect Detection (Frontend Visual Critic)

**Prompt:** "Review this screenshot of a solar observation planning interface. Identify every professional defect you can find. For each defect, state: what is wrong, which design discipline owns it (visual hierarchy, typography, color, composition, responsive design, interaction, motion, or accessibility), and how you would repair it."

**Test set:** HLG-DESK-DEF, HLG-MOB-DEF, HLG-DESK-SEL

**Ground truth (from self + independent critique):**
- color-contrast: 19 elements below WCAG AA (accessibility)
- Mobile target column hidden, requires tap-to-discover (responsive design / UX)
- Priority encoding color-only, no shape signal (information design)
- No confirmation transition animation (motion)
- Header proportion excessive on mobile (composition)

### Task 2: Causal Diagnosis (UX Critic)

**Prompt:** "A mobile astronomer needs to compare observation windows. Review this mobile screenshot. What task-specific problems exist, and what discipline does each belong to?"

**Test set:** HLG-MOB-DEF (initial — hidden columns) vs HLG-MOB-REP (repaired — two-tier)

**Expected diagnosis:**
- Initial: user cannot identify observation targets without tapping each row (information architecture / responsive design)
- Repaired: two-tier layout restores target + priority visibility (responsive recomposition, not column-hiding)

### Task 3: Pairwise Comparison — Art Direction (Art Director)

**Prompt:** "Which of these two interfaces better establishes a distinct, non-generic product identity? Compare A and B. Which is stronger and why? Be specific about visual language, not just 'looks better.'"

**Pairs:**
- A: HLG-DESK-DEF (Heliograph initial) vs B: FW-SMOKE-DEF (generic frontend smoke page)
- A-reversed: swap order and re-ask to measure position bias

### Task 4: Transfer Detection (Frontend Visual Critic)

**Prompt:** "Review these two screenshots. They are from different projects (solar observatory planning vs museum conservation). Identify which one general visual-design principle was successfully transferred between them, and note how the visual style was deliberately kept distinct."

**Test set:** HLG-DESK-REP vs CON-DESK-DEF

**Expected observations:**
- Non-color priority encoding (diamond/circle/outline shapes) transferred
- Mobile-responsive data restructure (two-tier rows) transferred
- Inline confirmation anchoring transferred
- Visual language deliberately changed: dark-warm/amber/serif → light-warm/burgundy/serif

---

## Rubric

| Dimension | Scoring |
|---|---|
| Failure detection | Did model identify documented defects? |
| Causal diagnosis | Did model attribute to correct discipline? |
| Discipline identification | Was the owning discipline correctly named? |
| Specificity | Was the critique specific (not "needs polish")? |
| Repair quality | Was the proposed repair causally sound? |
| False-positive rate | Did model invent problems not present? |
| Reference/taste sensitivity | Did model distinguish design decisions from defects? |
| Uncertainty calibration | Did model express uncertainty where appropriate? |
| Position consistency (pairwise) | Did A/B preference hold when order was swapped? |

---

## Judge Bias Controls

### Position Bias Test
- Run pairwise A/B then B/A for the same comparison
- If preference flips: mark POSITION_UNSTABLE
- Record: position_consistency = matched / total_pairs

### Self-Preference Diagnostic
- If builder model (the one that built Heliograph) is used as judge:
  - Anonymize: remove any identifying text, project names, timestamps
  - Compare preference rates with an independent model family if possible
  - Record: potential_self_preference_signal

### Agreement Tracking
- When multiple judges or multiple runs are available:
  - Record: judge_agreement_rate
  - Record: judge_disagreement_cases
  - Do not treat majority as truth for subjective dimensions

---

## Initial Routing Evidence (Placeholder — requires actual vision model calls)

| Role | Model | Defect Precision | Causal Accuracy | False Positive Rate | Position Consistency | Confidence |
|---|---|---|---|---|---|---|
| frontend_visual_critic | TBD | — | — | — | — | LOW |
| ux_visual_critic | TBD | — | — | — | — | LOW |
| art_director | TBD | — | — | — | — | LOW |

**Note:** This benchmark framework is deployable. Actual model calls against vision-capable models (GPT-4V, Claude 3.5 Sonnet, Gemini 2.0 Flash, etc.) with the defined evidence set would populate the routing matrix. The framework captures: evidence set, task definitions, rubric, bias controls, and ground-truth annotations. The routing update should re-run when new models become available.

---

## Routing Update Policy

- Do not hardcode "Model X is best for role Y"
- Every routing record carries: benchmark_version, model_version, date, evidence_set_version
- Re-evaluate when: new model versions, new evidence, new task types
- Prefer pairwise evidence over scalar scores
- Track judge disagreement, not just consensus