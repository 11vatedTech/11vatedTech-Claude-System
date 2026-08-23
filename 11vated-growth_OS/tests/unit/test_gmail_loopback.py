"""Automated tests for the Desktop App loopback OAuth flow.

Covers: state mismatch rejection, missing authorization code, OAuth error
callback, callback timeout, occupied-port fallback, token exchange failure,
successful loopback callback, credential persistence, and no token leakage
into logs. No network beyond loopback; the Google exchange is faked.
"""

from __future__ import annotations

import asyncio
import json
import logging
import socket
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from growthos.integrations import gmail_oauth
from growthos.integrations.gmail_oauth import (
    CallbackTimeoutError,
    OAuthCallbackError,
    StateMismatchError,
    perform_loopback_flow,
)


@pytest.fixture
def client_secret(tmp_path, monkeypatch):
    secret = {
        "installed": {
            "client_id": "fake-client-id.apps.googleusercontent.com",
            "client_secret": "fake-client-secret-value",
            "redirect_uris": ["http://127.0.0.1"],
        }
    }
    target = tmp_path / "gmail-client-secret.json"
    target.write_text(json.dumps(secret), encoding="utf-8")
    monkeypatch.setattr(gmail_oauth, "client_secret_path", lambda: target)
    return secret


async def _run_flow(opened: dict, *, exchange=None, store=None, store_access=None, timeout=10):
    return await perform_loopback_flow(
        timeout=timeout,
        open_browser=lambda url: opened.setdefault("url", url),
        exchange=exchange,
        store=store or (lambda rt: None),
        store_access=store_access or (lambda at: None),
    )


def _state_from_url(url: str) -> str:
    return parse_qs(urlparse(url).query)["state"][0]


def _port_from_url(url: str) -> int:
    """The loopback port lives inside the redirect_uri query parameter."""
    params = parse_qs(urlparse(url).query)
    redirect = params["redirect_uri"][0]
    return urlparse(redirect).port


async def _hit_callback(port: int, params: dict[str, str]) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        return await client.get(f"http://127.0.0.1:{port}/", params=params)


async def test_successful_loopback_callback(client_secret) -> None:
    opened: dict = {}
    captured: dict = {}

    async def fake_exchange(code, redirect_uri):
        captured["code"] = code
        captured["redirect_uri"] = redirect_uri
        return {"refresh_token": "rt-ok", "access_token": "at-ok"}

    task = asyncio.create_task(_run_flow(opened, exchange=fake_exchange))
    await asyncio.sleep(0.3)
    url = opened["url"]
    state = _state_from_url(url)
    port = _port_from_url(url)
    resp = await _hit_callback(port, {"state": state, "code": "AUTH-CODE-1"})
    assert resp.status_code == 200

    tokens = await asyncio.wait_for(task, timeout=10)
    assert tokens["refresh_token"] == "rt-ok"
    assert captured["code"] == "AUTH-CODE-1"
    # Loopback redirect was used with the actual bound port.
    assert captured["redirect_uri"] == f"http://127.0.0.1:{port}/"


async def test_state_mismatch_is_rejected(client_secret) -> None:
    opened: dict = {}
    task = asyncio.create_task(_run_flow(opened))
    await asyncio.sleep(0.3)
    port = _port_from_url(opened["url"])
    await _hit_callback(port, {"state": "wrong-state", "code": "AUTH-CODE"})
    with pytest.raises(StateMismatchError):
        await asyncio.wait_for(task, timeout=10)


async def test_missing_authorization_code(client_secret) -> None:
    opened: dict = {}
    task = asyncio.create_task(_run_flow(opened))
    await asyncio.sleep(0.3)
    port = _port_from_url(opened["url"])
    state = _state_from_url(opened["url"])
    await _hit_callback(port, {"state": state})
    with pytest.raises(OAuthCallbackError):
        await asyncio.wait_for(task, timeout=10)


async def test_oauth_error_callback(client_secret) -> None:
    opened: dict = {}
    task = asyncio.create_task(_run_flow(opened))
    await asyncio.sleep(0.3)
    port = _port_from_url(opened["url"])
    state = _state_from_url(opened["url"])
    await _hit_callback(port, {"state": state, "error": "access_denied"})
    with pytest.raises(OAuthCallbackError, match="access_denied"):
        await asyncio.wait_for(task, timeout=10)


