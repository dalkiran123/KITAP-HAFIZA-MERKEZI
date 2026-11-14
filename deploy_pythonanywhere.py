#!/usr/bin/env python3
"""One-command guarded PythonAnywhere deployment of the book multiuser pilot.

Run on PythonAnywhere Bash from repository root:
    python3 deploy_pythonanywhere.py

The script does not reload the site. The operator must reload in Web tab.
It refuses deployment unless isolated tests pass and expected paths exist.
"""
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOME = Path("/home/b2bsocialtest")
REPO = HOME / "KITAP-HAFIZA-MERKEZI"
DB = HOME / "BOOK_DATA" / "book_users.sqlite3"
WSGI = Path("/var/www/b2bsocialtest_pythonanywhere_com_wsgi.py")
HOST = "https://b2bsocialtest.pythonanywhere.com"

def main():
    if Path.cwd().resolve() != REPO.resolve():
        sys.exit("ERROR: Run from " + str(REPO))
    if not (REPO / "index.html").is_file() or not (REPO / "multiuser/web_app.py").is_file():
        sys.exit("ERROR: book UI/server missing")
    if not (REPO / "multiuser/account_preview.js").is_file():
        sys.exit("ERROR: account preview missing. Pull integration branch first")
    if not DB.is_file() or not WSGI.is_file():
        sys.exit("ERROR: database or current WSGI missing; no changes made")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "multiuser") + os.pathsep + str(REPO)
    env.pop("BOOK_PUBLIC_ORIGIN", None)
    env.pop("BOOK_DB_PATH", None)
    print("Running isolated tests against a temporary database...")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests",
         "-p", "test_multiuser_http_contract.py", "-v"],
        cwd=REPO, env=env, check=False,
    )
    if result.returncode:
        sys.exit("ERROR: tests failed. WSGI unchanged.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = HOME / "BOOK_DATA" / "deployment_backups"
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup_wsgi = backup_dir / ("b2b_wsgi_" + stamp + ".py")
    backup_db = backup_dir / ("book_users_" + stamp + ".sqlite3")
    shutil.copy2(WSGI, backup_wsgi)
    # SQLite online backup: safe if other processes are reading/writing.
    import sqlite3
    with sqlite3.connect(str(DB)) as src, sqlite3.connect(str(backup_db)) as dst:
        src.backup(dst)
    backup_db.chmod(0o600)
    # This WSGI entry point does not import or run B2B.
    config = (
        "import os\\nimport sys\\n"
        "PROJECT_DIR = " + repr(str(REPO)) + "\\n"
        "MULTIUSER_DIR = " + repr(str(REPO / "multiuser")) + "\\n"
        "for p in (MULTIUSER_DIR, PROJECT_DIR):\\n"
        "    if p not in sys.path: sys.path.insert(0, p)\\n"
        "os.environ['BOOK_DB_PATH'] = " + repr(str(DB)) + "\\n"
        "os.environ['BOOK_PUBLIC_ORIGIN'] = " + repr(HOST) + "\\n"
        "from multiuser.web_app import app as application\\n"
    )
    # Generate real newline-delimited Python code.
    config = config.replace("\\\\n", "\\n")
    compile(config, str(WSGI), "exec")
    temp_wsgi = WSGI.with_name(WSGI.name + ".booktmp")
    temp_wsgi.write_text(config, encoding="utf-8")
    os.replace(temp_wsgi, WSGI)
    print("WSGI prepared. B2B backup:", backup_wsgi)
    print("Book DB backup:", backup_db)
    print("NEXT: PythonAnywhere Web > Reload, then visit", HOST)
    print("Rollback: copy backup WSGI over", WSGI, "and Reload")

if __name__ == "__main__":
    main()
