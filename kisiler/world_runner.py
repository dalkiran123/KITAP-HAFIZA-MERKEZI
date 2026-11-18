#!/usr/bin/env python3
"""One scheduled command for reading, fictional life and persona evolution.

Run from kisiler/: python world_runner.py
Requires BOOKCENTER_PEOPLE_DB pointing to a persistent SQLite file.
Safe to retry: hourly reading and daily life are idempotent.
"""
import json
import people_engine
from life_continuity import simulate_day
from persona_evolution import evolve


def run(db):
    reading = people_engine.tick(db)
    life = simulate_day(db)
    evolution = []
    for person_id in range(1, 11):
        progress = evolve(db, person_id)
        evolution.append({"person_id": person_id, "experience": progress["experience"],
                          "curiosity": progress["current"]["traits"]["curiosity"]})
    return {"reading": reading, "life": life, "evolution": evolution,
            "simulation": True}


if __name__ == "__main__":
    db = people_engine.connect()
    try:
        print(json.dumps(run(db), ensure_ascii=False))
    finally:
        db.close()
