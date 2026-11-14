"""Real loopback HTTP integration test for the isolated WSGI prototype.

No external service, phone, or HTTPS is involved. The test runs a real
HTTP server on an ephemeral loopback port and exercises SQLite persistence.
"""
import http.client
import json
import os
import tempfile
import threading
import unittest
from wsgiref.simple_server import make_server

import web_app
from persistent_sessions import SQLiteSessionManager


class LoopbackIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db, self.old_sessions = web_app.DB_PATH, web_app.SESSIONS
        web_app.DB_PATH = os.path.join(self.tmp.name, 'books.sqlite3')
        web_app.SESSIONS = SQLiteSessionManager(web_app.DB_PATH)
        self.server = make_server('127.0.0.1', 0, web_app.app)
        self.port = self.server.server_port
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()

    def tearDown(self):
        self.server.shutdown()
        self.worker.join(timeout=5)
        self.server.server_close()
        web_app.DB_PATH, web_app.SESSIONS = self.old_db, self.old_sessions
        self.tmp.cleanup()

    def request(self, method, path, payload=None, cookie='', csrf=''):
        headers = {}
        if cookie:
            headers['Cookie'] = cookie
        if csrf:
            headers['X-CSRF-Token'] = csrf
        raw = None
        if payload is not None:
            raw = json.dumps(payload).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        connection = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        try:
            connection.request(method, path, body=raw, headers=headers)
            response = connection.getresponse()
            result = response.status, json.loads(response.read()), dict(response.getheaders())
            return result
        finally:
            connection.close()

    def test_registration_restart_read_and_logout(self):
        code, _, headers = self.request('POST', '/register', {
            'username': 'readerone', 'password': 'a secure long password'})
        self.assertEqual(code, 200)
        cookie = headers['Set-Cookie'].split(';')[0]
        code, csrf_data, _ = self.request('GET', '/csrf', cookie=cookie)
        self.assertEqual(code, 200)
        csrf = csrf_data['csrf_token']
        self.assertEqual(self.request('POST', '/my/sync', {
            'book_id': 'novel', 'state': {'notes': 'saved'}, 'expected_revision': 0},
            cookie=cookie)[0], 403)
        self.assertEqual(self.request('POST', '/my/sync', {
            'book_id': 'novel', 'state': {'notes': 'saved'}, 'expected_revision': 0},
            cookie=cookie, csrf=csrf)[0], 200)

        # Simulates a new application process with the same durable DB.
        web_app.SESSIONS = SQLiteSessionManager(web_app.DB_PATH)
        code, data, _ = self.request('GET', '/my/sync', cookie=cookie)
        self.assertEqual(code, 200)
        self.assertEqual(data['books'][0]['state']['notes'], 'saved')
        self.assertEqual(self.request('POST', '/logout', {}, cookie, csrf)[0], 200)
        self.assertEqual(self.request('GET', '/my/sync', cookie=cookie)[0], 401)

    def test_two_users_cannot_access_each_others_books(self):
        first = self.request('POST', '/register', {
            'username': 'readerone', 'password': 'a secure long password'})
        second = self.request('POST', '/register', {
            'username': 'readertwo', 'password': 'another secure password'})
        self.assertEqual(first[0], 200)
        self.assertEqual(second[0], 200)
        first_cookie = first[2]['Set-Cookie'].split(';')[0]
        second_cookie = second[2]['Set-Cookie'].split(';')[0]
        first_csrf = self.request('GET', '/csrf', cookie=first_cookie)[1]['csrf_token']
        second_csrf = self.request('GET', '/csrf', cookie=second_cookie)[1]['csrf_token']
        self.assertEqual(self.request('POST', '/my/sync', {
            'book_id': 'private-book', 'state': {'notes': 'private to reader one'},
            'expected_revision': 0}, first_cookie, first_csrf)[0], 200)
        self.assertEqual(self.request('GET', '/my/sync', cookie=second_cookie)[1]['books'], [])
        self.assertEqual(self.request('POST', '/my/sync', {
            'book_id': 'private-book', 'state': {'notes': 'reader two version'},
            'expected_revision': 0}, second_cookie, second_csrf)[0], 200)
        first_books = self.request('GET', '/my/sync', cookie=first_cookie)[1]['books']
        second_books = self.request('GET', '/my/sync', cookie=second_cookie)[1]['books']
        self.assertEqual(first_books[0]['state']['notes'], 'private to reader one')
        self.assertEqual(second_books[0]['state']['notes'], 'reader two version')


if __name__ == '__main__':
    unittest.main()
