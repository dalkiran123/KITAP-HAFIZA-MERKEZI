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
            "rated": "INTEGER NOT NULL DEFAULT 0",
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
        c.execute("""CREATE TABLE IF NOT EXISTS chess_lobby_watching (token_hash TEXT PRIMARY KEY,room TEXT NOT NULL,last_seen INTEGER NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS chess_ratings (
            player_hash TEXT PRIMARY KEY,
            rating REAL NOT NULL DEFAULT 1500,
            rd REAL NOT NULL DEFAULT 350,
            volatility REAL NOT NULL DEFAULT 0.06,
            rated_games INTEGER NOT NULL DEFAULT 0,
            updated INTEGER NOT NULL DEFAULT 0)""")
        c.execute("""CREATE TABLE IF NOT EXISTS chess_rating_events (
            room TEXT NOT NULL,
            player_hash TEXT NOT NULL,
            old_rating REAL NOT NULL,
            new_rating REAL NOT NULL,
            created INTEGER NOT NULL,
            PRIMARY KEY(room, player_hash))""")
        return c

    @app.get("/api/chess/rating/leaderboard")
    def chess_rating_leaderboard():
        """Read-only leaderboard; unrated players are not silently ranked."""
        with connect() as c:
            rows = c.execute("""SELECT p.name,r.rating,r.rd,r.rated_games
                FROM chess_ratings r JOIN chess_lobby_players p ON p.token_hash=r.player_hash
                WHERE r.rated_games>0
                ORDER BY r.rating DESC,r.rated_games DESC LIMIT 100""").fetchall()
        from chess_rating import league
        return jsonify(players=[dict(rank=i,name=row["name"],rating=round(row["rating"]),
            rd=round(row["rd"]),games=row["rated_games"],league=league(row["rating"]))
            for i,row in enumerate(rows,1)])

    @app.get("/api/chess/rating/bots")
    def chess_rating_bots():
        """Explicitly virtual roster. Not part of human rated leaderboard."""
        from chess_rating import BOT_ROSTER
        return jsonify(bots=list(BOT_ROSTER))

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
        updated = c.execute("SELECT * FROM chess_rooms WHERE id=?", (row["id"],)).fetchone()
        if updated["result"]:
            finalize_rating(c, updated)
        return updated

    def finalize_rating(c, row):
        """Idempotent, invitation-authenticated, opt-in rated settlement."""
        if not row["rated"] or not row["result"] or not row["black_token"]:
            return False
        if row["result"] not in ("white", "black", "draw"):
            return False
        invite = c.execute("""SELECT sender_hash,receiver_hash FROM chess_lobby_invites
            WHERE room=? AND status='accepted' LIMIT 1""", (row["id"],)).fetchone()
        if not invite or invite["sender_hash"] == invite["receiver_hash"]:
            return False
        players = (invite["sender_hash"], invite["receiver_hash"])
        if c.execute("SELECT 1 FROM chess_rating_events WHERE room=? LIMIT 1", (row["id"],)).fetchone():
            return False
        from chess_rating import Rating, update_rating
        old = []
        for player_hash in players:
            r = c.execute("SELECT * FROM chess_ratings WHERE player_hash=?", (player_hash,)).fetchone()
            old.append(Rating(r["rating"], r["rd"], r["volatility"]) if r else Rating())
        scores = (1.0, 0.0) if row["result"] == "white" else (0.0, 1.0) if row["result"] == "black" else (0.5, 0.5)
        updated = [update_rating(old[i], [(old[1-i], scores[i])]) for i in range(2)]
        now = int(time.time())
        for i, player_hash in enumerate(players):
            c.execute("""INSERT INTO chess_ratings(player_hash,rating,rd,volatility,rated_games,updated)
                VALUES(?,?,?,?,1,?)
                ON CONFLICT(player_hash) DO UPDATE SET
                rating=excluded.rating,rd=excluded.rd,volatility=excluded.volatility,
                rated_games=chess_ratings.rated_games+1,updated=excluded.updated""",
                (player_hash,updated[i].rating,updated[i].rd,updated[i].volatility,now))
            c.execute("""INSERT INTO chess_rating_events(room,player_hash,old_rating,new_rating,created)
                VALUES(?,?,?,?,?)""", (row["id"],player_hash,old[i].rating,updated[i].rating,now))
        return True

    def view(c, row, token):
        role = role_of(row, token)
        if not role:
            return None
        if row["result"]:
            finalize_rating(c, row)
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
            rated=bool(row["rated"]), finished=bool(row["result"]) or board.is_game_over(claim_draw=True),
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
            c.execute("DELETE FROM chess_lobby_players WHERE last_seen<?", (now-30*86400,))
            c.execute("""INSERT INTO chess_lobby_players(token_hash,name,last_seen)
                VALUES(?,?,?) ON CONFLICT(token_hash) DO UPDATE
                SET name=excluded.name,last_seen=excluded.last_seen""", (key,name,now))
        return jsonify(ok=True, online=True)

    @app.post("/api/chess/lobby/offline")
    def chess_lobby_offline():
        """Best-effort immediate disconnect; the normal heartbeat restores presence."""
        import hashlib
        data = request.get_json(silent=True) or {}
        token = str(data.get("token", ""))
        if not (32 <= len(token) <= 128) or not all(ch.isalnum() or ch in "-_" for ch in token):
            return jsonify(error="Geçersiz oturum anahtarı"), 400
        key = hashlib.sha256(token.encode()).hexdigest()
        with connect() as c:
            c.execute("UPDATE chess_lobby_players SET last_seen=? WHERE token_hash=?", (int(time.time())-121, key))
        return jsonify(ok=True)

    @app.get("/api/chess/lobby/players")
    def chess_lobby_players():
        """Registered players, presence, current matches and spectator activity."""
        now = int(time.time())
        with connect() as c:
            players = c.execute("""SELECT token_hash,name,last_seen FROM chess_lobby_players
                WHERE last_seen>=? ORDER BY last_seen DESC LIMIT 200""",(now-30*86400,)).fetchall()
            match_rows = c.execute("""SELECT i.sender_hash,i.receiver_hash,i.room,
                r.fen,r.result,r.minutes,r.white_ms,r.black_ms,r.tick_ms,
                s.name AS white_name,t.name AS black_name
                FROM chess_lobby_invites i
                JOIN chess_rooms r ON r.id=i.room
                JOIN chess_lobby_players s ON s.token_hash=i.sender_hash
                JOIN chess_lobby_players t ON t.token_hash=i.receiver_hash
                WHERE i.status='accepted' AND r.result='' ORDER BY r.created DESC
                LIMIT 100""").fetchall()
            active={}
            for r in match_rows:
                board=chess.Board(r["fen"])
                if board.is_game_over(claim_draw=True):
                    continue
                if r["minutes"] and r["tick_ms"]:
                    remaining=r["white_ms"] if board.turn else r["black_ms"]
                    if remaining <= max(0,now*1000-r["tick_ms"]):
                        continue
                for player_hash,opponent in ((r["sender_hash"],r["black_name"]),(r["receiver_hash"],r["white_name"])):
                    active.setdefault(player_hash,dict(activity="playing",opponent=opponent,room=r["room"]))
            watching={}
            for r in c.execute("""SELECT token_hash,room,last_seen FROM chess_lobby_watching
                WHERE last_seen>=?""",(now-20,)):
                watching[r["token_hash"]]=r["room"]
            match_names={r["room"]:r["white_name"]+" - "+r["black_name"] for r in match_rows}
            out=[]
            for p in players:
                online=p["last_seen"]>=now-60
                state=active.get(p["token_hash"])
                if online and p["token_hash"] in watching and watching[p["token_hash"]] in match_names:
                    state=dict(activity="watching",match=match_names[watching[p["token_hash"]]],room=watching[p["token_hash"]])
                out.append(dict(id=p["token_hash"],name=p["name"],online=online,
                    last_seen=p["last_seen"],**(state or dict(activity="idle"))))
            out.sort(key=lambda p:(not p["online"],p["name"].casefold()))
        return jsonify(players=out,count=sum(p["online"] for p in out),
            total=len(out),online_window_seconds=60)

    @app.post("/api/chess/lobby/watching")
    def chess_lobby_watching():
        """Spectator presence; identity is the same random browser token as lobby."""
        data=request.get_json(silent=True) or {}
        room=str(data.get("room",""))[:64]
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            player=lobby_identity(c)
            if player is None:
                return jsonify(error="Önce lobiye giriş yap"),403
            valid=c.execute("""SELECT 1 FROM chess_lobby_invites i JOIN chess_rooms r ON r.id=i.room
                WHERE i.room=? AND i.status='accepted' AND r.black_token IS NOT NULL""",(room,)).fetchone()
            if not valid:
                return jsonify(error="Maç bulunamadı"),404
            c.execute("""INSERT INTO chess_lobby_watching(token_hash,room,last_seen)
                VALUES(?,?,?) ON CONFLICT(token_hash) DO UPDATE
                SET room=excluded.room,last_seen=excluded.last_seen""",
                (player["token_hash"],room,int(time.time())))
        return jsonify(ok=True)

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
        if minutes not in (0, 1, 3, 5, 10):
            return jsonify(error="Geçersiz süre"), 400
        rated = data.get("rated", False) is True
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
            pending = c.execute("""SELECT id FROM chess_lobby_invites WHERE sender_hash=? AND receiver_hash=? AND status='pending' AND created>=?""",(sender["token_hash"],target,now-300)).fetchone()
            if pending:
                return jsonify(error="Bu oyuncuya bekleyen davetin var"), 409
            room, white_token = secrets.token_urlsafe(9), secrets.token_urlsafe(32)
            invite_id = secrets.token_urlsafe(12)
            c.execute("""INSERT INTO chess_rooms(id,white_token,fen,updated,created,minutes,white_ms,black_ms,rated)
                VALUES(?,?,?,?,?,?,?,?,?)""",(room,white_token,chess.STARTING_FEN,now,now,minutes,minutes*60000,minutes*60000,int(rated)))
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
                WHERE status='pending' AND created<=?""",(now,now-300))
            rows = c.execute("""SELECT i.*,s.name AS sender_name,r.name AS receiver_name,cr.fen AS room_fen,cr.result AS room_result,cr.reason AS room_reason,cr.minutes AS room_minutes,cr.white_ms AS room_white_ms,cr.black_ms AS room_black_ms,cr.tick_ms AS room_tick_ms
                FROM chess_lobby_invites i
                JOIN chess_lobby_players s ON s.token_hash=i.sender_hash
                JOIN chess_lobby_players r ON r.token_hash=i.receiver_hash
                LEFT JOIN chess_rooms cr ON cr.id=i.room
                WHERE (i.receiver_hash=? OR i.sender_hash=?) AND i.created>=?
                ORDER BY i.created DESC LIMIT 40""",(me["token_hash"],me["token_hash"],now-86400)).fetchall()
            def match_finished(r):
                if r["status"]!="accepted": return False
                if r["room_result"] or (r["room_fen"] and chess.Board(r["room_fen"]).is_game_over(claim_draw=True)): return True
                if r["room_minutes"] and r["room_tick_ms"]:
                    elapsed=max(0,int(time.time()*1000)-r["room_tick_ms"])
                    side=chess.Board(r["room_fen"]).turn
                    return (r["room_white_ms"] if side else r["room_black_ms"]) <= elapsed
                return False
            return jsonify(invites=[dict(finished=match_finished(r),id=r["id"],room=r["room"],status=r["status"],
                direction="incoming" if r["receiver_hash"]==me["token_hash"] else "outgoing",
                from_id=r["sender_hash"],to_id=r["receiver_hash"],expires_at=r["created"]+300,
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
            if row["status"]!="pending" or row["created"]<=int(time.time())-300:
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
            white_name,black_name=row["white_name"],row["black_name"]
            row=settle(c,row)
            board=chess.Board(row["fen"])
            return jsonify(room=row["id"],white_name=white_name,black_name=black_name,
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
        if minutes not in (0, 1, 3, 5, 10):
            return jsonify(error="Süre 1, 3, 5, 10 dakika veya süresiz olmalı"), 400
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

    @app.post("/api/chess/resign/<room>")
    def chess_resign(room):
        token = request.headers.get("X-Chess-Token", "")
        with connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row, role = current(c, room, token)
            if role not in ("white", "black"):
                return jsonify(error="Yalnızca oyuncular maçı bitirebilir"), 403
            if not row["black_token"]:
                return jsonify(error="Rakip henüz katılmadı"), 409
            if row["result"] or chess.Board(row["fen"]).is_game_over(claim_draw=True):
                return jsonify(error="Maç zaten sona erdi"), 409
            winner = "black" if role == "white" else "white"
            now = int(time.time())
            c.execute("""UPDATE chess_rooms SET result=?,reason='resign',ended=?,updated=?,tick_ms=0,undo_by='' WHERE id=? AND result=''""",
                      (winner, now, now, room))
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
