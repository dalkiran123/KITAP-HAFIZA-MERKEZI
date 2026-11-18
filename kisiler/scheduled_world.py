"""Production-safe entrypoint for the optional simulated world.

Use a separate SQLite file, a single scheduled process, and an OS lock.
This file does not configure or start PythonAnywhere jobs by itself.
"""
import json
import os
import sys
import time
import traceback

from world_runner import run
import people_engine


def main():
    db_path = os.environ.get("BOOKCENTER_PEOPLE_DB")
    if not db_path or not os.path.isabs(db_path):
        print("BOOKCENTER_PEOPLE_DB must be an absolute path", file=sys.stderr)
        return 2
    if not os.path.isfile(db_path):
        print("People database not initialized; run people_engine.py init first", file=sys.stderr)
        return 2
    lock_path = db_path + ".runner.lock"
    lock_fd = None
    try:
        # O_EXCL guarantees only one active runner can acquire this lock.
        # If an earlier process crashed, the operator must inspect and
        # remove a stale lock. We never remove another process's lock.
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(lock_fd, str(os.getpid()).encode("ascii"))
    except FileExistsError:
        print("World runner already active or stale lock present", file=sys.stderr)
        return 3
    try:
        db = people_engine.connect()
        try:
            result = run(db)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        finally:
            db.close()
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
            os.unlink(lock_path)


if __name__ == "__main__":
    sys.exit(main())
