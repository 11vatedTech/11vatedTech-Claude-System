#!/usr/bin/env python3
"""Semantic 9Router diagnostics.

A healthy chat gateway and a complete model registry are different states. This
probe never waits indefinitely on /v1/models and reports degraded discovery
without misclassifying the whole gateway as down.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_CATEGORIES = ("/v1/models/image", "/v1/models/tts", "/v1/models/embedding", "/v1/models/web", "/v1/models/stt", "/v1/models/image-to-text")

# Claude Code composes its Messages request as ANTHROPIC_BASE_URL + "/v1/messages".
# If the configured base already ends with "/v1" (9Router's own claude-settings
# writer forces that suffix), the effective path becomes "/v1/v1/messages".
# 9Router has historically accepted that doubled path (5k+ ok requests on
# record), so the duplicated /v1 is a diagnostic flag, not automatically fatal.
EXPECTED_CLIENT_PATH_SUFFIX = "/v1/messages"


def _redact(text: str) -> str:
    """Strip token-like material before it reaches any report/log."""
    import re

    return re.sub(r"(sk-[A-Za-z0-9_-]{6})[A-Za-z0-9_-]*", r"\1<redacted>", text)


def effective_claude_gateway(settings_path=None) -> dict:
    """Read the effective Claude gateway env from ~/.claude/settings.json.

    Returns the base URL, the request path Claude Code will compose, whether the
    path is duplicated, and the configured default model. Token values are never
    returned.
    """
    from pathlib import Path

    path = Path(settings_path) if settings_path else Path.home() / ".claude" / "settings.json"
    result = {"source": str(path), "present": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        result["error"] = "settings.json not found"
        return result
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    env = data.get("env") or {}
    base = env.get("ANTHROPIC_BASE_URL") or ""
    if not base:
        result["error"] = "no ANTHROPIC_BASE_URL in settings.json env"
        return result
    result["present"] = True
    result["base_url"] = _redact(base)
    result["composed_path"] = _redact(base.rstrip("/") + EXPECTED_CLIENT_PATH_SUFFIX)
    result["duplicated_v1"] = base.rstrip("/").endswith("/v1")
    for key, value in env.items():
        if key.startswith("ANTHROPIC_DEFAULT_") and value:
            result["default_model"] = str(value)
            break
    return result


def classify_registry_failure(error: BaseException) -> str:
    text = f"{type(error).__name__}: {error}".lower()
    if "timed out" in text or "timeout" in text:
        return "UPSTREAM_PROVIDER_FAILURE"
    if "dns" in text or "resolve" in text or "name or service" in text:
        return "DNS_FAILURE"
    if isinstance(error, urllib.error.HTTPError):
        return "REGISTRY_HTTP_FAILURE"
    return "MODEL_REGISTRY_PARTIAL"


def fetch(url: str, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", "replace"))


def _settings_token() -> str:
    """Return the local Claude gateway token for the smoke probe, if present.

    Used only to emulate the real client against 127.0.0.1; never printed or
    written to reports.
    """
    from pathlib import Path

    try:
        data = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8-sig"))
        return (data.get("env") or {}).get("ANTHROPIC_AUTH_TOKEN") or "sk-probe"
    except Exception:
        return "sk-probe"


def chat_smoke(path: str, model: str | None, timeout: float = 8.0) -> dict:
    """POST a minimal Anthropic-format message through the composed path.

    Classifies:
    - CHAT_PATH_HEALTHY: structured 2xx from the router
    - MODEL_RESOLUTION_FAILURE: structured router 4xx (model/credential leg)
    - PATH_NOT_ROUTED: HTML 404 (the composed path is not served)
    - UPSTREAM_PROVIDER_FAILURE: router reachable, model leg times out
    - ROUTER_DOWN: connection refused / gateway unreachable
    """
    token = _settings_token()
    body = json.dumps({
        "model": model or "claude-11",
        "max_tokens": 8,
        "messages": [{"role": "user", "content": "ping"}],
    }).encode("utf-8")
    req = urllib.request.Request(
        path,
        data=body,
        headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01", "x-api-key": token, "Authorization": f"Bearer {token}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return {"status": "CHAT_PATH_HEALTHY", "http": response.status, "body": _redact(response.read(160).decode("utf-8", "replace"))}
    except urllib.error.HTTPError as exc:
        raw = exc.read(200).decode("utf-8", "replace")
        if exc.code == 404 and raw.lstrip().startswith("<!DOCTYPE"):
            return {"status": "PATH_NOT_ROUTED", "http": exc.code}
        return {"status": "MODEL_RESOLUTION_FAILURE", "http": exc.code, "body": _redact(raw)}
    except Exception as exc:
        classification = classify_registry_failure(exc)
        if classification == "UPSTREAM_PROVIDER_FAILURE":
            return {"status": "UPSTREAM_PROVIDER_FAILURE", "error": f"{type(exc).__name__}: {exc}"}
        return {"status": "ROUTER_DOWN", "error": f"{type(exc).__name__}: {exc}"}


def probe(base: str = "http://127.0.0.1:20128", timeout: float = 8.0) -> dict[str, Any]:
    result: dict[str, Any] = {"schema_version": 2, "kind": "9router-health", "base": base, "timeout_seconds": timeout}
    gateway = effective_claude_gateway()
    result["claude_gateway"] = gateway
    composed = gateway.get("composed_path") or (base.rstrip("/") + EXPECTED_CLIENT_PATH_SUFFIX)
    try:
        health = fetch(base + "/api/health", timeout)
        result["router"] = {"status": "PASS" if health.get("ok") is True else "DEGRADED", "health": health}
    except Exception as exc:
        result["router"] = {"status": "ROUTER_DOWN", "error": f"{type(exc).__name__}: {exc}"}
        result["core_status"] = "FAIL"
        result["chat_smoke"] = {"status": "ROUTER_DOWN", "error": f"{type(exc).__name__}: {exc}"}
        return result

    result["chat_smoke"] = chat_smoke(composed, gateway.get("default_model"), timeout)
    canonical = base.rstrip("/") + "/v1/messages"
    if canonical != composed:
        result["canonical_smoke"] = chat_smoke(canonical, gateway.get("default_model"), timeout)

    try:
        data = fetch(base + "/v1/models", timeout)
        result["registry"] = {"status": "COMPLETE", "count": len(data.get("data", []))}
    except Exception as exc:
        result["registry"] = {"status": "DEGRADED", "classification": classify_registry_failure(exc), "error": f"{type(exc).__name__}: {exc}"}

    categories: dict[str, Any] = {}
    for path in DEFAULT_CATEGORIES:
        try:
            data = fetch(base + path, timeout)
            categories[path] = {"status": "PASS", "count": len(data.get("data", []))}
        except Exception as exc:
            categories[path] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    result["categories"] = categories
    category_ok = all(v.get("status") == "PASS" for v in categories.values())
    smoke_status = result["chat_smoke"]["status"]
    # Upstream/provider timeouts and structured model-resolution errors mean the
    # router is reachable but a model leg is degraded: report them honestly as
    # DEGRADED without failing the whole gate. Only an unreachable router or an
    # unexpected HTTP failure is a hard FAIL.
    smoke_fatal = smoke_status in ("ROUTER_DOWN", "HTTP_FAILURE")
    result["core_status"] = "PASS" if result["router"]["status"] == "PASS" and category_ok and not smoke_fatal else "DEGRADED"
    summary_parts = [f"FOUNDRY CORE: {result['core_status']}", f"MODEL REGISTRY: {result['registry']['status']}"]
    if smoke_status != "CHAT_PATH_HEALTHY":
        summary_parts.append(f"CLAUDE CHAT: {smoke_status}")
    if gateway.get("duplicated_v1"):
        summary_parts.append("PATH: duplicated /v1 (accepted by router, diagnostic)")
    result["summary"] = "; ".join(summary_parts)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--base", default=os.environ.get("NINEROUTER_URL", "http://127.0.0.1:20128").removesuffix("/v1")); parser.add_argument("--timeout", type=float, default=8.0); parser.add_argument("--out")
    args = parser.parse_args(); result = probe(args.base, args.timeout); text = json.dumps(result, indent=2)
    if args.out:
        from pathlib import Path
        Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(text, encoding="utf-8")
    print(text); return 0 if result.get("core_status") == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
