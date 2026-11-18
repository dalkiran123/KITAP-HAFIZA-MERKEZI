import os
import tempfile
import unittest

import people_engine
from world_runner import run


class WorldRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.tmp.name, "world.sqlite3")
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.tmp.cleanup()

    def test_world_runner_is_repeatable_without_duplicate_events(self):
        first = run(self.db)
        second = run(self.db)
        self.assertTrue(first["simulation"])
        self.assertGreater(first["reading"]["new"], 0)
        self.assertEqual(second["reading"]["new"], 0)
        self.assertEqual(second["life"]["created"], 0)
        self.assertEqual(len(first["evolution"]), 10)
        self.assertEqual(first["evolution"], second["evolution"])

    def test_world_does_not_generate_real_people(self):
        run(self.db)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM people WHERE simulated=0").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
