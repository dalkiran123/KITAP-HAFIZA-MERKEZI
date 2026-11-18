"""Isolated authenticated bot tick endpoint. Not wired into production WSGI."""
import hashlib
import hmac
import json
import os
import sqlite3
import time
from pathlib import Path

MAX_BODY = 65536
MAX_SKEW = 300

def _db(path):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("CREATE TABLE IF NOT EXISTS bot_ticks (tick_id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at INTEGER NOT NULL)")
    return conn

def handle_tick(method, path, headers, body, *, secret, database, now=None):
    """Return (status, object). Never touches BOOK_DB_PATH."""
    if method != "POST" or path != "/api/bots/tick":
        return 404, {"error": "Not found"}
    if not secret or len(secret) < 32:
        return 503, {"error": "Bot endpoint not configured"}
    if len(body) > MAX_BODY:
        return 413, {"error": "Payload too large"}
    now = int(time.time() if now is None else now)
    try:
        stamp = int(headers.get("x-bot-timestamp", ""))
        signature = headers.get("x-bot-signature", "")
    except (ValueError, TypeError):
        return 401, {"error": "Invalid signature"}
    if abs(now - stamp) > MAX_SKEW or len(signature) != 64:
        return 401, {"error": "Invalid signature"}
    message = str(stamp).encode() + b"." + body
    expected = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return 401, {"error": "Invalid signature"}
    try:
        payload = json.loads(body)
        tick_id = payload["tick_id"]
        bots = payload["bots"]
        if (not isinstance(tick_id, str) or len(tick_id) != 36
                or not isinstance(bots, dict) or len(bots) != 10
                or set(bots) != {f"bot-{i:02d}" for i in range(1, 11)}):
            raise ValueError()
        for item in bots.values():
            if (not isinstance(item, dict) or not isinstance(item.get("xp"), int)
                    or not 0 <= item["xp"] <= 100000000):
                raise ValueError()
    except (ValueError, TypeError, KeyError):
        return 400, {"error": "Invalid tick"}
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    with _db(database) as db:
        db.execute("BEGIN IMMEDIATE")
        existing = db.execute("SELECT payload FROM bot_ticks WHERE tick_id=?", (tick_id,)).fetchone()
        if existing:
            if existing[0] != body.decode("utf-8"):
                return 409, {"error": "Conflicting tick id"}
            return 200, {"ok": True, "duplicate": True}
        db.execute("INSERT INTO bot_ticks VALUES (?,?,?)", (tick_id, body.decode("utf-8"), now))
    return 201, {"ok": True, "duplicate": False}
