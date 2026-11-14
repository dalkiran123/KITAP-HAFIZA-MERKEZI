"""Session helpers for the local multiuser prototype.
Production requires TLS, CSRF mitigation, rate limits and secure deployment.
"""
import hashlib
import secrets
import time

SESSION_TTL_SECONDS = 12 * 3600

class SessionManager:
    def __init__(self):
        self._sessions = {}

    def issue(self, user_id, role='reader'):
        token = secrets.token_urlsafe(32)
        self._sessions[hashlib.sha256(token.encode()).hexdigest()] = {
            'user_id': user_id, 'role': role, 'expires': time.time() + SESSION_TTL_SECONDS
        }
        return token

    def lookup(self, token):
        if not isinstance(token, str) or len(token) > 256:
            return None
        key = hashlib.sha256(token.encode()).hexdigest()
        entry = self._sessions.get(key)
        if entry is None:
            return None
        if entry['expires'] <= time.time():
            self._sessions.pop(key, None)
            return None
        return {'user_id': entry['user_id'], 'role': entry['role']}

    def revoke(self, token):
        if not isinstance(token, str):
            return
        self._sessions.pop(hashlib.sha256(token.encode()).hexdigest(), None)
