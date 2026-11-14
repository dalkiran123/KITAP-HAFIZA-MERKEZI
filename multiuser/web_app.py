"""Local-only multi-user WSGI prototype. NOT production ready."""
import json
import hashlib
import hmac
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit
from http import HTTPStatus
from wsgiref.simple_server import make_server

from user_store import connect, create_user, authenticate, rate_book, leaderboard
from sessions import SessionManager
from persistent_sessions import SQLiteSessionManager
from login_limiter import LoginLimiter
from deployment_guard import validate_public_origin
from shelves import save_book, list_books
from reading_history import add_read, list_reads
from shelf_sync import read_sync, update_sync

DB_PATH = os.environ.get('BOOK_DB_PATH', 'book_users.sqlite3')
SESSIONS = SQLiteSessionManager(DB_PATH)
LOGIN_LIMITER = LoginLimiter(DB_PATH)


def csrf_for(token):
    # The random 256-bit session token is the HMAC key; the domain-separated
    # token remains stable across restarts without a process-local secret.
    return hmac.new(token.encode('utf-8'), b'book-memory-center:csrf:v1', hashlib.sha256).hexdigest()



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

    # An explicit deployment origin locks the accepted Host and expected
    # external scheme; the proxy must remove untrusted forwarded headers.
    public_origin = os.environ.get('BOOK_PUBLIC_ORIGIN', '')
    if public_origin and not validate_public_origin(env, public_origin):
        return respond(400, {'error': 'Invalid deployment host'})
    if public_origin:
        env = dict(env)
        env['wsgi.url_scheme'] = 'https'

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

    # Serve the existing full-featured book UI without modifying its local data.
    # The UI is still localStorage-based; this route alone does not enable sync.
    if method == 'GET' and path in ('/', '/index.html'):
        page = Path(__file__).resolve().parent.parent / 'index.html'
        data = page.read_bytes()
        script = b'<script defer src="/account-preview.js"></script>'
        if b'</body>' in data:
            data = data.replace(b'</body>', script + b'</body>', 1)
        else:
            data += script
        start_response('200 OK', [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Cache-Control', 'no-store'),
            ('X-Content-Type-Options', 'nosniff'),
            ('X-Frame-Options', 'DENY'),
        ])
        return [data]

    # The original homepage loads these catalog scripts dynamically.
    # Serve only the two explicitly allowed public assets.
    if method == 'GET' and path in ('/catalog.js', '/catalog-queue.js'):
        data = (Path(__file__).resolve().parent.parent / path.lstrip('/')).read_bytes()
        start_response('200 OK', [
            ('Content-Type', 'text/javascript; charset=utf-8'),
            ('Cache-Control', 'no-store'),
            ('X-Content-Type-Options', 'nosniff'),
        ])
        return [data]

    if method == 'GET' and path == '/account-preview.js':
        data = (Path(__file__).parent / 'account_preview.js').read_bytes()
        start_response('200 OK', [
            ('Content-Type', 'text/javascript; charset=utf-8'),
            ('Cache-Control', 'no-store'),
            ('X-Content-Type-Options', 'nosniff'),
        ])
        return [data]

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

    if method == 'GET' and path in ('/me', '/csrf', '/my/ratings', '/my/books', '/my/reading', '/my/sync', '/leaderboard'):
        if not account:
            return respond(401, {'error': 'Authentication required'})
        if path == '/me':
            return respond(200, account)
        if path == '/csrf':
            return respond(200, {'csrf_token': csrf_for(token)})
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

    # Every authenticated write requires a session-bound CSRF header,
    # including requests that omit Origin.
    if method == 'POST' and account:
        supplied = env.get('HTTP_X_CSRF_TOKEN', '')
        if not hmac.compare_digest(supplied, csrf_for(token)):
            return respond(403, {'error': 'CSRF token required'})

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

        # Shared, persistent failed-login limits; never trust unvalidated
        # X-Forwarded-For values from clients.
        if path == '/login':
            ip = env.get('REMOTE_ADDR', 'unknown')
            limiter = LoginLimiter(DB_PATH)
            if not limiter.allowed(ip):
                return respond(429, {'error': 'Too many login attempts'})

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
            if path == '/login':
                limiter.fail(ip)
            return respond(401, {'error': 'Invalid credentials'})
        if path == '/login':
            limiter.success(ip)
        token = SESSIONS.issue(identity['id'], identity['role'])
        return respond(200, identity,
                       f'session={token}; HttpOnly; Secure; SameSite=Strict; Path=/')
    except (ValueError, sqlite3.IntegrityError, TypeError, KeyError):
        return respond(400, {'error': 'Invalid request or duplicate username'})


if __name__ == '__main__':
    # Loopback only. Production needs HTTPS, CSRF defenses and rate limiting.
    with make_server('127.0.0.1', 8765, app) as server:
        server.serve_forever()
