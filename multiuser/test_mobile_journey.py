"""End-to-end WSGI regression for the mobile client API journey.

Exercises the exact routes used by mobile_client.js without requiring a
browser or changing the public GitHub Pages site.
"""
import io
import json
import os
import tempfile
import unittest

import web_app


class MobileJourneyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_path = web_app.DB_PATH
        self.original_sessions = web_app.SESSIONS
        web_app.DB_PATH = os.path.join(self.temp.name, 'mobile.sqlite3')
        web_app.SESSIONS = web_app.SessionManager()

    def tearDown(self):
        web_app.DB_PATH = self.original_path
        web_app.SESSIONS = self.original_sessions
        self.temp.cleanup()

    def call(self, method, path, data=None, cookie=''):
        raw = json.dumps(data).encode('utf-8') if data is not None else b''
        response = {}

        def start(status, headers):
            response['status'] = int(status.split()[0])
            response['headers'] = dict(headers)

        chunks = web_app.app({
            'REQUEST_METHOD': method, 'PATH_INFO': path,
            'CONTENT_LENGTH': str(len(raw)),
            'wsgi.input': io.BytesIO(raw),
            'HTTP_COOKIE': cookie,
        }, start)
        payload = b''.join(chunks)
        content_type = response['headers'].get('Content-Type', '')
        response['data'] = json.loads(payload) if 'application/json' in content_type else payload
        return response

    def test_registration_save_reload_conflict_logout_and_login(self):
        page = self.call('GET', '/mobile')
        self.assertEqual(page['status'], 200)
        self.assertIn(b'mobile_client.js', page['data'])

        first = self.call('POST', '/register', {
            'username': 'alice', 'password': 'a secure long password'})
        self.assertEqual(first['status'], 200)
        cookie = first['headers']['Set-Cookie'].split(';')[0]
        self.assertEqual(self.call('GET', '/me', cookie=cookie)['status'], 200)
        self.assertEqual(self.call('GET', '/my/sync', cookie=cookie)['data']['books'], [])

        created = self.call('POST', '/my/sync', {
            'book_id': 'classic', 'state': {'done': True, 'notes': 'iPhone'},
            'expected_revision': 0}, cookie)
        self.assertEqual(created['status'], 200)
        self.assertEqual(created['data']['revision'], 1)

        second_device = self.call('GET', '/my/sync', cookie=cookie)
        self.assertEqual(second_device['data']['books'][0]['state']['notes'], 'iPhone')

        updated = self.call('POST', '/my/sync', {
            'book_id': 'classic', 'state': {'done': True, 'notes': 'Android'},
            'expected_revision': 1}, cookie)
        self.assertEqual(updated['data']['revision'], 2)

        stale = self.call('POST', '/my/sync', {
            'book_id': 'classic', 'state': {'notes': 'stale iPhone'},
            'expected_revision': 1}, cookie)
        self.assertNotEqual(stale['status'], 200)
        self.assertEqual(self.call('GET', '/my/sync', cookie=cookie)
                         ['data']['books'][0]['state']['notes'], 'Android')

        self.assertEqual(self.call('POST', '/logout', {}, cookie)['status'], 200)
        self.assertEqual(self.call('GET', '/my/sync', cookie=cookie)['status'], 401)

        logged_in = self.call('POST', '/login', {
            'username': 'alice', 'password': 'a secure long password'})
        self.assertEqual(logged_in['status'], 200)
        new_cookie = logged_in['headers']['Set-Cookie'].split(';')[0]
        self.assertEqual(self.call('GET', '/my/sync', cookie=new_cookie)
                         ['data']['books'][0]['revision'], 2)

    def test_accounts_remain_private(self):
        a = self.call('POST', '/register', {
            'username': 'alice', 'password': 'a secure long password'})
        b = self.call('POST', '/register', {
            'username': 'bobby', 'password': 'another secure password'})
        ca = a['headers']['Set-Cookie'].split(';')[0]
        cb = b['headers']['Set-Cookie'].split(';')[0]
        self.call('POST', '/my/sync', {
            'book_id': 'secret', 'state': {'notes': 'private'},
            'expected_revision': 0}, ca)
        self.assertEqual(self.call('GET', '/my/sync', cookie=cb)['data']['books'], [])
        self.assertEqual(self.call('POST', '/my/sync', {
            'book_id': 'secret', 'state': {'notes': 'other user'},
            'expected_revision': 0}, cb)['status'], 200)
        self.assertEqual(self.call('GET', '/my/sync', cookie=ca)
                         ['data']['books'][0]['state']['notes'], 'private')


if __name__ == '__main__':
    unittest.main()
