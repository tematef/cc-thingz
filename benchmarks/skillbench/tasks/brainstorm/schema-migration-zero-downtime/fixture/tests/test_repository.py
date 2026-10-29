import unittest
from profiledb.repository import LegacyProfile, UserProfileStore

class ProfileStoreTest(unittest.TestCase):
    def test_put_get_v1(self) -> None:
        store = UserProfileStore()
        store.put_v1(LegacyProfile('u1', 'Ada Lovelace', '12 Main St, London, UK'))
        self.assertEqual(store.get_v1('u1').full_name, 'Ada Lovelace')
