from __future__ import annotations

import functools
from collections.abc import Callable
from typing import Any


def require_auth(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    return wrapper


@require_auth
def publish_draft(title: str) -> str:
    # The exported symbol is the wrapper; the body belongs to the original.
    # Type/definition queries must not conflate the two.
    return f"draft:{title}"