"""Regression tests for persistent social state."""
import sqlite3
import unittest
try:
    from .persistent_social import tick, feed
except ImportError:
    from persistent_social import tick, feed


class SocialTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE people(id INTEGER PRIMARY KEY,name TEXT,simulated INTEGER)")
        self.db.executemany("INSERT INTO people VALUES(?,?,1)", [(i, f"Bot {i}") for i in range(1,11)])

    def tearDown(self):
        self.db.close()

    def test_idempotent_hour(self):
        slot = "2026-11-18T19:00:00+00:00"
        first = tick(self.db, slot)
        second = tick(self.db, slot)
        self.assertEqual(first["posts"], 1)
        self.assertEqual(second["posts"], 0)
        self.assertEqual(second["comments"], 0)
        self.assertEqual(second["likes"], 0)
        self.assertEqual(len(feed(self.db)), 1)
        self.assertTrue(feed(self.db)[0]["simulated"])

    def test_new_hour_persists(self):
        tick(self.db, "2026-11-18T19:00:00+00:00")
        tick(self.db, "2026-11-18T20:00:00+00:00")
        self.assertEqual(len(feed(self.db)), 2)

    def test_no_people(self):
        self.db.execute("DELETE FROM people")
        self.assertEqual(tick(self.db, "2026-11-18T19:00:00+00:00")["posts"], 0)


if __name__ == "__main__":
    unittest.main()
