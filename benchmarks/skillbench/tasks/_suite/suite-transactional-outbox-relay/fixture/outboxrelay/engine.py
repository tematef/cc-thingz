from dataclasses import dataclass

@dataclass
class Order:
    order_id: str
    amount_cents: int

@dataclass
class OutboxRecord:
    seq: int
    order_id: str
    amount_cents: int
    sent: bool = False
    attempts: int = 0

class OrderStore:
    def __init__(self) -> None:
        self.orders: dict[str, Order] = {}
        self.outbox: list[OutboxRecord] = []
    def create_order(self, order_id: str, amount_cents: int) -> Order:
        if amount_cents <= 0:
            raise ValueError('amount_cents must be positive')
        order = Order(order_id, amount_cents)
        self.orders[order_id] = order
        return order
