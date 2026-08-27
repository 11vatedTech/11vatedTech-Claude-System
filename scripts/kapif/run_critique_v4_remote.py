"""
KAPIF M002.1 -- Run professional visual critique V4 controlled pairs through a
remote 9Router frontier vision route, scoring with the IDENTICAL scoring logic
used for local models (visual_critique_v4.score_pair).

Usage:
  python scripts/kapif/run_critique_v4_remote.py --model kr/claude-haiku-4.5
  python scripts/kapif/run_critique_v4_remote.py --model cu/claude-sonnet-5-medium --limit 6
"""
import argparse
import base64
import hashlib
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from visual_critique_v4 import PAIRS, ART, parse_critique, score_pair  # noqa: E402

ROUTER = "http://127.0.0.1:20128"
OUT_DIR = Path("artifacts/kapif/m002.1/runs-critique-v4")

CRITIQUE_TEMPLATE = (
    "You are a professional visual critic. Two images are provided: IMAGE A and IMAGE B.\n"
    "Compare them and answer ONLY with a JSON object:\n"
    '{"worse":"A|B|EQUAL","observation":"specific visible differences",'
    '"cause":"most likely design cause","impact":"effect on hierarchy/legibility/orientation/identity/emotion/interaction/quality",'
    '"repair":"specific change that addresses the cause","confidence":"HIGH|MEDIUM|LOW",'
    '"speculation":"anything not directly visible"}\n'
    "Rules: observation must name only things actually visible. Do not invent details. Output ONLY the JSON."
)


def call_router(model: str, path_a: Path, path_b: Path) -> dict:
    parts = [{"type": "text", "text": CRITIQUE_TEMPLATE}]
    for p in (path_a, path_b):
        b64 = base64.b64encode(p.read_bytes()).decode()
        parts.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}})
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": parts}],
        "max_tokens": 1500,
        "stream": False,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(ROUTER + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            out = r.read().decode("utf-8", "replace")
        code = 200
    except urllib.error.HTTPError as e:
        code = e.code
        out = e.read().decode("utf-8", "replace")
    except Exception as e:
        code = "ERR"
        out = str(e)
    lat = round(time.time() - t0, 1)
    content = ""
    if code == 200:
        try:
            content = json.loads(out)["choices"][0]["message"]["content"]
        except Exception:
            content = out
    return {"code": code, "raw": content, "latency_s": lat}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="kr/claude-haiku-4.5")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only-ids", default="")
    args = ap.parse_args()

    items = PAIRS
    if args.limit:
        items = items[: args.limit]
    if args.only_ids:
        want = {x.strip() for x in args.only_ids.split(",")}
        items = [p for p in items if p[0] in want]

    template_hash = hashlib.sha256(CRITIQUE_TEMPLATE.encode()).hexdigest()
    results = {
        "model": args.model,
        "template_hash": template_hash,
        "executed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "pairs": {},
    }

    for pair in items:
        pid, discipline, _, path_a, _, path_b, known, _ = pair
        full_a, full_b = ART / path_a, ART / path_b
        print(f"--- {pid} [{discipline}] {full_a.name} vs {full_b.name}", flush=True)
        resp = call_router(args.model, full_a, full_b)
        rec = {
            "pair_id": pid,
            "discipline": discipline,
            "known_intervention": known,
            "status": "OK" if resp["code"] == 200 and resp["raw"].strip() else f"HTTP_{resp['code']}",
            "code": resp["code"],
            "latency_s": resp["latency_s"],
            "raw": resp["raw"][:4000],
        }
        if resp["code"] == 200 and resp["raw"].strip():
            rec["parsed"] = parse_critique(resp["raw"])
            if rec["parsed"]:
                rec["score"] = score_pair(pair, rec["parsed"])
        results["pairs"][pid] = rec
        if rec.get("score"):
            s = rec["score"]
            print(f"   worse={s['worse']} cause_hit={s['cause_keyword_hit']} repair_hit={s['repair_keyword_hit']} conf={s['confidence']}")
        else:
            print(f"   no parse (code={resp['code']})")

    safe = args.model.replace("/", "_").replace(":", "-")
    out = OUT_DIR / f"critique-{safe}.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
