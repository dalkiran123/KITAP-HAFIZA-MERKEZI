# V7.3 bot inbox: release gate

Implemented:
- Public main page includes `bot-inbox.js`, hidden unless `window.BOOKCENTER_BOT_INBOX_API_URL` is configured.
- Server endpoint `kisiler/inbox_wsgi_v6.py`: authenticated GET unread messages, POST acknowledge a bot thread.
- Chat panel calls acknowledge after successful authenticated history load.
- Unit tests in `kisiler/test_inbox_wsgi_v6.py`.

NOT YET DEPLOYED:
- Existing PythonAnywhere WSGI must mount the inbox endpoint with its verified session resolver.
- Existing PWA must provide endpoint configuration, cross-site cookies and authenticated identity.
- Server-side bot-initiated messages need a separate scheduled producer; existing rule-based replies only respond after the user sends a message.
- Chat UI and read receipts are still on feature branch; do not claim the inbox is working live.
- Review rate limits, CSRF/session policy, data retention, and test on iPhone before enabling.

Deployment order:
1. Test migrations against a copy of the existing SQLite DB and run all tests.
2. Mount authenticated inbox/chat endpoints without altering existing book APIs.
3. Configure endpoint URLs on client and verify CORS/cookies.
4. Deploy chat UI, verify actual unread/read flow with two isolated test users.
5. Only then enable scheduled bot-initiated messages with opt-in, frequency limits, and quiet hours.
