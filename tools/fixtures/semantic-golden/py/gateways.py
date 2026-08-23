from __future__ import annotations

from typing import Protocol


class PaymentGateway(Protocol):
    """Structural protocol: any object with pay() satisfies it."""

    def pay(self, amount: float) -> str: ...


class StripeGateway:
    def pay(self, amount: float) -> str:
        return f"stripe:{amount}"


class PaypalGateway:
    def pay(self, amount: float) -> str:
        return f"paypal:{amount}"


class ManualGateway:
    """Duck-typed implementation: satisfies PaymentGateway without declaring it."""

    def pay(self, amount: float) -> str:
        return f"manual:{amount}"


def pay_via(gateway: PaymentGateway, amount: float) -> str:
    # Static receiver type is PaymentGateway; the concrete implementation is
    # not locally visible. UNKNOWN / POSSIBLE, never PROVEN.
    return gateway.pay(amount)


def charge_with_stripe(amount: float) -> str:
    # Direct concrete call: static and dynamic target are both StripeGateway.pay.
    return StripeGateway().pay(amount)