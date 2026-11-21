"""ChessOnline rated settlement regression tests; run with python -m unittest test_chess_rated_api.py."""
import os
import tempfile
import unittest
from unittest.mock import patch

from flask import Flask


class RatedApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "chess.sqlite3")
        import live_chess_api
        self.patch = patch.object(live_chess_api, "DB", self.db)
        self.patch.start()
        self.api = live_chess_api
        app = Flask(__name__)
        app.testing = True
        live_chess_api.register_chess(app)
        self.client = app.test_client()
        assert self.client.get('/api/chess/rating/leaderboard').status_code == 200
        self.white = "white-secret"
        self.black = "black-secret"

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def seed(self, rated=True, accepted=True):
        import chess
        with self.api.sqlite3.connect(self.db) as c:
            c.execute("INSERT INTO chess_lobby_players VALUES ('w','White',9999999999)")
            c.execute("INSERT INTO chess_lobby_players VALUES ('b','Black',9999999999)")
            c.execute("""INSERT INTO chess_rooms
                (id,white_token,black_token,fen,updated,created,minutes,white_ms,black_ms,rated)
                VALUES ('room',?,?,?,1,1,3,180000,180000,?)""",
                (self.white,self.black,chess.STARTING_FEN,int(rated)))
            c.execute("""INSERT INTO chess_lobby_invites
                (id,sender_hash,receiver_hash,room,status,created,updated)
                VALUES ('invite','w','b','room',?,1,1)""",
                ("accepted" if accepted else "pending",))

    def counts(self):
        with self.api.sqlite3.connect(self.db) as c:
            events = c.execute("SELECT COUNT(*) FROM chess_rating_events").fetchone()[0]
            ratings = c.execute("SELECT SUM(rated_games) FROM chess_ratings").fetchone()[0]
            return events, ratings or 0

    def test_resignation_rates_once_even_after_repeated_reads(self):
        self.seed()
        r = self.client.post("/api/chess/resign/room", headers={"X-Chess-Token":self.white})
        self.assertEqual(r.status_code, 200, r.get_json())
        self.assertEqual(self.counts(), (2, 2))
        for _ in range(3):
            self.assertEqual(self.client.get("/api/chess/state/room",
                headers={"X-Chess-Token":self.black}).status_code, 200)
        self.assertEqual(self.counts(), (2, 2))

    def test_unrated_does_not_change_ratings(self):
        self.seed(rated=False)
        self.assertEqual(self.client.post("/api/chess/resign/room",
            headers={"X-Chess-Token":self.white}).status_code, 200)
        self.assertEqual(self.counts(), (0, 0))

    def test_unaccepted_invite_cannot_change_ratings(self):
        self.seed(accepted=False)
        self.assertEqual(self.client.post("/api/chess/resign/room",
            headers={"X-Chess-Token":self.white}).status_code, 200)
        self.assertEqual(self.counts(), (0, 0))

    def test_rated_undo_is_rejected(self):
        self.seed()
        with self.api.sqlite3.connect(self.db) as c:
            c.execute("UPDATE chess_rooms SET moves='e2e4' WHERE id='room'")
        r = self.client.post("/api/chess/undo/room",
            headers={"X-Chess-Token":self.white}, json={"action":"request"})
        self.assertEqual(r.status_code, 409)


if __name__ == "__main__":
    unittest.main()
