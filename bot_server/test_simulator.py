import unittest
from datetime import datetime, timezone, timedelta
from bot_server.simulator import advance

class SimulatorTests(unittest.TestCase):
    def test_initializes_ten_bots(self):
        result = advance({}, datetime(2026, 11, 18, tzinfo=timezone.utc))
        self.assertEqual(len(result["bots"]), 10)
        self.assertEqual(len(result["events"]), 10)

    def test_idempotent_at_same_time(self):
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        first = advance({}, now)
        second = advance(first, now)
        self.assertEqual(first, second)

    def test_elapsed_hours(self):
        now = datetime(2026, 11, 18, tzinfo=timezone.utc)
        initial = advance({}, now)
        later = advance(initial, now + timedelta(hours=3))
        self.assertEqual(len(later["events"]), 40)

    def test_rejects_naive_clock(self):
        with self.assertRaises(ValueError):
            advance({}, datetime(2026, 11, 18))
