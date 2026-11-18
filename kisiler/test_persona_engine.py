import os
import tempfile
import unittest

import people_engine
from persona_engine import get_persona, set_persona, validate


class PersonaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.tmp.name, "test.sqlite3")
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.tmp.cleanup()

    def test_profile_persists_without_affecting_reading(self):
        profile = validate({})
        profile["occupation"] = "Öğretmen"
        profile["traits"]["curiosity"] = 90
        set_persona(self.db, 1, profile)
        self.assertEqual(get_persona(self.db, 1)["occupation"], "Öğretmen")
        self.assertEqual(get_persona(self.db, 1)["traits"]["curiosity"], 90)
        self.assertEqual(self.db.execute("SELECT books FROM people WHERE id=1").fetchone()[0], 0)

    def test_reject_invalid_persona(self):
        with self.assertRaises(ValueError):
            set_persona(self.db, 1, {"traits": {"curiosity": 900}})
        with self.assertRaises(ValueError):
            set_persona(self.db, 999, {})
        with self.assertRaises(ValueError):
            validate({"unknown": "value"})

    def test_defaults_are_independent(self):
        a = get_persona(self.db, 1)
        a["traits"]["empathy"] = 0
        self.assertEqual(get_persona(self.db, 2)["traits"]["empathy"], 50)


if __name__ == "__main__":
    unittest.main()
