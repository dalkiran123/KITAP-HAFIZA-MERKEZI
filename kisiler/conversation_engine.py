"""Auditable fictional conversations between simulated BOOK CENTER people.

Messages are deterministic scenario lines, not live AI chat. Each pair can
produce one exchange per day. No external delivery or real-world messaging.
"""
import datetime as dt
import random
import json

TOPICS = (
    ("book", "Son okuduğun kitap hakkında ne düşünüyorsun?",
     "Beni düşündüren bir bölümü vardı, konuşalım."),
    ("work", "Bugün işlerin nasıl gidiyor?",
     "Yoğun geçti. Akşam biraz kitap okumak iyi gelecek."),
    ("reading", "Birlikte aynı kitabı okuyalım mı?",
     "Olur, sonra yorumlarımızı karşılaştırırız."),
    ("life", "Son günlerde hayatında neler değişti?",
     "Bazı yeni kararlar aldım, zamanla anlatırım."),
)


def ensure_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS bot_conversations (
      id INTEGER PRIMARY KEY AUTOINCREMENT, person_a INTEGER NOT NULL,
      person_b INTEGER NOT NULL, day TEXT NOT NULL, topic TEXT NOT NULL,
      simulated INTEGER NOT NULL DEFAULT 1, UNIQUE(person_a,person_b,day));
    CREATE TABLE IF NOT EXISTS bot_conversation_messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL,
      sender_id INTEGER NOT NULL, text TEXT NOT NULL, sequence INTEGER NOT NULL,
      simulated INTEGER NOT NULL DEFAULT 1,
      UNIQUE(conversation_id,sequence));
    """)


def contextual_topic(db, person_id, rng):
    """Use an explicit fictional profile or recent life event when present."""
    row = db.execute("SELECT profile_json FROM person_personas WHERE person_id=?", (person_id,)).fetchone() if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='person_personas'").fetchone() else None
    if row:
        profile = json.loads(row[0])
        interests = profile.get("interests") or []
        if interests:
            interest = str(rng.choice(interests))[:100]
            return ("interest", f"{interest} hakkında yeni bir şey öğrendin mi?", "Bu konuyu konuşmak güzel, birlikte araştırabiliriz.")
        occupation = str(profile.get("occupation") or "")[:100]
        if occupation:
            return ("occupation", f"{occupation} alanındaki çalışmaların nasıl gidiyor?", "Bugün biraz yoğundu, akşam kitap okumayı düşünüyorum.")
    if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='life_world_events'").fetchone():
        event = db.execute("SELECT description FROM life_world_events WHERE person_id=? ORDER BY day DESC,id DESC LIMIT 1", (person_id,)).fetchone()
        if event:
            return ("memory", "Son yaşadığın değişiklik hakkında konuşmak ister misin?", "Evet, hayatımdaki yeni gelişmeleri değerlendirmeye çalışıyorum.")
    return rng.choice(TOPICS)


def simulate_day(db, day=None):
    day = day or dt.datetime.now(dt.timezone.utc).date().isoformat()
    dt.date.fromisoformat(day)
    ensure_schema(db)
    created = 0
    with db:
        rows = db.execute(
            "SELECT person_a,person_b,closeness FROM social_relations "
            "WHERE closeness>=10 ORDER BY person_a,person_b").fetchall()
        for a,b,closeness in rows:
            rng = random.Random(f"bookcenter-conversation-v1:{a}:{b}:{day}")
            if rng.random() >= min(0.65,0.10+closeness/150):
                continue
            topic, opening, reply = contextual_topic(db, a, rng)
            cursor = db.execute(
                "INSERT OR IGNORE INTO bot_conversations(person_a,person_b,day,topic) "
                "VALUES(?,?,?,?)", (a,b,day,topic))
            if not cursor.rowcount:
                continue
            created += 1
            conversation_id = cursor.lastrowid
            db.executemany(
                "INSERT INTO bot_conversation_messages(conversation_id,sender_id,text,sequence) "
                "VALUES(?,?,?,?)",
                [(conversation_id,a,opening,1),(conversation_id,b,reply,2)])
    return {"day":day,"created":created,"simulated":True}


def conversations(db, person_id, limit=20):
    rows = db.execute(
        "SELECT c.day,c.topic,m.sender_id,m.text,c.person_a,c.person_b "
        "FROM bot_conversations c JOIN bot_conversation_messages m "
        "ON m.conversation_id=c.id "
        "WHERE c.person_a=? OR c.person_b=? "
        "ORDER BY c.day DESC,c.id DESC,m.sequence ASC LIMIT ?",
        (person_id,person_id,max(1,min(int(limit),100)))).fetchall()
    return [{"day":r[0],"topic":r[1],"sender_id":r[2],
             "text":r[3],"other_id":r[5] if r[4]==person_id else r[4],
             "simulated":True} for r in rows]
