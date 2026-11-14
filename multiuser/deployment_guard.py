"""Optional strict deployment boundary for reverse-proxied HTTPS hosting.

Set BOOK_PUBLIC_ORIGIN to the exact external HTTPS origin, e.g.
https://books.example.com. Never trust client-supplied X-Forwarded-* headers.
The reverse proxy must forward the canonical Host and terminate TLS.
"""
from urllib.parse import urlsplit


def validate_public_origin(environ, configured_origin):
    if not configured_origin:
        return True
    try:
        expected = urlsplit(configured_origin)
        if (expected.scheme != 'https' or not expected.hostname
                or expected.username or expected.password
                or expected.path not in ('', '/') or expected.query or expected.fragment):
            return False
        host = environ.get('HTTP_HOST', '')
        if not host or ',' in host or '@' in host:
            return False
        # Host is checked against a single operator-controlled public origin.
        return host.lower() == expected.netloc.lower()
    except ValueError:
        return False
