"""Private reading-history operations for the multi-user prototype."""
from datetime import datetime

def _date(value):
    if not isinstance(value,str) or len(value)>64:
        raise ValueError('Invalid date')
    try:
        d=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc:
        raise ValueError('Invalid date') from exc
    if d.tzinfo is None:
        raise ValueError('Timezone required')
    return value

def add_read(db,user_id,book_id,completed_at):
    if not isinstance(book_id,str) or not 1<=len(book_id)<=256:
        raise ValueError('Invalid book id')
    _date(completed_at)
    with db:
        db.execute('INSERT OR IGNORE INTO reading(user_id,book_id,completed_at) VALUES(?,?,?)',
                   (user_id,book_id,completed_at))

def list_reads(db,user_id):
    return [{'book_id':bid,'completed_at':date}
            for bid,date in db.execute('SELECT book_id,completed_at FROM reading WHERE user_id=? ORDER BY completed_at DESC,book_id',(user_id,))]
