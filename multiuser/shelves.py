"""Per-user book shelf records for the isolated SQLite prototype."""
import json

def ensure_shelves(db):
    db.execute("""CREATE TABLE IF NOT EXISTS shelves(
      user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      book_id TEXT NOT NULL,
      state_json TEXT NOT NULL,
      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(user_id,book_id))""")

def save_book(db,user_id,book_id,state):
    if not isinstance(book_id,str) or not 1 <= len(book_id) <= 256:
        raise ValueError('Invalid book id')
    if not isinstance(state,dict):
        raise ValueError('Invalid book state')
    allowed={'read','done','listened','lastRead','lastListened','notes'}
    if set(state)-allowed:
        raise ValueError('Unsupported state fields')
    if any(k in state and type(state[k]) is not bool for k in ('read','done','listened')):
        raise ValueError('Invalid flags')
    if any(k in state and state[k] is not None and not isinstance(state[k],str) for k in ('lastRead','lastListened','notes')):
        raise ValueError('Invalid text')
    encoded=json.dumps(state,ensure_ascii=False,sort_keys=True)
    if len(encoded.encode('utf-8'))>32768:
        raise ValueError('State too large')
    ensure_shelves(db)
    with db:
        db.execute("""INSERT INTO shelves(user_id,book_id,state_json)
          VALUES(?,?,?) ON CONFLICT(user_id,book_id) DO UPDATE SET
          state_json=excluded.state_json,updated_at=CURRENT_TIMESTAMP""",
          (user_id,book_id,encoded))

def list_books(db,user_id):
    ensure_shelves(db)
    return [{'book_id':book_id,'state':json.loads(state)}
            for book_id,state in db.execute(
              'SELECT book_id,state_json FROM shelves WHERE user_id=? ORDER BY book_id',(user_id,)).fetchall()]
