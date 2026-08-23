"""Deterministic opportunity scoring."""

import pytest

from growthos.domain.enums import OpportunityClassification
from growthos.intelligence.scoring import score_opportunity


def test_strong_well_evidenced_opportunity_is_pursue_now():
    factors = {
        "need_severity": 0.9,
        "customer_fit": 0.9,
        "buyer_authority": 0.9,
        "ability_to_pay": 0.8,
        "urgency": 0.8,
        "reachability": 0.9,
        "delivery_confidence": 0.9,
        "potential_margin": 0.8,
        "strategic_value": 0.8,
        "repeat_potential": 0.7,
        "referral_potential": 0.7,
        "relationship_leverage": 0.7,
        "scope_risk": 0.1,
        "payment_risk": 0.1,
        "competitive_pressure": 0.2,
    }
    result = score_opportunity(factors)
    assert result.classification is OpportunityClassification.PURSUE_NOW
    assert result.confidence == 1.0
    assert result.overall_score > 0.75


def test_insufficient_evidence_lowers_confidence_and_softens():
    result = score_opportunity({"need_severity": 0.9, "customer_fit": 0.8})
    assert result.confidence < 0.5
    # High need/fit alone must not produce an aggressive classification.
    assert result.classification in {
        OpportunityClassification.NURTURE,
        OpportunityClassification.MONITOR,
    }


def test_empty_factors_score_zero():
    result = score_opportunity({})
    assert result.overall_score == 0.0
    assert result.classification is OpportunityClassification.REJECT
    assert result.confidence == 0.0


def test_high_risk_reduces_score():
    low_risk = score_opportunity(
        {
            "need_severity": 0.9,
            "customer_fit": 0.9,
            "buyer_authority": 0.9,
            "ability_to_pay": 0.9,
            "urgency": 0.9,
            "reachability": 0.9,
            "delivery_confidence": 0.9,
            "potential_margin": 0.9,
            "strategic_value": 0.9,
            "repeat_potential": 0.9,
            "referral_potential": 0.9,
            "relationship_leverage": 0.9,
            "scope_risk": 0.0,
            "payment_risk": 0.0,
            "competitive_pressure": 0.0,
        }
    )
    high_risk = score_opportunity(
        {
            "need_severity": 0.9,
            "customer_fit": 0.9,
            "buyer_authority": 0.9,
            "ability_to_pay": 0.9,
            "urgency": 0.9,
            "reachability": 0.9,
            "delivery_confidence": 0.9,
            "potential_margin": 0.9,
            "strategic_value": 0.9,
            "repeat_potential": 0.9,
            "referral_potential": 0.9,
            "relationship_leverage": 0.9,
            "scope_risk": 0.9,
            "payment_risk": 0.9,
            "competitive_pressure": 0.9,
        }
    )
    assert high_risk.overall_score < low_risk.overall_score


def test_factor_out_of_range_rejected():
    with pytest.raises(ValueError):
        score_opportunity({"need_severity": 1.5})
