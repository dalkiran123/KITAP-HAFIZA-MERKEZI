# BOOK CENTER Bot simulation, isolated pilot

This branch contains an offline simulation proof of concept for ten bots. It does **not** write to the existing book database, make network calls, or deploy to PythonAnywhere.

## Local verification
```bash
python -m unittest discover -s bot_server -p 'test_*.py' -v
python -m bot_server.simulator --state /tmp/book-bot-test.json
```

## Production integration gates (not implemented yet)
1. Inspect the deployed `multiuser/web_app.py` and existing authentication model. It is not present on GitHub main.
2. Back up and verify the existing database before any backend change.
3. Use a **separate** SQLite bot database on PythonAnywhere, outside the public web root.
4. Implement an authenticated, rate-limited HTTPS API with short-lived signed requests, replay protection, bounded request sizes, and least-privilege access.
5. Configure the API signing secret in GitHub Actions secrets and PythonAnywhere environment, never in repository files or screenshots.
6. Test 401 unauthorized, replay rejection, duplicate tick idempotency, malformed payload, and concurrent updates.
7. Only then add an hourly schedule and enable remote writes. Scheduled workflows may be delayed or skipped.
8. Keep the main branch and existing hourly book workflows unchanged until review.

This pilot models activities, not continuous sentient processes or real-world experiences.
