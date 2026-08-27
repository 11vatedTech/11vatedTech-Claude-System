"""Write deepened professional packs for KAPIF Milestone 002."""
import json, os

BASE = 'config/resource-packs'

# ── Pack 1: COMPOSITION_VALUE_COLOR_CORE ──
composition = {
    "schema_version": 2, "pack_id": "COMPOSITION_VALUE_COLOR_CORE",
    "date": "2026-08-23", "status": "ACTIVE",
    "knowledge_class": "evergreen_fundamentals_with_versioned_tool_notes",
    "disciplines": ["composition", "value-structure", "color-theory", "visual-hierarchy", "art-direction"],
    "professional_baseline": {
        "beginner": [
            "rule of thirds and basic framing vocabulary",
            "can identify foreground/midground/background",
            "understands value as lightness independent of hue",
            "can produce a 3-value thumbnail"
        ],
        "working_professional": [
            "controls focal hierarchy through value contrast, not just placement",
            "designs compositions that read at thumbnail, mid-distance, and full size",
            "builds color relationships from temperature, saturation, and value",
            "produces controlled value keys: high-key, low-key, full-range"
        ],
        "senior": [
            "diagnoses why a composition fails despite correct rule application",
            "recognizes value-grouping failures from local contrast conflicts",
            "understands color as structural hierarchy tool, not decoration",
            "critiques saturation exhaustion and weak focal budgeting"
        ],
        "lead_director": [
            "establishes composition/value/color canon that scales across media",
            "knows when a color script is ready for production",
            "rejects technically-correct but visually-dead compositions with causal reasoning"
        ]
    },
    "foundations": {
        "composition_principles": [
            {"principle": "focal_hierarchy", "definition": "One dominant point. Hierarchy via contrast (value, color, scale, detail, isolation).", "failure": "everything-shouts: competing focal points with equal contrast"},
            {"principle": "value_grouping", "definition": "Shapes with similar value read as one group. If 3-value thumbnail fails, composition fails.", "failure": "value-bleed: adjacent shapes share same value"},
            {"principle": "negative_space", "definition": "Space around subjects carries structural weight equal to subjects.", "failure": "claustrophobic: no rest areas"},
            {"principle": "visual_rhythm", "definition": "Repeated/varied spacing creates visual beat guiding scanning.", "failure": "monotonous-grid: equal spacing destroys hierarchy"},
            {"principle": "scale_and_proportion", "definition": "Relative size determines perceived importance. Scale contrast is strongest hierarchy tool.", "failure": "scale-confusion: no clear size hierarchy"},
            {"principle": "edge_control", "definition": "Hard edges draw eye; soft edges recede; lost edges invite depth.", "failure": "uniform-edges: every edge equally sharp"},
            {"principle": "depth_cues", "definition": "Overlap, scale diminution, atmospheric perspective, value falloff, temperature shift signal depth.", "failure": "flat-stack: objects like flat collage"}
        ],
        "value_principles": [
            {"principle": "value_is_structure", "definition": "Value carries more structural weight than color. Works in grayscale = works in color.", "failure": "color-dependent-structure: relies on hue for hierarchy"},
            {"principle": "contrast_budgeting", "definition": "Max contrast is finite resource. Spend at focal point.", "failure": "contrast-waste: high contrast in background"},
            {"principle": "value_keys", "definition": "High-key, low-key, full-range create different emotional registers.", "failure": "inappropriate-key: key contradicts mood"},
            {"principle": "midtone_preservation", "definition": "Midtones carry readable detail. Crushed blacks/blown whites destroy information.", "failure": "black-crush: shadows become opaque"}
        ],
        "color_principles": [
            {"principle": "temperature_hierarchy", "definition": "Warm advances, cool recedes. Temperature defines spatial depth more reliably than hue.", "failure": "temperature-chaos: warm/cool random"},
            {"principle": "saturation_economy", "definition": "High saturation demands attention. Gray is context that makes color meaningful.", "failure": "saturation-exhaustion: everything saturated"},
            {"principle": "simultaneous_contrast", "definition": "Color changes with surroundings. Design relationships, not isolated swatches.", "failure": "swatch-design: colors chosen in isolation"},
            {"principle": "color_as_information", "definition": "Color encodes categories but must never be sole information channel.", "failure": "color-only-coding: critical info via hue alone"},
            {"principle": "limited_palette_discipline", "definition": "3-7 colors with clear roles produce stronger identity than unlimited choice.", "failure": "palette-bloat: dozens of colors, no role structure"}
        ]
    },
    "workflow": [
        "intent_and_emotional_target", "thumbnail_exploration_3_value_minimum",
        "value_key_selection", "major_value_mass_blocking", "focal_contrast_budgeting",
        "color_temperature_strategy", "limited_palette_selection_with_roles",
        "saturation_hierarchy_assignment", "controlled_studies",
        "grayscale_verification", "color_blindness_simulation",
        "independent_review", "causal_repair", "unseen_transfer_test"
    ],
    "quality_dimensions": {
        "composition": ["focal hierarchy", "value grouping", "negative space", "rhythm", "scale", "depth cues", "edge control"],
        "value": ["thumbnail readability", "contrast budgeting", "midtone preservation", "key appropriateness", "plane separation"],
        "color": ["temperature structure", "saturation hierarchy", "palette discipline", "simultaneous contrast", "color-as-information", "accessibility"],
        "integration": ["grayscale verification", "color-blind simulation", "emotional register", "identity coherence"]
    },
    "failure_patterns": [
        {"id": "black-crush", "discipline": "value", "symptoms": ["no readable midtones", "hero reads as silhouette"], "causes": ["exposure too low", "no motivated fill"], "repair": "restore midtone separation with motivated fill"},
        {"id": "flat-hierarchy", "discipline": "composition", "symptoms": ["eye wanders", "no primary/secondary/tertiary read"], "causes": ["no contrast budgeting", "equal spacing"], "repair": "assign dominant focal, reduce contrast elsewhere"},
        {"id": "saturation-exhaustion", "discipline": "color", "symptoms": ["visual fatigue", "nothing stands out"], "causes": ["all colors high saturation"], "repair": "reduce 80% to low-medium, reserve high for focal"},
        {"id": "value-bleed", "discipline": "value", "symptoms": ["subject merges with background", "fails grayscale"], "causes": ["adjacent values too similar"], "repair": "10-15% value difference at critical boundaries"},
        {"id": "temperature-chaos", "discipline": "color", "symptoms": ["spatial depth contradicts cues"], "causes": ["warm/cool ignores perspective"], "repair": "warm-to-cool depth gradient"},
        {"id": "negative-space-collapse", "discipline": "composition", "symptoms": ["claustrophobic", "no breathing room"], "causes": ["uniform detail density"], "repair": "allocate 20-30% frame to rest areas"},
        {"id": "color-only-coding", "discipline": "color+accessibility", "symptoms": ["info lost in grayscale"], "causes": ["hue as sole differentiator"], "repair": "add secondary channel"}
    ],
    "causal_diagnostics": {
        "why_is_my_composition_flat": [
            "Is there one dominant focal point with maximum contrast?",
            "Are secondary areas demonstrably lower contrast?",
            "Do you have clear foreground/midground/background value plan?",
            "Are there rest areas for the eye?",
            "Does the 3-value thumbnail read clearly?"
        ],
        "why_does_my_color_feel_chaotic": [
            "Is there a clear temperature strategy?",
            "Is saturation used hierarchically?",
            "Does the palette have assigned roles?",
            "Have you tested adjacency effects between key pairs?"
        ]
    },
    "tools": {
        "analysis": ["grayscale conversion", "color-blind simulation", "thumbnail reduction", "squint test", "value histogram"],
        "creation": ["Krita when installed", "Blender lookdev", "Unreal post-process", "ImageMagick"],
        "evidence": ["grayscale screenshots", "color-blind captures", "3-value exports", "before/after comparisons"]
    },
    "micro_labs": [
        {"id": "three-value-thumbnail", "goal": "Readable composition with exactly 3 values before color/detail", "success": "reads at postage-stamp size, focal clear"},
        {"id": "limited-palette-study", "goal": "Composition with exactly 5 colors and clear role assignment", "success": "every color role identifiable, palette intentional"},
        {"id": "grayscale-verification", "goal": "Convert color composition to grayscale, diagnose value-grouping failures", "success": "identify 2+ value-bleed locations with repairs"},
        {"id": "contrast-budget", "goal": "Map contrast budget: highest/medium/lowest regions vs intended hierarchy", "success": "contrast map matches focal hierarchy"}
    ],
    "transfer_tests": [
        {"id": "different-domain", "goal": "Apply value/color principles from character to environment/UI", "success": "principles transfer, visual result distinct"},
        {"id": "invert-key", "goal": "Re-block high-key composition in low-key without losing hierarchy", "success": "focal hierarchy survives key inversion"}
    ],
    "golden_tasks": [
        {"id": "composition-audit", "description": "Analyze composition: focal hierarchy, value structure, color relationships, 2+ failure patterns with causal diagnosis", "evidence": "structured audit"},
        {"id": "value-repair", "description": "Given black-crush or value-bleed failures, produce repaired version", "evidence": "before/after grayscale, written rationale"},
        {"id": "palette-critique", "description": "Critique palette: saturation, temperature, roles, accessibility", "evidence": "causal critique with recommendations"}
    ],
    "cross_pack_links": {
        "depends_on": ["ART_DIRECTION_LOOKDEV_CORE"],
        "feeds_into": ["TYPOGRAPHY_INFORMATION_DESIGN_CORE", "MOTION_DESIGN_CORE", "FRONTEND_UI_UX_CORE"],
        "relationship": "Structural foundation that art direction orchestrates, typography inhabits, motion activates"
    },
    "evidence_requirements": ["value thumbnail", "grayscale verification", "color-blind simulation", "before/after repair", "independent review", "transfer artifact"],
    "sources": [
        {"title": "WCAG 2.2 — Use of Color (1.4.1)", "url": "https://www.w3.org/TR/WCAG22/#use-of-color", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "WCAG 2.2 — Contrast Minimum (1.4.3)", "url": "https://www.w3.org/TR/WCAG22/#contrast-minimum", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "Blender Manual: Color Management", "url": "https://docs.blender.org/manual/en/latest/render/color_management/index.html", "authority": "Blender docs", "retrieved": "2026-08-23"}
    ],
    "version_sensitive_facts": [
        {"fact": "Blender Filmic/AgX color management defaults", "version": "Blender 5.x", "revalidation": "on-major-release"}
    ],
    "known_limits": [
        "No script can certify visual taste or emotional impact.",
        "Color perception is physiological and cultural.",
        "Provides professional vocabulary and diagnostic frameworks, not automated scoring."
    ]
}

