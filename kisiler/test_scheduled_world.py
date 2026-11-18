import os
import tempfile
import unittest
from unittest.mock import patch

import scheduled_world


class ScheduledWorldTests(unittest.TestCase):
    def test_requires_explicit_database_path(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(scheduled_world.main(), 2)

    def test_requires_initialized_database(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"BOOKCENTER_PEOPLE_DB":os.path.join(folder,"missing.sqlite3")}):
                self.assertEqual(scheduled_world.main(), 2)

    def test_rejects_mismatched_database_path(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder,"people.sqlite3")
            open(path,"wb").close()
            with patch.dict(os.environ, {"BOOKCENTER_PEOPLE_DB":path}):
                with patch.object(scheduled_world.people_engine, "DB", os.path.join(folder,"other.sqlite3")):
                    self.assertEqual(scheduled_world.main(), 2)
            self.assertFalse(os.path.exists(path + ".runner.lock"))

    def test_does_not_override_existing_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder,"people.sqlite3")
            open(path,"wb").close()
            lock = path + ".runner.lock"
            with open(lock,"w") as f:
                f.write("existing")
            with patch.dict(os.environ, {"BOOKCENTER_PEOPLE_DB":path}):
                self.assertEqual(scheduled_world.main(), 3)
            with open(lock) as f:
                self.assertEqual(f.read(),"existing")


if __name__ == "__main__":
    unittest.main()
