import unittest
from proxyguard.client import UpstreamClient

class UpstreamClientTest(unittest.TestCase):
    def test_primary_call(self) -> None:
        client = UpstreamClient(lambda k: f'val:{k}')
        resp = client.call('abc')
        self.assertEqual(resp.endpoint, 'primary')
        self.assertEqual(resp.payload, 'val:abc')
