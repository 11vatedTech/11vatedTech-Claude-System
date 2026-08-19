#!/usr/bin/env python3
"""Check that a visual evidence markdown record contains required proof fields."""
from __future__ import annotations
import sys
from pathlib import Path

REQUIRED = [
    "## Scope",
    "## Build/runtime",
    "## Viewports inspected",
    "## Interaction states inspected",
    "## Console/network/server health",
    "## Accessibility evidence",
    "## Visual QA critique",
    "## Remaining limitations",
]


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: visual_evidence_check.py <evidence.md>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"missing_evidence {path}")
        return 1
    text = path.read_text(encoding="utf-8", errors="ignore")
    missing = [heading for heading in REQUIRED if heading not in text]
    if missing:
        for heading in missing:
            print(f"missing_heading {heading}")
        return 1
    weak = []
    for marker in ["desktop", "mobile", "screenshot", "console", "accessibility"]:
        if marker not in text.lower():
            weak.append(marker)
    for marker in weak:
        print(f"weak_or_absent_marker {marker}")
    if weak:
        return 1
    print(f"visual_evidence_ok {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
