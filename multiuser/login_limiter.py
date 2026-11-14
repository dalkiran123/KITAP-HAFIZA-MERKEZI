"""Shared SQLite login failure limits for the local multiuser server.

The remote address must come from a trusted reverse proxy; do not trust
X-Forwarded-For headers from arbitrary clients.
"""
import time
from contextlib import closing
from user_store import connect


class LoginLimiter:
    def __init__(self, db_path, window_seconds=300, max_failures=5):
        self.db_path=db_path
        self.window_seconds=window_seconds
        self.max_failures=max_failures

    def _db(self):
        db=connect(self.db_path)
        db.execute("""CREATE TABLE IF NOT EXISTS login_failures (
            ip TEXT NOT NULL, attempted_at REAL NOT NULL
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_login_failures_ip_time ON login_failures(ip,attempted_at)")
        return db

    def allowed(self, ip):
        now=time.time()
        with closing(self._db()) as db, db:
            db.execute('DELETE FROM login_failures WHERE attempted_at <= ?', (now-self.window_seconds,))
            count=db.execute('SELECT COUNT(*) FROM login_failures WHERE ip=?',(ip,)).fetchone()[0]
            return count < self.max_failures

    def fail(self, ip):
        now=time.time()
        with closing(self._db()) as db, db:
            db.execute('DELETE FROM login_failures WHERE attempted_at <= ?', (now-self.window_seconds,))
            db.execute('INSERT INTO login_failures(ip,attempted_at) VALUES(?,?)',(ip,now))

    def success(self, ip):
        with closing(self._db()) as db, db:
            db.execute('DELETE FROM login_failures WHERE ip=?',(ip,))
