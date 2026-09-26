#!/usr/bin/env python3
"""Render the Chinese version of the X thread archive.

Reads the English archive cache (threads/.cache/*.json) plus the translated
texts (threads/zh/_out/batch-*.json) and writes:

    threads/zh/<category>.md      — per-category Chinese threads
    threads/zh/README.md          — Chinese index
    threads/zh/all-threads.md     — single-file Chinese collection

Media files stay in threads/media/ and are referenced as ../media/...
Missing translations fall back to the English text with a marker.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_x_threads import (  # noqa: E402
    CACHE_DIR,
    MEDIA_DIR,
    THREADS_DIR,
    collect_media,
    fmt_date,
    is_meaningful_extra,
    parse_readme,
    safe_name,
)

ZH_DIR = THREADS_DIR / "zh"
OUT_DIR = ZH_DIR / "_out"

CATEGORY_ZH = {
    "Doing Research": "做研究",
    "Working with your mentors": "与导师共事",
    "Writing": "写作",
    "Presentation": "演讲",
    "Poster Presentation": "海报展示",
    "Communication": "沟通",
    "Career": "职业发展",
    "Productivity": "效率",
    "Networking": "社交",
    "Financial": "财务",
}


def load_translations() -> dict[str, str]:
    merged: dict[str, str] = {}
    for path in sorted(OUT_DIR.glob("batch-*.json")):
        merged.update(json.loads(path.read_text(encoding="utf-8")))
    return merged


def tr(trans: dict[str, str], key: str, fallback: str) -> str:
    value = trans.get(key)
    if value:
        return value
    fallback = (fallback or "").strip()
    if fallback:
        return fallback + "\n\n（此段暂无中文翻译，保留英文原文。）"
    return ""


def clean(text: str) -> str:
    lines = [line.rstrip() for line in (text or "").replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines).strip()


def render_media(tweet: dict, ok_files: set[str], no_dash: bool = False) -> list[str]:
    lines: list[str] = []
    for photo in tweet.get("photos") or []:
        name = photo.get("file")
        if name and name in ok_files:
            lines.append(f"![配图](../media/{name})")
            lines.append("")
    for video in tweet.get("videos") or []:
        poster = video.get("poster_file")
        mp4 = video.get("file")
        kind = "GIF 动画" if video.get("type") == "animated_gif" else "视频"
        if poster and poster in ok_files and mp4 and mp4 in ok_files:
            lines.append(f"[![{kind}预览](../media/{poster})](../media/{mp4})")
            lines.append("")
            lines.append(f"▶ [{kind}（点击播放）](../media/{mp4})")
            lines.append("")
        elif poster and poster in ok_files:
            lines.append(f"![{kind}预览](../media/{poster})")
            lines.append("")
        elif mp4 and mp4 in ok_files:
            lines.append(f"▶ [{kind}（点击播放）](../media/{mp4})")
            lines.append("")
        elif video.get("url"):
            lines.append(f"▶ [{kind}（原视频已失效，需在线播放）]({tweet['url']})")
            lines.append("")
    return lines


def render_tweet(tweet: dict, trans: dict[str, str], ok_files: set[str]) -> list[str]:
    lines: list[str] = []
    text = tr(trans, tweet["id"], tweet.get("text", ""))
    article = tweet.get("article") or {}
    if article.get("text"):
        title = article.get("title") or ""
        if title:
            lines.append(f"**{title}**")
            lines.append("")
        text = article["text"]
    if text.strip():
        lines.append(clean(text))
        lines.append("")
    quoted = tweet.get("quoted") or {}
    qtext = tr(trans, f"{tweet['id']}#quoted", quoted.get("text", ""))
    if qtext.strip():
        qauthor = quoted.get("author") or "i"
        qlines = [f"> **引用 [@{qauthor}](https://x.com/{qauthor})**：", ">"]
        for qline in clean(qtext).split("\n"):
            qlines.append("> " + qline if qline else ">")
        lines.extend(qlines)
        lines.append("")
    lines.extend(render_media(tweet, ok_files))
    links = [u for u in (tweet.get("links") or []) if isinstance(u, str)]
    if links:
        lines.append("相关链接：")
        for url in links:
            card = tweet.get("card")
            label = ""
            if card and card.get("url") == url and card.get("title"):
                label = f" — {card['title']}"
            lines.append(f"- <{url}>{label}")
        lines.append("")
    return lines


def render_thread(title_zh: str, en_title: str, res: dict, trans: dict[str, str], ok_files: set[str]) -> list[str]:
    chain = res.get("chain") or []
    tweets = [t for t in chain if not t.get("tombstone")]
    gaps = [t for t in chain if t.get("tombstone")]
    if not tweets:
        return [f"## {title_zh}", "", "_未获取到线程内容。_", ""]
    first = tweets[0]
    focal = next((t for t in tweets if t["id"] == res.get("focal_id")), first)
    header = f"原帖：<{first['url']}> · {fmt_date(focal.get('created_at', ''))} · 共 {len(tweets)} 条串文"
    if gaps:
        header += f"（另有 {len(gaps)} 条在 X 上已不可用）"
    lines = [f"## {title_zh}", "", header, ""]
    for tweet in chain:
        if tweet.get("tombstone"):
            lines.extend(["> ⚠️ 此处一条推文在 X 上显示为「不可用」（可能已删除），线程内容在此处不连续。", ""])
            continue
        lines.extend(render_tweet(tweet, trans, ok_files))
    extras = [t for t in (res.get("extras") or []) if is_meaningful_extra(t)]
    if extras:
        lines.extend(["### 作者补充回复", ""])
        for tweet in extras:
            text = tr(trans, tweet["id"], tweet.get("text", ""))
            if text.strip():
                lines.append(clean(text))
                lines.append("")
            lines.extend(render_media(tweet, ok_files))
            lines.append(f"<{tweet['url']}>")
            lines.append("")
    return lines


def main() -> None:
    trans = load_translations()
    results: dict[str, dict] = {}
    for path in CACHE_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        results[data["focal_id"]] = data
    collect_media(results)  # assign media file names (no download)
    ok_files = {p.name for p in MEDIA_DIR.iterdir() if p.is_file()}

    sections = parse_readme()
    missing = 0

    def tr_count(lines: list[str]) -> None:
        nonlocal missing
        missing += sum(1 for line in lines if "此段暂无中文翻译" in line)

    index_lines = [
        "# X/Twitter 线程归档（中文版·完整串文）",
        "",
        "来源：Jia-Bin Huang 的 [awesome-tips 仓库](../../README.md)。中文译自对应的英文归档（[EN 版](../README.md)）。",
        "",
        "> 全部 66 条线程的完整串文、配图与 GIF/短视频均已本地化，正文为中文翻译，专有名词保留原文。",
        "> 已删除的推文以 ⚠️ 标记。英文原文见 [threads/](../README.md)，单文件合集见 [all-threads.md](all-threads.md)。",
        "> 更多：[Bluesky 帖子中译](bsky-how-to-drive-your-research-forward.md) · [讲稿幻灯片中译](../slides/README.md) · [双语 README](../../README-CN.md)。",
        "",
    ]
    combined = ["# Awesome Tips：X/Twitter 线程完整合集（中文版）", "", "按 [README](../README.md) 分类整理的完整串文中译（含配图）。", ""]

    for category, posts in sections:
        cat_zh = CATEGORY_ZH.get(category, category)
        filename = safe_name(category) + ".md"
        lines = [f"# {cat_zh}", "", f"> 完整串文中译（{len(posts)} 条）。返回 [中文索引](README.md) · [英文原版](../{filename})。", ""]
        combined.extend([f"# {cat_zh}", ""])
        rendered: set[str] = set()
        for title, tid in posts:
            title_zh = trans.get(f"title:{tid}", title).strip() or title
            res = results.get(tid)
            if tid in rendered:
                lines.extend([f"## {title_zh}", "", f"_此线程已收录于本文件另一分类，见英文版索引。_", ""])
                continue
            if not res:
                lines.extend([f"## {title_zh}", "", f"原帖：<https://x.com/jbhuang0604/status/{tid}>", "", "_抓取数据缺失。_", ""])
                continue
            rendered.add(tid)
            block = render_thread(title_zh, title, res, trans, ok_files)
            tr_count(block)
            lines.extend(block)
            combined.extend(block)
        (ZH_DIR / filename).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        index_lines.append(f"- [{cat_zh}]({filename})（{len(posts)} 条）")
        print(f"  写入 threads/zh/{filename}")

    index_lines.append("")
    (ZH_DIR / "README.md").write_text("\n".join(index_lines), encoding="utf-8")
    (ZH_DIR / "all-threads.md").write_text("\n".join(combined).rstrip() + "\n", encoding="utf-8")
    print("  写入 threads/zh/README.md 与 threads/zh/all-threads.md")
    if missing:
        print(f"  ⚠️ 有 {missing} 段未找到译文（已保留英文）。")
    else:
        print("  ✅ 全部文本均有中文译文。")


if __name__ == "__main__":
    main()
