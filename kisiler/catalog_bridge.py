"""Optional catalog bridge for simulated readers.
Only explicitly supplied real catalog IDs are imported. No invented books.
"""
import json
import sqlite3


def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS catalog_books (
      book_id TEXT PRIMARY KEY,
      title TEXT NOT NULL,
      author TEXT NOT NULL DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS person_books (
      person_id INTEGER NOT NULL,
      book_id TEXT NOT NULL,
      minutes INTEGER NOT NULL DEFAULT 0,
      completed_at TEXT,
      PRIMARY KEY(person_id, book_id),
      FOREIGN KEY(book_id) REFERENCES catalog_books(book_id)
    );
    """)


def import_catalog(db, records):
    if not isinstance(records, list):
        raise ValueError("Catalog must be a list")
    validated = []
    for item in records:
        if not isinstance(item, dict):
            raise ValueError("Each record must be an object")
        book_id = str(item.get("id", "")).strip()
        title = str(item.get("title", "")).strip()
        author = str(item.get("author", "")).strip()
        if not book_id or not title or len(book_id) > 160 or len(title) > 500:
            raise ValueError("Book ID and title are required")
        validated.append((book_id, title, author))
    ensure_schema(db)
    with db:
        for record in validated:
            db.execute(
                "INSERT INTO catalog_books(book_id,title,author) VALUES(?,?,?) "
                "ON CONFLICT(book_id) DO UPDATE SET title=excluded.title,author=excluded.author",
                record)
    return len(validated)


def assign_book(db, person_id, book_id):
    ensure_schema(db)
    if not db.execute("SELECT 1 FROM people WHERE id=? AND simulated=1", (person_id,)).fetchone():
        raise ValueError("Unknown simulated person")
    if not db.execute("SELECT 1 FROM catalog_books WHERE book_id=?", (book_id,)).fetchone():
        raise ValueError("Unknown book ID")
    with db:
        db.execute("INSERT OR IGNORE INTO person_books(person_id,book_id) VALUES(?,?)",
                   (person_id, book_id))


def reading_progress(db, person_id):
    ensure_schema(db)
    rows = db.execute(
        "SELECT c.book_id,c.title,c.author,p.minutes,p.completed_at "
        "FROM person_books p JOIN catalog_books c ON c.book_id=p.book_id "
        "WHERE p.person_id=? ORDER BY c.title", (person_id,)).fetchall()
    return [{"id":r[0], "title":r[1], "author":r[2], "minutes":r[3],
             "completed_at":r[4]} for r in rows]
