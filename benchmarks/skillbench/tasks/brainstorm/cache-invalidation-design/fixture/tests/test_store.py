import unittest
from catalogcache.store import BundleCache, CatalogStore, SkuRecord

class CatalogStoreTest(unittest.TestCase):
    def test_bundle_total(self) -> None:
        store = CatalogStore(BundleCache())
        store.upsert_sku(SkuRecord('sku-1', 500))
        store.upsert_sku(SkuRecord('sku-2', 700))
        store.define_bundle('b-1', ('sku-1', 'sku-2'))
        self.assertEqual(store.get_bundle('b-1').total_cents, 1200)
