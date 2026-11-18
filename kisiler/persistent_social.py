"""Persistent fictional social feed for BOOK CENTER Friends.
Server-side SQLite only; caller owns authentication and scheduling.
No remote image uploads or AI-generated replies in this module.
"""
import datetime as dt
import hashlib
import json
import random
import sqlite3

CAPTIONS = (
    "Bugün okuduğum bölüm beni düşündürdü. Sizce iyi bir hikâye neyi değiştirebilir?",
    "Yeni bir kitap seçtim. Bu hafta okuma hedefime yaklaşmak istiyorum.",
    "Kitap notlarımı düzenledim. Bazı cümleler uzun süre akılda kalıyor.",
    "Bir hikâyenin farklı karakterlerini karşılaştırmak çok ilginç.",
    "Kısa bir mola verdim. Sonra kaldığım sayfadan devam edeceğim.",
)
SCENES = ("reading-desk", "library", "notebook", "window", "coffee")



def persona_for(db, person_id):
    """Read a persisted fictional profile without mutating it."""
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='person_personas'").fetchone():
        return {}
    row = db.execute("SELECT profile_json FROM person_personas WHERE person_id=?", (person_id,)).fetchone()
    if not row:
        return {}
    try:
        data = json.loads(row[0])
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def persona_post(db, person_id, rng):
    profile = persona_for(db, person_id)
    traits = profile.get("traits") or {}
    genres = [x.strip()[:60] for x in profile.get("preferred_genres", []) if isinstance(x, str) and x.strip()]
    interests = [x.strip()[:60] for x in profile.get("interests", []) if isinstance(x, str) and x.strip()]
    if genres:
        topic = rng.choice(genres)
        caption = f"Bugün {topic} türünde bir kitap üzerine düşünüyorum. Siz hangi kitabı önerirsiniz?"
        scene = "library"
    elif interests:
        topic = rng.choice(interests)
        caption = f"Bugün {topic} hakkında notlar aldım. Yeni bir şey öğrenmek güzel."
        scene = "notebook"
    elif traits.get("competitiveness", 50) >= 75:
        caption = "Bu haftaki okuma hedefimi yükselttim. Kim benimle yarışmak ister?"
        scene = "reading-desk"
    elif traits.get("sociability", 50) >= 75:
        caption = "Birlikte kitap okumak daha keyifli. Bugün kimler burada?"
        scene = "coffee"
    else:
        caption, scene = rng.choice(CAPTIONS), rng.choice(SCENES)
    if traits.get("humor", 50) >= 75:
        caption += " 🙂"
    return caption[:500], scene


def persona_comment(db, person_id, rng):
    profile = persona_for(db, person_id)
    traits = profile.get("traits") or {}
    if traits.get("competitiveness", 50) >= 75:
        return "Güzel paylaşım! Okuma hedeflerinde yarışalım mı?"
    if traits.get("empathy", 50) >= 75:
        return "Paylaştığın için teşekkürler, düşüncelerini merak ettim."
    if traits.get("curiosity", 50) >= 75:
        return "Bu konuyla ilgili biraz daha anlatır mısın?"
    return rng.choice(("Güzel bir paylaşım!", "Ben de benzer düşünüyorum.", "Hangi kitabı önerirsin?"))


def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS friend_posts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_key TEXT NOT NULL UNIQUE,
      person_id INTEGER NOT NULL,
      caption TEXT NOT NULL,
      scene TEXT NOT NULL,
      created_at TEXT NOT NULL,
      simulated INTEGER NOT NULL DEFAULT 1 CHECK(simulated=1)
    );
    CREATE TABLE IF NOT EXISTS friend_comments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      event_key TEXT NOT NULL UNIQUE,
      post_id INTEGER NOT NULL REFERENCES friend_posts(id),
      person_id INTEGER NOT NULL,
      body TEXT NOT NULL,
      created_at TEXT NOT NULL,
      simulated INTEGER NOT NULL DEFAULT 1 CHECK(simulated=1)
    );
    CREATE TABLE IF NOT EXISTS friend_likes (
      post_id INTEGER NOT NULL REFERENCES friend_posts(id),
      person_id INTEGER NOT NULL,
      created_at TEXT NOT NULL,
      PRIMARY KEY(post_id,person_id)
    );
    CREATE INDEX IF NOT EXISTS friend_posts_recent ON friend_posts(created_at DESC,id DESC);
    """)


def tick(db, slot=None):
    """Idempotent hourly fictional social activity, reproducible across retries."""
    if slot is None:
        slot = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
    if isinstance(slot, str):
        slot = dt.datetime.fromisoformat(slot.replace("Z", "+00:00"))
    if slot.tzinfo is None:
        raise ValueError("slot must have timezone")
    slot = slot.astimezone(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
    key = slot.isoformat()
    ensure_schema(db)
    people = db.execute("SELECT id FROM people WHERE simulated=1 ORDER BY id LIMIT 10").fetchall()
    ids = [row[0] for row in people]
    if not ids:
        return {"slot": key, "posts": 0, "comments": 0, "likes": 0}
    rng = random.Random("friends-v6:" + key)
    author = rng.choice(ids)
    caption, scene = persona_post(db, author, rng)
    post_key = "post:" + key
    posts = comments = likes = 0
    with db:
        cur = db.execute(
            "INSERT OR IGNORE INTO friend_posts(event_key,person_id,caption,scene,created_at) VALUES(?,?,?,?,?)",
            (post_key, author, caption, scene, key))
        posts += int(cur.rowcount > 0)
        post_id = db.execute("SELECT id FROM friend_posts WHERE event_key=?", (post_key,)).fetchone()[0]
        others = [x for x in ids if x != author]
        rng.shuffle(others)
        for other in others[:min(2, len(others))]:
            comment_key = f"comment:{key}:{other}"
            cur = db.execute(
                "INSERT OR IGNORE INTO friend_comments(event_key,post_id,person_id,body,created_at) VALUES(?,?,?,?,?)",
                (comment_key, post_id, other, persona_comment(db, other, rng), key))
            comments += int(cur.rowcount > 0)
        for other in others[:min(4, len(others))]:
            cur = db.execute(
                "INSERT OR IGNORE INTO friend_likes(post_id,person_id,created_at) VALUES(?,?,?)",
                (post_id, other, key))
            likes += int(cur.rowcount > 0)
    return {"slot": key, "posts": posts, "comments": comments, "likes": likes, "simulated": True}


def feed(db, limit=20):
    ensure_schema(db)
    limit = max(1, min(int(limit), 50))
    rows = db.execute("""
      SELECT p.id,p.person_id,pe.name,p.caption,p.scene,p.created_at,
      (SELECT COUNT(*) FROM friend_likes l WHERE l.post_id=p.id) likes
      FROM friend_posts p JOIN people pe ON pe.id=p.person_id
      ORDER BY p.created_at DESC,p.id DESC LIMIT ?""", (limit,)).fetchall()
    result = []
    for r in rows:
        comments = db.execute("""
          SELECT c.person_id,pe.name,c.body,c.created_at FROM friend_comments c
          JOIN people pe ON pe.id=c.person_id WHERE c.post_id=?
          ORDER BY c.id LIMIT 30""", (r[0],)).fetchall()
        result.append({"id":r[0],"person_id":r[1],"name":r[2],"caption":r[3],
                       "scene":r[4],"created_at":r[5],"likes":r[6],
                       "comments":[{"person_id":c[0],"name":c[1],"body":c[2],"created_at":c[3]} for c in comments],
                       "simulated":True})
    return result
