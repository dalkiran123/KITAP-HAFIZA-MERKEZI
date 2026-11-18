import os
import sqlite3
import tempfile
import unittest

import people_engine
from people_backup import backup, verify


class PeopleBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.source = os.path.join(self.temp.name, "people.sqlite3")
        self.backups = os.path.join(self.temp.name, "backups")
        os.mkdir(self.backups)
        self.old = people_engine.DB
        people_engine.DB = self.source
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB = self.old
        self.temp.cleanup()

    def test_backup_is_consistent_and_isolated(self):
        people_engine.tick(self.db)
        before = self.db.execute("SELECT COUNT(*) FROM activity").fetchone()[0]
        report = backup(self.source, self.backups)
        self.assertTrue(report["valid"])
        self.assertEqual(report["simulated_people"],10)
        self.assertEqual(len(report["sha256"]),64)
        with sqlite3.connect(report["path"]) as restored:
            self.assertEqual(restored.execute("SELECT COUNT(*) FROM activity").fetchone()[0],before)
        self.assertTrue(verify(report["path"])["valid"])
        self.assertEqual(os.listdir(self.backups),[os.path.basename(report["path"])])

    def test_missing_and_invalid_backup_are_rejected(self):
        with self.assertRaises(ValueError):
            verify(os.path.join(self.temp.name,"missing.sqlite3"))
        bad = os.path.join(self.backups,"bad.sqlite3")
        with open(bad,"wb") as f:
            f.write(b"not a sqlite database")
        with self.assertRaises(sqlite3.DatabaseError):
            verify(bad)

    def test_backup_requires_separate_directory(self):
        with self.assertRaises(ValueError):
            backup(self.source, self.temp.name)


if __name__ == "__main__":
    unittest.main()
