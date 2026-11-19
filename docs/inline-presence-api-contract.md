# BOOK CENTER: inline presence backend contract

Status: frontend integration branch only. **Not a deployed API.**

The static GitHub Pages frontend cannot serve `/api/presence/visible`. Configure
`window.BOOKCENTER_PRESENCE_API_URL` to an HTTPS backend endpoint **only after**
the backend implements this contract. Never embed API secrets in the PWA.

## GET /api/presence/visible

Require an authenticated session and allow credentialed CORS exclusively for
`https://dalkiran123.github.io`. Set `Access-Control-Allow-Credentials: true`
and `Vary: Origin`. Return `Cache-Control: private, no-store`.

Example response shape (illustrative only, not live data):

```json
{
  "friends": [
    {
      "id": "visible-friend-id",
      "name": "Display name",
      "kind": "user",
      "online": true,
      "location": {"type": "book", "id": "Book title"},
      "last_seen_at": "2026-11-19T12:00:00Z",
      "avatar_url": "/safe/avatar.png",
      "profile_url": "/safe/profile"
    }
  ]
}
```

Filter all records server-side by authenticated viewer and mutual friendship/
presence-sharing permissions. Do not expose private book history, private
messages, email, phone, exact location or raw authentication identifiers.
Only mark a human online when a recent heartbeat confirms it. Validate
`location.type` and `location.id` against allowed public UI sections.
Limit response size and rate; use stable, non-secret opaque IDs.

Bots must be marked `kind: "bot"` and not represented as real human users.
The current local Arena simulation remains separate. It only reads previously
persisted `reading[].title` / `reading[].at`, never claims live online
activity, and does not synchronize across devices.

## Deployment acceptance checks

1. Authenticated owner sees only opted-in friend presence.
2. Anonymous request is rejected; cross-origin credentials are scoped to
   the GitHub Pages origin; no wildcard credentialed CORS.
3. Revoked friendships stop appearing immediately.
4. Invalid/expired activity is not displayed as online.
5. Main-screen menu, book cards, videos, navigation, summaries and Arena
   retain their prior functionality on iPhone.
6. GitHub Actions regression checks pass before merging PR #56.

The PythonAnywhere bot-state endpoint `/api/bots/state` is **not** assumed
to satisfy this contract. Do not use its write secret in browser code.
