"""Gmail OAuth 2.0 (official Google APIs only, Desktop App loopback flow).

The deprecated out-of-band (OOB) copy-paste flow is NOT used. Instead:

    growthos setup gmail
    -> validate client credential file
    -> bind a temporary callback listener to 127.0.0.1 on an ephemeral port
    -> build the authorization URL with that loopback redirect URI + state
    -> open the founder's default browser
    -> founder authenticates with Google
    -> Google redirects to the local callback
    -> validate OAuth state (mismatch is rejected, never exchanged)
    -> capture the authorization code automatically
    -> exchange the code server-side
    -> store refresh/access credentials in the OS keychain (never the repo)
    -> close the temporary callback server
    -> verify the connected identity through the real Gmail API

The callback listener binds loopback (127.0.0.1) only and is never exposed
beyond localhost. Query strings (which carry the code) are never logged.

OAuth status truth states (never fabricate a healthy connection):

    NOT_CONFIGURED        no client secret imported
    AUTHORIZATION_REQUIRED client secret present, no refresh token yet
    CONNECTED             refresh token present and profile verified
    TOKEN_EXPIRED         refresh failed (e.g. 401 invalid_grant)
    TOKEN_REVOKED         token was explicitly revoked
    SCOPE_INSUFFICIENT    granted scopes miss required ones
    ERROR                 any other failure
"""

from __future__ import annotations

import asyncio
import json
import secrets
import threading
import webbrowser
from collections.abc import Callable
from datetime import UTC, datetime
from enum import StrEnum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from growthos.security.secrets import get_secret_store

# Least privilege. Deliberately NOT requesting gmail.modify or mail.google.com.
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

KEY_REFRESH = "gmail.refresh_token"
KEY_ACCESS = "gmail.access_token"

DEFAULT_CALLBACK_TIMEOUT_SECONDS = 180


