"""Secret storage.

Primary backend is the OS keychain (Windows Credential Manager via ``keyring``).
If no keychain backend is available, secrets fall back to an encrypted local
file whose key derives from ``SECRET_KEY``. Secrets are never committed.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from growthos.config import get_settings

_SERVICE = "11vatedTech-GrowthOS"


class SecretStore:
    """Get/set/delete secrets in the OS keychain with a file fallback."""

    def __init__(self) -> None:
        self._settings = get_settings()

    # -- keyring -----------------------------------------------------------
    def get(self, key: str) -> str | None:
        try:
            import keyring  # noqa: PLC0415

            return keyring.get_password(_SERVICE, key)
        except Exception:  # noqa: BLE001 - fall back to file
            return self._file_get(key)

    def set(self, key: str, value: str) -> None:
        try:
            import keyring  # noqa: PLC0415

            keyring.set_password(_SERVICE, key, value)
            return
        except Exception:  # noqa: BLE001 - fall back to file
            self._file_set(key, value)

    def delete(self, key: str) -> None:
        try:
            import keyring  # noqa: PLC0415

            keyring.delete_password(_SERVICE, key)
        except Exception:  # noqa: BLE001
            pass
        self._file_delete(key)

    # -- encrypted file fallback ------------------------------------------
    @property
    def _path(self) -> Path:
        root = Path(".secrets")
        root.mkdir(exist_ok=True)
        return root / "secrets.json"

    def _cipher(self):
        from cryptography.fernet import Fernet  # noqa: PLC0415

        key = base64.urlsafe_b64encode(
            self._settings.secret_key.encode("utf-8").ljust(32, b"\0")[:32]
        )
        return Fernet(key)

    def _read_map(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            plaintext = self._cipher().decrypt(data["blob"].encode()).decode()
            return json.loads(plaintext)
        except Exception:  # noqa: BLE001
            return {}

    def _write_map(self, mapping: dict[str, str]) -> None:
        blob = self._cipher().encrypt(json.dumps(mapping).encode()).decode()
        self._path.write_text(
            json.dumps({"blob": blob}), encoding="utf-8"
        )

    def _file_get(self, key: str) -> str | None:
        return self._read_map().get(key)

    def _file_set(self, key: str, value: str) -> None:
        mapping = self._read_map()
        mapping[key] = value
        self._write_map(mapping)

    def _file_delete(self, key: str) -> None:
        mapping = self._read_map()
        mapping.pop(key, None)
        self._write_map(mapping)


_secret_store: SecretStore | None = None


def get_secret_store() -> SecretStore:
    global _secret_store
    if _secret_store is None:
        _secret_store = SecretStore()
    return _secret_store
