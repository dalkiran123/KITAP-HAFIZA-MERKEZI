import os
import tempfile
import unittest

import people_engine
from life_engine import simulate_day, timeline


class LifeEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.temp.name, "test.sqlite3")
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.temp.cleanup()

    def test_idempotent_day_and_person_isolation(self):
        first = simulate_day(self.db, "2026-11-18")
        self.assertTrue(first["simulated"])
        self.assertEqual(simulate_day(self.db, "2026-11-18")["created"], 0)
        count = self.db.execute("SELECT COUNT(*) FROM life_events").fetchone()[0]
        self.assertEqual(count, first["created"])
        self.assertLessEqual(count, 10)
        for person_id in range(1,11):
            self.assertTrue(all(e["simulated"] for e in timeline(self.db, person_id)))
            self.assertLessEqual(len(timeline(self.db, person_id)), 1)

    def test_reading_data_is_unchanged(self):
        simulate_day(self.db, "2026-11-18")
        self.assertEqual(self.db.execute("SELECT SUM(books),SUM(minutes) FROM people").fetchone(), (0,0))


if __name__ == "__main__":
    unittest.main()
