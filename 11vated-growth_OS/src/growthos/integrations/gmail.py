"""Gmail adapter (official Gmail REST API, OAuth 2.0).

Least-privilege scopes: ``gmail.readonly`` + ``gmail.send`` only. Credentials
live in the OS keychain (see ``gmail_oauth``). Incremental sync uses Gmail's
history mechanism; message dedup is enforced by the database (account +
external message id); raw email is preserved separately from analysis. Sending
is approval-controlled — the caller must pass the autonomy gate first.
"""

from __future__ import annotations

from typing import Any

import httpx

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"


class GmailApiError(RuntimeError):
    """Raised for Gmail API failures, carrying the HTTP status."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


class GmailClient:
    """Thin adapter over the Gmail REST API using OAuth access tokens."""

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.request(method, f"{GMAIL_API}{path}", headers=self._headers(), **kwargs)
        if resp.status_code >= 400:
            raise GmailApiError(resp.status_code, f"Gmail API {method} {path}: HTTP {resp.status_code}")
        return resp.json() if resp.content else {}

    async def profile(self) -> dict[str, Any]:
        return await self._request("GET", "/users/me/profile")

    async def list_messages(
        self,
        *,
        query: str = "",
        max_results: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"maxResults": max_results}
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token
        return await self._request("GET", "/users/me/messages", params=params)

    async def get_message(self, message_id: str, *, raw: bool = False) -> dict[str, Any]:
        """Fetch one message.

        Defaults to ``format=full`` (structured payload: headers, body parts and
        attachment metadata including the Gmail attachment id). Pass ``raw=True``
        to receive the base64 RFC-822 MIME blob instead.
        """
        params = {"format": "raw"} if raw else {"format": "full"}
        return await self._request("GET", f"/users/me/messages/{message_id}", params=params)

    async def get_attachment(self, message_id: str, attachment_id: str) -> dict[str, Any]:
        return await self._request(
            "GET", f"/users/me/messages/{message_id}/attachments/{attachment_id}"
        )

    async def history_list(
        self, history_id: int, *, history_types: str = "messageAdded"
    ) -> dict[str, Any]:
        return await self._request(
            "GET",
            "/users/me/history",
            params={"startHistoryId": history_id, "historyTypes": history_types},
        )

    async def send(self, *, to: str, subject: str, body: str) -> dict[str, Any]:
        """Send an email. Callers MUST pass the approval gate first."""
        import base64
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return await self._request(
            "POST", "/users/me/messages/send", json={"raw": raw}
        )

    async def create_draft(self, *, to: str, subject: str, body: str) -> dict[str, Any]:
        import base64
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        return await self._request(
            "POST", "/users/me/drafts", json={"message": {"raw": raw}}
        )
