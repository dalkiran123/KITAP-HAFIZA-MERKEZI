import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from bot_server.wsgi_adapter import bot_wsgi_app

class AdapterTests(unittest.TestCase):
    def request(self, body=b"{}", **extra):
        env = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api/bots/tick",
               "CONTENT_LENGTH": str(len(body)), "wsgi.input": io.BytesIO(body), **extra}
        statuses = []
        response = b"".join(bot_wsgi_app(env, lambda status, headers: statuses.append(status)))
        return int(statuses[0][:3]), json.loads(response)

    def test_no_configuration_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.request()[0], 503)

    def test_refuses_shared_book_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "books.sqlite3")
            with patch.dict(os.environ, {"BOOK_BOT_DB_PATH": db, "BOOK_DB_PATH": db,
                                         "BOOK_BOT_API_SECRET": "s"*40}):
                self.assertEqual(self.request()[0], 503)
                self.assertFalse(os.path.exists(db))

    def test_invalid_body_length(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.request(body=b"")[0], 413)
            self.assertEqual(self.request(body=b"{}", CONTENT_LENGTH="abc")[0], 413)

    def test_unknown_path(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(self.request(PATH_INFO="/me")[0], 404)
