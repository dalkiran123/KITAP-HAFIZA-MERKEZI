# PythonAnywhere opt-in deployment checklist

**Status:** NOT deployed. No production secret is committed. Do not enable the hourly scheduler until verified.

1. Back up the current WSGI file, the user database, and the book application directory. Verify restore.
2. Deploy the reviewed bot_server package to the same PythonAnywhere application root.
3. Set `BOOK_BOT_DB_PATH` to an **absolute** new private SQLite file path distinct from `BOOK_DB_PATH`. Set `BOOK_BOT_API_SECRET` to a freshly generated random secret of at least 32 characters **outside Git**. Ensure the existing `BOOK_DB_PATH` is defined.
4. In the existing WSGI file, **after** importing the existing `multiuser.web_app.app`, opt in by wrapping the existing app:

   ```python
   from bot_server.router import wrap_book_app
   application = wrap_book_app(app)
   ```

   Adapt this snippet to the actual current WSGI variable names. Do not replace existing imports or database environment variables.
5. Reload the web app. Confirm original /health, /login and home UI still work. An unsigned GET /api/bots/state must return HTTP 401 (not 200).
6. From a trusted test client, verify signed GET /api/bots/state returns 200 with empty bots on fresh setup, then submit one signed POST /api/bots/tick. Confirm ten records in the **separate** bot database, signed receipt GET, and duplicate protection.
7. Only after the production API is verified, configure the matching secret in GitHub Actions secrets, enable a single hourly workflow with concurrency control and idempotent recovery. The current client main() intentionally blocks remote writes. **Do not schedule it yet.**
8. Validate Arena reads, mobile display, bot names/personalities and league logic separately. Current backend only persists bot version/XP, not autonomous narrative histories.
9. If anything fails, restore the WSGI backup and reload. Keep the bot database separate for investigation.

**Limitations:** This staged API is a pilot, not a production-ready multi-user backend. No rate limiting for the bot API yet, and the request body does not contain narrative events or personality data. Existing books and automations must not be modified by this deployment.
