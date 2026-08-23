"""Material Lab diagnostic — generate renders, critique through vision model."""
import json, base64, urllib.request, time
from pathlib import Path

BASE = "http://127.0.0.1:20128"
OUT = Path("artifacts/material-lab")
OUT.mkdir(parents=True, exist_ok=True)

# Generate 3 material renders
renders = []
for label, prompt in [
    ("aged_steel", "A single sphere made of aged steel with visible brushed texture, subtle scratches, light oxidation. Studio lighting, neutral gray background. Photorealistic CG material study. 512x512."),
    ("ceramic", "A single sphere made of white glazed ceramic, smooth glossy surface, subtle warm subsurface glow at edges. Studio lighting, neutral gray background. Photorealistic CG material study. 512x512."),
]:
    payload = json.dumps({"model": "ag/gemini-3.1-flash-image", "prompt": prompt, "n": 1, "size": "512x512", "response_format": "b64_json"}).encode()
    try:
        req = urllib.request.Request(f"{BASE}/v1/images/generations", data=payload, headers={"Content-Type": "application/json", "Authorization": "Bearer sk_9router"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read().decode())
        b64 = resp["data"][0].get("b64_json", "")
        if b64:
            p = OUT / f"{label}.png"
            p.write_bytes(base64.b64decode(b64))
            renders.append({"label": label, "path": str(p), "bytes": p.stat().st_size})
            print(f"{label}: {p.stat().st_size} bytes OK")
        time.sleep(2)
    except Exception as e:
        print(f"{label}: FAILED {type(e).__name__}")

# Critique through vision model
if renders:
    content = [{"type": "text", "text": "You are a material/lookdev artist. Image 1 is described as aged steel (should have: warm-gray colored specular, no diffuse, roughness ~0.35, visible edge Fresnel, brushed texture). Image 2 is described as white glazed ceramic (should have: white/colorless specular, tight small highlights, subtle warm subsurface at shadow edges, roughness ~0.08). For each image, evaluate: does it read as the intended material? What specific visual cue confirms or contradicts? Be specific about specular color (white vs colored), highlight tightness, edge behavior, subsurface, roughness."}]
    for r in renders:
        b64 = base64.b64encode(Path(r["path"]).read_bytes()).decode()
        content.append({"type": "text", "text": f"[Image: {r['label']}]"})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}})
    
    payload = {"model": "ag/gemini-2.5-flash", "messages": [{"role": "user", "content": content}], "max_tokens": 500, "stream": False}
    req = urllib.request.Request(f"{BASE}/v1/chat/completions", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "Authorization": "Bearer sk_9router"}, method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    critique = r["choices"][0]["message"]["content"]
    print(f"\nCRITIQUE:\n{critique[:600]}")
    (OUT / "material-critique.json").write_text(json.dumps({"critique": critique, "renders": renders}, indent=2))
    print(f"\nSaved: {OUT / 'material-critique.json'}")