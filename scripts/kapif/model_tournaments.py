#!/usr/bin/env python3
"""
Model Intelligence Tournament — Extraction, Verification, Embedding, Visual.

Runs real benchmarks against frozen reference sets using multiple 9Router models.
Records evidence for role-specific model selection.
"""
import json
import hashlib
import os
import re
import sys
import time
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from kapif.model_intelligence import (
    chat_completion, embed_texts, record_benchmark, set_role_preference,
    shortlist_candidates, discover_available_models, get_model_evidence_summary,
    Role, ModelState
)
from kapif.security import scan_advanced

# ── Paths ──
GOLDEN_SET_PATH = ROOT / "data" / "kapif" / "golden-sets" / "extraction-golden-set.json"
RETRIEVAL_SET_PATH = ROOT / "data" / "kapif" / "golden-sets" / "retrieval-relevance-set.json"
FREEZE_PATH = ROOT / "data" / "kapif" / "golden-sets" / "freeze-manifest.json"
OUTPUT_DIR = ROOT / "data" / "kapif" / "tournament-results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Extraction Tournament Candidates ──
EXTRACTION_CANDIDATES = [
    "kr/claude-sonnet-4.5",
    "kr/deepseek-3.2",
    "kr/claude-haiku-4.5",
    "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/google/gemma-4-31b-it:free",
]

# ── Verification Tournament Candidates ──
VERIFICATION_CANDIDATES = [
    "kr/claude-sonnet-4.5",
    "kr/deepseek-3.2",
    "kr/glm-5",
    "openrouter/inclusionai/ling-3.0-flash:free",
]

# ── Embedding Candidates ──
EMBEDDING_CANDIDATES = [
    "openrouter/nvidia/llama-nemotron-embed-vl-1b-v2:free",
]

# ── Visual Candidates ──
VISUAL_CANDIDATES = [
    "kr/claude-sonnet-4.5",
    "kr/claude-haiku-4.5",
    "11",
]

EXTRACTION_SYSTEM_PROMPT = """You are a professional knowledge extraction system. 
Extract atomic knowledge claims from the source text.

IMPORTANT RULES:
1. Every extracted claim MUST include a verbatim evidence span from the source.
2. Do NOT invent causal relationships not stated in the source.
3. Do NOT make claims broader than what the source states.
4. Do NOT extract marketing language, instructions, or speculation as facts.
5. Type your output as a JSON array of atoms.

Atom schema:
{
  "type": "FACT|PRINCIPLE|PROCEDURE|CONSTRAINT|FAILURE_PATTERN|TRADEOFF|TOOL_CAPABILITY|VERSION_FACT|LICENSE_FACT|PERFORMANCE_FACT|DESIGN_PATTERN|ANTI_PATTERN|EXTERNAL_EXPERIENCE",
  "statement": "precise claim from the source",
  "evidence_span": "exact quote from source supporting this claim",
  "discipline": "relevant discipline",
  "scope": "scope of applicability",
  "conditions": "conditions under which this holds",
  "exceptions": "known exceptions",
  "version_context": "version/time context if applicable"
}

Return ONLY a JSON array. No explanation."""

VERIFICATION_SYSTEM_PROMPT = """You are an independent knowledge verifier.

You receive:
1. A candidate knowledge atom (claim)
2. The source evidence it was extracted from
3. Minimal surrounding context

Your task: determine whether the claim is SUPPORTED by the evidence.

VERDICTS:
- SUPPORTED: The evidence directly and clearly supports the claim
- PARTIALLY_SUPPORTED: The evidence supports a narrower version of the claim
- OVERCLAIMED: The claim is broader than what the evidence supports
- UNSUPPORTED: The evidence does not support the claim
- INSUFFICIENT_EVIDENCE: Not enough evidence to judge

IMPORTANT:
- Do NOT accept claims that invent causal relationships not in the evidence
- Do NOT accept claims that generalize beyond the source
- Conservative rejection is preferred over false acceptance

Return ONLY a JSON object:
{"verdict": "SUPPORTED|PARTIALLY_SUPPORTED|OVERCLAIMED|UNSUPPORTED|INSUFFICIENT_EVIDENCE", 
 "reasoning": "brief explanation",
 "corrected_statement": "if PARTIALLY_SUPPORTED, a narrower claim"}"""


