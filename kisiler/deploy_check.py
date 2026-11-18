"""Standalone deployment checklist for the optional People simulation.

Never modify existing BOOK CENTER jobs or production databases.
Set BOOKCENTER_PEOPLE_DB to a *new* private SQLite path. The web app
must expose only people_api.application (read-only).
"""
import os
import sys
import sqlite3

def check():
    path = os.environ.get("BOOKCENTER_PEOPLE_DB", "")
    if not path:
        return ["BOOKCENTER_PEOPLE_DB tanımlanmamış."]
    if not os.path.isabs(path):
        return ["Veritabanı yolu mutlak olmalı."]
    if not os.path.isdir(os.path.dirname(path)):
        return ["Veritabanı klasörü mevcut değil."]
    if os.path.exists(path):
        if not os.path.isfile(path):
            return ["Veritabanı yolu normal dosya değil."]
        try:
            con = sqlite3.connect("file:" + os.path.realpath(path) + "?mode=ro", uri=True)
            try:
                tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not {"people","activity","engine_ticks"}.issubset(tables):
                    return ["Mevcut dosya sanal yaşam veritabanı değil. Üzerine yazmayın."]
            finally:
                con.close()
        except sqlite3.Error:
            return ["Mevcut dosya geçerli SQLite veritabanı değil."]
    return []

if __name__ == "__main__":
    problems = check()
    if problems:
        for item in problems:
            print("HATA:", item)
        sys.exit(1)
    print("Ortam hazır. İlk kurulum: python people_engine.py init")
    print("Zamanlanmış görev: python scheduled_world.py")
    print("WSGI uygulaması: people_api.application")
    print("GitHub Pages kisiler/config.json apiBase: yalnızca HTTPS sunucu adresi")
