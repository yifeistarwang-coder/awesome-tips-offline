#!/usr/bin/env python3
"""Render the two guest-lecture/workshop slide decks (Dropbox PPTX links in
README.md) as local English and Chinese markdown, with slide images extracted
from the original pptx files.

Sources kept in the repo:
    threads/slides/<deck>/slides.json   — per-slide text/images/notes
    threads/slides/translations.json    — Chinese translation per slide
    threads/media/slides/<deck>/*       — slide images (>=15KB)

Outputs:
    threads/slides/<deck>.en.md / .zh.md
    threads/slides/README.md
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLIDES = ROOT / "threads" / "slides"

DECKS = {
    "ninja": {
        "en": "The Road to Becoming an AI Ninja",
        "zh": "成为 AI 忍者之路（哈佛客座讲座）",
        "source": "https://www.dropbox.com/s/2s0wt4uxv9vk3gb/2022_11_18%20Guest_lecture_Harvard.pptx?dl=0",
    },
    "faculty": {
        "en": "Fantastic Faculty Jobs and How to Get Them",
        "zh": "梦幻教职——以及如何拿到它们（学术求职工作坊）",
        "source": "https://www.dropbox.com/s/avkflol8mx99c7e/2022_12_05%20Academic%20Job%20workshop.pptx?dl=0",
    },
}


def load_slides(deck: str) -> list[dict]:
    return json.loads((SLIDES / deck / "slides.json").read_text(encoding="utf-8"))


def render(deck: str, lang: str, trans: dict[str, str]) -> str:
    info = DECKS[deck]
    slides = load_slides(deck)
    title = info[lang]
    lines = [
        f"# {title}",
        "",
        f"讲者：Jia-Bin Huang · 原始文件：[{Path(info['source'].split('/')[-1]).name}]({info['source']})",
        "（PPTX 已下载并逐页提取为本地 Markdown 与图片，无需再访问原链接。）",
        "",
    ]
    web = "（图片保留原版幻灯片内容）" if lang == "zh" else ""
    for slide in slides:
        n = slide["slide"]
        heading = f"第 {n} 页" if lang == "zh" else f"Slide {n}"
        lines.append(f"## {heading}")
        lines.append("")
        if lang == "zh":
            text = trans.get(f"{deck}:{n}", "")
            if text:
                for line in text.split("\n"):
                    lines.append(f"- {line}" if line else "")
                lines.append("")
        else:
            for text in slide["texts"]:
                lines.append(f"- {text}")
            if slide["texts"]:
                lines.append("")
        for image in slide["images"]:
            path = ROOT / "threads" / "media" / "slides" / deck / image
            if path.exists():
                lines.append(f"![{heading}]({'../media/slides/' + deck + '/' + image})")
                lines.append("")
        notes = [t for t in slide.get("notes", []) if t.strip()]
        if notes and lang == "en":
            lines.append("> 备注：" + " ".join(notes))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    trans = json.loads((SLIDES / "translations.json").read_text(encoding="utf-8"))
    index = [
        "# 讲稿/工作坊幻灯片（PPTX 本地化版）",
        "",
        "README.md 中两个 Dropbox PPTX 链接已下载并逐页转换为 Markdown（文字 + 幻灯片图片），",
        "无需访问 Dropbox 即可阅读。",
        "",
    ]
    for deck, info in DECKS.items():
        for lang in ("en", "zh"):
            out = SLIDES / f"{deck}.{lang}.md"
            out.write_text(render(deck, lang, trans), encoding="utf-8")
            print(f"  写入 threads/slides/{out.name}")
        index.append(f"- {info['zh']}")
        index.append(f"  - [中文版]({deck}.zh.md) · [English]({deck}.en.md) · 原始链接：<{info['source']}>")
    index.append("")
    (SLIDES / "README.md").write_text("\n".join(index), encoding="utf-8")
    print("  写入 threads/slides/README.md")


if __name__ == "__main__":
    main()
