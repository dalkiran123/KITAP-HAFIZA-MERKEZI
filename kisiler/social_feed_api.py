"""Read-only WSGI endpoint for the persistent fictional social feed.
Mount at /api/people/social-feed behind the existing application's routing.
No write methods, no credentials exposed, no CORS wildcard.
"""
import json
import os
import sqlite3

try:
    from .persistent_social import feed
except ImportError:
    from persistent_social import feed


def application(environ, start_response):
    def respond(code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        start_response(code, [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(data))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
            ("Access-Control-Allow-Origin", "https://dalkiran123.github.io"),
            ("Vary", "Origin")])
        return [data]

    if environ.get("REQUEST_METHOD") != "GET":
        return respond("405 Method Not Allowed", {"error": "method_not_allowed"})
    if environ.get("PATH_INFO") not in ("/api/people/social-feed", "/social-feed"):
        return respond("404 Not Found", {"error": "not_found"})
    db_path = os.environ.get("BOOKCENTER_PEOPLE_DB", "")
    if not db_path or not os.path.isabs(db_path) or not os.path.isfile(db_path):
        return respond("503 Service Unavailable", {"error": "database_not_ready"})
    try:
        # Read-only connection: do not initialize or mutate production tables.
        db = sqlite3.connect("file:" + db_path + "?mode=ro", uri=True, timeout=3)
        try:
            # feed() initializes schema, so read directly in this read-only handler.
            rows = db.execute("""
                SELECT p.id,p.person_id,pe.name,p.caption,p.scene,p.created_at,
                  (SELECT COUNT(*) FROM friend_likes l WHERE l.post_id=p.id)
                FROM friend_posts p JOIN people pe ON pe.id=p.person_id
                ORDER BY p.created_at DESC,p.id DESC LIMIT 30
            """).fetchall()
            posts = []
            for r in rows:
                comments = db.execute("""
                    SELECT c.person_id,pe.name,c.body,c.created_at
                    FROM friend_comments c JOIN people pe ON pe.id=c.person_id
                    WHERE c.post_id=? ORDER BY c.id LIMIT 20
                """, (r[0],)).fetchall()
                posts.append({"id": r[0], "person_id": r[1], "name": r[2],
                    "caption": r[3], "scene": r[4], "created_at": r[5],
                    "likes": r[6], "comments": [
                        {"person_id": c[0], "name": c[1], "body": c[2], "created_at": c[3]}
                        for c in comments], "simulated": True})
            return respond("200 OK", {"source": "server", "simulated": True, "posts": posts})
        finally:
            db.close()
    except sqlite3.Error:
        return respond("503 Service Unavailable", {"error": "feed_not_ready"})
