import unittest
from user_store import connect,create_user
from shelves import save_book,list_books

class ShelfTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:')
        self.a=create_user(self.db,'alice','a secure long password')
        self.b=create_user(self.db,'bobby','another secure password')
    def tearDown(self): self.db.close()
    def test_private_shelves(self):
        save_book(self.db,self.a,'book-1',{'done':True,'notes':'private'})
        save_book(self.db,self.b,'book-1',{'done':False,'notes':'different'})
        self.assertEqual(list_books(self.db,self.a)[0]['state']['notes'],'private')
        self.assertEqual(list_books(self.db,self.b)[0]['state']['notes'],'different')
    def test_upsert_and_validation(self):
        save_book(self.db,self.a,'book-1',{'read':False})
        save_book(self.db,self.a,'book-1',{'read':True})
        self.assertEqual(len(list_books(self.db,self.a)),1)
        self.assertTrue(list_books(self.db,self.a)[0]['state']['read'])
        with self.assertRaises(ValueError): save_book(self.db,self.a,'book-1',{'role':'admin'})
        with self.assertRaises(ValueError): save_book(self.db,self.a,'book-1',{'notes':'x'*40000})

if __name__=='__main__': unittest.main()
