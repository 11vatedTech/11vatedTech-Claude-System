#!/usr/bin/env python3
"""Read-only Wave A before-state capture for the Pumkit frontend."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NODE_DIR = ROOT / "tools" / "frontend" / "node_modules"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(ROOT / "tools" / "frontend" / "py-deps"))
    from playwright.sync_api import sync_playwright

    viewports = [
        ("desktop-wide", 1440, 900),
        ("desktop-laptop", 1280, 800),
        ("desktop-narrow", 1024, 768),
        ("mobile", 375, 812),
        ("mobile-narrow", 320, 700),
        ("tablet", 768, 1024),
    ]
    states = ["default", "liquid", "behavior-alert", "field-mode"]
    evidence = {
        "schema_version": 1,
        "kind": "wave-a-pumkit-before-evidence",
        "url": args.url,
        "read_only": True,
        "viewports": [],
        "console_errors": [],
        "network_failures": [],
        "observations": [],
    }

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe", headless=True)
        for name, width, height in viewports:
            for state in states:
                context = browser.new_context(viewport={"width": width, "height": height})
                page = context.new_page()
                page.on("console", lambda msg, n=name, s=state: evidence["console_errors"].append({"viewport": n, "state": s, "type": msg.type, "text": msg.text}) if msg.type == "error" else None)
                page.on("response", lambda response, n=name, s=state: evidence["network_failures"].append({"viewport": n, "state": s, "url": response.url, "status": response.status}) if response.status >= 400 else None)
                page.goto(args.url, wait_until="networkidle", timeout=30000)
                if state == "liquid":
                    page.locator(".liquid-trigger").click()
                elif state == "behavior-alert":
                    page.locator('[data-state="alert"]').click()
                elif state == "field-mode":
                    page.locator(".field-toggle").click()
                page.wait_for_timeout(500)
                shot = args.out / f"{name}__{state}.png"
                page.screenshot(path=str(shot), full_page=True)
                observation = page.evaluate("""() => {
                  const rect = (selector) => { const el = document.querySelector(selector); if (!el) return null; const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return {selector, x:r.x, y:r.y, width:r.width, height:r.height, display:s.display, position:s.position, zIndex:s.zIndex, overflow:s.overflow, color:s.color, backgroundColor:s.backgroundColor, fontSize:s.fontSize, lineHeight:s.lineHeight}; };
                  const links = [...document.querySelectorAll('a,button,[tabindex]')].map((el, i) => ({i, tag:el.tagName, text:(el.innerText || el.getAttribute('aria-label') || '').trim().slice(0,120), ariaPressed:el.getAttribute('aria-pressed'), href:el.getAttribute('href'), tabIndex:el.tabIndex, disabled:el.disabled}));
                  const overflow = [...document.querySelectorAll('body,main,section,.topbar,nav')].map(el => { const r=el.getBoundingClientRect(); return {selector:el.tagName+'.'+el.className, scrollWidth:el.scrollWidth, clientWidth:el.clientWidth, overflowX:getComputedStyle(el).overflowX, clipped:el.scrollWidth>el.clientWidth+1, rect:{x:r.x,y:r.y,width:r.width,height:r.height}}; });
                  return {title:document.title, viewport:{width:innerWidth,height:innerHeight}, bodyText:document.body.innerText.slice(0,1000), landmarkCounts:{main:document.querySelectorAll('main').length, nav:document.querySelectorAll('nav').length, header:document.querySelectorAll('header').length}, hero:rect('.hero-character'), heroImage:rect('.hero-character img'), topbar:rect('.topbar'), nav:rect('nav'), fieldToggle:rect('.field-toggle'), focusableCount:links.length, focusables:links, overflow};
                }""")
                evidence["viewports"].append({"name": name, "width": width, "height": height, "state": state, "screenshot": shot.name, "observation": observation})
                context.close()
        browser.close()

    evidence["summary"] = {"captures": len(evidence["viewports"]), "screenshots": len(evidence["viewports"]), "console_errors": len(evidence["console_errors"]), "network_failures": len(evidence["network_failures"]), "clipped_entries": sum(1 for item in evidence["viewports"] for x in item["observation"]["overflow"] if x["clipped"])}
    (args.out / "pumkit-before-evidence.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
