"""Validated, idempotent import of a V3 phone backup into private SQLite.
Not an HTTP endpoint. Caller must authenticate and authorize user_id.
Never store uploaded backups in a public repository.
"""
import hashlib
import json
from datetime import datetime, timezone

def preview(payload):
    if not isinstance(payload, dict) or payload.get('version') not in (2, 3):
        raise ValueError('Unsupported backup version')
    books = payload.get('books')
    if not isinstance(books, list) or len(books) > 20000:
        raise ValueError('Invalid books')
    ids = set()
    ratings = []
    events = []
    for b in books:
        if not isinstance(b, dict) or not all(isinstance(b.get(k), str) for k in ('id','name','author','summary')):
            raise ValueError('Invalid book')
        book_id = b['id']
        if not book_id or len(book_id) > 256 or book_id in ids:
            raise ValueError('Duplicate or invalid book id')
        ids.add(book_id)
        rating = b.get('rating')
        if rating is not None:
            if type(rating) is not int or not 1 <= rating <= 10:
                raise ValueError('Invalid rating')
            ratings.append((book_id, rating))
        history = b.get('history', [])
        if not isinstance(history, list) or len(history) > 10000:
            raise ValueError('Invalid history')
        for event in history:
            if not isinstance(event, dict) or event.get('type') not in ('read','listen') or not isinstance(event.get('date'),str):
                raise ValueError('Invalid history event')
            date = event['date']
            try:
                dt = datetime.fromisoformat(date.replace('Z','+00:00'))
                if dt.tzinfo is None:
                    raise ValueError('Timezone required')
            except (ValueError, TypeError):
                raise ValueError('Invalid event date')
            events.append((book_id, date, event['type']))
        if (b.get('read') or b.get('done') or b.get('listened')) and not history:
            # Historical completion without an event timestamp cannot be fabricated.
            pass
    requests = payload.get('requests', [])
    request_history = payload.get('requestHistory', [])
    storage = payload.get('localStorage', {})
    if not isinstance(requests,list) or not isinstance(request_history,list) or not isinstance(storage,dict):
        raise ValueError('Invalid backup sections')
    if any(not isinstance(k,str) or not k.startswith('kitap-hafiza') or not isinstance(v,str) for k,v in storage.items()):
        raise ValueError('Unexpected local storage')
    return {'books':len(books),'ratings':len(ratings),'events':len(events),'requests':len(requests),
            'request_history':len(request_history),'storage_keys':len(storage),
            'ratings_rows':ratings,'event_rows':events}

def import_backup(db, user_id, payload, *, confirmed=False):
    if not confirmed:
        raise ValueError('Explicit confirmation required')
    details = preview(payload)
    # Hash canonical JSON for repeat-safe imports.
    fingerprint = hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    with db:
        if not db.execute('SELECT 1 FROM users WHERE id=?',(user_id,)).fetchone():
            raise ValueError('Unknown user')
        if db.execute('SELECT 1 FROM migration_imports WHERE user_id=? AND import_id=?',(user_id,fingerprint)).fetchone():
            return {'status':'already_imported','fingerprint':fingerprint}
        for book_id,score in details['ratings_rows']:
            db.execute('INSERT INTO ratings(user_id,book_id,score) VALUES(?,?,?) ON CONFLICT(user_id,book_id) DO UPDATE SET score=excluded.score',(user_id,book_id,score))
        # Reading table stores timestamps, but not event type; keep only actual read events.
        for book_id,date,event_type in details['event_rows']:
            if event_type == 'read':
                db.execute('INSERT OR IGNORE INTO reading(user_id,book_id,completed_at) VALUES(?,?,?)',(user_id,book_id,date))
        db.execute('INSERT INTO migration_imports(user_id,import_id) VALUES(?,?)',(user_id,fingerprint))
    return {'status':'imported','fingerprint':fingerprint,'ratings':details['ratings'],'read_events':sum(e[2]=='read' for e in details['event_rows']),
            'warning':'Book notes, completion flags, listening events and requests are not yet migrated; do not delete original backup.'}
