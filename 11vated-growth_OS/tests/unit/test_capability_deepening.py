
from growthos.intelligence.capability_deepening import (
    capability_review,
    sanitize_commercial_text,
)


def test_runtime_confidence_ceiling_without_runtime_evidence():
    review = capability_review("Interactive Sprite System Prototyping", {"runtime_status": "STATIC_ONLY", "sprite_system_terms": ["sprite", "runtime"], "evidence_counts": {"DIRECT_IMPLEMENTATION": 10}, "reproducibility": "UNKNOWN", "evidence_samples": {}, "contradictions": [], "missing": []})
    assert review["runtime_confidence"] < 0.5
    assert review["recommended_maturity"] == "EXPERIMENTAL"


def test_frontend_project_ui_is_not_general_capability():
    review = capability_review("Interactive Frontend Development", {"runtime_status": "STATIC_ONLY", "frontend_terms": ["typescript", "component"], "evidence_counts": {}, "reproducibility": "UNKNOWN", "evidence_samples": {}, "contradictions": [], "missing": []})
    assert review["recommended_decision"] == "REJECT"
    assert "project UI" in review["recommendation_reason"]


def test_commercial_sanitizer_removes_private_values():
    text = r"Built at C:\private\repo with token=do-not-share and https://user:password@example.com"
    clean = sanitize_commercial_text(text)
    assert "C:\\private" not in clean
    assert "do-not-share" not in clean
    assert "user:password" not in clean
