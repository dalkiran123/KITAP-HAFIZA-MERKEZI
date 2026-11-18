# Friends V6.4 chat integration contract

The chat UI is feature-gated: it reads `window.BOOKCENTER_CHAT_API_URL` only when configured by the deployed application. No fallback or demo success is shown.

## Server integration required
1. Mount `kisiler.chat_wsgi_v6.make_application(resolve_user)` on `/api/people/chat` within the existing authenticated PythonAnywhere WSGI app.
2. `resolve_user(environ)` must validate the existing signed server session and return a stable user id. Do not trust a user id from query parameters, request body, or an unverified cookie.
3. Configure the exact HTTPS endpoint in the served client configuration as `window.BOOKCENTER_CHAT_API_URL`. No API secret may be placed in JavaScript.
4. Verify cross-origin cookie policy (SameSite=None; Secure where required), CSRF protection, rate limiting, per-user message quotas, logging redaction and session expiration before production.
5. Run `python -m unittest discover -s kisiler -p 'test_*v6.py' -v` and the other social feed tests; verify on iPhone PWA.
6. Preserve existing book keys and server API routes. Do not enable chat in production until all checks pass.

Current engine uses persona-based templates, **not** generative AI. Photos in the social feed are local uploads or simulated scenes, not automatically generated bot photographs.
