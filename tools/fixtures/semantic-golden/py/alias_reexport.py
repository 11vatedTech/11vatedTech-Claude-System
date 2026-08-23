from __future__ import annotations

# Import alias (class H): the same module is reachable under two names.
from core.orders import OrderService as OS
from core.orders import TAX_RATE as rate

# Re-export (class I): downstream imports should still ground to core.orders.
__all__ = ["OS", "rate", "OrderService"]

from core.orders import OrderService  # noqa: E402  (re-export under original name)