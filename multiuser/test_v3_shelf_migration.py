import os
import tempfile
import unittest
from user_store import connect, create_user
from import_backup import import_backup
from shelf_sync import read_sync, update_sync


class V3ShelfMigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=connect(os.path.join(self.tmp.name,'users.sqlite3'))
        self.uid=create_user(self.db,'readerone','a secure long password')
        self.payload={'version':3,'books':[
            {'id':'novel','name':'Novel','author':'Author','summary':'Summary',
             'notes':'my original note','read':True,'done':True,'rating':9},
            {'id':'other','name':'Other','author':'Author','summary':'Summary',
             'notes':'other note','listened':True}]}

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_notes_flags_and_ratings_import_without_duplicates(self):
        result=import_backup(self.db,self.uid,self.payload,confirmed=True)
        self.assertEqual(result['status'],'imported')
        books={row['book_id']:row for row in read_sync(self.db,self.uid)}
        self.assertEqual(books['novel']['state']['notes'],'my original note')
        self.assertTrue(books['novel']['state']['done'])
        self.assertTrue(books['other']['state']['listened'])
        self.assertEqual(self.db.execute('SELECT score FROM ratings WHERE user_id=? AND book_id=?',
                                         (self.uid,'novel')).fetchone()[0],9)
        self.assertEqual(import_backup(self.db,self.uid,self.payload,confirmed=True)['status'],'already_imported')
        self.assertEqual(len(read_sync(self.db,self.uid)),2)

    def test_import_never_overwrites_newer_device_edit(self):
        update_sync(self.db,self.uid,'novel',{'notes':'new device note'},0)
        import_backup(self.db,self.uid,self.payload,confirmed=True)
        books={row['book_id']:row for row in read_sync(self.db,self.uid)}
        self.assertEqual(books['novel']['state']['notes'],'new device note')
        self.assertEqual(books['novel']['revision'],1)

    def test_confirmation_required(self):
        with self.assertRaises(ValueError):
            import_backup(self.db,self.uid,self.payload)
        self.assertEqual(read_sync(self.db,self.uid),[])


if __name__=='__main__':
    unittest.main()
