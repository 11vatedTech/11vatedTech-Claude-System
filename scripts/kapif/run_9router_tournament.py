"""
KAPIF M002.1 — 9Router Multimodal Tournament.

Probes bounded shortlist of 9Router vision routes with real images.
Measures: availability, latency, response quality, SSE streaming.
"""

import base64
import json
import time
from pathlib import Path

import requests

BASE = "http://127.0.0.1:20128"
ART = Path("artifacts")

# Shortlisted routes for tournament
SHORTLIST = [
    "kr/claude-haiku-4.5",
    "ag/gemini-3.7-flash-medium",
    "kr/claude-sonnet-5",
    "ag/gemini-3.1-pro-low",
]

# Test images (one composition, one material)
TEST_IMAGES = [
    ("composition", "composition-lab/comp-c-original.png"),
    ("material", "material-lab/renders/diag_ceramic_too_metallic.png"),
]

PROBE_PROMPT = (
    "You are a professional visual critic. Examine this image and respond with ONLY a JSON object:\n"
    '{"orientation":"PORTRAIT|LANDSCAPE|SQUARE","ui_present":"YES|NO","dominant_value":"LOW_KEY|MID_KEY|HIGH_KEY",'
    '"cause_class":"one word describing the main visual issue or NONE","confidence":"HIGH|MEDIUM|LOW"}\n'
    "Output ONLY the JSON."
)


def infer_9router(route, img_path, prompt):
    """Run inference via 9Router with SSE streaming support."""
    img_b64 = base64.b64encode(Path(img_path).read_bytes()).decode()
    payload = {
        "model": route,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                    },
                ],
            }
        ],
        "max_tokens": 512,
        "temperature": 0.0,
    }
    t0 = time.time()
    try:
        r = requests.post(
            f"{BASE}/v1/chat/completions",
            json=payload,
            stream=True,
            timeout=60,
        )
        if r.status_code != 200:
            latency = time.time() - t0
            return {"status": f"HTTP_{r.status_code}", "latency": latency, "raw": r.text[:300]}

        # Parse SSE streaming
        content_parts = []
        for line in r.iter_lines():
            if line:
                line = line.decode()
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            content_parts.append(delta["content"])
                    except Exception:
                        pass

        latency = time.time() - t0
        content = "".join(content_parts)
        return {"status": "OK", "latency": latency, "raw": content}
    except Exception as e:
        latency = time.time() - t0
        return {"status": f"ERROR_{type(e).__name__}", "latency": latency, "raw": str(e)[:200]}


def parse_json_response(raw):
    """Extract JSON from model response."""
    s = (raw or "").strip()
    if "```" in s:
        parts = s.split("```")
        s = parts[1] if len(parts) > 1 else s
        s = s.strip("json\n ")
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b > a:
        try:
            return json.loads(s[a : b + 1])
        except Exception:
            pass
    return None


def main():
    results = {}
    for route in SHORTLIST:
        print(f"\n=== {route} ===")
        route_results = []
        for img_name, img_path in TEST_IMAGES:
            full_path = ART / img_path
            if not full_path.exists():
                print(f"  {img_name}: SKIP (missing)")
                continue
            r = infer_9router(route, str(full_path), PROBE_PROMPT)
            parsed = parse_json_response(r["raw"])
            result = {
                "image": img_name,
                "status": r["status"],
                "latency": r["latency"],
                "parsed": parsed,
                "raw_preview": (r["raw"] or "")[:200],
            }
            route_results.append(result)
            status_char = "OK" if parsed else "PARSE_FAIL"
            print(f"  {img_name}: {status_char} ({r['latency']:.1f}s)")
            if parsed:
                print(f"    -> {json.dumps(parsed)[:120]}")

        results[route] = route_results

    # Summary
    print("\n=== TOURNAMENT SUMMARY ===")
    summary = []
    for route, rs in results.items():
        parsed_count = sum(1 for r in rs if r.get("parsed"))
        avg_latency = sum(r["latency"] for r in rs) / len(rs) if rs else 0
        summary.append({
            "route": route,
            "parsed": f"{parsed_count}/{len(rs)}",
            "avg_latency": f"{avg_latency:.1f}s",
        })
        print(f"  {route}: {parsed_count}/{len(rs)} parsed, avg {avg_latency:.1f}s")

    out_file = ART / "kapif" / "m002.1" / "9router-tournament.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({"results": results, "summary": summary}, indent=1), encoding="utf-8")
    print(f"\nSaved: {out_file}")


if __name__ == "__main__":
    main()
