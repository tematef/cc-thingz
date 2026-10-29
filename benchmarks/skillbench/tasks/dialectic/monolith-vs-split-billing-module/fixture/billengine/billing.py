from dataclasses import dataclass

@dataclass(frozen=True)
class InvoiceRecord:
    tenant_id: str
    period: str
    units: int
    total_cents: int

class UsageMeter:
    def __init__(self) -> None:
        self._active: dict[tuple[str, str], int] = {}
        self._frozen: set[tuple[str, str]] = set()
    def record(self, tenant_id: str, period: str, units: int) -> None:
        key = (tenant_id, period)
        if key in self._frozen:
            raise RuntimeError('period already closed')
        self._active[key] = self._active.get(key, 0) + units

class InvoiceBuilder:
    def __init__(self, meter: UsageMeter, unit_price_cents: int = 5) -> None:
        self._meter = meter
        self._price = unit_price_cents
    def close_billing_period(self, tenant_id: str, period: str) -> InvoiceRecord:
        key = (tenant_id, period)
        self._meter._frozen.add(key)
        units = self._meter._active.get(key, 0)
        return InvoiceRecord(tenant_id, period, units, units * self._price)
