"""Password hashing (Argon2id) and strength validation."""

from __future__ import annotations

import re

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, Exception):  # noqa: BLE001 - any failure = invalid
        return False


def is_strong_password(password: str) -> bool:
    """Require at least 12 chars with upper, lower, and a digit."""
    if len(password) < 12:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    return bool(re.search(r"[0-9]", password))
