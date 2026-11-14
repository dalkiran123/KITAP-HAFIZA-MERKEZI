"""Book Memory Center: isolated database foundation (not a live web server)."""
import hashlib
import hmac
import os
import sqlite3

MAX_USERS = 100
ITERATIONS = 600_000

def connect(path):
    db = sqlite3.connect(path)
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=5000')
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
      salt BLOB NOT NULL, password_hash BLOB NOT NULL,
      role TEXT NOT NULL DEFAULT 'reader' CHECK(role IN ('reader','admin')),
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS reading (
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      book_id TEXT NOT NULL, completed_at TEXT NOT NULL,
      PRIMARY KEY(user_id,book_id,completed_at)
    );
    CREATE TABLE IF NOT EXISTS ratings (
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      book_id TEXT NOT NULL, score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 10),
      PRIMARY KEY(user_id,book_id)
    );
    CREATE TABLE IF NOT EXISTS migration_imports (
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      import_id TEXT NOT NULL, imported_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(user_id,import_id)
    );
    """)
    return db

def create_user(db, username, password, *, role='reader'):
    if not isinstance(username,str) or not (3 <= len(username) <= 32) or not all(c.isalnum() or c in '_-' for c in username):
        raise ValueError('Invalid username')
    if not isinstance(password,str) or len(password) < 12:
        raise ValueError('Password must be at least 12 characters')
    if role not in ('reader','admin'):
        raise ValueError('Invalid role')
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac('sha256',password.encode(),salt,ITERATIONS)
    with db:
        db.execute('BEGIN IMMEDIATE') if not db.in_transaction else None
        if db.execute('SELECT COUNT(*) FROM users').fetchone()[0] >= MAX_USERS:
            raise ValueError('User capacity reached')
        cur = db.execute('INSERT INTO users(username,salt,password_hash,role) VALUES(?,?,?,?)',(username,salt,digest,role))
        return cur.lastrowid

def authenticate(db, username, password):
    row = db.execute('SELECT id,salt,password_hash,role FROM users WHERE username=?',(username,)).fetchone()
    if row is None:
        return None
    digest = hashlib.pbkdf2_hmac('sha256',password.encode(),row[1],ITERATIONS)
    return {'id':row[0],'role':row[3]} if hmac.compare_digest(digest,row[2]) else None

def rate_book(db, user_id, book_id, score):
    if type(score) is not int or not 1 <= score <= 10:
        raise ValueError('Score must be 1..10')
    with db:
        db.execute('INSERT INTO ratings(user_id,book_id,score) VALUES(?,?,?) ON CONFLICT(user_id,book_id) DO UPDATE SET score=excluded.score',(user_id,book_id,score))

def leaderboard(db):
    return db.execute('SELECT u.username,COUNT(DISTINCT r.book_id) AS books FROM users u LEFT JOIN reading r ON r.user_id=u.id GROUP BY u.id ORDER BY books DESC,u.username ASC').fetchall()
