"""Import explicitly approved fictional character profiles on the server.

Server-side operator command only; no public write endpoint or secrets in JS.
Usage: BOOKCENTER_PEOPLE_DB=/private/people.sqlite3 python persona_import.py profiles.json
Input: {"characters":[{"id":1,"name":"Luna","occupation":"...","background":"...",
"interests":["..."]}]}
"""
import argparse
import json
import os
import sqlite3
import sys

from persona_engine import DEFAULT, ensure_schema, validate


def import_profiles(db, payload):
    if not isinstance(payload, dict) or set(payload) != {"characters"}:
        raise ValueError("Expected characters object")
    characters = payload["characters"]
    if not isinstance(characters, list) or not 1 <= len(characters) <= 10:
        raise ValueError("Expected 1-10 characters")
    prepared = []
    seen = set()
    for item in characters:
        if not isinstance(item, dict) or set(item) - {"id","name","occupation","background","interests"}:
            raise ValueError("Unknown character fields")
        pid = item.get("id")
        if type(pid) is not int or not 1 <= pid <= 10 or pid in seen:
            raise ValueError("Invalid or repeated character ID")
        seen.add(pid)
        name = item.get("name")
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 35:
            raise ValueError("Invalid character name")
        fields = {k:item[k] for k in ("occupation","background","interests") if k in item}
        fields["traits"] = dict(DEFAULT["traits"])
        prepared.append((pid,name.strip(),validate(fields)))
    ensure_schema(db)
    # Validate all before changing any records.
    for pid, _, _ in prepared:
        if not db.execute("SELECT 1 FROM people WHERE id=? AND simulated=1",(pid,)).fetchone():
            raise ValueError("Missing simulated person")
    with db:
        for pid,name,profile in prepared:
            db.execute("UPDATE people SET name=? WHERE id=?",(name,pid))
            db.execute(
                "INSERT INTO person_personas(person_id,profile_json) VALUES(?,?) "
                "ON CONFLICT(person_id) DO UPDATE SET profile_json=excluded.profile_json,updated_at=CURRENT_TIMESTAMP",
                (pid,json.dumps(profile,ensure_ascii=False)))
    return {"imported":len(prepared),"simulated":True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file")
    args = parser.parse_args()
    db_path = os.environ.get("BOOKCENTER_PEOPLE_DB")
    if not db_path or not os.path.isabs(db_path) or not os.path.isfile(db_path):
        print("Separate initialized BOOKCENTER_PEOPLE_DB required",file=sys.stderr)
        return 2
    try:
        with open(args.json_file,encoding="utf-8") as stream:
            payload = json.load(stream)
        con = sqlite3.connect(db_path)
        try:
            print(json.dumps(import_profiles(con,payload),ensure_ascii=False))
        finally:
            con.close()
        return 0
    except (ValueError, OSError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(str(exc),file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
