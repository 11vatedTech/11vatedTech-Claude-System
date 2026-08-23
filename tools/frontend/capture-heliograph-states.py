"""Capture HELIOGRAPH interaction states: selected row, detail open, confirmed."""
import json, sys, time, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "frontend" / "py-deps"))

from playwright.sync_api import sync_playwright

PAGE = "file:///" + str((ROOT / "tools/fixtures/frontend-transfer/heliograph/index.html").resolve().as_posix())
OUT = ROOT / "artifacts/frontend/transfer-lab-001/interaction-evidence.json"
SCREENSHOT_DIR = ROOT / "artifacts/frontend/transfer-lab-001"

VIEWPORTS = [
    ("desktop", 1440, 900),
    ("tablet", 768, 1024),
    ("mobile", 375, 812),
]

results = {"states": [], "console_errors": [], "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

with sync_playwright() as pw:
    npm_chromium = Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright" / "chromium-1234" / "chrome-win64" / "chrome.exe"
    launch_args = {"headless": True}
    if npm_chromium.exists():
        launch_args["executable_path"] = str(npm_chromium)
    else:
        launch_args["channel"] = "chrome"
    browser = pw.chromium.launch(**launch_args)
    
    for vp_name, width, height in VIEWPORTS:
        ctx = browser.new_context(viewport={"width": width, "height": height})
        page = ctx.new_page()
        
        page.on("console", lambda msg: results["console_errors"].append({"type": msg.type, "text": msg.text}) if msg.type == "error" else None)
        
        page.goto(PAGE, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(500)
        
        # State 1: default (already captured by harness, skip)
        
        # State 2: hover first row
        page.hover(".obs-row:first-of-type .obs-main", timeout=5000)
        page.wait_for_timeout(300)
        ss = SCREENSHOT_DIR / f"{vp_name}_hover-row.png"
        page.screenshot(path=str(ss), full_page=True)
        results["states"].append({"viewport": vp_name, "state": "hover-row", "screenshot": str(ss.name)})
        
        # State 3: select first row (detail open)
        page.click(".obs-row:first-of-type .obs-main", timeout=5000)
        page.wait_for_timeout(500)
        ss = SCREENSHOT_DIR / f"{vp_name}_selected-detail.png"
        page.screenshot(path=str(ss), full_page=True)
        results["states"].append({"viewport": vp_name, "state": "selected-detail-open", "screenshot": str(ss.name)})
        
        # State 4: confirm observation
        page.click(".btn-select", timeout=5000)
        page.wait_for_timeout(500)
        ss = SCREENSHOT_DIR / f"{vp_name}_confirmed.png"
        page.screenshot(path=str(ss), full_page=True)
        results["states"].append({"viewport": vp_name, "state": "confirmed", "screenshot": str(ss.name)})
        
        # State 5: keyboard focus on first row
        page2 = ctx.new_page()
        page2.goto(PAGE, wait_until="networkidle", timeout=30000)
        page2.keyboard.press("Tab")
        page2.wait_for_timeout(300)
        ss = SCREENSHOT_DIR / f"{vp_name}_keyboard-focus.png"
        page2.screenshot(path=str(ss), full_page=True)
        results["states"].append({"viewport": vp_name, "state": "keyboard-focus", "screenshot": str(ss.name)})
        page2.close()
        
        ctx.close()
    
    browser.close()

json.dump(results, sys.stdout, indent=2)
OUT.write_text(json.dumps(results, indent=2))
print(f"\nSaved: {OUT}")