class GmailOAuthState(StrEnum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    CONNECTED = "CONNECTED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    SCOPE_INSUFFICIENT = "SCOPE_INSUFFICIENT"
    ERROR = "ERROR"


class GmailSetupError(RuntimeError):
    """Raised when the Gmail OAuth setup prerequisites are missing."""


class OAuthCallbackError(RuntimeError):
    """Raised when the loopback callback fails (missing code, OAuth error)."""


class StateMismatchError(RuntimeError):
    """Raised when the callback state does not match the issued state."""


class CallbackTimeoutError(RuntimeError):
    """Raised when no callback arrives within the timeout window."""


def client_secret_path() -> Path:
    return Path(".secrets") / "gmail-client-secret.json"


def load_client_secret() -> dict[str, Any]:
    """Load the OAuth client secret JSON (gitignored). Raises if missing."""
    path = client_secret_path()
    if not path.is_file():
        raise GmailSetupError(
            "Gmail client secret missing. Place it at "
            ".secrets/gmail-client-secret.json (gitignored)."
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GmailSetupError("Gmail client secret file is unreadable/invalid.") from exc
    try:
        return data["installed"]
    except KeyError:
        try:
            return data["web"]
        except KeyError as exc:
            raise GmailSetupError(
                "Client secret JSON must contain an 'installed' or 'web' key."
            ) from exc


def build_auth_url(
    *, client_id: str, redirect_uri: str, state: str
) -> str:
    """Build the Google consent URL for the founder's browser."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str, *, redirect_uri: str) -> dict[str, Any]:
    """Exchange an authorization code for tokens. Returns Google's response."""
    secret = load_client_secret()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": secret["client_id"],
                "client_secret": secret["client_secret"],
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if resp.status_code != 200:
            raise GmailSetupError(f"Token exchange failed: HTTP {resp.status_code}")
        return resp.json()


async def refresh_access_token(refresh_token: str) -> str:
    """Exchange a refresh token for a fresh access token."""
    secret = load_client_secret()
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "refresh_token": refresh_token,
                "client_id": secret["client_id"],
                "client_secret": secret["client_secret"],
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code != 200:
            raise GmailSetupError(f"Token refresh failed: HTTP {resp.status_code}")
        return str(resp.json()["access_token"])


async def revoke_token(token: str) -> None:
    """Revoke a token with Google (best effort; 400 means already revoked)."""
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(GOOGLE_REVOKE_URL, data={"token": token})


def store_refresh_token(refresh_token: str) -> None:
    get_secret_store().set(KEY_REFRESH, refresh_token)


def load_refresh_token() -> str | None:
    return get_secret_store().get(KEY_REFRESH)


def store_access_token(access_token: str) -> None:
    get_secret_store().set(KEY_ACCESS, access_token)


def load_access_token() -> str | None:
    return get_secret_store().get(KEY_ACCESS)


def clear_credentials() -> None:
    store = get_secret_store()
    store.delete(KEY_REFRESH)
    store.delete(KEY_ACCESS)


def has_client_secret() -> bool:
    return client_secret_path().is_file()


def oauth_state(*, refresh_token: str | None, access_token: str | None, error: str | None) -> GmailOAuthState:
    """Derive the truthful OAuth state from what actually exists."""
    if not has_client_secret():
        return GmailOAuthState.NOT_CONFIGURED
    if not refresh_token:
        return GmailOAuthState.AUTHORIZATION_REQUIRED
    if error:
        lowered = error.lower()
        if "invalid_grant" in lowered or "revoked" in lowered or "token_expired" in lowered:
            return GmailOAuthState.TOKEN_EXPIRED
        return GmailOAuthState.ERROR
    if not access_token:
        # Refresh token exists but we have no proof of a live connection yet.
        return GmailOAuthState.AUTHORIZATION_REQUIRED
    return GmailOAuthState.CONNECTED


def missing_scopes(granted: list[str]) -> list[str]:
    return [s for s in GMAIL_SCOPES if s not in granted]


def utcnow() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# Desktop App loopback flow
# ---------------------------------------------------------------------------


def _make_callback_handler(state: str, result: dict[str, str]) -> type[BaseHTTPRequestHandler]:
    """Build a loopback request handler that validates state and captures code."""

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server API)
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            def finish_with(status: int, message: str, *, error: str | None = None) -> None:
                if error is not None:
                    result["error"] = error
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(message.encode("utf-8"))
                # Stop serving; the flow's wait loop observes the result.
                self.server.shutdown()  # type: ignore[attr-defined]

            received_state = (params.get("state") or [""])[0]
            if received_state != state:
                finish_with(400, "State mismatch; authorization rejected.", error="state_mismatch")
                return

            if "error" in params:
                oauth_error = params["error"][0]
                finish_with(400, f"Authorization failed: {oauth_error}", error=f"oauth_error:{oauth_error}")
                return

            codes = params.get("code")
            if not codes:
                finish_with(400, "Missing authorization code.", error="missing_code")
                return

            result["code"] = codes[0]
            finish_with(200, "Authorization complete. You may close this window.")

        def log_message(self, format: str, *args: Any) -> None:
            # Never log request lines: the query string carries the code.
            return

    return CallbackHandler


def _bind_loopback(
    port: int, handler_factory: Callable[[], type[BaseHTTPRequestHandler]]
) -> ThreadingHTTPServer:
    """Bind the callback listener to 127.0.0.1 (never beyond localhost)."""
    return ThreadingHTTPServer(("127.0.0.1", port), handler_factory())


async def _wait_for_result(result: dict[str, str], timeout: float) -> None:
    deadline = asyncio.get_running_loop().time() + timeout
    while not result:
        if asyncio.get_running_loop().time() >= deadline:
            raise CallbackTimeoutError(
                "No OAuth callback received within "
                f"{timeout:.0f}s. Retry and complete the consent screen."
            )
        await asyncio.sleep(0.05)


async def perform_loopback_flow(
    client_secret: dict[str, Any] | None = None,
    *,
    timeout: float = DEFAULT_CALLBACK_TIMEOUT_SECONDS,
    open_browser: Callable[[str], Any] = webbrowser.open,
    on_auth_url: Callable[[str], Any] | None = None,
    exchange: Callable[..., Any] | None = None,
    store: Callable[[str], None] = store_refresh_token,
    store_access: Callable[[str], None] = store_access_token,
    port: int = 0,
) -> dict[str, Any]:
    """Run the full Desktop App loopback OAuth flow. Returns Google's tokens.

    Failure modes raise: ``StateMismatchError``, ``OAuthCallbackError``,
    ``CallbackTimeoutError``, ``GmailSetupError`` (exchange failure).
    """
    secret = client_secret or load_client_secret()
    exchange = exchange or exchange_code
    state = secrets.token_urlsafe(16)
    result: dict[str, str] = {}

    try:
        server = _bind_loopback(port, lambda: _make_callback_handler(state, result))
    except OSError:
        if port == 0:
            raise
        # Occupied-port fallback: bind an ephemeral loopback port instead.
        server = _bind_loopback(0, lambda: _make_callback_handler(state, result))

    bound_port = int(server.server_address[1])
    redirect_uri = f"http://127.0.0.1:{bound_port}/"
    auth_url = build_auth_url(
        client_id=secret["client_id"], redirect_uri=redirect_uri, state=state
    )

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        if on_auth_url is not None:
            on_auth_url(auth_url)
        open_browser(auth_url)
        await _wait_for_result(result, timeout=timeout)
    finally:
        server.shutdown()
        thread.join(timeout=2)

    error = result.get("error")
    if error == "state_mismatch":
        raise StateMismatchError("OAuth state mismatch; callback rejected.")
    if error == "missing_code":
        raise OAuthCallbackError("OAuth callback arrived without an authorization code.")
    if error and error.startswith("oauth_error:"):
        raise OAuthCallbackError(f"OAuth error from Google: {error.removeprefix('oauth_error:')}")

    code = result.get("code")
    if not code:
        raise OAuthCallbackError("No authorization code captured from the callback.")

    tokens = await exchange(code, redirect_uri=redirect_uri)
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise GmailSetupError(
            "No refresh_token returned. The consent project may be in "
            "'Testing' (refresh tokens then expire after 7 days) or the "
            "scope grant was incomplete."
        )
    store(str(refresh_token))
    access_token = tokens.get("access_token")
    if access_token:
        store_access(str(access_token))
    return tokens
