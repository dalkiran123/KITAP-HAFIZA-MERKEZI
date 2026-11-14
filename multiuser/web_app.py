"""Local-only WSGI prototype. NOT production ready or deployed."""
import json
import os
import secrets
import sqlite3
from http import HTTPStatus
from wsgiref.simple_server import make_server
from user_store import connect,create_user,authenticate

DB_PATH=os.environ.get('BOOK_DB_PATH','book_users.sqlite3')
SESSIONS={}  # Temporary process memory; needs expiry and durable production storage.

def app(env,start_response):
    method,path=env.get('REQUEST_METHOD'),env.get('PATH_INFO')
    def respond(code,data,cookie=None):
        headers=[('Content-Type','application/json; charset=utf-8'),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff')]
        if cookie: headers.append(('Set-Cookie',cookie))
        start_response(f'{code} {HTTPStatus(code).phrase}',headers)
        return [json.dumps(data,ensure_ascii=False).encode()]
    if method=='GET' and path=='/health': return respond(200,{'status':'prototype'})
    if method!='POST' or path not in ('/register','/login'): return respond(404,{'error':'Not found'})
    try:
        size=int(env.get('CONTENT_LENGTH') or '0')
        if size<1 or size>8192: return respond(413,{'error':'Invalid body size'})
        payload=json.loads(env['wsgi.input'].read(size))
        username,password=payload.get('username'),payload.get('password')
        if not isinstance(username,str) or not isinstance(password,str): return respond(400,{'error':'Invalid input'})
        db=connect(DB_PATH)
        try:
            if path=='/register':
                user_id=create_user(db,username,password)
                account={'id':user_id,'role':'reader'}
            else: account=authenticate(db,username,password)
        finally: db.close()
        if account is None: return respond(401,{'error':'Invalid credentials'})
        token=secrets.token_urlsafe(32)
        SESSIONS[token]=account
        return respond(200,account,f'session={token}; HttpOnly; Secure; SameSite=Strict; Path=/')
    except (ValueError,sqlite3.IntegrityError,TypeError,KeyError):
        return respond(400,{'error':'Invalid request or duplicate username'})

if __name__=='__main__':
    # Loopback only. No TLS, rate limits, CSRF handling, or session expiry yet.
    with make_server('127.0.0.1',8765,app) as server: server.serve_forever()
