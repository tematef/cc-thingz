import threading
from dataclasses import dataclass

@dataclass
class SkuSlot:
    sku: str
    available: int
    version: int = 0

class InventoryTable:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._slots: dict[str, SkuSlot] = {}
    def seed(self, sku: str, available: int) -> None:
        self._slots[sku] = SkuSlot(sku, available, 0)
    def reserve_items(self, quantities: dict[str, int]) -> bool:
        with self._lock:
            for sku, qty in quantities.items():
                if self._slots[sku].available < qty:
                    return False
            for sku, qty in quantities.items():
                slot = self._slots[sku]
                slot.available -= qty
                slot.version += 1
            return True
