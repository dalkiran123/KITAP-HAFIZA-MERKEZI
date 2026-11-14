import unittest
from user_store import connect, create_user, rate_book, leaderboard

class IsolationTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:')
    def tearDown(self):
        self.db.close()
    def test_separate_user_ratings(self):
        a=create_user(self.db,'alice','a secure long password')
        b=create_user(self.db,'bobby','another long password')
        rate_book(self.db,a,'abc',10)
        rate_book(self.db,b,'abc',3)
        self.assertEqual(self.db.execute('SELECT score FROM ratings WHERE user_id=? AND book_id=?',(a,'abc')).fetchone()[0],10)
        self.assertEqual(self.db.execute('SELECT score FROM ratings WHERE user_id=? AND book_id=?',(b,'abc')).fetchone()[0],3)
    def test_leaderboard_uses_distinct_books(self):
        a=create_user(self.db,'alice','a secure long password')
        b=create_user(self.db,'bobby','another long password')
        with self.db:
            self.db.execute('INSERT INTO reading(user_id,book_id,completed_at) VALUES(?,?,?)',(a,'abc','2026-11-14T12:00:00Z'))
            self.db.execute('INSERT INTO reading(user_id,book_id,completed_at) VALUES(?,?,?)',(a,'abc','2026-11-14T13:00:00Z'))
            self.db.execute('INSERT INTO reading(user_id,book_id,completed_at) VALUES(?,?,?)',(b,'xyz','2026-11-14T13:00:00Z'))
        self.assertEqual(dict(leaderboard(self.db)),{'alice':1,'bobby':1})

if __name__=='__main__': unittest.main()
