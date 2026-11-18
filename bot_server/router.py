"""Optional dispatch wrapper; preserve the existing BOOK CENTER WSGI app."""
from bot_server.wsgi_adapter import bot_wsgi_app

BOT_PATHS = frozenset(("/api/bots/tick", "/api/bots/state"))

def wrap_book_app(book_app):
    """Only opt-in bot routes are intercepted; all other paths pass unchanged."""
    def application(environ, start_response):
        path = environ.get("PATH_INFO", "")
        if path in BOT_PATHS or path.startswith("/api/bots/ticks/"):
            return bot_wsgi_app(environ, start_response)
        return book_app(environ, start_response)
    return application
