"""
KAPIF M002.1 -- Visual Grounding Benchmark V4 runner (local Ollama).

Frozen prompt template + enum schema + alias normalization + exact scoring.
Incremental persistence: results saved after EVERY sample so a timeout never
loses completed work. Model execution, scoring, persistence and console
presentation are separated failure boundaries (M002.1 Pass 06).

Usage:
  python scripts/kapif/run_visual_benchmark_v4.py --model moondream [--limit N] [--resume]
  python scripts/kapif/run_visual_benchmark_v4.py --model qwen3-vl:4b [--limit N] [--resume]
"""

import argparse
import base64
import hashlib
import json
import subprocess
import time
from pathlib import Path

import requests

DATASET = Path("artifacts/kapif/m002.1/visual-benchmark-v4-dataset.json")
OUT_DIR = Path("artifacts/kapif/m002.1/runs-v4")
OLLAMA = "http://127.0.0.1:11434"

PROMPT_TEMPLATE = """You are a visual grounding system. Look at the provided image and answer ONLY with a JSON object using EXACTLY these keys and values:
{"orientation":"PORTRAIT|LANDSCAPE|SQUARE","ui_present":"YES|NO|UNCERTAIN","render_type":"3D|2D|MIXED|NONE|UNCERTAIN","visible_text":"YES|NO|UNCERTAIN","dominant_value":"LOW_KEY|MID_KEY|HIGH_KEY|MIXED|UNCERTAIN","focal_region":"TOP_LEFT|TOP_CENTER|TOP_RIGHT|CENTER_LEFT|CENTER|CENTER_RIGHT|BOTTOM_LEFT|BOTTOM_CENTER|BOTTOM_RIGHT|MULTIPLE|NONE|UNCERTAIN"}
Rules:
- orientation: width vs height (PORTRAIT if taller).
- ui_presentation: YES only if a software interface (buttons, inputs, tables, panels) is visible.
- render_type: 3D = computer-generated 3D render; 2D = flat UI/graphic; MIX = UI overlaying 3D content; NONE = no render/interface.
- visible_text: YES if any legible text characters are visible.
- dominant_value: LOW_KEY = predominantly dark/shadows; MID_KEY = balanced; HIGH_KEY = mostly bright; MIXED = very wide contrast.
- focal_region: the 3x3 grid region the eye is drawn to (brightest or most detailed); MULTIPLE if several compete; NONE if none.
If you cannot determine an answer use UNCERTAIN. Do not invent details. Output ONLY the JSON object."""

PROMPT_HASH = hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest()

# Humanity-normalized alias map applied BEFORE exact scoring
ALIASES = {
    "dark": "LOW_KEY", "lowkey": "LOW_KEY", "low key": "LOW_KEY",
    "highkey": "HIGH_KEY", "high key": "HIGH_KEY", "bright": "HIGH_KEY",
    "middle": "MID_KEY", "midkey": "MID_KEY", "mid key": "MID_KEY",
    "mixed": "MIXED", "3d": "3D", "2d": "2D", "ui": "YES", "no ui": "NO",
    "yes": "YES", "no": "NO", "center": "CENTER", "port": "PORTRAIT",
    "landscape": "LANDSCAPE", "square": "SQUARE",
}
VALID = {
    "orientation": {"PORTRAIT", "LANDSCAPE", "SQUARE"},
    "ui_presentation": {"YES", "NO", "UNCERTAIN"},
    "ui_present": {"YES", "NO", "UNCERTAIN"},
    "render_type": {"3D", "2D", "MIX", "NONE", "UNCERTAIN"},
    "visible_text": {"YES", "NO", "UNCERTAIN"},
    "dominant_value": {"LOW_KEY", "MID_KEY", "HIGH_KEY", "MIXED", "UNCERTAIN"},
    "focal_region": {"TOP_LEFT", "TOP_CENTER", "TOP_RIGHT", "CENTER_LEFT", "CENTER", "CENTER_RIGHT",
                     "BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT", "MULTIPLE", "NONE", "UNCERTAIN"},
}
# dataset property names -> prompt keys
PROP_MAP = {
    "orientation": "orientation",
    "ui_present": "ui_presentation",
    "render_type": "render_type",
    "visible_text": "visible_text",
    "dominant_value": "dominant_value",
    "focal_region": "focal_region",
}


def norm(v: str) -> str:
    v = (v or "").strip().strip('"').strip("'").lower()
    if v in ALIASES:
        return ALIASES[v]
    # famously ambiguous strings must NOT become YES/NO
    if v in ("yes or no", "no or yes", "maybe", "both", "y/n"):
        return "INVALID"
    return v.upper()


