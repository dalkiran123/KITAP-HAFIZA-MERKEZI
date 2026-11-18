"""Deterministic, fictional bot-to-bot relationships.

No external messaging, real-person impersonation or private data.
The relationship state is durable and each day is processed at most once.
"""
import datetime as dt
import random

KINDS = ("strangers", "acquaintances", "friends", "distant")


def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS social_relations (
      person_a INTEGER NOT NULL, person_b INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'strangers',
      closeness INTEGER NOT NULL DEFAULT 0,
      updated_day TEXT,
      PRIMARY KEY(person_a,person_b),
      CHECK(person_a < person_b),
      CHECK(closeness BETWEEN 0 AND 100));
    CREATE TABLE IF NOT EXISTS social_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      person_a INTEGER NOT NULL, person_b INTEGER NOT NULL,
      day TEXT NOT NULL, event_key TEXT NOT NULL,
      description TEXT NOT NULL, simulated INTEGER NOT NULL DEFAULT 1,
      UNIQUE(person_a,person_b,day));
    """)


def simulate_day(db, day=None):
    day = day or dt.datetime.now(dt.timezone.utc).date().isoformat()
    dt.date.fromisoformat(day)
    ensure_schema(db)
    created = 0
    with db:
        ids = [r[0] for r in db.execute("SELECT id FROM people WHERE simulated=1 ORDER BY id")]
        for a_index, a in enumerate(ids):
            for b in ids[a_index + 1:]:
                rng = random.Random(f"social-v1:{a}:{b}:{day}")
                if rng.random() >= 0.08:
                    continue
                row = db.execute(
                    "SELECT closeness,updated_day FROM social_relations WHERE person_a=? AND person_b=?",
                    (a,b)).fetchone()
                if row and row[1] and day <= row[1]:
                    continue
                closeness = row[0] if row else 0
                delta = rng.choice((-8,-4,5,8,12))
                updated = max(0,min(100,closeness+delta))
                status = ("friends" if updated >= 45 else
                          "acquaintances" if updated >= 10 else
                          "distant" if row and updated < closeness else "strangers")
                key = "bond" if delta > 0 else "distance"
                description = ("Birbirleriyle yakınlaştılar." if delta > 0 else
                               "Aralarındaki iletişim zayıfladı.")
                cursor = db.execute(
                    "INSERT OR IGNORE INTO social_events(person_a,person_b,day,event_key,description) "
                    "VALUES(?,?,?,?,?)", (a,b,day,key,description))
                if cursor.rowcount:
                    created += 1
                    db.execute(
                        "INSERT INTO social_relations(person_a,person_b,status,closeness,updated_day) "
                        "VALUES(?,?,?,?,?) ON CONFLICT(person_a,person_b) DO UPDATE SET "
                        "status=excluded.status,closeness=excluded.closeness,"
                        "updated_day=excluded.updated_day",
                        (a,b,status,updated,day))
    return {"day":day,"created":created,"simulated":True}


def relations(db, person_id):
    rows = db.execute(
        "SELECT person_a,person_b,status,closeness FROM social_relations "
        "WHERE person_a=? OR person_b=? ORDER BY closeness DESC,person_a,person_b",
        (person_id,person_id)).fetchall()
    return [{"person_id":r[1] if r[0] == person_id else r[0],
             "status":r[2],"closeness":r[3],"simulated":True} for r in rows]
