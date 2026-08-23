"""``growthos doctor`` — environment validation.

Each check reports PASS / FAIL / BLOCKED / NOT CONFIGURED. Nothing here claims a
capability exists; it only verifies the prerequisites for it.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import enum
import pathlib
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass

import httpx

from growthos.config import get_settings
from growthos.security.secrets import get_secret_store


def _run_async(coro):
    """Run a coroutine even if a loop is already running on this thread."""

    def _run():
        return asyncio.run(coro)

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _run()
    with concurrent.futures.ThreadPoolExecutor(1) as executor:
        return executor.submit(_run).result()


class CheckStatus(enum.StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    NOT_CONFIGURED = "NOT CONFIGURED"


@dataclass
class Check:
    name: str
    status: CheckStatus
    detail: str


def _which(cmd: str) -> str | None:
    return shutil.which(cmd)


def _check_python() -> Check:
    ok = (sys.version_info.major, sys.version_info.minor) >= (3, 12)
    return Check(
        "Python",
        CheckStatus.PASS if ok else CheckStatus.FAIL,
        f"{platform.python_version()} ({sys.executable})",
    )


def _check_node() -> Check:
    node = _which("node")
    if not node:
        return Check("Node.js", CheckStatus.NOT_CONFIGURED, "node not on PATH")
    try:
        out = subprocess.run(
            [node, "--version"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
        return Check("Node.js", CheckStatus.PASS, out)
    except Exception:  # noqa: BLE001
        return Check("Node.js", CheckStatus.FAIL, "node --version failed")


def _check_postgres() -> Check:
    # Check for a local PostgreSQL installation.
    pg_roots = [
        pathlib.Path(r"C:\Program Files\PostgreSQL"),
        pathlib.Path(r"C:\Program Files (x86)\PostgreSQL"),
    ]

    found = None
    for root in pg_roots:
        p = pathlib.Path(root)
        if p.exists():
            versions = [d.name for d in p.iterdir() if d.is_dir()]
            if versions:
                found = f"installed: {', '.join(versions)}"
    if not found:
        return Check("PostgreSQL", CheckStatus.NOT_CONFIGURED, "no local install found")
    return Check("PostgreSQL", CheckStatus.PASS, found)


def _check_ollama_server() -> Check:
    settings = get_settings()
    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m.get("name") for m in resp.json().get("models", [])]
            return Check(
                "Ollama server",
                CheckStatus.PASS,
                f"{len(models)} model(s) present",
            )
        return Check("Ollama server", CheckStatus.FAIL, f"HTTP {resp.status_code}")
    except Exception as exc:  # noqa: BLE001
        return Check(
            "Ollama server",
            CheckStatus.BLOCKED,
            f"unreachable at {settings.ollama_base_url}: {exc}",
        )


def _ollama_models() -> list[str]:
    settings = get_settings()
    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        return [m.get("name") for m in resp.json().get("models", [])]
    except Exception:  # noqa: BLE001
        return []


def _check_model(name: str) -> Check:
    models = _ollama_models()
    base = name.split(":")[0]
    present = any(m == name or m == f"{base}:latest" or m.startswith(base) for m in models)
    if present:
        return Check(f"Model {name}", CheckStatus.PASS, "present")
    return Check(
        f"Model {name}",
        CheckStatus.NOT_CONFIGURED,
        "not pulled — run `growthos setup ai`",
    )


def _check_db_connectivity() -> Check:
    from sqlalchemy import text

    from growthos.db import build_engine

    async def _try() -> str | None:
        engine = build_engine()
        try:
            async with engine.connect() as conn:
                version = await conn.scalar(text("SELECT version()"))
                return str(version)[:60]
        except Exception as exc:  # noqa: BLE001
            return f"ERROR: {exc}"
        finally:
            await engine.dispose()

    result = _run_async(_try())
    if result and str(result).startswith("ERROR"):
        return Check("Database connection", CheckStatus.BLOCKED, str(result))
    return Check("Database connection", CheckStatus.PASS, str(result or ""))


def _check_migrations() -> Check:
    from sqlalchemy import text

    from growthos.db import build_engine

    async def _try() -> str:
        engine = build_engine()
        try:
            try:
                async with engine.connect() as conn:
                    try:
                        current = await conn.scalar(
                            text("SELECT version_num FROM alembic_version")
                        )
                        return f"revision {current}"
                    except Exception:  # noqa: BLE001 - table missing
                        return "no alembic_version — run `growthos migrate`"
            except Exception as exc:  # noqa: BLE001 - cannot connect
                return f"ERROR: {exc}"
        finally:
            await engine.dispose()

    result = _run_async(_try())
    if result.startswith("ERROR"):
        return Check("Migrations", CheckStatus.BLOCKED, result)
    if result.startswith("no alembic_version"):
        return Check("Migrations", CheckStatus.NOT_CONFIGURED, result)
    return Check("Migrations", CheckStatus.PASS, result)


def _check_secrets() -> Check:
    try:
        store = get_secret_store()
        store.get("growthos.doctor.probe")
        return Check("Secret storage", CheckStatus.PASS, "OS keychain available")
    except Exception:  # noqa: BLE001
        return Check(
            "Secret storage",
            CheckStatus.NOT_CONFIGURED,
            "keyring unavailable; encrypted file fallback active",
        )


def _check_gmail() -> Check:
    store = get_secret_store()
    token = store.get("gmail.credentials")
    if token:
        return Check("Gmail", CheckStatus.PASS, "credentials stored")
    return Check("Gmail", CheckStatus.NOT_CONFIGURED, "run `growthos setup gmail`")


def _check_linkedin() -> Check:
    store = get_secret_store()
    token = store.get("linkedin.credentials")
    if token:
        return Check("LinkedIn", CheckStatus.PASS, "credentials stored")
    return Check("LinkedIn", CheckStatus.NOT_CONFIGURED, "run `growthos setup linkedin`")


def _check_sms() -> Check:
    # Hardware truth: the gateway adapter is only operational with a device+SIM.
    return Check(
        "SMS gateway",
        CheckStatus.BLOCKED,
        "compatible gateway hardware/SIM required (Android SMS gateway device)",
    )


def _check_tailscale() -> Check:
    ts = _which("tailscale")
    if not ts:
        return Check(
            "Tailscale", CheckStatus.NOT_CONFIGURED, "run `growthos setup remote-access`"
        )
    try:
        out = subprocess.run(
            [ts, "status"], capture_output=True, text=True, timeout=10
        ).stdout
        return Check("Tailscale", CheckStatus.PASS, out.splitlines()[0] if out else "installed")
    except Exception:  # noqa: BLE001
        return Check("Tailscale", CheckStatus.NOT_CONFIGURED, "not signed in")


def _check_frontend() -> Check:
    import pathlib

    node_modules = pathlib.Path("apps/web/node_modules")
    if node_modules.exists():
        return Check("Frontend", CheckStatus.PASS, "dependencies installed")
    return Check("Frontend", CheckStatus.NOT_CONFIGURED, "cd apps/web && pnpm install")


def _check_test_database() -> Check:
    import os

    from sqlalchemy import text

    from growthos.config import get_settings
    from growthos.db import build_engine

    url = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://growthos:growthos@127.0.0.1:5432/growthos_test")
    if url == get_settings().database_url:
        return Check("Test database isolation", CheckStatus.FAIL, "TEST_DATABASE_URL points to production DB")

    async def _probe() -> str:
        engine = build_engine(url)
        try:
            async with engine.connect() as conn:
                db = await conn.scalar(text("SELECT current_database()"))
                return str(db)
        except Exception as exc:  # noqa: BLE001
            return f"ERROR: {exc}"
        finally:
            await engine.dispose()

    result = _run_async(_probe())
    if result.startswith("ERROR"):
        return Check("Test database", CheckStatus.FAIL, result)
    return Check("Test database", CheckStatus.PASS, f"reachable: {result}; isolated from production")


def run_doctor(include_tests: bool = False) -> list[Check]:
    checks = [
        _check_python(),
        _check_node(),
        _check_postgres(),
        _check_ollama_server(),
        _check_model(get_settings().ollama_fast_model),
        _check_model(get_settings().ollama_embedding_model),
        _check_db_connectivity(),
        _check_migrations(),
        _check_secrets(),
        _check_gmail(),
        _check_linkedin(),
        _check_sms(),
        _check_tailscale(),
        _check_frontend(),
    ]
    if include_tests:
        checks.extend([_check_test_database()])
    return checks


def format_doctor(checks: list[Check]) -> str:
    lines = ["GrowthOS doctor", "=" * 60]
    for check in checks:
        lines.append(f"[{check.status.value}] {check.name}")
        if check.detail:
            lines.append(f"        {check.detail}")
    return "\n".join(lines)
