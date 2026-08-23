"""Unit tests for the deterministic Revenue Opportunity Score engine."""

from __future__ import annotations

import pytest

from growthos.intelligence.revenue_scoring import (
    ALL_FACTORS,
    score_revenue_prospect,
)


def _full_factors(**overrides) -> dict[str, float | None]:
    factors = {name: 0.5 for name in ALL_FACTORS}
    factors.update(overrides)
    return factors


def test_strong_prospect_scores_high_and_high_confidence() -> None:
    result = score_revenue_prospect(
        _full_factors(
            buyer_fit=0.9,
            problem_severity=0.9,
            ability_to_pay=0.9,
            expected_deal_size=0.9,
            expected_margin=0.8,
            scope_risk=0.1,
            payment_risk=0.1,
            founder_capacity_cost=0.2,
        )
    )
    assert result.revenue_opportunity_score >= 0.6
    assert result.confidence == 1.0
    assert result.probability <= 0.85  # never 100% conversion


def test_weak_prospect_scores_low_and_recommends_reject() -> None:
    result = score_revenue_prospect(
        _full_factors(
            buyer_fit=0.1,
            problem_severity=0.1,
            ability_to_pay=0.1,
            urgency=0.1,
            scope_risk=0.9,
            payment_risk=0.9,
        )
    )
    assert result.revenue_opportunity_score < 0.4
    assert "reject" in result.recommended_sales_motion


def test_missing_evidence_lowers_confidence_and_probability() -> None:
    factors = {name: None for name in ALL_FACTORS}
    factors["buyer_fit"] = 0.8
    factors["problem_severity"] = 0.8
    result = score_revenue_prospect(factors)
    assert result.confidence < 0.5
    assert result.probability < 0.5
    assert any("evidence" in r for r in result.reasoning)


def test_short_term_vs_strategic_lenses_are_separate() -> None:
    cash_heavy = score_revenue_prospect(
        _full_factors(
            expected_deal_size=0.95,
            expected_margin=0.9,
            urgency=0.9,
            recurring_potential=0.1,
            partnership_leverage=0.1,
        )
    )
    strategic_heavy = score_revenue_prospect(
        _full_factors(
            recurring_potential=0.95,
            partnership_leverage=0.95,
            productization_potential=0.95,
            strategic_value=0.95,
            expected_deal_size=0.3,
        )
    )
    # The strategic lens is separate from the short-term cash lens.
    assert strategic_heavy.strategic_value_score > cash_heavy.strategic_value_score
    assert cash_heavy.short_term_score > strategic_heavy.short_term_score


def test_out_of_range_value_rejected() -> None:
    with pytest.raises(ValueError):
        score_revenue_prospect({"buyer_fit": 1.5})


def test_empty_factors_returns_zero_with_low_confidence() -> None:
    result = score_revenue_prospect({})
    assert result.revenue_opportunity_score == 0.0
    assert result.confidence == 0.0
