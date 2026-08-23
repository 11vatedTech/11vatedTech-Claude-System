from __future__ import annotations

from typing import Union

Amount = Union[int, float]  # declared alias used by the function signature


def format_currency(amount: float, symbol: str = "$") -> str:
    return f"{symbol}{amount:,.2f}"


def format_units(amount: Amount) -> str:
    # Declared type is the Amount alias (Union[int, float]).
    return f"{amount}u"