"""Local-only multi-user WSGI prototype. NOT production ready."""
import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit
from http import HTTPStatus
from wsgiref.simple_server import make_server

from user_store import connect, create_user, authenticate, rate_book, leaderboard
from sessions import SessionManager
from shelves import save_book, list_books
from reading_history import add_read, list_reads
from shelf_sync import read_sync, update_sync

DB_PATH = os.environ.get('BOOK_DB_PATH', 'book_users.sqlite3')
SESSIONS = SessionManager()


def app(env, start_response):
    method, path = env.get('REQUEST_METHOD'), env.get('PATH_INFO')

    def respond(code, data, cookie=None):
        headers = [('Content-Type', 'application/json; charset=utf-8'),
                   ('Cache-Control', 'no-store'),
                   ('X-Content-Type-Options', 'nosniff')]
        if cookie is not None:
            headers.append(('Set-Cookie', cookie))
        start_response(f'{code} {HTTPStatus(code).phrase}', headers)
        return [json.dumps(data, ensure_ascii=False).encode()]

    # Defense in depth for browser-originated writes. A production reverse proxy
    # must also enforce a trusted Host and HTTPS configuration.
    if method == 'POST':
        origin = env.get('HTTP_ORIGIN')
        if origin:
            parsed = urlsplit(origin)
            host = env.get('HTTP_HOST') or env.get('SERVER_NAME', '')
            scheme = env.get('wsgi.url_scheme', 'http')
            if (parsed.scheme not in ('http', 'https') or not parsed.netloc
                    or parsed.username is not None or parsed.password is not None
                    or parsed.path not in ('', '/') or parsed.query or parsed.fragment
                    or parsed.netloc.lower() != host.lower()
                    or parsed.scheme != scheme):
                return respond(403, {'error': 'Cross-origin write blocked'})

    if method == 'GET' and path in ('/mobile', '/mobile/', '/mobile/mobile_client.js'):
        name = 'mobile_client.js' if path.endswith('.js') else 'index.html'
        data = (Path(__file__).parent / 'mobile' / name).read_bytes()
        content_type = 'text/javascript; charset=utf-8' if name.endswith('.js') else 'text/html; charset=utf-8'
        start_response('200 OK', [('Content-Type', content_type),
                                  ('Cache-Control', 'no-store'),
                                  ('X-Content-Type-Options', 'nosniff')])
        return [data]

    if method == 'GET' and path == '/health':
        return respond(200, {'status': 'prototype'})

    raw_cookie = env.get('HTTP_COOKIE', '')
    token = next((item.strip().split('=', 1)[1]
                  for item in raw_cookie.split(';')
                  if item.strip().startswith('session=')), None)
    account = SESSIONS.lookup(token)

    if method == 'GET' and path in ('/me', '/my/ratings', '/my/books', '/my/reading', '/my/sync', '/leaderboard'):
        if not account:
            return respond(401, {'error': 'Authentication required'})
        if path == '/me':
            return respond(200, account)
        db = connect(DB_PATH)
        try:
            uid = account['user_id']
            if path == '/my/sync':
                return respond(200, {'books': read_sync(db, uid)})
            if path == '/my/books':
                return respond(200, {'books': list_books(db, uid)})
            if path == '/my/reading':
                return respond(200, {'reading': list_reads(db, uid)})
            if path == '/my/ratings':
                rows = db.execute('SELECT book_id,score FROM ratings WHERE user_id=? ORDER BY book_id',
                                  (uid,)).fetchall()
                return respond(200, {'ratings': [{'book_id': bid, 'score': score}
                                                 for bid, score in rows]})
            return respond(200, {'leaderboard': [{'username': name, 'books': count}
                                                for name, count in leaderboard(db)]})
        finally:
            db.close()

    if method == 'POST' and path == '/logout':
        if not account:
            return respond(401, {'error': 'Authentication required'})
        SESSIONS.revoke(token)
        return respond(200, {'ok': True},
                       'session=; Max-Age=0; HttpOnly; Secure; SameSite=Strict; Path=/')

    if method != 'POST' or path not in ('/register', '/login', '/my/ratings',
                                       '/my/books', '/my/reading', '/my/sync'):
        return respond(404, {'error': 'Not found'})

    try:
        size = int(env.get('CONTENT_LENGTH') or '0')
        if not 1 <= size <= 8192:
            return respond(413, {'error': 'Invalid body size'})
        payload = json.loads(env['wsgi.input'].read(size))
        if not isinstance(payload, dict):
            return respond(400, {'error': 'Invalid JSON object'})

        if path in ('/my/ratings', '/my/books', '/my/reading', '/my/sync'):
            if not account:
                return respond(401, {'error': 'Authentication required'})
            db = connect(DB_PATH)
            try:
                uid = account['user_id']
                if path == '/my/sync':
                    revision = update_sync(db, uid, payload.get('book_id'), payload.get('state'), payload.get('expected_revision'))
                    return respond(200, {'revision': revision})
                if path == '/my/books':
                    save_book(db, uid, payload.get('book_id'), payload.get('state'))
                elif path == '/my/reading':
                    add_read(db, uid, payload.get('book_id'), payload.get('completed_at'))
                else:
                    bid, score = payload.get('book_id'), payload.get('score')
                    if not isinstance(bid, str) or not 1 <= len(bid) <= 256:
                        raise ValueError('Invalid book id')
                    rate_book(db, uid, bid, score)
            except ValueError as error:
                if str(error) == 'Revision conflict':
                    return respond(409, {'error': 'Revision conflict', 'action': 'refresh'})
                return respond(400, {'error': 'Invalid record'})
            except (TypeError, sqlite3.IntegrityError):
                return respond(400, {'error': 'Invalid record'})
            finally:
                db.close()
            return respond(200, {'ok': True})

        username, password = payload.get('username'), payload.get('password')
        if not isinstance(username, str) or not isinstance(password, str):
            return respond(400, {'error': 'Invalid input'})
        db = connect(DB_PATH)
        try:
            if path == '/register':
                uid = create_user(db, username, password)
                identity = {'id': uid, 'role': 'reader'}
            else:
                identity = authenticate(db, username, password)
        finally:
            db.close()
        if identity is None:
            return respond(401, {'error': 'Invalid credentials'})
        token = SESSIONS.issue(identity['id'], identity['role'])
        return respond(200, identity,
                       f'session={token}; HttpOnly; Secure; SameSite=Strict; Path=/')
    except (ValueError, sqlite3.IntegrityError, TypeError, KeyError):
        return respond(400, {'error': 'Invalid request or duplicate username'})


if __name__ == '__main__':
    # Loopback only. Production needs HTTPS, CSRF defenses and rate limiting.
    with make_server('127.0.0.1', 8765, app) as server:
        server.serve_forever()
