"""Lossless staging of a V3 phone backup, without overwriting user data.

The original JSON is preserved byte-for-byte as a private SQLite BLOB. This
is a staging mechanism, NOT proof that every field has been migrated into the
new relational tables. Never commit user backups to Git.
"""
import hashlib
import json

MAX_BACKUP_BYTES=20*1024*1024

def ensure_archive(db):
    db.execute("""CREATE TABLE IF NOT EXISTS backup_archives(
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        fingerprint TEXT NOT NULL,
        payload BLOB NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(user_id,fingerprint))""")

def stage_backup(db,user_id,raw_bytes):
    if not isinstance(raw_bytes,bytes) or not 1<=len(raw_bytes)<=MAX_BACKUP_BYTES:
        raise ValueError('Invalid backup size')
    try:
        payload=json.loads(raw_bytes.decode('utf-8'))
    except (ValueError,UnicodeError) as exc:
        raise ValueError('Invalid JSON backup') from exc
    from import_backup import preview
    details=preview(payload)
    fingerprint=hashlib.sha256(raw_bytes).hexdigest()
    ensure_archive(db)
    with db:
        if not db.execute('SELECT 1 FROM users WHERE id=?',(user_id,)).fetchone():
            raise ValueError('Unknown user')
        db.execute('INSERT OR IGNORE INTO backup_archives(user_id,fingerprint,payload) VALUES(?,?,?)',
                   (user_id,fingerprint,raw_bytes))
    return {'fingerprint':fingerprint,'bytes':len(raw_bytes),'books':details['books'],
            'status':'staged_only','warning':'Do not delete the original phone backup.'}

def restore_bytes(db,user_id,fingerprint):
    ensure_archive(db)
    row=db.execute('SELECT payload FROM backup_archives WHERE user_id=? AND fingerprint=?',
                   (user_id,fingerprint)).fetchone()
    return row[0] if row else None
