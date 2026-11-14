"""Compatibility facade over the canonical revisioned shelf store.

New clients should use /my/sync with expected_revision to prevent lost updates.
Legacy save_book performs last-write-wins and must not be used for device sync.
"""
from shelf_sync import ensure_sync, read_sync, update_sync


def ensure_shelves(db):
    """Maintain legacy call compatibility; the canonical table is shelf_sync."""
    ensure_sync(db)


def save_book(db, user_id, book_id, state):
    """Legacy upsert. Existing API clients have no revision field."""
    ensure_sync(db)
    row = db.execute(
        'SELECT revision FROM shelf_sync WHERE user_id=? AND book_id=?',
        (user_id, book_id)).fetchone()
    revision = row[0] if row else 0
    update_sync(db, user_id, book_id, state, revision)


def list_books(db, user_id):
    return [{'book_id': entry['book_id'], 'state': entry['state']}
            for entry in read_sync(db, user_id)]
