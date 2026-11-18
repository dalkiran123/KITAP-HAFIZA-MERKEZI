"""Isolated signed bot-tick storage. Not connected to production WSGI."""
import hashlib
import hmac
import json
import sqlite3
import time
import uuid
from pathlib import Path

MAX_BODY = 65536
MAX_SKEW = 300

def _db(path):
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("CREATE TABLE IF NOT EXISTS bot_ticks (tick_id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at INTEGER NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS bot_state (bot_id TEXT PRIMARY KEY, version INTEGER NOT NULL, xp INTEGER NOT NULL)")
    return conn

def handle_tick(method, path, headers, body, *, secret, database, now=None):
    """Return HTTP status and JSON-compatible response. Never reads BOOK_DB_PATH."""
    if method != "POST" or path != "/api/bots/tick":
        return 404, {"error": "Not found"}
    if not isinstance(secret, str) or len(secret) < 32:
        return 503, {"error": "Bot endpoint not configured"}
    if not isinstance(body, bytes) or not 1 <= len(body) <= MAX_BODY:
        return 413, {"error": "Invalid body size"}
    now = int(time.time() if now is None else now)
    try:
        stamp = int(headers.get("x-bot-timestamp", ""))
        signature = headers.get("x-bot-signature", "")
    except (ValueError, TypeError, AttributeError):
        return 401, {"error": "Invalid signature"}
    if abs(now - stamp) > MAX_SKEW or not isinstance(signature, str) or len(signature) != 64:
        return 401, {"error": "Invalid signature"}
    expected = hmac.new(secret.encode(), str(stamp).encode() + b"." + body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return 401, {"error": "Invalid signature"}
    try:
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError()
        tick_id = payload["tick_id"]
        bots = payload["bots"]
        if (not isinstance(tick_id, str) or str(uuid.UUID(tick_id)) != tick_id
                or not isinstance(bots, dict) or set(bots) != {f"bot-{i:02d}" for i in range(1, 11)}):
            raise ValueError()
        for item in bots.values():
            if (not isinstance(item, dict) or type(item.get("xp")) is not int
                    or not 0 <= item["xp"] <= 100000000
                    or type(item.get("version")) is not int
                    or not 1 <= item["version"] <= 100000000):
                raise ValueError()
    except (ValueError, TypeError, KeyError, UnicodeDecodeError, OverflowError):
        return 400, {"error": "Invalid tick"}
    # Atomic transaction: a duplicate request is accepted only if bytes match.
    # Production must additionally enforce per-bot monotonic versions and authorization.
    Path(database).parent.mkdir(parents=True, exist_ok=True)
    conn = _db(database)
    try:
        conn.execute("BEGIN IMMEDIATE")
        previous = conn.execute("SELECT payload FROM bot_ticks WHERE tick_id=?", (tick_id,)).fetchone()
        if previous:
            conn.execute("ROLLBACK")
            if previous[0] != body.decode("utf-8"):
                return 409, {"error": "Conflicting tick id"}
            return 200, {"ok": True, "duplicate": True}
        for bot_id, item in bots.items():
            old = conn.execute("SELECT version, xp FROM bot_state WHERE bot_id=?", (bot_id,)).fetchone()
            if old is not None and (item["version"] != old[0] + 1 or item["xp"] < old[1]):
                conn.execute("ROLLBACK")
                return 409, {"error": "Stale bot version or decreasing xp"}
            if old is None and item["version"] != 1:
                conn.execute("ROLLBACK")
                return 409, {"error": "Initial version must be 1"}
        for bot_id, item in bots.items():
            conn.execute("INSERT INTO bot_state(bot_id,version,xp) VALUES(?,?,?) "
                         "ON CONFLICT(bot_id) DO UPDATE SET version=excluded.version,xp=excluded.xp",
                         (bot_id, item["version"], item["xp"]))
        conn.execute("INSERT INTO bot_ticks VALUES (?,?,?)", (tick_id, body.decode("utf-8"), now))
        conn.execute("COMMIT")
        return 201, {"ok": True, "duplicate": False}
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()
