#!/usr/bin/env python3
"""
KAPIF Content Normalizer + Security Quarantine.

THIS IS A HARD SECURITY LAW: All external acquired content is UNTRUSTED_DATA.
It is NEVER system instruction, developer instruction, tool authorization, or mission change.

Two-plane architecture:
  UNTRUSTED READING PLANE: network read, parsing, extraction, injection scanning → structured output
  PRIVILEGED FOUNDRY PLANE: receives only schema-validated structured output, never raw imperative web content
"""
from __future__ import annotations

import re
from typing import Any

# ── Prompt injection patterns ──

INJECTION_PATTERNS = [
    # System instruction overrides
    r"(?i)(ignore|disregard|override|forget).*(previous|all|above).*(instruction|prompt|system|rule)",
    r"(?i)(you are now|you are no longer|your new role is|your new identity is)",
    r"(?i)(system prompt|system message|system instruction).*(is now|has been changed|is overridden)",
    r"(?i)(do not follow|do not obey|never follow).*(instruction|rule|guideline)",
    # Tool call injection
    r"(?i)<tool_call>|</tool_call>|<function_call>|</function_call>",
    r"(?i)<\|tool_calls\|>|</\|tool_calls\|>",
    r"(?i)\{.*\"name\".*\"arguments\".*\}",
    # Memory/context poisoning
    r"(?i)(remember this|store this|save this).*(permanently|forever|always)",
    r"(?i)(add to memory|update memory|this is now true)",
    # Fake system messages
    r"(?i)<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]",
    r"(?i)Human:|Assistant:|System:|User:",
]

# ── Content normalization ──


def normalize_html(html: str, url: str = "") -> dict[str, Any]:
    """Strip scripts, styles, hidden elements, tracking params from HTML. Returns (normalized, warnings)."""
    warnings = []

    # Remove script and style blocks
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style[^>]*>.*?</style>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<noscript[^>]*>.*?</noscript>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Remove hidden/invisible elements
    if re.search(r"(display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0|hidden\s*=\s*[\"']hidden[\"']|aria-hidden\s*=\s*[\"']true[\"'])", cleaned, re.IGNORECASE):
        warnings.append("hidden_elements_detected")

    # Remove HTML comments
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)

    # Strip remaining tags for text extraction
    text = re.sub(r"<[^>]+>", " ", cleaned)
    text = re.sub(r"\s+", " ", text).strip()

    # Remove tracking parameters from links
    text = re.sub(r"[\?&](utm_|fbclid|gclid|ref|source|mc_)[^&\s]*", "", text)

    # Unicode control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    return {"text": text, "warnings": warnings, "char_count": len(text)}


def normalize_markdown(md: str, url: str = "") -> dict[str, Any]:
    """Strip HTML blocks and hidden content from markdown."""
    warnings = []
    cleaned = re.sub(r"<script[^>]*>.*?</script>", "", md, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<!--.*?-->", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\[/?INST\]", "", cleaned)
    cleaned = re.sub(r"<\|im_start\|>.*?<\|im_end\|>", "", cleaned, flags=re.DOTALL)
    return {"text": cleaned.strip(), "warnings": warnings, "char_count": len(cleaned)}


def normalize_json(data: dict | list, url: str = "") -> dict[str, Any]:
    """JSON is already structured — just extract readable text."""
    text = str(data)
    return {"text": text, "warnings": [], "char_count": len(text)}


# ── Injection scanning ──


def scan_injections(text: str) -> dict[str, Any]:
    """Scan normalized content for prompt injection patterns. Returns (flagged, matches)."""
    matches = []
    for pattern in INJECTION_PATTERNS:
        found = re.findall(pattern, text, re.IGNORECASE)
        for m in found:
            matches.append({"pattern": pattern, "match": str(m)[:200]})

    # Also check for base64-encoded suspicious content
    b64_matches = re.findall(r"[A-Za-z0-9+/]{40,}={0,2}", text)
    suspicious_b64 = []
    for b64 in b64_matches[:5]:
        try:
            import base64
            decoded = base64.b64decode(b64).decode("utf-8", errors="replace")
            if any(re.search(p, decoded, re.IGNORECASE) for p in INJECTION_PATTERNS[:5]):
                suspicious_b64.append(b64[:40] + "...")
        except Exception:
            pass

    flagged = len(matches) > 0 or len(suspicious_b64) > 0
    return {
        "flagged": flagged,
        "injection_matches": matches[:10],
        "suspicious_base64": suspicious_b64,
        "flagged_count": len(matches) + len(suspicious_b64),
    }


def normalize_and_scan(content: bytes | str, content_type: str = "text/html",
                       url: str = "") -> dict[str, Any]:
    """Full normalization + injection scan pipeline. Returns structured output only."""
    if isinstance(content, bytes):
        raw: str = content.decode("utf-8", errors="replace")
    else:
        raw = content

    # Normalize
    if "html" in content_type or "xml" in content_type:
        result = normalize_html(raw, url)
    elif "markdown" in content_type or "text/md" in content_type:
        result = normalize_markdown(raw, url)
    elif "json" in content_type:
        result = normalize_json(raw, url)  # type: ignore[arg-type]
    else:
        result = normalize_html(raw, url)  # Best-effort

    # Security scan
    injection = scan_injections(result["text"])

    result["injection"] = injection
    result["safe_for_privileged_plane"] = not injection["flagged"]

    return result


# ── Quarantine gate ──


class UntrustedContent:
    """Quarantine wrapper. Raw content must pass through this before touching the Foundry."""

    def __init__(self, raw_bytes: bytes, url: str, content_type: str = "text/html",
                 adapter: str = "unknown", upstream_quarantined: bool = False):
        self.raw = raw_bytes
        self.url = url
        self.content_type = content_type
        self.adapter = adapter
        self.upstream_quarantined = upstream_quarantined
        self._result: dict[str, Any] | None = None

    def process(self) -> dict[str, Any]:
        if self._result is None:
            self._result = normalize_and_scan(self.raw, self.content_type, self.url)
            if self.upstream_quarantined:
                self._result.setdefault("warnings", []).append("upstream_source_quarantined")
                self._result["safe_for_privileged_plane"] = False
                self._result["quarantine_reason"] = "upstream_source_quarantined"
        return self._result

    @property
    def is_safe(self) -> bool:
        return self.process().get("safe_for_privileged_plane", False) and not self.upstream_quarantined

    @property
    def text(self) -> str:
        return self.process().get("text", "")

    @property
    def injection_flagged(self) -> bool:
        return self.process().get("injection", {}).get("flagged", False)