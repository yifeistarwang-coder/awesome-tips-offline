#!/usr/bin/env python3
"""Build a self-contained static website from the offline archive in this repo.

Design goals
------------
* **No CDN, no network, no JS framework.** The output works from ``file://``
  and from any static host, completely offline.
* **Bilingual.** English and Chinese are mirrored page-for-page, with a
  language switch that keeps you on the same article.
* **Generated from the Markdown sources**, so re-running the fetch/translate
  scripts and rebuilding the site is all it takes to refresh it.

Usage
-----
    python3 scripts/build_site.py                 # -> site/
    python3 scripts/build_site.py --out dist      # custom output dir
    python3 scripts/build_site.py --no-media      # skip linking threads/media
    python3 scripts/build_site.py --serve         # build, then serve on :8000

Output layout
-------------
    site/index.html                       landing page (bilingual)
    site/en/index.html                    English table of contents
    site/zh/index.html                    Chinese table of contents
    site/en/<category>/index.html         category page (all threads inline)
    site/en/<category>/<thread>.html      single thread (deep link target)
    site/en/articles/<name>.html          long-form repo articles
    site/en/slides/<deck>.html            localised guest-lecture decks
    site/gallery.html  site/zh/gallery.html
    site/assets/{style.css,app.js,search-index.js}
    site/media/...                        hardlinks to threads/media
"""

from __future__ import annotations

import argparse
import html as H
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_readmes import CATEGORY_ZH, LOCAL_ARTICLE_ZH, PPTX, slug  # noqa: E402
from fetch_x_threads import safe_name  # noqa: E402

ASSETS_SRC = Path(__file__).resolve().parent / "site_assets"
MEDIA_SRC = ROOT / "threads" / "media"
MARKER = ".awesome-tips-site"

