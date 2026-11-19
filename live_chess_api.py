"""BOOK CENTER live chess API. Mount register_chess(app) in the existing Flask server.
Requires Flask and python-chess. Store database outside the public web root.
"""
import os, sqlite3, secrets, time
from flask import request, jsonify
import chess

DB = os.environ.get("BOOK_CHESS_DB", os.path.expanduser("~/BOOK_DATA/chess.sqlite3"))
ORIGIN = "https://dalkiran123.github.io"

def register_chess(app):
    def connect():
        os.makedirs(os.path.dirname(os.path.abspath(DB)), exist_ok=True)
        c = sqlite3.connect(DB, timeout=10, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA busy_timeout=10000")
        c.execute("""CREATE TABLE IF NOT EXISTS chess_rooms (
          id TEXT PRIMARY KEY, white_token TEXT NOT NULL, black_token TEXT,
          fen TEXT NOT NULL, moves TEXT NOT NULL DEFAULT '',
          updated INTEGER NOT NULL)""")
        return c

    @app.after_request
    def chess_cors(response):
        if request.path.startswith("/api/chess/"):
            if request.headers.get("Origin") == ORIGIN:
                response.headers["Access-Control-Allow-Origin"] = ORIGIN
                response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/api/chess/<path:unused>", methods=["OPTIONS"])
    def chess_options(unused):
        return "", 204

    def view(row, token):
        role = "white" if secrets.compare_digest(token, row["white_token"]) else (
            "black" if row["black_token"] and secrets.compare_digest(token, row["black_token"]) else None)
        if not role:
            return None
        board = chess.Board(row["fen"])
        return dict(id=row["id"], role=role, fen=row["fen"], moves=row["moves"].split() if row["moves"] else [],
                    turn="white" if board.turn else "black", joined=bool(row["black_token"]),
                    finished=board.is_game_over(claim_draw=True), updated=row["updated"])

    @app.post("/api/chess/create")
    def chess_create():
        room, token = secrets.token_urlsafe(9), secrets.token_urlsafe(32)
        with connect() as c:
            c.execute("INSERT INTO chess_rooms(id,white_token,fen,updated) VALUES(?,?,?,?)",
                      (room, token, chess.STARTING_FEN, int(time.time())))
        return jsonify(room=room, token=token, role="white"), 201

    @app.post("/api/chess/join")
    def chess_join():
        data = request.get_json(silent=True) or {}
        room = str(data.get("room", ""))[:64]
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
            if not row:
                return jsonify(error="Oda bulunamadı"), 404
            if row["black_token"]:
                return jsonify(error="Oda dolu"), 409
            token = secrets.token_urlsafe(32)
            c.execute("UPDATE chess_rooms SET black_token=?,updated=? WHERE id=?",
                      (token, int(time.time()), room))
        return jsonify(room=room, token=token, role="black")

    @app.get("/api/chess/state/<room>")
    def chess_state(room):
        token = request.headers.get("X-Chess-Token", "")
        with connect() as c:
            row = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
        result = view(row, token) if row else None
        return (jsonify(result), 200) if result else (jsonify(error="Erişim reddedildi"), 403)

    @app.post("/api/chess/move/<room>")
    def chess_move(room):
        token = request.headers.get("X-Chess-Token", "")
        uci = str((request.get_json(silent=True) or {}).get("uci", ""))
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
            state = view(row, token) if row else None
            if not state:
                return jsonify(error="Erişim reddedildi"), 403
            board = chess.Board(row["fen"])
            if not state["joined"] or state["finished"]:
                return jsonify(error="Oyun henüz başlamadı veya bitti"), 409
            if state["role"] != state["turn"]:
                return jsonify(error="Rakibin sırası"), 409
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                return jsonify(error="Geçersiz hamle"), 400
            if move not in board.legal_moves:
                return jsonify(error="Kurallara aykırı hamle"), 400
            board.push(move)
            c.execute("UPDATE chess_rooms SET fen=?,moves=?,updated=? WHERE id=?",
                      (board.fen(), (row["moves"]+" "+uci).strip(), int(time.time()), room))
            updated = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
        return jsonify(view(updated, token))
