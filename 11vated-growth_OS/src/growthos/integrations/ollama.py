"""Local inference via Ollama.

Provides a provider interface so the local model can be upgraded without
rewriting GrowthOS. Every request records model, purpose, input evidence IDs,
structured output, latency, and failure state.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from growthos.config import get_settings
from growthos.domain.models_system import ModelRequest
from growthos.shared.ids import new_id

T = TypeVar("T", bound=BaseModel)


@dataclass
class ModelResponse:
    text: str
    model: str
    latency_ms: int
    tokens_in: int | None = None
    tokens_out: int | None = None


class ModelProvider(ABC):
    """Provider interface for local (and future) inference backends."""

    @abstractmethod
    async def chat(
        self,
        session,
        *,
        purpose: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        evidence_ids: list[str] | None = None,
    ) -> ModelResponse:
        raise NotImplementedError

    @abstractmethod
    async def embed(
        self,
        session,
        *,
        purpose: str,
        text: str,
        model: str | None = None,
        evidence_ids: list[str] | None = None,
    ) -> list[float]:
        raise NotImplementedError


class OllamaProvider(ModelProvider):
    """Talks to the local Ollama server over HTTP."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout or settings.ollama_timeout_seconds

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(f"{self.base_url}{path}", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def chat(
        self,
        session,
        *,
        purpose: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        evidence_ids: list[str] | None = None,
    ) -> ModelResponse:
        settings = get_settings()
        model_name = model or settings.ollama_fast_model
        started = time.perf_counter()
        try:
            data = await self._post(
                "/api/chat",
                {
                    "model": model_name,
                    "messages": messages,
                    "stream": False,
                },
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            content = (data.get("message") or {}).get("content", "")
            resp = ModelResponse(
                text=content,
                model=model_name,
                latency_ms=latency_ms,
                tokens_in=data.get("prompt_eval_count"),
                tokens_out=data.get("eval_count"),
            )
            await self._log(
                session,
                purpose=purpose,
                model=model_name,
                evidence_ids=evidence_ids,
                latency_ms=latency_ms,
                tokens_in=resp.tokens_in,
                tokens_out=resp.tokens_out,
                raw_output=content,
                structured_output=None,
                prompt=json.dumps(messages),
            )
            return resp
        except Exception as exc:  # noqa: BLE001 - record failure, re-raise
            latency_ms = int((time.perf_counter() - started) * 1000)
            await self._log(
                session,
                purpose=purpose,
                model=model_name,
                evidence_ids=evidence_ids,
                latency_ms=latency_ms,
                failure_state=type(exc).__name__,
                error=str(exc),
                prompt=json.dumps(messages),
            )
            raise

    async def structured(
        self,
        session,
        *,
        purpose: str,
        prompt: str,
        schema: type[T],
        model: str | None = None,
        evidence_ids: list[str] | None = None,
        max_retries: int = 2,
    ) -> T:
        """Extract a validated structured object.

        The model is asked for JSON, which is parsed and validated with a
        Pydantic schema. A validation failure retries once with the error
        included as feedback.
        """
        attempts = 0
        last_error: str | None = None
        while attempts <= max_retries:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a structured extraction engine. Respond with "
                        "ONLY a valid JSON object matching the requested "
                        "schema. No markdown, no commentary."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            if last_error:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous JSON was invalid: "
                            f"{last_error}\nReturn corrected JSON only."
                        ),
                    }
                )
            response = await self.chat(
                session,
                purpose=purpose,
                messages=messages,
                model=model,
                evidence_ids=evidence_ids,
            )
            try:
                parsed = json.loads(_extract_json(response.text))
                instance = schema.model_validate(parsed)
                await self._log_structured(
                    session, purpose, model or get_settings().ollama_fast_model,
                    evidence_ids, response, instance,
                )
                return instance
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = str(exc)
                attempts += 1
        raise ValueError(
            f"Structured extraction failed after {max_retries + 1} attempts: "
            f"{last_error}"
        )

    async def embed(
        self,
        session,
        *,
        purpose: str,
        text: str,
        model: str | None = None,
        evidence_ids: list[str] | None = None,
    ) -> list[float]:
        settings = get_settings()
        model_name = model or settings.ollama_embedding_model
        started = time.perf_counter()
        try:
            data = await self._post(
                "/api/embed", {"model": model_name, "input": text}
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            await self._log(
                session,
                purpose=purpose,
                model=model_name,
                evidence_ids=evidence_ids,
                latency_ms=latency_ms,
                raw_output=f"embedding[{len(data.get('embeddings', [[]])[0])}]",
                prompt=text[:1000],
            )
            return data.get("embeddings", [[None]])[0] or []
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.perf_counter() - started) * 1000)
            await self._log(
                session,
                purpose=purpose,
                model=model_name,
                evidence_ids=evidence_ids,
                latency_ms=latency_ms,
                failure_state=type(exc).__name__,
                error=str(exc),
                prompt=text[:1000],
            )
            raise

    async def _log(
        self,
        session,
        *,
        purpose: str,
        model: str,
        evidence_ids: list[str] | None,
        latency_ms: int,
        tokens_in: int | None = None,
        tokens_out: int | None = None,
        raw_output: str | None = None,
        structured_output: dict[str, Any] | None = None,
        failure_state: str | None = None,
        error: str | None = None,
        prompt: str | None = None,
    ) -> None:
        session.add(
            ModelRequest(
                id=new_id(),
                provider="ollama",
                model=model,
                purpose=purpose,
                input_evidence_ids=evidence_ids or [],
                prompt=prompt,
                raw_output=raw_output,
                structured_output=structured_output,
                latency_ms=latency_ms,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                failure_state=failure_state,
                error=error,
            )
        )
        await session.flush()

    async def _log_structured(
        self,
        session,
        purpose: str,
        model: str,
        evidence_ids: list[str] | None,
        response: ModelResponse,
        instance: BaseModel,
    ) -> None:
        await self._log(
            session,
            purpose=purpose,
            model=model,
            evidence_ids=evidence_ids,
            latency_ms=response.latency_ms,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
            raw_output=response.text,
            structured_output=instance.model_dump(mode="json"),
        )


class ModelRouter:
    """Selects models by purpose (fast / deep analysis / embeddings)."""

    def __init__(self, provider: ModelProvider | None = None) -> None:
        settings = get_settings()
        self.provider = provider or OllamaProvider()
        self.fast_model = settings.ollama_fast_model
        self.deep_model = settings.ollama_deep_model
        self.embedding_model = settings.ollama_embedding_model

    def model_for(self, purpose: str) -> str:
        if purpose == "embedding":
            return self.embedding_model
        if purpose == "deep_analysis":
            return self.deep_model
        return self.fast_model


def _extract_json(text: str) -> str:
    """Extract the first balanced JSON object/array from model output."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text
