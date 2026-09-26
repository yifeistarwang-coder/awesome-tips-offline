#!/usr/bin/env python3
"""Archive the full X/Twitter threads linked from README.md.

Uses the logged-in Safari session (via AppleScript JavaScript injection) to call
X's TweetDetail GraphQL endpoint, so the complete author thread — not just the
root post — plus photos and short videos/GIFs are captured locally.

Usage:
    python3 scripts/fetch_x_threads.py            # incremental: cached threads skipped
    python3 scripts/fetch_x_threads.py --refresh  # re-fetch everything
    python3 scripts/fetch_x_threads.py --ids 1647098218172252160
    python3 scripts/fetch_x_threads.py --limit 3  # first N threads (debug)
"""

from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
THREADS_DIR = ROOT / "threads"
MEDIA_DIR = THREADS_DIR / "media"
CACHE_DIR = THREADS_DIR / ".cache"
SCRIPTS_DIR = Path(__file__).resolve().parent
BATCH_JS = SCRIPTS_DIR / "x_fetch_batch.js"
PROBE_JS = SCRIPTS_DIR / "x_graphql_probe.js"

# Fallbacks in case the bundle probe cannot find them.
FALLBACK_QID = "zoF7_t363wZyzylk-BLfZQ"
FALLBACK_BEARER = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

BATCH_SIZE = 4
CURL_RETRIES = 3


# --------------------------------------------------------------------------
# Safari / AppleScript bridge
# --------------------------------------------------------------------------

def _run_osascript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script], capture_output=True, text=True, timeout=180
    )
    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if "Allow JavaScript from Apple Events" in (out + err):
        raise SystemExit(
            "错误：Safari 未开启脚本注入权限。请按 browser-scrape skill 的 "
            "references/permission-guide.md 开启后重试。"
        )
    if proc.returncode != 0 or "execution error" in err.lower():
        raise RuntimeError((err or out or "osascript failed")[:500])
    return out


def do_js(js: str) -> str:
    """Run JavaScript in the current tab of Safari's front window."""
    escaped = js.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        'tell application "Safari"\n'
        f'  do JavaScript "{escaped}" in current tab of front window\n'
        "end tell"
    )
    return _run_osascript(script)


def focus_x_tab() -> None:
    """Bring an x.com tab to the front, opening one if necessary."""
    script = '''
tell application "Safari"
  activate
  set found to false
  repeat with w in windows
    repeat with t in tabs of w
      set u to URL of t
      if u starts with "https://x.com" or u starts with "https://twitter.com" then
        set current tab of w to t
        set index of w to 1
        set found to true
        exit repeat
      end if
    end repeat
    if found then exit repeat
  end repeat
  if not found then
    if (count of windows) = 0 then
      make new document with properties {URL:"https://x.com/home"}
    else
      tell front window
        set t to make new tab with properties {URL:"https://x.com/home"}
        set current tab to t
      end tell
    end if
    delay 8
  end if
end tell
return "ok"
'''
    _run_osascript(script)


def ensure_x_page() -> None:
    url = do_js("location.href")
    if not (url.startswith("https://x.com") or url.startswith("https://twitter.com")):
        focus_x_tab()
        time.sleep(2)
        url = do_js("location.href")
        if not (url.startswith("https://x.com") or url.startswith("https://twitter.com")):
            raise RuntimeError(f"当前 Safari 标签页不是 x.com：{url}")


def probe_endpoint() -> tuple[str, str]:
    """Find the current TweetDetail queryId and bearer token from loaded bundles."""
    do_js(PROBE_JS.read_text(encoding="utf-8"))
    for _ in range(30):
        time.sleep(1)
        raw = do_js("window.__probe || 'PENDING'")
        if raw and raw != "PENDING":
            break
    try:
        data = json.loads(raw)
    except Exception:
        data = {}
    qid = data.get("queryId") or FALLBACK_QID
    bearer = data.get("bearer") or FALLBACK_BEARER
    if data.get("queryId"):
        print(f"  TweetDetail queryId: {qid} (从页面 bundle 提取)")
    else:
        print(f"  TweetDetail queryId: {qid} (使用内置回退值)")
    return qid, bearer


