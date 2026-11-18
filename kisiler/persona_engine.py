"""Editable fictional persona profiles for simulated BOOK CENTER readers.

All profiles are synthetic. Do not impersonate a real person without their consent.
Profiles are stored in a separate SQLite table; reading history is not modified.
"""
import json

DEFAULT = {
    "age": None, "occupation": "", "education": "", "background": "",
    "interests": [], "preferred_genres": [], "speaking_style": "doğal",
    "traits": {"curiosity": 50, "empathy": 50, "humor": 50,
               "competitiveness": 50, "sociability": 50, "patience": 50},
    "initiative": "medium", "daily_reading_goal_minutes": 30,
    "behavior_rules": [], "memory_enabled": True
}
TRAITS = set(DEFAULT["traits"])
INITIATIVES = {"low", "medium", "high"}


def ensure_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS person_personas (
        person_id INTEGER PRIMARY KEY, profile_json TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(person_id) REFERENCES people(id))""")


def validate(profile):
    if not isinstance(profile, dict):
        raise ValueError("Profile must be an object")
    if set(profile) - set(DEFAULT):
        raise ValueError("Unknown persona field")
    result = dict(DEFAULT)
    result.update(profile)
    age = result["age"]
    if age is not None and (type(age) is not int or not 18 <= age <= 100):
        raise ValueError("Fictional age must be 18-100")
    for field in ("occupation", "education", "background", "speaking_style"):
        if not isinstance(result[field], str) or len(result[field]) > 500:
            raise ValueError("Invalid text field: " + field)
    for field in ("interests", "preferred_genres", "behavior_rules"):
        val = result[field]
        if not isinstance(val, list) or len(val) > 20 or any(
            not isinstance(x, str) or len(x) > 250 for x in val
        ):
            raise ValueError("Invalid list field: " + field)
    if not isinstance(result["traits"], dict) or set(result["traits"]) != TRAITS:
        raise ValueError("All six traits are required")
    if any(type(v) is not int or not 0 <= v <= 100 for v in result["traits"].values()):
        raise ValueError("Traits must be integers between 0 and 100")
    if result["initiative"] not in INITIATIVES:
        raise ValueError("Invalid initiative")
    if type(result["daily_reading_goal_minutes"]) is not int or not 0 <= result["daily_reading_goal_minutes"] <= 480:
        raise ValueError("Invalid reading goal")
    if type(result["memory_enabled"]) is not bool:
        raise ValueError("Invalid memory flag")
    return result


def set_persona(db, person_id, profile):
    data = validate(profile)
    if not db.execute("SELECT 1 FROM people WHERE id=? AND simulated=1", (person_id,)).fetchone():
        raise ValueError("Only existing simulated readers may have personas")
    ensure_schema(db)
    with db:
        db.execute("""INSERT INTO person_personas(person_id,profile_json)
                      VALUES(?,?) ON CONFLICT(person_id) DO UPDATE SET
                      profile_json=excluded.profile_json,
                      updated_at=CURRENT_TIMESTAMP""",
                   (person_id, json.dumps(data, ensure_ascii=False)))
    return data


def get_persona(db, person_id):
    ensure_schema(db)
    row = db.execute("SELECT profile_json FROM person_personas WHERE person_id=?", (person_id,)).fetchone()
    return json.loads(row[0]) if row else validate({})
