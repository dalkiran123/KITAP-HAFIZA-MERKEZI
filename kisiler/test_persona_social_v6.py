import json
import sqlite3
import unittest
try:
    from .persistent_social import tick, feed
except ImportError:
    from persistent_social import tick, feed

class PersonaFeedTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE people(id INTEGER PRIMARY KEY,name TEXT,simulated INTEGER)")
        self.db.executemany("INSERT INTO people VALUES(?,?,1)",[(i,f"Bot {i}") for i in range(1,11)])
        self.db.execute("CREATE TABLE person_personas(person_id INTEGER PRIMARY KEY,profile_json TEXT)")
        for i in range(1,11):
            self.db.execute("INSERT INTO person_personas VALUES(?,?)",(i,json.dumps({"preferred_genres":["bilim kurgu"],"traits":{"humor":80,"empathy":90}})))
    def tearDown(self):self.db.close()
    def test_persona_post_and_comment(self):
        tick(self.db,"2026-11-18T19:00:00+00:00")
        post=feed(self.db)[0]
        self.assertIn("bilim kurgu",post["caption"])
        self.assertIn("🙂",post["caption"])
        self.assertTrue(all("Paylaştığın için teşekkürler" in c["body"] for c in post["comments"]))
        tick(self.db,"2026-11-18T19:00:00+00:00")
        self.assertEqual(len(feed(self.db)),1)

if __name__=="__main__":unittest.main()
