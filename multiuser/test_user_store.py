import unittest
from user_store import connect,create_user,authenticate,rate_book

class StoreTests(unittest.TestCase):
    def setUp(self): self.db=connect(':memory:')
    def tearDown(self): self.db.close()
    def test_login_and_isolation(self):
        a=create_user(self.db,'admin','a secure password',role='admin')
        b=create_user(self.db,'reader','another password')
        self.assertEqual(authenticate(self.db,'admin','a secure password')['role'],'admin')
        self.assertIsNone(authenticate(self.db,'admin','wrong password'))
        rate_book(self.db,a,'book-1',10)
        rate_book(self.db,b,'book-1',3)
        self.assertEqual(self.db.execute('SELECT score FROM ratings WHERE user_id=?',(a,)).fetchone()[0],10)
        self.assertEqual(self.db.execute('SELECT score FROM ratings WHERE user_id=?',(b,)).fetchone()[0],3)
    def test_capacity(self):
        for i in range(100): create_user(self.db,f'user{i:03}','strong password')
        with self.assertRaises(ValueError): create_user(self.db,'extra','strong password')
    def test_duplicate_case_insensitive(self):
        create_user(self.db,'Reader','strong password')
        with self.assertRaises(Exception): create_user(self.db,'reader','strong password')
    def test_rating_validation(self):
        u=create_user(self.db,'reader','strong password')
        with self.assertRaises(ValueError): rate_book(self.db,u,'x',11)

if __name__=='__main__': unittest.main()
