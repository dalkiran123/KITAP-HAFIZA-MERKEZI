import io
import json
import os
import tempfile
import unittest
import web_app


class CanonicalShelfAPITests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        web_app.DB_PATH = os.path.join(self.tmp.name, 'users.sqlite3')
        web_app.SESSIONS = web_app.SessionManager()

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, method, path, data=None, cookie=''):
        body = json.dumps(data).encode() if data is not None else b''
        result = {}

        def start(status, headers):
            result['code'] = int(status.split()[0])
            result['headers'] = dict(headers)

        payload = b''.join(web_app.app({
            'REQUEST_METHOD': method, 'PATH_INFO': path,
            'CONTENT_LENGTH': str(len(body)), 'wsgi.input': io.BytesIO(body),
            'HTTP_COOKIE': cookie,
          'HTTP_X_CSRF_TOKEN': web_app.csrf_for(cookie.split('=',1)[1]) if cookie.startswith('session=') else ''}, start))
        return result['code'], json.loads(payload), result['headers']

    def test_legacy_and_revisioned_reads_share_one_record(self):
        _, _, headers = self.call('POST', '/register', {
            'username': 'alice', 'password': 'a secure long password'})
        cookie = headers['Set-Cookie'].split(';')[0]
        self.assertEqual(self.call('POST', '/my/books', {
            'book_id': 'b1', 'state': {'notes': 'first'}}, cookie)[0], 200)
        sync = self.call('GET', '/my/sync', cookie=cookie)[1]['books']
        self.assertEqual(sync[0]['revision'], 1)
        self.assertEqual(sync[0]['state']['notes'], 'first')
        self.assertEqual(self.call('POST', '/my/sync', {
            'book_id': 'b1', 'state': {'notes': 'second'},
            'expected_revision': 1}, cookie)[1]['revision'], 2)
        books = self.call('GET', '/my/books', cookie=cookie)[1]['books']
        self.assertEqual(len(books), 1)
        self.assertEqual(books[0]['state']['notes'], 'second')
        self.assertEqual(self.call('POST', '/my/sync', {
            'book_id': 'b1', 'state': {'notes': 'stale'},
            'expected_revision': 1}, cookie)[0], 409)
        self.assertEqual(self.call('GET', '/my/books', cookie=cookie)[1]['books'][0]['state']['notes'], 'second')


if __name__ == '__main__':
    unittest.main()