async def test_callback_timeout(client_secret) -> None:
    opened: dict = {}
    with pytest.raises(CallbackTimeoutError):
        await _run_flow(opened, timeout=0.3)


def _occupied_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    # Keep it bound (do not close) so the port is genuinely occupied.
    return port, sock


async def test_occupied_port_falls_back_to_ephemeral(client_secret) -> None:
    port, sock = _occupied_port()
    try:
        opened: dict = {}
        async def fake_exchange(code, redirect_uri):
            return {"refresh_token": "rt", "access_token": "at"}

        task = asyncio.create_task(
            perform_loopback_flow(
                timeout=10,
                open_browser=lambda url: opened.setdefault("url", url),
                exchange=fake_exchange,
                store=lambda rt: None,
                store_access=lambda at: None,
                port=port,
            )
        )
        await asyncio.sleep(0.3)
        bound = _port_from_url(opened["url"])
        assert bound != port  # fell back to a different ephemeral port
        state = _state_from_url(opened["url"])
        await _hit_callback(bound, {"state": state, "code": "CODE"})
        tokens = await asyncio.wait_for(task, timeout=10)
        assert tokens["refresh_token"] == "rt"
    finally:
        sock.close()


async def test_token_exchange_failure(client_secret) -> None:
    opened: dict = {}

    async def failing_exchange(code, redirect_uri):
        raise gmail_oauth.GmailSetupError("Token exchange failed: HTTP 400")

    task = asyncio.create_task(_run_flow(opened, exchange=failing_exchange))
    await asyncio.sleep(0.3)
    port = _port_from_url(opened["url"])
    state = _state_from_url(opened["url"])
    await _hit_callback(port, {"state": state, "code": "CODE"})
    with pytest.raises(gmail_oauth.GmailSetupError, match="Token exchange failed"):
        await asyncio.wait_for(task, timeout=10)


async def test_credential_persistence(client_secret) -> None:
    stored: dict = {}
    opened: dict = {}

    class FakeStore:
        def set(self, key, value):
            stored[key] = value

        def get(self, key):
            return stored.get(key)

        def delete(self, key):
            stored.pop(key, None)

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(gmail_oauth, "get_secret_store", lambda: FakeStore())

    async def fake_exchange(code, redirect_uri):
        return {"refresh_token": "rt-persist", "access_token": "at-persist"}

    # Use the DEFAULT store functions so the flow persists via
    # get_secret_store() -> FakeStore.
    task = asyncio.create_task(
        perform_loopback_flow(
            timeout=10,
            open_browser=lambda url: opened.setdefault("url", url),
            exchange=fake_exchange,
        )
    )
    await asyncio.sleep(0.3)
    port = _port_from_url(opened["url"])
    state = _state_from_url(opened["url"])
    await _hit_callback(port, {"state": state, "code": "CODE"})
    await asyncio.wait_for(task, timeout=10)
    monkeypatch.undo()

    # Refresh token persists and is readable back; never echoed.
    assert stored.get("gmail.refresh_token") == "rt-persist"
    assert stored.get("gmail.access_token") == "at-persist"


async def test_no_token_leakage_into_logs(client_secret, caplog) -> None:
    opened: dict = {}
    caplog.set_level(logging.DEBUG)
    logging.getLogger("http.server").setLevel(logging.DEBUG)
    # The test's own httpx client would log its request URL at DEBUG; that is
    # test noise, not the flow. Silence it so the invariant under test is the
    # flow's own logs (the callback server never logs query strings).
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    async def fake_exchange(code, redirect_uri):
        return {"refresh_token": "SECRET-REFRESH-TOKEN-XYZ", "access_token": "SECRET-ACCESS-TOKEN-XYZ"}

    task = asyncio.create_task(_run_flow(opened, exchange=fake_exchange))
    await asyncio.sleep(0.3)
    port = _port_from_url(opened["url"])
    state = _state_from_url(opened["url"])
    await _hit_callback(port, {"state": state, "code": "AUTH-CODE-LEAK-CHECK"})
    await asyncio.wait_for(task, timeout=10)

    log_text = caplog.text
    assert "AUTH-CODE-LEAK-CHECK" not in log_text
    assert "SECRET-REFRESH-TOKEN-XYZ" not in log_text
    assert "SECRET-ACCESS-TOKEN-XYZ" not in log_text
