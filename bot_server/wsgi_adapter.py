"""Opt-in WSGI adapter for isolated bot API. Not deployed automatically."""
import json
import os
from http import HTTPStatus
from pathlib import Path
from bot_server.api import handle_tick, handle_state, MAX_BODY

def bot_wsgi_app(environ, start_response):
    """Dedicated WSGI app, deliberately separate from book web_app.app."""
    method = environ.get("REQUEST_METHOD", "")
    path = environ.get("PATH_INFO", "")
    if method == "GET" and path == "/api/bots/state":
        headers = {"x-bot-timestamp": environ.get("HTTP_X_BOT_TIMESTAMP", ""),
                   "x-bot-signature": environ.get("HTTP_X_BOT_SIGNATURE", "")}
        secret = os.environ.get("BOOK_BOT_API_SECRET", "")
        database = os.environ.get("BOOK_BOT_DB_PATH", "")
        book_db = os.environ.get("BOOK_DB_PATH", "")
        if not database or (book_db and Path(database).resolve() == Path(book_db).resolve()):
            code, result = 503, {"error": "Isolated bot database not configured"}
        else:
            code, result = handle_state(method, path, headers, secret=secret, database=database)
    elif method != "POST" or path != "/api/bots/tick":
        code, result = 404, {"error": "Not found"}
    else:
        try:
            size = int(environ.get("CONTENT_LENGTH", ""))
        except (TypeError, ValueError):
            size = -1
        if size < 1 or size > MAX_BODY:
            code, result = 413, {"error": "Invalid body size"}
        else:
            body = environ["wsgi.input"].read(size)
            if len(body) != size:
                code, result = 400, {"error": "Incomplete body"}
            else:
                headers = {
                    "x-bot-timestamp": environ.get("HTTP_X_BOT_TIMESTAMP", ""),
                    "x-bot-signature": environ.get("HTTP_X_BOT_SIGNATURE", ""),
                }
                # Fail closed if secrets/DB path are not configured.
                secret = os.environ.get("BOOK_BOT_API_SECRET", "")
                database = os.environ.get("BOOK_BOT_DB_PATH", "")
                book_db = os.environ.get("BOOK_DB_PATH", "")
                if not database or (book_db and Path(database).resolve() == Path(book_db).resolve()):
                    code, result = 503, {"error": "Isolated bot database not configured"}
                else:
                    code, result = handle_tick(method, path, headers, body, secret=secret, database=database)
    data = json.dumps(result, ensure_ascii=False).encode("utf-8")
    start_response(f"{code} {HTTPStatus(code).phrase}", [
        ("Content-Type", "application/json; charset=utf-8"),
        ("Cache-Control", "no-store"),
        ("X-Content-Type-Options", "nosniff"),
        ("Content-Length", str(len(data))),
    ])
    return [data]