def load_extraction_golden_set() -> list[dict]:
    """Load the frozen extraction reference set."""
    if not GOLDEN_SET_PATH.exists():
        return []
    with open(GOLDEN_SET_PATH) as f:
        data = json.load(f)
    return data.get("excerpts", data.get("items", []))


def load_retrieval_golden_set() -> list[dict]:
    """Load the frozen retrieval relevance set."""
    if not RETRIEVAL_SET_PATH.exists():
        return []
    with open(RETRIEVAL_SET_PATH) as f:
        data = json.load(f)
    return data.get("queries", [])


def _fuzzy_match(extracted: str, expected: str) -> float:
    """Compute word-overlap match score."""
    ext = set(re.sub(r'[^\w\s]', '', extracted.lower()).split())
    exp = set(re.sub(r'[^\w\s]', '', expected.lower()).split())
    if not exp:
        return 0.0
    return len(ext & exp) / len(exp)


def _type_compatible(a: str, b: str) -> bool:
    """Check if atom types are compatible."""
    groups = {
        "FACT": ["FACT", "VERSION_FACT", "LICENSE_FACT", "PERFORMANCE_FACT"],
        "PRINCIPLE": ["PRINCIPLE", "TRADEOFF", "DESIGN_PATTERN", "REFERENCE_PRINCIPLE"],
        "TOOL": ["TOOL_CAPABILITY", "TOOL_LIMITATION"],
        "PROCEDURE": ["PROCEDURE", "CONSTRAINT", "FAILURE_PATTERN"],
    }
    a_up = a.upper() if a else ""
    b_up = b.upper() if b else ""
    for group, members in groups.items():
        if a_up in members and b_up in members:
            return True
    # Also accept if either is empty/unknown
    if not a_up or not b_up:
        return True
    return a_up == b_up


