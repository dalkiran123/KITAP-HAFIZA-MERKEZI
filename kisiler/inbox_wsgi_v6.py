"""Private bot inbox API. Mount only with a verified host-session resolver."""
import json
import os
import sqlite3
from urllib.parse import parse_qs

ORIGIN="https://dalkiran123.github.io"

def ensure_schema(db):
    db.execute("""CREATE TABLE IF NOT EXISTS friend_dm_reads(
      user_id TEXT NOT NULL, message_id INTEGER NOT NULL,
      read_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY(user_id,message_id))""")

def unread(db,user,limit=5):
    ensure_schema(db)
    rows=db.execute("""SELECT m.id,m.person_id,COALESCE(p.name,'Sanal arkadaş'),
      m.body,m.created_at FROM friend_direct_messages m
      JOIN people p ON p.id=m.person_id AND p.simulated=1
      LEFT JOIN friend_dm_reads r ON r.message_id=m.id AND r.user_id=m.user_id
      WHERE m.user_id=? AND m.sender='bot' AND r.message_id IS NULL
      ORDER BY m.id DESC LIMIT ?""",(user,max(1,min(int(limit),20)))).fetchall()
    return [{"id":str(r[0]),"person_id":r[1],"person_name":r[2],
             "body":r[3],"created_at":r[4],"sender_type":"bot","unread":True} for r in rows]

def mark_read(db,user,person_id):
    ensure_schema(db)
    with db:
        db.execute("""INSERT OR IGNORE INTO friend_dm_reads(user_id,message_id)
          SELECT ?,id FROM friend_direct_messages
          WHERE user_id=? AND person_id=? AND sender='bot'""",(user,user,person_id))

def make_application(resolve_user):
    def app(env,start_response):
        def respond(code,obj):
            data=json.dumps(obj,ensure_ascii=False).encode()
            origin=env.get("HTTP_ORIGIN","")
            headers=[("Content-Type","application/json; charset=utf-8"),
              ("Content-Length",str(len(data))),("Cache-Control","no-store"),
              ("Vary","Origin"),("X-Content-Type-Options","nosniff")]
            if origin==ORIGIN:
                headers.extend([("Access-Control-Allow-Origin",ORIGIN),
                                ("Access-Control-Allow-Credentials","true")])
            start_response(code,headers)
            return [data]
        if env.get("PATH_INFO")!="/api/people/inbox":
            return respond("404 Not Found",{"error":"not_found"})
        method=env.get("REQUEST_METHOD","GET")
        if method=="OPTIONS" and env.get("HTTP_ORIGIN")==ORIGIN:
            start_response("204 No Content",[("Access-Control-Allow-Origin",ORIGIN),
              ("Access-Control-Allow-Credentials","true"),
              ("Access-Control-Allow-Methods","GET,POST,OPTIONS"),
              ("Access-Control-Allow-Headers","Content-Type"),("Vary","Origin")])
            return [b""]
        if method not in ("GET","POST"):
            return respond("405 Method Not Allowed",{"error":"method_not_allowed"})
        if method=="POST" and env.get("HTTP_ORIGIN")!=ORIGIN:
            return respond("403 Forbidden",{"error":"origin_rejected"})
        user=resolve_user(env)
        if not isinstance(user,str) or not user:
            return respond("401 Unauthorized",{"error":"login_required"})
        path=os.environ.get("BOOKCENTER_PEOPLE_DB","")
        if not os.path.isabs(path) or not os.path.isfile(path):
            return respond("503 Service Unavailable",{"error":"database_not_ready"})
        try:
            with sqlite3.connect(path,timeout=5) as db:
                if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='friend_direct_messages'").fetchone():
                    return respond("200 OK",{"messages":[]}) if method=="GET" else respond("404 Not Found",{"error":"no_messages"})
                if method=="GET":
                    return respond("200 OK",{"messages":unread(db,user)})
                try:
                    length=int(env.get("CONTENT_LENGTH") or "0")
                    if not 0<length<=1024:raise ValueError()
                    payload=json.loads(env["wsgi.input"].read(length))
                    person=payload.get("person_id")
                    if type(person) is not int or not 1<=person<=10:raise ValueError()
                except (ValueError,TypeError,KeyError):
                    return respond("400 Bad Request",{"error":"invalid_request"})
                mark_read(db,user,person)
                return respond("200 OK",{"ok":True})
        except sqlite3.Error:
            return respond("503 Service Unavailable",{"error":"database_unavailable"})
    return app
