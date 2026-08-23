"""Autonomy policy engine."""

from growthos.domain.enums import PermissionDecision
from growthos.security.permissions import AutonomyEngine


def test_research_is_auto():
    engine = AutonomyEngine()
    assert engine.evaluate("research").decision is PermissionDecision.ALLOW


def test_draft_email_is_auto():
    engine = AutonomyEngine()
    assert engine.evaluate("draft_email").decision is PermissionDecision.ALLOW


def test_send_email_requires_approval():
    engine = AutonomyEngine()
    result = engine.evaluate("send_prospect_email")
    assert result.decision is PermissionDecision.REQUIRE_APPROVAL


def test_sms_cannot_authorize_high_risk():
    engine = AutonomyEngine()
    result = engine.evaluate("financial_transfer", via_channel="sms")
    assert result.decision is PermissionDecision.DENY
    # The same action via dashboard is only approval-gated, not denied.
    web = engine.evaluate("financial_transfer", via_channel="web")
    assert web.decision is PermissionDecision.REQUIRE_APPROVAL


def test_unknown_action_denied():
    engine = AutonomyEngine()
    assert engine.evaluate("delete_all_data").decision is PermissionDecision.DENY


def test_scraping_bypass_denied():
    engine = AutonomyEngine()
    assert (
        engine.evaluate("bypass_robots_txt").decision is PermissionDecision.DENY
    )
    assert (
        engine.evaluate("auto_bulk_dm").decision is PermissionDecision.DENY
    )
