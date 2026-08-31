"""Capture repaired Canvas painting to PNG via Playwright."""
import os
from playwright.sync_api import sync_playwright
from PIL import Image
import numpy as np

HTML = os.path.abspath("artifacts/visual/final-craft/heroes/obsidian_forge_painting.html").replace(os.sep, '/')
OUT = os.path.abspath("artifacts/visual/final-craft/heroes/obsidian_forge_captured.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1600, "height": 1100})
    page.goto(f"file:///{HTML}", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    
    # Extract canvas
    result = page.evaluate("""() => {
        const c = document.getElementById('c');
        if (!c) return {error: 'no canvas'};
        return {dataUrl: c.toDataURL('image/png'), w: c.width, h: c.height, len: c.toDataURL('image/png').length};
    }""")
    print(f"Canvas: {result}")
    
    if 'dataUrl' in result and result['len'] > 1000:
        import base64
        raw = base64.b64decode(result['dataUrl'].split(',')[1])
        with open(OUT, 'wb') as f:
            f.write(raw)
        print(f"Saved {len(raw)} bytes")
        
        img = Image.open(OUT)
        arr = np.array(img)
        print(f"Size: {img.size}, mean: {arr[:,:,:3].mean():.1f}, max: {arr[:,:,:3].max()}")
        
        # Analyze composition
        gray = arr[:,:,:3].mean(axis=2)
        h, w = gray.shape
        # Check focal contrast (furnace area vs periphery)
        furnace = gray[int(h*0.3):int(h*0.5), int(w*0.35):int(w*0.5)].mean()
        periphery = gray.mean()
        print(f"Furnace brightness: {furnace:.1f}, Periphery: {periphery:.1f}, Ratio: {furnace/periphery:.2f}")
        
        # Edge density (higher = more detail)
        edges = np.abs(np.diff(gray, axis=0)).mean() + np.abs(np.diff(gray, axis=1)).mean()
        print(f"Edge density: {edges:.2f}")
        
        # Color richness
        unique = len(np.unique(arr.reshape(-1,3), axis=0))
        print(f"Unique RGB colors: {unique}")
        
        # Quadrant analysis
        q = {
            'TL': gray[:h//2,:w//2].mean(),
            'TR': gray[:h//2,w//2:].mean(),
            'BL': gray[h//2:,:w//2].mean(),
            'BR': gray[h//2:,w//2:].mean(),
        }
        print(f"Quadrants: {q}")
        
        if arr[:,:,:3].mean() < 5:
            print("FAIL: Mostly black")
        else:
            print("PASS: Visible content")
    else:
        print(f"FAIL: {result.get('error', 'no data')}")
    
    browser.close()
