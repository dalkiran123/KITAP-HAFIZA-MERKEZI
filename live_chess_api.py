"""BOOK CENTER chess rooms: moves, chat, consented takebacks and server clocks."""
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
        columns = {r["name"] for r in c.execute("PRAGMA table_info(chess_rooms)")}
        extras = {
            "created": "INTEGER NOT NULL DEFAULT 0",
            "minutes": "INTEGER NOT NULL DEFAULT 0",
            "white_ms": "INTEGER NOT NULL DEFAULT 0",
            "black_ms": "INTEGER NOT NULL DEFAULT 0",
            "tick_ms": "INTEGER NOT NULL DEFAULT 0",
            "result": "TEXT NOT NULL DEFAULT ''",
            "reason": "TEXT NOT NULL DEFAULT ''",
            "ended": "INTEGER NOT NULL DEFAULT 0",
            "undo_by": "TEXT NOT NULL DEFAULT ''",
            "undo_at": "INTEGER NOT NULL DEFAULT 0",
            "clock_history": "TEXT NOT NULL DEFAULT ''",
        }
        for name, ddl in extras.items():
            if name not in columns:
                c.execute("ALTER TABLE chess_rooms ADD COLUMN " + name + " " + ddl)
        c.execute("""CREATE TABLE IF NOT EXISTS chess_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT NOT NULL,
            role TEXT NOT NULL, body TEXT NOT NULL, created INTEGER NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS chess_messages_room ON chess_messages(room,id)")
        return c

    @app.after_request
    def chess_cors(response):
        if request.path.startswith("/api/chess/"):
            if request.headers.get("Origin") == ORIGIN:
                response.headers["Access-Control-Allow-Origin"] = ORIGIN
                response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-Chess-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/api/chess/<path:unused>", methods=["OPTIONS"])
    def chess_options(unused):
        return "", 204

    def role_of(row, token):
        if not row or not token:
            return None
        if secrets.compare_digest(token, row["white_token"]):
            return "white"
        if row["black_token"] and secrets.compare_digest(token, row["black_token"]):
            return "black"
        return None

    def settle(c, row):
        """Debit elapsed time atomically, including when no browser is polling."""
        if not row["black_token"] or row["result"] or not row["minutes"] or not row["tick_ms"]:
            return row
        board = chess.Board(row["fen"])
        turn = "white" if board.turn else "black"
        now = int(time.time() * 1000)
        elapsed = max(0, now - row["tick_ms"])
        remaining = max(0, row[turn + "_ms"] - elapsed)
        if remaining == 0:
            winner = "black" if turn == "white" else "white"
            # FIDE: no win on time if the opponent cannot possibly mate.
            opponent = chess.WHITE if winner == "white" else chess.BLACK
            result = "draw" if board.has_insufficient_material(opponent) else winner
            c.execute("UPDATE chess_rooms SET " + turn + "_ms=0,tick_ms=?,result=?,reason='timeout',ended=?,updated=? WHERE id=?",
                      (now, result, int(time.time()), int(time.time()), row["id"]))
        else:
            c.execute("UPDATE chess_rooms SET " + turn + "_ms=?,tick_ms=? WHERE id=?",
                      (remaining, now, row["id"]))
        return c.execute("SELECT * FROM chess_rooms WHERE id=?", (row["id"],)).fetchone()

    def view(c, row, token):
        role = role_of(row, token)
        if not role:
            return None
        board = chess.Board(row["fen"])
        messages = [dict(id=m["id"], role=m["role"], text=m["body"], at=m["created"])
                    for m in c.execute("SELECT * FROM chess_messages WHERE room=? ORDER BY id DESC LIMIT 100", (row["id"],))]
        return dict(id=row["id"], role=role, fen=row["fen"],
            moves=row["moves"].split() if row["moves"] else [],
            turn="white" if board.turn else "black", joined=bool(row["black_token"]),
            finished=bool(row["result"]) or board.is_game_over(claim_draw=True),
            result=row["result"], reason=row["reason"], updated=row["updated"],
            created=row["created"], ended=row["ended"], minutes=row["minutes"],
            white_ms=row["white_ms"], black_ms=row["black_ms"],
            tick_ms=row["tick_ms"], undo_by=row["undo_by"],
            messages=list(reversed(messages)))

    def current(c, room, token):
        row = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
        if not role_of(row, token):
            return None, None
        row = settle(c, row)
        return row, role_of(row, token)

    @app.post("/api/chess/create")
    def chess_create():
        data = request.get_json(silent=True) or {}
        try:
            minutes = int(data.get("minutes", 0))
        except (ValueError, TypeError):
            return jsonify(error="Geçersiz süre"), 400
        if minutes not in (0, 10, 30, 60):
            return jsonify(error="Süre 10, 30 veya 60 dakika olmalı"), 400
        room, token = secrets.token_urlsafe(9), secrets.token_urlsafe(32)
        now = int(time.time())
        with connect() as c:
            c.execute("""INSERT INTO chess_rooms
                (id,white_token,fen,updated,created,minutes,white_ms,black_ms)
                VALUES(?,?,?,?,?,?,?,?)""",
                (room, token, chess.STARTING_FEN, now, now, minutes, minutes*60000, minutes*60000))
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
            now = int(time.time())
            c.execute("UPDATE chess_rooms SET black_token=?,tick_ms=?,updated=? WHERE id=?",
                      (token, int(time.time()*1000) if row["minutes"] else 0, now, room))
        return jsonify(room=room, token=token, role="black")

    @app.get("/api/chess/state/<room>")
    def chess_state(room):
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row, role = current(c, room, request.headers.get("X-Chess-Token", ""))
            if not role:
                return jsonify(error="Erişim reddedildi"), 403
            return jsonify(view(c, row, request.headers.get("X-Chess-Token", "")))

    @app.post("/api/chess/move/<room>")
    def chess_move(room):
        token = request.headers.get("X-Chess-Token", "")
        uci = str((request.get_json(silent=True) or {}).get("uci", ""))
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row, role = current(c, room, token)
            if not role:
                return jsonify(error="Erişim reddedildi"), 403
            board = chess.Board(row["fen"])
            if not row["black_token"] or row["result"] or board.is_game_over(claim_draw=True):
                return jsonify(error="Oyun başlamadı veya sona erdi"), 409
            if role != ("white" if board.turn else "black"):
                return jsonify(error="Rakibin sırası"), 409
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                return jsonify(error="Geçersiz hamle"), 400
            if move not in board.legal_moves:
                return jsonify(error="Kurallara aykırı hamle"), 400
            history = row["clock_history"] + (" " if row["clock_history"] else "") + str(row["white_ms"]) + "," + str(row["black_ms"])
            board.push(move)
            outcome = board.outcome(claim_draw=True)
            result = ("white" if outcome.winner else "black") if outcome and outcome.winner is not None else ("draw" if outcome else "")
            now = int(time.time())
            c.execute("""UPDATE chess_rooms SET fen=?,moves=?,updated=?,tick_ms=?,result=?,reason=?,ended=?,
                undo_by='',clock_history=? WHERE id=?""",
                (board.fen(), (row["moves"]+" "+uci).strip(), now,
                 int(time.time()*1000) if row["minutes"] else 0, result,
                 "board" if result else "", now if result else 0, history, room))
            updated = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
            return jsonify(view(c, updated, token))

    @app.post("/api/chess/chat/<room>")
    def chess_chat(room):
        token = request.headers.get("X-Chess-Token", "")
        body = str((request.get_json(silent=True) or {}).get("text", "")).strip()
        if not body or len(body) > 500:
            return jsonify(error="Mesaj 1-500 karakter olmalı"), 400
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row, role = current(c, room, token)
            if not role:
                return jsonify(error="Erişim reddedildi"), 403
            if not row["black_token"]:
                return jsonify(error="Rakip henüz katılmadı"), 409
            c.execute("INSERT INTO chess_messages(room,role,body,created) VALUES(?,?,?,?)",
                      (room, role, body, int(time.time())))
            return jsonify(view(c, row, token))

    @app.post("/api/chess/undo/<room>")
    def chess_undo(room):
        token = request.headers.get("X-Chess-Token", "")
        action = str((request.get_json(silent=True) or {}).get("action", ""))
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row, role = current(c, room, token)
            if not role:
                return jsonify(error="Erişim reddedildi"), 403
            if not row["black_token"] or not row["moves"] or row["result"]:
                return jsonify(error="Geri alma mümkün değil"), 409
            if action == "request":
                if row["undo_by"]:
                    return jsonify(error="Bekleyen bir talep var"), 409
                c.execute("UPDATE chess_rooms SET undo_by=?,undo_at=? WHERE id=?",
                          (role, int(time.time()), room))
            elif action in ("accept", "reject"):
                if not row["undo_by"] or row["undo_by"] == role:
                    return jsonify(error="Rakibin bekleyen talebi yok"), 409
                if action == "accept":
                    board = chess.Board()
                    for previous in row["moves"].split()[:-1]:
                        board.push_uci(previous)
                    clocks = row["clock_history"].split()
                    white_ms, black_ms = map(int, clocks[-1].split(",")) if clocks else (row["white_ms"], row["black_ms"])
                    c.execute("""UPDATE chess_rooms SET fen=?,moves=?,white_ms=?,black_ms=?,clock_history=?,
                        tick_ms=?,undo_by='',undo_at=0,updated=? WHERE id=?""",
                        (board.fen(), " ".join(row["moves"].split()[:-1]), white_ms, black_ms,
                         " ".join(clocks[:-1]), int(time.time()*1000) if row["minutes"] else 0,
                         int(time.time()), room))
                else:
                    c.execute("UPDATE chess_rooms SET undo_by='',undo_at=0 WHERE id=?", (room,))
            else:
                return jsonify(error="Geçersiz işlem"), 400
            updated = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
            return jsonify(view(c, updated, token))

    @app.get("/api/chess/history")
    def chess_history():
        token = request.headers.get("X-Chess-Token", "")
        if not token:
            return jsonify(error="Erişim reddedildi"), 403
        with connect() as c:
            rows = c.execute("""SELECT * FROM chess_rooms
                WHERE (white_token=? OR black_token=?) AND black_token IS NOT NULL
                ORDER BY created DESC LIMIT 30""", (token, token)).fetchall()
            out = []
            for row in rows:
                board = chess.Board(row["fen"])
                out.append(dict(room=row["id"], created=row["created"], ended=row["ended"],
                    moves=len(row["moves"].split()), result=row["result"],
                    reason=row["reason"], minutes=row["minutes"],
                    finished=bool(row["result"]) or board.is_game_over(claim_draw=True)))
            return jsonify(matches=out)