def run_batch(ids: list[str], qid: str, bearer: str) -> dict:
    js = BATCH_JS.read_text(encoding="utf-8").replace("__QID__", qid).replace("__BEARER__", bearer)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as fh:
        fh.write(js)
        tmp_path = fh.name
    try:
        # 不主动抢焦点：仅在当前标签页不是 x.com 时才重新聚焦，避免打断用户。
        current = do_js("location.href")
        if not (current.startswith("https://x.com") or current.startswith("https://twitter.com")):
            focus_x_tab()
        do_js(f"window.__ids = {json.dumps(ids)}; 'ok'")
        do_js(js)
        for _ in range(60):
            time.sleep(1)
            raw = do_js("window.__batch")
            if raw == "PENDING":
                continue
            if raw.startswith("ERROR"):
                raise RuntimeError(raw)
            if not raw:
                continue
            return json.loads(raw)
        raise RuntimeError("等待 GraphQL 响应超时（Safari 可能被切到后台或标签被关闭）")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# --------------------------------------------------------------------------
# README parsing
# --------------------------------------------------------------------------

def parse_readme() -> list[tuple[str, list[tuple[str, str]]]]:
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    seen: set[str] = set()
    current = None
    for line in README.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"^###\s+(.+)$", line)
        if heading:
            current = heading.group(1).strip()
            sections.append((current, []))
            continue
        link = re.match(
            r"^- \[([^]]+)\]\(https?://(?:twitter|x)\.com/jbhuang0604/status/(\d+)[^)]*\)",
            line,
        )
        if link and current and link.group(2) not in seen:
            seen.add(link.group(2))
            sections[-1][1].append((link.group(1), link.group(2)))
    if not any(posts for _, posts in sections):
        sections = parse_index_json()
    return [(c, p) for c, p in sections if p]


def parse_index_json() -> list[tuple[str, list[tuple[str, str]]]]:
    """Fallback once README.md links locally: rebuild the thread list from the
    cached scripts/readme_index.json (created from the original README)."""
    index = SCRIPTS_DIR / "readme_index.json"
    if not index.exists():
        return []
    raw = json.loads(index.read_text(encoding="utf-8"))
    seen: set[str] = set()
    sections: list[tuple[str, list[tuple[str, str]]]] = []
    for category, items in raw:
        posts: list[tuple[str, str]] = []
        for item in items:
            if item.get("type") == "x" and item.get("id") not in seen:
                seen.add(item["id"])
                posts.append((item["title"], item["id"]))
        sections.append((category, posts))
    return sections


# --------------------------------------------------------------------------
# Fetching
# --------------------------------------------------------------------------

def fetch_all(ids: list[str], qid: str, bearer: str, refresh: bool) -> dict[str, dict]:
    results: dict[str, dict] = {}
    pending: list[str] = []
    for tid in ids:
        cache = CACHE_DIR / f"{tid}.json"
        if cache.exists() and not refresh:
            try:
                results[tid] = json.loads(cache.read_text(encoding="utf-8"))
                continue
            except Exception:
                pass
        pending.append(tid)

    if not pending:
        print("所有线程都已缓存，跳过抓取。")
        return results

    print(f"需要抓取 {len(pending)} 个线程（共 {len(ids)} 个）")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    round_no = 0
    while pending and round_no < 4:
        round_no += 1
        failed: list[str] = []
        done = 0
        for i in range(0, len(pending), BATCH_SIZE):
            batch = pending[i : i + BATCH_SIZE]
            print(f"  [第 {round_no} 轮] 批次 {batch[0]}…（{len(batch)} 个）", flush=True)
            try:
                payload = run_batch(batch, qid, bearer)
            except Exception as exc:
                print(f"    批次失败：{exc}")
                failed.extend(batch)
                time.sleep(5)
                continue
            for tid in batch:
                res = payload.get(tid)
                if res and not res.get("error"):
                    (CACHE_DIR / f"{tid}.json").write_text(
                        json.dumps(res, ensure_ascii=False), encoding="utf-8"
                    )
                    results[tid] = res
                    n = len(res.get("chain") or [])
                    print(f"    ✓ {tid}: {n} 条串文")
                else:
                    err = (res or {}).get("error", "无返回")
                    print(f"    ✗ {tid}: {err}")
                    failed.append(tid)
            done += len(batch)
            time.sleep(1.2)

        if failed:
            # Rate limits need a longer cool-down than transient errors.
            any_rate = False
            for tid in failed:
                print(f"    重试队列：{tid}")
            any_rate = round_no < 2
            wait = 60 if any_rate else 15
            print(f"    等待 {wait}s 后重试 {len(failed)} 个失败的线程…")
            time.sleep(wait)
        pending = failed
    if pending:
        print(f"仍有 {len(pending)} 个线程抓取失败：{pending}")
    return results


