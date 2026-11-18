"""WSGI API contract tests."""
import json
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
try:
    from .persistent_social import tick
    from .social_feed_api import application
except ImportError:
    from persistent_social import tick
    from social_feed_api import application


class ApiTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        db = sqlite3.connect(self.path)
        db.execute("CREATE TABLE people(id INTEGER PRIMARY KEY,name TEXT,simulated INTEGER)")
        db.executemany("INSERT INTO people VALUES(?,?,1)", [(i, f"Bot {i}") for i in range(1,11)])
        tick(db, "2026-11-18T19:00:00+00:00")
        db.close()

    def tearDown(self):
        os.unlink(self.path)

    def request(self, method="GET", path="/api/people/social-feed"):
        status = []
        def start_response(code, headers):
            status.append((code, dict(headers)))
        with patch.dict(os.environ, {"BOOKCENTER_PEOPLE_DB": self.path}):
            body = b"".join(application({"REQUEST_METHOD": method, "PATH_INFO": path}, start_response))
        return status[0], json.loads(body)

    def test_read_feed(self):
        status, data = self.request()
        self.assertTrue(status[0].startswith("200"))
        self.assertEqual(len(data["posts"]), 1)
        self.assertTrue(data["posts"][0]["simulated"])

    def test_reject_writes(self):
        status, data = self.request("POST")
        self.assertTrue(status[0].startswith("405"))

    def test_unknown_path(self):
        status, data = self.request(path="/other")
        self.assertTrue(status[0].startswith("404"))


if __name__ == "__main__":
    unittest.main()