CJK_RE = re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]")
VIDEO_EXT = {".mp4", ".mov", ".webm", ".m4v", ".ogv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".bmp"}
AUTOPLAY_PRELOAD = "none"              # clip bytes are only fetched once playback starts
GENERIC_ALT = {
    "image", "images", "img", "video", "gif",
    "图片", "配图", "视频", "gif 动画预览", "视频预览",
}

UI = {
    "en": {
        "site": "Awesome Tips",
        "tagline": "Research advice, archived for offline reading",
        "read": "Read",
        "search": "Search",
        "search_ph": "Search 66 threads, articles and slides…",
        "search_hint": "Type to search · ↑↓ to navigate · Enter to open · Esc to close",
        "no_results": "No matches. Try a shorter query.",
        "catalog": "Contents",
        "articles": "Long-form articles",
        "slides": "Lecture slides",
        "gallery": "Media gallery",
        "threads": "threads",
        "items": "items",
        "back_to": "Back to",
        "prev": "Previous",
        "next": "Next",
        "original": "Original post",
        "author_note": "Author's follow-up replies",
        "home": "Home",
        "theme": "Toggle light / dark theme",
        "menu": "Menu",
        "lang": "中文",
        "lang_title": "切换到中文",
        "media_note": "All images, GIFs and videos are stored locally in this archive.",
        "footer_note": "Generated from the Markdown archive in this repository — works fully offline, no CDN, no tracking.",
        "source": "Upstream project",
        "toc": "On this page",
        "all_threads": "All threads",
        "gallery_note": "Every image, GIF preview and video thumbnail in the archive.",
        "stat_threads": "threads",
        "stat_media": "media files",
        "stat_categories": "categories",
        "stat_langs": "languages",
        "open": "Open",
        "read_zh": "阅读中文版",
        "read_en": "Read in English",
        "browse": "Browse the archive",
        "replies": "replies",
    },
    "zh": {
        "site": "Awesome Tips",
        "tagline": "科研经验分享 · 完整离线归档",
        "read": "阅读",
        "search": "搜索",
        "search_ph": "搜索 66 条串文、长文与讲稿…",
        "search_hint": "输入即搜 · ↑↓ 选择 · Enter 打开 · Esc 关闭",
        "no_results": "没有匹配结果，试试更短的关键词。",
        "catalog": "目录",
        "articles": "长文整理",
        "slides": "讲稿幻灯片",
        "gallery": "图片与视频",
        "threads": "条",
        "items": "项",
        "back_to": "返回",
        "prev": "上一篇",
        "next": "下一篇",
        "original": "原帖",
        "author_note": "作者补充回复",
        "home": "首页",
        "theme": "切换深浅色主题",
        "menu": "菜单",
        "lang": "EN",
        "lang_title": "Switch to English",
        "media_note": "全部配图、GIF 与短视频均已本地化存储。",
        "footer_note": "由仓库中的 Markdown 归档自动生成 · 完全离线可用，无 CDN、无追踪。",
        "source": "上游项目",
        "toc": "本页目录",
        "all_threads": "全部串文",
        "gallery_note": "归档中的全部图片、GIF 预览与视频封面。",
        "stat_threads": "条串文",
        "stat_media": "个媒体文件",
        "stat_categories": "个分类",
        "stat_langs": "种语言",
        "open": "打开",
        "read_zh": "阅读中文版",
        "read_en": "Read in English",
        "browse": "浏览归档",
        "replies": "条",
    },
}


# --------------------------------------------------------------------------- #
# content model
# --------------------------------------------------------------------------- #
class Item:
    """One addressable piece of content (thread / article / deck / post)."""

    def __init__(self, kind: str, key: str, category: str | None = None):
        self.kind = kind
        self.key = key
        self.category = category
        self.data: dict[str, dict] = {}       # lang -> {title, body, src, url, date, count}
        self.slug = slug(key)
        self.headings: dict[str, list] = {}
        self.last_gallery: dict[str, list] = {}

    @property
    def title(self) -> dict[str, str]:
        return {lang: d["title"] for lang, d in self.data.items()}


META_RE = re.compile(
    r"^原帖：<(?P<url>https?://[^>]+)>"
    r"\s*(?:（[^）]*）)?"
    r"(?:\s*·\s*(?P<date>\d{4}-\d{2}-\d{2})\s*·\s*共\s*(?P<count>\d+)\s*条串文)?"
)


def read_lines(rel: str) -> list[str]:
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


def parse_sections(rel: str) -> tuple[str, list[str], list[dict]]:
    """Split a ``threads/<category>.md`` file into its ``## `` sections."""
    lines = read_lines(rel)
    page_title = ""
    intro: list[str] = []
    sections: list[dict] = []
    current: dict | None = None
    for line in lines:
        if line.startswith("# ") and not line.startswith("## "):
            page_title = line[2:].strip()
            continue
        if line.startswith("## "):
            if current:
                sections.append(current)
            current = {"title": line[3:].strip(), "meta": "", "body": []}
            continue
        if current is None:
            intro.append(line)
            continue
        if not current["meta"]:
            m = META_RE.match(line.strip())
            if m:
                current["meta"] = line.strip()
                current.update(
                    url=m.group("url"),
                    date=m.group("date") or "",
                    count=int(m.group("count") or 0),
                )
                continue
        current["body"].append(line)
    if current:
        sections.append(current)
    for s in sections:
        while s["body"] and not s["body"][0].strip():
            s["body"].pop(0)
        while s["body"] and not s["body"][-1].strip():
            s["body"].pop()
    return page_title, intro, sections


def load_threads() -> list[Item]:
    """Pair the English and Chinese thread files by original post URL."""
    en_index = []  # (category, file)
    for line in read_lines("threads/README.md"):
        m = re.match(r"^- \[(.+?)\]\((.+?\.md)\)", line)
        if m:
            en_index.append((m.group(1), "threads/" + m.group(2)))

    items: list[Item] = []
    by_url: dict[str, Item] = {}
    for category, rel in en_index:
        _, _, sections = parse_sections(rel)
        for s in sections:
            item = Item("thread", s.get("url") or slug(s["title"]), category)
            item.data["en"] = {
                "title": s["title"],
                "body": s["body"],
                "src": f"{rel}#{slug(s['title'])}",
                "url": s.get("url", ""),
                "date": s.get("date", ""),
                "count": s.get("count", 0),
            }
            items.append(item)
            if s.get("url"):
                by_url[s["url"]] = item

    # Chinese translations, matched on the original post URL
    for line in read_lines("threads/zh/README.md"):
        m = re.match(r"^- \[(.+?)\]\((.+?\.md)\)", line)
        if not m:
            continue
        rel = "threads/zh/" + m.group(2)
        _, _, sections = parse_sections(rel)
        for s in sections:
            item = by_url.get(s.get("url", ""))
            if item is None:
                print(f"  ! zh thread without EN counterpart: {s['title']}")
                continue
            item.data["zh"] = {
                "title": s["title"],
                "body": s["body"],
                "src": f"{rel}#{slug(s['title'])}",
                "url": s.get("url", ""),
                "date": s.get("date", ""),
                "count": s.get("count", 0),
            }
    for item in items:
        if "zh" not in item.data:
            print(f"  ! missing zh translation: {item.data['en']['title']}")
    return items


def load_bsky() -> Item:
    item = Item("bsky", "how-to-drive-your-research-forward", "Doing Research")
    for lang, rel, title in (
        ("en", "threads/bsky-how-to-drive-your-research-forward.md", None),
        ("zh", "threads/zh/bsky-how-to-drive-your-research-forward.md", None),
    ):
        lines = read_lines(rel)
        match = re.match(r"^#\s+(.+)$", lines[0])
        title = match.group(1).strip() if match else rel
        body = lines[1:]
        while body and not body[0].strip():
            body.pop(0)
        item.data[lang] = {
            "title": title,
            "body": body,
            "src": rel,
            "url": "https://bsky.app/profile/jbhuang0604.bsky.social/post/3lcbmsfnzm224",
            "date": "2024-12-01",
            "count": 0,
        }
    return item


def parse_article(rel: str) -> tuple[str, list[str]]:
    lines = read_lines(rel)
    title = rel
    start = 0
    if lines and lines[0].startswith("# "):
        title = lines[0][2:].strip()
        start = 1
    return title, lines[start:]


def load_articles() -> list[Item]:
    """Five English long-form articles + their Chinese digest sections."""
    zh_lines = read_lines("中文离线阅读版.md")
    zh_sections: dict[str, list[str]] = {}
    current = None
    for line in zh_lines:
        if line.startswith("## "):
            current = line[3:].strip()
            zh_sections[current] = []
            continue
        if current:
            zh_sections[current].append(line)

    items = []
    used = set()
    for rel, zh_title in LOCAL_ARTICLE_ZH.items():
        item = Item("article", Path(rel).stem)
        title, body = parse_article(rel)
        item.data["en"] = {
            "title": title,
            "body": body,
            "src": rel,
            "url": "",
            "date": "",
            "count": 0,
        }
        zh_body = zh_sections.get(zh_title)
        if zh_body is not None:
            zh_body = list(zh_body)
            while zh_body and not zh_body[0].strip():
                zh_body.pop(0)
            while zh_body and not zh_body[-1].strip():
                zh_body.pop()
            item.data["zh"] = {
                "title": zh_title,
                "body": zh_body,
                "src": f"中文离线阅读版.md#{slug(zh_title)}",
                "url": "",
                "date": "",
                "count": 0,
            }
            used.add(zh_title)
        items.append(item)

    for zh_title, body in zh_sections.items():
        if zh_title in used:
            continue
        body = list(body)
        while body and not body[0].strip():
            body.pop(0)
        while body and not body[-1].strip():
            body.pop()
        item = Item("article", "scope")
        item.data["zh"] = {
            "title": zh_title,
            "body": body,
            "src": f"中文离线阅读版.md#{slug(zh_title)}",
            "url": "",
            "date": "",
            "count": 0,
        }
        items.append(item)
    return items


DECK_FILES = {
    "ninja": (
        "2022_11_18 Guest lecture, Harvard University",
        "https://www.dropbox.com/s/2s0wt4uxv9vk3gb/2022_11_18%20Guest_lecture_Harvard.pptx?dl=0",
    ),
    "faculty": (
        "2022_12_05 Academic Job Workshop",
        "https://www.dropbox.com/s/avkflol8mx99c7e/2022_12_05%20Academic%20Job%20workshop.pptx?dl=0",
    ),
}


def load_slides() -> list[Item]:
    items = []
    for deck, (label, source) in DECK_FILES.items():
        item = Item("slide", deck)
        for lang in ("en", "zh"):
            rel = f"threads/slides/{deck}.{lang}.md"
            title, body = parse_article(rel)
            item.data[lang] = {
                "title": title,
                "body": body,
                "src": rel,
                "url": source,
                "date": "",
                "count": 0,
            }
        items.append(item)
    return items


# --------------------------------------------------------------------------- #
# markdown -> html
# --------------------------------------------------------------------------- #
CODE_RE = re.compile(r"`([^`\n]+)`")
AUTOLINK_RE = re.compile(r"<(https?://[^>\s]+)>")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(\s*([^)\s]+?)(?:\s+\"[^\"]*\")?\s*\)")
LINKED_IMAGE_RE = re.compile(
    r"\[!\[([^\]]*)\]\(\s*([^)\s]+?)(?:\s+\"[^\"]*\")?\s*\)\]"
    r"\(\s*([^)\s]+?)(?:\s+\"[^\"]*\")?\s*\)"
)
LINK_RE = re.compile(r"\[([^\]]*)\]\(\s*([^)\s]+?)(?:\s+\"[^\"]*\")?\s*\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.S)
ITALIC_RE = re.compile(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])")
STRIKE_RE = re.compile(r"~~(.+?)~~")
MATH_RE = re.compile(r"\$([^$\n]+)\$")
MEDIA_LINE_RE = re.compile(
    r"^(?:!\[[^\]]*\]\([^)\s]+\)"
    r"|\[!\[[^\]]*\]\([^)\s]+\)\]\([^)\s]+\)"
    r"|▶\s*\[[^\]]*\]\([^)\s]+\))$"
)


def is_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text))


def human_size(n: int) -> str:
    """Compact byte size, kept for build-time diagnostics."""
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.0f} MB"
    return f"{max(1, round(n / 1024))} KB"