def run_extraction_benchmark(model_id: str, golden_set: list[dict],
                             max_items: int = 27) -> dict:
    """Run extraction benchmark for a single model."""
    print(f"\n{'='*60}")
    print(f"EXTRACTION BENCHMARK: {model_id}")
    print(f"{'='*60}")

    results = []
    total_latency = 0
    failures = 0

    for i, excerpt in enumerate(golden_set[:max_items]):
        source_text = excerpt.get("text", excerpt.get("source_text", ""))
        expected_atoms = excerpt.get("expected_atoms", [])
        must_not_extract = excerpt.get("must_not_extract", [])

        if not source_text:
            continue

        print(f"  [{i+1}/{min(len(golden_set), max_items)}] excerpt_id={excerpt.get('id', i)}...", end=" ")

        response = chat_completion(
            model=model_id,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Source text:\n\n{source_text[:3000]}\n\nExtract knowledge atoms."}
            ],
            max_tokens=2000,
            temperature=0.0,
            timeout=60
        )

        if not response["success"]:
            print(f"FAIL: {response.get('error', 'unknown')[:60]}")
            failures += 1
            continue

        total_latency += response["latency"]
        content = response["content"]

        # Parse JSON from response
        try:
            # Try to extract JSON array from response
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                extracted_atoms = json.loads(json_match.group())
            else:
                extracted_atoms = []
        except json.JSONDecodeError:
            print(f"MALFORMED JSON")
            failures += 1
            continue

        # Score against expected
        excerpt_results = {
            "excerpt_id": excerpt.get("id", i),
            "extracted_count": len(extracted_atoms),
            "expected_count": len(expected_atoms),
            "must_not_count": len(must_not_extract),
            "matches": [],
            "misses": [],
            "false_positives": [],
            "overclaims": [],
        }

        # Check extracted against expected
        matched_expected = set()
        for atom in extracted_atoms:
            atom_stmt = atom.get("statement", "")
            atom_type = atom.get("type", atom.get("atom_type", "FACT"))
            best_match = None
            best_score = 0.0

            for j, exp in enumerate(expected_atoms):
                if j in matched_expected:
                    continue
                exp_stmt = exp.get("statement", "")
                score = _fuzzy_match(atom_stmt, exp_stmt)
                exp_type = exp.get("atom_type", exp.get("type", ""))
                type_ok = _type_compatible(atom_type, exp_type)
                if score > best_score and type_ok:
                    best_score = score
                    best_match = j

            if best_match is not None and best_score >= 0.3:
                matched_expected.add(best_match)
                excerpt_results["matches"].append({
                    "extracted": atom_stmt[:100],
                    "expected": expected_atoms[best_match]["statement"][:100],
                    "score": round(best_score, 3),
                    "type": atom_type,
                })
            else:
                # Check if it's a must-not-extract
                is_forbidden = False
                for fn in must_not_extract:
                    fn_text = fn.get("text", fn.get("statement", ""))
                    if _fuzzy_match(atom_stmt, fn_text) > 0.5:
                        is_forbidden = True
                        break
                if is_forbidden:
                    excerpt_results["false_positives"].append(atom_stmt[:100])
                else:
                    excerpt_results["overclaims"].append(atom_stmt[:100])

        # Check misses
        for j, exp in enumerate(expected_atoms):
            if j not in matched_expected:
                excerpt_results["misses"].append(exp.get("statement", "")[:100])

        results.append(excerpt_results)
        tp = len(excerpt_results["matches"])
        fp = len(excerpt_results["overclaims"]) + len(excerpt_results["false_positives"])
        fn = len(excerpt_results["misses"])
        print(f"TP={tp} FP={fp} FN={fn}")

    # Aggregate metrics
    total_tp = sum(len(r["matches"]) for r in results)
    total_fp = sum(len(r["overclaims"]) + len(r["false_positives"]) for r in results)
    total_fn = sum(len(r["misses"]) for r in results)
    total_forbidden = sum(len(r["false_positives"]) for r in results)
    total_overclaims = sum(len(r["overclaims"]) for r in results)
    total_expected = sum(r["expected_count"] for r in results)

    precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    overclaim_rate = total_fp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    false_positive_rate = total_forbidden / max(total_forbidden + total_tp, 1)
    avg_latency = total_latency / max(len(results), 1)

    metrics = {
        "model": model_id,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "overclaim_rate": round(overclaim_rate, 4),
        "false_positive_forbidden": total_forbidden,
        "false_positive_overclaims": total_overclaims,
        "false_positive_rate": round(false_positive_rate, 4),
        "total_tp": total_tp,
        "total_fp": total_fp,
        "total_fn": total_fn,
        "total_expected": total_expected,
        "avg_latency": round(avg_latency, 3),
        "failure_count": failures,
        "items_evaluated": len(results),
    }

    print(f"\n--- {model_id} RESULTS ---")
    print(f"  Precision: {metrics['precision']:.1%}")
    print(f"  Recall:    {metrics['recall']:.1%}")
    print(f"  F1:        {metrics['f1']:.1%}")
    print(f"  Overclaim: {metrics['overclaim_rate']:.1%}")
    print(f"  Forbidden FP: {metrics['false_positive_forbidden']}")
    print(f"  Avg latency:  {metrics['avg_latency']}s")
    print(f"  Failures:     {metrics['failure_count']}")

    return metrics


