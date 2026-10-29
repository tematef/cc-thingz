from dataclasses import dataclass

@dataclass(frozen=True)
class TransferRequest:
    from_account: str
    to_account: str
    amount_cents: int

@dataclass(frozen=True)
class TransferReceipt:
    from_account: str
    to_account: str
    amount_cents: int
    status: str

class WalletLedger:
    def __init__(self) -> None:
        self._balances: dict[str, int] = {}
    def credit(self, account: str, amount_cents: int) -> None:
        self._balances[account] = self._balances.get(account, 0) + amount_cents
    def balance(self, account: str) -> int:
        return self._balances.get(account, 0)
    def transfer(self, req: TransferRequest) -> TransferReceipt:
        self._balances[req.from_account] = self.balance(req.from_account) - req.amount_cents
        self._balances[req.to_account] = self.balance(req.to_account) + req.amount_cents
        return TransferReceipt(req.from_account, req.to_account, req.amount_cents, 'APPLIED')
