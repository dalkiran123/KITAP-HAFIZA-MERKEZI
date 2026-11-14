import unittest
from unittest.mock import patch
from sessions import SessionManager

class SessionTests(unittest.TestCase):
    def test_issue_lookup_and_revoke(self):
        s=SessionManager()
        token=s.issue(7)
        self.assertEqual(s.lookup(token),{'user_id':7,'role':'reader'})
        self.assertIsNone(s.lookup('not-a-token'))
        s.revoke(token)
        self.assertIsNone(s.lookup(token))
    def test_expiry(self):
        s=SessionManager()
        with patch('sessions.time.time',return_value=100):
            token=s.issue(1)
        with patch('sessions.time.time',return_value=100+12*3600):
            self.assertIsNone(s.lookup(token))
    def test_no_plaintext_token_in_store(self):
        s=SessionManager()
        token=s.issue(1)
        self.assertNotIn(token,s._sessions)

if __name__=='__main__': unittest.main()
