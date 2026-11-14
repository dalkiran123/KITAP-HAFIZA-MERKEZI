import unittest
from user_store import connect,create_user
from reading_history import add_read,list_reads

class ReadingHistoryTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:')
        self.a=create_user(self.db,'alice','a secure long password')
        self.b=create_user(self.db,'bobby','another secure password')
    def tearDown(self): self.db.close()
    def test_user_isolation_and_repeat_safety(self):
        add_read(self.db,self.a,'novel','2026-11-14T12:00:00Z')
        add_read(self.db,self.a,'novel','2026-11-14T12:00:00Z')
        self.assertEqual(len(list_reads(self.db,self.a)),1)
        self.assertEqual(list_reads(self.db,self.b),[])
        add_read(self.db,self.b,'novel','2026-11-14T13:00:00Z')
        self.assertEqual(len(list_reads(self.db,self.b)),1)
    def test_invalid_timestamp(self):
        with self.assertRaises(ValueError): add_read(self.db,self.a,'novel','yesterday')
        with self.assertRaises(ValueError): add_read(self.db,self.a,'novel','2026-11-14T12:00:00')

if __name__=='__main__': unittest.main()
