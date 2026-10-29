from dataclasses import dataclass
from .allocator import CostShare, allocate_shares

@dataclass(frozen=True)
class InvoiceSummary:
    net_total_cents: int
    allocated_sum_cents: int
    balanced: bool

class Reconciler:
    def verify_invoice(self, gross_cents: int, discount_pct: float, weights: dict[str, int]) -> InvoiceSummary:
        shares: list[CostShare] = allocate_shares(gross_cents, discount_pct, weights)
        net_total = int(round(gross_cents * (1.0 - discount_pct / 100.0)))
        alloc_sum = sum(s.allocated_cents for s in shares)
        return InvoiceSummary(net_total, alloc_sum, net_total == alloc_sum)
