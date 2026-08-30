#!/usr/bin/env python3
"""Capture screenshots for all code-native benchmark HTML files."""
from playwright.sync_api import sync_playwright
import os, time

html_files = {
    'golden-j-shader': 'artifacts/visual/atlas/golden-j-shader.html',
    'golden-k-motion': 'artifacts/visual/atlas/golden-k-motion.html',
    'golden-m-typo': 'artifacts/visual/atlas/golden-m-typography.html',
    'golden-n-hybrid': 'artifacts/visual/atlas/golden-n-hybrid.html',
    'golden-o-world': 'artifacts/visual/atlas/golden-o-world.html',
}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 720})
    
    for name, path in html_files.items():
        abs_path = os.path.abspath(path).replace(os.sep, '/')
        page.goto(f'file:///{abs_path}')
        # Wait for shader/hybrid to render
        time.sleep(2.5 if 'shader' in name or 'hybrid' in name else 1.5)
        out = f'artifacts/visual/atlas/{name}.png'
        page.screenshot(path=out, full_page=False)
        sz = os.path.getsize(out) // 1024
        print(f'  {name}: {sz}KB -> {out}')
    
    browser.close()
print('All code-native screenshots captured')
