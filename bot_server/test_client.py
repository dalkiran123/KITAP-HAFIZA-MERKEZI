import io
import json
import unittest
from datetime import datetime, timezone
from bot_server.client import make_payload, post_tick, signed_headers, next_tick_from_remote, deterministic_tick_id, plan_hourly_tick

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

    def test_remote_state_one_sequential_step(self):
        bots = {f"bot-{i:02d}": {"version": 7, "xp": 20+i} for i in range(1,11)}
        body = next_tick_from_remote(bots, tick_id="00000000-0000-0000-0000-000000000091")
        payload = json.loads(body)
        self.assertEqual(payload["bots"]["bot-01"], {"version": 8, "xp": 22})
        self.assertEqual(len(payload["bots"]), 10)

    def test_remote_state_initialization_and_partial_rejection(self):
        body = next_tick_from_remote({}, tick_id="00000000-0000-0000-0000-000000000092")
        self.assertEqual(json.loads(body)["bots"]["bot-10"]["version"], 1)
        with self.assertRaises(ValueError):
            next_tick_from_remote({"bot-01": {"version": 1, "xp": 1}},
                                  tick_id="00000000-0000-0000-0000-000000000093")

    def test_hourly_tick_id_is_stable(self):
        from datetime import timedelta
        hour = datetime(2026, 11, 18, 11, 2, tzinfo=timezone.utc)
        same_hour = hour + timedelta(minutes=40)
        later = hour + timedelta(hours=1)
        self.assertEqual(deterministic_tick_id(hour), deterministic_tick_id(same_hour))
        self.assertNotEqual(deterministic_tick_id(hour), deterministic_tick_id(later))
        with self.assertRaises(ValueError):
            deterministic_tick_id(datetime(2026, 11, 18))
        self.assertEqual(json.loads(plan_hourly_tick({}, hour))["tick_id"], deterministic_tick_id(hour))
