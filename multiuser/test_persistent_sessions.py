import os
import tempfile
import unittest
from unittest.mock import patch
from user_store import connect, create_user
from persistent_sessions import SQLiteSessionManager


class PersistentSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,'users.sqlite3')
        db=connect(self.path)
        self.uid=create_user(db,'alice','a secure long password')
        db.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_restart_reuses_session_and_revoke_is_shared(self):
        first=SQLiteSessionManager(self.path)
        token=first.issue(self.uid)
        second=SQLiteSessionManager(self.path)
        self.assertEqual(second.lookup(token),{'user_id':self.uid,'role':'reader'})
        second.revoke(token)
        self.assertIsNone(first.lookup(token))

    def test_expired_session_is_deleted(self):
        with patch('persistent_sessions.time.time',return_value=100):
            token=SQLiteSessionManager(self.path).issue(self.uid)
        with patch('persistent_sessions.time.time',return_value=100+12*3600):
            self.assertIsNone(SQLiteSessionManager(self.path).lookup(token))

    def test_only_digest_is_persisted(self):
        token=SQLiteSessionManager(self.path).issue(self.uid)
        db=connect(self.path)
        stored=db.execute('SELECT token_hash FROM login_sessions').fetchone()[0]
        db.close()
        self.assertNotEqual(token,stored)
        self.assertEqual(len(stored),64)


if __name__=='__main__':
    unittest.main()
