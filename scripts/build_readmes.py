#!/usr/bin/env python3
"""Rewrite README.md (English) and build README-CN.md so that every bullet
maps to locally archived content — no X/Dropbox links required.

The item list is parsed once from the original README (with X/Dropbox links)
and cached in scripts/readme_index.json; subsequent runs build the READMEs from
that cache.

Local targets:
  * X threads      -> threads/<category>.md#<anchor>          (EN)
                      threads/zh/<category>.md#<anchor>       (CN)
  * repo articles  -> <name>.md                               (EN)
                      中文离线阅读版.md#<anchor>               (CN)
  * Dropbox slides -> threads/slides/<deck>.en.md / .zh.md
  * Bluesky post   -> threads/bsky-*.md / threads/zh/bsky-*.md
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_x_threads import parse_readme, safe_name  # noqa: E402

README = ROOT / "README.md"
README_CN = ROOT / "README-CN.md"
INDEX = Path(__file__).resolve().parent / "readme_index.json"
ZH_TRANS = ROOT / "threads" / "zh" / "_out"

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

LOCAL_ARTICLE_ZH = {
    "steady-progress.md": "研究推进",
    "working-with-mentor.md": "与导师协作",
    "related-work.md": "论文相关工作",
    "paper-writing.md": "论文写作：让读者少做匹配",
    "cold-emails.md": "写冷邮件",
}

PPTX = {
    "2s0wt4uxv9vk3gb": ("ninja", "成为 AI 忍者之路（哈佛客座讲座）"),
    "avkflol8mx99c7e": ("faculty", "梦幻教职——以及如何拿到它们（学术求职工作坊）"),
}


def slug(text: str) -> str:
    """GitHub-style heading anchor."""
    text = text.strip().lower()
    text = re.sub(r"[^\w\u4e00-\u9fff \-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def parse_original_readme() -> list[tuple[str, list[dict]]]:
    sections: list[tuple[str, list[dict]]] = []
    current = None
    for line in README.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^###\s+(.+)$", line)
        if heading:
            current = heading.group(1).strip()
            sections.append((current, []))
            continue
        link = re.match(r"^- \[([^]]+)\]\(([^)]+)\)\s*$", line)
        if not link or current is None:
            continue
        title, url = link.group(1).strip(), link.group(2)
        item: dict = {"title": title, "url": url}
        m = re.match(r"https?://(?:twitter|x)\.com/([^/]+)/status/(\d+)", url)
        if m:
            item.update(type="x", author=m.group(1), id=m.group(2))
        elif url.endswith(".md"):
            item.update(type="local", path=url)
        elif "dropbox.com" in url and url.endswith(".pptx?dl=0"):
            key = url.split("/s/")[1].split("/")[0]
            item.update(type="pptx", key=key)
        elif "bsky.app" in url:
            item.update(type="bsky")
        else:
            item.update(type="other")
        sections[-1][1].append(item)
    return sections


def load_index() -> list[tuple[str, list[dict]]]:
    if INDEX.exists():
        raw = json.loads(INDEX.read_text(encoding="utf-8"))
        return [(c, items) for c, items in raw]
    sections = parse_original_readme()
    INDEX.write_text(json.dumps(sections, ensure_ascii=False, indent=1), encoding="utf-8")
    return sections


def load_zh_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    for path in sorted(ZH_TRANS.glob("batch-*.json")):
        for key, value in json.loads(path.read_text(encoding="utf-8")).items():
            if key.startswith("title:"):
                titles[key.split(":", 1)[1]] = value.strip()
    return titles


def en_target(item: dict, owner_categories: dict[str, str]) -> str:
    t = item["type"]
    if t == "x":
        category = owner_categories[item["id"]]
        return f"threads/{safe_name(category)}.md#{slug(item['title'])}"
    if t == "local":
        return item["path"]
    if t == "pptx":
        deck = PPTX[item["key"]][0]
        return f"threads/slides/{deck}.en.md"
    if t == "bsky":
        return "threads/bsky-how-to-drive-your-research-forward.md"
    return item["url"]


def zh_target(item: dict, owner_categories: dict[str, str], zh_titles: dict[str, str]) -> str:
    t = item["type"]
    if t == "x":
        category = owner_categories[item["id"]]
        zh_title = zh_titles.get(item["id"]) or item["title"]
        return f"threads/zh/{safe_name(category)}.md#{slug(zh_title)}"
    if t == "local":
        zh_title = LOCAL_ARTICLE_ZH.get(item["path"], item["title"])
        return f"中文离线阅读版.md#{slug(zh_title)}"
    if t == "pptx":
        deck = PPTX[item["key"]][0]
        return f"threads/slides/{deck}.zh.md"
    if t == "bsky":
        return "threads/zh/bsky-how-to-drive-your-research-forward.md"
    return item["url"]


def build_en(sections: list[tuple[str, list[dict]]], owner: dict, zh_titles: dict) -> str:
    lines = [
        "# Awesome Tips [![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)",
        "",
        "A curated list of tips on various topics. **Every entry now links to locally archived, offline-readable content.**",
        "",
        "- 中文版（Chinese）：[README-CN.md](README-CN.md)",
        "- X/Twitter 完整串文归档：[threads/README.md](threads/README.md)（66 条 · 配图/GIF 本地化）",
        "- 仓库正文中文整理：[中文离线阅读版.md](中文离线阅读版.md)",
        "- 讲稿/幻灯片（Dropbox PPTX 已本地化）：[threads/slides/README.md](threads/slides/README.md)",
        "- **静态网站**：`python3 scripts/build_site.py` 生成 `site/`（双语、离线搜索、可 `--serve` 预览）",
        "",
        "## What is in here",
        "",
        "| Path | Contents |",
        "| --- | --- |",
        "| [`threads/`](threads/README.md) | Full text of all 66 X/Twitter threads, one file per category. Every image, GIF and clip is stored locally in `threads/media/`; `t.co` links are expanded. |",
        "| [`threads/zh/`](threads/zh/README.md) | Chinese translation of every thread. |",
        "| [`threads/slides/`](threads/slides/README.md) | The two Dropbox decks (Harvard guest lecture, academic job workshop), extracted slide by slide. |",
        "| Root `*.md` | The five long-form articles. [`中文离线阅读版.md`](中文离线阅读版.md) is their Chinese digest. |",
        "| [`scripts/`](scripts) | The pipeline that produced all of the above. |",
        "",
        "## Reading it",
        "",
        "**Static site (recommended).** Bilingual, full-text search (`/` or `Cmd-K`), dark mode, clips autoplay while on screen:",
        "",
        "```bash",
        "python3 scripts/build_site.py            # writes site/",
        "python3 scripts/build_site.py --serve    # ... and serves http://localhost:8000",
        "```",
        "",
        "It needs no network at all — no CDN, no web fonts, no tracking — so `site/index.html` also opens straight from `file://`.",
        "",
        "**Plain Markdown.** Everything is readable as-is: start at [`threads/README.md`](threads/README.md) (English) or [`threads/zh/README.md`](threads/zh/README.md) (中文).",
        "",
        "## Rebuilding the archive",
        "",
        "```bash",
        "python3 scripts/fetch_x_threads.py         # refresh threads + media from X (uses your browser session)",
        "python3 scripts/prepare_zh_translation.py  # cut the text into translation batches",
        "python3 scripts/render_x_threads_zh.py     # render the Chinese archive",
        "python3 scripts/build_readmes.py           # regenerate README.md / README-CN.md from scripts/readme_index.json",
        "python3 scripts/build_site.py              # regenerate the website",
        "```",
        "",
        "## Notes",
        "",
        "- `threads/media/` holds 966 files (~251 MB). `site/media/` is hard-linked to it, so building the site costs almost no extra disk — but weigh that size before pushing the repository anywhere.",
        "- `site/` is generated output and is gitignored; only the sources are tracked.",
        "- The clips are muted H.264 conversions of the original GIFs. Autoplay stays the browser's decision: clips start once they are on screen, pause when they scroll away, and stay still when the OS asks for reduced motion.",
        "",
        "## Contents",
        "",
    ]
    seen_x: set[str] = set()
    first_title: dict[str, str] = {}
    for category, items in sections:
        if not items:
            continue
        lines.append(f"### {category}")
        for item in items:
            if item["type"] == "x" and item["id"] in seen_x:
                dup_cat = owner[item["id"]]
                target = f"threads/{safe_name(dup_cat)}.md#{slug(first_title[item['id']])}"
                lines.append(f"- [{item['title']}]({target})（已收录于 {dup_cat}）")
                continue
            target = en_target(item, owner)
            if item["type"] == "x":
                seen_x.add(item["id"])
                first_title[item["id"]] = item["title"]
            lines.append(f"- [{item['title']}]({target})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_zh(sections: list[tuple[str, list[dict]]], owner: dict, zh_titles: dict) -> str:
    lines = [
        "# Awesome Tips（中文版）",
        "",
        "本文件把 README 中每一条内容都映射到**本地中文 Markdown**，无需访问 X / Dropbox。",
        "",
        "- 英文版：[README.md](README.md)",
        "- 中文完整串文归档（66 条）：[threads/zh/README.md](threads/zh/README.md)",
        "- 仓库五篇正文的中文整理：[中文离线阅读版.md](中文离线阅读版.md)",
        "- 讲稿/幻灯片中文版：[threads/slides/README.md](threads/slides/README.md)",
        "- **静态网站**：`python3 scripts/build_site.py` 生成 `site/`（中英双语、离线搜索、可 `--serve` 预览）",
        "",
        "## 仓库里有什么",
        "",
        "| 路径 | 内容 |",
        "| --- | --- |",
        "| [`threads/`](threads/README.md) | 66 条 X/Twitter 串文全文，按分类分文件。全部配图、GIF 与短视频已存到本地 `threads/media/`，`t.co` 短链已展开。 |",
        "| [`threads/zh/`](threads/zh/README.md) | 每条串文的中文翻译。 |",
        "| [`threads/slides/`](threads/slides/README.md) | 两份 Dropbox 讲稿（哈佛客座讲座、学术求职工作坊），已逐页提取。 |",
        "| 根目录 `*.md` | 五篇长文，其中 [`中文离线阅读版.md`](中文离线阅读版.md) 是它们的中文整理。 |",
        "| [`scripts/`](scripts) | 生成以上全部内容的流水线。 |",
        "",
        "## 怎么读",
        "",
        "**静态网站（推荐）**：中英双语、全文搜索（`/` 或 `Cmd-K`）、深浅色主题、动画在屏幕上时自动播放。",
        "",
        "```bash",
        "python3 scripts/build_site.py            # 生成 site/",
        "python3 scripts/build_site.py --serve    # 生成并起 http://localhost:8000",
        "```",
        "",
        "完全不依赖网络——没有 CDN、没有 web 字体、没有统计——所以 `site/index.html` 直接双击（`file://`）也能打开。",
        "",
        "**纯 Markdown**：所有内容本来就能直接读，入口是 [`threads/zh/README.md`](threads/zh/README.md)（中文）或 [`threads/README.md`](threads/README.md)（英文）。",
        "",
        "## 重新生成",
        "",
        "```bash",
        "python3 scripts/fetch_x_threads.py         # 用本机浏览器登录态刷新串文与媒体",
        "python3 scripts/prepare_zh_translation.py  # 切分翻译批次",
        "python3 scripts/render_x_threads_zh.py     # 渲染中文归档",
        "python3 scripts/build_readmes.py           # 由 scripts/readme_index.json 重建 README.md / README-CN.md",
        "python3 scripts/build_site.py              # 重建网站",
        "```",
        "",
        "## 说明",
        "",
        "- `threads/media/` 有 966 个文件、约 251 MB；`site/media/` 是指向它的硬链接，所以建站几乎不额外占用磁盘——但推送到任何远端之前请先掂量这个体积。",
        "- `site/` 是生成产物，已在 `.gitignore` 中忽略，仓库里只跟踪源文件。",
        "- 短视频是原 GIF 的无声 H.264 转码。是否自动播放始终由浏览器决定：进入屏幕才开始、划走就暂停，系统要求「减弱动态效果」时保持静止。",
        "",
        "## 目录",
        "",
    ]
    seen_x: set[str] = set()
    first_zh_title: dict[str, str] = {}
    for category, items in sections:
        if not items:
            continue
        lines.append(f"### {CATEGORY_ZH.get(category, category)}")
        for item in items:
            if item["type"] == "x" and item["id"] in seen_x:
                dup_cat = owner[item["id"]]
                zh_first = first_zh_title[item["id"]]
                target = f"threads/zh/{safe_name(dup_cat)}.md#{slug(zh_first)}"
                item_zh = zh_titles.get(item["id"]) or item["title"]
                lines.append(f"- [{item_zh}]({target})（已收录于「{CATEGORY_ZH.get(dup_cat, dup_cat)}」）")
                continue
            target = zh_target(item, owner, zh_titles)
            if item["type"] == "x":
                title = zh_titles.get(item["id"]) or item["title"]
                seen_x.add(item["id"])
                first_zh_title[item["id"]] = title
            elif item["type"] == "local":
                title = LOCAL_ARTICLE_ZH.get(item["path"], item["title"])
            elif item["type"] == "pptx":
                title = PPTX[item["key"]][1]
            elif item["type"] == "bsky":
                title = "如何推动你的研究向前进（Bluesky）"
            else:
                title = item["title"]
            lines.append(f"- [{title}]({target})")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    sections = load_index()
    zh_titles = load_zh_titles()

    # The category file a thread is archived in = the first category listing it
    # (parse_readme dedupes globally in the same order).
    owner: dict[str, str] = {}
    for category, items in sections:
        for item in items:
            if item["type"] == "x" and item["id"] not in owner:
                owner[item["id"]] = category

    README.write_text(build_en(sections, owner, zh_titles), encoding="utf-8")
    README_CN.write_text(build_zh(sections, owner, zh_titles), encoding="utf-8")
    n = sum(len(items) for _, items in sections)
    print(f"  写入 README.md 与 README-CN.md（{n} 个条目，{len(owner)} 条 X 线程）")


if __name__ == "__main__":
    main()