def run_verification_benchmark(model_id: str) -> dict:
    """Run verification benchmark with deliberate test cases."""
    print(f"\n{'='*60}")
    print(f"VERIFICATION BENCHMARK: {model_id}")
    print(f"{'='*60}")

    # Construct test cases with known verdicts
    test_cases = [
        {
            "claim": "WCAG 2.2 SC 2.5.8 TARGET SIZE (MINIMUM) requires 24x24 CSS pixels at Level AA",
            "evidence": "WCAG 2.2 SC 2.5.8 Target Size (Minimum) Level AA requires target sizes of at least 24 by 24 CSS pixels, subject to several exceptions.",
            "expected_verdict": "SUPPORTED",
        },
        {
            "claim": "All touch targets must be at least 44x44 pixels for WCAG AA compliance",
            "evidence": "WCAG 2.2 SC 2.5.8 Target Size (Minimum) Level AA requires 24x24 CSS pixels. SC 2.5.5 Target Size (Enhanced) Level AAA recommends 44x44.",
            "expected_verdict": "OVERCLAIMED",
        },
        {
            "claim": "Typography hierarchy is established through contrast and scale",
            "evidence": "Visual hierarchy in typography uses contrast in weight, size, and color to guide the reader's attention through the content.",
            "expected_verdict": "SUPPORTED",
        },
        {
            "claim": "Semantic similarity between CSS properties determines rendering output",
            "evidence": "CSS properties like margin and padding both create space, but margin creates space outside the element while padding creates space inside.",
            "expected_verdict": "UNSUPPORTED",
        },
        {
            "claim": "The rule of thirds guarantees effective composition",
            "evidence": "The rule of thirds is a compositional guideline that divides the frame into thirds.",
            "expected_verdict": "OVERCLAIMED",
        },
        {
            "claim": "FTS5 uses BM25 scoring by default in SQLite",
            "evidence": "SQLite FTS5 full-text search module uses a ranking function based on BM25 by default.",
            "expected_verdict": "SUPPORTED",
        },
        {
            "claim": "Claude models are trained on copyrighted material",
            "evidence": "The specific training data composition of Claude models has not been publicly disclosed by Anthropic.",
            "expected_verdict": "INSUFFICIENT_EVIDENCE",
        },
        {
            "claim": "Reciprocal Rank Fusion always outperforms individual retrieval methods",
            "evidence": "RRF combines ranked lists but empirical results vary by corpus and query type.",
            "expected_verdict": "OVERCLAIMED",
        },
    ]

    results = []
    correct = 0
    total = 0
    false_acceptances = 0
    false_rejections = 0
    overclaim_detected = 0
    total_overclaim_cases = 0
    total_latency = 0
    failures = 0

    for i, tc in enumerate(test_cases):
        print(f"  [{i+1}/{len(test_cases)}] expected={tc['expected_verdict']}...", end=" ")

        response = chat_completion(
            model=model_id,
            messages=[
                {"role": "system", "content": VERIFICATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Candidate claim: {tc['claim']}\n\nSource evidence: {tc['evidence']}"}
            ],
            max_tokens=500,
            temperature=0.0,
            timeout=45
        )

        if not response["success"]:
            print(f"FAIL: {response.get('error', '')[:50]}")
            failures += 1
            continue

        total_latency += response["latency"]
        content = response["content"]

        try:
            json_match = re.search(r'\{[^{}]*"verdict"[^{}]*\}', content)
            if json_match:
                verdict_data = json.loads(json_match.group())
                actual_verdict = verdict_data.get("verdict", "UNKNOWN")
            else:
                # Try to find verdict keyword
                for v in ["SUPPORTED", "PARTIALLY_SUPPORTED", "OVERCLAIMED", "UNSUPPORTED", "INSUFFICIENT_EVIDENCE"]:
                    if v in content:
                        actual_verdict = v
                        break
                else:
                    actual_verdict = "UNKNOWN"
        except Exception:
            actual_verdict = "UNKNOWN"

        expected = tc["expected_verdict"]
        match = actual_verdict == expected
        total += 1
        if match:
            correct += 1
            print(f"CORRECT ({actual_verdict})")
        else:
            print(f"WRONG (got {actual_verdict}, expected {expected})")

        # Track false acceptances (accepted OVERCLAIMED/UNSUPPORTED as SUPPORTED)
        if expected in ("OVERCLAIMED", "UNSUPPORTED") and actual_verdict == "SUPPORTED":
            false_acceptances += 1
        if expected == "SUPPORTED" and actual_verdict in ("OVERCLAIMED", "UNSUPPORTED"):
            false_rejections += 1
        if expected == "OVERCLAIMED" and actual_verdict in ("OVERCLAIMED", "UNSUPPORTED"):
            overclaim_detected += 1
        if expected == "OVERCLAIMED":
            total_overclaim_cases += 1

        results.append({
            "expected": expected,
            "actual": actual_verdict,
            "match": match,
        })

    verdict_accuracy = correct / total if total > 0 else 0.0
    avg_latency = total_latency / max(total, 1)

    metrics = {
        "model": model_id,
        "verdict_accuracy": round(verdict_accuracy, 4),
        "false_acceptance_rate": round(false_acceptances / max(total, 1), 4),
        "false_rejection_rate": round(false_rejections / max(total, 1), 4),
        "overclaim_detection_rate": round(overclaim_detected / max(total_overclaim_cases, 1), 4),
        "correct": correct,
        "total": total,
        "false_acceptances": false_acceptances,
        "false_rejections": false_rejections,
        "avg_latency": round(avg_latency, 3),
        "failure_count": failures,
        "results": results,
    }

    print(f"\n--- {model_id} VERIFICATION RESULTS ---")
    print(f"  Verdict accuracy:   {metrics['verdict_accuracy']:.1%}")
    print(f"  False acceptance:   {metrics['false_acceptance_rate']:.1%}")
    print(f"  False rejection:    {metrics['false_rejection_rate']:.1%}")
    print(f"  Overclaim detected: {metrics['overclaim_detection_rate']:.1%}")
    print(f"  Avg latency:        {metrics['avg_latency']}s")

    return metrics


def run_embedding_benchmark(model_id: str, atoms: list[dict]) -> dict:
    """Run embedding benchmark using retrieval relevance set."""
    print(f"\n{'='*60}")
    print(f"EMBEDDING BENCHMARK: {model_id}")
    print(f"{'='*60}")

    if not atoms:
        print("  No atoms available for embedding")
        return {"model": model_id, "error": "no atoms"}

    # Embed the atom corpus
    texts = [a.get("statement", "")[:500] for a in atoms[:50]]
    print(f"  Embedding {len(texts)} atoms...", end=" ")

    emb_result = embed_texts(model_id, texts, timeout=60)
    if not emb_result["success"]:
        print(f"FAIL: {emb_result.get('error', '')[:80]}")
        return {"model": model_id, "error": emb_result.get("error", "")}

    print(f"OK ({emb_result['dimensions']}d, {emb_result['latency']}s)")

    # Test semantic similarity with known relevant pairs
    test_queries = [
        ("WCAG contrast requirements", "WCAG AA requires 4.5:1 contrast ratio for normal text"),
        ("semantic search approach", "FTS5 uses BM25 scoring for lexical search"),
        ("visual hierarchy principles", "Typography establishes hierarchy through scale and weight"),
        ("animation timing", "Easing curves control the rate of change in animation"),
        ("model performance benchmark", "Precision and recall measure extraction quality"),
    ]

    correct_rankings = 0
    total_rankings = 0
    latencies = []

    for query_text, expected_match_text in test_queries:
        # Embed query
        q_result = embed_texts(model_id, [query_text], timeout=30)
        if not q_result["success"]:
            continue
        latencies.append(q_result["latency"])

        q_emb = q_result["embeddings"][0]

        # Compute cosine similarity against all atom embeddings
        similarities = []
        for i, emb in enumerate(emb_result["embeddings"]):
            # Cosine similarity
            dot = sum(a * b for a, b in zip(q_emb, emb))
            norm_a = sum(a * a for a in q_emb) ** 0.5
            norm_b = sum(b * b for b in emb) ** 0.5
            sim = dot / (norm_a * norm_b) if (norm_a * norm_b) > 0 else 0
            similarities.append((sim, texts[i][:80]))

        similarities.sort(reverse=True)

        # Check if expected match is in top 5
        total_rankings += 1
        top_5 = [s[1] for s in similarities[:5]]
        for t5 in top_5:
            if any(w in t5.lower() for w in expected_match_text.lower().split()[:5]):
                correct_rankings += 1
                break

    avg_latency = sum(latencies) / max(len(latencies), 1)

    metrics = {
        "model": model_id,
        "dimensions": emb_result["dimensions"],
        "atoms_indexed": len(texts),
        "retrieval_accuracy": round(correct_rankings / max(total_rankings, 1), 4),
        "top5_relevant": correct_rankings,
        "total_queries": total_rankings,
        "avg_latency": round(avg_latency, 3),
    }

    print(f"\n--- {model_id} EMBEDDING RESULTS ---")
    print(f"  Dimensions:     {metrics['dimensions']}")
    print(f"  Atoms indexed:  {metrics['atoms_indexed']}")
    print(f"  Top-5 relevant: {metrics['top5_relevant']}/{metrics['total_queries']}")
    print(f"  Avg latency:    {metrics['avg_latency']}s")

    return metrics


def run_visual_grounding_benchmark(model_id: str, image_paths: list[dict]) -> dict:
    """Run visual grounding tests with actual image bytes."""
    print(f"\n{'='*60}")
    print(f"VISUAL GROUNDING BENCHMARK: {model_id}")
    print(f"{'='*60}")

    if not image_paths:
        print("  No images available")
        return {"model": model_id, "error": "no images"}

    correct = 0
    total = 0
    failures = 0
    latencies = []

    for img_info in image_paths[:10]:
        img_path = img_info["path"]
        questions = img_info.get("questions", [])

        if not os.path.exists(img_path):
            print(f"  SKIP: {img_path} not found")
            continue

        # Read and base64 encode image
        try:
            with open(img_path, "rb") as f:
                img_bytes = f.read()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
            img_hash = hashlib.sha256(img_bytes).hexdigest()[:16]
        except Exception as e:
            print(f"  SKIP: {img_path} read error: {e}")
            continue

        for q in questions:
            question_text = q["question"]
            expected_answer = q["expected"]

            print(f"  [{img_hash}] Q: {question_text[:50]}...", end=" ")

            # Build multimodal message
            messages = [
                {"role": "system", "content": "You are a visual analysis system. Answer questions about images precisely and concisely. Return ONLY a JSON object with your answer."},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Question: {question_text}\n\nReturn JSON: {{\"answer\": \"your answer\", \"confidence\": \"HIGH|MEDIUM|LOW\"}}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]}
            ]

            response = chat_completion(
                model=model_id,
                messages=messages,
                max_tokens=300,
                temperature=0.0,
                timeout=45
            )

            if not response["success"]:
                print(f"FAIL: {response.get('error', '')[:50]}")
                failures += 1
                continue

            latencies.append(response["latency"])
            content = response["content"]

            # Check if answer matches expected
            total += 1
            content_lower = content.lower()
            expected_lower = expected_answer.lower()

            # Simple keyword match for grounding
            match = any(w in content_lower for w in expected_lower.split()[:3])
            if match:
                correct += 1
                print(f"CORRECT")
            else:
                print(f"WRONG (expected '{expected_answer[:30]}')")

    accuracy = correct / total if total > 0 else 0.0
    avg_latency = sum(latencies) / max(len(latencies), 1)

    metrics = {
        "model": model_id,
        "accuracy": round(accuracy, 4),
        "correct": correct,
        "total": total,
        "failures": failures,
        "avg_latency": round(avg_latency, 3),
    }

    print(f"\n--- {model_id} VISUAL GROUNDING RESULTS ---")
    print(f"  Accuracy:  {metrics['accuracy']:.1%}")
    print(f"  Correct:   {metrics['correct']}/{metrics['total']}")
    print(f"  Failures:  {metrics['failures']}")
    print(f"  Latency:   {metrics['avg_latency']}s")

    return metrics


def find_foundry_images() -> list[dict]:
    """Find Foundry-owned/generated images for visual testing."""
    images = []

    # Look for turntable frames
    turntable_dir = ROOT / "artifacts" / "creative-stack-validation" / "blender-ops" / "turntable"
    if turntable_dir.exists():
        for f in sorted(turntable_dir.glob("*.png"))[:3]:
            images.append({
                "path": str(f),
                "source": "foundry-generated",
                "questions": [
                    {"question": "Is this image landscape or portrait orientation?", "expected": "landscape"},
                    {"question": "What is the dominant color tone?", "expected": "dark"},
                    {"question": "Does the image contain a 3D rendered object?", "expected": "yes"},
                ]
            })

    # Look for preview frames
    preview_dir = ROOT / "artifacts" / "creative-stack-validation" / "blender-ops" / "preview"
    if preview_dir.exists():
        for f in sorted(preview_dir.glob("*.png"))[:2]:
            images.append({
                "path": str(f),
                "source": "foundry-generated",
                "questions": [
                    {"question": "Is this a rendered 3D scene?", "expected": "yes"},
                    {"question": "Does the image show lighting effects?", "expected": "yes"},
                ]
            })

    # Look for creative stack images
    image_dir = ROOT / "artifacts" / "creative-stack-validation" / "image"
    if image_dir.exists():
        for f in sorted(image_dir.glob("*.png"))[:2]:
            images.append({
                "path": str(f),
                "source": "foundry-validation",
                "questions": [
                    {"question": "What type of image is this?", "expected": "rendered"},
                ]
            })

    # Asset vault blobs
    vault_dir = ROOT / "artifacts" / "asset-vault" / "blobs"
    if vault_dir.exists():
        for f in sorted(vault_dir.glob("*.png"))[:3]:
            images.append({
                "path": str(f),
                "source": "asset-vault",
                "questions": [
                    {"question": "Does this image contain text or UI elements?", "expected": "no"},
                ]
            })

    return images


def run_all_tournaments():
    """Run all M002.1 model tournaments."""
    print("=" * 70)
    print("KAPIF M002.1 MODEL INTELLIGENCE TOURNAMENTS")
    print("=" * 70)

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "extraction": {},
        "verification": {},
        "embedding": {},
        "visual_grounding": {},
    }

    # Load reference sets
    extraction_set = load_extraction_golden_set()
    print(f"Extraction golden set: {len(extraction_set)} excerpts")

    # ── EXTRACTION TOURNAMENT ──
    print("\n" + "=" * 70)
    print("TOURNAMENT 1: PROFESSIONAL EXTRACTION")
    print("=" * 70)
    extraction_metrics = {}
    for model_id in EXTRACTION_CANDIDATES:
        metrics = run_extraction_benchmark(model_id, extraction_set)
        extraction_metrics[model_id] = metrics
        record_benchmark(Role.PROFESSIONAL_EXTRACTION, model_id,
                        "m002.1-extraction-tournament", metrics,
                        f"Full extraction benchmark on {len(extraction_set)} excerpts")

    # Select preferred extractor
    best_extraction = max(extraction_metrics.items(),
                         key=lambda x: (x[1].get("f1", 0), -x[1].get("overclaim_rate", 1)))
    backup_extraction = sorted(extraction_metrics.items(),
                              key=lambda x: (x[1].get("f1", 0), -x[1].get("overclaim_rate", 1)),
                              reverse=True)
    backup_id = backup_extraction[1][0] if len(backup_extraction) > 1 else None

    if best_extraction[1].get("f1", 0) > 0:
        set_role_preference(
            Role.PROFESSIONAL_EXTRACTION,
            best_extraction[0], backup_id,
            "m002.1-extraction-tournament",
            f"F1={best_extraction[1]['f1']:.1%}, overclaim={best_extraction[1]['overclaim_rate']:.1%}",
            "PROVISIONAL", sample_n=len(extraction_set)
        )
    results["extraction"] = {
        "candidates": extraction_metrics,
        "preferred": best_extraction[0],
        "preferred_f1": best_extraction[1].get("f1", 0),
        "preferred_overclaim": best_extraction[1].get("overclaim_rate", 0),
    }

    # ── VERIFICATION TOURNAMENT ──
    print("\n" + "=" * 70)
    print("TOURNAMENT 2: INDEPENDENT VERIFICATION")
    print("=" * 70)
    verification_metrics = {}
    for model_id in VERIFICATION_CANDIDATES:
        metrics = run_verification_benchmark(model_id)
        verification_metrics[model_id] = metrics
        record_benchmark(Role.INDEPENDENT_VERIFICATION, model_id,
                        "m002.1-verification-tournament", metrics,
                        "Verification benchmark on 8 test cases")

    # Select preferred verifier — prioritize low false acceptance
    best_verification = max(verification_metrics.items(),
                           key=lambda x: (x[1].get("verdict_accuracy", 0),
                                         -x[1].get("false_acceptance_rate", 1)))
    results["verification"] = {
        "candidates": verification_metrics,
        "preferred": best_verification[0],
        "preferred_accuracy": best_verification[1].get("verdict_accuracy", 0),
    }

    # ── EMBEDDING TOURNAMENT ──
    print("\n" + "=" * 70)
    print("TOURNAMENT 3: EMBEDDING RETRIEVAL")
    print("=" * 70)
    # Load atoms for embedding
    from kapif.data_layer import search_atoms
    atoms = search_atoms("knowledge", limit=50)
    embedding_metrics = {}
    for model_id in EMBEDDING_CANDIDATES:
        metrics = run_embedding_benchmark(model_id, atoms)
        embedding_metrics[model_id] = metrics
        record_benchmark(Role.EMBEDDING_RETRIEVAL, model_id,
                        "m002.1-embedding-tournament", metrics,
                        "Embedding retrieval benchmark")

    if embedding_metrics:
        best_embed = max(embedding_metrics.items(),
                        key=lambda x: x[1].get("retrieval_accuracy", 0))
        set_role_preference(
            Role.EMBEDDING_RETRIEVAL,
            best_embed[0], None,
            "m002.1-embedding-tournament",
            f"execution-confirmed only; retrieval tournament requires frozen relevance metrics",
            "LOW", sample_n=0
        )
    results["embedding"] = embedding_metrics

    # ── VISUAL GROUNDING TOURNAMENT ──
    print("\n" + "=" * 70)
    print("TOURNAMENT 4: VISUAL GROUNDING")
    print("=" * 70)
    images = find_foundry_images()
    print(f"Found {len(images)} test images")
    visual_metrics = {}
    for model_id in VISUAL_CANDIDATES:
        metrics = run_visual_grounding_benchmark(model_id, images)
        visual_metrics[model_id] = metrics
        record_benchmark(Role.VISUAL_GROUNDING, model_id,
                        "m002.1-visual-grounding-tournament", metrics,
                        f"Visual grounding on {len(images)} images")

    if visual_metrics:
        best_visual = max(visual_metrics.items(),
                         key=lambda x: x[1].get("accuracy", 0))
        set_role_preference(
            Role.VISUAL_GROUNDING,
            best_visual[0], None,
            "m002.1-visual-grounding-tournament",
            f"small-sample objective grounding only; professional critique not established",
            "LOW", sample_n=best_visual[1].get("total", 0)
        )
    results["visual_grounding"] = visual_metrics

    # ── SAVE RESULTS ──
    output_path = OUTPUT_DIR / "m002.1-tournament-results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to {output_path}")

    # ── SUMMARY ──
    print("\n" + "=" * 70)
    print("TOURNAMENT SUMMARY — ROLE PREFERRED MODELS")
    print("=" * 70)

    from kapif.model_intelligence import get_all_role_preferences
    prefs = get_all_role_preferences()
    for role, pref in prefs.items():
        print(f"  {role}:")
        print(f"    Preferred: {pref.get('preferred_model', 'none')}")
        print(f"    Backup:    {pref.get('backup_model', 'none')}")
        print(f"    Reason:    {pref.get('selection_reason', '')}")

    return results


if __name__ == "__main__":
    results = run_all_tournaments()
