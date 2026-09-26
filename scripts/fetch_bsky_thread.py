#!/usr/bin/env python3
"""Archive a Bluesky thread: the author's own chain, plus its embeds.

Bluesky has a public AppView API, so unlike the X archive this needs no browser
session at all:

    resolveHandle(handle)      -> did
    getPostThread(uri, depth)  -> the whole tree

Only posts by the thread author are kept (same rule as the X archive: other
people's replies are not part of the thread), following the self-reply chain
downwards. External embeds (Tenor GIFs) and image embeds are mirrored into
``threads/media/bsky/``; GIFs become H.264 clips with a poster frame, which is
the convention used everywhere else in this archive.

Usage
-----
    python3 scripts/fetch_bsky_thread.py                       # the default post
    python3 scripts/fetch_bsky_thread.py <post-url-or-at-uri>  # any public post
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "threads" / "media" / "bsky"
API = "https://public.api.bsky.app/xrpc"
UA = {"User-Agent": "awesome-tips-archive/1.0"}

DEFAULT = ("jbhuang0604.bsky.social", "3lcbmsfnzm224")
OUT_EN = ROOT / "threads" / "bsky-how-to-drive-your-research-forward.md"


def api(method: str, **params) -> dict:
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    req = urllib.request.Request(f"{API}/{method}?{query}", headers=UA)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read())


def download(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size:
        print(f"  cached  {dest.name}")
        return True
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"  FAILED  {url} ({exc})")
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"  fetched {dest.name} ({len(data) / 1e3:.0f}KB)")
    return True


def embed_markdown(embed: dict | None, stem: str, rel: str) -> str:
    """Turn one embed into the archive's [![preview](poster)](clip) form."""
    if not embed:
        return ""
    kind = embed.get("$type", "").split(".")[-1]

    urls: list[tuple[str, str]] = []          # (url, alt)
    if kind == "external":
        ext = embed["external"]
        alt = (ext.get("description") or ext.get("title") or "").removeprefix("ALT: ").strip()
        urls.append((ext.get("uri", ""), alt))
    elif kind == "images":
        for n, img in enumerate(embed.get("images", []), 1):
            urls.append((img.get("fullsize") or img.get("thumb", ""), img.get("alt", "")))
    elif kind == "video":
        urls.append((embed.get("video", {}).get("ref", {}).get("$link", ""), embed.get("alt", "")))

    out = []
    for n, (url, alt) in enumerate(urls, 1):
        if not url or not url.startswith("http"):
            continue
        suffix = Path(url.split("?")[0]).suffix.lower() or ".gif"
        name = f"{stem}-{n}{suffix}"
        dest = MEDIA / name
        # a converted GIF no longer exists on disk, so check the clip instead
        already = dest.with_suffix(".mp4").exists() if suffix in (".gif", ".webp") else dest.exists()
        if already:
            print(f"  cached  {name}")
            dest.unlink(missing_ok=True)      # drop a stale source GIF from an earlier run
        elif not download(url, dest):
            continue
        if suffix in (".gif", ".webp"):
            clip = dest.with_suffix(".mp4")
            if not clip.exists():
                run = subprocess.run(
                    ["ffmpeg", "-v", "error", "-y", "-i", str(dest), "-movflags", "+faststart",
                     "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "slow",
                     "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos", "-an", str(clip)],
                    capture_output=True, text=True,
                )
                if run.returncode != 0:
                    clip.unlink(missing_ok=True)
                    out.append(f"![{alt}]({rel}/{name})")
                    continue
                dest.unlink(missing_ok=True)
                thumb = embed.get("external", {}).get("thumb")
            poster = clip.with_suffix(".jpg")
            if not poster.exists():
                subprocess.run(
                    ["ffmpeg", "-v", "error", "-y", "-i", str(clip), "-frames:v", "1", "-q:v", "4",
                     "-update", "1", str(poster)],
                    capture_output=True, text=True,
                )
            label = alt.strip() or "GIF"
            out.append(f"[![{label}]({rel}/{poster.name})]({rel}/{clip.name})")
        else:
            out.append(f"![{alt.strip() or 'image'}]({rel}/{name})")
    return "\n\n".join(out)


def author_chain(thread: dict, did: str) -> list[dict]:
    """Walk the self-reply chain: the author's posts in order."""
    chain: list[dict] = []
    node = thread
    while node and node.get("post"):
        post = node["post"]
        if post["author"]["did"] != did:
            break
        chain.append(post)
        replies = node.get("replies") or []
        # the author's next post is whichever reply is also from the author
        node = next((r for r in replies if (r.get("post") or {}).get("author", {}).get("did") == did), None)
    return chain


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("post", nargs="?", help="post URL or at:// URI (default: the archived one)")
    ap.add_argument("--out", type=Path, default=OUT_EN, help="Markdown file to write")
    ap.add_argument("--title", default="How to Drive Your Research Forward")
    args = ap.parse_args()

    if args.post and args.post.startswith("at://"):
        uri = args.post
        handle = None
    else:
        m = re.search(r"profile/([^/]+)/post/(\w+)", args.post or "")
        handle, rkey = (m.group(1), m.group(2)) if m else DEFAULT
        did = api("com.atproto.identity.resolveHandle", handle=handle)["did"]
        uri = f"at://{did}/app.bsky.feed.post/{rkey}"

    data = api("app.bsky.feed.getPostThread", uri=uri, depth="10", parentHeight="0")
    thread = data.get("thread") or {}
    if not thread.get("post"):
        sys.exit(f"could not load thread: {json.dumps(data)[:200]}")

    root = thread["post"]
    did = root["author"]["did"]
    chain = author_chain(thread, did)
    handle = root["author"]["handle"]
    created = root["record"]["createdAt"][:10]
    others = len(thread.get("replies") or []) - (1 if len(chain) > 1 else 0)

    print(f"@{handle} · {created} · {len(chain)} author posts")
    rel = "media/bsky"
    body = []
    for n, post in enumerate(chain, 1):
        text = post["record"]["text"].strip()
        piece = text
        media = embed_markdown(post["record"].get("embed"), f"post{n:02d}", rel)
        if media:
            piece += "\n\n" + media
        body.append(piece)

    lines = [
        f"# {args.title}",
        "",
        f"来源：Bluesky [@{handle}](https://bsky.app/profile/{handle})，{created}",
        f"原帖：<https://bsky.app/profile/{handle}/post/{root['uri'].rsplit('/', 1)[-1]}>"
        "（内容已完整本地化，无需访问原链接）",
        "",
        f"> 作者串文共 {len(chain)} 条（他人回复未收录）。",
        "",
        "---",
        "",
        "\n\n".join(body),
        "",
    ]
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT)} ({args.out.stat().st_size} bytes)")
    if others > 0:
        print(f"note: {others} reply/replies by other accounts were skipped (archive convention)")


if __name__ == "__main__":
    import urllib.parse  # noqa: E402  (used by api())
    main()
