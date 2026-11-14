"""Local-only WSGI prototype. NOT production ready or deployed."""
import json
import os
import secrets
import sqlite3
from http import HTTPStatus
from wsgiref.simple_server import make_server
from user_store import connect,create_user,authenticate,rate_book,leaderboard
from sessions import SessionManager

DB_PATH=os.environ.get('BOOK_DB_PATH','book_users.sqlite3')
SESSIONS=SessionManager()  # Process-local prototype; not production-ready.

def app(env,start_response):
    method,path=env.get('REQUEST_METHOD'),env.get('PATH_INFO')
    def respond(code,data,cookie=None):
        headers=[('Content-Type','application/json; charset=utf-8'),('Cache-Control','no-store'),('X-Content-Type-Options','nosniff')]
        if cookie: headers.append(('Set-Cookie',cookie))
        start_response(f'{code} {HTTPStatus(code).phrase}',headers)
        return [json.dumps(data,ensure_ascii=False).encode()]
    if method=='GET' and path=='/health': return respond(200,{'status':'prototype'})
    cookie=env.get('HTTP_COOKIE','')
    token=next((v.strip().split('=',1)[1] for v in cookie.split(';') if v.strip().startswith('session=')),None)
    account=SESSIONS.lookup(token)
    if method=='GET' and path in ('/me','/my/ratings','/leaderboard'):
        if not account: return respond(401,{'error':'Authentication required'})
        if path=='/me': return respond(200,account)
        db=connect(DB_PATH)
        try:
            if path=='/my/ratings':
                rows=db.execute('SELECT book_id,score FROM ratings WHERE user_id=? ORDER BY book_id',(account['user_id'],)).fetchall()
                return respond(200,{'ratings':[{'book_id':b,'score':score} for b,score in rows]})
            return respond(200,{'leaderboard':[{'username':name,'books':count} for name,count in leaderboard(db)]})
        finally: db.close()
    if method=='POST' and path=='/logout':
        if not account: return respond(401,{'error':'Authentication required'})
        SESSIONS.revoke(token)
        return respond(200,{'ok':True},'session=; Max-Age=0; HttpOnly; Secure; SameSite=Strict; Path=/')
    if method!='POST' or path not in ('/register','/login','/my/ratings'): return respond(404,{'error':'Not found'})
    try:
        size=int(env.get('CONTENT_LENGTH') or '0')
        if size<1 or size>8192: return respond(413,{'error':'Invalid body size'})
        payload=json.loads(env['wsgi.input'].read(size))
        if not isinstance(payload,dict): return respond(400,{'error':'Invalid JSON object'})
        if path=='/my/ratings':
            if not account: return respond(401,{'error':'Authentication required'})
            book_id,score=payload.get('book_id'),payload.get('score')
            if not isinstance(book_id,str) or not 1<=len(book_id)<=256 or type(score) is not int or not 1<=score<=10:
                return respond(400,{'error':'Invalid rating'})
            db=connect(DB_PATH)
            try: rate_book(db,account['user_id'],book_id,score)
            finally: db.close()
            return respond(200,{'ok':True})
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
        token=SESSIONS.issue(account['id'],account['role'])
        return respond(200,account,f'session={token}; HttpOnly; Secure; SameSite=Strict; Path=/')
    except (ValueError,sqlite3.IntegrityError,TypeError,KeyError):
        return respond(400,{'error':'Invalid request or duplicate username'})

if __name__=='__main__':
    # Loopback only. No TLS, rate limits, CSRF handling, or session expiry yet.
    with make_server('127.0.0.1',8765,app) as server: server.serve_forever()
