"""Opt-in GitHub Actions bot tick client. No writes without explicit configuration."""
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from bot_server.simulator import advance

def make_payload(state, now=None):
    now = now or datetime.now(timezone.utc)
    updated = advance(state, now)
    tick_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "book-center:bot-tick:" + updated["last_tick"]))
    payload = {"tick_id": tick_id, "bots": {
        bot_id: {"xp": bot["xp"], "version": bot["activity_count"]}
        for bot_id, bot in updated["bots"].items()}}
    return updated, json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()

def signed_headers(body, secret, timestamp=None):
    stamp = str(int(time.time() if timestamp is None else timestamp))
    signature = hmac.new(secret.encode(), stamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return {"Content-Type": "application/json", "X-Bot-Timestamp": stamp,
            "X-Bot-Signature": signature}

def post_tick(url, body, secret, *, opener=None):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path != "/api/bots/tick":
        raise ValueError("Expected HTTPS bot endpoint without query or credentials")
    if not secret or len(secret) < 32:
        raise ValueError("Missing API secret")
    req = urllib.request.Request(url, data=body, headers=signed_headers(body, secret), method="POST")
    response = (opener or urllib.request.urlopen)(req, timeout=20)
    with response as res:
        if res.status not in (200, 201):
            raise RuntimeError("Unexpected server status")
        return json.load(res)


def get_state(url, secret, *, opener=None, timestamp=None):
    parts = urlsplit(url)
    if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password
            or parts.query or parts.fragment or parts.path != "/api/bots/state"):
        raise ValueError("Expected HTTPS bot state endpoint")
    if not isinstance(secret, str) or len(secret) < 32:
        raise ValueError("Missing API secret")
    stamp = str(int(time.time() if timestamp is None else timestamp))
    signature = hmac.new(secret.encode(), stamp.encode() + b".GET./api/bots/state", hashlib.sha256).hexdigest()
    req = urllib.request.Request(url, headers={"X-Bot-Timestamp": stamp,
                                                "X-Bot-Signature": signature}, method="GET")
    with (opener or urllib.request.urlopen)(req, timeout=20) as res:
        if res.status != 200:
            raise RuntimeError("Unexpected state status")
        data = json.load(res)
    bots = data.get("bots")
    if not isinstance(bots, dict) or (bots and set(bots) != {f"bot-{i:02d}" for i in range(1, 11)}):
        raise ValueError("Incomplete bot state")
    for item in bots.values():
        if (not isinstance(item, dict) or type(item.get("version")) is not int
                or type(item.get("xp")) is not int or item["version"] < 1 or item["xp"] < 0):
            raise ValueError("Invalid bot state")
    return bots

def next_tick_from_remote(bots, *, tick_id):
    """Prepare exactly one sequential tick from authoritative versions."""
    if not isinstance(tick_id, str) or str(uuid.UUID(tick_id)) != tick_id:
        raise ValueError("Invalid tick id")
    expected = {f"bot-{i:02d}" for i in range(1, 11)}
    if bots and set(bots) != expected:
        raise ValueError("Partial remote state")
    updated = {}
    for bot_id in sorted(expected):
        current = bots.get(bot_id, {"version": 0, "xp": 0})
        updated[bot_id] = {"version": current["version"] + 1, "xp": current["xp"] + 1}
    return json.dumps({"tick_id": tick_id, "bots": updated},
                      separators=(",", ":"), sort_keys=True).encode()


def deterministic_tick_id(slot):
    """One UUID per UTC hour, stable across workflow retries."""
    if not isinstance(slot, datetime) or slot.tzinfo is None:
        raise ValueError("Timezone-aware datetime required")
    utc = slot.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "book-center:hourly:" + utc.isoformat()))

def plan_hourly_tick(bots, slot):
    """Build a retry-stable tick for one UTC hour from committed state."""
    return next_tick_from_remote(bots, tick_id=deterministic_tick_id(slot))


def get_tick_receipt(url, secret, tick_id, *, opener=None):
    parts = urlsplit(url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment or parts.path != "/api/bots/state":
        raise ValueError("Invalid bot API URL")
    path = "/api/bots/ticks/" + tick_id
    stamp = str(int(time.time()))
    signature = hmac.new(secret.encode(), stamp.encode() + b".GET." + path.encode(), hashlib.sha256).hexdigest()
    req = urllib.request.Request("https://" + parts.netloc + path,
                                 headers={"X-Bot-Timestamp": stamp, "X-Bot-Signature": signature}, method="GET")
    with (opener or urllib.request.urlopen)(req, timeout=20) as res:
        if res.status != 200:
            raise RuntimeError("Receipt lookup failed")
        data = json.load(res)
    if type(data.get("committed")) is not bool:
        raise ValueError("Invalid receipt")
    return data

def run_one_hour(state_url, secret, slot, *, reader=get_state, sender=post_tick, receipt_reader=get_tick_receipt):
    """At most one committed tick per UTC slot. No blind retry after timeout."""
    tick_id = deterministic_tick_id(slot)
    receipt = receipt_reader(state_url, secret, tick_id)
    if receipt["committed"]:
        return {"ok": True, "already_committed": True}
    bots = reader(state_url, secret)
    body = plan_hourly_tick(bots, slot)
    target = state_url.removesuffix("/api/bots/state") + "/api/bots/tick"
    try:
        return sender(target, body, secret)
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        # Query receipt once, never blindly recompute and resend.
        receipt = receipt_reader(state_url, secret, tick_id)
        if receipt["committed"] and receipt.get("payload_sha256") == hashlib.sha256(body).hexdigest():
            return {"ok": True, "recovered": True}
        raise

def main():
    # Deliberately fail closed: no scheduling and no production write by default.
    if os.environ.get("BOOK_BOT_ENABLE_REMOTE_WRITE") != "true":
        print("Remote writes disabled. No request sent.")
        return
    url = os.environ.get("BOOK_BOT_API_URL", "")
    secret = os.environ.get("BOOK_BOT_API_SECRET", "")
    if not url or not secret or len(secret) < 32:
        raise SystemExit("Missing bot API configuration")
    slot = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    result = run_one_hour(url, secret, slot)
    print(json.dumps({"slot": slot.isoformat(), "result": result}, sort_keys=True))

if __name__ == "__main__":
    main()
