import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import deploy_check
import people_engine


class DeployCheckTests(unittest.TestCase):
    def test_missing_and_relative_path(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertTrue(deploy_check.check())
        with patch.dict(os.environ,{"BOOKCENTER_PEOPLE_DB":"relative.db"}):
            self.assertTrue(deploy_check.check())

    def test_new_private_database_path_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ,{"BOOKCENTER_PEOPLE_DB":os.path.join(folder,"people.sqlite3")}):
                self.assertEqual(deploy_check.check(),[])

    def test_unrelated_existing_sqlite_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=os.path.join(folder,"unrelated.sqlite3")
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE books(id INTEGER)")
            with patch.dict(os.environ,{"BOOKCENTER_PEOPLE_DB":path}):
                self.assertTrue(deploy_check.check())

    def test_initialized_people_database_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=os.path.join(folder,"people.sqlite3")
            old=people_engine.DB
            try:
                people_engine.DB=path
                people_engine.connect().close()
                with patch.dict(os.environ,{"BOOKCENTER_PEOPLE_DB":path}):
                    self.assertEqual(deploy_check.check(),[])
            finally:
                people_engine.DB=old


if __name__=="__main__":
    unittest.main()