# --------------------------------------------------------------------------
# Media download
# --------------------------------------------------------------------------

def collect_media(results: dict[str, dict]) -> list[dict]:
    """Return a deduplicated media download plan."""
    plan: dict[str, dict] = {}
    for tid in sorted(results):
        res = results[tid]
        for tweet in (res.get("chain") or []) + (res.get("extras") or []):
            index = 0
            for photo in tweet.get("photos") or []:
                index += 1
                url = photo["url"]
                name = f"{tweet['id']}-{index}{media_ext(url)}"
                item = plan.setdefault(url, {"url": url, "path": MEDIA_DIR / name, "name": name, "tweet": tweet["id"]})
                item.setdefault("kinds", []).append("photo")
                photo["file"] = item["name"]
            for video in tweet.get("videos") or []:
                index += 1
                poster_url = video.get("poster")
                mp4_url = video.get("url")
                if poster_url:
                    name = f"{tweet['id']}-{index}.jpg"
                    item = plan.setdefault(poster_url, {"url": poster_url, "path": MEDIA_DIR / name, "name": name, "tweet": tweet["id"]})
                    item.setdefault("kinds", []).append("poster")
                    video["poster_file"] = name
                if mp4_url:
                    name = f"{tweet['id']}-{index}.mp4"
                    item = plan.setdefault(mp4_url, {"url": mp4_url, "path": MEDIA_DIR / name, "name": name, "tweet": tweet["id"]})
                    item.setdefault("kinds", []).append("video")
                    video["file"] = name
    return list(plan.values())


def media_ext(url: str) -> str:
    path = url.split("?")[0]
    suffix = Path(path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


def download_one(item: dict) -> tuple[str, bool, str]:
    target: Path = item["path"]
    if target.exists() and target.stat().st_size > 512:
        return item["name"], True, ""
    cmd = [
        "curl", "-sL", "--fail", "--retry", str(CURL_RETRIES), "--retry-delay", "2",
        "--max-time", "120", "-A",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "-o", str(target), item["url"],
    ]
    for attempt in range(2):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0 and target.exists() and target.stat().st_size > 512:
            return item["name"], True, ""
        time.sleep(1 + attempt)
    return item["name"], False, (proc.stderr or f"curl exit {proc.returncode}").strip()[:200]


def download_media(plan: list[dict]) -> set[str]:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    ok: set[str] = set()
    done = 0
    total = len(plan)
    print(f"下载 {total} 个媒体文件…")
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(download_one, item): item for item in plan}
        for fut in as_completed(futures):
            name, success, err = fut.result()
            done += 1
            if success:
                ok.add(name)
            else:
                print(f"  ✗ {name}: {err}")
            if done % 25 == 0 or done == total:
                print(f"  {done}/{total}")
    return ok


# --------------------------------------------------------------------------
# Markdown rendering
# --------------------------------------------------------------------------

def fmt_date(raw: str) -> str:
    try:
        dt = parsedate_to_datetime(raw)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return raw


def clean_text(text: str) -> str:
    text = html.unescape(text or "")
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines).strip()


