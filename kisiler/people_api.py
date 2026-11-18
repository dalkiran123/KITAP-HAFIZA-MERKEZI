"""Read-only WSGI API for BOOK CENTER V5.1 simulated people.
Deploy separately from the existing app. No mutations exposed.
Environment: BOOKCENTER_PEOPLE_DB=/private/path/people.sqlite3
"""
import json
import os
import sqlite3
from urllib.parse import parse_qs

DB = os.environ.get("BOOKCENTER_PEOPLE_DB", os.path.join(os.path.dirname(__file__), "people.sqlite3"))

def application(environ, start_response):
    path = environ.get("PATH_INFO", "")
    method = environ.get("REQUEST_METHOD", "GET")
    if method != "GET":
        return respond(start_response, 405, {"error": "method_not_allowed"})
    if path == "/api/people/health":
        return respond(start_response, 200, {"service": "bookcenter-people", "status": "ok"})
    if path not in ("/api/people/league", "/api/people/activity"):
        return respond(start_response, 404, {"error": "not_found"})
    if not os.path.isfile(DB):
        return respond(start_response, 503, {"error": "database_not_initialized"})
    try:
        con = sqlite3.connect("file:" + DB + "?mode=ro", uri=True, timeout=3)
        con.row_factory = sqlite3.Row
        try:
            if path.endswith("/league"):
                rows = con.execute("SELECT id,name,books,minutes,level FROM people WHERE simulated=1 ORDER BY books DESC,minutes DESC,id ASC LIMIT 10").fetchall()
                return respond(start_response, 200, {"source": "simulated", "people": [dict(x) for x in rows]})
            query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=False)
            try:
                pid = int(query.get("person_id", ["0"])[0])
            except (TypeError, ValueError):
                return respond(start_response, 400, {"error": "invalid_person_id"})
            if not 1 <= pid <= 10:
                return respond(start_response, 400, {"error": "invalid_person_id"})
            rows = con.execute("SELECT kind,description,occurred_at FROM activity WHERE person_id=? ORDER BY occurred_at DESC,id DESC LIMIT 20", (pid,)).fetchall()
            return respond(start_response, 200, {"source": "simulated", "person_id": pid, "activity": [dict(x) for x in rows]})
        finally:
            con.close()
    except sqlite3.Error:
        return respond(start_response, 503, {"error": "database_unavailable"})

def respond(start_response, status, data):
    statuses = {200: "OK", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed", 503: "Service Unavailable"}
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    start_response(f"{status} {statuses[status]}", [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Content-Length", str(len(payload))),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("Access-Control-Allow-Origin", "https://dalkiran123.github.io"),
        ("Vary", "Origin"),
    ])
    return [payload]
