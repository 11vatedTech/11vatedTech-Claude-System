"""Android SMS gateway adapter.

Targets the self-hosted server of the open-source
``capcom6/android-sms-gateway`` project. The Android device with a carrier SIM
is the modem; no Twilio or metered telephony SaaS.

The gateway's own API key is stored via the OS keychain. The founder number is
allowlisted in settings and is the only privileged command source.
"""

from __future__ import annotations

from typing import Any

import httpx

from growthos.security.secrets import get_secret_store

_SECRET_KEY = "sms.gateway.api_key"


class AndroidSmsGateway:
    """Client for a self-hosted Android SMS gateway server."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = (base_url or "http://127.0.0.1:8090").rstrip("/")
        self.api_key = api_key or get_secret_store().get(_SECRET_KEY)
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def send_message(
        self, phone_number: str, message: str, sim_index: int | None = None
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "phoneNumbers": [phone_number],
            "message": message,
        }
        if sim_index is not None:
            payload["simIndex"] = sim_index
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/message",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def list_messages(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/message", headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                f"{self.base_url}/health", headers=self._headers()
            )
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    def store_api_key(api_key: str) -> None:
        get_secret_store().set(_SECRET_KEY, api_key)
