"""Continuity-aware fictional life simulation.

Separate from the lightweight legacy life_engine. Each character's durable
state drives future choices. Events never assert facts about real people.
"""
import datetime as dt
import json
import random

DEFAULT = {"career":"employed","home":"settled","education":"none",
           "social":"stable","finance":"stable","family":"stable"}


def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS life_world_state (
      person_id INTEGER PRIMARY KEY, state_json TEXT NOT NULL,
      last_day TEXT, FOREIGN KEY(person_id) REFERENCES people(id));
    CREATE TABLE IF NOT EXISTS life_world_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INTEGER NOT NULL,
      day TEXT NOT NULL, event_key TEXT NOT NULL, description TEXT NOT NULL,
      before_json TEXT NOT NULL, after_json TEXT NOT NULL,
      simulated INTEGER NOT NULL DEFAULT 1, UNIQUE(person_id,day));
    """)


def get_state(db, person_id):
    row = db.execute("SELECT state_json FROM life_world_state WHERE person_id=?",
                     (person_id,)).fetchone()
    return json.loads(row[0]) if row else dict(DEFAULT)


def choices(state):
    result = [
        ("study_start", "Yeni bir eğitim programına başladı.", "education", "studying"),
        ("finance_plan", "Yeni bir tasarruf planı hazırladı.", "finance", "planning"),
        ("new_friend", "Yeni bir arkadaşlık kurdu.", "social", "expanding"),
    ]
    if state["career"] == "employed":
        result.append(("job_change", "Yeni bir işe geçti.", "career", "new_job"))
    elif state["career"] == "new_job":
        result.append(("job_settled", "Yeni işine alışmaya başladı.", "career", "employed"))
    if state["home"] == "settled":
        result.append(("move", "Yeni bir eve taşındı.", "home", "new_home"))
    elif state["home"] == "new_home":
        result.append(("unpack", "Yeni evine yerleşti.", "home", "settled"))
    if state["education"] == "studying":
        result.append(("graduation", "Eğitim programını tamamladı.", "education", "completed"))
    if state["finance"] == "planning":
        result.append(("savings", "Tasarruf hedefinde ilerleme kaydetti.", "finance", "stable"))
    return result


def simulate_day(db, day=None):
    day = day or dt.datetime.now(dt.timezone.utc).date().isoformat()
    dt.date.fromisoformat(day)
    ensure_schema(db)
    created = 0
    with db:
        for (pid,) in db.execute("SELECT id FROM people WHERE simulated=1 ORDER BY id"):
            row = db.execute("SELECT last_day FROM life_world_state WHERE person_id=?", (pid,)).fetchone()
            if row and row[0] and day <= row[0]:
                continue
            before = get_state(db, pid)
            after = dict(before)
            rng = random.Random(f"world-v2:{pid}:{day}")
            if rng.random() < 0.40:
                key, description, field, value = rng.choice(choices(before))
                after[field] = value
                cursor = db.execute(
                    "INSERT OR IGNORE INTO life_world_events(person_id,day,event_key,description,before_json,after_json) "
                    "VALUES(?,?,?,?,?,?)",
                    (pid,day,key,description,json.dumps(before),json.dumps(after)))
                created += cursor.rowcount
            db.execute(
                "INSERT INTO life_world_state(person_id,state_json,last_day) VALUES(?,?,?) "
                "ON CONFLICT(person_id) DO UPDATE SET state_json=excluded.state_json,last_day=excluded.last_day",
                (pid,json.dumps(after),day))
    return {"day":day,"created":created,"simulated":True}


def history(db, person_id, limit=30):
    rows = db.execute(
        "SELECT day,event_key,description,before_json,after_json "
        "FROM life_world_events WHERE person_id=? ORDER BY day DESC,id DESC LIMIT ?",
        (person_id,max(1,min(int(limit),100)))).fetchall()
    return [{"day":r[0],"key":r[1],"description":r[2],
             "before":json.loads(r[3]),"after":json.loads(r[4]),"simulated":True}
            for r in rows]
