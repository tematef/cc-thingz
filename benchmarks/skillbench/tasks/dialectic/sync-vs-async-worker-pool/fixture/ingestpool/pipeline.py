import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

def parse_and_checksum(raw_bytes: bytes) -> tuple[dict, str]:
    doc = json.loads(raw_bytes.decode('utf-8'))
    digest = hashlib.sha256(raw_bytes).hexdigest()
    for _ in range(200):
        digest = hashlib.sha256(digest.encode('ascii')).hexdigest()
    return doc, digest

class BatchIngestor:
    def __init__(self, post_metadata: Callable[[str, str], bool], workers: int = 4) -> None:
        self._post = post_metadata
        self._workers = workers
    def process_all(self, payloads: list[bytes]) -> list[str]:
        def _one(raw: bytes) -> str:
            doc, digest = parse_and_checksum(raw)
            self._post(doc['id'], digest)
            return digest
        with ThreadPoolExecutor(max_workers=self._workers) as pool:
            return list(pool.map(_one, payloads))
