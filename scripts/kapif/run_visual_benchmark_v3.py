#!/usr/bin/env python3
"""Visual Grounding V3 Benchmark Runner.

Runs vision models against the balanced V3 dataset using:
- Real image bytes (not placeholders)
- Structured JSON prompt
- Exact-match enum scoring
- Per-property accuracy
- Trivial baselines
- Provider status separation from quality
"""

import json
import time
import base64
import re
import requests
from pathlib import Path

DATASET_PATH = Path("artifacts/kapif/m002.1/visual-v3-dataset/dataset-manifest.json")
RESULTS_DIR = Path("artifacts/kapif/m002.1")
OLLAMA_URL = "http://localhost:11434/api/generate"

SCORING_PROPERTIES = [
    "ui_present", "visible_text", "render_type",
    "dominant_value", "major_clipping", "major_overlap",
    "orientation", "focal_region",
]

VALID_ENUMS = {
    "ui_present": ["YES", "NO"],
    "visible_text": ["YES", "NO"],
    "render_type": ["2D", "3D", "MIXED", "NONE"],
    "dominant_value": ["LOW_KEY", "MID_KEY", "HIGH_KEY", "MIXED"],
    "major_clipping": ["YES", "NO"],
    "major_overlap": ["YES", "NO"],
    "orientation": ["LANDSCAPE", "PORTRAIT", "SQUARE"],
    "focal_region": [
        "TOP_LEFT", "TOP_CENTER", "TOP_RIGHT",
        "CENTER_LEFT", "CENTER", "CENTER_RIGHT",
        "BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT",
        "MULTIPLE", "NONE",
    ],
}

PROMPT_TEMPLATE = """Analyze this image. Return ONLY a JSON object with these exact keys and enum values (no other text):

{
  "ui_present": "YES" or "NO",
  "visible_text": "YES" or "NO",
  "render_type": "2D" or "3D" or "MIXED" or "NONE",
  "dominant_value": "LOW_KEY" or "MID_KEY" or "HIGH_KEY" or "MIXED",
  "major_clipping": "YES" or "NO",
  "major_overlap": "YES" or "NO",
  "orientation": "LANDSCAPE" or "PORTRAIT" or "SQUARE",
  "focal_region": one of "TOP_LEFT", "TOP_CENTER", "TOP_RIGHT", "CENTER_LEFT", "CENTER", "CENTER_RIGHT", "BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT", "MULTIPLE", "NONE"
}

Return ONLY the JSON object. No explanation."""


def normalize_enum(prop, raw_value):
    """Normalize a raw string to the expected enum value."""
    if not raw_value:
        return "UNCERTAIN"
    v = raw_value.strip().upper().replace(" ", "_").replace("-", "_")
    # Common aliases
    aliases = {
        "DARK": "LOW_KEY", "LIGHT": "HIGH_KEY", "MEDIUM": "MID_KEY",
        "PORTRAIT_MODE": "PORTRAIT", "LANDSCAPE_MODE": "LANDSCAPE",
        "SQUARE_IMAGE": "SQUARE",
        "YES_": "YES", "NO_": "NO",
        "TRUE": "YES", "FALSE": "NO",
        "NONE_": "NONE",
    }
    v = aliases.get(v, v)
    valid = VALID_ENUMS.get(prop, [])
    if v in valid:
        return v
    # Check substring containment (fallback)
    for ev in valid:
        if ev in v:
            return ev
    return "INVALID"


def extract_json_from_response(text):
    """Extract JSON from model response, handling markdown code blocks."""
    # Try direct parse
    text = text.strip()
    # Remove markdown code fences
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*$', '', text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to find JSON object in text
    match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def query_ollama(model_name, image_b64, prompt, timeout=120):
    """Query Ollama with an image and prompt."""
    start = time.time()
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": model_name,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
            "options": {"temperature": 0.0},
        }, timeout=timeout)
        elapsed = time.time() - start
        if resp.status_code == 200:
            data = resp.json()
            return {
                "status": "SUCCESS",
                "response": data.get("response", ""),
                "latency_s": round(elapsed, 2),
                "eval_count": data.get("eval_count", 0),
                "eval_duration_ns": data.get("eval_duration", 0),
            }
        else:
            return {
                "status": f"HTTP_{resp.status_code}",
                "response": "",
                "latency_s": round(elapsed, 2),
            }
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "response": "", "latency_s": round(time.time() - start, 2)}
    except Exception as e:
        return {"status": f"ERROR:{type(e).__name__}", "response": "", "latency_s": round(time.time() - start, 2)}


