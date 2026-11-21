"""ChessOnline V10 smoke tests for supported time controls and two-player moves."""
import os
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask
import live_chess_api


class ChessMobileSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(live_chess_api, "DB", os.path.join(self.tmp.name, "chess.sqlite3"))
        self.patch.start()
        app = Flask(__name__)
        app.testing = True
        live_chess_api.register_chess(app)
        self.client = app.test_client()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_all_time_controls_create_and_join(self):
        for minutes in (0, 1, 3, 5, 10, 30, 60):
            with self.subTest(minutes=minutes):
                created = self.client.post("/api/chess/create", json={"minutes": minutes})
                self.assertEqual(created.status_code, 201, created.get_json())
                room = created.get_json()["room"]
                joined = self.client.post("/api/chess/join", json={"room": room})
                self.assertEqual(joined.status_code, 200, joined.get_json())

    def test_two_players_alternate_moves_and_block_out_of_turn(self):
        created = self.client.post("/api/chess/create", json={"minutes": 10}).get_json()
        room = created["room"]
        joined = self.client.post("/api/chess/join", json={"room": room}).get_json()
        white = {"X-Chess-Token": created["token"]}
        black = {"X-Chess-Token": joined["token"]}
        self.assertEqual(self.client.post("/api/chess/move/" + room, headers=black,
                         json={"uci": "e7e5"}).status_code, 409)
        self.assertEqual(self.client.post("/api/chess/move/" + room, headers=white,
                         json={"uci": "e2e4"}).status_code, 200)
        self.assertEqual(self.client.post("/api/chess/move/" + room, headers=white,
                         json={"uci": "d2d4"}).status_code, 409)
        self.assertEqual(self.client.post("/api/chess/move/" + room, headers=black,
                         json={"uci": "e7e5"}).status_code, 200)
        for headers in (white, black):
            state = self.client.get("/api/chess/state/" + room, headers=headers)
            self.assertEqual(state.status_code, 200)
            self.assertEqual(state.get_json()["moves"], ["e2e4", "e7e5"])


if __name__ == "__main__":
    unittest.main()
