import os
import tempfile
import unittest

import people_engine
from social_engine import simulate_day, relations


class SocialEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.tmp.name, "test.sqlite3")
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.tmp.cleanup()

    def test_social_day_idempotent(self):
        first = simulate_day(self.db, "2026-11-18")
        self.assertEqual(simulate_day(self.db, "2026-11-18")["created"], 0)
        self.assertEqual(first["created"],
                         self.db.execute("SELECT COUNT(*) FROM social_events").fetchone()[0])

    def test_relationships_are_symmetric(self):
        simulate_day(self.db, "2026-11-18")
        for a in range(1, 11):
            for r in relations(self.db, a):
                b = r["person_id"]
                reverse = [x for x in relations(self.db, b) if x["person_id"] == a]
                self.assertEqual(len(reverse), 1)
                self.assertEqual(reverse[0]["closeness"], r["closeness"])
                self.assertTrue(r["simulated"])

    def test_social_activity_does_not_change_books(self):
        simulate_day(self.db, "2026-11-18")
        self.assertEqual(self.db.execute("SELECT SUM(books),SUM(minutes) FROM people").fetchone(), (0,0))


if __name__ == "__main__":
    unittest.main()
