"""FREE_RUNTIME_POLICY cost guard."""

from growthos.security.cost_guard import CostGuard


def test_free_connectors_allowed():
    guard = CostGuard()
    assert guard.is_allowed("ollama")
    assert guard.is_allowed("postgresql")
    assert guard.is_allowed("gmail_api")


def test_billable_connectors_blocked():
    guard = CostGuard()
    assert not guard.is_allowed("twilio")
    assert not guard.is_allowed("sendgrid")


def test_unknown_connector_blocked():
    guard = CostGuard()
    assert not guard.is_allowed("some_unknown_paid_service")
