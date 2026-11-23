"""Deterministic, offline bot-world simulation. No user database access."""
import json
from datetime import datetime, timezone, timedelta

BOT_COUNT = 10
EVENTS = ("read", "quiz", "rest", "chat", "practice")

def advance(state, now=None, interval_minutes=60, max_steps=24):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    state = json.loads(json.dumps(state))
    bots = state.setdefault("bots", {})
    events = state.setdefault("events", [])
    for i in range(1, BOT_COUNT + 1):
        key = f"bot-{i:02d}"
        bot = bots.setdefault(key, {"name": f"Bot {i:02d}", "xp": 0, "activity_count": 0})
        previous = state.get("last_tick")
        if previous:
            prev = datetime.fromisoformat(previous.replace("Z", "+00:00"))
        else:
            prev = now - timedelta(minutes=interval_minutes)
        due = max(0, min(max_steps, int((now - prev).total_seconds() // (interval_minutes * 60))))
        for step in range(due):
            kind = EVENTS[(i + bot["activity_count"]) % len(EVENTS)]
            bot["activity_count"] += 1
            bot["xp"] += 2 if kind in ("read", "quiz", "practice") else 1
            events.append({"bot_id": key, "type": kind, "at": (prev + timedelta(minutes=interval_minutes * (step + 1))).isoformat()})
    state["last_tick"] = now.isoformat()
    state["events"] = events[-500:]
    return state

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    args = parser.parse_args()
    from pathlib import Path
    path = Path(args.state)
    state = json.loads(path.read_text()) if path.exists() else {}
    updated = advance(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(updated, ensure_ascii=False, indent=2))
    temp.replace(path)
    print(json.dumps({"bots": len(updated["bots"]), "events": len(updated["events"])}))

if __name__ == "__main__":
    main()
