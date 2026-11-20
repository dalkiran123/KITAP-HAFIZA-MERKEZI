"""One-time chess-only fresh start. Run manually on PythonAnywhere after deploying.
Creates a backup before deleting chess data. Does not touch other BOOK CENTER tables.
"""
import os
import shutil
import sqlite3
from datetime import datetime, timezone

DB = os.environ.get("BOOK_CHESS_DB", os.path.expanduser("~/BOOK_DATA/chess.sqlite3"))
TABLES = ("chess_messages", "chess_lobby_watching", "chess_lobby_invites", "chess_rooms", "chess_lobby_players")

def main():
    if not os.path.isfile(DB):
        raise SystemExit("Chess database not found; nothing was deleted: " + DB)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = DB + ".backup-before-reset-" + stamp
    with sqlite3.connect(DB, timeout=15) as con:
        con.execute("PRAGMA busy_timeout=15000")
        existing = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        present = [t for t in TABLES if t in existing]
        if not present:
            raise SystemExit("No chess tables found; nothing was deleted")
        with sqlite3.connect(backup) as dest:
            con.backup(dest)
        con.execute("BEGIN IMMEDIATE")
        try:
            counts = {t: con.execute('SELECT COUNT(*) FROM "' + t + '"').fetchone()[0] for t in present}
            for t in present:
                con.execute('DELETE FROM "' + t + '"')
            con.commit()
        except Exception:
            con.rollback()
            raise
    print("Chess reset completed:", counts)
    print("Backup:", backup)
    print("Other tables left unchanged.")

if __name__ == "__main__":
    main()
