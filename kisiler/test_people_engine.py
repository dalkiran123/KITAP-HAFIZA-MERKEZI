import datetime as dt
import os
import tempfile
import unittest
from unittest.mock import patch

import people_engine as engine


class PeopleEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = engine.DB
        engine.DB = os.path.join(self.tmp.name, "people.sqlite3")
        self.db = engine.connect()

    def tearDown(self):
        self.db.close()
        engine.DB = self.old
        self.tmp.cleanup()

    def test_creates_exactly_ten_distinct_simulated_people(self):
        people = engine.status(self.db)
        self.assertEqual(len(people), 10)
        self.assertEqual(len({p["id"] for p in people}), 10)
        self.assertTrue(all(p["simulated"] for p in people))

    def test_hour_is_idempotent_and_persistent(self):
        when = dt.datetime(2026, 11, 18, 9, tzinfo=dt.timezone.utc)
        first = engine.tick(self.db, when)
        before = engine.status(self.db)
        second = engine.tick(self.db, when)
        self.assertGreaterEqual(first["new"], 2)
        self.assertEqual(second["new"], 0)
        self.assertEqual(before, engine.status(self.db))
        self.assertEqual(self.db.execute("SELECT count(*) FROM engine_ticks").fetchone()[0], 1)
        self.db.close()
        self.db = engine.connect()
        self.assertEqual(before, engine.status(self.db))

    def test_new_hour_adds_activity_without_match_points(self):
        a = dt.datetime(2026, 11, 18, 9, tzinfo=dt.timezone.utc)
        b = a + dt.timedelta(hours=1)
        engine.tick(self.db, a)
        engine.tick(self.db, b)
        self.assertEqual(self.db.execute("SELECT count(*) FROM engine_ticks").fetchone()[0], 2)
        self.assertGreaterEqual(self.db.execute("SELECT count(*) FROM activity").fetchone()[0], 4)
        self.assertGreater(sum(p["minutes"] for p in engine.status(self.db)), 0)


if __name__ == "__main__":
    unittest.main()
