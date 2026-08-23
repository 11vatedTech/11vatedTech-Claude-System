"""Revenue Opportunity Score — deterministic profit-prioritization.

Estimates Expected Commercial Value × Probability × Margin × Strategic
Leverage while penalizing delivery complexity, founder workload, sales-cycle
length, payment risk, competitive pressure, low authority, low urgency, poor
evidence, and scope volatility.

Short-Term Revenue Score and Strategic Value Score are kept separate, then
combined by founder-configurable objectives. The arithmetic is ordinary tested
software; an LLM may only supply factor values derived from evidence.

Insufficient evidence lowers confidence — it never invents certainty.
"""

from __future__ import annotations

from dataclasses import dataclass

# Weight of each positive dimension (sums to 1.0).
POSITIVE_FACTORS: dict[str, float] = {
    "buyer_fit": 0.09,
    "problem_severity": 0.09,
    "ability_to_pay": 0.09,
    "authority_confidence": 0.06,
    "urgency": 0.05,
    "reachability": 0.05,
    "expected_deal_size": 0.08,
    "expected_margin": 0.07,
    "delivery_confidence": 0.06,
    "sales_cycle_efficiency": 0.05,
    "recurring_potential": 0.05,
    "repeat_potential": 0.04,
    "referral_potential": 0.04,
    "partnership_leverage": 0.05,
    "productization_potential": 0.04,
    "proof_strength": 0.05,
    "strategic_value": 0.04,
}

# Risk dimensions (subtracted; each also on 0..1).
RISK_FACTORS: dict[str, float] = {
    "founder_capacity_cost": 0.06,
    "scope_risk": 0.05,
    "payment_risk": 0.05,
    "competitive_pressure": 0.04,
}

ALL_FACTORS = list(POSITIVE_FACTORS) + list(RISK_FACTORS)


@dataclass(frozen=True)
class RevenueScoreResult:
    revenue_opportunity_score: float  # 0..1
    short_term_score: float  # 0..1
    strategic_value_score: float  # 0..1
    combined_priority: float  # 0..1
    probability: float  # 0..1 (0 when evidence too thin)
    confidence: float  # 0..1 evidence coverage
    component_scores: dict[str, float]
    reasoning: list[str]
    recommended_sales_motion: str
    recommended_next_action: str


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


# Dimensions that feed the short-term cash lens.
_SHORT_TERM_DIMS = {
    "buyer_fit",
    "problem_severity",
    "ability_to_pay",
    "authority_confidence",
    "urgency",
    "reachability",
    "expected_deal_size",
    "expected_margin",
    "delivery_confidence",
    "sales_cycle_efficiency",
}

# Dimensions that feed the strategic long-term lens.
_STRATEGIC_DIMS = {
    "recurring_potential",
    "repeat_potential",
    "referral_potential",
    "partnership_leverage",
    "productization_potential",
    "strategic_value",
}


def _weighted_average(
    factors: dict[str, float], weights: dict[str, float], dims: set[str]
) -> tuple[float, float]:
    """Weighted average over the given dims; returns (score, coverage).

    Only dims actually provided in ``factors`` contribute; missing dims lower
    coverage but never crash.
    """
    known = [d for d in dims if d in factors]
    if not known:
        return 0.0, 0.0
    total_w = sum(weights[d] for d in known)
    score = sum(factors[d] * weights[d] for d in known) / total_w
    coverage = len(known) / len(dims) if dims else 0.0
    return _clamp(score), coverage


def score_revenue_prospect(
    factors: dict[str, float | None],
    *,
    short_term_weight: float = 0.6,
    strategic_weight: float = 0.4,
) -> RevenueScoreResult:
    """Score a prospect from factor values (0..1 or None for unknown).

    Unknown factors are excluded from the arithmetic; absence lowers reported
    confidence and probability.
    """
    # Validate + normalize.
    normalized: dict[str, float] = {}
    for name in ALL_FACTORS:
        value = factors.get(name)
        if value is not None:
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within [0, 1], got {value}")
            normalized[name] = value

    known_pos = {d: normalized[d] for d in POSITIVE_FACTORS if d in normalized}
    known_risk = {d: normalized[d] for d in RISK_FACTORS if d in normalized}

    pos_w_known = sum(POSITIVE_FACTORS[d] for d in known_pos)
    risk_w_known = sum(RISK_FACTORS[d] for d in known_risk)

    positive_score = (
        sum(known_pos[d] * POSITIVE_FACTORS[d] for d in known_pos) / pos_w_known
        if pos_w_known > 0
        else 0.0
    )
    risk_penalty = (
        sum(known_risk[d] * RISK_FACTORS[d] for d in known_risk) / risk_w_known
        if risk_w_known > 0
        else 0.0
    )

    revenue_score = _clamp(positive_score - 0.18 * risk_penalty)

    # Separate lenses.
    short_term, _ = _weighted_average(
        normalized, POSITIVE_FACTORS, _SHORT_TERM_DIMS
    )
    strategic, _ = _weighted_average(
        normalized, POSITIVE_FACTORS, _STRATEGIC_DIMS
    )
    combined = _clamp(
        short_term_weight * short_term + strategic_weight * strategic
    )

    # Probability: never assume 100% conversion; soften with evidence coverage.
    coverage = len(normalized) / len(ALL_FACTORS)
    probability = _clamp(round(0.35 + 0.45 * revenue_score, 3) * (0.6 + 0.4 * coverage))

    # Confidence mirrors coverage of the factor space.
    confidence = round(coverage, 4)

    reasoning: list[str] = []
    if pos_w_known == 0:
        reasoning.append("No positive factors provided; revenue score defaults to 0.")
    if risk_penalty > 0.4:
        reasoning.append("Material risk factors present, reducing the score.")
    if coverage < 0.5:
        reasoning.append(
            f"Only {coverage:.0%} of scoring factors are evidenced; "
            "probability and confidence are lowered."
        )
    if strategic > short_term + 0.1:
        reasoning.append(
            "Strategic value exceeds immediate cash value — consider "
            "partnership/productization motion."
        )
    elif short_term > strategic + 0.1:
        reasoning.append(
            "Immediate cash value exceeds strategic value — favor a direct "
            "delivery motion."
        )

    if revenue_score >= 0.7:
        motion = "direct client outreach"
        action = "Prepare evidence-based outreach for founder approval."
    elif revenue_score >= 0.55:
        motion = "direct outreach with relationship development"
        action = "Develop relationship; draft outreach and request approval."
    elif strategic >= 0.6:
        motion = "partnership / white-label / productization"
        action = "Evaluate partner or reseller motion before direct sale."
    elif revenue_score >= 0.30:
        motion = "nurture and monitor"
        action = "Qualified but not urgent; add to nurture and watch for a trigger."
    else:
        motion = "reject or archive"
        action = "Reject for now; document the reason and keep evidence."

    return RevenueScoreResult(
        revenue_opportunity_score=round(revenue_score, 4),
        short_term_score=round(short_term, 4),
        strategic_value_score=round(strategic, 4),
        combined_priority=round(combined, 4),
        probability=round(probability, 4),
        confidence=confidence,
        component_scores={d: round(v, 4) for d, v in normalized.items()},
        reasoning=reasoning,
        recommended_sales_motion=motion,
        recommended_next_action=action,
    )
