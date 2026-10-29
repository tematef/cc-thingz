from dataclasses import dataclass

@dataclass
class SkuRecord:
    sku_id: str
    price_cents: int

@dataclass
class BundleView:
    bundle_id: str
    sku_ids: tuple[str, ...]
    total_cents: int

class BundleCache:
    def __init__(self) -> None:
        self._entries: dict[str, BundleView] = {}
    def get(self, bundle_id: str) -> BundleView | None:
        return self._entries.get(bundle_id)
    def put(self, view: BundleView) -> None:
        self._entries[view.bundle_id] = view

class CatalogStore:
    def __init__(self, cache: BundleCache) -> None:
        self._skus: dict[str, SkuRecord] = {}
        self._bundles: dict[str, tuple[str, ...]] = {}
        self._cache = cache
    def upsert_sku(self, sku: SkuRecord) -> None:
        self._skus[sku.sku_id] = sku
    def define_bundle(self, bundle_id: str, sku_ids: tuple[str, ...]) -> None:
        self._bundles[bundle_id] = sku_ids
    def get_bundle(self, bundle_id: str) -> BundleView:
        cached = self._cache.get(bundle_id)
        if cached is not None:
            return cached
        sku_ids = self._bundles[bundle_id]
        total = sum(self._skus[s].price_cents for s in sku_ids)
        view = BundleView(bundle_id=bundle_id, sku_ids=sku_ids, total_cents=total)
        self._cache.put(view)
        return view
