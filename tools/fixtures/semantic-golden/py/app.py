from __future__ import annotations

from core.orders import OrderService
from gateways import StripeGateway, pay_via
from utils.formatting import format_currency


def run_order(order_id: int, amount: float, tax_rate: float = 0.08) -> str:
    service = OrderService(tax_rate)
    result = service.process(order_id, amount)
    return format_currency(result["total"])


def run_stripe(amount: float) -> str:
    return pay_via(StripeGateway(), amount)