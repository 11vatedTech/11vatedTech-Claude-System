from __future__ import annotations

# Deliberate trap: a module-level `process` that has no relation to
# core.orders.OrderService.process.
def process(order_id: int, amount: float) -> float:
    return amount - (order_id % 10)