import sqlite3
import unittest
try:
 from .inbox_wsgi_v6 import unread,mark_read
except ImportError:
 from inbox_wsgi_v6 import unread,mark_read

class InboxTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:")
  self.db.execute("CREATE TABLE people(id INTEGER PRIMARY KEY,name TEXT,simulated INTEGER)")
  self.db.execute("INSERT INTO people VALUES(1,'Luna',1)")
  self.db.execute("""CREATE TABLE friend_direct_messages(
   id INTEGER PRIMARY KEY,user_id TEXT,person_id INTEGER,sender TEXT,body TEXT,created_at TEXT)""")
  self.db.executemany("INSERT INTO friend_direct_messages VALUES(?,?,?,?,?,?)",[
   (1,'u1',1,'bot','Selam!','2026-11-18T12:00:00+00:00'),
   (2,'u2',1,'bot','Özel mesaj','2026-11-18T12:01:00+00:00'),
   (3,'u1',1,'user','Merhaba','2026-11-18T12:02:00+00:00')])
 def tearDown(self):self.db.close()
 def test_private_unread_and_mark_read(self):
  items=unread(self.db,'u1')
  self.assertEqual(len(items),1)
  self.assertEqual(items[0]['body'],'Selam!')
  self.assertEqual(len(unread(self.db,'u2')),1)
  mark_read(self.db,'u1',1)
  self.assertEqual(unread(self.db,'u1'),[])
  self.assertEqual(len(unread(self.db,'u2')),1)
 def test_mark_read_idempotent(self):
  mark_read(self.db,'u1',1)
  mark_read(self.db,'u1',1)
  self.assertEqual(self.db.execute("SELECT count(*) FROM friend_dm_reads").fetchone()[0],1)
if __name__=='__main__':unittest.main()
