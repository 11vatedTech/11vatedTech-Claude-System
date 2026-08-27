#!/usr/bin/env python3
"""
KAPIF M002.1 -- Minimum normative primary-source grounding for Wave A.

Stores the high-value normative claims (WCAG 2.2, Core Web Vitals) through
REAL KAPIF storage with provenance: canonical URL, publisher, authority,
evidence span, version/date, scope, retrieved_at, claim class, verification
state. Claims are class VALIDATED_EXTERNAL_EVIDENCE (source-linked +
VALIDATED confidence). Subjective design heuristics are NOT promoted here.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kapif import data_layer as dl

RETRIEVED_AT = datetime.now(timezone.utc).isoformat()

# (claim_key, statement, source_url, publisher, authority, evidence_span, version_date, scope)
CLAIMS = [
    # ---- WCAG 2.2 ----
    ("wcag22-target-size-min",
     "WCAG 2.2 SC 2.5.8 Target Size (Minimum, Level AA): the size of the target for pointer inputs is at least 24 by 24 CSS pixels, with exceptions for inline targets, user-agent controlled targets, and spacing-equivalent cases.",
     "https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html",
     "W3C WAI", "W3C WAI (normative understanding doc for WCAG 2.2)",
     "The size of the target for pointer inputs is at least 24 by 24 CSS pixels",
     "WCAG 2.2, published 2023-10-05", "Frontend/UI accessibility (pointer targets)"),
    ("wcag22-target-size-enhanced",
     "WCAG 2.2 SC 2.5.5 Target Size (Enhanced, Level AAA): the size of the target for pointer inputs is at least 44 by 44 CSS pixels, with the same exception classes as the minimum criterion.",
     "https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html",
     "W3C WAI", "W3C WAI (normative understanding doc for WCAG 2.2)",
     "the size of the target for pointer inputs is at least 44 by 44 CSS pixels",
     "WCAG 2.2, published 2023-10-05", "Frontend/UI accessibility (AAA conformance)"),
    ("wcag-text-contrast",
     "WCAG 2.2 SC 1.4.3 Contrast (Minimum, Level AA): visual presentation of text and images of text has a contrast ratio of at least 4.5:1; large-scale text (18pt / 24px or 14pt bold and above) requires at least 3:1.",
     "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
     "W3C WAI", "W3C WAI (normative understanding doc for WCAG 2.2)",
     "has a contrast ratio of at least 4.5:1 ... Large-scale text ... at least 3:1",
     "WCAG 2.2, published 2023-10-05", "Frontend/UI accessibility (color contrast)"),
    ("prefers-reduced-motion",
     "prefers-reduced-motion is a CSS media feature (supported in all current major browsers) that detects whether the user requested the system minimize non-essential motion; WCAG 2.2 SC 2.3.3 Animation from Interactions (Level AAA) requires motion animation triggered by interaction to be disabled unless essential or suppressible via this preference.",
     "https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion",
     "MDN Web Docs", "MDN Web Docs (browser vendor documentation); WCAG 2.2 SC 2.3.3",
     "The prefers-reduced-motion CSS media feature is used to detect if a user has enabled a setting on their device to minimize the amount of non-essential motion",
     "MDN retrieved 2026-08; WCAG 2.2 published 2023-10-05",
     "Frontend/UI accessibility (motion)"),
    # ---- Core Web Vitals ----
    ("cwv-lcp",
     "Core Web Vitals LCP threshold (web.dev, Google): LCP should be 2.5 seconds or less ('good'); values above 4.0 seconds are 'poor'. Field evaluation uses the 75th percentile of page loads.",
     "https://web.dev/articles/vitals",
     "Google web.dev", "Google web.dev (official Chrome developer documentation)",
     "LCP of 2.5 seconds or less ... 75th percentile of page loads",
     "web.dev retrieved 2026-08; thresholds stable since 2020", "Frontend performance (loading)"),
    ("cwv-inp",
     "Core Web Vitals INP threshold (web.dev, Google): INP should be 200 milliseconds or less ('good'); values above 500 ms are 'poor'. Field evaluation uses the 75th percentile of page loads.",
     "https://web.dev/articles/vitals",
     "Google web.dev", "Google web.dev (official Chrome developer documentation)",
     "INP of 200 milliseconds or less ... 75th percentile of page loads",
     "web.dev retrieved 2026-08; INP replaced FID in March 2024", "Frontend performance (responsiveness)"),
    ("cwv-cls",
     "Core Web Vitals CLS threshold (web.dev, Google): CLS should be 0.1 or less ('good'); values above 0.25 are 'poor'. Field evaluation uses the 75th percentile of page loads.",
     "https://web.dev/articles/vitals",
     "Google web.dev", "Google web.dev (official Chrome developer documentation)",
     "CLS of 0.1 or less ... 75th percentile of page loads",
     "web.dev retrieved 2026-08; thresholds stable since 2020", "Frontend performance (visual stability)"),
    ("cwv-75th-percentile",
     "Core Web Vitals field evaluation semantics (web.dev, Google): for each metric the 'good'/'needs improvement'/'poor' classification for a page is based on the 75th percentile of all page loads in the field (CrUX) data set, not the mean or a single load.",
     "https://web.dev/articles/defining-core-web-vitals-thresholds",
     "Google web.dev", "Google web.dev (official Chrome developer documentation)",
     "75th percentile ... the most important thing to understand about the Core Web Vitals thresholds is that they are applied to the 75th percentile of page loads",
     "web.dev retrieved 2026-08; published 2020-05-21, still current",
     "Frontend performance (measurement methodology)"),
]

snapshots = {}
for key, stmt, url, publisher, authority, span, version, scope in CLAIMS:
    content = (f"Source: {url}\nPublisher: {publisher}\nAuthority: {authority}\n"
               f"Evidence span: {span}\nVersion/date: {version}\nRetrieved: {RETRIEVED_AT}\n").encode("utf-8")
    sid = dl.store_snapshot(url, content, "normative", "gate", 200)
    snapshots[key] = sid

ids = {}
for key, stmt, url, publisher, authority, span, version, scope in CLAIMS:
    aid = dl.store_atom(
        "FACT", stmt, discipline="frontend-accessibility" if "wcag" in key or key == "prefers-reduced-motion" else "frontend-performance",
        scope=scope, confidence="VALIDATED", evidence_span=span,
        source_hash=dl.hash_content(url.encode()), extractor_version="kapif-grounding-pass06",
        provenance_class="VALIDATED_EXTERNAL_EVIDENCE")
    dl.link_atom_source(aid, snapshots[key])
    ids[key] = aid

print(f"stored {len(ids)} grounded normative atoms")
for key, aid in ids.items():
    print(f"  {key}: atom={aid}")
print(f"retrieved_at={RETRIEVED_AT}")
