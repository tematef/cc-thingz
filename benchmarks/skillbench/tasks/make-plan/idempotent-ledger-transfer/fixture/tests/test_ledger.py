import unittest
from walletcore.ledger import TransferRequest, WalletLedger

class WalletLedgerTest(unittest.TestCase):
    def test_simple_transfer(self) -> None:
        ledger = WalletLedger()
        ledger.credit('alice', 1000)
        receipt = ledger.transfer(TransferRequest('alice', 'bob', 400))
        self.assertEqual(receipt.status, 'APPLIED')
        self.assertEqual(ledger.balance('alice'), 600)
        self.assertEqual(ledger.balance('bob'), 400)
