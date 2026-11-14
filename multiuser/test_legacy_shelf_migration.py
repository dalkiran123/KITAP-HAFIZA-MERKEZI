"""Regression tests for non-destructive legacy shelf migration."""
import json
import unittest

from user_store import connect, create_user
from shelves import ensure_shelves, list_books, save_book
from shelf_sync import read_sync, update_sync


class LegacyShelfMigrationTests(unittest.TestCase):
    def setUp(self):
        self.db = connect(':memory:')
        self.alice = create_user(self.db, 'alice', 'a secure long password')
        self.bobby = create_user(self.db, 'bobby', 'another secure password')
        self.db.execute("""CREATE TABLE shelves(
            user_id INTEGER NOT NULL, book_id TEXT NOT NULL,
            state_json TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id,book_id))""")
        self.db.execute('INSERT INTO shelves(user_id,book_id,state_json) VALUES(?,?,?)',
                        (self.alice, 'classic', json.dumps({'notes':'original','done':True})))
        self.db.execute('INSERT INTO shelves(user_id,book_id,state_json) VALUES(?,?,?)',
                        (self.bobby, 'classic', json.dumps({'notes':'other account'})))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_import_preserves_both_accounts_and_legacy_table(self):
        ensure_shelves(self.db)
        self.assertEqual(read_sync(self.db,self.alice)[0]['state']['notes'],'original')
        self.assertEqual(read_sync(self.db,self.bobby)[0]['state']['notes'],'other account')
        self.assertEqual(list_books(self.db,self.alice)[0]['state']['done'],True)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM shelves').fetchone()[0],2)
        ensure_shelves(self.db)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM shelf_sync').fetchone()[0],2)

    def test_newer_sync_value_never_overwritten_by_legacy(self):
        ensure_shelves(self.db)
        self.assertEqual(update_sync(self.db,self.alice,'classic',{'notes':'new device'},1),2)
        ensure_shelves(self.db)
        self.assertEqual(read_sync(self.db,self.alice)[0]['state']['notes'],'new device')
        self.assertEqual(read_sync(self.db,self.alice)[0]['revision'],2)
        self.assertEqual(self.db.execute('SELECT state_json FROM shelves WHERE user_id=?',
                                         (self.alice,)).fetchone()[0],
                         json.dumps({'notes':'original','done':True}))

    def test_direct_sync_read_imports_legacy_without_facade(self):
        books = read_sync(self.db, self.alice)
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]['state']['notes'], 'original')
        self.assertEqual(read_sync(self.db, self.bobby)[0]['state']['notes'], 'other account')

    def test_direct_sync_write_rejects_overwriting_legacy_revision_zero(self):
        with self.assertRaisesRegex(ValueError, 'Revision conflict'):
            update_sync(self.db, self.alice, 'classic', {'notes':'stale'}, 0)
        self.assertEqual(read_sync(self.db, self.alice)[0]['state']['notes'], 'original')

    def test_legacy_save_uses_canonical_store(self):
        ensure_shelves(self.db)
        save_book(self.db,self.alice,'classic',{'notes':'compatibility'})
        self.assertEqual(read_sync(self.db,self.alice)[0]['revision'],2)
        self.assertEqual(list_books(self.db,self.alice)[0]['state']['notes'],'compatibility')


if __name__ == '__main__':
    unittest.main()
