import unittest
from statecfg.differ import diff_snapshots

class DifferBaselineTest(unittest.TestCase):
    def test_flat_diff(self) -> None:
        changes = diff_snapshots({'a': 1}, {'a': 2, 'b': 3})
        self.assertEqual(len(changes), 2)
