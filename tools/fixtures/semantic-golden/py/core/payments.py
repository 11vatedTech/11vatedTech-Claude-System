from __future__ import annotations

import os
from typing import Literal, overload


@overload
def process_payment(order_id: int, amount: int, method: Literal["cash"]) -> str: ...
@overload
def process_payment(order_id: int, amount: float, method: Literal["card"]) -> str: ...


def process_payment(order_id: int, amount: float, method: str) -> str:
    """Overloaded by declared type; runtime dispatch is by value."""
    return f"paid:{order_id}:{amount}:{method}"


def _card_secret() -> str:
    """Private helper; runtime callers cannot be proven statically."""
    return os.environ.get("CARD_SECRET", "")


def process_refund(order_id: int, amount: float) -> str:
    ...


def charge_multi(values: list[float]) -> list[str]:
    return [process_payment(i, v, "card") for i, v in enumerate(values)]