def is_meaningful_extra(tweet: dict) -> bool:
    if tweet.get("photos") or tweet.get("videos"):
        return True
    text = clean_text(tweet.get("text", ""))
    if len(text) < 60:
        return False
    if re.fullmatch(r"(@\w+\s*)+[^A-Za-z]{0,3}(Thanks|Thank you)[^A-Za-z]{0,3}", text, re.I):
        return False
    return True


def render_media(tweet: dict, ok_files: set[str]) -> list[str]:
    lines: list[str] = []
    for photo in tweet.get("photos") or []:
        name = photo.get("file")
        if name and name in ok_files:
            alt = clean_text(photo.get("alt") or "").replace("]", "]") or "image"
            lines.append(f"![{alt}](media/{name})")
            lines.append("")
    for video in tweet.get("videos") or []:
        poster = video.get("poster_file")
        mp4 = video.get("file")
        kind = "GIF 动画" if video.get("type") == "animated_gif" else "视频"
        if poster and poster in ok_files and mp4 and mp4 in ok_files:
            lines.append(f"[![{kind}预览](media/{poster})](media/{mp4})")
            lines.append("")
            lines.append(f"▶ [{kind}（点击播放）](media/{mp4})")
            lines.append("")
        elif poster and poster in ok_files:
            lines.append(f"![{kind}预览](media/{poster})")
            lines.append("")
        elif mp4 and mp4 in ok_files:
            lines.append(f"▶ [{kind}（点击播放）](media/{mp4})")
            lines.append("")
        elif video.get("url"):
            lines.append(f"▶ [{kind}（需在线播放）]({tweet['url']})")
            lines.append("")
    return lines


def render_tweet(tweet: dict, ok_files: set[str], title: str) -> list[str]:
    lines: list[str] = []
    text = clean_text(tweet.get("text", ""))
    article = tweet.get("article") or {}
    if article.get("text"):
        if article.get("title"):
            lines.append(f"**{clean_text(article['title'])}**")
            lines.append("")
        text = clean_text(article["text"])
    if text:
        lines.append(text)
        lines.append("")
    quoted = tweet.get("quoted")
    if quoted and clean_text(quoted.get("text")):
        qtext = clean_text(quoted["text"])
        qauthor = quoted.get("author") or "i"
        qlines = ["> **引用 [@" + qauthor + "](https://x.com/" + qauthor + ")**：", ">"]
        for qline in qtext.split("\n"):
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
                label = f" — {clean_text(card['title'])}"
            lines.append(f"- <{url}>{label}")
        lines.append("")
    return lines


def render_thread(title: str, res: dict, ok_files: set[str]) -> list[str]:
    chain = res.get("chain") or []
    tweets = [t for t in chain if not t.get("tombstone")]
    gaps = [t for t in chain if t.get("tombstone")]
    if not tweets:
        return [f"## {title}", "", "_未获取到线程内容。_", ""]
    first = tweets[0]
    focal = next((t for t in tweets if t["id"] == res.get("focal_id")), first)
    header = f"原帖：<{first['url']}> · {fmt_date(focal.get('created_at', ''))} · 共 {len(tweets)} 条串文"
    if gaps:
        header += f"（另有 {len(gaps)} 条已不可用）"
    lines = [f"## {title}", "", header, ""]
    for tweet in chain:
        if tweet.get("tombstone"):
            lines.extend(["> ⚠️ 此处一条推文在 X 上显示为“不可用”（可能已删除），线程内容在此处不连续。", ""])
            continue
        lines.extend(render_tweet(tweet, ok_files, title))
    extras = [t for t in (res.get("extras") or []) if is_meaningful_extra(t)]
    if extras:
        lines.extend(["### 作者补充回复", ""])
        for tweet in extras:
            text = clean_text(tweet.get("text", ""))
            if text:
                lines.append(text)
                lines.append("")
            lines.extend(render_media(tweet, ok_files))
            lines.append(f"<{tweet['url']}>")
            lines.append("")
    return lines


