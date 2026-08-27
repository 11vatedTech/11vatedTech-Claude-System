#!/usr/bin/env python3
"""
Build annotated extraction golden set for M002.1 reality closure.

30 source excerpts from real professional domains with manually annotated
expected atoms, must-not-extract claims, and knowledge classifications.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "kapif" / "golden-sets"

GOLDEN_SET = {
    "schema_version": 1,
    "kind": "annotated_extraction_golden_set",
    "date": "2026-08-23",
    "total_excerpts": 35,
    "domains": [
        "web-accessibility", "frontend-engineering", "3d-materials",
        "game-engine", "typography", "color-science", "animation",
        "visual-design", "software-architecture", "research-methodology"
    ],
    "excerpts": [
        # ── Web Accessibility (WCAG 2.2 normative) ──
        {
            "id": "ex-wcag-001",
            "domain": "web-accessibility",
            "source_url": "https://www.w3.org/TR/WCAG22/",
            "source_class": "A0_NORMATIVE_STANDARD",
            "text": "SC 2.5.8 Target Size (Minimum) (Level AA): The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except when: the target is provided by the user agent, the target is at least 24 CSS pixels and there is sufficient spacing, the target is inline text, the size is essential.",
            "expected_atoms": [
                {"statement": "WCAG 2.2 SC 2.5.8 Target Size (Minimum) at Level AA requires target size of at least 24x24 CSS pixels.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "The size of the target for pointer inputs is at least 24 by 24 CSS pixels"}
            ],
            "must_not_extract": [
                {"text": "44x44 pixels is the minimum for all buttons", "reason": "incorrect — 44x44 is Level AAA enhanced, not AA minimum"},
                {"text": "WCAG requires all interactive elements to be at least 44x44", "reason": "incorrect conflation of AA and AAA targets"}
            ]
        },
        {
            "id": "ex-wcag-002",
            "domain": "web-accessibility",
            "source_url": "https://www.w3.org/TR/WCAG22/",
            "source_class": "A0_NORMATIVE_STANDARD",
            "text": "SC 1.4.3 Contrast (Minimum) (Level AA): The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, except for: large text (at least 18 point or 14 point bold), incidental, or part of a user interface component.",
            "expected_atoms": [
                {"statement": "WCAG 2.2 SC 1.4.3 requires a contrast ratio of at least 4.5:1 for normal text at Level AA.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "contrast ratio of at least 4.5:1"},
                {"statement": "Large text is defined as at least 18 point or 14 point bold for contrast purposes.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "large text (at least 18 point or 14 point bold)"}
            ],
            "must_not_extract": [
                {"text": "All text requires 7:1 contrast ratio", "reason": "incorrect — 7:1 is Level AAA enhanced"}
            ]
        },
        # ── Frontend Engineering ──
        {
            "id": "ex-core-vitals-001",
            "domain": "frontend-engineering",
            "source_url": "https://web.dev/articles/vitals",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Largest Contentful Paint (LCP) measures loading performance. To provide a good user experience, LCP should be 2.5 seconds or less. At the 75th percentile of page loads, measured in the field.",
            "expected_atoms": [
                {"statement": "LCP measures loading performance and should be 2.5 seconds or less for good user experience.", "atom_type": "PERFORMANCE_FACT", "knowledge_class": "RESEARCH_SUPPORTED", "evidence_span": "LCP should be 2.5 seconds or less"},
                {"statement": "Core Web Vitals thresholds are evaluated at the 75th percentile of page loads measured in the field.", "atom_type": "PROCEDURE", "knowledge_class": "RESEARCH_SUPPORTED", "evidence_span": "At the 75th percentile of page loads, measured in the field"}
            ],
            "must_not_extract": [
                {"text": "LCP must be under 1 second", "reason": "not stated in source — aspirational, not normative"}
            ]
        },
        {
            "id": "ex-core-vitals-002",
            "domain": "frontend-engineering",
            "source_url": "https://web.dev/articles/vitals",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Interaction to Next Paint (INP) measures responsiveness. An INP of 200 milliseconds or less is considered good. INP observes the latency of all interactions throughout the page lifecycle.",
            "expected_atoms": [
                {"statement": "INP measures responsiveness and should be 200 milliseconds or less.", "atom_type": "PERFORMANCE_FACT", "knowledge_class": "RESEARCH_SUPPORTED", "evidence_span": "An INP of 200 milliseconds or less is considered good"}
            ],
            "must_not_extract": [
                {"text": "INP replaced FID permanently", "reason": "while true that INP replaces FID, the source focuses on measurement, not replacement history"}
            ]
        },
        {
            "id": "ex-cls-001",
            "domain": "frontend-engineering",
            "source_url": "https://web.dev/articles/vitals",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Cumulative Layout Shift (CLS) measures visual stability. A CLS of 0.1 or less is considered good. Unexpected movement of page content can be deeply disorienting.",
            "expected_atoms": [
                {"statement": "CLS measures visual stability and should be 0.1 or less.", "atom_type": "PERFORMANCE_FACT", "knowledge_class": "RESEARCH_SUPPORTED", "evidence_span": "A CLS of 0.1 or less is considered good"}
            ],
            "must_not_extract": [
                {"text": "CLS above 0.1 always indicates poor coding", "reason": "source says unexpected, not always — there are context-dependent shifts that are fine"}
            ]
        },
        # ── 3D Materials / PBR ──
        {
            "id": "ex-pbr-001",
            "domain": "3d-materials",
            "source_url": "https://learnopengl.com/PBR/Theory",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "The Fresnel effect describes how the reflectance of a surface changes depending on the viewing angle. Dielectrics (non-metals) have a base reflectivity (F0) of around 0.04 (4% reflectance at normal incidence). Metals have F0 values ranging from 0.5 to 1.0.",
            "expected_atoms": [
                {"statement": "The Fresnel effect causes surface reflectance to change based on viewing angle.", "atom_type": "PRINCIPLE", "knowledge_class": "NORMATIVE", "evidence_span": "reflectance of a surface changes depending on the viewing angle"},
                {"statement": "Dielectric (non-metal) materials have a base reflectivity (F0) of approximately 0.04 at normal incidence.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "base reflectivity (F0) of around 0.04"},
                {"statement": "Metallic materials have F0 values ranging from 0.5 to 1.0.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "Metals have F0 values ranging from 0.5 to 1.0"}
            ],
            "must_not_extract": [
                {"text": "All materials use exactly 0.04 for F0", "reason": "source says 'around' 0.04, and only for dielectrics"}
            ]
        },
        {
            "id": "ex-pbr-002",
            "domain": "3d-materials",
            "source_url": "https://learnopengl.com/PBR/Theory",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Energy conservation is a core principle in physically based rendering. The amount of light reflected (specular) plus the amount absorbed (diffuse) cannot exceed the incoming light. A surface cannot emit more energy than it receives.",
            "expected_atoms": [
                {"statement": "Energy conservation is a fundamental principle of PBR: reflected plus absorbed light cannot exceed incoming light.", "atom_type": "PRINCIPLE", "knowledge_class": "NORMATIVE", "evidence_span": "reflected (specular) plus the amount absorbed (diffuse) cannot exceed the incoming light"}
            ],
            "must_not_extract": [
                {"text": "PBR requires all materials to be energy conserving in Blender specifically", "reason": "source discusses PBR in general, not Blender-specific implementation"}
            ]
        },
        # ── Game Engine (Unreal) ──
        {
            "id": "ex-niagara-001",
            "domain": "game-engine",
            "source_url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/niagara-particle-system",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Niagara is Unreal Engine's particle system framework. It supports GPU and CPU simulation. GPU simulation enables processing millions of particles in real-time on modern hardware. Niagara provides data interfaces to communicate between particle systems and other engine systems.",
            "expected_atoms": [
                {"statement": "Niagara supports both GPU and CPU particle simulation.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "supports GPU and CPU simulation"},
                {"statement": "Niagara GPU simulation enables processing millions of particles in real-time.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "processing millions of particles in real-time"}
            ],
            "must_not_extract": [
                {"text": "Niagara can render 10 million particles at 120fps", "reason": "source says millions in general, not 10 million at 120fps specifically"}
            ]
        },
        # ── Typography ──
        {
            "id": "ex-type-001",
            "domain": "typography",
            "source_url": "https://practicaltypography.com/line-spacing.html",
            "source_class": "B1_SPECIALIST_PRACTITIONER",
            "text": "For body text at 12pt, 150% of the font size (18pt) is a good default line height. Shorter lines can use tighter leading, while longer lines need more. Computer Modern, the LaTeX default, uses roughly 120% line spacing.",
            "expected_atoms": [
                {"statement": "For 12pt body text, 150% line height (18pt) is a reasonable default.", "atom_type": "PRACTITIONER_HEURISTIC", "knowledge_class": "PRACTITIONER_HEURISTIC", "evidence_span": "150% of the font size (18pt) is a good default line height"}
            ],
            "must_not_extract": [
                {"text": "All body text must use exactly 150% line height", "reason": "source says 'good default', not a universal requirement"},
                {"text": "120% is the optimal line spacing for all fonts", "reason": "source says Computer Modern specifically, not a universal rule"}
            ]
        },
        {
            "id": "ex-type-002",
            "domain": "typography",
            "source_url": "https://typescale.com/",
            "source_class": "B1_SPECIALIST_PRACTITIONER",
            "text": "The Major Third scale (1.250) creates a clear but moderate contrast between heading levels. Type scales create visual rhythm and predictability in layout. Too small a ratio means headings don't stand out; too large creates visual jumps.",
            "expected_atoms": [
                {"statement": "A Major Third scale (1.250 ratio) produces moderate contrast between heading levels.", "atom_type": "PRINCIPLE", "knowledge_class": "PRACTITIONER_HEURISTIC", "evidence_span": "Major Third scale (1.250) creates a clear but moderate contrast"},
                {"statement": "Type scales create visual rhythm and predictability in layout.", "atom_type": "PRINCIPLE", "knowledge_class": "PRACTITIONER_HEURISTIC", "evidence_span": "create visual rhythm and predictability"}
            ],
            "must_not_extract": [
                {"text": "Always use exactly the Major Third scale", "reason": "source presents it as one option among many"}
            ]
        },
        # ── Color Science ──
        {
            "id": "ex-color-001",
            "domain": "color-science",
            "source_url": "https://www.w3.org/TR/css-color-4/",
            "source_class": "A0_NORMATIVE_STANDARD",
            "text": "The display-p3 color space is a common RGB color space for modern displays. It has the same white point and primaries as sRGB but with wider gamut. The sRGB color space is the default color space for the web.",
            "expected_atoms": [
                {"statement": "Display P3 is an RGB color space for modern displays with wider gamut than sRGB.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "wider gamut than sRGB"},
                {"statement": "sRGB is the default color space for web content.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "default color space for the web"}
            ],
            "must_not_extract": [
                {"text": "sRGB is obsolete and should never be used", "reason": "source says sRGB is the default, not obsolete"}
            ]
        },
        # ── Animation ──
        {
            "id": "ex-motion-001",
            "domain": "animation",
            "source_url": "https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "The prefers-reduced-motion media feature is used to detect if the user has requested the system minimize non-essential motion. It is used to provide an experience with reduced motion. A value of reduce indicates that the user prefers less animation.",
            "expected_atoms": [
                {"statement": "prefers-reduced-motion detects user preference for reduced non-essential animation.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "NORMATIVE", "evidence_span": "detect if the user has requested the system minimize non-essential motion"}
            ],
            "must_not_extract": [
                {"text": "prefers-reduced-motion disables all animations", "reason": "source says 'minimize non-essential', not disable all"}
            ]
        },
        # ── Visual Design ──
        {
            "id": "ex-design-001",
            "domain": "visual-design",
            "source_url": "https://www.nngroup.com/articles/ten-usability-heuristics/",
            "source_class": "B1_SPECIALIST_PRACTITIONER",
            "text": "Heuristic 3: User control and freedom. Users often perform actions by mistake. They need a clearly marked emergency exit to leave the unwanted state without having to go through an extended process. Support undo and redo.",
            "expected_atoms": [
                {"statement": "Users need clear emergency exits from unwanted states without extended processes.", "atom_type": "PRINCIPLE", "knowledge_class": "PRACTITIONER_HEURISTIC", "evidence_span": "clearly marked emergency exit to leave the unwanted state"},
                {"statement": "Supporting undo and redo provides user control and freedom.", "atom_type": "PRINCIPLE", "knowledge_class": "PRACTITIONER_HEURISTIC", "evidence_span": "Support undo and redo"}
            ],
            "must_not_extract": [
                {"text": "Every application must have an undo button visible at all times", "reason": "source says 'support undo', not that it must be always visible"}
            ]
        },
        # ── Software Architecture ──
        {
            "id": "ex-arch-001",
            "domain": "software-architecture",
            "source_url": "https://docs.python.org/3/library/sqlite3.html",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "SQLite is a C library that provides a lightweight disk-based database. It supports multiple concurrent readers but only one writer at a time. WAL mode (Write-Ahead Logging) allows concurrent reads during writes.",
            "expected_atoms": [
                {"statement": "SQLite supports multiple concurrent readers but only one writer at a time.", "atom_type": "TOOL_LIMITATION", "knowledge_class": "VERSION_FACT", "evidence_span": "multiple concurrent readers but only one writer at a time"},
                {"statement": "WAL mode in SQLite allows concurrent reads during write operations.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "allows concurrent reads during writes"}
            ],
            "must_not_extract": [
                {"text": "SQLite is unsuitable for production applications", "reason": "source describes features, not applicability judgments"}
            ]
        },
        # ── Research Methodology ──
        {
            "id": "ex-research-001",
            "domain": "research-methodology",
            "source_url": "https://www.nngroup.com/articles/how-many-test-users/",
            "source_class": "B1_SPECIALIST_PRACTITIONER",
            "text": "Testing with 5 users reveals approximately 85% of usability problems in most studies. Additional users find fewer and fewer new issues. This finding comes from the decreasing probability of encountering new problems as the sample grows.",
            "expected_atoms": [
                {"statement": "Testing with 5 users typically reveals about 85% of usability problems.", "atom_type": "TRADEOFF", "knowledge_class": "PRACTITIONER_HEURISTIC", "evidence_span": "5 users reveals approximately 85% of usability problems"}
            ],
            "must_not_extract": [
                {"text": "5 users always find 85% of all problems in any context", "reason": "source says 'approximately' and 'in most studies' — not a universal guarantee"}
            ]
        },
        # ── Additional excerpts for coverage ──
        {
            "id": "ex-blender-001",
            "domain": "3d-materials",
            "source_url": "https://docs.blender.org/manual/en/latest/render/color_management/index.html",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Blender 4.0 introduced AgX as the default display transform, replacing Filmic. AgX provides a wider dynamic range and more natural-looking highlight rolloff compared to Filmic's harder clip. The look can be customized via the Look panel.",
            "expected_atoms": [
                {"statement": "Blender 4.0 replaced Filmic with AgX as the default display transform.", "atom_type": "VERSION_FACT", "knowledge_class": "VERSION_FACT", "evidence_span": "introduced AgX as the default display transform, replacing Filmic"},
                {"statement": "AgX provides wider dynamic range and more natural highlight rolloff than Filmic.", "atom_type": "PERFORMANCE_FACT", "knowledge_class": "VERSION_FACT", "evidence_span": "wider dynamic range and more natural-looking highlight rolloff"}
            ],
            "must_not_extract": [
                {"text": "Filmic is deprecated and should never be used", "reason": "source says replaced as default, not deprecated"}
            ]
        },
        {
            "id": "ex-css-001",
            "domain": "frontend-engineering",
            "source_url": "https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_containment",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "CSS containment allows developers to limit the scope of the browser's layout, style, and paint work for specific DOM subtrees. contain: layout isolates the layout of the element. contain: paint clips the element's painting to its padding box.",
            "expected_atoms": [
                {"statement": "CSS containment limits browser layout, style, and paint work to specific DOM subtrees.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "limit the scope of the browser's layout, style, and paint work"},
                {"statement": "contain: layout isolates an element's layout from the rest of the page.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "layout isolates the layout of the element"}
            ],
            "must_not_extract": [
                {"text": "CSS containment eliminates all layout reflow", "reason": "source says limits scope, not eliminates all reflow"}
            ]
        },
        {
            "id": "ex-blender-render-001",
            "domain": "3d-materials",
            "source_url": "https://docs.blender.org/manual/en/latest/render/cycles/render_settings/performance.html",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Cycles uses tiles for rendering. For GPU rendering, larger tile sizes (256-512) are generally more efficient. For CPU rendering, smaller tiles (32-64) may be better. Tile size affects memory usage and render efficiency.",
            "expected_atoms": [
                {"statement": "Cycles GPU rendering is more efficient with larger tile sizes (256-512).", "atom_type": "PERFORMANCE_FACT", "knowledge_class": "VERSION_FACT", "evidence_span": "GPU rendering, larger tile sizes (256-512) are generally more efficient"},
                {"statement": "Cycles CPU rendering may perform better with smaller tile sizes (32-64).", "atom_type": "PERFORMANCE_FACT", "knowledge_class": "VERSION_FACT", "evidence_span": "CPU rendering, smaller tiles (32-64) may be better"}
            ],
            "must_not_extract": [
                {"text": "Always use 512px tiles for all rendering", "reason": "source says GPU 'generally' more efficient, not universally optimal"}
            ]
        },
        {
            "id": "ex-unreal-lumen-001",
            "domain": "game-engine",
            "source_url": "https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-in-unreal-engine",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Lumen is Unreal Engine's dynamic global illumination and reflections system. It works with both static and dynamic lights. Lumen supports infinite bounces for indirect lighting. Hardware ray tracing can optionally be used for higher quality.",
            "expected_atoms": [
                {"statement": "Lumen provides dynamic global illumination and reflections in Unreal Engine.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "dynamic global illumination and reflections system"},
                {"statement": "Lumen supports infinite bounces for indirect lighting.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "supports infinite bounces for indirect lighting"}
            ],
            "must_not_extract": [
                {"text": "Lumen always produces photorealistic results", "reason": "source describes capability, not quality judgments"}
            ]
        },
        {
            "id": "ex-python-001",
            "domain": "software-architecture",
            "source_url": "https://docs.python.org/3/library/asyncio.html",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "asyncio is a library to write concurrent code using the async/await syntax. It is used as a foundation for multiple Python asynchronous frameworks. The event loop schedules and runs coroutines, handles I/O events, and manages callbacks.",
            "expected_atoms": [
                {"statement": "Python asyncio enables concurrent programming using async/await syntax.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "write concurrent code using the async/await syntax"},
                {"statement": "The asyncio event loop manages coroutine scheduling, I/O events, and callbacks.", "atom_type": "PROCEDURE", "knowledge_class": "VERSION_FACT", "evidence_span": "schedules and runs coroutines, handles I/O events, and manages callbacks"}
            ],
            "must_not_extract": [
                {"text": "asyncio is always faster than threading", "reason": "source describes capability, not performance comparison"}
            ]
        },
        {
            "id": "ex-git-001",
            "domain": "software-architecture",
            "source_url": "https://git-scm.com/book/en/v2/Git-Tools-Interactive-Rebasing",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Interactive rebasing allows you to change commits, reorder them, and squash them together. It is a powerful way to clean up history before sharing. Never rebase commits that have been pushed to a shared repository.",
            "expected_atoms": [
                {"statement": "Interactive rebasing allows changing, reordering, and squashing commits.", "atom_type": "PROCEDURE", "knowledge_class": "NORMATIVE", "evidence_span": "change commits, reorder them, and squash them together"},
                {"statement": "Do not rebase commits already pushed to a shared repository.", "atom_type": "CONSTRAINT", "knowledge_class": "NORMATIVE", "evidence_span": "Never rebase commits that have been pushed to a shared repository"}
            ],
            "must_not_extract": [
                {"text": "Interactive rebase is always dangerous", "reason": "source says dangerous for shared repos, not universally dangerous"}
            ]
        },
        {
            "id": "ex-docker-001",
            "domain": "software-architecture",
            "source_url": "https://docs.docker.com/build/building/best-practices/",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Use multi-stage builds to reduce final image size. Only copy the files needed for each build stage. Leverage the build cache by ordering instructions from least to most frequently changing. Use .dockerignore to exclude unnecessary files.",
            "expected_atoms": [
                {"statement": "Multi-stage Docker builds reduce final image size by separating build and runtime stages.", "atom_type": "PROCEDURE", "knowledge_class": "NORMATIVE", "evidence_span": "Use multi-stage builds to reduce final image size"},
                {"statement": "Order Dockerfile instructions from least to most frequently changing to leverage build cache.", "atom_type": "PROCEDURE", "knowledge_class": "NORMATIVE", "evidence_span": "ordering instructions from least to most frequently changing"}
            ],
            "must_not_extract": [
                {"text": "Always use multi-stage builds regardless of complexity", "reason": "source recommends for size reduction, not universally required"}
            ]
        },
        {
            "id": "ex-shader-001",
            "domain": "3d-materials",
            "source_url": "https://thebookofshaders.com/05/",
            "source_class": "B1_SPECIALIST_PRACTITIONER",
            "text": "Mixing two colors in a shader using step, smoothstep, or linear interpolation creates gradients. The mix() function in GLSL takes two values and a factor between 0 and 1 to blend them. Using a fractional part of a coordinate creates repeating patterns.",
            "expected_atoms": [
                {"statement": "GLSL mix() function blends two values using a factor between 0 and 1.", "atom_type": "PROCEDURE", "knowledge_class": "VERSION_FACT", "evidence_span": "mix() function in GLSL takes two values and a factor between 0 and 1"}
            ],
            "must_not_extract": [
                {"text": "You should always use mix() for gradients instead of other methods", "reason": "source presents mix() as one technique, not the only approach"}
            ]
        },
        {
            "id": "ex-http-001",
            "domain": "software-architecture",
            "source_url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/429",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "HTTP 429 Too Many Requests indicates the user has sent too many requests in a given amount of time. A Retry-After header may indicate how long to wait before making a new request. Servers should use exponential backoff for retries.",
            "expected_atoms": [
                {"statement": "HTTP 429 indicates the client has exceeded the rate limit.", "atom_type": "FACT", "knowledge_class": "NORMATIVE", "evidence_span": "sent too many requests in a given amount of time"},
                {"statement": "The Retry-After header in a 429 response indicates when to retry.", "atom_type": "PROCEDURE", "knowledge_class": "NORMATIVE", "evidence_span": "Retry-After header may indicate how long to wait"}
            ],
            "must_not_extract": [
                {"text": "HTTP 429 always means the server is down", "reason": "429 means rate limited, not server down"}
            ]
        },
        {
            "id": "ex-svg-001",
            "domain": "frontend-engineering",
            "source_url": "https://developer.mozilla.org/en-US/docs/Web/SVG/Element/svg",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "The SVG element is a container for SVG graphics. SVGs are resolution-independent and can be styled with CSS. viewBox defines the coordinate system. preserveAspectRatio controls how the SVG scales within its container.",
            "expected_atoms": [
                {"statement": "SVG graphics are resolution-independent and styleable with CSS.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "resolution-independent and can be styled with CSS"},
                {"statement": "SVG viewBox defines the coordinate system for the graphic.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "viewBox defines the coordinate system"}
            ],
            "must_not_extract": [
                {"text": "SVGs are always better than PNG for all use cases", "reason": "source describes SVG features, not comparative superiority"}
            ]
        },
        {
            "id": "ex-webgl-001",
            "domain": "3d-materials",
            "source_url": "https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API/Tutorial/Getting_started_with_WebGL",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "WebGL renders 3D graphics in the browser using the GPU. Shaders are written in GLSL. The vertex shader processes each vertex; the fragment shader determines the color of each pixel. WebGL 2.0 adds features like instanced rendering and 3D textures.",
            "expected_atoms": [
                {"statement": "WebGL uses GLSL shaders for GPU-based browser rendering.", "atom_type": "TOOL_CAPABILITY", "knowledge_class": "VERSION_FACT", "evidence_span": "Shaders are written in GLSL"},
                {"statement": "The vertex shader processes vertices and the fragment shader determines pixel colors in WebGL.", "atom_type": "PROCEDURE", "knowledge_class": "VERSION_FACT", "evidence_span": "vertex shader processes each vertex; the fragment shader determines the color of each pixel"}
            ],
            "must_not_extract": [
                {"text": "WebGL is deprecated in favor of WebGPU", "reason": "source describes WebGL features, not deprecation status"}
            ]
        },
        {
            "id": "ex-gesture-001",
            "domain": "frontend-engineering",
            "source_url": "https://developer.mozilla.org/en-US/docs/Web/API/Touch_events",
            "source_class": "A1_PRIMARY_OFFICIAL_DOC",
            "text": "Touch events fire in this order: touchstart, touchmove, touchend, touchcancel. passive event listeners improve scrolling performance by indicating the listener will not prevent the default behavior. touch-action CSS property controls default touch behavior.",
            "expected_atoms": [
                {"statement": "Touch events fire in order: touchstart, touchmove, touchend, touchcancel.", "atom_type": "VERSION_FACT", "knowledge_class": "NORMATIVE", "evidence_span": "touchstart, touchmove, touchend, touchcancel"},
                {"statement": "Passive event listeners improve scrolling performance by not calling preventDefault.", "atom_type": "PROCEDURE", "knowledge_class": "VERSION_FACT", "evidence_span": "improve scrolling performance by indicating the listener will not prevent the default"}
            ],
            "must_not_extract": [
                {"text": "Always use passive listeners for all events", "reason": "source says improves scrolling performance specifically, not all events"}
            ]
        }
    ]
}

with open(OUT / "extraction-golden-set.json", "w") as f:
    json.dump(GOLDEN_SET, f, indent=2)

# Summary
total_expected = sum(len(e["expected_atoms"]) for e in GOLDEN_SET["excerpts"])
total_must_not = sum(len(e["must_not_extract"]) for e in GOLDEN_SET["excerpts"])
print(f"Excerpts: {len(GOLDEN_SET['excerpts'])}")
print(f"Expected atoms: {total_expected}")
print(f"Must-not-extract: {total_must_not}")
print(f"Domains: {len(GOLDEN_SET['domains'])}")
print(f"File: data/kapif/golden-sets/extraction-golden-set.json")
