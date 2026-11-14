import unittest
from user_store import connect,create_user
from shelf_sync import read_sync,update_sync

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(':memory:')
        self.a=create_user(self.db,'alice','a secure long password')
        self.b=create_user(self.db,'bobby','another secure password')
    def tearDown(self): self.db.close()
    def test_conflict_prevents_lost_updates(self):
        self.assertEqual(update_sync(self.db,self.a,'b1',{'notes':'phone'},0),1)
        self.assertEqual(update_sync(self.db,self.a,'b1',{'notes':'tablet'},1),2)
        with self.assertRaisesRegex(ValueError,'Revision conflict'):
            update_sync(self.db,self.a,'b1',{'notes':'stale phone'},1)
        self.assertEqual(read_sync(self.db,self.a)[0]['state']['notes'],'tablet')
    def test_account_isolation(self):
        update_sync(self.db,self.a,'b1',{'done':True},0)
        self.assertEqual(read_sync(self.db,self.b),[])
        self.assertEqual(update_sync(self.db,self.b,'b1',{'done':False},0),1)
        self.assertEqual(read_sync(self.db,self.a)[0]['state']['done'],True)
    def test_invalid_revision(self):
        with self.assertRaises(ValueError):
            update_sync(self.db,self.a,'b1',{},-1)

if __name__=='__main__': unittest.main()
