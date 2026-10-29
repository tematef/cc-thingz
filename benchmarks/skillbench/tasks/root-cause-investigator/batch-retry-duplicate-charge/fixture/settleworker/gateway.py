"""Simulated external payment gateway with idempotency-key deduplication."""

from __future__ import annotations

from dataclasses import dataclass


class GatewayTimeoutError(RuntimeError):
    """Raised when the payment gateway times out during a charge call."""


@dataclass(frozen=True)
class ChargeReceipt:
    tx_id: str
    customer_id: str
    amount_cents: int
    idempotency_key: str


class PaymentGateway:
    """Processes customer charges and deduplicates repeated `idempotency_key` values."""

    def __init__(self) -> None:
        self._by_key: dict[str, ChargeReceipt] = {}
        self.charges: list[ChargeReceipt] = []
        self._fail_once_customers: set[str] = set()

    def fail_next_for_customer(self, customer_id: str) -> None:
        self._fail_once_customers.add(customer_id)

    def charge(
        self,
        customer_id: str,
        amount_cents: int,
        *,
        idempotency_key: str,
    ) -> ChargeReceipt:
        if idempotency_key in self._by_key:
            return self._by_key[idempotency_key]
        if customer_id in self._fail_once_customers:
            self._fail_once_customers.remove(customer_id)
            raise GatewayTimeoutError(f"gateway timeout charging {customer_id}")
        receipt = ChargeReceipt(
            tx_id=f"tx-{len(self.charges) + 1}",
            customer_id=customer_id,
            amount_cents=amount_cents,
            idempotency_key=idempotency_key,
        )
        self._by_key[idempotency_key] = receipt
        self.charges.append(receipt)
        return receipt
