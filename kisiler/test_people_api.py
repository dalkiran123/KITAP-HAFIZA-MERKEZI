import json
import os
import tempfile
import unittest
from unittest.mock import patch

import people_api
import people_engine


def request(path, query="", method="GET"):
    result = {}
    def start_response(status, headers):
        result["status"] = status
        result["headers"] = dict(headers)
    body = b"".join(people_api.application(
        {"PATH_INFO": path, "QUERY_STRING": query, "REQUEST_METHOD": method}, start_response))
    result["body"] = json.loads(body)
    return result


class PeopleAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp.name, "people.sqlite3")
        self.old_engine_db, self.old_api_db = people_engine.DB, people_api.DB
        people_engine.DB = people_api.DB = self.db_path
        self.db = people_engine.connect()

    def tearDown(self):
        self.db.close()
        people_engine.DB, people_api.DB = self.old_engine_db, self.old_api_db
        self.temp.cleanup()

    def test_health(self):
        self.assertTrue(request("/api/people/health")["status"].startswith("200"))

    def test_league_has_ten_simulated_profiles(self):
        r = request("/api/people/league")
        self.assertTrue(r["status"].startswith("200"))
        self.assertEqual(r["body"]["source"], "simulated")
        self.assertEqual(len(r["body"]["people"]), 10)
        self.assertNotIn("messages", r["body"])

    def test_activity_requires_valid_person_id(self):
        self.assertTrue(request("/api/people/activity", "person_id=1")["status"].startswith("200"))
        for bad in ("person_id=0", "person_id=11", "person_id=abc", "person_id=1%20OR%201=1"):
            self.assertTrue(request("/api/people/activity", bad)["status"].startswith("400"))

    def test_read_only(self):
        self.assertTrue(request("/api/people/league", method="POST")["status"].startswith("405"))
        self.assertTrue(request("/api/people/unknown")["status"].startswith("404"))

    def test_missing_database(self):
        self.db.close()
        os.remove(self.db_path)
        self.assertTrue(request("/api/people/league")["status"].startswith("503"))
        self.db = people_engine.connect()


if __name__ == "__main__":
    unittest.main()
