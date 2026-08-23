"""Identifier generation.

UUIDv4 is used throughout. PostgreSQL stores these natively as ``uuid``.
"""

from __future__ import annotations

import uuid


def new_id() -> str:
    """Return a new random UUID string (canonical form)."""
    return str(uuid.uuid4())


def is_valid_id(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False