class Renderer:
    """A deliberately small Markdown subset renderer.

    The archive only uses headings, blockquotes, lists, emphasis, links,
    images and autolinks -- plus X-style video previews, which get turned into
    real ``<video>`` players.
    """

    def __init__(self, prefix: str, resolve, lang: str = "en"):
        self.prefix = prefix          # relative path from the page to the site root
        self.resolve = resolve        # (href) -> site-relative url | external url | None
        self.ui = UI.get(lang, UI["en"])
        self.headings: list[tuple[int, str, str]] = []
        self.emitted: set[str] = set()
        self.gallery: list[dict] = []
        self.stash: list[str] = []    # shared across nested inline() calls

    # -- inline ---------------------------------------------------------- #
    def keep(self, html: str) -> str:
        self.stash.append(html)
        return f"\x00{len(self.stash) - 1}\x00"

    def inline(self, text: str) -> str:
        keep = self.keep

        # [![preview](x.jpg)](x.mp4) -> inline video player
        def linked_image(m: re.Match) -> str:
            alt, preview, href = m.group(1), m.group(2), m.group(3)
            target = self.resolve(href)
            if target is None:
                return keep("")
            if Path(href.split("#")[0]).suffix.lower() in VIDEO_EXT:
                return keep(self.figure(target, alt, href, video_src=target))
            return keep(f'<a href="{H.escape(target, quote=True)}">{self.inline(f"![{alt}]({preview})")}</a>')

        text = LINKED_IMAGE_RE.sub(linked_image, text)

        # standalone images
        def image(m: re.Match) -> str:
            alt, src = m.group(1), m.group(2)
            url = self.resolve(src)
            if url is None:
                return keep("")
            return keep(self.figure(url, alt, src))

        text = IMAGE_RE.sub(image, text)

        def link(m: re.Match) -> str:
            label, href = m.group(1), m.group(2)
            if "\x00" in label:      # label already rendered as a block
                return keep(label)
            if Path(href.split("#")[0]).suffix.lower() in VIDEO_EXT:
                video = self.resolve(href)
                if video and href not in self.emitted:
                    return keep(self.figure(video, label, href, video_src=video))
            url = self.resolve(href)
            if url is None:
                return keep(self.inline(label))
            external = url.startswith(("http://", "https://", "mailto:"))
            attrs = ' target="_blank" rel="noopener"' if external else ""
            return keep(f'<a href="{H.escape(url, quote=True)}"{attrs}>{self.inline(label)}</a>')

        text = LINK_RE.sub(link, text)
        text = AUTOLINK_RE.sub(
            lambda m: keep(f'<a href="{H.escape(m.group(1), quote=True)}" target="_blank" rel="noopener">{H.escape(m.group(1))}</a>'),
            text,
        )
        text = CODE_RE.sub(lambda m: keep(f"<code>{H.escape(m.group(1))}</code>"), text)
        text = MATH_RE.sub(lambda m: keep(f'<code class="math">{H.escape(m.group(1))}</code>'), text)

        text = H.escape(text, quote=False)
        text = BOLD_RE.sub(r"<strong>\1</strong>", text)
        text = ITALIC_RE.sub(r"<em>\1</em>", text)
        text = STRIKE_RE.sub(r"<del>\1</del>", text)

        def restore(m: re.Match) -> str:
            idx = int(m.group(1))
            return self.stash[idx] if idx < len(self.stash) else ""

        return re.sub(r"\x00(\d+)\x00", restore, text)

    # -- media ----------------------------------------------------------- #
    def figure(self, url: str, alt: str, raw_href: str, video_src: str | None = None) -> str:
        ext = Path(raw_href).suffix.lower()
        caption = "" if (alt or "").strip().lower() in GENERIC_ALT else (alt or "").strip()
        cap = f'<figcaption>{self.inline(caption)}</figcaption>' if caption else ""

        if video_src or ext in VIDEO_EXT:
            src = video_src or url
            poster = ""
            base = url.rsplit(".", 1)[0]
            for candidate in (f"{base}.jpg", f"{base}.png", f"{base}.jpeg"):
                if self.media_exists(candidate):
                    poster = f' poster="{H.escape(candidate, quote=True)}"'
                    break
            self.emitted.add(raw_href)
            size = self.media_size(url)
            # ``autoplay`` is what Safari/EU-style autoplay policies actually honour for
            # muted clips: a programmatic play() on a page that never ran a declarative
            # autoplay is rejected with NotAllowedError. Browsers defer autoplay for
            # clips that are off-screen, and app.js still pauses/resumes on scroll and
            # honours the autoplay toggle.
            return (
                f'<figure class="video"><div class="video-wrap">'
                f'<video autoplay muted loop playsinline controls preload="none"{poster} data-size="{size}">'
                f'<source src="{H.escape(src, quote=True)}">'
                f"</video></div>{cap}</figure>"
            )
        if ext in IMAGE_EXT or not ext:
            root = url[len(self.prefix):] if url.startswith(self.prefix) else url
            self.gallery.append({"src": url, "root": root, "alt": caption or alt, "kind": "image"})
            return (
                f'<figure><a class="zoom" href="{H.escape(url, quote=True)}">'
                f'<img loading="lazy" decoding="async" src="{H.escape(url, quote=True)}"'
                f' alt="{H.escape(alt or "", quote=True)}"></a>{cap}</figure>'
            )
        return f'<p><a href="{H.escape(url, quote=True)}">{H.escape(raw_href)}</a></p>'

    def media_exists(self, url: str) -> bool:
        rel = url[len(self.prefix):] if url.startswith(self.prefix) else url
        return (ROOT / "threads" / rel) .exists()

    def media_size(self, url: str) -> int:
        rel = url[len(self.prefix):] if url.startswith(self.prefix) else url
        path = ROOT / "threads" / rel
        try:
            return path.stat().st_size
        except OSError:
            return 0

    # -- blocks ---------------------------------------------------------- #
    def render(self, lines: list[str]) -> str:
        out: list[str] = []
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
                out.append("<hr>")
                i += 1
                continue

            heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading:
                level = len(heading.group(1))
                text = heading.group(2).strip()
                hid = slug(text)
                base = hid
                k = 2
                while any(h[1] == hid for h in self.headings):
                    hid = f"{base}-{k}"
                    k += 1
                self.headings.append((level, text, hid))
                cls = ""
                if re.fullmatch(r"(作者补充回复|Author'?s? (follow-up )?repl(y|ies))", text, re.I):
                    cls = ' class="note-heading"'
                out.append(
                    f'<h{level} id="{H.escape(hid, quote=True)}"{cls}>'
                    f'<a class="anchor" href="#{H.escape(hid, quote=True)}" aria-label="anchor">#</a>'
                    f"{self.inline(text)}</h{level}>"
                )
                i += 1
                continue

            if stripped.startswith(">"):
                buf = []
                while i < n and lines[i].strip().startswith(">"):
                    buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                    i += 1
                out.append(f'<blockquote>{self.render(buf)}</blockquote>')
                continue

            if re.match(r"^\s*[-*+]\s+", line):
                html, i = self.list(lines, i, ordered=False)
                out.append(html)
                continue
            if re.match(r"^\s*\d+[.)]\s+", line):
                html, i = self.list(lines, i, ordered=True)
                out.append(html)
                continue

            if self.is_redundant(stripped):
                i += 1
                continue
            if MEDIA_LINE_RE.match(stripped):
                out.append(self.inline(stripped))
                i += 1
                continue

            buf = []
            while i < n and lines[i].strip() and not self.starts_block(lines[i]):
                buf.append(lines[i].strip())
                i += 1
            if not buf:  # safety valve
                buf = [lines[i].strip()]
                i += 1
            out.append("<p>" + "<br>".join(self.inline(x) for x in buf if not self.is_redundant(x)) + "</p>")

        return "\n".join(x for x in out if x and x not in ("<p></p>",))

    def is_redundant(self, line: str) -> bool:
        """Drop the ``▶ [video](x.mp4)`` line that repeats a player already emitted."""
        m = re.fullmatch(r"\s*▶\s*\[([^\]]*)\]\(\s*([^)\s]+?)\s*\)\s*", line)
        if not m:
            return False
        return m.group(2) in self.emitted

    @staticmethod
    def starts_block(line: str) -> bool:
        stripped = line.strip()
        return bool(
            re.match(r"^\s*(#{1,6}\s|>|[-*+]\s|\d+[.)]\s)", line)
            or re.fullmatch(r"\s*(-{3,}|\*{3,}|_{3,})\s*", line)
            or MEDIA_LINE_RE.match(stripped)
            or re.fullmatch(r"\s*▶\s*\[[^\]]*\]\([^)\s]+\)\s*", line)
        )

    def list(self, lines: list[str], i: int, ordered: bool) -> tuple[str, int]:
        pattern = r"^(\s*)(\d+[.)]|[-*+])\s+(.*)$"
        items: list[str] = []
        n = len(lines)
        while i < n:
            m = re.match(pattern, lines[i])
            if not m:
                break
            indent, _, text = m.groups()
            sub: list[str] = []
            i += 1
            while i < n and lines[i].strip() and not re.match(pattern, lines[i]):
                if self.starts_block(lines[i]) and not lines[i].startswith("  "):
                    break
                sub.append(lines[i].strip())
                i += 1
            body = self.inline(text)
            if sub:
                body += "<br>" + "<br>".join(self.inline(x) for x in sub if not self.is_redundant(x))
            items.append(f"<li>{body}</li>")
        tag = "ol" if ordered else "ul"
        return f"<{tag}>" + "".join(items) + f"</{tag}>", i


