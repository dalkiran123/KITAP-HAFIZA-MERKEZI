"""Regression tests for the existing multi-user WSGI prototype.

Run from repository root:
  PYTHONPATH=multiuser:. python3 -m unittest discover -s tests -p 'test_multiuser_http_contract.py' -v
All tests use a temporary SQLite database; production data is never opened.
"""
import importlib
import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from wsgiref.simple_server import make_server


class MultiuserHttpContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.previous_db = os.environ.get("BOOK_DB_PATH")
        cls.previous_origin = os.environ.pop("BOOK_PUBLIC_ORIGIN", None)
        os.environ["BOOK_DB_PATH"] = str(Path(cls.temp.name) / "test.sqlite3")
        cls.mod = importlib.import_module("multiuser.web_app")
        cls.server = make_server("127.0.0.1", 0, cls.mod.app)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)
        if cls.previous_db is None:
            os.environ.pop("BOOK_DB_PATH", None)
        else:
            os.environ["BOOK_DB_PATH"] = cls.previous_db
        if cls.previous_origin is not None:
            os.environ["BOOK_PUBLIC_ORIGIN"] = cls.previous_origin
        cls.temp.cleanup()

    def call(self, path, *, body=None, cookie=None, csrf=None):
        headers = {}
        if cookie:
            headers["Cookie"] = cookie
        if csrf:
            headers["X-CSRF-Token"] = csrf
        if body is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(body).encode()
        request = urllib.request.Request(self.base + path, data=body, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.load(response), response.headers
        except urllib.error.HTTPError as error:
            return error.code, json.load(error), error.headers

    def login(self, name):
        code, _, headers = self.call("/register", body={
            "username": name, "password": "test-only-password-12345"
        })
        self.assertEqual(code, 200)
        cookie = headers.get("Set-Cookie", "").split(";", 1)[0]
        self.assertTrue(cookie.startswith("session="))
        self.assertIn("Secure", headers["Set-Cookie"])
        code, data, _ = self.call("/csrf", cookie=cookie)
        self.assertEqual(code, 200)
        return cookie, data["csrf_token"]

    def test_full_book_home_is_served_without_authentication(self):
        with urllib.request.urlopen(self.base + "/", timeout=5) as response:
            html = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
            self.assertIn("Kitap Hafıza Merkezi", html)
            self.assertIn("localStorage", html)
            self.assertIn("/account-preview.js", html)
        with urllib.request.urlopen(self.base + "/account-preview.js", timeout=5) as response:
            script = response.read().decode("utf-8")
            self.assertEqual(response.status, 200)
            self.assertIn("/my/sync", script)
            self.assertIn("Yerel kitaplık değiştirilmedi", script)

    def test_health_and_protected_routes(self):
        self.assertEqual(self.call("/health")[0], 200)
        for route in ("/me", "/my/books", "/my/reading", "/my/ratings", "/my/sync"):
            with self.subTest(route=route):
                self.assertEqual(self.call(route)[0], 401)

    def test_csrf_sync_conflict_and_user_isolation(self):
        alice, alice_csrf = self.login("test_alice")
        bob, bob_csrf = self.login("test_bob")
        payload = {"book_id": "book-1", "state": {"done": True}, "expected_revision": 0}
        self.assertEqual(self.call("/my/sync", body=payload, cookie=alice)[0], 403)
        self.assertEqual(self.call("/my/sync", body=payload, cookie=alice, csrf=alice_csrf)[0], 200)
        code, data, _ = self.call("/my/sync", cookie=alice)
        self.assertEqual(code, 200)
        self.assertEqual(len(data["books"]), 1)
        self.assertEqual(data["books"][0]["revision"], 1)
        self.assertEqual(self.call("/my/sync", body=payload, cookie=alice, csrf=alice_csrf)[0], 409)
        code, data, _ = self.call("/my/sync", cookie=bob)
        self.assertEqual(code, 200)
        self.assertEqual(data["books"], [])
        self.assertEqual(self.call("/logout", body={}, cookie=alice, csrf=alice_csrf)[0], 200)
        self.assertEqual(self.call("/me", cookie=alice)[0], 401)
        self.assertEqual(self.call("/me", cookie=bob)[0], 200)


if __name__ == "__main__":
    unittest.main()
