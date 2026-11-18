import hashlib
import hmac
import json
import tempfile
import unittest
from pathlib import Path
from bot_server.api import handle_tick

class BotApiTests(unittest.TestCase):
    def test_auth_and_replay(self):
        secret = "s" * 40
        body = json.dumps({"tick_id": "00000000-0000-0000-0000-000000000001",
                           "bots": {f"bot-{i:02d}": {"xp": i} for i in range(1,11)}}).encode()
        timestamp = 1795000000
        signature = hmac.new(secret.encode(), str(timestamp).encode()+b"."+body, hashlib.sha256).hexdigest()
        headers = {"x-bot-timestamp": str(timestamp), "x-bot-signature": signature}
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp)/"bots.sqlite3")
            self.assertEqual(handle_tick("POST", "/api/bots/tick", {}, body, secret=secret, database=db, now=timestamp)[0], 401)
            self.assertEqual(handle_tick("POST", "/api/bots/tick", headers, body, secret=secret, database=db, now=timestamp)[0], 201)
            status, result = handle_tick("POST", "/api/bots/tick", headers, body, secret=secret, database=db, now=timestamp)
            self.assertEqual(status, 200)
            self.assertTrue(result["duplicate"])
            self.assertEqual(handle_tick("POST", "/api/bots/tick", headers, body, secret=secret, database=db, now=timestamp+301)[0], 401)
