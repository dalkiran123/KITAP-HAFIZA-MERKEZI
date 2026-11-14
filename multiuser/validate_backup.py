"""Read-only validator for Kitap Hafiza Merkezi exported JSON backups."""
import json
import sys
from pathlib import Path
MAX_BYTES = 20 * 1024 * 1024

def inspect(path):
    p = Path(path)
    if p.stat().st_size > MAX_BYTES:
        raise ValueError('Yedek dosyası beklenen boyutu aşıyor')
    data = json.loads(p.read_text(encoding='utf-8'))
    if isinstance(data, list):
        books, requests, history, storage = data, [], [], {}
        version = 'legacy-list'
    elif isinstance(data, dict):
        version = data.get('version', 'unknown')
        books = data.get('books')
        requests = data.get('requests', [])
        history = data.get('requestHistory', [])
        storage = data.get('localStorage', {})
    else:
        raise ValueError('Geçersiz yedek yapısı')
    if not isinstance(books, list):
        raise ValueError('Kitap listesi bulunamadı')
    if not isinstance(requests, list) or not isinstance(history, list) or not isinstance(storage, dict):
        raise ValueError('Yedek alanlarının türleri geçersiz')
    ids = []
    for b in books:
        if not isinstance(b, dict) or not all(isinstance(b.get(k), str) for k in ('id', 'name', 'author', 'summary')):
            raise ValueError('Kitap kaydı geçersiz')
        ids.append(b['id'])
    if len(ids) != len(set(ids)):
        raise ValueError('Tekrarlanan kitap kimlikleri var; otomatik aktarım durdurulmalı')
    for k,v in storage.items():
        if not isinstance(k,str) or not k.startswith('kitap-hafiza') or not isinstance(v,str):
            raise ValueError('Beklenmeyen yerel kayıt alanı')
    return {'format':version,'books':len(books),'requests':len(requests),'request_history':len(history),'local_storage_keys':len(storage),'safe_to_review':True}

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Kullanım: python validate_backup.py YEDEK.json')
    try:
        print(json.dumps(inspect(sys.argv[1]), ensure_ascii=False, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as e:
        sys.exit('Doğrulama başarısız: '+str(e))
