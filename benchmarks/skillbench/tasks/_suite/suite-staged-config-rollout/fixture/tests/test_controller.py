import unittest
from flagrollout.controller import FlagController, FlagRule

class ControllerTest(unittest.TestCase):
    def test_enabled_flag(self) -> None:
        c = FlagController()
        c.configure(FlagRule('new-ui', enabled=True, rollout_pct=100))
        self.assertTrue(c.evaluate('new-ui', 'user-1'))
