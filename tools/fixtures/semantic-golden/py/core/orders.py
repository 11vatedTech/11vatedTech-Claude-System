from __future__ import annotations

TAX_RATE: float = 0.08


class OrderService:
    """Computes order totals. The tax rate is configurable at construction."""

    def __init__(self, tax_rate: float = TAX_RATE) -> None:
        self.tax_rate = tax_rate

    def process(self, order_id: int, amount: float) -> dict:
        """Returns a summary dict for the given order."""
        return {"order_id": order_id, "total": amount * (1.0 + self.tax_rate)}