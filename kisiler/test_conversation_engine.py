import os
import tempfile
import unittest

import people_engine
from social_engine import ensure_schema as ensure_social
from conversation_engine import simulate_day, conversations


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.tmp.name, "test.sqlite3")
        self.db = people_engine.connect()
        ensure_social(self.db)
        with self.db:
            self.db.execute("INSERT INTO social_relations(person_a,person_b,status,closeness,updated_day) VALUES(1,2,'friends',90,'2026-11-17')")

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.tmp.cleanup()

    def test_conversation_is_repeatable_and_bidirectional(self):
        count = 0
        for day in range(1,31):
            count += simulate_day(self.db, f"2026-11-{day:02d}")["created"]
        self.assertGreater(count, 0)
        self.assertEqual(simulate_day(self.db, "2026-11-18")["created"],0)
        a = conversations(self.db,1,100)
        b = conversations(self.db,2,100)
        self.assertEqual(len(a),len(b))
        self.assertTrue(all(m["simulated"] for m in a))
        self.assertTrue(all(m["other_id"]==2 for m in a))

    def test_no_unrelated_person_messages(self):
        simulate_day(self.db, "2026-11-18")
        self.assertEqual(conversations(self.db,3),[])


if __name__ == "__main__":
    unittest.main()
