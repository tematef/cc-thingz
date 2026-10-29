from dataclasses import dataclass

@dataclass(frozen=True)
class CostShare:
    center_id: str
    weight: int
    allocated_cents: int

def allocate_shares(gross_cents: int, discount_pct: float, weights: dict[str, int]) -> list[CostShare]:
    total_weight = sum(weights.values())
    out: list[CostShare] = []
    for cid, w in weights.items():
        raw_share = (gross_cents * (w / total_weight)) * (1.0 - discount_pct / 100.0)
        out.append(CostShare(cid, w, int(round(raw_share))))
    return out
