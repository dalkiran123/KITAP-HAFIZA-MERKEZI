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

    def test_invalid_body_and_conflicting_replay(self):
        secret = "s" * 40
        stamp = 1795000000
        def signed(body):
            return {"x-bot-timestamp": str(stamp),
                    "x-bot-signature": hmac.new(secret.encode(), str(stamp).encode()+b"."+body, hashlib.sha256).hexdigest()}
        payload = {"tick_id": "00000000-0000-0000-0000-000000000002",
                   "bots": {f"bot-{i:02d}": {"xp": i} for i in range(1, 11)}}
        body = json.dumps(payload).encode()
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp)/"bots.sqlite3")
            self.assertEqual(handle_tick("POST", "/api/bots/tick", signed(body), body, secret=secret, database=db, now=stamp)[0], 201)
            changed = json.dumps({**payload, "bots": {**payload["bots"], "bot-01": {"xp": 999}}}).encode()
            self.assertEqual(handle_tick("POST", "/api/bots/tick", signed(changed), changed, secret=secret, database=db, now=stamp)[0], 409)
            self.assertEqual(handle_tick("POST", "/api/bots/tick", signed(b"not-json"), b"not-json", secret=secret, database=db, now=stamp)[0], 400)
            self.assertEqual(handle_tick("POST", "/api/bots/tick", signed(b""), b"", secret=secret, database=db, now=stamp)[0], 413)
            self.assertEqual(handle_tick("POST", "/api/bots/tick", signed(body), body, secret="", database=db, now=stamp)[0], 503)
