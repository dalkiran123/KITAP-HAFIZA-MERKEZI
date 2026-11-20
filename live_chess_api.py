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
        c.execute("""CREATE TABLE IF NOT EXISTS chess_lobby_players (
            token_hash TEXT PRIMARY KEY, name TEXT NOT NULL,
            last_seen INTEGER NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS chess_lobby_seen ON chess_lobby_players(last_seen)")
        c.execute("""CREATE TABLE IF NOT EXISTS chess_lobby_invites (
            id TEXT PRIMARY KEY, sender_hash TEXT NOT NULL, receiver_hash TEXT NOT NULL,
            room TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
            created INTEGER NOT NULL, updated INTEGER NOT NULL)""")
        c.execute("CREATE INDEX IF NOT EXISTS chess_invites_receiver ON chess_lobby_invites(receiver_hash,status)")
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
        invite = c.execute("""SELECT s.name AS white_name,r.name AS black_name
            FROM chess_lobby_invites i
            JOIN chess_lobby_players s ON s.token_hash=i.sender_hash
            JOIN chess_lobby_players r ON r.token_hash=i.receiver_hash
            WHERE i.room=? AND i.status='accepted' LIMIT 1""",(row["id"],)).fetchone()
        white_name = invite["white_name"] if invite else "Beyaz"
        black_name = invite["black_name"] if invite else "Siyah"
        return dict(white_name=white_name, black_name=black_name, id=row["id"], role=role, fen=row["fen"],
            moves=row["moves"].split() if row["moves"] else [],
            turn="white" if board.turn else "black", joined=bool(row["black_token"]),
            finished=bool(row["result"]) or board.is_game_over(claim_draw=True),
            result=row["result"], reason=row["reason"], updated=row["updated"],
            created=row["created"], ended=row["ended"], minutes=row["minutes"],
            white_ms=row["white_ms"], black_ms=row["black_ms"],
            tick_ms=row["tick_ms"], clock_history=row["clock_history"].split(), undo_by=row["undo_by"],
            messages=list(reversed(messages)))

    def current(c, room, token):
        row = c.execute("SELECT * FROM chess_rooms WHERE id=?", (room,)).fetchone()
        if not role_of(row, token):
            return None, None
        row = settle(c, row)
        return row, role_of(row, token)

    @app.post("/api/chess/lobby/heartbeat")
    def chess_lobby_heartbeat():
        """Anonymous nickname presence, scoped to a private random browser token."""
        import hashlib
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "")).strip()
        token = str(data.get("token", ""))
        if not (2 <= len(name) <= 24) or any(ord(ch) < 32 for ch in name):
            return jsonify(error="Oyuncu adı 2-24 karakter olmalı"), 400
        if not (32 <= len(token) <= 128) or not all(ch.isalnum() or ch in "-_" for ch in token):
            return jsonify(error="Geçersiz oturum anahtarı"), 400
        key = hashlib.sha256(token.encode()).hexdigest()
        now = int(time.time())
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM chess_lobby_players WHERE last_seen<?", (now-86400,))
            c.execute("""INSERT INTO chess_lobby_players(token_hash,name,last_seen)
                VALUES(?,?,?) ON CONFLICT(token_hash) DO UPDATE
                SET name=excluded.name,last_seen=excluded.last_seen""", (key,name,now))
        return jsonify(ok=True, online=True)

    @app.get("/api/chess/lobby/players")
    def chess_lobby_players():
        now = int(time.time())
        with connect() as c:
            rows = c.execute("""SELECT name,last_seen FROM chess_lobby_players
                WHERE last_seen>=? ORDER BY name COLLATE NOCASE LIMIT 200""",
                (now-60,)).fetchall()
        return jsonify(players=[dict(id=r["token_hash"],name=r["name"],online=True) for r in c.execute("""SELECT token_hash,name,last_seen FROM chess_lobby_players WHERE last_seen>=? ORDER BY name COLLATE NOCASE LIMIT 200""",(now-60,))],
                       count=len(rows),online_window_seconds=60)


    def lobby_identity(c):
        import hashlib
        token = str(request.headers.get("X-Chess-Token", ""))
        if not (32 <= len(token) <= 128) or not all(ch.isalnum() or ch in "-_" for ch in token):
            return None
        key = hashlib.sha256(token.encode()).hexdigest()
        row = c.execute("SELECT * FROM chess_lobby_players WHERE token_hash=?", (key,)).fetchone()
        if not row or row["last_seen"] < int(time.time()) - 60:
            return None
        return row

    @app.post("/api/chess/lobby/invite")
    def chess_lobby_invite():
        data = request.get_json(silent=True) or {}
        target = str(data.get("player_id", ""))
        if len(target) != 64 or any(ch not in "0123456789abcdef" for ch in target):
            return jsonify(error="Geçersiz oyuncu"), 400
        try:
            minutes = int(data.get("minutes", 10))
        except (TypeError, ValueError):
            return jsonify(error="Geçersiz süre"), 400
        if minutes not in (0, 10, 30, 60):
            return jsonify(error="Geçersiz süre"), 400
        now = int(time.time())
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            sender = lobby_identity(c)
            if sender is None:
                return jsonify(error="Önce lobiye giriş yap"), 403
            if sender["token_hash"] == target:
                return jsonify(error="Kendine davet gönderemezsin"), 400
            receiver = c.execute("SELECT * FROM chess_lobby_players WHERE token_hash=? AND last_seen>=?",(target,now-60)).fetchone()
            if receiver is None:
                return jsonify(error="Oyuncu çevrimdışı"), 404
            pending = c.execute("""SELECT id FROM chess_lobby_invites WHERE sender_hash=? AND receiver_hash=? AND status='pending' AND created>=?""",(sender["token_hash"],target,now-120)).fetchone()
            if pending:
                return jsonify(error="Bu oyuncuya bekleyen davetin var"), 409
            room, white_token = secrets.token_urlsafe(9), secrets.token_urlsafe(32)
            invite_id = secrets.token_urlsafe(12)
            c.execute("""INSERT INTO chess_rooms(id,white_token,fen,updated,created,minutes,white_ms,black_ms)
                VALUES(?,?,?,?,?,?,?,?)""",(room,white_token,chess.STARTING_FEN,now,now,minutes,minutes*60000,minutes*60000))
            c.execute("""INSERT INTO chess_lobby_invites(id,sender_hash,receiver_hash,room,status,created,updated)
                VALUES(?,?,?,?,?,?,?)""",(invite_id,sender["token_hash"],target,room,"pending",now,now))
        return jsonify(ok=True,invite_id=invite_id,room=room,token=white_token,status="pending"), 201

    @app.get("/api/chess/lobby/invites")
    def chess_lobby_invites():
        with connect() as c:
            me = lobby_identity(c)
            if me is None:
                return jsonify(error="Önce lobiye giriş yap"), 403
            now = int(time.time())
            c.execute("""UPDATE chess_lobby_invites SET status='expired',updated=?
                WHERE status='pending' AND created<?""",(now,now-120))
            rows = c.execute("""SELECT i.*,s.name AS sender_name,r.name AS receiver_name
                FROM chess_lobby_invites i
                JOIN chess_lobby_players s ON s.token_hash=i.sender_hash
                JOIN chess_lobby_players r ON r.token_hash=i.receiver_hash
                WHERE (i.receiver_hash=? OR i.sender_hash=?) AND i.created>=?
                ORDER BY i.created DESC LIMIT 40""",(me["token_hash"],me["token_hash"],now-86400)).fetchall()
            return jsonify(invites=[dict(id=r["id"],room=r["room"],status=r["status"],
                direction="incoming" if r["receiver_hash"]==me["token_hash"] else "outgoing",
                from_name=r["sender_name"],to_name=r["receiver_name"],created=r["created"]) for r in rows])

    @app.post("/api/chess/lobby/invites/<invite_id>/respond")
    def chess_lobby_invite_respond(invite_id):
        action = str((request.get_json(silent=True) or {}).get("action",""))
        if action not in ("accept","reject"):
            return jsonify(error="Geçersiz işlem"), 400
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            me = lobby_identity(c)
            if me is None:
                return jsonify(error="Önce lobiye giriş yap"), 403
            row = c.execute("SELECT * FROM chess_lobby_invites WHERE id=? AND receiver_hash=?",
                (invite_id,me["token_hash"])).fetchone()
            if not row:
                return jsonify(error="Davet bulunamadı"), 404
            if row["status"]!="pending" or row["created"]<int(time.time())-120:
                return jsonify(error="Davet süresi doldu veya yanıtlandı"), 409
            now=int(time.time())
            if action=="reject":
                c.execute("UPDATE chess_lobby_invites SET status='rejected',updated=? WHERE id=?",(now,invite_id))
                return jsonify(ok=True,status="rejected")
            room=c.execute("SELECT * FROM chess_rooms WHERE id=?",(row["room"],)).fetchone()
            if not room or room["black_token"]:
                return jsonify(error="Oyun odası dolu"), 409
            black_token=secrets.token_urlsafe(32)
            c.execute("UPDATE chess_rooms SET black_token=?,tick_ms=?,updated=? WHERE id=?",
                (black_token,int(time.time()*1000) if room["minutes"] else 0,now,row["room"]))
            c.execute("UPDATE chess_lobby_invites SET status='accepted',updated=? WHERE id=?",(now,invite_id))
            return jsonify(ok=True,status="accepted",room=row["room"],token=black_token,role="black")


    @app.get("/api/chess/live")
    def chess_live_matches():
        """Public metadata for accepted invitation matches; no player tokens or chat."""
        with connect() as c:
            rows = c.execute("""SELECT r.*,p1.name AS white_name,p2.name AS black_name
                FROM chess_rooms r JOIN chess_lobby_invites i
                ON i.room=r.id AND i.status='accepted'
                JOIN chess_lobby_players p1 ON p1.token_hash=i.sender_hash
                JOIN chess_lobby_players p2 ON p2.token_hash=i.receiver_hash
                WHERE r.black_token IS NOT NULL AND r.result='' AND r.created>=?
                ORDER BY r.updated DESC LIMIT 40""",(int(time.time())-86400,)).fetchall()
            matches=[]
            for row in rows:
                row=settle(c,row)
                if row["result"] or chess.Board(row["fen"]).is_game_over(claim_draw=True):
                    continue
                names=c.execute("""SELECT p1.name AS white_name,p2.name AS black_name
                    FROM chess_lobby_invites i JOIN chess_lobby_players p1 ON p1.token_hash=i.sender_hash
                    JOIN chess_lobby_players p2 ON p2.token_hash=i.receiver_hash
                    WHERE i.room=? AND i.status='accepted' LIMIT 1""",(row["id"],)).fetchone()
                matches.append(dict(room=row["id"],white_name=names["white_name"],black_name=names["black_name"],
                    moves=len(row["moves"].split()),minutes=row["minutes"]))
        return jsonify(matches=matches)

    @app.get("/api/chess/watch/<room>")
    def chess_watch(room):
        """Read-only spectator board state. Deliberately excludes chat, tokens and undo."""
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row=c.execute("""SELECT r.*,p1.name AS white_name,p2.name AS black_name
                FROM chess_rooms r JOIN chess_lobby_invites i
                ON i.room=r.id AND i.status='accepted'
                JOIN chess_lobby_players p1 ON p1.token_hash=i.sender_hash
                JOIN chess_lobby_players p2 ON p2.token_hash=i.receiver_hash
                WHERE r.id=? AND r.black_token IS NOT NULL""",(room,)).fetchone()
            if row is None:
                return jsonify(error="İzlenebilir maç bulunamadı"),404
            row=settle(c,row)
            board=chess.Board(row["fen"])
            return jsonify(room=row["id"],white_name=row["white_name"],black_name=row["black_name"],
                fen=row["fen"],moves=row["moves"].split() if row["moves"] else [],
                turn="white" if board.turn else "black",minutes=row["minutes"],
                white_ms=row["white_ms"],black_ms=row["black_ms"],tick_ms=row["tick_ms"],
                finished=bool(row["result"]) or board.is_game_over(claim_draw=True),
                result=row["result"],reason=row["reason"],updated=row["updated"])

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
            invite_room = c.execute("SELECT id FROM chess_lobby_invites WHERE room=?", (room,)).fetchone()
            if invite_room:
                return jsonify(error="Bu oda yalnızca davet edilen oyuncuya açık"), 403
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
