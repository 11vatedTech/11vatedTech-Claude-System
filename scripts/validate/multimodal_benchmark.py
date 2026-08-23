#!/usr/bin/env python3
"""Real multimodal 9Router benchmark — actual image bytes, real model calls.

Sends HELIOGRAPH screenshots + preserved evidence to vision-confirmed models
through the 9Router gateway. Records: groundedness, defect detection,
pairwise comparison (A/B + B/A), professional critique quality.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
BASE = "http://127.0.0.1:20128"

MODELS = ["11", "claude-11", "ag/gemini-2.5-flash"]

EVIDENCE_DIR = ROOT / "artifacts" / "frontend" / "transfer-lab-001"
SMOKE_DIR = ROOT / "artifacts" / "frontend"


def load_image(path: Path) -> dict:
    """Return base64-encoded image with media type."""
    data = path.read_bytes()
    media = "image/png"
    if path.suffix.lower() == ".webp":
        media = "image/webp"
    return {
        "base64": base64.b64encode(data).decode("utf-8"),
        "media_type": media,
        "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data),
    }


def call_vision(model: str, prompt: str, images: list[dict], max_tokens: int = 300, timeout_s: int = 60) -> dict:
    """Send images + prompt to a model through 9Router."""
    content = [{"type": "text", "text": prompt}]
    for img in images:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{img['media_type']};base64,{img['base64']}",
                "detail": "high",
            },
        })

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "stream": False,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/v1/chat/completions",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer sk_9router"},
        method="POST",
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            resp = json.loads(r.read().decode("utf-8", "replace"))
        latency_ms = int((time.perf_counter() - start) * 1000)
        content_text = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        return {
            "ok": True,
            "http": r.status,
            "latency_ms": latency_ms,
            "response": content_text,
            "response_chars": len(content_text),
            "model": model,
        }
    except urllib.error.HTTPError as e:
        body = e.read(500).decode("utf-8", "replace")
        return {"ok": False, "http": e.code, "error": body[:300], "model": model}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}", "model": model}


# ── Image Loading ────────────────────────────────────────────────────────


def load_evidence() -> dict:
    """Load all relevant screenshots for benchmarking."""
    images = {}

    # HELIOGRAPH screenshots
    for stem, desc in [
        ("desktop_default", "Heliograph desktop — default list view"),
        ("mobile_default", "Heliograph mobile — default view"),
        ("desktop_selected-detail", "Heliograph desktop — detail panel open"),
        ("desktop_confirmed", "Heliograph desktop — observation confirmed"),
        ("mobile_selected-detail", "Heliograph mobile — detail panel open"),
    ]:
        p = EVIDENCE_DIR / f"{stem}.png"
        if p.exists():
            images[desc] = load_image(p)

    # Repaired versions (from repaired-final capture)
    for stem, desc in [
        ("repaired-final_desktop_default", "Heliograph repaired — desktop default"),
        ("repaired-final_mobile_default", "Heliograph repaired — mobile default"),
        ("repaired-final_desktop_focus", "Heliograph repaired — focus state"),
    ]:
        p = EVIDENCE_DIR / f"{stem}.png"
        if p.exists():
            images[desc] = load_image(p)
        else:
            # Try alternate naming
            alt = EVIDENCE_DIR / f"{stem.replace('repaired-final_', 'repaired_')}.png"
            if alt.exists():
                images[desc] = load_image(alt)

    # Conservation queue
    transfer_p = EVIDENCE_DIR / "transfer-evidence_desktop_default.png"
    if transfer_p.exists():
        images["Conservation queue — transfer component"] = load_image(transfer_p)

    # Smoke page (generic baseline)
    smoke_p = SMOKE_DIR / "runtime-evidence" / "desktop_default.png"
    if smoke_p.exists():
        images["Generic frontend smoke page"] = load_image(smoke_p)

    return images


# ── Task Definitions ─────────────────────────────────────────────────────


def tasks() -> list[dict]:
    """Return benchmark tasks. Each task has a prompt, image keys, and ground truth annotations."""
    return [
        # ── OBJECTIVE / GROUNDING ──
        {
            "id": "grounding-01",
            "type": "objective",
            "role": "frontend_visual_critic",
            "images": ["Heliograph desktop — default list view"],
            "prompt": "Is this a mobile or desktop interface? Answer with one word.",
            "ground_truth": "desktop",
            "check": "answer_contains_expected",
        },
        {
            "id": "grounding-02",
            "type": "objective",
            "role": "frontend_visual_critic",
            "images": ["Heliograph mobile — default view"],
            "prompt": "Is this a mobile or desktop interface? Answer with one word.",
            "ground_truth": "mobile",
            "check": "answer_contains_expected",
        },
        {
            "id": "grounding-03",
            "type": "objective",
            "role": "frontend_visual_critic",
            "images": ["Heliograph desktop — default list view"],
            "prompt": "How many observation windows (rows of data) are visible in this interface? Answer with just the number.",
            "ground_truth": "6",
            "check": "answer_contains_expected",
        },
        # ── DEFECT DETECTION ──
        {
            "id": "defect-01",
            "type": "professional",
            "role": "frontend_visual_critic",
            "images": ["Heliograph mobile — default view"],
            "prompt": "Review this mobile interface. What professional design or usability problems do you see? List each problem with: what is wrong, which design discipline owns it, and a specific repair suggestion. Be concrete.",
            "known_defects": ["hidden target column", "requires tap to identify observation"],
            "check": "defect_mentioned",
        },
        {
            "id": "defect-02",
            "type": "professional",
            "role": "frontend_visual_critic",
            "images": ["Heliograph desktop — default list view"],
            "prompt": "Review this desktop interface for visual hierarchy, typography, and color. Identify any issues with: contrast, information priority, column layout, type choices, or visual weight distribution. Be specific about what is wrong and which design discipline it belongs to.",
            "known_defects": ["color contrast", "visual hierarchy", "priority encoding"],
            "check": "defect_mentioned",
        },
        # ── PAIRWISE COMPARISON (A/B) ──
        {
            "id": "pairwise-01-AB",
            "type": "pairwise",
            "role": "art_director",
            "images_a": ["Heliograph desktop — default list view"],
            "images_b": ["Generic frontend smoke page"],
            "prompt": "Compare Interface A (first image) and Interface B (second image). Which has a stronger, more deliberate visual identity? Explain specifically what makes one stronger than the other. Name concrete characteristics: palette, typography, spatial language, surface treatment, information design choices.",
            "expected_preference": "A",
            "criteria": "visual_identity",
        },
        {
            "id": "pairwise-01-BA",
            "type": "pairwise",
            "role": "art_director",
            "images_a": ["Generic frontend smoke page"],
            "images_b": ["Heliograph desktop — default list view"],
            "prompt": "Compare Interface A (first image) and Interface B (second image). Which has a stronger, more deliberate visual identity? Explain specifically what makes one stronger than the other. Name concrete characteristics: palette, typography, spatial language, surface treatment, information design choices.",
            "expected_preference": "B",
            "criteria": "visual_identity",
        },
        # ── PAIRWISE BEFORE/AFTER ──
        {
            "id": "pairwise-ba-01-AB",
            "type": "pairwise",
            "role": "ux_visual_critic",
            "images_a": ["Heliograph mobile — default view"],
            "images_b": ["Heliograph repaired — mobile default"],
            "prompt": "Compare these two mobile interfaces of the same application — Interface A (before) and Interface B (after). Which provides better information accessibility for the user? Focus on: can the user identify observation targets without interaction, can they compare items, is critical information visible on the default view? Explain which specific design change made the difference.",
            "expected_preference": "B",
            "criteria": "information_accessibility",
        },
        {
            "id": "pairwise-ba-01-BA",
            "type": "pairwise",
            "role": "ux_visual_critic",
            "images_a": ["Heliograph repaired — mobile default"],
            "images_b": ["Heliograph mobile — default view"],
            "prompt": "Compare these two mobile interfaces of the same application — Interface A (after repair) and Interface B (before repair). Which provides better information accessibility for the user? Focus on: can the user identify observation targets without interaction, can they compare items, is critical information visible on the default view? Explain which specific design change made the difference.",
            "expected_preference": "A",
            "criteria": "information_accessibility",
        },
        # ── PROFESSIONAL CRITIQUE ──
        {
            "id": "critique-01",
            "type": "professional",
            "role": "art_director",
            "images": ["Heliograph desktop — default list view"],
            "prompt": "Evaluate this interface's art direction. Describe: the visual thesis (what aesthetic is it pursuing?), the color strategy, the typographic voice, the spatial language. Then critique: does it deliver on its thesis? Is it distinct from generic dark-mode dashboards? What strengthens or weakens its identity? Be specific about visual characteristics, not vague impressions.",
            "check": "specific_critique",
        },
        # ── TRANSFER DETECTION ──
        {
            "id": "transfer-01",
            "type": "professional",
            "role": "frontend_visual_critic",
            "images": ["Heliograph repaired — desktop default", "Conservation queue — transfer component"],
            "prompt": "These two interfaces — a solar observation planner and a museum conservation queue — were designed by the same team. Identify which visual-design principles were deliberately transferred between them, and which were deliberately changed. What is similar (at the level of structural principles, not visual style)? What is different (at the level of visual language, palette, typography)?",
            "check": "transfer_detected",
        },
    ]


# ── Evaluation ───────────────────────────────────────────────────────────


def evaluate(task: dict, response: str) -> dict:
    """Score a task response against ground truth."""
    check = task.get("check", "")
    resp_lower = response.lower()
    ev = {"task_id": task["id"], "evaluation": {}}

    if check == "answer_contains_expected":
        expected = task["ground_truth"].lower()
        ev["evaluation"]["correct"] = expected in resp_lower
        ev["evaluation"]["grounded"] = expected in resp_lower

    elif check == "defect_mentioned":
        defects = task.get("known_defects", [])
        hits = sum(1 for d in defects if d.lower() in resp_lower)
        ev["evaluation"]["defects_found"] = hits
        ev["evaluation"]["defects_expected"] = len(defects)
        ev["evaluation"]["recall"] = hits / len(defects) if defects else 0
        # Check for overclaims (vague statements without specifics)
        vague_markers = ["needs polish", "make it pop", "looks basic", "make it premium", "looks better", "more modern"]
        ev["evaluation"]["vague_critique"] = any(m in resp_lower for m in vague_markers)

    elif check == "specific_critique":
        # Was the critique specific (named concrete visual characteristics)?
        specific_markers = ["palette", "color", "type", "font", "typography", "contrast", "amber", "dark", "monospace", "serif", "gauge", "column", "grid", "spacing", "hierarchy", "density", "alignment"]
        specificity = sum(1 for m in specific_markers if m in resp_lower)
        vague_markers = ["looks good", "looks nice", "needs polish", "make it pop", "could be better"]
        vagueness = sum(1 for m in vague_markers if m in resp_lower)
        ev["evaluation"]["specificity_score"] = min(specificity, 10)
        ev["evaluation"]["vague_count"] = vagueness
        ev["evaluation"]["quality"] = "SPECIFIC" if specificity >= 3 and vagueness == 0 else ("MIXED" if specificity >= 2 else "VAGUE")

    elif check == "transfer_detected":
        transfer_markers = ["shape", "priority", "color", "non-color", "contrast", "responsive", "layout", "mobile", "inline", "confirmation", "badge", "typography", "serif", "monospace", "palette", "warm", "dark", "light"]
        hits = sum(1 for m in transfer_markers if m in resp_lower)
        ev["evaluation"]["transfer_specificity"] = min(hits, 10)

    return ev


# ── Main ─────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "frontend" / "transfer-lab-001" / "multimodal-benchmark-results.json")
    parser.add_argument("--models", nargs="*", default=MODELS)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    images = load_evidence()
    print(f"Loaded {len(images)} images for benchmark")
    for desc, img in images.items():
        print(f"  {desc}: {img['bytes']} bytes, sha256={img['sha256'][:12]}")

    all_tasks = tasks()
    if args.limit:
        all_tasks = all_tasks[: args.limit]

    results = {
        "schema_version": 2,
        "kind": "multimodal-benchmark-execution",
        "date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models_tested": args.models,
        "task_count": len(all_tasks),
        "image_hashes": {desc: img["sha256"][:12] for desc, img in images.items()},
        "results": [],
        "pairwise_analysis": [],
    }

    # ── Run all tasks against all models ──
    for task in all_tasks:
        for model in args.models:
            # Resolve images
            task_images = []
            for key in task.get("images", []):
                if key in images:
                    task_images.append(images[key])
                else:
                    print(f"  WARNING: image '{key}' not found")

            # Handle pairwise tasks
            if task["type"] == "pairwise":
                imgs_a = [images[k] for k in task.get("images_a", []) if k in images]
                imgs_b = [images[k] for k in task.get("images_b", []) if k in images]
                if not imgs_a or not imgs_b:
                    print(f"  SKIP {task['id']}: missing pairwise images")
                    continue
                prompt_with_label = f"[Interface A — first image attached]\n[Interface B — second image attached]\n\n{task['prompt']}"
                task_images = imgs_a + imgs_b
            else:
                prompt_with_label = task["prompt"]

            if not task_images:
                print(f"  SKIP {task['id']}: no images resolved")
                continue

            print(f"  {task['id']} [{model}] ({len(task_images)} images)...", end=" ", flush=True)
            t0 = time.perf_counter()
            result = call_vision(model, prompt_with_label, task_images, max_tokens=300, timeout_s=90)
            elapsed = time.perf_counter() - t0

            if result["ok"]:
                ev = evaluate(task, result["response"])
                record = {
                    "task_id": task["id"],
                    "model": model,
                    "ok": True,
                    "latency_ms": result["latency_ms"],
                    "response_chars": result["response_chars"],
                    "response": result["response"][:800],
                    "evaluation": ev["evaluation"],
                    "task_type": task["type"],
                    "role": task.get("role", ""),
                }
                print(f"OK {result['latency_ms']}ms")
                # Quick grounding check
                if ev["evaluation"].get("correct") is False:
                    print(f"    GROUNDING FAIL: expected '{task.get('ground_truth', '')}' not in response")
            else:
                record = {
                    "task_id": task["id"],
                    "model": model,
                    "ok": False,
                    "error": result.get("error", result.get("http", "unknown")),
                    "task_type": task["type"],
                }
                print(f"FAIL {result.get('http', result.get('error', ''))}")

            results["results"].append(record)

    # ── Pairwise Analysis ──
    pairwise_pairs = {}
    for r in results["results"]:
        tid = r["task_id"]
        if "pairwise" in tid and r.get("ok"):
            base_id = tid.rsplit("-", 2)[0] if "-AB" in tid or "-BA" in tid else tid
            if base_id not in pairwise_pairs:
                pairwise_pairs[base_id] = {}
            order = "AB" if tid.endswith("-AB") else "BA"
            if r["model"] not in pairwise_pairs[base_id]:
                pairwise_pairs[base_id][r["model"]] = {}
            ev = r.get("evaluation", {})
            pairwise_pairs[base_id][r["model"]][order] = {
                "response": r.get("response", "")[:400],
                "preference": None,
            }

    # Detect position stability
    for base_id, models in pairwise_pairs.items():
        for model, orders in models.items():
            if "AB" in orders and "BA" in orders:
                # Simple heuristic: check if same interface is preferred in both orders
                ab_pref = _extract_preference(orders["AB"]["response"])
                ba_pref = _extract_preference(orders["BA"]["response"])
                orders["AB"]["preference"] = ab_pref
                orders["BA"]["preference"] = ba_pref
                stable = ab_pref == ba_pref if ab_pref and ba_pref else None
                results["pairwise_analysis"].append({
                    "task_base": base_id,
                    "model": model,
                    "AB_preference": ab_pref,
                    "BA_preference": ba_pref,
                    "position_stable": stable,
                    "note": "UNSTABLE" if stable is False else ("STABLE" if stable else "INCONCLUSIVE"),
                })

    # ── Save ──
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nResults: {args.out}")
    print(f"Tasks run: {len(results['results'])}")
    ok_count = sum(1 for r in results["results"] if r.get("ok"))
    print(f"Successful: {ok_count}")
    print(f"Pairwise analyses: {len(results['pairwise_analysis'])}")

    return 0 if ok_count > 0 else 1


def _extract_preference(response: str) -> str | None:
    """Heuristic: did the model prefer A or B?"""
    r = response.lower()
    # Look for clear preference signals
    if "interface a" in r and any(m in r for m in ["stronger", "better", "prefer", "more deliberate", "clearer", "superior"]):
        return "A"
    if "interface b" in r and any(m in r for m in ["stronger", "better", "prefer", "more deliberate", "clearer", "superior"]):
        return "B"
    if "first interface" in r and any(m in r for m in ["stronger", "better", "prefer"]):
        return "A"
    if "second interface" in r and any(m in r for m in ["stronger", "better", "prefer"]):
        return "B"
    return None


if __name__ == "__main__":
    raise SystemExit(main())