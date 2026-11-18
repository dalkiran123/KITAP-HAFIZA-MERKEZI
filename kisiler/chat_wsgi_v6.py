"""Authenticated WSGI chat API adapter for Friends V6.
Deployment requires a trusted session resolver supplied by the host application.
No fallback anonymous identity, no token in browser, no CORS wildcard.
"""
import json
import os
import sqlite3
from urllib.parse import parse_qs
try:
    from .persona_chat_v6 import send_message, history
except ImportError:
    from persona_chat_v6 import send_message, history

MAX_BODY=4096

def make_application(resolve_user):
    """resolve_user(environ) -> stable authenticated user id or None.
    Resolver MUST validate an existing server-side session.
    """
    def application(environ,start_response):
        def respond(code,payload):
            data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
            origin=environ.get("HTTP_ORIGIN","")
            headers=[("Content-Type","application/json; charset=utf-8"),
                     ("Content-Length",str(len(data))),("Cache-Control","no-store"),
                     ("X-Content-Type-Options","nosniff"),("Vary","Origin")]
            if origin=="https://dalkiran123.github.io":
                headers.extend([("Access-Control-Allow-Origin",origin),
                                ("Access-Control-Allow-Credentials","true")])
            start_response(code,headers)
            return [data]
        path=environ.get("PATH_INFO","")
        if path!="/api/people/chat":
            return respond("404 Not Found",{"error":"not_found"})
        method=environ.get("REQUEST_METHOD","GET")
        if method not in ("GET","POST"):
            return respond("405 Method Not Allowed",{"error":"method_not_allowed"})
        # Cross-site POSTs must originate from the exact configured PWA origin.
        if method=="POST" and environ.get("HTTP_ORIGIN")!="https://dalkiran123.github.io":
            return respond("403 Forbidden",{"error":"origin_rejected"})
        user=resolve_user(environ)
        if not user or not isinstance(user,str):
            return respond("401 Unauthorized",{"error":"login_required"})
        try:
            if method=="GET":
                args=parse_qs(environ.get("QUERY_STRING",""))
                person=int(args.get("person_id",["0"])[0])
                body=None
            else:
                size=int(environ.get("CONTENT_LENGTH") or "0")
                if not 0<size<=MAX_BODY:
                    return respond("413 Content Too Large",{"error":"invalid_size"})
                body=json.loads(environ["wsgi.input"].read(size))
                person=body.get("person_id")
                if type(person) is not int:
                    raise ValueError("invalid person")
            if type(person) is not int or not 1<=person<=10:
                raise ValueError("invalid person")
        except (ValueError,TypeError,KeyError,json.JSONDecodeError):
            return respond("400 Bad Request",{"error":"invalid_request"})
        path_db=os.environ.get("BOOKCENTER_PEOPLE_DB","")
        if not os.path.isabs(path_db) or not os.path.isfile(path_db):
            return respond("503 Service Unavailable",{"error":"database_not_ready"})
        try:
            db=sqlite3.connect(path_db,timeout=5)
            try:
                if method=="GET":
                    # History is private to the authenticated user.
                    return respond("200 OK",{"person_id":person,"messages":history(db,user,person)})
                message=body.get("message")
                try:
                    result=send_message(db,user,person,message)
                except ValueError:
                    return respond("400 Bad Request",{"error":"invalid_message"})
                return respond("200 OK",result)
            finally:
                db.close()
        except sqlite3.Error:
            return respond("503 Service Unavailable",{"error":"database_unavailable"})
    return application
