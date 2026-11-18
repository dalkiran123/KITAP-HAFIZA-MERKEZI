import io
import json
import unittest
from datetime import datetime, timezone
from bot_server.client import make_payload, post_tick, signed_headers

class ClientTests(unittest.TestCase):
    def test_ten_bots_and_signature(self):
        _, body = make_payload({}, datetime(2026,11,18,tzinfo=timezone.utc))
        payload = json.loads(body)
        self.assertEqual(len(payload["bots"]), 10)
        self.assertEqual(payload["bots"]["bot-01"]["version"], 1)
        self.assertEqual(len(signed_headers(body, "s"*40, 123)["X-Bot-Signature"]), 64)

    def test_rejects_non_https(self):
        with self.assertRaises(ValueError):
            post_tick("http://example.com/api/bots/tick", b"{}", "s"*40)

    def test_rejects_wrong_path(self):
        with self.assertRaises(ValueError):
            post_tick("https://example.com/health", b"{}", "s"*40)
