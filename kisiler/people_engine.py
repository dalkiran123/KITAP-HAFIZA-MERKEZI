#!/usr/bin/env python3
"""BOOK CENTER V5.1: persistent simulated-reader engine.
Run: python people_engine.py init
     python people_engine.py tick
     python people_engine.py status
Schedule 'tick' externally (cron / PythonAnywhere scheduled task).
This engine never claims real reading by humans.
"""
import argparse
import datetime as dt
import json
import os
import random
import sqlite3

DB = os.environ.get("BOOKCENTER_PEOPLE_DB", "people.sqlite3")
NAMES = ["Luna", "Atlas", "Mira", "Deniz", "Ada", "Arda", "Ece", "Nova", "Eren", "Duru"]
UTC = dt.timezone.utc

def connect():
    db = sqlite3.connect(DB)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=5000")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS people (
      id INTEGER PRIMARY KEY, name TEXT NOT NULL, simulated INTEGER NOT NULL DEFAULT 1,
      books INTEGER NOT NULL DEFAULT 0, minutes INTEGER NOT NULL DEFAULT 0,
      level TEXT NOT NULL DEFAULT 'Okur');
    CREATE TABLE IF NOT EXISTS activity (
      id INTEGER PRIMARY KEY AUTOINCREMENT, person_id INTEGER NOT NULL,
      kind TEXT NOT NULL, description TEXT NOT NULL, occurred_at TEXT NOT NULL,
      UNIQUE(person_id,kind,occurred_at));
    CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER NOT NULL,
      receiver_id INTEGER NOT NULL, text TEXT NOT NULL,
      created_at TEXT NOT NULL, read_at TEXT);
    CREATE TABLE IF NOT EXISTS friendships (
      sender_id INTEGER NOT NULL, receiver_id INTEGER NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('pending','accepted','rejected')),
      created_at TEXT NOT NULL, PRIMARY KEY(sender_id,receiver_id));
    CREATE TABLE IF NOT EXISTS engine_ticks (
      slot TEXT PRIMARY KEY, processed_at TEXT NOT NULL);
    """)
    for i, name in enumerate(NAMES, 1):
        db.execute("INSERT OR IGNORE INTO people(id,name) VALUES(?,?)", (i,name))
    db.commit()
    return db

def tick(db, now=None):
    now = now or dt.datetime.now(UTC)
    slot = now.strftime("%Y-%m-%dT%H")
    with db:
        cursor = db.execute("INSERT OR IGNORE INTO engine_ticks(slot,processed_at) VALUES(?,?)",
                            (slot,now.isoformat()))
        if cursor.rowcount == 0:
            return {"slot":slot,"new":0,"reason":"already_processed"}
        rng = random.Random(slot)
        selected = rng.sample(range(1,11), rng.randint(2,5))
        for pid in selected:
            minutes = rng.randint(8,38)
            row = db.execute("SELECT minutes,books FROM people WHERE id=?", (pid,)).fetchone()
            # One book per 180 minutes of cumulative simulated reading, max 1 per tick.
            completed = int((row[0]+minutes)//180 > row[0]//180)
            db.execute("UPDATE people SET minutes=minutes+?,books=books+?,level=? WHERE id=?",
                       (minutes,completed,"Yetkin" if row[1]+completed>=20 else "Okur",pid))
            description = f"{minutes} dakika simüle okuma" + ("; 1 kitap tamamlandı" if completed else "")
            db.execute("INSERT INTO activity(person_id,kind,description,occurred_at) VALUES(?,?,?,?)",
                       (pid,"simulated_reading",description,now.isoformat()))
    return {"slot":slot,"new":len(selected)}

def status(db):
    rows=db.execute("SELECT id,name,books,minutes,level FROM people ORDER BY books DESC,minutes DESC").fetchall()
    return [{"id":r[0],"name":r[1],"books":r[2],"minutes":r[3],"level":r[4],"simulated":True} for r in rows]

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=["init","tick","status"])
    args=p.parse_args()
    db=connect()
    if args.command=="init": print(json.dumps({"initialized":True,"database":DB}))
    elif args.command=="tick": print(json.dumps(tick(db)))
    else: print(json.dumps(status(db),ensure_ascii=False,indent=2))
