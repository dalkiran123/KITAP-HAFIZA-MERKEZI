import os
import tempfile
import unittest

import people_engine
from life_continuity import ensure_schema, simulate_day, get_state, history, choices


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.tmp.name, "test.sqlite3")
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.tmp.cleanup()

    def test_transition_choices_follow_existing_state(self):
        self.assertIn("job_change", [x[0] for x in choices({"career":"employed","home":"settled","education":"none","social":"stable","finance":"stable","family":"stable"})])
        self.assertNotIn("job_change", [x[0] for x in choices({"career":"new_job","home":"new_home","education":"studying","social":"stable","finance":"planning","family":"stable"})])
        self.assertIn("job_settled", [x[0] for x in choices({"career":"new_job","home":"new_home","education":"studying","social":"stable","finance":"planning","family":"stable"})])

    def test_no_duplicate_day_and_history_consistency(self):
        first = simulate_day(self.db,"2026-11-18")
        self.assertEqual(simulate_day(self.db,"2026-11-18")["created"],0)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM life_world_events").fetchone()[0],first["created"])
        for pid in range(1,11):
            for event in history(self.db,pid):
                self.assertNotEqual(event["before"],event["after"])
                self.assertTrue(event["simulated"])
            self.assertIn("career",get_state(self.db,pid))

    def test_older_day_does_not_rewind_state(self):
        simulate_day(self.db,"2026-11-18")
        before = [get_state(self.db,pid) for pid in range(1,11)]
        simulate_day(self.db,"2026-11-17")
        self.assertEqual(before,[get_state(self.db,pid) for pid in range(1,11)])


if __name__ == "__main__":
    unittest.main()
