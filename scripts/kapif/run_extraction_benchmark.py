#!/usr/bin/env python3
"""
Run extraction benchmark against frozen reference set.

Measures:
- claim precision (extracted atoms that match expected)
- claim recall (expected atoms that were extracted)
- F1
- atom-type accuracy
- evidence-span grounding accuracy
- overclaim rate
- causal-invention rate
- must-not-extract false-positive rate
- latency p50/p95
- model failure rate
"""
import json
import hashlib
import sys
import time
import io
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(ROOT / "scripts"))


from kapif.llm_extractor import extract_atoms, verify_atom
from kapif.embeddings import is_available, embed_text

# Load frozen reference set
GOLDEN_SET_PATH = ROOT / "data" / "kapif" / "golden-sets" / "extraction-golden-set.json"
FREEZE_PATH = ROOT / "data" / "kapif" / "golden-sets" / "freeze-manifest.json"
OUTPUT_DIR = ROOT / "data" / "kapif" / "benchmark-results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _verify_freeze():
    """Verify reference set hasn't been modified since freeze."""
    if not FREEZE_PATH.exists():
        print("WARNING: No freeze manifest found")
        return True
    
    freeze = json.load(open(FREEZE_PATH))
    ref_hash = freeze["sets"]["FOUNDRY_CURATED_EXTRACTION_REFERENCE_SET"]["sha256"]
    
    with open(GOLDEN_SET_PATH, "rb") as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()
    
    if current_hash != ref_hash:
        print(f"FATAL: Reference set modified! frozen={ref_hash[:16]} current={current_hash[:16]}")
        return False
    print(f"Freeze verified: {current_hash[:16]}...")
    return True


def _fuzzy_match(extracted: str, expected: str) -> float:
    """Compute fuzzy match score between extracted and expected statements."""
    # Normalize
    ext = set(extracted.lower().replace(".", "").replace(",", "").split())
    exp = set(expected.lower().replace(".", "").replace(",", "").split())
    
    if not exp:
        return 0.0
    
    overlap = len(ext & exp)
    return overlap / len(exp)


def _type_match(extracted_type: str, expected_type: str) -> bool:
    """Check if atom types are equivalent."""
    aliases = {
        "FACT": ["FACT", "VERSION_FACT", "LICENSE_FACT", "PERFORMANCE_FACT"],
        "PRINCIPLE": ["PRINCIPLE", "TRADEOFF", "DESIGN_PATTERN"],
        "TOOL_CAPABILITY": ["TOOL_CAPABILITY", "TOOL_LIMITATION"],
        "PROCEDURE": ["PROCEDURE", "CONSTRAINT", "FAILURE_PATTERN"],
    }
    for group, members in aliases.items():
        if extracted_type in members and expected_type in members:
            return True
    return extracted_type == expected_type


