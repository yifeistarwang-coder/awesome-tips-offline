#!/usr/bin/env python3
"""Prepare translation batches for the X thread archive.

Reads threads/.cache/*.json and threads the tweet texts (chain tweets, quoted
tweets, meaningful extras, and README titles) into numbered batch files under
threads/zh/_src/. Each batch is small enough to translate in one pass.

After translating every batch into threads/zh/_out/batch-XX.json
(same keys), run scripts/render_x_threads_zh.py to build the Chinese archive.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_x_threads import CACHE_DIR, parse_readme  # noqa: E402

ZH = ROOT / "threads" / "zh"
SRC = ZH / "_src"
OUT = ZH / "_out"

# Roughly 9k English characters per batch.
CHAR_BUDGET = 9000


def is_meaningful_extra(tweet: dict) -> bool:
    if tweet.get("photos") or tweet.get("videos"):
        return True
    text = (tweet.get("text") or "").strip()
    if len(text) < 60:
        return False
    return not re.fullmatch(r"(@\w+\s*)+[^A-Za-z]{0,3}(Thanks|Thank you)[^A-Za-z]{0,3}", text, re.I)


def collect_items() -> list[dict]:
    sections = parse_readme()
    items: list[dict] = []
    seen_keys: set[str] = set()

    def add(key: str, en: str, kind: str, title: str = "") -> None:
        en = (en or "").strip()
        if not en or key in seen_keys:
            return
        seen_keys.add(key)
        items.append({"key": key, "kind": kind, "title": title, "en": en})

    for category, posts in sections:
        for title, tid in posts:
            cache = CACHE_DIR / f"{tid}.json"
            if not cache.exists():
                continue
            res = json.loads(cache.read_text(encoding="utf-8"))
            add(f"title:{tid}", title, "title")
            for tweet in res.get("chain") or []:
                if tweet.get("tombstone"):
                    continue
                add(tweet["id"], tweet.get("text", ""), "tweet", title)
                quoted = tweet.get("quoted") or {}
                if quoted.get("text"):
                    add(f"{tweet['id']}#quoted", quoted["text"], "quoted", title)
            for tweet in res.get("extras") or []:
                if is_meaningful_extra(tweet):
                    add(tweet["id"], tweet.get("text", ""), "extra", title)
    return items


def main() -> None:
    SRC.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    items = collect_items()
    batches: list[list[dict]] = []
    current: list[dict] = []
    chars = 0
    for item in items:
        n = len(item["en"])
        if current and chars + n > CHAR_BUDGET:
            batches.append(current)
            current = []
            chars = 0
        current.append(item)
        chars += n
    if current:
        batches.append(current)

    for i, batch in enumerate(batches, 1):
        path = SRC / f"batch-{i:02d}.json"
        path.write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = {
        "total_items": len(items),
        "total_chars": sum(len(x["en"]) for x in items),
        "batches": len(batches),
    }
    (SRC / "index.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False))
    for i, batch in enumerate(batches, 1):
        print(f"  batch-{i:02d}: {len(batch)} items, {sum(len(x['en']) for x in batch)} chars")


if __name__ == "__main__":
    main()
