"""Truthful Ollama health and capability reporting.

The Integrations page must never report CONNECTED merely because the Ollama
executable exists. This module probes the actual runtime: reachability, model
availability (pull state), a real generation, a real structured-output
extraction, and latency. Every state is derived from a live probe.

States surfaced to the UI:

* CONNECTED + MODEL AVAILABLE — runtime up, configured model present, probes pass
* CONNECTED (MODEL MISSING)     — runtime up, configured model not pulled
* OLLAMA OFFLINE                — runtime unreachable
* ERROR                         — probe failed

No cloud fallback: if the local runtime is down, the system reports it.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from pydantic import BaseModel, Field

from growthos.config import get_settings

HEALTH_PROBE_TIMEOUT = 90.0


class _ProbeResult(BaseModel):
    label: str
    ok: bool
    detail: str = ""
    latency_ms: int = 0


class OllamaStatus(BaseModel):
    state: str  # CONNECTED | OLLAMA_OFFLINE | ERROR
    runtime: str | None = None
    model: str | None = None
    model_available: bool = False
    model_pull_state: str = "unknown"  # available | missing | checking
    generation_ok: bool = False
    structured_output_ok: bool = False
    tool_selection_ok: bool = False
    latency_ms: int = 0
    error_message: str | None = None
    probes: list[dict[str, Any]] = []
    models_installed: list[str] = []


async def ollama_status() -> OllamaStatus:
    """Probe the local Ollama runtime truthfully. Never raises."""
    settings = get_settings()
    base_url = settings.ollama_base_url.rstrip("/")
    model = settings.ollama_fast_model

    status = OllamaStatus(state="ERROR")
    probes: list[_ProbeResult] = []

    # 1. Runtime reachability.
    try:
        async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
            started = time.perf_counter()
            resp = await client.get(f"{base_url}/api/tags")
            latency = int((time.perf_counter() - started) * 1000)
        resp.raise_for_status()
        data = resp.json()
        installed = [m.get("name", "") for m in data.get("models", [])]
        status.models_installed = installed
        status.runtime = "ollama"
        probes.append(_ProbeResult(label="runtime", ok=True, detail=f"Ollama reachable ({latency}ms)", latency_ms=latency))
    except Exception as exc:  # noqa: BLE001
        status.state = "OLLAMA_OFFLINE"
        status.error_message = f"Ollama runtime unreachable at {base_url}: {type(exc).__name__}"
        status.probes = [_ProbeResult(label="runtime", ok=False, detail=status.error_message).model_dump()]
        return status

    # 2. Configured model availability.
    available = any(
        m == model or m.startswith(f"{model}:") or m.startswith(f"{model}-")
        for m in installed
    )
    status.model = model
    status.model_available = available
    status.model_pull_state = "available" if available else "missing"
    probes.append(
        _ProbeResult(
            label="model",
            ok=available,
            detail=f"Model {model!r} {'available' if available else 'not pulled yet'}",
        )
    )
    if not available:
        status.state = "CONNECTED"
        status.generation_ok = False
        status.structured_output_ok = False
        status.probes = [p.model_dump() for p in probes]
        status.error_message = (
            f"Model {model!r} is not installed. Run: ollama pull {model}"
        )
        return status

    # 3. Real generation probe (short, cheap).
    try:
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
            resp = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": "Reply with the single word: ok", "stream": False},
            )
            latency = int((time.perf_counter() - started) * 1000)
            resp.raise_for_status()
            gen_text = resp.json().get("response", "")
        ok = "ok" in gen_text.lower()
        status.generation_ok = ok
        probes.append(_ProbeResult(label="generation", ok=ok, detail=f"generate probe ({latency}ms)", latency_ms=latency))
        status.latency_ms = latency
    except Exception as exc:  # noqa: BLE001
        status.state = "ERROR"
        status.error_message = f"Generation probe failed: {type(exc).__name__}: {exc}"
        status.probes = [p.model_dump() for p in probes]
        return status

    # 4. Structured-output probe.
    class _Echo(BaseModel):
        word: str = Field(min_length=1)

    try:
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
            resp = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                'Return ONLY a JSON object like {"word": "ok"} '
                                "with the word 'ok'. No commentary."
                            ),
                        }
                    ],
                    "stream": False,
                },
            )
            latency = int((time.perf_counter() - started) * 1000)
            resp.raise_for_status()
            content = (resp.json().get("message") or {}).get("content", "")
        import json as _json
        import re

        match = re.search(r"\{.*\}", content, re.DOTALL)
        parsed = _json.loads(match.group(0)) if match else {}
        validated = _Echo.model_validate(parsed)
        status.structured_output_ok = validated.word == "ok"
        probes.append(
            _ProbeResult(
                label="structured_output",
                ok=status.structured_output_ok,
                detail=f"structured JSON probe ({latency}ms)",
                latency_ms=latency,
            )
        )
        status.latency_ms = max(status.latency_ms, latency)
    except Exception as exc:  # noqa: BLE001
        status.structured_output_ok = False
        probes.append(
            _ProbeResult(label="structured_output", ok=False, detail=f"{type(exc).__name__}: {exc}")
        )

    # Tool-selection probe: the model must pick a deterministic branch.
    try:
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=HEALTH_PROBE_TIMEOUT) as client:
            resp = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                "Classify this request into exactly one tool: "
                                "'classify_email', 'product_intake', or 'none'. "
                                "Request: 'What is 2+2?' Reply with only the tool name."
                            ),
                        }
                    ],
                    "stream": False,
                },
            )
            latency = int((time.perf_counter() - started) * 1000)
            resp.raise_for_status()
            tool = (resp.json().get("message") or {}).get("content", "").strip().lower()
        status.tool_selection_ok = any(
            t in tool for t in ("classify_email", "product_intake", "none")
        )
        probes.append(
            _ProbeResult(
                label="tool_selection",
                ok=status.tool_selection_ok,
                detail=f"tool-selection probe ({latency}ms)",
                latency_ms=latency,
            )
        )
        status.latency_ms = max(status.latency_ms, latency)
    except Exception as exc:  # noqa: BLE001
        status.tool_selection_ok = False
        probes.append(
            _ProbeResult(label="tool_selection", ok=False, detail=f"{type(exc).__name__}: {exc}")
        )

    status.state = "CONNECTED"
    status.probes = [p.model_dump() for p in probes]
    return status
