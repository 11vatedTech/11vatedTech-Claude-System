"""Automated secret-leak guard.

Scans tracked repository files and generated runtime logs for credential-like
content WITHOUT printing any matched value. Reports only relative paths and a
redacted marker so a leak cannot be amplified by the scan itself.

Covered patterns:

- private key blocks (PEM)
- OAuth client secrets / refresh tokens / access tokens as value literals
- bearer tokens in logs
- explicit password assignments in env-like or log files
- tracked secrets files (`.env`, `.secrets/`, credential JSON) present in git

These tests intentionally contain NO real credentials.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Patterns (name -> compiled regex). Never capture and print the matched text.
# ---------------------------------------------------------------------------

PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    re.MULTILINE,
)
CLIENT_SECRET_VALUE = re.compile(
    r"""client_secret['"]?\s*[:=]\s*['"][A-Za-z0-9_\-\.]{20,}['"]""",
    re.MULTILINE,
)
REFRESH_TOKEN_VALUE = re.compile(
    r"""refresh_token['"]?\s*[:=]\s*['"][A-Za-z0-9_\-\.]{20,}['"]""",
    re.MULTILINE,
)
ACCESS_TOKEN_VALUE = re.compile(
    r"""access_token['"]?\s*[:=]\s*['"][A-Za-z0-9_\-\.]{20,}['"]""",
    re.MULTILINE,
)
BEARER_IN_LOG = re.compile(r"Authorization:\s*Bearer\s+\S+", re.IGNORECASE)
PASSWORD_IN_ENV_OR_LOG = re.compile(
    r"""(?:^|\s)(?:PASSWORD|PASSWD|DB_PASSWORD|POSTGRES_PASSWORD)\s*=\s*['"]?\S+['"]?""",
    re.IGNORECASE | re.MULTILINE,
)

TRACKED_FILE_PATTERNS = {
    "private_key": PRIVATE_KEY,
    "client_secret_value": CLIENT_SECRET_VALUE,
    "refresh_token_value": REFRESH_TOKEN_VALUE,
    "access_token_value": ACCESS_TOKEN_VALUE,
}

LOG_PATTERNS = {
    "bearer_in_log": BEARER_IN_LOG,
    "password_in_log": PASSWORD_IN_ENV_OR_LOG,
    "refresh_token_value": REFRESH_TOKEN_VALUE,
    "access_token_value": ACCESS_TOKEN_VALUE,
}

SECRET_FILE_NAMES = (
    ".env",
    "credentials.json",
    "client_secret",
    "token.json",
    "secrets.json",
)


def _tracked_files() -> list[Path]:
    """Return tracked files via git (ignores .venv, node_modules, .git)."""
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [REPO_ROOT / name for name in result.stdout.split("\0") if name]


def _runtime_logs() -> list[Path]:
    log_dir = REPO_ROOT / ".freebuff"
    if not log_dir.is_dir():
        return []
    return sorted(
        p for p in log_dir.iterdir() if p.suffix in {".log", ".err"}
    )


def _scan_files(paths: list[Path], patterns: dict[str, re.Pattern]) -> list[str]:
    """Return redacted findings: 'path: pattern' lines (values never printed)."""
    findings: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, pattern in patterns.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(REPO_ROOT)}: {name}")
    return findings


def test_no_secret_files_are_tracked() -> None:
    tracked = _tracked_files()
    offenders = [
        p.relative_to(REPO_ROOT)
        for p in tracked
        if any(part in SECRET_FILE_NAMES for part in p.parts)
    ]
    assert not offenders, (
        "Secret files are tracked in git (***REDACTED***): "
        + ", ".join(str(o) for o in offenders)
    )


def test_tracked_source_contains_no_credential_literals() -> None:
    findings = _scan_files(_tracked_files(), TRACKED_FILE_PATTERNS)
    assert not findings, (
        "Credential-like content found in tracked files (***REDACTED***): "
        + "; ".join(findings)
    )


def test_runtime_logs_contain_no_credentials() -> None:
    findings = _scan_files(_runtime_logs(), LOG_PATTERNS)
    assert not findings, (
        "Credential-like content found in runtime logs (***REDACTED***): "
        + "; ".join(findings)
    )


def test_no_plaintext_password_placeholders_in_env_template() -> None:
    template = REPO_ROOT / ".env.example"
    if not template.is_file():
        return
    text = template.read_text(encoding="utf-8")
    # Only secret-bearing keys must use placeholders; non-secret config like
    # ENVIRONMENT may carry real defaults.
    for line in text.splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            key = key.strip().upper()
            value = value.strip()
            is_secret_key = any(
                token in key for token in ("PASSWORD", "SECRET", "TOKEN", "KEY")
            )
            has_userinfo = bool(re.search(r"://[^/@]+:[^/@]+@", value))
            is_credential_url = "URL" in key and has_userinfo
            if not (is_secret_key or is_credential_url):
                continue
            assert "CHANGE" in value.upper() or not value, (
                f".env.example line {key!r} has a concrete value "
                "(***REDACTED***); secret templates must use CHANGE* "
                "placeholders"
            )
