"""SQLite online backups for the separate fictional People database.

Usage:
  BOOKCENTER_PEOPLE_DB=/absolute/path/people.sqlite3 python people_backup.py backup /private/backups
  python people_backup.py verify /private/backups/people-20261118T120000Z.sqlite3
Never restores or overwrites a database automatically.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path):
    if not os.path.isfile(path):
        raise ValueError("Backup file not found")
    uri = "file:" + os.path.abspath(path) + "?mode=ro&immutable=1"
    db = sqlite3.connect(uri, uri=True)
    try:
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError("SQLite integrity check failed: " + integrity)
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        required = {"people", "activity", "engine_ticks"}
        if not required.issubset(tables):
            raise ValueError("Missing People engine tables")
        count = db.execute("SELECT COUNT(*) FROM people WHERE simulated=1").fetchone()[0]
        if count != 10:
            raise ValueError("Expected exactly ten simulated people")
        return {"valid":True,"simulated_people":count,"sha256":sha256(path),
                "bytes":os.path.getsize(path)}
    finally:
        db.close()


def backup(source, destination_dir):
    if not source or not os.path.isabs(source) or not os.path.isfile(source):
        raise ValueError("Source database must exist at an absolute path")
    if not os.path.isdir(destination_dir):
        raise ValueError("Backup directory must already exist")
    source = os.path.realpath(source)
    destination_dir = os.path.realpath(destination_dir)
    if destination_dir == os.path.dirname(source):
        raise ValueError("Use a separate backup directory")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = os.path.join(destination_dir, "people-" + stamp + ".sqlite3")
    temp = output + ".partial"
    if os.path.exists(output) or os.path.exists(temp):
        raise ValueError("Backup path already exists")
    src = None
    dst = None
    try:
        src = sqlite3.connect("file:" + source + "?mode=ro", uri=True, timeout=10)
        dst = sqlite3.connect(temp)
        src.backup(dst)
        dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        dst.close()
        dst = None
        src.close()
        src = None
        report = verify(temp)
        os.chmod(temp, 0o600)
        os.replace(temp, output)
        report["path"] = output
        return report
    finally:
        if dst is not None:
            dst.close()
        if src is not None:
            src.close()
        if os.path.exists(temp):
            os.unlink(temp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["backup","verify"])
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        result = backup(os.environ.get("BOOKCENTER_PEOPLE_DB"), args.path) if args.command == "backup" else verify(args.path)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError,sqlite3.Error,ValueError) as exc:
        print("Backup error: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
