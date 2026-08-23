#!/usr/bin/env python3
"""Independent creative review through a different 9Router model family.

The reviewer receives the brief and evidence bundle, not the builder's success
summary. A screenshot is sent as multimodal evidence when the selected model
supports it; failures are recorded rather than converted into a pass.
"""
from __future__ import annotations

import base64
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "validate"))
from model_golden_tasks import chat, get_auth  # type: ignore


def main() -> int:
    model = "ag/gemini-3.7-flash-medium"
    image = ROOT / "artifacts/flagship/qa/runtime-canonical-final2/frame-03.png"
    report = json.loads((ROOT / "artifacts/flagship/emberveil-canonical/canonical-build-report.json").read_text(encoding="utf-8"))
    export = report["results"]["export"]["glb_validation"]
    evidence = {
        "artifact": "Emberveil — Warden of Dying Fires",
        "mission": "calibration instrument for creative production intelligence, not a finished commercial product",
        "structural": {k: export.get(k) for k in ["valid", "mesh_count", "material_count", "animation_count", "node_count"]},
        "render_evidence": ["960x540 Cycles preview", "24-frame turntable", "72-frame cinematic sequence", "H.264 turntable and cinematic encodes"],
        "runtime_observation": {"hero_loaded": True, "active_animation_count": 4, "ember_particles": 420, "console_errors": 0, "network_failures": 0},
        "perceptual_diagnostics": {"readability_gate": "PASS", "black_crush": "diagnostic pass", "limitation": "metrics do not prove artistic quality"},
        "known_risk": "procedurally authored lathed vessel and shrine; no texture images; no audio; no authored ignition performance; rig controls are not skinned",
    }
    prompt = f"""You are an independent senior art director and technical-art reviewer. Attack this calibration artifact; do not praise it by default and do not infer quality from structural pass statuses. Review the attached runtime screenshot plus this factual evidence bundle: {json.dumps(evidence, indent=2)}.

Return JSON with exactly these keys:
critical_blockers (array), professional_gaps (array), primitive_or_generic_elements (array), strongest_identity_signals (array), actionable_repairs (array), verdict (one of COHERENT, POLISHED, PRODUCTION, SIGNATURE), confidence (0..1), limitations (array).
Be specific about silhouette, material readability, lighting, composition, environment, motion, VFX, typography, and runtime cohesion. Reject false completion."""
    try:
        encoded = base64.b64encode(image.read_bytes()).decode("ascii")
        messages = [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + encoded}},
        ]}]
        base, token = get_auth()
        started = time.time()
        content, latency = chat(base, token, model, messages, max_tokens=1400, timeout=180)
        result = {"schema_version": 1, "model": model, "provider_family": "Gemini", "latency_s": latency,
                  "evidence_image": str(image), "prompt": prompt, "review": content, "ok": bool(content.strip()),
                  "independence": "separate reviewer prompt/model family; builder summary not supplied"}
    except Exception as exc:
        result = {"schema_version": 1, "model": model, "provider_family": "Gemini", "ok": False,
                  "failure_type": "review_model_or_multimodal_unavailable", "error": f"{type(exc).__name__}: {exc}",
                  "limitations": ["independent creative review could not be executed"]}
    out = ROOT / "artifacts/flagship/qa/independent-creative-review.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print("INDEPENDENT_REVIEW", "PASS" if result.get("ok") else "FAIL", result.get("model"), result.get("error", ""))
    if result.get("review"):
        print(result["review"][:3000])
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
