"""SQLite-backed session store for the multiuser prototype.

Only SHA-256 token digests are persisted. A server restart does not log out
users, and revocation is shared by processes using the same SQLite file.
"""
import hashlib
import secrets
import time
from contextlib import closing
from user_store import connect
from sessions import SESSION_TTL_SECONDS


class SQLiteSessionManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        db = connect(self.db_path)
        db.execute("""CREATE TABLE IF NOT EXISTS login_sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            expires REAL NOT NULL
        )""")
        return db

    def issue(self, user_id, role='reader'):
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode('utf-8')).hexdigest()
        with closing(self._connect()) as db, db:
            db.execute('DELETE FROM login_sessions WHERE expires <= ?', (time.time(),))
            db.execute('INSERT INTO login_sessions(token_hash,user_id,role,expires) VALUES(?,?,?,?)',
                       (digest, user_id, role, time.time() + SESSION_TTL_SECONDS))
        return token

    def lookup(self, token):
        if not isinstance(token, str) or not token or len(token) > 256:
            return None
        digest = hashlib.sha256(token.encode('utf-8')).hexdigest()
        with closing(self._connect()) as db, db:
            row = db.execute('SELECT user_id,role,expires FROM login_sessions WHERE token_hash=?',
                             (digest,)).fetchone()
            if row is None:
                return None
            if row[2] <= time.time():
                db.execute('DELETE FROM login_sessions WHERE token_hash=?', (digest,))
                return None
            return {'user_id': row[0], 'role': row[1]}

    def revoke(self, token):
        if not isinstance(token, str) or len(token) > 256:
            return
        digest = hashlib.sha256(token.encode('utf-8')).hexdigest()
        with closing(self._connect()) as db, db:
            db.execute('DELETE FROM login_sessions WHERE token_hash=?', (digest,))
