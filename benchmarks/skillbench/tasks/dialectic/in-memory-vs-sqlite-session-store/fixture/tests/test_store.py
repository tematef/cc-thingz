import unittest
from sessionvault.store import SessionStore, SessionToken

class SessionStoreTest(unittest.TestCase):
    def test_validate_and_touch(self) -> None:
        s = SessionStore()
        s.put(SessionToken('t1', 'u1', 200.0, 100.0))
        tok = s.validate_and_touch('t1', 150.0)
        self.assertIsNotNone(tok)
        self.assertEqual(tok.last_seen_at, 150.0)
