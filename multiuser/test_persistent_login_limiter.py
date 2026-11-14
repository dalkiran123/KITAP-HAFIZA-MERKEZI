import os
import tempfile
import unittest
from unittest.mock import patch
from login_limiter import LoginLimiter


class PersistentLoginLimiterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.tmp.name,'users.sqlite3')

    def tearDown(self):
        self.tmp.cleanup()

    def test_limits_survive_new_instance_and_are_per_ip(self):
        first=LoginLimiter(self.path)
        for _ in range(5):
            first.fail('192.0.2.1')
        second=LoginLimiter(self.path)
        self.assertFalse(second.allowed('192.0.2.1'))
        self.assertTrue(second.allowed('192.0.2.2'))
        second.success('192.0.2.1')
        self.assertTrue(first.allowed('192.0.2.1'))

    def test_expiry(self):
        with patch('login_limiter.time.time',return_value=100):
            limiter=LoginLimiter(self.path)
            for _ in range(5):
                limiter.fail('192.0.2.1')
            self.assertFalse(limiter.allowed('192.0.2.1'))
        with patch('login_limiter.time.time',return_value=401):
            self.assertTrue(LoginLimiter(self.path).allowed('192.0.2.1'))


if __name__=='__main__':
    unittest.main()
