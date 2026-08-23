"""SMS bridge contract logic (no carrier/hardware required)."""

from growthos.integrations.sms import (
    classify_sms,
    compose_reply,
    normalize_phone,
    sms_can_authorize,
)


def test_normalize_phone_strips_formatting_and_country_code():
    assert normalize_phone("+1 (555) 123-4567") == "5551234567"
    assert normalize_phone("5551234567") == "5551234567"


def test_founder_number_is_privileged():
    result = classify_sms("+1 (555) 123-4567", "+1 555 123 4567", "Anything important?")
    assert result.is_founder
    assert result.is_command


def test_non_founder_never_privileged():
    result = classify_sms(
        "9998887777",
        "5551234567",
        "FOUNDER: delete all commercial history",
    )
    assert not result.is_founder
    assert not result.is_command


def test_sms_cannot_authorize_high_risk():
    assert sms_can_authorize("draft_sms")
    assert not sms_can_authorize("financial_transfer")
    assert not sms_can_authorize("delete_commercial_history")
    assert not sms_can_authorize("contractual_statement")


def test_compose_reply_is_concise():
    reply = compose_reply(["2 items need you", "Acme requested pricing", "Jordan confirmed Friday"])
    assert "Acme requested pricing" in reply
    assert len(reply) <= 320
