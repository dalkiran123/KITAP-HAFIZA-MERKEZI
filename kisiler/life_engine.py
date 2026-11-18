"""Deterministic, autonomous *fictional* life events for BOOK CENTER personas.

Only simulated profiles. No real-world actions, external messages or claims
about the lives of real people. Each day is idempotent and event-sourced.
"""
import datetime as dt
import json
import random

EVENTS = (
    ("work", "İş hayatında yeni bir gelişme yaşadı.", "career"),
    ("friendship", "Yeni bir arkadaşlık kurdu.", "social"),
    ("move", "Yeni bir eve taşınmaya karar verdi.", "home"),
    ("study", "Yeni bir eğitim programına başladı.", "education"),
    ("family", "Ailesiyle ilgili önemli bir karar aldı.", "family"),
    ("career", "Yeni bir iş fırsatını değerlendirmeye başladı.", "career"),
    ("relationship", "Yakın bir ilişkisi hakkında önemli bir karar aldı.", "social"),
    ("finance", "Kişisel bütçesini yeniden düzenledi.", "finance"),
)


def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS life_state (
      person_id INTEGER PRIMARY KEY, phase TEXT NOT NULL DEFAULT 'stable',
      latest_event_id INTEGER, updated_at TEXT NOT NULL,
      FOREIGN KEY(person_id) REFERENCES people(id));
    CREATE TABLE IF NOT EXISTS life_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INTEGER NOT NULL,
      day TEXT NOT NULL, event_key TEXT NOT NULL, category TEXT NOT NULL,
      description TEXT NOT NULL, simulated INTEGER NOT NULL DEFAULT 1,
      UNIQUE(person_id,day), FOREIGN KEY(person_id) REFERENCES people(id));
    """)


def simulate_day(db, day=None):
    day = day or dt.datetime.now(dt.timezone.utc).date().isoformat()
    dt.date.fromisoformat(day)
    ensure_schema(db)
    created = 0
    with db:
        people = db.execute("SELECT id FROM people WHERE simulated=1 ORDER BY id").fetchall()
        for (pid,) in people:
            rng = random.Random(f"bookcenter-life-v1:{pid}:{day}")
            # Not every person has a significant event every day.
            if rng.random() >= 0.38:
                continue
            key, description, category = EVENTS[rng.randrange(len(EVENTS))]
            cursor = db.execute(
                "INSERT OR IGNORE INTO life_events(person_id,day,event_key,category,description) "
                "VALUES(?,?,?,?,?)", (pid,day,key,category,description))
            if cursor.rowcount:
                created += 1
                db.execute(
                    "INSERT INTO life_state(person_id,phase,latest_event_id,updated_at) "
                    "VALUES(?,?,?,?) ON CONFLICT(person_id) DO UPDATE SET "
                    "phase=excluded.phase,latest_event_id=excluded.latest_event_id,"
                    "updated_at=excluded.updated_at",
                    (pid,category,cursor.lastrowid,day))
    return {"day":day,"created":created,"simulated":True}


def timeline(db, person_id, limit=30):
    rows = db.execute(
        "SELECT day,event_key,category,description FROM life_events "
        "WHERE person_id=? ORDER BY day DESC,id DESC LIMIT ?",
        (person_id, max(1,min(int(limit),100)))).fetchall()
    return [{"day":r[0],"key":r[1],"category":r[2],
             "description":r[3],"simulated":True} for r in rows]
