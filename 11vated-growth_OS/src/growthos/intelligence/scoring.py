"""Deterministic opportunity scoring.

Scoring is ordinary tested software. Insufficient evidence lowers confidence;
it never increases imaginary certainty. An LLM may supply factor *values*
derived from evidence, but the arithmetic and classification are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

from growthos.domain.enums import OpportunityClassification

# Positive factors and their weights (sum to 1.0).
POSITIVE_FACTORS: dict[str, float] = {
    "need_severity": 0.15,
    "customer_fit": 0.12,
    "buyer_authority": 0.10,
    "ability_to_pay": 0.10,
    "urgency": 0.08,
    "reachability": 0.06,
    "delivery_confidence": 0.08,
    "potential_margin": 0.08,
    "strategic_value": 0.06,
    "repeat_potential": 0.05,
    "referral_potential": 0.04,
    "relationship_leverage": 0.08,
}

RISK_FACTORS: dict[str, float] = {
    "scope_risk": 0.05,
    "payment_risk": 0.05,
    "competitive_pressure": 0.05,
}

ALL_FACTORS = list(POSITIVE_FACTORS) + list(RISK_FACTORS)


@dataclass(frozen=True)
class ScoreResult:
    overall_score: float
    confidence: float
    classification: OpportunityClassification
    reasoning: list[str]
    recommended_next_action: str


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def classify(overall_score: float) -> OpportunityClassification:
    if overall_score >= 0.75:
        return OpportunityClassification.PURSUE_NOW
    if overall_score >= 0.60:
        return OpportunityClassification.DEVELOP_RELATIONSHIP
    if overall_score >= 0.45:
        return OpportunityClassification.NURTURE
    if overall_score >= 0.30:
        return OpportunityClassification.MONITOR
    return OpportunityClassification.REJECT


def score_opportunity(factors: dict[str, float | None]) -> ScoreResult:
    """Score an opportunity from factor values (0..1 or None for unknown).

    Unknown factors are excluded from the arithmetic; their absence lowers the
    reported confidence.
    """
    known_positive: dict[str, float] = {}
    for name, weight in POSITIVE_FACTORS.items():
        value = factors.get(name)
        if value is not None:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0, 1]")
            known_positive[name] = weight * value

    known_risk: dict[str, float] = {}
    for name, weight in RISK_FACTORS.items():
        value = factors.get(name)
        if value is not None:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0, 1]")
            known_risk[name] = weight * value

    # Renormalize the weights over the factors that were actually provided.
    positive_weight_known = sum(POSITIVE_FACTORS[k] for k in known_positive)
    risk_weight_known = sum(RISK_FACTORS[k] for k in known_risk)

    positive_score = (
        sum(known_positive.values()) / positive_weight_known
        if positive_weight_known > 0
        else 0.0
    )
    risk_penalty = (
        sum(known_risk.values()) / risk_weight_known
        if risk_weight_known > 0
        else 0.0
    )

    overall = _clamp(positive_score - 0.15 * risk_penalty)
    classification = classify(overall)

    # Confidence reflects evidence coverage of the factor space.
    coverage = sum(
        1 for name in ALL_FACTORS if factors.get(name) is not None
    ) / len(ALL_FACTORS)

    # If a lot is unknown, soften aggressive classifications.
    if coverage < 0.5 and classification in {
        OpportunityClassification.PURSUE_NOW,
        OpportunityClassification.DEVELOP_RELATIONSHIP,
    }:
        classification = OpportunityClassification.NURTURE

    reasoning: list[str] = []
    if positive_weight_known == 0:
        reasoning.append("No positive factors provided; score defaults to 0.")
    if risk_penalty > 0.4:
        reasoning.append("Material risk factors present, reducing score.")
    if coverage < 0.5:
        reasoning.append(
            f"Only {coverage:.0%} of scoring factors are evidenced; "
            "confidence lowered."
        )

    next_action = {
        OpportunityClassification.PURSUE_NOW: "Prepare and send approved outreach.",
        OpportunityClassification.DEVELOP_RELATIONSHIP: (
            "Develop the relationship before commercial outreach."
        ),
        OpportunityClassification.NURTURE: "Add to nurture cadence and monitor.",
        OpportunityClassification.MONITOR: "Monitor for a trigger event.",
        OpportunityClassification.REJECT: "Do not pursue; document rejection reason.",
    }[classification]

    return ScoreResult(
        overall_score=round(overall, 4),
        confidence=round(coverage, 4),
        classification=classification,
        reasoning=reasoning,
        recommended_next_action=next_action,
    )
