"""Persona-consistent simulated replies with durable conversation memory.
Not a language model; deterministic context-aware template responses.
Caller must authenticate user and enforce rate limits before calling send_message.
"""
import datetime as dt
import hashlib
import json
import sqlite3

def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS friend_direct_messages(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id TEXT NOT NULL, person_id INTEGER NOT NULL,
      sender TEXT NOT NULL CHECK(sender IN ('user','bot')),
      body TEXT NOT NULL, created_at TEXT NOT NULL,
      simulated INTEGER NOT NULL DEFAULT 1
    );
    CREATE INDEX IF NOT EXISTS friend_dm_thread ON friend_direct_messages(user_id,person_id,id);
    """)

def _persona(db, person_id):
    row = None
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='person_personas'").fetchone():
        row = db.execute("SELECT profile_json FROM person_personas WHERE person_id=?", (person_id,)).fetchone()
    try:
        return json.loads(row[0]) if row else {}
    except (ValueError, TypeError):
        return {}

def reply_for(db, person_id, message):
    """Constrained replies grounded in persona fields; never invent personal memories."""
    profile = _persona(db, person_id)
    traits = profile.get("traits") or {}
    style = str(profile.get("speaking_style") or "doğal").lower()
    interests = [str(x)[:70] for x in profile.get("interests", []) if isinstance(x, str)]
    genres = [str(x)[:70] for x in profile.get("preferred_genres", []) if isinstance(x, str)]
    message_lower = message.casefold()
    if any(x in message_lower for x in ("merhaba", "selam", "nasılsın")):
        core = "Merhaba! Bugün kitaplardan konuşmak ister misin?"
    elif any(x in message_lower for x in ("kitap", "oku", "roman", "öner")):
        core = ("Ben " + genres[0] + " türünü seviyorum. Sen en son ne okudun?") if genres else "En son okuduğun kitabı anlatır mısın? Birlikte değerlendirelim."
    elif any(x in message_lower for x in ("fotoğraf", "resim", "görsel")):
        core = "Profilimdeki sanal görsel sahnelerine bakabilirsin. Gerçek bir fotoğraf çekmiyorum."
    elif interests:
        core = interests[0] + " ilgimi çekiyor. Senin bu konudaki düşüncen ne?"
    else:
        core = "Bunu biraz daha anlatır mısın? Seni dinliyorum."
    if traits.get("competitiveness", 50) >= 75 and "kitap" in message_lower:
        core += " İstersen okuma yarışması da yapalım!"
    if traits.get("humor", 50) >= 75:
        core += " 🙂"
    if "kısa" in style or "öz" in style:
        core = core.split(". ")[0].rstrip(".") + "."
    return core[:600]

def send_message(db, user_id, person_id, body, now=None):
    if not isinstance(user_id, str) or not 1 <= len(user_id) <= 100:
        raise ValueError("invalid user id")
    if type(person_id) is not int or not 1 <= person_id <= 10:
        raise ValueError("invalid person id")
    if not isinstance(body, str) or not 1 <= len(body.strip()) <= 1000:
        raise ValueError("message must be 1-1000 characters")
    if not db.execute("SELECT 1 FROM people WHERE id=? AND simulated=1", (person_id,)).fetchone():
        raise ValueError("bot does not exist")
    ensure_schema(db)
    timestamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat()
    answer = reply_for(db, person_id, body.strip())
    with db:
        db.execute("INSERT INTO friend_direct_messages(user_id,person_id,sender,body,created_at) VALUES(?,?,'user',?,?)",
                   (user_id, person_id, body.strip(), timestamp))
        db.execute("INSERT INTO friend_direct_messages(user_id,person_id,sender,body,created_at) VALUES(?,?,'bot',?,?)",
                   (user_id, person_id, answer, timestamp))
    return {"person_id": person_id, "reply": answer, "simulated": True, "engine": "persona_rules_v1"}

def history(db, user_id, person_id, limit=50):
    ensure_schema(db)
    rows = db.execute("SELECT sender,body,created_at FROM friend_direct_messages WHERE user_id=? AND person_id=? ORDER BY id DESC LIMIT ?",
                      (user_id, person_id, max(1, min(int(limit),100)))).fetchall()
    return [{"sender":r[0],"body":r[1],"created_at":r[2],"simulated":r[0]=="bot"} for r in reversed(rows)]
