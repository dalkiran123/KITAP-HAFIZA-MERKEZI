#!/usr/bin/env python3
"""Read-only validation for Kitap Hafıza Merkezi catalog. Never modifies user data."""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path, variable):
    source = (ROOT / path).read_text(encoding="utf-8")
    match = re.fullmatch(r"\s*window\." + re.escape(variable) + r"\s*=\s*(\[.*\])\s*;?\s*", source, re.S)
    if not match:
        raise ValueError(f"{path}: unexpected JavaScript wrapper")
    return json.loads(match.group(1))

def paragraphs(value):
    return [p.strip() for p in re.split(r"\n\s*\n", value or "") if p.strip()]

def main():
    catalog = load("catalog.js", "KITAP_CATALOG")
    queue = load("catalog-queue.js", "KITAP_UPCOMING")
    issues = []
    seen = set()
    for book in catalog:
        key = (book.get("name", "").casefold().strip(), book.get("author", "").casefold().strip())
        if key in seen:
            issues.append(f"DUPLICATE catalog: {book.get('name')}")
        seen.add(key)
        counts = [len(paragraphs(book.get(field))) for field in ("summary", "longSummary", "detailSummary")]
        if counts[0] != 6 or counts[1] != 20:
            issues.append(f"INCOMPLETE legacy summaries: {book.get('name')} {counts[:2]}")
        if counts[2] not in (0, 100):
            issues.append(f"INCOMPLETE detailSummary: {book.get('name')} {counts[2]}/100")
        stamp = book.get("preparedAt")
        if stamp:
            try:
                datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            except ValueError:
                issues.append(f"INVALID preparedAt: {book.get('name')}")
        isbn = str(book.get("isbn") or "").replace("-", "").replace(" ", "")
        if isbn and (not isbn.isdigit() or len(isbn) not in (10, 13)):
            issues.append(f"INVALID ISBN format: {book.get('name')}")
    for book in queue:
        key = (book.get("name", "").casefold().strip(), book.get("author", "").casefold().strip())
        if key in seen:
            issues.append(f"READY ALSO QUEUED: {book.get('name')}")
    detailed = sum(len(paragraphs(x.get("detailSummary"))) == 100 for x in catalog)
    print(f"Catalog={len(catalog)} Queue={len(queue)} Complete100={detailed} Issues={len(issues)}")
    for item in issues:
        print(" -", item)
    return 1 if issues else 0

if __name__ == "__main__":
    sys.exit(main())
