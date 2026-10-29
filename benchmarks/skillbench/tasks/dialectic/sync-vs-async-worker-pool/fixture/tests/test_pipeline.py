import unittest
from ingestpool.pipeline import BatchIngestor

class PipelineTest(unittest.TestCase):
    def test_process_all(self) -> None:
        seen = []
        ing = BatchIngestor(lambda i, d: seen.append((i, d)) or True, workers=2)
        digests = ing.process_all([b'{"id": "doc-1"}'])
        self.assertEqual(len(digests), 1)
