"""Controlled, auditable fictional-persona development.

The baseline is user-owned; the evolving layer is generated from recorded
simulated reading activity. No private details of real people are required.
"""
import json
import sqlite3
from persona_engine import ensure_schema, get_persona


def ensure_evolution_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS persona_evolution (
      person_id INTEGER PRIMARY KEY,
      last_activity_id INTEGER NOT NULL DEFAULT 0,
      experience INTEGER NOT NULL DEFAULT 0,
      curiosity_delta INTEGER NOT NULL DEFAULT 0,
      notes_json TEXT NOT NULL DEFAULT '[]',
      FOREIGN KEY(person_id) REFERENCES people(id))""")


def evolve(db, person_id):
    """Idempotently record new simulated-reading experiences.

    Does not alter the user's chosen baseline personality. Bounded drift:
    curiosity may rise by at most 10 points, one point per 10 activities.
    """
    baseline = get_persona(db, person_id)
    ensure_evolution_schema(db)
    with db:
        db.execute("INSERT OR IGNORE INTO persona_evolution(person_id) VALUES(?)", (person_id,))
        previous = db.execute(
            "SELECT last_activity_id,experience FROM persona_evolution WHERE person_id=?",
            (person_id,)).fetchone()
        events = db.execute(
            "SELECT id,description FROM activity WHERE person_id=? AND kind='simulated_reading' AND id>? "
            "ORDER BY id", (person_id, previous[0])).fetchall()
        experience = previous[1] + len(events)
        last_id = events[-1][0] if events else previous[0]
        drift = min(10, experience // 10)
        db.execute(
            "UPDATE persona_evolution SET last_activity_id=?,experience=?,curiosity_delta=? WHERE person_id=?",
            (last_id, experience, drift, person_id))
    current = dict(baseline)
    current["traits"] = dict(baseline["traits"])
    current["traits"]["curiosity"] = min(100, current["traits"]["curiosity"] + drift)
    return {"person_id": person_id, "baseline": baseline, "current": current,
            "experience": experience, "simulated": True}


def reset_evolution(db, person_id):
    """User may reset acquired changes without losing baseline or reading history."""
    ensure_evolution_schema(db)
    with db:
        db.execute("DELETE FROM persona_evolution WHERE person_id=?", (person_id,))
