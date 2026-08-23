"""Unit tests for Gmail OAuth state validation and scope policy.

No network calls: ``oauth_state`` and URL building are pure with a temporary
client secret file.
"""

from __future__ import annotations

import json

import pytest

from growthos.integrations import gmail_oauth
from growthos.integrations.gmail_oauth import (
    GmailOAuthState,
    build_auth_url,
    has_client_secret,
    missing_scopes,
    oauth_state,
)


@pytest.fixture
def client_secret(tmp_path, monkeypatch):
    secret = {
        "installed": {
            "client_id": "fake-client-id.apps.googleusercontent.com",
            "client_secret": "fake-client-secret-value",
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"],
        }
    }
    target = tmp_path / "gmail-client-secret.json"
    target.write_text(json.dumps(secret), encoding="utf-8")
    monkeypatch.setattr(gmail_oauth, "client_secret_path", lambda: target)
    return target


def test_scopes_are_least_privilege() -> None:
    assert "https://www.googleapis.com/auth/gmail.readonly" in gmail_oauth.GMAIL_SCOPES
    assert "https://www.googleapis.com/auth/gmail.send" in gmail_oauth.GMAIL_SCOPES
    # Never request full mailbox or modify authority for v1.
    assert "https://mail.google.com/" not in gmail_oauth.GMAIL_SCOPES
    assert "gmail.modify" not in " ".join(gmail_oauth.GMAIL_SCOPES)


def test_auth_url_built_with_expected_params(client_secret) -> None:
    url = build_auth_url(
        client_id="fake-client-id.apps.googleusercontent.com",
        redirect_uri="http://127.0.0.1:54321/",
        state="state-abc",
    )
    assert "accounts.google.com/o/oauth2/v2/auth" in url
    assert "client_id=fake-client-id.apps.googleusercontent.com" in url
    assert "redirect_uri=" in url
    assert "127.0.0.1" in url and "54321" in url  # loopback redirect, no OOB
    assert "state=state-abc" in url
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "gmail.readonly" in url
    assert "gmail.send" in url
    assert "gmail.modify" not in url


def test_auth_url_never_uses_oob_redirect() -> None:
    url = build_auth_url(
        client_id="c", redirect_uri="http://127.0.0.1:4321/", state="s"
    )
    assert "urn:ietf:wg:oauth:2.0:oob" not in url


def test_oauth_state_transitions(client_secret, monkeypatch) -> None:
    # No client secret at all -> NOT_CONFIGURED
    monkeypatch.setattr(gmail_oauth, "client_secret_path", lambda: client_secret.parent / "missing.json")
    assert oauth_state(refresh_token=None, access_token=None, error=None) is GmailOAuthState.NOT_CONFIGURED

    # Restore secret: no tokens -> AUTHORIZATION_REQUIRED
    monkeypatch.setattr(gmail_oauth, "client_secret_path", lambda: client_secret)
    assert (
        oauth_state(refresh_token=None, access_token=None, error=None)
        is GmailOAuthState.AUTHORIZATION_REQUIRED
    )

    # Refresh token but no access token yet -> still authorization required
    assert (
        oauth_state(refresh_token="rt", access_token=None, error=None)
        is GmailOAuthState.AUTHORIZATION_REQUIRED
    )

    # Both tokens -> CONNECTED
    assert (
        oauth_state(refresh_token="rt", access_token="at", error=None)
        is GmailOAuthState.CONNECTED
    )

    # Refresh failures map to truthful states
    assert (
        oauth_state(refresh_token="rt", access_token="at", error="invalid_grant")
        is GmailOAuthState.TOKEN_EXPIRED
    )
    assert (
        oauth_state(refresh_token="rt", access_token="at", error="token has been revoked")
        is GmailOAuthState.TOKEN_EXPIRED
    )
    assert (
        oauth_state(refresh_token="rt", access_token="at", error="network down")
        is GmailOAuthState.ERROR
    )


def test_missing_scopes_reports_actual_gap() -> None:
    missing = missing_scopes(["https://www.googleapis.com/auth/gmail.send"])
    assert missing == ["https://www.googleapis.com/auth/gmail.readonly"]
    assert missing_scopes(gmail_oauth.GMAIL_SCOPES) == []


def test_has_client_secret(client_secret, monkeypatch) -> None:
    assert has_client_secret() is True
    monkeypatch.setattr(gmail_oauth, "client_secret_path", lambda: client_secret.parent / "nope.json")
    assert has_client_secret() is False