def compute_trivial_baselines(samples):
    """Compute majority-class baselines."""
    baselines = {}
    for prop in SCORING_PROPERTIES:
        counts = {}
        for s in samples:
            v = s["ground_truth"].get(prop, "UNCERTAIN")
            counts[v] = counts.get(v, 0) + 1
        if counts:
            majority = max(counts, key=counts.get)
            baselines[prop] = {
                "majority_class": majority,
                "majority_count": counts[majority],
                "total": sum(counts.values()),
                "accuracy": round(counts[majority] / sum(counts.values()), 4),
            }
    return baselines


def score_predictions(samples, predictions, baselines):
    """Score predictions against ground truth."""
    property_correct = {p: 0 for p in SCORING_PROPERTIES}
    property_total = {p: 0 for p in SCORING_PROPERTIES}
    property_invalid = {p: 0 for p in SCORING_PROPERTIES}
    false_details = 0
    total_scored = 0
    total_samples = 0

    for i, s in enumerate(samples):
        pred = predictions.get(s["sample_id"], {})
        if pred.get("status") != "VALID":
            # Track as provider/error issue, not quality
            continue

        total_samples += 1
        parsed = pred.get("parsed", {})
        gt = s["ground_truth"]

        for prop in SCORING_PROPERTIES:
            if prop not in gt:
                continue
            gt_val = gt[prop]
            pred_val = normalize_enum(prop, parsed.get(prop, ""))
            property_total[prop] += 1

            if pred_val == "INVALID":
                property_invalid[prop] += 1
            elif pred_val == gt_val:
                property_correct[prop] += 1

        total_scored += 1

    # Per-property accuracy (among valid responses)
    property_accuracy = {}
    for prop in SCORING_PROPERTIES:
        t = property_total[prop]
        c = property_correct[prop]
        inv = property_invalid[prop]
        if t > 0:
            property_accuracy[prop] = {
                "correct": c,
                "total": t,
                "invalid": inv,
                "accuracy": round(c / t, 4),
            }

    # Macro accuracy
    valid_accs = [v["accuracy"] for v in property_accuracy.values() if v["total"] > 0]
    macro_accuracy = round(sum(valid_accs) / len(valid_accs), 4) if valid_accs else 0.0

    # Delta over baselines
    deltas = {}
    for prop in SCORING_PROPERTIES:
        if prop in property_accuracy and prop in baselines:
            model_acc = property_accuracy[prop]["accuracy"]
            base_acc = baselines[prop]["accuracy"]
            deltas[prop] = round(model_acc - base_acc, 4)

    return {
        "total_samples": len(samples),
        "scored_samples": total_samples,
        "property_accuracy": property_accuracy,
        "macro_accuracy": macro_accuracy,
        "deltas_over_baseline": deltas,
    }


