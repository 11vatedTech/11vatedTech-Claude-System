#!/usr/bin/env python3
"""Bounded visual-grounding V3 dataset and scoring utilities.

The dataset uses real PNG artifacts already owned by the Foundry. Ground truth
is explicit controlled/adjudicated metadata; it is never inferred from a
filename or from model output. Model execution, scoring, persistence, and
console presentation remain separate failure boundaries.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "kapif" / "m002.1"

ENUMS = {
    "orientation": {"PORTRAIT", "LANDSCAPE", "SQUARE"},
    "ui_present": {"YES", "NO", "UNCERTAIN", "NOT_APPLICABLE"},
    "render_type": {"3D", "2D", "MIXED", "NONE", "UNCERTAIN", "NOT_APPLICABLE"},
    "dominant_value": {"LOW_KEY", "MID_KEY", "HIGH_KEY", "MIXED", "UNCERTAIN", "NOT_APPLICABLE"},
    "focal_region": {"TOP_LEFT", "TOP_CENTER", "TOP_RIGHT", "CENTER_LEFT", "CENTER", "CENTER_RIGHT", "BOTTOM_LEFT", "BOTTOM_CENTER", "BOTTOM_RIGHT", "MULTIPLE", "NONE", "UNCERTAIN", "NOT_APPLICABLE"},
    "visible_text": {"YES", "NO", "UNCERTAIN", "NOT_APPLICABLE"},
    "major_clipping": {"YES", "NO", "UNCERTAIN", "NOT_APPLICABLE"},
    "major_overlap": {"YES", "NO", "UNCERTAIN", "NOT_APPLICABLE"},
}

# Each label record is a controlled/adjudicated assertion. The artifact path
# is deliberately not used to derive labels. Existing turntable sequences are
# represented only sparsely to avoid making temporal duplicates the benchmark.
REAL_SPECS = [
    ("real-001", "artifacts/flagship/emberveil/preview/preview-frame-0024.png", {"ui_present": "NO", "render_type": "3D", "dominant_value": "LOW_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-002", "artifacts/flagship/emberveil/preview-frame-0001.png", {"ui_present": "NO", "render_type": "3D", "dominant_value": "LOW_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-003", "artifacts/creative-stack-validation/blender/render.png", {"ui_present": "NO", "render_type": "3D", "dominant_value": "MID_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-004", "artifacts/creative-stack-validation/image/generated.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "HIGH_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-005", "artifacts/creative-stack-validation/image/alpha.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "HIGH_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-006", "artifacts/composition-lab/comp-a.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "MID_KEY", "focal_region": "CENTER_LEFT", "visible_text": "YES", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-007", "artifacts/composition-lab/comp-b.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "MID_KEY", "focal_region": "CENTER_RIGHT", "visible_text": "YES", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-008", "artifacts/composition-lab/comp-c-original.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "LOW_KEY", "focal_region": "MULTIPLE", "visible_text": "YES", "major_clipping": "NO", "major_overlap": "YES"}),
    ("real-009", "artifacts/composition-lab/comp-c-repaired.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "MID_KEY", "focal_region": "CENTER", "visible_text": "YES", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-010", "artifacts/composition-lab/transfer-wrong.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "LOW_KEY", "focal_region": "CENTER_RIGHT", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-011", "artifacts/composition-lab/transfer-repaired.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "HIGH_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-012", "artifacts/creative-stack-validation/audio/waveform.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "HIGH_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-013", "artifacts/creative-stack-validation/video/contact-sheet.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "MID_KEY", "focal_region": "MULTIPLE", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-014", "artifacts/creative-stack-validation/video/thumbnail.png", {"ui_present": "NO", "render_type": "2D", "dominant_value": "MID_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-015", "artifacts/flagship/emberveil/turntable/turntable-000.png", {"ui_present": "NO", "render_type": "3D", "dominant_value": "LOW_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-016", "artifacts/flagship/emberveil/turntable/turntable-012.png", {"ui_present": "NO", "render_type": "3D", "dominant_value": "MID_KEY", "focal_region": "CENTER", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-017", "artifacts/flagship/emberveil-canonical/cinematic-frames/seq-0001.png", {"ui_present": "NO", "render_type": "3D", "dominant_value": "LOW_KEY", "focal_region": "CENTER_LEFT", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
    ("real-018", "artifacts/flagship/emberveil-canonical/cinematic-frames/seq-0030.png", {"ui_present": "NO", "render_type": "3D", "dominant_value": "MID_KEY", "focal_region": "CENTER_RIGHT", "visible_text": "NO", "major_clipping": "NO", "major_overlap": "NO"}),
]


def _png_dimensions(payload: bytes) -> tuple[int, int]:
    if payload[:8] != b"\x89PNG\r\n\x1a\n" or len(payload) < 24:
        raise ValueError("invalid PNG signature or header")
    return int.from_bytes(payload[16:20], "big"), int.from_bytes(payload[20:24], "big")


def build_v3_dataset() -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sample_id, relative_path, labels in REAL_SPECS:
        path = ROOT / relative_path
        payload = path.read_bytes()
        sha = hashlib.sha256(payload).hexdigest()
        if sha in seen:
            continue
        seen.add(sha)
        width, height = _png_dimensions(payload)
        full = dict(labels)
        full["orientation"] = "LANDSCAPE" if width > height else "PORTRAIT" if height > width else "SQUARE"
        samples.append({
            "sample_id": sample_id,
            "sha256": sha,
            "source_artifact": relative_path,
            "width": width,
            "height": height,
            "labels": full,
            "label_provenance": "CONTROLLED_OR_INDEPENDENTLY_ADJUDICATED_V3",
        })
    if len(samples) < 12:
        raise RuntimeError(f"real-image V3 dataset too small: {len(samples)}")
    dataset = {"schema_version": 3, "kind": "visual-grounding-v3-dataset", "sample_count": len(samples), "samples": samples}
    dataset["dataset_hash"] = hashlib.sha256(json.dumps(dataset, sort_keys=True).encode()).hexdigest()
    return dataset


def validate_prediction(prediction: Any) -> dict[str, str] | None:
    if not isinstance(prediction, dict):
        return None
    result: dict[str, str] = {}
    for key, allowed in ENUMS.items():
        value = prediction.get(key)
        if not isinstance(value, str) or value not in allowed:
            return None
        result[key] = value
    return result


def score_prediction(prediction: Any, labels: dict[str, str]) -> dict[str, Any]:
    normalized = validate_prediction(prediction)
    if normalized is None:
        return {"status": "INVALID_RESPONSE", "scored": 0, "matches": {}}
    matches = {key: normalized[key] == value for key, value in labels.items() if value != "NOT_APPLICABLE"}
    return {"status": "SCORED", "scored": len(matches), "correct": sum(matches.values()), "matches": matches}


def aggregate_status(attempted: int, successful: int, scored: int, *, min_successful: int = 5, rate_limited: int = 0, payment_required: int = 0, invalid_response: int = 0) -> str:
    if successful == 0 and payment_required:
        return "PAYMENT_REQUIRED"
    if successful == 0 and rate_limited:
        return "RATE_LIMITED"
    if successful == 0:
        return "PROVIDER_UNAVAILABLE"
    if successful < min_successful or scored == 0:
        return "INSUFFICIENT_SAMPLE"
    return "PASS"


def label_distributions(dataset: dict[str, Any]) -> dict[str, dict[str, int]]:
    properties = ("orientation", "ui_present", "render_type", "dominant_value", "focal_region", "visible_text", "major_clipping", "major_overlap")
    return {prop: dict(Counter(sample["labels"].get(prop, "NOT_APPLICABLE") for sample in dataset["samples"])) for prop in properties}


def trivial_baselines(dataset: dict[str, Any]) -> dict[str, Any]:
    distributions = label_distributions(dataset)
    return {prop: {"distribution": counts, "majority": max(counts, key=counts.get)} for prop, counts in distributions.items()}


def run_negative_tests() -> dict[str, Any]:
    cases = [
        ("all_402", aggregate_status(10, 0, 0, payment_required=10) == "PAYMENT_REQUIRED"),
        ("all_429", aggregate_status(10, 0, 0, rate_limited=10) == "RATE_LIMITED"),
        ("zero_samples", aggregate_status(0, 0, 0) == "PROVIDER_UNAVAILABLE"),
        ("below_minimum", aggregate_status(1, 1, 1) == "INSUFFICIENT_SAMPLE"),
        ("substring_rejected", score_prediction({"orientation": "LANDSCAPE or PORTRAIT"}, {"orientation": "LANDSCAPE"})["status"] == "INVALID_RESPONSE"),
    ]
    return {"passed": sum(ok for _, ok in cases), "total": len(cases), "cases": [{"name": name, "pass": ok} for name, ok in cases]}


def validate_dataset_balance(dataset: dict[str, Any]) -> dict[str, Any]:
    distributions = label_distributions(dataset)
    required_binary_properties = ("ui_present", "visible_text", "major_clipping", "major_overlap")
    missing_classes = {
        prop: sorted(set(("YES", "NO")) - set(distributions[prop]))
        for prop in required_binary_properties
        if not {"YES", "NO"}.issubset(distributions[prop])
    }
    return {
        "status": "PASS" if not missing_classes else "REJECTED_INSUFFICIENT_CLASS_BALANCE",
        "required_binary_properties": list(required_binary_properties),
        "missing_classes": missing_classes,
        "distributions": distributions,
    }


def persist_dataset_and_tests() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    dataset = build_v3_dataset()
    balance = validate_dataset_balance(dataset)
    (OUT / "visual-grounding-v3-dataset.json").write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    result = {
        "status": "DATASET_FROZEN",
        "dataset_hash": dataset["dataset_hash"],
        "sample_count": dataset["sample_count"],
        "label_distribution": label_distributions(dataset),
        "balance_gate": balance,
        "trivial_baselines": trivial_baselines(dataset),
        "model_quality_claim_allowed": balance["status"] == "PASS",
        "negative_tests": run_negative_tests(),
        "prior_v2_status": "INVALIDATED_BENCHMARK_CONSTANT_LABELS_AND_PERMISSIVE_SCORING",
    }
    (OUT / "visual-grounding-v3-preflight.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    # Evidence is persisted before presentation so console encoding cannot
    # invalidate a completed fixture/preflight run.
    result = persist_dataset_and_tests()
    print(json.dumps(result, indent=2, ensure_ascii=True))