def write_markdown(
    sections: list[tuple[str, list[tuple[str, str]]]],
    results: dict[str, dict],
    ok_files: set[str],
) -> set[str]:
    used_files: set[str] = set()

    n_threads = len(results)
    n_photos = sum(len(t.get("photos") or []) for r in results.values() for t in (r.get("chain") or []) + (r.get("extras") or []))
    n_videos = sum(len(t.get("videos") or []) for r in results.values() for t in (r.get("chain") or []) + (r.get("extras") or []))
    n_gaps = sum(1 for r in results.values() for t in (r.get("chain") or []) if t.get("tombstone"))

    def render_and_track(title: str, res: dict) -> list[str]:
        lines = render_thread(title, res, ok_files)
        for m in re.finditer(r"\(media/([^)]+)\)", "\n".join(lines)):
            used_files.add(m.group(1))
        return lines

    index_lines = [
        "# X/Twitter 线程归档（完整串文）",
        "",
        "来源：Jia-Bin Huang 的 [awesome-tips 仓库](../README.md)。",
        "",
        f"共 **{n_threads}** 条线程（README 去重后）、**{n_photos}** 张配图、**{n_videos}** 个 GIF/视频。",
        "",
        "> 此目录由 `scripts/fetch_x_threads.py` 借助本机 Safari 的 X 登录态调用 TweetDetail 接口生成：",
        "> 包含作者完整串文、配图与 GIF/短视频（保存在 `media/`），t.co 短链已展开。",
        "> 其他用户的回复未收录；作者对评论的补充回复以“作者补充回复”附在文末。",
        f"> 若原帖在 X 上已被删除，会以 ⚠️ 标记占位（共 {n_gaps} 处）。全部线程另见 [all-threads.md](all-threads.md)。",
        "> 中文版：[中文索引](zh/README.md) · [中文合集](zh/all-threads.md)。更多本地化内容：[Bluesky 帖子](bsky-how-to-drive-your-research-forward.md)、[讲稿幻灯片](slides/README.md)、[双语 README](../README-CN.md)。",
        "",
    ]
    rendered_titles: dict[str, str] = {}
    combined = ["# Awesome Tips：X/Twitter 线程完整合集", "", "按 [README](../README.md) 分类整理的完整串文（含配图）。", ""]
    for category, posts in sections:
        filename = safe_name(category) + ".md"
        lines = [f"# {category}", "", f"> 完整串文归档（{len(posts)} 条）。返回 [线程索引](README.md)。", ""]
        combined.append(f"# {category}")
        combined.append("")
        for title, tid in posts:
            if tid in rendered_titles:
                ref = rendered_titles[tid]
                lines.extend([f"## {title}", "", f"_此线程已收录于 [{ref}]({safe_name(ref)}.md)。_", ""])
                combined.extend([f"## {title}", "", f"_此线程已收录于 [{ref}]({safe_name(ref)}.md)。_", ""])
                continue
            res = results.get(tid)
            if not res:
                lines.extend([f"## {title}", "", f"原帖：<https://x.com/jbhuang0604/status/{tid}>", "", "_抓取失败。_", ""])
                continue
            rendered_titles[tid] = category
            block = render_and_track(title, res)
            lines.extend(block)
            combined.extend(block)
        (THREADS_DIR / filename).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        index_lines.append(
            "- [{cat}]({f})（{n} 条）".format(cat=category, f=filename, n=len(posts))
        )
        print(f"  写入 threads/{filename}")
    index_lines.append("")
    (THREADS_DIR / "README.md").write_text("\n".join(index_lines), encoding="utf-8")
    (THREADS_DIR / "all-threads.md").write_text("\n".join(combined).rstrip() + "\n", encoding="utf-8")
    print("  写入 threads/README.md 与 threads/all-threads.md")
    return used_files


def safe_name(text: str) -> str:
    name = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return name or "misc"