def parse_json_response(raw: str):
    """Extract first JSON object, tolerant of markdown fences; strict on schema."""
    s = raw.strip()
    if s.startswith("```"):
        s = s.split("```")[1] if "```" in s else s
        s = s.strip("json\n ")
    a, b = s.find("{"), s.rfind("}")
    if a == -1 or b <= a:
        return None
    try:
        obj = json.loads(s[a : b + 1])
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    out = {}
    ok = True
    for prop, key in PROP_MAP.items():
        # accept both the exact prompt key and common model synonyms
        if key not in obj:
            if key == "ui_presentation" and "ui_present" in obj:
                key = "ui_present"
            else:
                ok = False
                break
        nv = norm(str(obj[key]))
        if nv not in VALID[prop]:
            # try alias on the raw value once more via upper
            nv2 = norm(str(obj[key]).replace("-", " ").replace("_", " "))
            if nv2 in VALID[prop]:
                nv = nv2
            else:
                ok = False
                break
        out[prop] = nv
    return out if ok else None


def gpu_telemetry():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        parts = out.split(",")
        return {"dedicated_vram_mb_used": int(parts[0].strip()), "vram_total_mb": int(parts[1].strip()),
                "gpu_util_pct": int(parts[2].strip())}
    except Exception:
        return None


def infer(model: str, img_b64: str, keep_alive="30m"):
    t0 = time.time()
    r = requests.post(
        f"{OLLAMA}/api/generate",
        json={
            "model": model,
            "prompt": PROMPT_TEMPLATE,
            "images": [img_b64],
            "stream": False,
            "keep_alive": keep_alive,
            "options": {"temperature": 0.0, "num_predict": 2048},
        },
        timeout=240,
    )
    dt = time.time() - t0
    if r.status_code != 200:
        return {"status": f"HTTP_{r.status_code}", "latency_s": round(dt, 2), "raw": r.text[:200]}
    body = r.json()
    return {
        "status": "OK",
        "latency_s": round(dt, 2),
        "raw": body.get("response", ""),
        "tokens": body.get("eval_count"),
        "model": body.get("model"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--recover", action="store_true", help="re-run only samples without a parsed result")
    args = ap.parse_args()

    ds = json.loads(DATASET.read_text(encoding="utf-8"))
    samples = ds["samples"]
    if args.limit:
        samples = samples[: args.limit]

    out_file = OUT_DIR / f"results-{args.model.replace(':','_')}.json"
    out = {"model": args.model, "dataset_hash": ds["dataset_hash"], "label_hash": ds["label_hash"],
           "prompt_hash": PROMPT_HASH, "results": {}}
    if out_file.exists():
        prev = json.loads(out_file.read_text(encoding="utf-8"))
        if prev.get("dataset_hash") != ds["dataset_hash"]:
            print("STALE dataset vs results; refusing resume")
            raise SystemExit(1)
        out = prev

    done = set(out["results"].keys())
    if args.recover:
        # target = executed but no parsed result (truncated/invalid output)
        samples = [s for s in samples if s["sample_id"] in done
                   and not out["results"].get(s["sample_id"]).get("parsed")]
        print("recover targets:", len(samples))
    done = set(out["results"].keys())
    telemetry_taken = False
    for i, s in enumerate(samples):
        sid = s["sample_id"]
        if sid in done and not args.recover:
            continue
        img_b64 = base64.b64encode(Path(s["path"]).read_bytes()).decode()
        r = infer(args.model, img_b64)
        rec = {"sample_id": sid, "path": s["path"], **r}
        if r["status"] == "OK":
            parsed = parse_json_response(r["raw"])
            rec["parsed"] = parsed
        if not telemetry_taken and r["status"] == "OK":
            rec["gpu_telemetry"] = gpu_telemetry()
            telemetry_taken = True
        # PERSIST BEFORE any console rendering
        out["results"][sid] = rec
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"[{i+1}/{len(samples)}] {sid} {r['status']} {r.get('latency_s')}s", flush=True)

    print("DONE writing", out_file)
    # summary
    ok = [v for v in out["results"].values() if v.get("status") == "OK"]
    print(f"total={len(out['results'])} ok={len(ok)} "
          f"lat_median={sorted(v['latency_s'] for v in ok)[len(ok)//2] if ok else '-'}s")


if __name__ == "__main__":
    main()