import json
import sqlite3
import unittest
try:
    from .persona_chat_v6 import send_message, history
except ImportError:
    from persona_chat_v6 import send_message, history

class PersonaChatTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE people(id INTEGER PRIMARY KEY,name TEXT,simulated INTEGER)")
        self.db.execute("INSERT INTO people VALUES(1,'Beril',1)")
        self.db.execute("CREATE TABLE person_personas(person_id INTEGER PRIMARY KEY,profile_json TEXT)")
        self.db.execute("INSERT INTO person_personas VALUES(1,?)",(json.dumps({"preferred_genres":["bilim kurgu"],"traits":{"competitiveness":90,"humor":80},"speaking_style":"samimi"}),))
    def tearDown(self):self.db.close()
    def test_personality_and_memory(self):
        r=send_message(self.db,"owner",1,"Bana kitap öner")
        self.assertIn("bilim kurgu",r["reply"])
        self.assertIn("yarışması",r["reply"])
        self.assertEqual(len(history(self.db,"owner",1)),2)
        self.assertEqual(history(self.db,"other",1),[])
    def test_no_unsupported_photo_claim(self):
        r=send_message(self.db,"owner",1,"Bana fotoğraf gönder")
        self.assertIn("Gerçek bir fotoğraf çekmiyorum",r["reply"])
    def test_invalid_messages(self):
        with self.assertRaises(ValueError):send_message(self.db,"owner",1,"")
        with self.assertRaises(ValueError):send_message(self.db,"owner",2,"Merhaba")

if __name__=="__main__":unittest.main()