def update_root_docs() -> None:
    text = README.read_text(encoding="utf-8")
    old = "- [X/Twitter threads: fetched post text and available images](threads/README.md)"
    new = "- [X/Twitter threads: full thread text with images and GIFs](threads/README.md) · [单文件合集](threads/all-threads.md)"
    if old in text:
        README.write_text(text.replace(old, new), encoding="utf-8")
        print("  更新 README.md 索引")

    zh = ROOT / "中文离线阅读版.md"
    if zh.exists():
        zh_text = zh.read_text(encoding="utf-8")
        old_note = (
            "另已抓取 README 中 66 条去重 X/Twitter 线程根帖及可获取的本地配图，"
            "按分类整理在 [线程归档](threads/README.md)。X 的匿名公开接口没有提供大多数线程回复，"
            "因此该归档不是完整串文；未获取的回复没有推测补写。"
        )
        new_note = (
            "另已借助本机 Safari 的 X 登录态抓取 README 中全部去重 X/Twitter 线程的"
            "**完整串文**、配图与 GIF/短视频，按分类整理在 [线程归档](threads/README.md)"
            "（单文件合集：[all-threads.md](threads/all-threads.md)）。正文保留作者英文原文，未做翻译。"
        )
        if old_note in zh_text:
            zh.write_text(zh_text.replace(old_note, new_note), encoding="utf-8")
            print("  更新 中文离线阅读版.md 说明")


def cleanup_media(used_files: set[str]) -> None:
    removed = 0
    for path in MEDIA_DIR.iterdir():
        if not path.is_file():
            continue
        if path.name not in used_files:
            path.unlink()
            removed += 1
    if removed:
        print(f"  清理 {removed} 个不再引用的旧媒体文件")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="忽略缓存重新抓取")
    parser.add_argument("--ids", nargs="*", help="只抓取指定 tweet id")
    parser.add_argument("--limit", type=int, help="只处理前 N 个线程（调试用）")
    parser.add_argument("--skip-media", action="store_true", help="跳过媒体下载")
    args = parser.parse_args()

    sections = parse_readme()
    all_ids: list[str] = []
    for _, posts in sections:
        for _, tid in posts:
            if tid not in all_ids:
                all_ids.append(tid)
    if not all_ids:
        raise SystemExit("README 中没有找到 X/Twitter 线程链接。")
    selected = list(all_ids)
    if args.ids:
        wanted = set(args.ids)
        selected = [i for i in all_ids if i in wanted]
        if not selected:
            raise SystemExit("指定的 --ids 不在 README 中。")
    if args.limit:
        selected = selected[: args.limit]
    if not selected:
        raise SystemExit("没有需要处理的线程。")

    print(f"共 {len(all_ids)} 个线程，本次处理 {len(selected)} 个。检查 Safari…")
    focus_x_tab()
    ensure_x_page()
    qid, bearer = probe_endpoint()

    results = fetch_all(selected, qid, bearer, args.refresh)
    # 渲染时使用全部线程：优先本次结果，其次磁盘缓存。
    render_results: dict[str, dict] = {}
    for tid in all_ids:
        if tid in results:
            render_results[tid] = results[tid]
        else:
            cache = CACHE_DIR / f"{tid}.json"
            if cache.exists():
                try:
                    render_results[tid] = json.loads(cache.read_text(encoding="utf-8"))
                except Exception:
                    pass
    partial = args.limit is not None or bool(args.ids)
    if args.skip_media:
        # Rerender only; reuse whatever media files already exist locally.
        collect_media(render_results)  # 重新分配文件名（不下载）
        ok_files = {p.name for p in MEDIA_DIR.iterdir() if p.is_file()} if MEDIA_DIR.exists() else set()
        write_markdown(sections, render_results, ok_files)
        return

    media_plan = collect_media(render_results)
    ok_files = download_media(media_plan)
    used = write_markdown(sections, render_results, ok_files)
    failed_ids = [tid for tid in all_ids if tid not in render_results]
    if not partial and not failed_ids:
        cleanup_media(used)
        update_root_docs()
    elif failed_ids:
        print("  存在失败线程，保留旧媒体文件并暂不更新根 README。")

    print()
    print("完成。")
    if failed_ids:
        print(f"失败 {len(failed_ids)} 个：{', '.join(failed_ids)}")
    print(f"线程：{len(results)}，媒体：{len(ok_files)}/{len(media_plan)}")


if __name__ == "__main__":
    main()
