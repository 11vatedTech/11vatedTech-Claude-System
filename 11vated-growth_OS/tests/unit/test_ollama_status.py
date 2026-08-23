"""Unit tests for Ollama health/status truth.

Mocks the HTTP transport only; never hits a real model. Verifies that the
reported state is derived from live probe results, never assumed from the
executable's existence.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from growthos.intelligence.ollama_status import OllamaStatus, ollama_status

FAST_MODEL = "gemma2:9b"


class FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            from httpx import HTTPStatusError

            raise HTTPStatusError(
                f"HTTP {self.status_code}", request=None, response=self  # type: ignore[arg-type]
            )

    def json(self) -> dict:
        return self._payload


def _tags_payload(include_model: bool = True) -> dict:
    models = [
        {"name": "qwen2.5:32b"},
        {"name": "codestral:22b"},
    ]
    if include_model:
        models.append({"name": FAST_MODEL})
    return {"models": models}


@pytest.mark.asyncio
async def test_ollama_offline_reported_truthfully() -> None:
    async def fake_get(url, **kwargs):
        raise ConnectionError("runtime not listening")

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=fake_get)):
        status: OllamaStatus = await ollama_status()
    assert status.state == "OLLAMA_OFFLINE"
    assert status.generation_ok is False
    assert status.error_message and "unreachable" in status.error_message


@pytest.mark.asyncio
async def test_model_missing_reported_truthfully() -> None:
    async def fake_get(url, **kwargs):
        return FakeResponse(200, _tags_payload(include_model=False))

    with patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=fake_get)):
        status: OllamaStatus = await ollama_status()
    assert status.state == "CONNECTED"
    assert status.model_available is False
    assert status.model_pull_state == "missing"
    assert status.generation_ok is False
    assert "not installed" in (status.error_message or "")


@pytest.mark.asyncio
async def test_full_connected_probe() -> None:
    async def fake_get(url, **kwargs):
        if url.endswith("/api/tags"):
            return FakeResponse(200, _tags_payload(include_model=True))
        raise AssertionError(f"unexpected GET {url}")

    async def fake_post(url, **kwargs):
        payload = kwargs.get("json", {})
        if url.endswith("/api/generate"):
            return FakeResponse(200, {"response": "ok"})
        if url.endswith("/api/chat"):
            content = payload["messages"][-1]["content"]
            if "JSON object" in content:
                return FakeResponse(200, {"message": {"content": '{"word": "ok"}'}})
            return FakeResponse(200, {"message": {"content": "product_intake"}})
        raise AssertionError(f"unexpected POST {url}")

    with (
        patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=fake_get)),
        patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)),
    ):
        status: OllamaStatus = await ollama_status()
    assert status.state == "CONNECTED"
    assert status.model_available is True
    assert status.model_pull_state == "available"
    assert status.generation_ok is True
    assert status.structured_output_ok is True
    assert status.tool_selection_ok is True
    assert status.latency_ms > 0
    assert status.error_message is None


@pytest.mark.asyncio
async def test_generation_failure_reported_as_error() -> None:
    async def fake_get(url, **kwargs):
        return FakeResponse(200, _tags_payload(include_model=True))

    async def fake_post(url, **kwargs):
        raise TimeoutError("generation timed out")

    with (
        patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=fake_get)),
        patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)),
    ):
        status: OllamaStatus = await ollama_status()
    assert status.state == "ERROR"
    assert status.generation_ok is False
    assert status.error_message and "Generation probe failed" in status.error_message


@pytest.mark.asyncio
async def test_structured_output_failure_is_partial_not_fatal() -> None:
    responses = {"generation": True, "structured": False, "tool": True}

    async def fake_get(url, **kwargs):
        return FakeResponse(200, _tags_payload(include_model=True))

    async def fake_post(url, **kwargs):
        payload = kwargs.get("json", {})
        if url.endswith("/api/generate"):
            return FakeResponse(200, {"response": "ok"})
        content = payload["messages"][-1]["content"]
        if "JSON object" in content:
            if responses["structured"]:
                return FakeResponse(200, {"message": {"content": '{"word": "ok"}'}})
            return FakeResponse(200, {"message": {"content": "sorry, no json"}})
        return FakeResponse(200, {"message": {"content": "none"}})

    with (
        patch("httpx.AsyncClient.get", new=AsyncMock(side_effect=fake_get)),
        patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=fake_post)),
    ):
        status: OllamaStatus = await ollama_status()
    assert status.state == "CONNECTED"
    assert status.generation_ok is True
    assert status.structured_output_ok is False
    assert status.tool_selection_ok is True