def md_to_text(lines: list[str]) -> str:
    """Plain text used for the search index."""
    out = []
    for line in lines:
        s = line.strip()
        if not s or s.startswith(("![", "▶")):
            continue
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"^#{1,6}\s*", "", s)
        s = re.sub(r"^>\s?", "", s)
        s = re.sub(r"[*`_]", "", s)
        out.append(s)
    return re.sub(r"\s+", " ", " ".join(out)).strip()


# --------------------------------------------------------------------------- #
# site building
# --------------------------------------------------------------------------- #
class Site:
    def __init__(self, out: Path, with_media: bool = True):
        self.out = out
        self.with_media = with_media
        self.pages: list[tuple[str, str]] = []       # (site-relative url, html)
        self.catalog: dict[str, list[dict]] = {"en": [], "zh": []}
        self.search: list[dict] = []
        self.md_links: dict[tuple[str, str], str] = {}
        self.media_count = 0

    # -- helpers --------------------------------------------------------- #
    def prefix_for(self, url: str) -> str:
        depth = url.count("/")
        return "../" * depth

    def resolve_factory(self, src_rel: str, prefix: str):
        base = (ROOT / src_rel.split("#")[0]).parent

        def resolve(href: str):
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*:", href) or href.startswith("//"):
                return href
            if href.startswith("#") or not href:
                return href or None
            path, _, frag = href.partition("#")
            if not path:
                return "#" + frag
            target = (base / unquote(path)).resolve()
            try:
                rel = target.relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                return href
            if rel.startswith("threads/media/"):
                site = rel[len("threads/"):]
                return prefix + site
            if rel in MD_LINKS_GLOBAL or (rel, unquote(frag)) in self.md_links:
                key = (rel, unquote(frag))
                site = self.md_links.get(key) or MD_LINKS_GLOBAL.get(rel)
                if site:
                    return prefix + site
            return None

        return resolve

    def render_item(self, item: Item, lang: str, prefix: str) -> str:
        data = item.data[lang]
        renderer = Renderer(prefix, self.resolve_factory(data["src"], prefix), lang)
        body = renderer.render(data["body"])
        item.headings[lang] = renderer.headings
        item.last_gallery[lang] = renderer.gallery
        return body

    # -- pages ----------------------------------------------------------- #
    def write(self, url: str, html: str) -> None:
        self.pages.append((url, html))

    def build(self) -> None:
        self.threads = load_threads()
        self.bsky = load_bsky()
        self.articles = load_articles()
        self.slides = load_slides()
        self.register_urls()
        self.render_content()
        self.render_indexes()
        self.render_home()
        self.render_gallery()
        self.emit()

    def register_urls(self) -> None:
        cats = []
        seen = []
        for item in self.threads:
            if item.category not in seen:
                seen.append(item.category)
        self.categories = seen

        for cat in self.categories:
            cat_slug = safe_name(cat)
            en_src = f"threads/{cat_slug}.md"
            zh_src = f"threads/zh/{cat_slug}.md"
            self.md_links[(en_src, "")] = f"en/{cat_slug}/index.html"
            self.md_links[(zh_src, "")] = f"zh/{cat_slug}/index.html"
            for item in self.threads:
                if item.category != cat:
                    continue
                item.slug = slug(item.data["en"]["title"]) or item.key
                self.md_links[(item.data["en"]["src"].split("#")[0], item.data["en"]["src"].split("#")[1])] = (
                    f"en/{cat_slug}/{item.slug}.html"
                )
                self.md_links[("threads/zh/" + safe_name(cat) + ".md", slug(item.data["zh"]["title"]))] = (
                    f"zh/{cat_slug}/{item.slug}.html"
                )
                self.md_links[(item.data["zh"]["src"].split("#")[0], item.data["zh"]["src"].split("#")[1])] = (
                    f"zh/{cat_slug}/{item.slug}.html"
                )

        self.md_links[("threads/bsky-how-to-drive-your-research-forward.md", "")] = (
            "en/doing-research/how-to-drive-your-research-forward.html"
        )
        self.md_links[("threads/zh/bsky-how-to-drive-your-research-forward.md", "")] = (
            "zh/doing-research/how-to-drive-your-research-forward.html"
        )
        self.md_links[("threads/README.md", "")] = "en/index.html"
        self.md_links[("threads/zh/README.md", "")] = "zh/index.html"
        self.md_links[("threads/all-threads.md", "")] = "en/index.html"
        self.md_links[("threads/zh/all-threads.md", "")] = "zh/index.html"
        self.md_links[("README.md", "")] = "index.html"
        self.md_links[("README-CN.md", "")] = "zh/index.html"
        self.md_links[("中文离线阅读版.md", "")] = "zh/index.html"

        for item in self.articles:
            for lang, url in (("en", f"en/articles/{item.key}.html"), ("zh", f"zh/articles/{item.key}.html")):
                data = item.data.get(lang)
                if not data:
                    continue
                src, _, frag = data["src"].partition("#")
                self.md_links[(src, frag)] = url
                if not frag:
                    self.md_links[(src, "")] = url

        for item in self.slides:
            for lang in ("en", "zh"):
                src = item.data[lang]["src"]
                self.md_links[(src, "")] = f"{lang}/slides/{item.key}.html"

        # English article <-> Chinese digest cross links
        for item in self.articles:
            if "en" in item.data and "zh" in item.data:
                self.md_links[(item.data["en"]["src"], "")] = f"en/articles/{item.key}.html"
                src, _, frag = item.data["zh"]["src"].partition("#")
                self.md_links[(src, frag)] = f"zh/articles/{item.key}.html"

    def render_content(self) -> None:
        cat_slug_cache = {c: safe_name(c) for c in self.categories}
        self.rendered: dict[tuple[str, str], str] = {}

        for lang in ("en", "zh"):
            for item in self.threads + [self.bsky]:
                if lang not in item.data:
                    continue
                cat = item.category if item.kind == "thread" else "Doing Research"
                url = f"{lang}/{safe_name(cat)}/{item.slug}.html"
                prefix = self.prefix_for(url)
                self.rendered[(lang, item.key)] = self.render_item(item, lang, prefix)
                cat_url = f"{lang}/{safe_name(cat)}/"
                self.catalog[lang].append(
                    {
                        "kind": item.kind,
                        "slug": item.slug,
                        "cat": cat,
                        "url": url,
                        **self.entry_meta(item, lang),
                    }
                )
                self.search.append(self.search_entry(item, lang, url))

        for item in self.articles:
            for lang in ("en", "zh"):
                if lang not in item.data:
                    continue
                url = f"{lang}/articles/{item.key}.html"
                prefix = self.prefix_for(url)
                self.rendered[(lang, "article:" + item.key)] = self.render_item(item, lang, prefix)
                self.search.append(self.search_entry(item, lang, url))

        for item in self.slides:
            for lang in ("en", "zh"):
                url = f"{lang}/slides/{item.key}.html"
                prefix = self.prefix_for(url)
                self.rendered[(lang, "slide:" + item.key)] = self.render_item(item, lang, prefix)
                self.search.append(self.search_entry(item, lang, url))

    def entry_meta(self, item: Item, lang: str) -> dict:
        d = item.data[lang]
        return {"title": d["title"], "date": d["date"], "count": d["count"], "source": d["url"]}

    def search_entry(self, item: Item, lang: str, url: str) -> dict:
        d = item.data[lang]
        text = md_to_text(d["body"])
        return {
            "t": d["title"],
            "l": lang,
            "k": item.kind,
            "c": CATEGORY_ZH.get(item.category, "") if lang == "zh" else (item.category or ""),
            "u": url,
            "d": d.get("date", ""),
            "x": text[:1400],
        }

    # -- rendering of chrome --------------------------------------------- #
    def nav_html(self, lang: str, current_url: str, current_cat: str | None) -> str:
        t = UI[lang]
        parts = [f'<a class="nav-home" href="{self.prefix_for(current_url)}index.html">{t["home"]}</a>']
        parts.append(f'<a class="nav-home" href="{self.prefix_for(current_url)}{lang}/index.html">{t["catalog"]}</a>')
        for cat in self.categories:
            cat_slug = safe_name(cat)
            items = [i for i in self.threads if i.category == cat and lang in i.data]
            if not items:
                continue
            title = CATEGORY_ZH.get(cat, cat) if lang == "zh" else cat
            active = " active" if cat == current_cat else ""
            open_ = " open" if cat == current_cat else ""
            links = []
            for it in items:
                url = f"{lang}/{cat_slug}/{it.slug}.html"
                cls = ' class="current"' if current_url.endswith(f"{cat_slug}/{it.slug}.html") else ""
                links.append(f'<li><a href="{self.prefix_for(current_url)}{url}"{cls}>{H.escape(it.data[lang]["title"])}</a></li>')
            parts.append(
                f'<details class="nav-cat{active}"{open_}><summary><span>{H.escape(title)}</span>'
                f'<span class="badge">{len(items)}</span></summary><ul>{"" .join(links)}</ul></details>'
            )
        return "".join(parts)

    def page(
        self,
        *,
        lang: str,
        url: str,
        title: str,
        body: str,
        desc: str = "",
        current_cat: str | None = None,
        alt_url: str | None = None,
        body_class: str = "",
        with_sidebar: bool = True,
    ) -> str:
        t = UI[lang]
        prefix = self.prefix_for(url)
        full_title = f"{title} · {t['site']}" if title else t["site"]
        alt = alt_url or "index.html"
        sidebar = (
            f'<aside class="sidebar" id="sidebar"><nav class="nav">{self.nav_html(lang, url, current_cat)}</nav></aside>'
            if with_sidebar
            else ""
        )
        return f"""<!doctype html>
<html lang="{'zh-Hans' if lang == 'zh' else 'en'}" data-lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{H.escape(full_title)}</title>
<meta name="description" content="{H.escape(desc or t['tagline'])}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💡</text></svg>">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body class="{body_class}">
<a class="skip" href="#main">{t['read']}</a>
<header class="topbar">
{f'  <button class="icon-btn nav-toggle" aria-label="{t["menu"]}" aria-controls="sidebar">☰</button>' + chr(10) if with_sidebar else ''}  <a class="brand" href="{prefix}index.html"><span class="brand-mark">💡</span><span class="brand-text">{t['site']}</span></a>
  <div class="topbar-spacer"></div>
  <button class="search-btn" type="button" data-search-open><span class="search-ico">⌕</span><span class="search-label">{t['search']}</span><kbd>/</kbd></button>
  <a class="icon-btn lang-btn" href="{prefix}{alt}" title="{t['lang_title']}">{t['lang']}</a>
  <button class="icon-btn theme-btn" type="button" data-theme-toggle title="{t['theme']}" aria-label="{t['theme']}"><span class="theme-glyph">◐</span></button>
</header>
<div class="progress" id="progress"></div>
<div class="layout{' no-sidebar' if not with_sidebar else ''}">
{sidebar}
<main id="main" class="content">{body}</main>
</div>
<footer class="footer">
  <div><strong>{t['site']}</strong> — {t['footer_note']}</div>
  <div>{t['source']}：<a href="https://github.com/jbhuang0604/awesome-tips" target="_blank" rel="noopener">jbhuang0604/awesome-tips</a> · MIT License</div>
</footer>
<div class="overlay" id="search-overlay" hidden>
  <div class="search-panel" role="dialog" aria-modal="true" aria-label="{t['search']}">
    <div class="search-head">
      <span class="search-ico">⌕</span>
      <input id="search-input" type="search" autocomplete="off" spellcheck="false" placeholder="{t['search_ph']}">
      <button class="icon-btn" type="button" data-search-close aria-label="close">✕</button>
    </div>
    <div class="search-meta" id="search-meta">{t['search_hint']}</div>
    <div class="search-results" id="search-results"></div>
  </div>
</div>
<div class="lightbox" id="lightbox" hidden><img alt=""><button class="icon-btn" type="button" data-lightbox-close aria-label="close">✕</button></div>
<script>window.__ROOT__={json.dumps(prefix)};window.__LANG__={json.dumps(lang)};window.__UI__={json.dumps(t, ensure_ascii=False)};</script>
<script src="{prefix}assets/search-index.js"></script>
<script src="{prefix}assets/app.js"></script>
</body>
</html>
"""

    # -- content pages ---------------------------------------------------- #
    def render_indexes(self) -> None:
        t = UI
        for lang in ("en", "zh"):
            cat_blocks = []
            for cat in self.categories:
                items = [i for i in self.threads if i.category == cat][:]
                if cat == self.bsky.category and lang in self.bsky.data:
                    items.append(self.bsky)
                cat_slug = safe_name(cat)
                title = CATEGORY_ZH.get(cat, cat) if lang == "zh" else cat
                cards = []
                for it in items:
                    d = it.data[lang]
                    meta = " · ".join(x for x in (d.get("date"), (f"{d['count']} {t[lang]['replies']}" if d.get("count") else "")) if x)
                    cards.append(
                        f'<a class="card" href="{self.prefix_for(lang + "/")}{lang}/{cat_slug}/{it.slug}.html">'
                        f'<span class="card-title">{H.escape(d["title"])}</span>'
                        f'<span class="card-meta">{H.escape(meta)}</span></a>'
                    )
                cat_blocks.append(
                    f'<section class="cat-block"><h2 id="{cat_slug}">{H.escape(title)}'
                    f'<span class="badge">{len(items)}</span></h2><div class="cards">{"".join(cards)}</div></section>'
                )
            body = (
                f'<div class="hero small"><h1>{t[lang]["catalog"]}</h1>'
                f'<p class="lede">{t[lang]["tagline"]}</p>'
                f'<p class="hero-links">'
                f'<a class="btn" href="{self.prefix_for(lang + "/")}{lang}/index.html">{t[lang]["all_threads"]}</a>'
                f'<a class="btn ghost" href="{self.prefix_for(lang + "/")}gallery.html">{t[lang]["gallery"]}</a>'
                f'<a class="btn ghost" href="{self.prefix_for(lang + "/")}{lang}/articles/index.html">{t[lang]["articles"]}</a>'
                f'<a class="btn ghost" href="{self.prefix_for(lang + "/")}{lang}/slides/index.html">{t[lang]["slides"]}</a>'
                f"</p></div>"
                + "".join(cat_blocks)
            )
            self.write(
                f"{lang}/index.html",
                self.page(
                    lang=lang,
                    url=f"{lang}/index.html",
                    title=t[lang]["catalog"],
                    body=body,
                    alt_url=("zh/index.html" if lang == "en" else "en/index.html"),
                    with_sidebar=False,
                ),
            )

            # articles index
            cards = []
            prefix = self.prefix_for(f"{lang}/articles/index.html")
            for item in self.articles:
                if lang not in item.data:
                    continue
                d = item.data[lang]
                cards.append(
                    f'<a class="card wide" href="{prefix}{lang}/articles/{item.key}.html">'
                    f'<span class="card-title">{H.escape(d["title"])}</span>'
                    f'<span class="card-meta">{H.escape(md_to_text(d["body"])[:150])}…</span></a>'
                )
            self.write(
                f"{lang}/articles/index.html",
                self.page(
                    lang=lang,
                    url=f"{lang}/articles/index.html",
                    title=t[lang]["articles"],
                    body=f'<h1>{t[lang]["articles"]}</h1><div class="cards">{"".join(cards)}</div>',
                    alt_url=f"{'zh' if lang == 'en' else 'en'}/articles/index.html",
                ),
            )

            # slides index
            cards = []
            prefix = self.prefix_for(f"{lang}/slides/index.html")
            for item in self.slides:
                d = item.data[lang]
                cards.append(
                    f'<a class="card wide" href="{prefix}{lang}/slides/{item.key}.html">'
                    f'<span class="card-title">{H.escape(d["title"])}</span>'
                    f'<span class="card-meta">{H.escape(DECK_FILES[item.key][0])}</span></a>'
                )
            self.write(
                f"{lang}/slides/index.html",
                self.page(
                    lang=lang,
                    url=f"{lang}/slides/index.html",
                    title=t[lang]["slides"],
                    body=f'<h1>{t[lang]["slides"]}</h1><div class="cards">{"".join(cards)}</div>',
                    alt_url=f"{'zh' if lang == 'en' else 'en'}/slides/index.html",
                ),
            )

        # thread pages + category pages
        for cat in self.categories:
            cat_slug = safe_name(cat)
            for lang in ("en", "zh"):
                items = [i for i in self.threads if i.category == cat and lang in i.data]
                if cat == self.bsky.category and lang in self.bsky.data:
                    items = items + [self.bsky]
                title = CATEGORY_ZH.get(cat, cat) if lang == "zh" else cat
                for pos, item in enumerate(items):
                    d = item.data[lang]
                    meta = " · ".join(
                        x for x in (d.get("date"), (f"{d['count']} {t[lang]['replies']}" if d.get("count") else "")) if x
                    )
                    src = (
                        f'<a href="{H.escape(d["url"], quote=True)}" target="_blank" rel="noopener">'
                        f'{t[lang]["original"]} ↗</a>'
                        if d.get("url")
                        else ""
                    )
                    prev_item = items[pos - 1] if pos > 0 else None
                    next_item = items[pos + 1] if pos + 1 < len(items) else None
                    page_url = f"{lang}/{cat_slug}/{item.slug}.html"
                    prefix = self.prefix_for(page_url)
                    nav = ['<nav class="pager">']
                    nav.append(
                        f'<a class="pager-prev" href="{prefix}{lang}/{cat_slug}/{prev_item.slug}.html">'
                        f'<span class="pager-label">← {t[lang]["prev"]}</span><span>{H.escape(prev_item.data[lang]["title"])}</span></a>'
                        if prev_item
                        else '<span class="pager-prev empty"></span>'
                    )
                    nav.append(
                        f'<a class="pager-next" href="{prefix}{lang}/{cat_slug}/{next_item.slug}.html">'
                        f'<span class="pager-label">{t[lang]["next"]} →</span><span>{H.escape(next_item.data[lang]["title"])}</span></a>'
                        if next_item
                        else '<span class="pager-next empty"></span>'
                    )
                    nav.append("</nav>")
                    toc = self.toc_html(item.headings[lang], level_min=3)
                    body = (
                        f'<article class="thread">'
                        f'<header class="thread-head">'
                        f'<p class="crumb"><a href="{prefix}{lang}/{cat_slug}/index.html">← {H.escape(title)}</a></p>'
                        f"<h1>{H.escape(d['title'])}</h1>"
                        f'<p class="thread-meta">{H.escape(meta)}{" · " if meta and src else ""}{src}</p>'
                        f"</header>{toc}{self.rendered[(lang, item.key)]}"
                        f"{''.join(nav)}</article>"
                    )
                    self.write(
                        page_url,
                        self.page(
                            lang=lang,
                            url=f"{lang}/{cat_slug}/{item.slug}.html",
                            title=d["title"],
                            body=body,
                            desc=md_to_text(d["body"])[:180],
                            current_cat=cat,
                            alt_url=f"{'zh' if lang == 'en' else 'en'}/{cat_slug}/{item.slug}.html",
                            body_class="thread-page",
                        ),
                    )

                # category page: every thread inline, anchor-linked
                cat_url = f"{lang}/{cat_slug}/index.html"
                prefix = self.prefix_for(cat_url)
                sections = []
                for item in items:
                    d = item.data[lang]
                    meta = " · ".join(
                        x for x in (d.get("date"), (f"{d['count']} {t[lang]['replies']}" if d.get("count") else "")) if x
                    )
                    sections.append(
                        f'<section class="thread-inline" id="{H.escape(slug(d["title"]), quote=True)}">'
                        f'<h2><a href="{prefix}{lang}/{cat_slug}/{item.slug}.html">{H.escape(d["title"])}</a>'
                        f'{" " + str(d["count"]) + " " + t[lang]["replies"] if d.get("count") else ""}</h2>'
                        f'<p class="thread-meta">{H.escape(meta)}</p>{self.rendered[(lang, item.key)]}</section>'
                    )
                listing = "".join(
                    f'<li><a href="#{H.escape(slug(it.data[lang]["title"]), quote=True)}">{H.escape(it.data[lang]["title"])}</a></li>'
                    for it in items
                )
                other = "zh" if lang == "en" else "en"
                body = (
                    f'<header class="thread-head"><h1>{H.escape(title)}</h1>'
                    f'<p class="thread-meta">{len(items)} {t[lang]["threads"]}</p></header>'
                    f'<nav class="toc list"><h2>{t[lang]["toc"]}</h2><ol class="toc-list">{listing}</ol></nav>'
                    + "".join(sections)
                    + f'<nav class="pager"><a class="pager-next" href="{prefix}{lang}/index.html">'
                    f'<span class="pager-label">{t[lang]["back_to"]}</span><span>{t[lang]["catalog"]}</span></a></nav>'
                )
                self.write(
                    cat_url,
                    self.page(
                        lang=lang,
                        url=f"{lang}/{cat_slug}/index.html",
                        title=title,
                        body=body,
                        current_cat=cat,
                        alt_url=f"{other}/{cat_slug}/index.html",
                        body_class="category-page",
                    ),
                )

        # article + slide pages
        for item in self.articles:
            for lang in ("en", "zh"):
                if lang not in item.data:
                    continue
                d = item.data[lang]
                other = "zh" if lang == "en" else "en"
                page_url = f"{lang}/articles/{item.key}.html"
                prefix = self.prefix_for(page_url)
                body = (
                    f'<article class="thread"><header class="thread-head">'
                    f'<p class="crumb"><a href="{prefix}{lang}/articles/index.html">← {t[lang]["articles"]}</a></p>'
                    f'<h1>{H.escape(d["title"])}</h1></header>'
                    f'{self.toc_html(item.headings[lang], level_min=2)}{self.rendered[(lang, "article:" + item.key)]}'
                    f"</article>"
                )
                self.write(
                    page_url,
                    self.page(
                        lang=lang,
                        url=page_url,
                        title=d["title"],
                        body=body,
                        desc=md_to_text(d["body"])[:180],
                        alt_url=self.alt_for(item, lang, "articles"),
                        body_class="article-page",
                    ),
                )

        for item in self.slides:
            for lang in ("en", "zh"):
                d = item.data[lang]
                other = "zh" if lang == "en" else "en"
                page_url = f"{lang}/slides/{item.key}.html"
                prefix = self.prefix_for(page_url)
                body = (
                    f'<article class="thread deck"><header class="thread-head">'
                    f'<p class="crumb"><a href="{prefix}{lang}/slides/index.html">← {t[lang]["slides"]}</a></p>'
                    f'<h1>{H.escape(d["title"])}</h1>'
                    f'<p class="thread-meta"><a href="{H.escape(DECK_FILES[item.key][1], quote=True)}" target="_blank" rel="noopener">'
                    f'{t[lang]["original"]} ↗</a></p></header>'
                    f'{self.rendered[(lang, "slide:" + item.key)]}</article>'
                )
                self.write(
                    page_url,
                    self.page(
                        lang=lang,
                        url=page_url,
                        title=d["title"],
                        body=body,
                        desc=DECK_FILES[item.key][0],
                        alt_url=self.alt_for(item, lang, "slides"),
                        body_class="slide-page",
                    ),
                )

    def alt_for(self, item: Item, lang: str, folder: str) -> str:
        other = "zh" if lang == "en" else "en"
        if other in item.data:
            return f"{other}/{folder}/{item.key}.html"
        return f"{other}/{folder}/index.html"

    def toc_html(self, headings, level_min: int = 3) -> str:
        heads = [h for h in headings if h[0] >= level_min]
        if len(heads) < 2:
            return ""
        lis = "".join(
            f'<li><a href="#{H.escape(hid, quote=True)}">{H.escape(text)}</a></li>' for _, text, hid in heads
        )
        return f'<nav class="toc inline"><h2>{UI["en"]["toc"]}</h2><ol class="toc-list">{lis}</ol></nav>'

    def render_home(self) -> None:
        stats = [
            (len(self.threads), "threads / 条串文"),
            (media_count(), "media files / 个媒体文件"),
            (len(self.categories), "categories / 个分类"),
            (2, "languages / 种语言"),
        ]
        stat_html = "".join(
            f'<div class="stat"><span class="stat-num">{value}</span><span class="stat-label">'
            f'{H.escape(label.split(" / ")[0])}<small>{H.escape(label.split(" / ")[1])}</small></span></div>'
            for value, label in stats
        )
        cards = []
        for cat in self.categories:
            items = [i for i in self.threads if i.category == cat]
            slug_ = safe_name(cat)
            cards.append(
                f'<div class="cat-card"><h3>{H.escape(CATEGORY_ZH.get(cat, cat))} <small>{H.escape(cat)}</small></h3>'
                f'<p class="cat-count">{len(items)} threads</p>'
                f'<p class="cat-links"><a href="en/{slug_}/index.html">English</a><a href="zh/{slug_}/index.html">中文</a></p></div>'
            )
        body = f"""
<div class="hero">
  <p class="eyebrow">Jia-Bin Huang · research advice archive</p>
  <h1>Awesome Tips</h1>
  <p class="lede">A curated collection of research, writing, presentation and career tips —<br>
  完整离线归档：66 条 X/Twitter 串文、长文、讲稿与全部配图/GIF/短视频。</p>
  <p class="hero-links">
    <a class="btn" href="zh/index.html">阅读中文版</a>
    <a class="btn ghost" href="en/index.html">Read in English</a>
    <button class="btn ghost" type="button" data-search-open>搜索 / Search</button>
  </p>
</div>
<div class="stats">{stat_html}</div>
<section><h2>Contents <small>目录</small></h2><div class="cat-grid">{''.join(cards)}</div></section>
<section><h2>More <small>更多</small></h2>
<div class="cards">
  <a class="card wide" href="en/articles/index.html"><span class="card-title">Long-form articles <small>长文整理</small></span><span class="card-meta">5 articles · steady progress, related work, paper writing, mentors, cold emails</span></a>
  <a class="card wide" href="en/slides/index.html"><span class="card-title">Lecture slides <small>讲稿幻灯片</small></span><span class="card-meta">Harvard guest lecture · academic job workshop (PPTX localised)</span></a>
  <a class="card wide" href="gallery.html"><span class="card-title">Media gallery <small>图片与视频</small></span><span class="card-meta">Every image, GIF preview and video thumbnail — stored locally</span></a>
</div></section>
<p class="note">Generated from the Markdown archive in this repository. Works fully offline: no CDN, no network requests, no tracking.</p>
"""
        self.write(
            "index.html",
            self.page(lang="en", url="index.html", title="", body=body, with_sidebar=False, alt_url="zh/index.html", body_class="home"),
        )

    def render_gallery(self) -> None:
        for lang, url in (("en", "gallery.html"), ("zh", "zh/gallery.html")):
            t = UI[lang]
            prefix = self.prefix_for(url)
            groups = []
            for cat in self.categories:
                title = CATEGORY_ZH.get(cat, cat) if lang == "zh" else cat
                blocks = []
                entries = [i for i in self.threads if i.category == cat and lang in i.data]
                if lang == "en":
                    entries += [self.bsky]
                for item in entries:
                    gallery = item.last_gallery.get(lang, [])
                    if not gallery:
                        continue
                    seen = set()
                    thumbs = []
                    for g in gallery:
                        if g["root"] in seen:
                            continue
                        seen.add(g["root"])
                        src = prefix + g["root"]
                        thumbs.append(
                            f'<a class="gallery-item" href="{H.escape(src, quote=True)}" '
                            f'data-caption="{H.escape(g["alt"] or "", quote=True)}">'
                            f'<img loading="lazy" decoding="async" src="{H.escape(src, quote=True)}" '
                            f'alt="{H.escape(g["alt"] or "", quote=True)}"></a>'
                        )
                    blocks.append(
                        f'<section class="gallery-thread"><h3><a href="{prefix}{lang}/{safe_name(cat)}/{item.slug}.html">'
                        f'{H.escape(item.data[lang]["title"])}</a></h3><div class="gallery-grid">{"".join(thumbs)}</div></section>'
                    )
                if blocks:
                    groups.append(
                        f'<section class="gallery-cat"><h2 id="{safe_name(cat)}">{H.escape(title)}</h2>{"".join(blocks)}</section>'
                    )

            # articles + lecture slides
            extras = [
                (t["articles"], self.articles, "{lang}/articles/{key}.html"),
                (t["slides"], self.slides, "{lang}/slides/{key}.html"),
            ]
            for label, collection, url_tpl in extras:
                blocks = []
                for entry in collection:
                    if lang not in entry.data:
                        continue
                    gallery = entry.last_gallery.get(lang, [])
                    if not gallery:
                        continue
                    seen, thumbs = set(), []
                    for g in gallery:
                        if g["root"] in seen:
                            continue
                        seen.add(g["root"])
                        src = prefix + g["root"]
                        thumbs.append(
                            f'<a class="gallery-item" href="{H.escape(src, quote=True)}" '
                            f'data-caption="{H.escape(g["alt"] or "", quote=True)}">'
                            f'<img loading="lazy" decoding="async" src="{H.escape(src, quote=True)}" '
                            f'alt="{H.escape(g["alt"] or "", quote=True)}"></a>'
                        )
                    target = url_tpl.format(lang=lang, key=entry.key)
                    blocks.append(
                        f'<section class="gallery-thread"><h3><a href="{prefix}{target}">'
                        f'{H.escape(entry.data[lang]["title"])}</a></h3><div class="gallery-grid">{"".join(thumbs)}</div></section>'
                    )
                if blocks:
                    groups.append(
                        f'<section class="gallery-cat"><h2 id="{safe_name(label)}">{H.escape(label)}</h2>{"".join(blocks)}</section>'
                    )
            body = (
                f'<header class="thread-head"><h1>{t["gallery"]}</h1>'
                f'<p class="thread-meta">{t["gallery_note"]}</p></header>'
                f'<div class="gallery-search"><input type="search" id="gallery-filter" placeholder="{t["search"]}…"></div>'
                + "".join(groups)
            )
            self.write(
                url,
                self.page(
                    lang=lang,
                    url=url,
                    title=t["gallery"],
                    body=body,
                    alt_url=("zh/gallery.html" if lang == "en" else "gallery.html"),
                    body_class="gallery-page",
                    with_sidebar=False,
                ),
            )

    # -- emit ------------------------------------------------------------- #
    def emit(self) -> None:
        if self.out.exists():
            if (self.out / MARKER).exists():
                shutil.rmtree(self.out)
            else:
                print(f"refusing to delete {self.out} (no {MARKER} marker)")
                raise SystemExit(1)
        (self.out / "assets").mkdir(parents=True)

        for url, html in self.pages:
            path = self.out / url
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(html, encoding="utf-8")

        for name in ("style.css", "app.js"):
            shutil.copy2(ASSETS_SRC / name, self.out / "assets" / name)

        index = json.dumps(self.search, ensure_ascii=False, separators=(",", ":"))
        (self.out / "assets" / "search-index.js").write_text(
            "window.__SEARCH__=" + index + ";\n", encoding="utf-8"
        )
        (self.out / MARKER).write_text("generated by scripts/build_site.py\n", encoding="utf-8")

        if self.with_media:
            self.link_media()

        total = sum((self.out / u).stat().st_size for u, _ in self.pages)
        print(f"  pages      : {len(self.pages)}")
        print(f"  html size  : {total / 1024:.0f} KB")
        print(f"  search idx : {len(self.search)} entries, {len(index) / 1024:.0f} KB")
        print(f"  media      : {self.media_count} files linked")

    def link_media(self) -> None:
        target = self.out / "media"
        if target.exists():
            return
        if not MEDIA_SRC.exists():
            print("  ! threads/media missing, skipping")
            return
        target.mkdir()
        count = 0
        fallback = 0
        for src in MEDIA_SRC.rglob("*"):
            rel = src.relative_to(MEDIA_SRC)
            dst = target / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
                continue
            try:
                os.link(src, dst)
            except OSError:
                shutil.copy2(src, dst)
                fallback += 1
            count += 1
        self.media_count = count
        if fallback:
            print(f"  ! {fallback} files copied (hardlink unavailable)")


def media_count() -> int:
    if not MEDIA_SRC.exists():
        return 0
    return sum(1 for p in MEDIA_SRC.rglob("*") if p.is_file())


MD_LINKS_GLOBAL: dict[str, str] = {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="site", help="output directory (default: site)")
    parser.add_argument("--no-media", action="store_true", help="do not link threads/media into the site")
    parser.add_argument("--serve", action="store_true", help="serve the site on http://localhost:8000 after building")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    out = (ROOT / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out)
    print(f"building site -> {out}")
    site = Site(out, with_media=not args.no_media)
    site.build()
    print("done.")

    if args.serve:
        import functools
        import http.server
        import socketserver

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
        with socketserver.TCPServer(("", args.port), handler) as httpd:
            print(f"serving http://localhost:{args.port}/  (Ctrl-C to stop)")
            httpd.serve_forever()


if __name__ == "__main__":
    main()