def run_benchmark(model_name, samples, keep_alive="5m", timeout=120):
    """Run a model against the full V3 dataset."""
    predictions = {}
    latencies = []
    successful = 0
    failed = 0

    for i, s in enumerate(samples):
        img_path = s["source_path"]
        if not Path(img_path).exists():
            predictions[s["sample_id"]] = {"status": "FILE_MISSING"}
            failed += 1
            continue

        with open(img_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        # Warm up on first call (model loading)
        if i == 0:
            t0 = time.time()
            q = query_ollama(model_name, img_b64, "Say OK", timeout=timeout)
            cold_start = time.time() - t0
        else:
            cold_start = 0

        result = query_ollama(model_name, img_b64, PROMPT_TEMPLATE, timeout=timeout)

        if result["status"] == "SUCCESS":
            parsed = extract_json_from_response(result["response"])
            if parsed:
                predictions[s["sample_id"]] = {
                    "status": "VALID",
                    "parsed": parsed,
                    "latency_s": result["latency_s"],
                    "raw_length": len(result["response"]),
                    "eval_count": result.get("eval_count", 0),
                }
                latencies.append(result["latency_s"])
                successful += 1
            else:
                predictions[s["sample_id"]] = {
                    "status": "PARSE_FAILED",
                    "raw": result["response"][:200],
                    "latency_s": result["latency_s"],
                }
                failed += 1
        else:
            predictions[s["sample_id"]] = {
                "status": result["status"],
                "latency_s": result["latency_s"],
            }
            failed += 1

        # Print progress (ASCII only for Windows)
        pct = (i+1) * 100 // len(samples)
        print(f"  [{pct:3d}%] {s['sample_id']}: {predictions[s['sample_id']]['status']}", flush=True)

    # Latency stats
    latencies.sort()
    n = len(latencies)
    latency_stats = {}
    if n > 0:
        latency_stats = {
            "p50": round(latencies[n//2], 2),
            "p95": round(latencies[int(n*0.95)], 2) if n > 1 else latencies[0],
            "min": round(latencies[0], 2),
            "max": round(latencies[-1], 2),
            "n": n,
        }

    return {
        "model": model_name,
        "successful": successful,
        "failed": failed,
        "total": len(samples),
        "latencies": latency_stats,
        "predictions": predictions,
        "cold_start_s": round(cold_start, 2) if cold_start else 0,
    }


def main():
    # Load dataset
    if not DATASET_PATH.exists():
        print(f"ERROR: Dataset not found at {DATASET_PATH}")
        print("Run visual_grounding_v3_dataset.py first.")
        return

    with open(str(DATASET_PATH)) as f:
        dataset = json.load(f)

    samples = dataset["samples"]
    print(f"V3 Dataset: {len(samples)} samples, hash: {dataset['dataset_hash']}")

    # Compute baselines
    baselines = compute_trivial_baselines(samples)
    print("\nTrivial baselines:")
    for prop, b in baselines.items():
        print(f"  {prop}: {b['majority_class']} ({b['accuracy']:.1%})")

    all_results = {}

    for model_name in ["moondream", "qwen3-vl:4b"]:
        print(f"\n{'='*60}")
        print(f"Running: {model_name}")
        print(f"{'='*60}")

        result = run_benchmark(model_name, samples)
        scores = score_predictions(samples, result["predictions"], baselines)
        result["scores"] = scores

        # Print results (ASCII only)
        print(f"\n  Successful: {result['successful']}/{result['total']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Latency p50: {result['latencies'].get('p50', 'N/A')}s")
        print(f"  Latency p95: {result['latencies'].get('p95', 'N/A')}s")
        print(f"  Cold start: {result['cold_start_s']}s")
        print(f"  Macro accuracy: {scores['macro_accuracy']:.1%}")
        print(f"\n  Per-property accuracy:")
        for prop, acc in sorted(scores["property_accuracy"].items()):
            delta = scores["deltas_over_baseline"].get(prop, 0)
            delta_str = f" (delta={delta:+.1%})" if delta != 0 else ""
            print(f"    {prop}: {acc['accuracy']:.1%} ({acc['correct']}/{acc['total']}){delta_str}")

        all_results[model_name] = result

    # Determine overall status
    for model_name, result in all_results.items():
        s = result["scores"]
        if result["successful"] == 0:
            status = "PROVIDER_UNAVAILABLE"
        elif result["successful"] < 5:
            status = "INSUFFICIENT_SAMPLE"
        elif s["macro_accuracy"] > 0:
            status = "PASS"
        else:
            status = "FAIL"

        all_results[model_name]["aggregate_status"] = status
        print(f"\n{model_name} aggregate: {status}")

    # Persist results
    output_path = RESULTS_DIR / "visual-benchmark-v3-results.json"
    with open(str(output_path), "w") as f:
        json.dump({
            "dataset_hash": dataset["dataset_hash"],
            "dataset_version": dataset["version"],
            "total_samples": len(samples),
            "baselines": baselines,
            "results": {
                name: {
                    "model": r["model"],
                    "aggregate_status": r["aggregate_status"],
                    "successful": r["successful"],
                    "failed": r["failed"],
                    "latencies": r["latencies"],
                    "scores": r["scores"],
                    "cold_start_s": r["cold_start_s"],
                }
                for name, r in all_results.items()
            },
        }, f, indent=2)

    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