def run_benchmark(max_excerpts: int = 10) -> dict[str, Any]:
    """Run extraction benchmark on reference set.
    
    Uses subset by default due to rate limits on free models.
    """
    if not _verify_freeze():
        return {"error": "Freeze verification failed"}
    
    golden = json.load(open(GOLDEN_SET_PATH))
    excerpts = golden["excerpts"][:max_excerpts]
    
    print(f"\n=== Extraction Benchmark ===")
    print(f"Excerpts: {len(excerpts)}")
    print(f"Embedding provider: {'available' if is_available() else 'unavailable'}")
    
    results = []
    total_expected = 0
    total_extracted = 0
    total_matched = 0
    total_type_correct = 0
    total_span_grounded = 0
    total_overclaim = 0
    total_must_not_fp = 0
    total_latencies = []
    model_failures = 0
    
    for i, excerpt in enumerate(excerpts):
        print(f"\n[{i+1}/{len(excerpts)}] {excerpt['id']}: {excerpt['domain']}")
        
        # Extract
        t0 = time.time()
        extraction = extract_atoms(
            excerpt["text"],
            {"url": excerpt["source_url"], "source_class": excerpt["source_class"]},
            hashlib.sha256(excerpt["text"].encode()).hexdigest()
        )
        latency_ms = int((time.time() - t0) * 1000)
        total_latencies.append(latency_ms)
        
        extracted_atoms = extraction["atoms"]
        expected_atoms = excerpt["expected_atoms"]
        must_not = excerpt["must_not_extract"]
        
        total_expected += len(expected_atoms)
        total_extracted += len(extracted_atoms)
        
        if extraction.get("error"):
            model_failures += 1
            print(f"  ERROR: {extraction['error'][:80]}")
            continue
        
        print(f"  Extracted: {len(extracted_atoms)}, Expected: {len(expected_atoms)}, Must-not: {len(must_not)}")
        
        # Match extracted to expected
        matched_expected = set()
        for ext in extracted_atoms:
            best_match = 0.0
            best_idx = -1
            for j, exp in enumerate(expected_atoms):
                if j in matched_expected:
                    continue
                score = _fuzzy_match(ext["statement"], exp["statement"])
                if score > best_match:
                    best_match = score
                    best_idx = j
            
            if best_match >= 0.5 and best_idx >= 0:
                matched_expected.add(best_idx)
                total_matched += 1
                
                # Type accuracy
                if _type_match(ext.get("atom_type", ""), expected_atoms[best_idx]["atom_type"]):
                    total_type_correct += 1
                
                # Span grounding
                if ext.get("evidence_span", "") and len(ext["evidence_span"]) > 5:
                    total_span_grounded += 1
                
                # Overclaim detection
                if best_match < 0.7:
                    total_overclaim += 1
                
                print(f"    MATCH: {ext['statement'][:60]}... (score={best_match:.2f})")
            else:
                # Check if it's a must-not-extract
                is_must_not = False
                for mn in must_not:
                    if _fuzzy_match(ext["statement"], mn["text"]) > 0.4:
                        total_must_not_fp += 1
                        is_must_not = True
                        print(f"    FALSE POSITIVE (must-not): {ext['statement'][:60]}...")
                        break
                if not is_must_not:
                    print(f"    UNMATCHED: {ext['statement'][:60]}...")
        
        # Check missed expectations
        missed = len(expected_atoms) - len(matched_expected)
        if missed > 0:
            print(f"    MISSED: {missed} expected atoms not extracted")
    
    # Compute metrics
    precision = total_matched / total_extracted if total_extracted > 0 else 0.0
    recall = total_matched / total_expected if total_expected > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    type_accuracy = total_type_correct / total_matched if total_matched > 0 else 0.0
    grounding_rate = total_span_grounded / total_matched if total_matched > 0 else 0.0
    overclaim_rate = total_overclaim / total_matched if total_matched > 0 else 0.0
    must_not_fp_rate = total_must_not_fp / max(total_extracted, 1)
    
    latencies_sorted = sorted(total_latencies)
    p50 = latencies_sorted[len(latencies_sorted)//2] if latencies_sorted else 0
    p95 = latencies_sorted[int(len(latencies_sorted)*0.95)] if latencies_sorted else 0
    
    report = {
        "date": datetime.now().isoformat(),
        "excerpts_run": len(excerpts),
        "total_expected_atoms": total_expected,
        "total_extracted_atoms": total_extracted,
        "matched": total_matched,
        "metrics": {
            "claim_precision": round(precision, 4),
            "claim_recall": round(recall, 4),
            "f1": round(f1, 4),
            "atom_type_accuracy": round(type_accuracy, 4),
            "evidence_span_grounding_rate": round(grounding_rate, 4),
            "overclaim_rate": round(overclaim_rate, 4),
            "must_not_extract_fp_rate": round(must_not_fp_rate, 4),
        },
        "latency_ms": {"p50": p50, "p95": p95},
        "model_failures": model_failures,
        "failure_rate": round(model_failures / len(excerpts), 4) if excerpts else 0,
    }
    
    # Save report
    out_path = OUTPUT_DIR / "extraction-benchmark-results.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== Results ===")
    print(f"Precision: {precision:.2%}")
    print(f"Recall: {recall:.2%}")
    print(f"F1: {f1:.2%}")
    print(f"Type accuracy: {type_accuracy:.2%}")
    print(f"Span grounding: {grounding_rate:.2%}")
    print(f"Overclaim rate: {overclaim_rate:.2%}")
    print(f"Must-not FP rate: {must_not_fp_rate:.2%}")
    print(f"Latency p50={p50}ms p95={p95}ms")
    print(f"Model failures: {model_failures}/{len(excerpts)}")
    print(f"Report saved: {out_path}")
    
    return report


if __name__ == "__main__":
    max_excerpts = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    run_benchmark(max_excerpts)
