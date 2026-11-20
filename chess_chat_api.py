"""Room-scoped chess chat API. Register only with the existing chess room validator.

Integration (in the PythonAnywhere Flask application):
    from chess_chat_api import create_chess_chat_blueprint
    app.register_blueprint(create_chess_chat_blueprint(
        database_path="/home/b2bsocialtest/BOOK_DATA/chess_chat.sqlite3",
        authorize=lambda room, token: existing_chess_room_authorizer(room, token),
    ))

authorize(room, token) MUST verify that the token belongs to an actual player
in that room and return 'white' or 'black', or None. Never use a user-supplied role.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request


def create_chess_chat_blueprint(database_path: str, authorize):
    if not callable(authorize):
        raise TypeError("A server-side room/token authorizer is required")
    bp = Blueprint("chess_room_chat", __name__)

    def connection():
        os.makedirs(os.path.dirname(os.path.abspath(database_path)), exist_ok=True)
        db = sqlite3.connect(database_path, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("""CREATE TABLE IF NOT EXISTS chess_room_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('white','black')),
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS chess_room_chat_idx ON chess_room_messages(room,id)")
        return db

    def identity(room):
        token = request.headers.get("X-Chess-Token", "")
        if not token:
            return None
        role = authorize(room, token)
        return role if role in ("white", "black") else None

    @bp.route("/api/chess/chat/<room>", methods=["GET", "POST"])
    def chat(room):
        if not room or len(room) > 128:
            return jsonify(error="Invalid room"), 400
        role = identity(room)
        if not role:
            return jsonify(error="Unauthorized room participant"), 403
        if request.method == "POST":
            data = request.get_json(silent=True) or {}
            message = data.get("text")
            if not isinstance(message, str) or not message.strip() or len(message.strip()) > 500:
                return jsonify(error="Message must contain 1–500 characters"), 400
            stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            with connection() as db:
                db.execute("INSERT INTO chess_room_messages(room,role,message,created_at) VALUES(?,?,?,?)",
                           (room, role, message.strip(), stamp))
            return jsonify(ok=True), 201
        with connection() as db:
            rows = db.execute("""SELECT id,role,message,created_at FROM (
                SELECT id,role,message,created_at FROM chess_room_messages
                WHERE room=? ORDER BY id DESC LIMIT 100
            ) ORDER BY id""", (room,)).fetchall()
        return jsonify(messages=[dict(id=r[0],role=r[1],text=r[2],created_at=r[3]) for r in rows])

    return bp
