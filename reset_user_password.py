#!/usr/bin/env python3
"""Reset an existing user's password without changing their user ID or book records.

Run on PythonAnywhere from the project root:
    python3 reset_user_password.py
"""
import getpass
import hashlib
import os
import sqlite3
import sys
from pathlib import Path

from multiuser.user_store import ITERATIONS

DB_PATH = Path('/home/b2bsocialtest/BOOK_DATA/book_users.sqlite3')

def main():
    if not DB_PATH.is_file():
        sys.exit('ERROR: database not found. No changes made.')
    username = input('Existing username [Numan34]: ').strip() or 'Numan34'
    with sqlite3.connect(str(DB_PATH)) as db:
        row = db.execute(
            'SELECT id, username, role FROM users WHERE username=? COLLATE NOCASE',
            (username,),
        ).fetchone()
        if row is None:
            sys.exit('ERROR: user does not exist. No changes made.')
        print('Account:', row[1], '| ID:', row[0], '| Role:', row[2])
        password = getpass.getpass('New password (12+ characters): ')
        confirmation = getpass.getpass('Repeat new password: ')
        if len(password) < 12 or password != confirmation:
            sys.exit('ERROR: password too short or confirmation mismatch. No changes made.')
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, ITERATIONS)
        with db:
            db.execute(
                'UPDATE users SET salt=?, password_hash=? WHERE id=?',
                (salt, digest, row[0]),
            )
        print('SUCCESS: password updated. Account ID and book records unchanged.')

if __name__ == '__main__':
    main()
