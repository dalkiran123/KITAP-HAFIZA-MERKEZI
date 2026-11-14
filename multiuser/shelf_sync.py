"""Optimistic revision control for cross-device shelf updates.

A client must send the revision it last read. Conflicts are rejected rather
than silently overwriting another device's changes.
"""
import json
import sqlite3

def ensure_sync(db):
    db.execute("""CREATE TABLE IF NOT EXISTS shelf_sync (
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        book_id TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision >= 1),
        state_json TEXT NOT NULL,
        PRIMARY KEY(user_id,book_id))""")
    # Import records from the original unversioned prototype on every access.
    # INSERT OR IGNORE preserves revisions and never overwrites newer edits.
    legacy = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='shelves'").fetchone()
    if legacy:
        with db:
            db.execute("""INSERT OR IGNORE INTO shelf_sync(user_id,book_id,revision,state_json)
                SELECT user_id,book_id,1,state_json FROM shelves""")

def read_sync(db,user_id):
    ensure_sync(db)
    rows=db.execute('SELECT book_id,revision,state_json FROM shelf_sync WHERE user_id=? ORDER BY book_id',(user_id,))
    return [{'book_id':bid,'revision':rev,'state':json.loads(state)} for bid,rev,state in rows]

def update_sync(db,user_id,book_id,state,expected_revision):
    if not isinstance(book_id,str) or not 1<=len(book_id)<=256:
        raise ValueError('Invalid book id')
    if type(expected_revision) is not int or expected_revision<0:
        raise ValueError('Invalid revision')
    if not isinstance(state,dict):
        raise ValueError('Invalid state')
    allowed={'read','done','listened','lastRead','lastListened','notes'}
    if set(state)-allowed:
        raise ValueError('Unsupported fields')
    if any(k in state and type(state[k]) is not bool for k in ('read','done','listened')):
        raise ValueError('Invalid flags')
    if any(k in state and state[k] is not None and not isinstance(state[k],str)
           for k in ('lastRead','lastListened','notes')):
        raise ValueError('Invalid text')
    encoded=json.dumps(state,ensure_ascii=False,sort_keys=True)
    if len(encoded.encode())>32768:
        raise ValueError('State too large')
    ensure_sync(db)
    with db:
        if expected_revision==0:
            try:
                db.execute('INSERT INTO shelf_sync(user_id,book_id,revision,state_json) VALUES(?,?,1,?)',
                           (user_id,book_id,encoded))
                return 1
            except sqlite3.IntegrityError:
                raise ValueError('Revision conflict')
        cursor=db.execute("""UPDATE shelf_sync SET revision=revision+1,state_json=?
            WHERE user_id=? AND book_id=? AND revision=?""",
            (encoded,user_id,book_id,expected_revision))
        if cursor.rowcount!=1:
            raise ValueError('Revision conflict')
        return expected_revision+1
