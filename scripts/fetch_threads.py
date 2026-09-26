#!/usr/bin/env python3
"""Fetch public root-post text and attached media for awesome-tips links."""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
OUTPUT = ROOT / "threads"
USER_AGENT = "Mozilla/5.0 (compatible; awesome-tips-archiver/1.0)"


def request(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def get_tweet(tweet_id: str) -> dict:
    url = f"https://api.fxtwitter.com/status/{tweet_id}"
    last_error = None
    for attempt in range(5):
        try:
            data = json.loads(request(url))
            if data.get("code") == 200 and data.get("tweet"):
                return data["tweet"]
            last_error = data.get("message", "No tweet data returned")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(2 ** attempt)
    raise RuntimeError(str(last_error))


def safe_name(text: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return name or "misc"


def extract_sections() -> list[tuple[str, list[tuple[str, str]]]]:
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    seen_ids: set[str] = set()
    current = "Other"
    for line in README.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^###\s+(.+)$", line)
        if heading:
            current = heading.group(1).strip()
            sections.append((current, []))
            continue
        link = re.match(r"^- \[([^]]+)\]\(https?://(?:twitter|x)\.com/jbhuang0604/status/(\d+)[^)]*\)", line)
        if link:
            if link.group(2) in seen_ids:
                continue
            seen_ids.add(link.group(2))
            if not sections or sections[-1][0] != current:
                sections.append((current, []))
            sections[-1][1].append((link.group(1), link.group(2)))
    return sections


def download_media(tweet: dict, tweet_id: str) -> list[str]:
    media = tweet.get("media", {}).get("all", [])
    local_paths = []
    folder = OUTPUT / "media"
    folder.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(media, 1):
        if item.get("type") != "photo":
            continue
        source = item.get("url", "")
        parsed = urllib.parse.urlparse(source)
        filename = Path(parsed.path).name or f"image-{index}.jpg"
        suffix = Path(filename).suffix or ".jpg"
        target = folder / f"{tweet_id}-{index}{suffix}"
        if not target.exists():
            proxy_url = "https://wsrv.nl/?url=" + urllib.parse.quote(source, safe="")
            last_error = None
            for attempt in range(3):
                try:
                    content = request(proxy_url, timeout=45)
                    if len(content) < 256:
                        raise RuntimeError("Image response was unexpectedly small")
                    target.write_bytes(content)
                    last_error = None
                    break
                except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                    last_error = str(exc)
                    time.sleep(2 ** attempt)
            if last_error:
                print(f"  image failed {tweet_id}: {last_error}")
                continue
        local_paths.append("media/" + target.name)
    return local_paths


def main() -> None:
    sections = extract_sections()
    OUTPUT.mkdir(exist_ok=True)
    index_lines = [
        "# X/Twitter 线程归档",
        "",
        "来源：Jia-Bin Huang 的 [awesome-tips 仓库](../README.md)。以下归档保留原帖英文文本，并本地保存可获取的配图。",
        "",
        "> 说明：公开接口目前只返回根帖及其附件，不返回完整回复串。很多线程的建议要点在图片中；未抓取到的回复不会被推测补写。视频附件不下载。",
        "",
    ]
    total = sum(len(posts) for _, posts in sections)
    done = 0
    for category, posts in sections:
        if not posts:
            continue
        # The same tweet can appear under multiple topics; archive it once under its first listing.
        posts = list(dict((tweet_id, (title, tweet_id)) for title, tweet_id in posts).values())
        filename = safe_name(category) + ".md"
        lines = [f"# {category}", ""]
        seen_ids: set[str] = set()
        for title, tweet_id in posts:
            if tweet_id in seen_ids:
                continue
            seen_ids.add(tweet_id)
            done += 1
            try:
                tweet = get_tweet(tweet_id)
                text = html.unescape(tweet.get("text", "")).strip()
                date = tweet.get("created_at", "")
                images = download_media(tweet, tweet_id)
                lines.extend([f"## {title}", "", f"原帖：[{tweet_id}](https://x.com/jbhuang0604/status/{tweet_id})" + (f" · {date}" if date else ""), ""])
                lines.extend([text, ""])
                for image in images:
                    lines.extend([f"![{title}]({image})", ""])
                if not images and not text:
                    lines.extend(["_未获取到公开文本或配图。_", ""])
                print(f"[{done}/{total}] fetched {tweet_id} ({len(images)} images)")
            except Exception as exc:
                print(f"[{done}/{total}] failed {tweet_id}: {exc}")
                lines.extend([f"## {title}", "", f"原帖：[https://x.com/jbhuang0604/status/{tweet_id}](https://x.com/jbhuang0604/status/{tweet_id})", "", f"_抓取失败：{exc}_", ""])
            time.sleep(1.2)
        (OUTPUT / filename).write_text("\n".join(lines), encoding="utf-8")
        index_lines.append(f"- [{category}]({filename})")
    index_lines.append("")
    (OUTPUT / "README.md").write_text("\n".join(index_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
