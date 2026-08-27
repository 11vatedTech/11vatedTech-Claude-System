"""
KAPIF M002.1 — Critique V5 with UI-UX specialist model (local Transformers).
"""

import argparse
import base64
import json
import sys
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

sys.path.insert(0, str(Path(__file__).parent))
from visual_critique_v5 import (
    CRITIQUE_TEMPLATE_V5,
    UI_UX_PAIRS,
    counterbalance_pairs,
    parse_critique,
    score_pair,
    compute_aggregate,
    ensure_character_images,
)

ART = Path("artifacts")
OUT_DIR = Path("artifacts/kapif/m002.1/runs-critique-v5")
MODEL_ID = "afx-team/UI-UX"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", action="store_true")
    args = ap.parse_args()

    ensure_character_images()
    out_file = OUT_DIR / "critique-v5-uiux-local.json"

    print("Loading UI-UX model...", flush=True)
    t0 = time.time()
    processor = AutoProcessor.from_pretrained(MODEL_ID)
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID, dtype=torch.bfloat16, device_map="auto"
    )
    print(f"Model loaded in {time.time()-t0:.1f}s, device={model.device}", flush=True)

    balanced = counterbalance_pairs(UI_UX_PAIRS)
    out = {
        "version": "v5",
        "model": MODEL_ID,
        "backend": "transformers_local",
        "device": str(model.device),
        "dtype": str(model.dtype),
        "pairs": {},
        "aggregate": {},
    }
    if out_file.exists():
        out = json.loads(out_file.read_text(encoding="utf-8"))

    scored = []
    for pair in balanced:
        pid = pair["pair_id"]
        if args.resume and pid in out["pairs"]:
            r = out["pairs"][pid]
            if r.get("parsed") and r.get("score"):
                scored.append(r["score"])
                continue

        pa = ART / pair["path_a"]
        pb = ART / pair["path_b"]
        if not pa.exists() or not pb.exists():
            print(f"{pid} SKIP (missing)", flush=True)
            continue

        # Build messages with both images
        img_a = Image.open(pa).convert("RGB")
        img_b = Image.open(pb).convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img_a},
                    {"type": "image", "image": img_b},
                    {"type": "text", "text": CRITIQUE_TEMPLATE_V5},
                ],
            }
        ]

        t0 = time.time()
        try:
            inputs = processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt",
            ).to(model.device)

            with torch.no_grad():
                output = model.generate(
                    **inputs,
                    max_new_tokens=2048,
                    temperature=0.0,
                    do_sample=False,
                )
            response = processor.decode(
                output[0][len(inputs.input_ids[0]) :], skip_special_tokens=True
            )
            latency = time.time() - t0
            r = {"status": "OK", "raw": response, "latency": latency}
        except Exception as e:
            latency = time.time() - t0
            r = {"status": f"ERROR_{type(e).__name__}", "raw": str(e)[:300], "latency": latency}

        rec = {
            "pair_id": pid,
            "base_pair_id": pair["base_pair_id"],
            "discipline": pair["discipline"],
            "presentation": pair["presentation"],
            "ground_truth_worse": pair["ground_truth_worse"],
            "known_intervention": pair["known_intervention"],
            **r,
        }
        if r["status"] == "OK":
            rec["parsed"] = parse_critique(r["raw"])
            if rec["parsed"]:
                rec["score"] = score_pair(pair, rec["parsed"])
                scored.append(rec["score"])

        out["pairs"][pid] = rec
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(out, indent=1), encoding="utf-8")
        ok = "OK" if rec.get("score", {}).get("worse_correct") else "MISS"
        print(f"{pid} [{pair['presentation']}] {ok} ({latency:.1f}s)", flush=True)

    out["aggregate"] = compute_aggregate(scored)
    out_file.write_text(json.dumps(out, indent=1), encoding="utf-8")

    agg = out["aggregate"]
    print(f"\n=== UI-UX CRITIQUE V5 AGGREGATE ===")
    print(f"Pairs: {agg.get('total_pairs', 0)}")
    print(f"Worse accuracy: {agg.get('worse_accuracy', 0):.1%}")
    print(f"Cause exact: {agg.get('cause_exact_accuracy', 0):.1%}")
    print(f"Output: {out_file}")


if __name__ == "__main__":
    main()