# ── Pack 2: TYPOGRAPHY_INFORMATION_DESIGN_CORE ──
typography = {
    "schema_version": 2, "pack_id": "TYPOGRAPHY_INFORMATION_DESIGN_CORE",
    "date": "2026-08-23", "status": "ACTIVE",
    "knowledge_class": "evergreen_fundamentals_with_versioned_web_typography",
    "disciplines": ["typography", "information-design", "editorial-design", "frontend-design", "accessibility"],
    "professional_baseline": {
        "beginner": [
            "understands typeface vs font distinction",
            "can identify serif, sans-serif, monospace, display classifications",
            "sets readable body copy (measure, leading, size)",
            "establishes a basic heading/body hierarchy"
        ],
        "working_professional": [
            "designs type systems with clear role assignment across breakpoints",
            "controls measure (45-75 chars), leading (1.2-1.6x), and tracking intentionally",
            "uses type scale with harmonic ratios (major third, perfect fourth, golden ratio)",
            "understands optical sizing and variable font axes",
            "designs tabular data, labels, annotations as first-class typography"
        ],
        "senior": [
            "diagnoses readability failures causally (not just 'too small')",
            "understands how typography interacts with composition, color, and motion",
            "selects typefaces for product identity, not decoration",
            "designs information hierarchy that survives responsive collapse",
            "critiques density, scan patterns, and information architecture through typography"
        ],
        "lead_director": [
            "establishes typographic voice that scales across products and media",
            "knows when a type system needs character vs. when it needs restraint",
            "approves typeface selection with accessibility, performance, and licensing awareness"
        ]
    },
    "foundations": {
        "type_system_principles": [
            {"principle": "hierarchy_through_type", "definition": "Size, weight, case, color, position, and spacing differentiate information levels. Use at least 3 of these channels for robust hierarchy.", "failure": "single-channel-hierarchy: only size differentiates levels"},
            {"principle": "measure_discipline", "definition": "Line length (measure) of 45-75 characters for body text. Shorter for captions; can be longer for headings. Measure affects reading comfort as much as size.", "failure": "measure-drift: body lines span full viewport width at desktop"},
            {"principle": "vertical_rhythm", "definition": "Consistent baseline grid creates structural order. Line-height multiples align elements even when they span different type sizes.", "failure": "rhythm-break: adjacent blocks float at different vertical offsets"},
            {"principle": "type_scale_ratios", "definition": "Harmonic ratios (1.25 major third, 1.333 perfect fourth, 1.5 perfect fifth, 1.618 golden ratio) produce intentional contrast between levels.", "failure": "arbitrary-scale: sizes chosen by eye with no mathematical relationship"},
            {"principle": "role_assignment", "definition": "Every typeface in a system has a role: body, heading, UI, data, code, display. Roles constrain usage and prevent ad-hoc font selection.", "failure": "role-drift: heading font used for body, display font used for UI labels"},
            {"principle": "optical_sizing", "definition": "Type designed for display sizes differs from type designed for text sizes. Optical size axes or separate optical variants ensure readability at every scale.", "failure": "single-optical: display typeface used at 12px with collapsed stroke contrast"}
        ],
        "readability_principles": [
            {"principle": "contrast_is_not_just_ratio", "definition": "WCAG 4.5:1 is minimum. Beyond ratio: font weight, size, anti-aliasing, and background complexity affect real-world readability.", "failure": "passes-ratio-fails-real: 4.5:1 but thin weight on photographic background unreadable"},
            {"principle": "content_density", "definition": "Information density must match user task. Dense applications need tighter typography; editorial reading needs generous spacing.", "failure": "wrong-density: editorial at application density or dashboard at reading density"},
            {"principle": "scan_patterns", "definition": "Users scan before they read. F-pattern and Z-pattern scanning behavior should inform heading placement, bold lead-ins, and key information positioning.", "failure": "unscannable: walls of text with no entry points, bold terms, or structural breaks"}
        ],
        "information_design_principles": [
            {"principle": "tabular_numerics", "definition": "Numbers in tables and data displays must be tabular (fixed-width) and right-aligned for magnitude comparison. Proportional figures destroy scan-ability.", "failure": "proportional-data: proportional figures in data columns create jagged reads"},
            {"principle": "label_hierarchy", "definition": "Labels, captions, annotations, and metadata each need distinct typographic treatment. Not everything is body or heading.", "failure": "label-flattening: all secondary text at same size/weight/color"},
            {"principle": "responsive_typography", "definition": "Type scales, measure, and hierarchy must adapt to viewport. A 48px headline on desktop may need to become 32px on mobile — but relationship to body must survive.", "failure": "scale-collapse: mobile headings and body collapse to same visual weight"}
        ]
    },
    "workflow": [
        "content_audit_and_type_specimen", "typeface_selection_with_roles",
        "type_scale_definition", "vertical_rhythm_baseline",
        "heading_body_ui_data_code_assignments",
        "responsive_scale_breakpoints",
        "contrast_verification_all_sizes",
        "readability_testing_real_content",
        "accessibility_review", "performance_audit_font_loading",
        "independent_review", "causal_repair", "unseen_transfer_test"
    ],
    "quality_dimensions": {
        "hierarchy": ["heading/body differentiation", "information level count", "multi-channel coding", "responsive adaptation"],
        "readability": ["measure", "leading", "contrast", "weight", "size", "content density match"],
        "identity": ["typeface character", "voice appropriateness", "role assignment clarity", "cross-media coherence"],
        "accessibility": ["contrast ratios", "resize behavior", "font loading fallback", "letter-spacing for readability"],
        "performance": ["font file size", "loading strategy", "FOIT/FOUT handling", "subset if appropriate"]
    },
    "failure_patterns": [
        {"id": "measure-drift", "discipline": "typography", "symptoms": ["body text spans full viewport", "eye loses place between lines"], "causes": ["no max-width on text containers", "responsive breakpoints ignore measure"], "repair": "cap body text containers at 65-75ch; test at every breakpoint"},
        {"id": "faux-hierarchy", "discipline": "information-design", "symptoms": ["everything looks same importance", "users cannot scan"], "causes": ["only size differentiates levels", "no weight/color/position contrast"], "repair": "add at least 2 additional hierarchy channels"},
        {"id": "type-overload", "discipline": "typography", "symptoms": ["too many typefaces", "no clear role per font"], "causes": ["ad-hoc selection", "every designer adds a favorite"], "repair": "reduce to 2-3 typefaces with explicit roles, document in design system"},
        {"id": "system-font-default", "discipline": "typography+identity", "symptoms": ["no product identity", "looks like unstyled browser default"], "causes": ["no typeface selection process", "defaulting to system sans-serif without intention"], "repair": "select typeface(s) that express product character"},
        {"id": "contrast-brittle", "discipline": "typography+accessibility", "symptoms": ["text readable on solid background, unreadable on image"], "causes": ["contrast tested only on flat backgrounds"], "repair": "test on photographic/video/gradient backgrounds, add text-shadow or scrim if needed"},
        {"id": "data-typography-neglect", "discipline": "information-design", "symptoms": ["numbers hard to compare", "tables visually chaotic"], "causes": ["proportional figures in data", "no alignment discipline"], "repair": "tabular figures, right-align numbers, consistent label treatment"}
    ],
    "causal_diagnostics": {
        "why_is_my_type_hierarchy_weak": [
            "Are you using at least 3 channels (size, weight, color, position, case, spacing)?",
            "Does your type scale use a harmonic ratio?",
            "Is your heading/body contrast at least 2x in visual weight?",
            "Does your hierarchy survive at mobile breakpoints?"
        ],
        "why_is_my_text_hard_to_read": [
            "Is measure between 45-75 characters?",
            "Is leading at least 1.4x for body text?",
            "Is contrast at least 4.5:1 on actual backgrounds?",
            "Is font weight at least 400 at the rendered size?",
            "Are fonts loading before text is visible?"
        ]
    },
    "tools": {
        "selection": ["Google Fonts for quick prototyping", "professional foundry catalogs", "variable font testing tools"],
        "implementation": ["CSS font-face", "variable font axes", "font-display strategy", "WOFF2 delivery"],
        "testing": ["contrast checkers", "zoom/resize testing", "Playwright screenshots", "Lighthouse font metrics"]
    },
    "micro_labs": [
        {"id": "type-scale-build", "goal": "Build a type scale from a chosen ratio, assign it to heading/body/UI/caption roles, and verify at 3 breakpoints", "success": "clear differentiation at every level, ratio consistent across breakpoints"},
        {"id": "roles-only-system", "goal": "Design a typography system using exactly 2 typefaces (1 body, 1 display) with explicit role boundaries", "success": "no cross-role usage, every text element classifiable"},
        {"id": "responsive-measure", "goal": "Test body text measure at 320, 768, 1024, and 1440px viewports; adjust containers until measure stays 45-75 chars everywhere", "success": "measure in range at all breakpoints"},
        {"id": "contrast-audit", "goal": "Audit every text element on real backgrounds (not flat color swatches), record actual contrast ratios", "success": "all text elements meet 4.5:1 on actual backgrounds"}
    ],
    "transfer_tests": [
        {"id": "editorial-to-application", "goal": "Apply typographic principles from an editorial layout to a data-dense application UI", "success": "hierarchy transfers, density adapts, identity survives"},
        {"id": "brand-swap", "goal": "Swap typefaces while preserving all hierarchy, measure, and readability constraints", "success": "hierarchy intact, new typeface expresses different character"}
    ],
    "golden_tasks": [
        {"id": "type-system-audit", "description": "Audit a provided UI against all typographic dimensions: hierarchy, measure, contrast, roles, accessibility, responsive behavior", "evidence": "structured audit with specific failure citations"},
        {"id": "type-repair", "description": "Given a typography system with identified failures, produce a repaired system with rationales", "evidence": "before/after with role assignments, scale table, breakpoint behavior"},
        {"id": "responsive-scale-test", "description": "Test type scale survival across 4 breakpoints, diagnose collapse points", "evidence": "breakpoint comparison table with specific hierarchy measurements"}
    ],
    "cross_pack_links": {
        "depends_on": ["COMPOSITION_VALUE_COLOR_CORE", "FRONTEND_UI_UX_CORE"],
        "feeds_into": ["UI_UX_INTERACTION_CORE", "MOTION_DESIGN_CORE", "ART_DIRECTION_LOOKDEV_CORE"],
        "relationship": "Typography is the structural material that gives composition its verbal dimension and frontend its information voice"
    },
    "evidence_requirements": ["type scale table", "role assignment map", "contrast audit", "responsive breakpoint evidence", "before/after repair", "transfer artifact"],
    "sources": [
        {"title": "WCAG 2.2 — Contrast Minimum (1.4.3)", "url": "https://www.w3.org/TR/WCAG22/#contrast-minimum", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "WCAG 2.2 — Resize Text (1.4.4)", "url": "https://www.w3.org/TR/WCAG22/#resize-text", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "WCAG 2.2 — Text Spacing (1.4.12)", "url": "https://www.w3.org/TR/WCAG22/#text-spacing", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "MDN: CSS Text", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_text", "authority": "MDN Web Docs", "retrieved": "2026-08-23"}
    ],
    "version_sensitive_facts": [
        {"fact": "CSS text-wrap: balance and pretty support", "version": "browser-dependent, check caniuse", "revalidation": "quarterly"},
        {"fact": "Variable font browser support", "version": "96%+ global support as of 2025", "revalidation": "annually"}
    ],
    "known_limits": [
        "Typography quality depends on content context; this pack provides frameworks, not automated grading.",
        "Font licensing must be verified per typeface selected.",
        "Real readability requires human testing; automated metrics are necessary but insufficient."
    ]
}

# ── Pack 3: UI_UX_INTERACTION_CORE ──
uiux = {
    "schema_version": 2, "pack_id": "UI_UX_INTERACTION_CORE",
    "date": "2026-08-23", "status": "ACTIVE",
    "knowledge_class": "evergreen_with_versioned_web_standards",
    "disciplines": ["ui-design", "ux", "interaction-design", "accessibility", "frontend-design"],
    "professional_baseline": {
        "beginner": [
            "can design a single-screen form or task flow",
            "understands basic affordance (buttons look clickable)",
            "designs for one breakpoint coherently",
            "can create a basic state inventory (default, hover, focus, active)"
        ],
        "working_professional": [
            "designs complete task architectures spanning multiple screens/states",
            "understands information scent and progressive disclosure",
            "handles error prevention, validation, and recovery systematically",
            "designs keyboard, touch, and pointer interaction paths",
            "produces state-complete designs (loading, empty, error, edge cases)"
        ],
        "senior": [
            "diagnoses why users get lost or abandon tasks",
            "designs navigation that reveals structure without overwhelming",
            "balances power (expert shortcuts) with learnability (novice guidance)",
            "understands when automation harms user agency",
            "critiques interaction from task evidence, not just heuristic opinion"
        ],
        "lead_director": [
            "establishes interaction language and quality bar across products",
            "aligns UX research, interaction design, visual design, and engineering",
            "protects user outcomes when business/stakeholder pressure pushes dark patterns"
        ]
    },
    "foundations": {
        "task_architecture": [
            {"principle": "task_analysis", "definition": "Map what users need to accomplish before designing screens. Jobs-to-be-done or task analysis precedes layout.", "failure": "screen-first-design: screens designed before understanding what user needs to do"},
            {"principle": "progressive_disclosure", "definition": "Show what is needed now; reveal complexity on demand. Don't present every option at once.", "failure": "control-bombardment: every possible action visible at all times"},
            {"principle": "information_scent", "definition": "Every interaction element should communicate what will happen next. Users forage for information; strong scent reduces abandonment.", "failure": "mystery-navigation: labels don't predict content, users guess and fail"}
        ],
        "interaction_principles": [
            {"principle": "affordance_clarity", "definition": "Interactive elements must look interactive. Buttons look like buttons. Links are distinguishable. Non-interactive elements don't invite clicks.", "failure": "flat-design-extremism: everything looks like everything, users poke randomly"},
            {"principle": "feedback_immediacy", "definition": "Every action produces visible, immediate feedback. No silent operations. No mystery loading states.", "failure": "silent-operation: click produces no visible change, user repeats or abandons"},
            {"principle": "error_prevention_over_recovery", "definition": "Prevent errors before they happen (constraints, defaults, confirmation for destructive actions). Recovery is necessary but prevention is better.", "failure": "blame-the-user: destructive action has no undo, no confirmation, no recovery path"},
            {"principle": "recognition_over_recall", "definition": "Show options; don't require users to remember them. Menus, autocomplete, and visible affordances reduce cognitive load.", "failure": "command-line-memory: users must remember exact commands, paths, or codes"}
        ],
        "state_design": [
            {"principle": "state_inventory", "definition": "Every component has states: default, hover, focus, active, disabled, loading, empty, error, success. Design all of them.", "failure": "state-gaps: loading spinner appears with no explanation, empty state is blank, error message is technical"},
            {"principle": "empty_state_as_onboarding", "definition": "Empty states teach. Show what belongs there, provide a first action, set expectations.", "failure": "void-empty: blank screen with 'No items' and no next step"},
            {"principle": "loading_communication", "definition": "Loading states must communicate what is happening, how long, and whether the user can do anything else. Skeletons > spinners > blank.", "failure": "spinner-everywhere: generic spinner with no context, progress, or cancel option"}
        ],
        "accessibility_interaction": [
            {"principle": "keyboard_completeness", "definition": "Every interactive element reachable and operable via keyboard. Tab order follows visual order. Focus never trapped.", "failure": "mouse-only: critical flows impossible without pointer device"},
            {"principle": "focus_management", "definition": "Focus moves predictably. After modal opens, focus moves inside. After modal closes, focus returns to trigger. Dynamic content changes manage focus.", "failure": "focus-loss: focus disappears after interaction, user disoriented"},
            {"principle": "accessible_names", "definition": "Every interactive element has an accessible name. Icons have labels. Form controls have associated labels. State changes are announced.", "failure": "unnamed-controls: interactive elements read as 'button' with no purpose"}
        ]
    },
    "workflow": [
        "user_task_analysis", "information_architecture",
        "interaction_flow_mapping", "state_inventory_per_component",
        "keyboard_path_design", "touch_target_sizing",
        "error_prevention_review", "loading_empty_error_design",
        "accessibility_audit", "usability_testing_plan",
        "independent_review", "causal_repair", "unseen_transfer_test"
    ],
    "quality_dimensions": {
        "task": ["completeness", "efficiency", "error rate", "learnability", "satisfaction"],
        "interaction": ["affordance clarity", "feedback immediacy", "state coverage", "keyboard operability", "touch operability"],
        "accessibility": ["WCAG 2.2 AA minimum", "screen reader path", "focus management", "reduced motion", "color independence"],
        "resilience": ["error prevention", "recovery paths", "loading communication", "empty state guidance"]
    },
    "failure_patterns": [
        {"id": "form-hostility", "discipline": "interaction", "symptoms": ["validation on submit only", "unclear error location", "lost input on error"], "causes": ["no inline validation", "no input preservation"], "repair": "validate on blur, preserve input, show field-level errors with guidance"},
        {"id": "modal-mismanagement", "discipline": "interaction+accessibility", "symptoms": ["focus not trapped", "escape doesn't close", "background scrolls"], "causes": ["no focus management", "no inert background"], "repair": "trap focus, close on escape, inert background, return focus on close"},
        {"id": "mystery-meat-navigation", "discipline": "information-architecture", "symptoms": ["users cannot find content", "navigation labels vague"], "causes": ["clever labels over clear ones", "no information scent testing"], "repair": "use user language, test navigation comprehension, add breadcrumbs"},
        {"id": "infinite-scroll-trauma", "discipline": "interaction", "symptoms": ["cannot reach footer", "lost position on back navigation", "no pagination alternative"], "causes": ["infinite scroll as default without escape hatch"], "repair": "provide pagination option, preserve scroll position, show count"},
        {"id": "dark-pattern", "discipline": "ux-ethics", "symptoms": ["unsubscribe hidden", "charges without clear consent", "confirmshamed into action"], "causes": ["metrics prioritized over user agency"], "repair": "clear opt-out paths, transparent pricing, no manipulative language"},
        {"id": "motion-sickness", "discipline": "interaction+accessibility", "symptoms": ["parallax nausea", "autoplay video cannot stop", "scroll-jacking"], "causes": ["motion without user control", "prefers-reduced-motion ignored"], "repair": "respect prefers-reduced-motion, add pause controls, never hijack scroll"}
    ],
    "causal_diagnostics": {
        "why_are_users_abandoning_this_flow": [
            "Is there a clear next step at every point?",
            "Are loading states communicating progress?",
            "Are errors helpful (what happened + what to do)?",
            "Is the path completable via keyboard alone?",
            "Did we test with someone who has never seen this before?"
        ],
        "why_does_this_feel_hard_to_use": [
            "Are interactive elements visually distinct from non-interactive?",
            "Does every action produce immediate feedback?",
            "Are destructive actions protected?",
            "Can users recover from mistakes without starting over?",
            "Does the interface remember user choices that matter?"
        ]
    },
    "tools": {
        "design": ["Figma/Penpot wireframes", "interaction specifications", "state inventory documents"],
        "testing": ["Playwright for interaction paths", "axe-core for accessibility", "keyboard-only walkthrough", "screen reader testing"],
        "evidence": ["interaction flow recordings", "keyboard path evidence", "accessibility audit results", "task completion evidence"]
    },
    "micro_labs": [
        {"id": "state-inventory", "goal": "Take a single component and design all 8+ states: default, hover, focus, active, disabled, loading, empty, error, success", "success": "every state visually distinct and appropriate"},
        {"id": "keyboard-path", "goal": "Complete a multi-step task using only keyboard, document every focus transition", "success": "task completable, focus never lost, tab order logical"},
        {"id": "error-friendly-form", "goal": "Design a form that prevents 5 common errors, validates inline, preserves input, and guides recovery", "success": "errors prevented or recovered without data loss"},
        {"id": "empty-state-onboarding", "goal": "Design empty states for 3 different components that teach first action", "success": "user knows exactly what to do first in each"}
    ],
    "transfer_tests": [
        {"id": "desktop-to-mobile-task", "goal": "Redesign a desktop interaction flow for mobile touch without losing task completeness", "success": "task completable via touch, no information loss"},
        {"id": "visual-to-nonvisual", "goal": "Design the interaction path so it works via screen reader without visual reference", "success": "all states announced, all actions reachable, all feedback audible"}
    ],
    "golden_tasks": [
        {"id": "interaction-audit", "description": "Audit a flow against all interaction principles: affordance, feedback, error handling, state coverage, keyboard, accessibility", "evidence": "structured audit with specific failure citations and severity"},
        {"id": "state-repair", "description": "Given a component with missing states, design the complete state inventory", "evidence": "state matrix before/after, rationale for each state design"},
        {"id": "accessibility-path-test", "description": "Complete a task via keyboard and screen reader, document every barrier", "evidence": "barrier log with severity, WCAG reference, repair recommendation"}
    ],
    "cross_pack_links": {
        "depends_on": ["TYPOGRAPHY_INFORMATION_DESIGN_CORE", "FRONTEND_UI_UX_CORE", "COMPOSITION_VALUE_COLOR_CORE"],
        "feeds_into": ["MOTION_DESIGN_CORE", "ART_DIRECTION_LOOKDEV_CORE"],
        "relationship": "Interaction is where typography, composition, and visual hierarchy become usable behavior"
    },
    "evidence_requirements": ["state inventory", "keyboard path evidence", "interaction flow recording", "accessibility audit", "human task evidence where available"],
    "sources": [
        {"title": "WCAG 2.2 — Keyboard (2.1)", "url": "https://www.w3.org/TR/WCAG22/#keyboard-accessible", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "WCAG 2.2 — Focus Order (2.4.3)", "url": "https://www.w3.org/TR/WCAG22/#focus-order", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "ARIA Authoring Practices Guide", "url": "https://www.w3.org/WAI/ARIA/apg/", "authority": "W3C WAI", "retrieved": "2026-08-23"},
        {"title": "NNGroup: 10 Usability Heuristics", "url": "https://www.nngroup.com/articles/ten-usability-heuristics/", "authority": "Nielsen Norman Group", "retrieved": "2026-08-23"}
    ],
    "version_sensitive_facts": [
        {"fact": "CSS :has() selector support enables parent-state styling without JS", "version": "92%+ browser support as of 2025", "revalidation": "quarterly"},
        {"fact": "Popover API and invokers for accessible overlays", "version": "browser-dependent", "revalidation": "quarterly"}
    ],
    "known_limits": [
        "UX quality cannot be certified from screenshots alone.",
        "Real usability requires task evidence with representative users.",
        "This pack provides professional frameworks; human testing remains essential.",
        "Heuristic evaluation is not usability testing."
    ]
}

# ── Pack 4: MOTION_DESIGN_CORE ──
motion = {
    "schema_version": 2, "pack_id": "MOTION_DESIGN_CORE",
    "date": "2026-08-23", "status": "ACTIVE",
    "knowledge_class": "evergreen_fundamentals_with_versioned_web_motion",
    "disciplines": ["motion-design", "interaction-design", "frontend-design", "animation", "accessibility"],
    "professional_baseline": {
        "beginner": [
            "can animate opacity, transform, and position with CSS transitions",
            "understands easing vs linear motion",
            "can apply hover transitions to interactive elements",
            "respects prefers-reduced-motion as binary on/off"
        ],
        "working_professional": [
            "designs motion that communicates state change, spatial relationship, and causality",
            "uses duration hierarchy (micro 100-200ms, macro 300-500ms, page 500-1000ms)",
            "orchestrates staggered animations with intentional delay relationships",
            "designs enter/exit/layout-shift animations that preserve spatial understanding",
            "handles reduced-motion with meaningful alternatives, not just disabling"
        ],
        "senior": [
            "diagnoses why motion feels 'off' — timing, easing, spatial inconsistency",
            "designs motion language consistent with visual identity and interaction model",
            "understands when motion adds clarity vs when it adds noise",
            "critiques motion from performance, accessibility, and perceptual perspectives simultaneously"
        ],
        "lead_director": [
            "establishes motion language that scales across products and platforms",
            "knows when motion enhances brand vs when it impedes usability",
            "approves motion with awareness of frame budget, accessibility law, and device diversity"
        ]
    },
    "foundations": {
        "motion_purpose": [
            {"principle": "motion_explains_state", "definition": "Motion's primary job is to explain what changed, where it came from, where it went, and why. Decorative motion is secondary and must not impede understanding.", "failure": "motion-as-decoration: animation exists purely for visual interest, obscures rather than explains"},
            {"principle": "causal_motion", "definition": "Actions should have visible consequences. A tap causes a ripple. A delete causes the item to leave. A navigation causes directionally appropriate movement.", "failure": "acausal-motion: things animate with no clear trigger or relationship to user action"},
            {"principle": "continuity", "definition": "Motion bridges states so users maintain spatial understanding. A card expanding to full page communicates 'this is the same object.'", "failure": "hard-cut: state change with no transition destroys spatial model"}
        ],
        "temporal_principles": [
            {"principle": "duration_hierarchy", "definition": "Micro-interactions (100-200ms), component transitions (200-400ms), page transitions (300-700ms). Duration communicates importance and distance.", "failure": "uniform-duration: everything takes exactly 300ms regardless of distance or importance"},
            {"principle": "easing_intentionality", "definition": "Ease-out for entering (decelerating into position). Ease-in for exiting (accelerating away). Custom curves for branded motion. Never linear.", "failure": "linear-default: linear easing produces robotic, unnatural movement"},
            {"principle": "staggering", "definition": "Multiple elements animating simultaneously should stagger (20-50ms delay between items) to create readable sequence rather than simultaneous noise.", "failure": "simultaneous-flash: everything animates at once, eye cannot track"},
            {"principle": "anticipation_and_settle", "definition": "Meaningful motion often has anticipation (preparing for action) and settle (overshooting and correcting). These phases communicate physicality.", "failure": "abrupt-start-stop: motion begins and ends with no preparation or deceleration"}
        ],
        "spatial_principles": [
            {"principle": "directional_consistency", "definition": "Navigation forward moves content right-to-left. Going back moves left-to-right. Expanding downward reveals more. Inconsistent direction destroys spatial model.", "failure": "direction-chaos: forward moves left, back moves down, expand moves up"},
            {"principle": "shared_element_transition", "definition": "When an element appears in two different contexts, animate between them to communicate they are the same thing.", "failure": "disconnected-views: same content in two places with no spatial bridge"},
            {"principle": "z_space_clarity", "definition": "Elements moving toward the user (modals, overlays) should scale up or translate in Z. Elements receding should scale down. Motion communicates depth.", "failure": "flat-motion: all movement in screen plane regardless of depth relationship"}
        ],
        "accessibility_motion": [
            {"principle": "reduced_motion_is_not_no_motion", "definition": "prefers-reduced-motion does not mean disable all animation. It means reduce vestibular triggers: no large parallax, no spinning, no rapid flashing, reduced distance/duration.", "failure": "all-or-nothing: reduced motion kills all animation including important state communication"},
            {"principle": "no_flashing", "definition": "No content flashes more than 3 times per second (WCAG 2.3.1). Flashing can trigger seizures.", "failure": "strobe-effect: rapid blinking or flashing animation"},
            {"principle": "duration_control", "definition": "Animations triggered by interaction should be brief. Long-running animations should be pausable. Autoplay motion should be stoppable.", "failure": "trapped-in-animation: cannot interact until animation completes"}
        ]
    },
    "workflow": [
        "identify_state_changes_needing_explanation",
        "define_motion_language_duration_easing",
        "design_enter_exit_layout_animations",
        "spatial_consistency_review",
        "stagger_sequence_design",
        "performance_profiling_frame_budget",
        "reduced_motion_alternatives",
        "flashing_seizure_review",
        "independent_review", "causal_repair", "unseen_transfer_test"
    ],
    "quality_dimensions": {
        "communication": ["state change clarity", "spatial relationship", "causality", "attention direction"],
        "craft": ["easing quality", "duration appropriateness", "stagger choreography", "settle behavior"],
        "accessibility": ["reduced-motion alternatives", "no flashing", "duration control", "interruptibility"],
        "performance": ["60fps target", "compositor-only properties", "no layout thrashing", "will-change restraint"],
        "identity": ["motion language coherence", "brand character", "cross-component consistency"]
    },
    "failure_patterns": [
        {"id": "everything-bounces", "discipline": "motion", "symptoms": ["every element has overshoot bounce", "motion feels same across components"], "causes": ["default easing applied universally", "no motion hierarchy"], "repair": "assign easing by purpose: subtle for micro, moderate for component, expressive for branded moments"},
        {"id": "vestibular-assault", "discipline": "motion+accessibility", "symptoms": ["large parallax on scroll", "continuous spinning", "rapid flashing"], "causes": ["motion designed for visual impact without accessibility review"], "repair": "respect prefers-reduced-motion, limit parallax displacement, no auto-spin"},
        {"id": "animation-race", "discipline": "motion+interaction", "symptoms": ["animations overlap unexpectedly", "state changes queue up"], "causes": ["no interrupt handling", "animations fire on every state change"], "repair": "cancel previous animations on new interaction, debounce rapid triggers"},
        {"id": "jank-scroll", "discipline": "motion+performance", "symptoms": ["stutter during animated scroll", "frames drop below 30fps"], "causes": ["animating layout-triggering properties", "no will-change or transform-only strategy"], "repair": "animate only transform and opacity, promote layers, profile frame budget"},
        {"id": "loading-as-entertainment", "discipline": "motion", "symptoms": ["elaborate loading animation longer than the load itself", "no progress communication"], "causes": ["loading animation prioritized over actual loading speed"], "repair": "loading animation must communicate progress; never extend perceived wait"},
        {"id": "reduced-motion-as-afterthought", "discipline": "motion+accessibility", "symptoms": ["reduced motion disables all animation including status indicators"], "causes": ["binary toggle without semantic alternatives"], "repair": "design reduced-motion alternatives that still communicate state change"}
    ],
    "causal_diagnostics": {
        "why_does_this_motion_feel_wrong": [
            "Is the easing appropriate for the action (enter/exit/attention)?",
            "Is the duration proportional to the distance/importance?",
            "Does the direction match the spatial relationship?",
            "Are stagger delays creating readable sequence or just delay?",
            "Does the motion explain the state change or just decorate it?"
        ],
        "why_is_this_motion_janky": [
            "Are you animating only transform and opacity?",
            "Is the element promoted to its own compositor layer?",
            "Are you measuring layout during animation?",
            "Is the frame budget under 16ms (60fps) / 8ms (120Hz)?"
        ]
    },
    "tools": {
        "design": ["CSS animations/transitions", "Web Animations API", "Framer Motion or project animation library"],
        "profiling": ["Chrome DevTools Performance panel", "Rendering > Paint Flashing", "Frame Rendering Stats"],
        "testing": ["Playwright for reduced-motion testing", "manual frame-rate observation", "accessibility motion audit"]
    },
    "micro_labs": [
        {"id": "state-communication", "goal": "Animate 3 state changes (open modal, add item, delete item) using motion that explains what happened", "success": "without labels, observer can identify what changed and where it came from"},
        {"id": "easing-system", "goal": "Define an easing system with 3-4 curves, assign each to a purpose, and apply consistently across components", "success": "every animation uses an intentional curve from the system"},
        {"id": "reduced-motion-redesign", "goal": "Take an animation-heavy interaction and design its reduced-motion alternative that still communicates state", "success": "state change remains clear without vestibular triggers"},
        {"id": "frame-budget", "goal": "Profile an animated page, identify frames exceeding 16ms, and optimize to 60fps", "success": "all frames under 16ms, no layout thrashing detected"}
    ],
    "transfer_tests": [
        {"id": "same-language-different-product", "goal": "Apply the same motion language to a completely different product type", "success": "motion feels coherently branded but appropriate to new context"},
        {"id": "desktop-to-mobile-motion", "goal": "Adapt desktop motion patterns for mobile touch interaction", "success": "spatial clarity survives, gestures feel natural, duration adapts to smaller screen"}
    ],
    "golden_tasks": [
        {"id": "motion-audit", "description": "Audit an interface for motion quality: state communication, easing, duration, spatial consistency, accessibility, performance", "evidence": "structured audit with specific observations and frame analysis"},
        {"id": "motion-system", "description": "Design a complete motion system: duration scale, easing curves with purposes, stagger rules, reduced-motion alternatives", "evidence": "system document with rationale, before/after examples"},
        {"id": "jank-repair", "description": "Given a janky animation, diagnose cause and produce optimized version at 60fps", "evidence": "before/after performance profiles, optimization rationale"}
    ],
    "cross_pack_links": {
        "depends_on": ["UI_UX_INTERACTION_CORE", "COMPOSITION_VALUE_COLOR_CORE", "TYPOGRAPHY_INFORMATION_DESIGN_CORE"],
        "feeds_into": ["FRONTEND_UI_UX_CORE", "ART_DIRECTION_LOOKDEV_CORE"],
        "relationship": "Motion is the temporal dimension of interaction, the activation of composition, and the behavior of typography"
    },
    "evidence_requirements": ["motion system document", "before/after recordings", "performance profiles", "reduced-motion evidence", "transfer artifact"],
    "sources": [
        {"title": "WCAG 2.2 — Three Flashes or Below Threshold (2.3.1)", "url": "https://www.w3.org/TR/WCAG22/#three-flashes-or-below-threshold", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "WCAG 2.2 — Pause, Stop, Hide (2.2.2)", "url": "https://www.w3.org/TR/WCAG22/#pause-stop-hide", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "WCAG 2.2 — Motion Actuation (2.5.4)", "url": "https://www.w3.org/TR/WCAG22/#motion-actuation", "authority": "W3C Recommendation", "retrieved": "2026-08-23"},
        {"title": "MDN: prefers-reduced-motion", "url": "https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion", "authority": "MDN Web Docs", "retrieved": "2026-08-23"},
        {"title": "Material Design: Motion", "url": "https://m3.material.io/styles/motion/overview", "authority": "Google Material Design", "retrieved": "2026-08-23"}
    ],
    "version_sensitive_facts": [
        {"fact": "Scroll-driven animations (CSS scroll-timeline)", "version": "browser-dependent, check caniuse", "revalidation": "quarterly"},
        {"fact": "View Transitions API browser support", "version": "Chrome 111+, expanding", "revalidation": "quarterly"}
    ],
    "known_limits": [
        "Motion quality is inherently temporal; static screenshots cannot evaluate it.",
        "60fps on developer machine does not guarantee 60fps on target devices.",
        "Motion taste is subjective; professional principles guide, not dictate.",
        "Real vestibular impact requires user testing, not just WCAG compliance."
    ]
}

# ── Write all files ──
packs = [
    ("composition-value-color-core.json", composition),
    ("typography-information-design-core.json", typography),
    ("ui-ux-interaction-core.json", uiux),
    ("motion-design-core.json", motion),
]

for filename, data in packs:
    path = os.path.join(BASE, filename)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Written: {filename} ({len(json.dumps(data))} bytes)")

# Verify
print("\n=== Depth verification ===")
for filename, _ in packs:
    path = os.path.join(BASE, filename)
    d = json.load(open(path))
    has = lambda k: k in d and len(d[k]) > 0
    score = sum([has('professional_baseline'), has('foundations'), has('failure_patterns'), has('micro_labs'), has('golden_tasks'), has('cross_pack_links')])
    print(f"  {filename}: depth={score}/6, keys={len(d)}")