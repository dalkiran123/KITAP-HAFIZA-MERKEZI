import os
import tempfile
import unittest

import people_engine
from persona_import import import_profiles
from persona_engine import get_persona


class PersonaImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = people_engine.DB
        people_engine.DB = os.path.join(self.temp.name,"people.sqlite3")
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.temp.cleanup()

    def test_import_is_persistent(self):
        result = import_profiles(self.db, {"characters":[{"id":1,"name":"Luna Yeni",
            "occupation":"Öğretmen","interests":["roman","bilim"],"background":"Kurgusal geçmiş"}]})
        self.assertEqual(result["imported"],1)
        self.assertEqual(self.db.execute("SELECT name FROM people WHERE id=1").fetchone()[0],"Luna Yeni")
        self.assertEqual(get_persona(self.db,1)["interests"],["roman","bilim"])

    def test_invalid_batch_changes_nothing(self):
        with self.assertRaises(ValueError):
            import_profiles(self.db,{"characters":[{"id":1,"name":"Yeni"},
                {"id":2,"name":"Atlas","interests":"not a list"}]})
        self.assertEqual(self.db.execute("SELECT name FROM people WHERE id=1").fetchone()[0],"Luna")

    def test_import_preserves_existing_traits(self):
        from persona_engine import set_persona
        set_persona(self.db,1,{"traits":{"curiosity":91,"empathy":50,"humor":50,
            "competitiveness":50,"sociability":50,"patience":50},
            "daily_reading_goal_minutes":75})
        import_profiles(self.db,{"characters":[{"id":1,"name":"Luna",
            "occupation":"Mimar"}]})
        persona=get_persona(self.db,1)
        self.assertEqual(persona["traits"]["curiosity"],91)
        self.assertEqual(persona["daily_reading_goal_minutes"],75)
        self.assertEqual(persona["occupation"],"Mimar")

    def test_duplicate_id_rejected(self):
        with self.assertRaises(ValueError):
            import_profiles(self.db,{"characters":[{"id":1,"name":"A"},{"id":1,"name":"B"}]})


if __name__ == "__main__":
    unittest.main()
