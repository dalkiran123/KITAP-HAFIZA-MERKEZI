"""Run persistent simulated social activity once per hourly slot.
Example: BOOKCENTER_PEOPLE_DB=/private/people.sqlite3 python -m kisiler.social_job
Schedule separately on server; do not run from browser.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path
try:
    from .persistent_social import tick
except ImportError:
    from persistent_social import tick


def main():
    path = os.environ.get("BOOKCENTER_PEOPLE_DB", "")
    if not path or not os.path.isabs(path) or not Path(path).is_file():
        print("BOOKCENTER_PEOPLE_DB must point to an initialized absolute SQLite file", file=sys.stderr)
        return 2
    db = sqlite3.connect(path, timeout=20)
    try:
        db.execute("PRAGMA busy_timeout=20000")
        print(json.dumps(tick(db), ensure_ascii=False))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
