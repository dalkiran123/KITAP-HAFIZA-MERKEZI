import io
import json
import unittest
from unittest.mock import patch
from bot_server.router import wrap_book_app

class RouterTests(unittest.TestCase):
    def test_preserves_book_app(self):
        calls = []
        def original(env, start_response):
            calls.append(env["PATH_INFO"])
            start_response("200 OK", [])
            return [b"original"]
        wrapped = wrap_book_app(original)
        for path in ("/", "/login", "/me", "/leaderboard", "/catalog.js", "/health"):
            result = b"".join(wrapped({"PATH_INFO": path}, lambda status, headers: None))
            self.assertEqual(result, b"original")
        self.assertEqual(len(calls), 6)

    def test_bot_route_is_isolated(self):
        calls = []
        def original(env, start_response):
            calls.append(1)
            return [b"wrong"]
        wrapped = wrap_book_app(original)
        with patch.dict("os.environ", {}, clear=True):
            statuses = []
            data = b"".join(wrapped({"PATH_INFO": "/api/bots/state", "REQUEST_METHOD": "GET"},
                                    lambda status, headers: statuses.append(status)))
        self.assertEqual(statuses[0][:3], "503")
        self.assertFalse(calls)
        self.assertIn("error", json.loads(data))
