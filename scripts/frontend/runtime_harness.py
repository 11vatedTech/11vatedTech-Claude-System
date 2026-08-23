#!/usr/bin/env python3
"""Frontend runtime quality harness — Playwright + axe-core + Lighthouse.

Captures real browser behaviour: screenshots with environment fingerprints,
accessibility scans, Lighthouse audits, console/network observation, and
keyboard navigation evidence.

This harness produces machine-readable evidence that the existing
frontend_quality_contract.py validates.  It does NOT certify visual design,
UX, or creative quality — those require perceptual / human review."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "tools" / "frontend"
sys.path.insert(0, str(FRONTEND_DIR / "py-deps"))

# ── environment fingerprint ────────────────────────────────────────────


def _playwright_version() -> str:
    pkg = FRONTEND_DIR / "node_modules" / "playwright-core" / "package.json"
    if pkg.exists():
        return json.loads(pkg.read_text(encoding="utf-8")).get("version", "unknown")
    return "unknown"


def _env_fingerprint(browser: str, browser_version: str, pw_version: str,
                     viewport: dict, headless: bool) -> dict:
    return {
        "os": platform.system(),
        "os_release": platform.release(),
        "browser": browser,
        "browser_version": browser_version,
        "playwright_version": pw_version,
        "headless": headless,
        "viewport": viewport,
        "device_scale_factor": 1,
        "locale": "en-US",
        "timezone": "America/Los_Angeles",
        "color_scheme": "light",
        "reduced_motion": "no-preference",
    }


def _captured_at() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ── axe-core runner ────────────────────────────────────────────────────


def _axe_script() -> str:
    axe_path = FRONTEND_DIR / "node_modules" / "axe-core" / "axe.min.js"
    return axe_path.read_text(encoding="utf-8")


# ── Lighthouse runner ──────────────────────────────────────────────────


def _run_lighthouse(url: str, out_dir: Path, runs: int = 3) -> list[dict]:
    lh_js = str(FRONTEND_DIR / "node_modules" / "lighthouse" / "cli" / "index.js")
    results: list[dict] = []
    for i in range(runs):
        out_path = out_dir / f"lighthouse-run-{i + 1}.json"
        cmd = [
            "node", lh_js, url,
            "--output=json",
            f"--output-path={out_path}",
            "--chrome-flags=--headless --no-sandbox",
            "--only-categories=accessibility,performance,best-practices",
        ]
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(ROOT))
            if out_path.exists():
                results.append(json.loads(out_path.read_text(encoding="utf-8")))
        except Exception as exc:
            results.append({"error": str(exc)})
    return results


# ── main harness ───────────────────────────────────────────────────────


def run_harness(page_url: str, states: list[dict], viewports: list[dict],
                out_dir: Path, headless: bool = True,
                capture_lighthouse: bool = True) -> dict:
    """Execute frontend quality matrix and produce evidence artifact."""

    from playwright.sync_api import sync_playwright

    out_dir.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, Any] = {
        "schema_version": 2,
        "kind": "frontend-runtime-evidence",
        "captured_at": _captured_at(),
        "page_url": page_url,
        "state_matrix": [],
        "accessibility": {},
        "console_errors": [],
        "network_failures": [],
        "keyboard_traversal": {},
        "lighthouse": [],
        "blockers": [],
        "environment_fingerprints": [],
    }

    with sync_playwright() as pw:
        # Use existing npm-managed chromium, or system Chrome as fallback
        npm_chromium = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright" / "chromium-1234" / "chrome-win64" / "chrome.exe"
        launch_args = {"headless": headless}
        if npm_chromium.exists():
            launch_args["executable_path"] = str(npm_chromium)
        else:
            launch_args["channel"] = "chrome"
        browser = pw.chromium.launch(**launch_args)
        pw_version = _playwright_version()
        browser_version = browser.version

        for vp_def in viewports:
            vp_name = vp_def.get("name", f"{vp_def['width']}x{vp_def['height']}")
            vp = {"width": vp_def["width"], "height": vp_def["height"]}
            fp = _env_fingerprint("chromium", browser_version, pw_version, vp, headless)
            evidence["environment_fingerprints"].append(fp)

            for st in states:
                state_name = st.get("name", "default")
                ctx = browser.new_context(
                    viewport=vp,
                    device_scale_factor=1,
                    locale="en-US",
                    timezone_id="America/Los_Angeles",
                    color_scheme=st.get("color_scheme", "light"),
                    reduced_motion="reduce" if st.get("reduced_motion") else "no-preference",
                )
                page = ctx.new_page()

                # Collect console errors
                page.on("console", lambda msg: (
                    evidence["console_errors"].append({
                        "type": msg.type, "text": msg.text,
                        "state": state_name, "viewport": vp_name,
                    }) if msg.type == "error" else None
                ))

                # Collect network failures
                page.on("response", lambda resp: (
                    evidence["network_failures"].append({
                        "url": resp.url, "status": resp.status,
                        "state": state_name, "viewport": vp_name,
                    }) if resp.status >= 400 else None
                ))

                page.goto(page_url, wait_until="networkidle", timeout=30000)

                # Apply state interactions
                for action in st.get("actions", []):
                    sel = action.get("selector")
                    if not sel:
                        continue
                    if action.get("type") == "click":
                        page.click(sel, timeout=5000)
                    elif action.get("type") == "hover":
                        page.hover(sel, timeout=5000)
                    elif action.get("type") == "focus":
                        page.focus(sel, timeout=5000)
                    elif action.get("type") == "fill":
                        page.fill(sel, action.get("value", ""), timeout=5000)
                    page.wait_for_timeout(300)

                # Screenshot
                ss_path = out_dir / f"{vp_name}_{state_name}.png"
                ss_path = ss_path.with_name(ss_path.name.replace(" ", "_").replace("/", "_"))
                page.screenshot(path=str(ss_path), full_page=True)

                evidence["state_matrix"].append({
                    "viewport": vp_name,
                    "state": state_name,
                    "screenshot": str(ss_path.relative_to(out_dir)),
                    "environment_fingerprint": fp,
                })

                # Axe scan (first viewport only to avoid duplication)
                if vp_name == viewports[0].get("name", f"{viewports[0]['width']}x{viewports[0]['height']}"):
                    try:
                        page.evaluate(_axe_script())
                        axe_result = page.evaluate("() => axe.run(document)")
                        evidence["accessibility"] = {
                            "violations": axe_result.get("violations", []),
                            "passes_count": len(axe_result.get("passes", [])),
                            "timestamp": _captured_at(),
                        }
                    except Exception as exc:
                        evidence["blockers"].append(f"axe_scan_failed: {exc}")

                # Keyboard traversal (first state only)
                if evidence.get("keyboard_traversal") == {}:
                    try:
                        page.keyboard.press("Tab")
                        page.wait_for_timeout(200)
                        focused = page.evaluate("() => document.activeElement?.tagName || 'none'")
                        evidence["keyboard_traversal"] = {
                            "initial_focus": focused,
                            "tab_sequence_available": focused != "BODY",
                            "note": "basic focus check only; full keyboard audit requires manual verification",
                        }
                    except Exception:
                        evidence["keyboard_traversal"] = {"error": "keyboard check failed"}

                ctx.close()

        browser.close()

    # Lighthouse (offline, after browser session)
    if capture_lighthouse:
        evidence["lighthouse"] = _run_lighthouse(page_url, out_dir, runs=3)

    # Summary
    evidence["summary"] = {
        "states_tested": len(evidence["state_matrix"]),
        "viewports_tested": len(viewports),
        "screenshots_captured": len(evidence["state_matrix"]),
        "console_errors": len(evidence["console_errors"]),
        "network_failures": len(evidence["network_failures"]),
        "axe_violations": len(evidence.get("accessibility", {}).get("violations", [])),
        "lighthouse_runs": len(evidence.get("lighthouse", [])),
        "keyboard_baseline": bool(evidence.get("keyboard_traversal", {}).get("initial_focus")),
    }

    return evidence


# ── state matrix builder ───────────────────────────────────────────────


def build_state_matrix(include_states: Optional[list[str]] = None,
                       include_viewports: Optional[list[str]] = None) -> tuple[list[dict], list[dict]]:
    """Return canonical state and viewport definitions."""

    all_states = [
        {"name": "default"},
        {"name": "hover", "actions": [{"selector": "a:first-of-type", "type": "hover"}]},
        {"name": "focus", "actions": [{"selector": "body", "type": "focus"}]},
        {"name": "loading"},
        {"name": "empty"},
        {"name": "error"},
        {"name": "success"},
        {"name": "dark", "color_scheme": "dark"},
        {"name": "reduced_motion", "reduced_motion": True},
    ]

    all_viewports = [
        {"name": "desktop", "width": 1440, "height": 900},
        {"name": "tablet", "width": 768, "height": 1024},
        {"name": "mobile", "width": 375, "height": 812},
    ]

    states = [s for s in all_states if not include_states or s["name"] in include_states]
    viewports = [v for v in all_viewports if not include_viewports or v["name"] in include_viewports]
    return states, viewports


# ── CLI ────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Page URL to audit")
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "frontend" / "runtime-evidence.json")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--no-lighthouse", action="store_true")
    parser.add_argument("--states", nargs="*")
    parser.add_argument("--viewports", nargs="*")
    args = parser.parse_args()

    states, viewports = build_state_matrix(args.states, args.viewports)
    result = run_harness(
        page_url=args.url,
        states=states,
        viewports=viewports,
        out_dir=args.out.parent,
        headless=not args.headed,
        capture_lighthouse=not args.no_lighthouse,
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())