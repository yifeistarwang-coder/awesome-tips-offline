#!/usr/bin/env python3
"""Mirror the media that the long-form articles still link to over the network.

The five root articles came from the upstream repository and point at GitHub's
``user-images.githubusercontent.com`` (and one ``media.giphy.com`` GIF) with bare
URLs on their own line. They play inline on GitHub, but they are the last thing
in the archive that still needs a network.

This script downloads each one into ``threads/media/articles/``, extracts a
poster frame for videos, and rewrites the bare URL into the same
``[![preview](poster)](clip)`` form the thread archive uses -- which the site
builder turns into a real player.

Idempotent: already-downloaded files are reused, and rewritten lines are
recognised and skipped.

Usage
-----
    python3 scripts/fetch_article_media.py [--report]
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "threads" / "media" / "articles"
REL = "threads/media/articles"

BARE_RE = re.compile(
    r"^(?P<url>https://(?:user-images\.githubusercontent\.com|media\.giphy\.com)/[^\s)]+"
    r"\.(?:mp4|gif|webp|png|jpe?g))\s*$",
    re.M,
)
MD_IMG_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<url>https://(?:user-images\.githubusercontent\.com|media\.giphy\.com)/"
    r"[^)\s]+\.(?:mp4|gif|webp|png|jpe?g))\)"
)
DONE_RE = re.compile(r"^\[!\[[^\]]*\]\(" + re.escape(REL) + r"/[^)]+\)\]\(" + re.escape(REL) + r"/[^)]+\)\s*$", re.M)
VIDEO_EXT = {".mp4", ".webm", ".mov"}
UA = {"User-Agent": "awesome-tips-archive/1.0 (+https://github.com/yifeistarwang-coder/awesome-tips-offline)"}


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  cached   {dest.name} ({dest.stat().st_size / 1e3:.0f}KB)")
        return True
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  FAILED   {url}  ({exc})")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"  fetched  {dest.name} ({len(data) / 1e3:.0f}KB)")
    return True


def poster(clip: Path) -> Path | None:
    """Still frame next to the clip, so the site shows something before playback."""
    img = clip.with_suffix(".jpg")
    if img.exists():
        return img
    run = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-frames:v", "1", "-q:v", "4", "-update", "1", str(img)],
        capture_output=True, text=True,
    )
    return img if run.returncode == 0 and img.exists() else None


def gif_to_clip(gif: Path) -> Path | None:
    """The archive keeps animation as H.264 -- far smaller than an animated GIF."""
    clip = gif.with_suffix(".mp4")
    if clip.exists():
        return clip
    run = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", str(gif), "-movflags", "+faststart", "-pix_fmt", "yuv420p",
         "-crf", "28", "-preset", "slow", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos", "-an", str(clip)],
        capture_output=True, text=True,
    )
    if run.returncode == 0 and clip.exists():
        gif.unlink(missing_ok=True)
        return clip
    clip.unlink(missing_ok=True)
    return None


def to_local(url: str, alt: str = "") -> str | None:
    """Download one remote asset and return the replacement Markdown."""
    name = url.rsplit("/", 1)[-1]
    dest = DEST / name
    if not download(url, dest):
        return None

    clip = dest
    if dest.suffix.lower() == ".gif":
        converted = gif_to_clip(dest)
        if converted:
            clip = converted
        else:
            print(f"  ! keeping {dest.name} as GIF (conversion failed)")

    if clip.suffix.lower() in VIDEO_EXT:
        img = poster(clip)
        label = "GIF 动画预览" if url.endswith(".gif") else "视频预览"
        if img:
            return f"[![{label}]({REL}/{img.name})]({REL}/{clip.name})"
        return f"[▶ {label}（点击播放）]({REL}/{clip.name})"
    return f"![{alt or '配图'}]({REL}/{clip.name})"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="list what would be mirrored")
    args = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")

    total = 0
    for md in sorted(ROOT.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        found = BARE_RE.findall(text)
        images = [m for m in MD_IMG_RE.finditer(text)]
        already = len(DONE_RE.findall(text))
        if not found and not images and not already:
            continue
        print(f"{md.name}: {len(found)} bare URLs, {len(images)} image links, {already} already local")

        for url in found:
            if args.report:
                print(f"  would fetch {url.rsplit('/', 1)[-1]}")
                continue
            replacement = to_local(url)
            if replacement:
                text = text.replace(url, replacement, 1)
                total += 1

        for m in reversed(list(MD_IMG_RE.finditer(text))):
            if args.report:
                print(f"  would fetch {m.group('url').rsplit('/', 1)[-1]}")
                continue
            replacement = to_local(m.group("url"), m.group("alt"))
            if replacement:
                text = text[: m.start()] + replacement + text[m.end():]
                total += 1

        if not args.report:
            md.write_text(text, encoding="utf-8")

    if args.report:
        return
    print(f"\nmirrored {total} files into {REL}/")
    print("next: python3 scripts/build_readmes.py && rm -rf site && python3 scripts/build_site.py")


if __name__ == "__main__":
    main()
