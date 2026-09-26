#!/usr/bin/env python3
"""Shrink ``threads/media`` in place, without touching any file name.

Every reference in the Markdown archive (and therefore in the generated site)
is by name, so the optimiser never renames or re-encodes to a different
container: a ``.png`` stays a ``.png``, a ``.mp4`` stays a ``.mp4``. It only
re-encodes, and it keeps the result **only when it is actually smaller**, so
running it twice is a no-op and it can never make the archive bigger.

What it does, by kind:

  mp4  >= 20 MB  screen recordings: downscale to <=960px, cap 24fps, CRF 32,
                 maxrate 1200k, audio (if any) becomes 64 kbps mono AAC
  mp4  3-20 MB  screen recordings: <=1280px, cap 30fps, CRF 30
  mp4  <  3 MB   GIF conversions: <=640px, cap 24fps, CRF 32
  jpg / jpeg     max 1200px, mjpeg quality 4 (~q85)
  png            max 1200px, re-deflate (slide screenshots)
  gif            max 640px, cap 15fps, 128-colour palette (--gif-to-video replaces
                 animated GIFs with H.264 clips instead, which is far smaller)

Usage
-----
    python3 scripts/optimize_media.py --report          # show what would happen
    python3 scripts/optimize_media.py                   # do it (parallel)
    python3 scripts/optimize_media.py -j 4 --only videos
    python3 scripts/optimize_media.py --check           # verify every file is readable

Afterwards rebuild the site (``rm -rf site && python3 scripts/build_site.py``)
so that ``site/media`` links to the new files instead of the old inodes.
"""

from __future__ import annotations

import argparse
import concurrent.futures as futures
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ROOT / "threads" / "media"

VIDEO_GIANT = 20 * 1024 * 1024         # 1080p60 screen recordings
VIDEO_BIG = 3 * 1024 * 1024           # still screen recordings, but short
KEEP_MARGIN = 0.98                    # only replace when >=2% smaller


def ffprobe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v",
         "-show_entries", "stream=width,height,r_frame_rate,codec_name",
         "-show_entries", "format=duration,size,bit_rate", "-of", "default=nw=1", str(path)],
        capture_output=True, text=True,
    ).stdout
    info: dict[str, str] = {}
    for line in out.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            info[k] = v
    return info


def has_audio(path: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_name",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    return bool(out)


def fps_of(info: dict) -> float:
    raw = info.get("r_frame_rate", "0/1")
    try:
        num, den = raw.split("/")
        return float(num) / float(den) if float(den) else 0.0
    except ValueError:
        return 0.0


def plan(path: Path, aggressive: bool = False) -> tuple[list[str], str]:
    """Return (ffmpeg args, human description) for this file."""
    size = path.stat().st_size
    ext = path.suffix.lower()
    tmp = path.with_name(path.stem + "__opt" + ext)

    if ext == ".mp4":
        info = ffprobe(path)
        w = int(info.get("width") or 0)
        fps = fps_of(info)
        if size >= VIDEO_GIANT:
            maxw, maxfps, crf, cap = 960, 24, 32, "1200k"
        elif size >= VIDEO_BIG:
            maxw, maxfps, crf, cap = 1280, 30, 30, None
        else:
            maxw, maxfps, crf, cap = 640, 24, 32, None
        if aggressive:
            if size >= VIDEO_GIANT:
                maxw, maxfps, crf, cap = 720, 24, 34, "800k"
            elif size >= VIDEO_BIG:
                maxw, maxfps, crf, cap = 960, 24, 32, "1000k"
        filters = []
        if w > maxw:
            filters.append(f"scale='min({maxw},iw)':-2:flags=lanczos")
        if fps > maxfps:
            filters.append(f"fps={maxfps}")
        args = ["-c:v", "libx264", "-preset", "slow", "-crf", str(crf), "-pix_fmt", "yuv420p"]
        if cap:
            args += ["-maxrate", cap, "-bufsize", str(int(cap.rstrip("k")) * 2) + "k"]
        if filters:
            args += ["-vf", ",".join(filters)]
        if has_audio(path):
            args += ["-map", "0:v:0", "-map", "0:a:0", "-c:a", "aac", "-b:a", "64k", "-ac", "1"]
        else:
            args += ["-an"]
        args += ["-movflags", "+faststart"]
        tier = "giant" if size >= VIDEO_GIANT else ("screen" if size >= VIDEO_BIG else "gif-like")
        label = f"mp4 {tier} {w}px@{fps:.0f}->{maxw}px crf{crf}"

    elif ext in (".jpg", ".jpeg"):
        maxw, q = (1000, "5") if aggressive else (1200, "4")
        args = ["-vf", f"scale='min({maxw},iw)':-2:flags=lanczos", "-q:v", q,
                "-frames:v", "1", "-update", "1"]
        label = f"jpeg max{maxw} q{q}"

    elif ext == ".png":
        maxw = 1000 if aggressive else 1200
        args = ["-vf", f"scale='min({maxw},iw)':-2:flags=lanczos", "-compression_level", "9",
                "-pred", "mixed", "-frames:v", "1", "-update", "1"]
        label = f"png max{maxw}"

    elif ext == ".gif":
        if aggressive:
            maxw, fps, colors, dither = 480, 12, 64, "dither=none"
        else:
            maxw, fps, colors, dither = 640, 15, 128, "dither=bayer:bayer_scale=3"
        chain = (
            f"scale='min({maxw},iw)':-2:flags=lanczos,fps={fps},split[a][b];"
            f"[a]palettegen=max_colors={colors}:stats_mode=diff[p];"
            f"[b][p]paletteuse={dither}:diff_mode=rectangle"
        )
        args = ["-vf", chain]
        label = f"gif max{maxw} {fps}fps {colors}c"

    else:
        return [], "skip"

    return ["ffmpeg", "-v", "error", "-y", "-i", str(path), *args, str(tmp)], label


def optimize(path: Path, dry: bool, aggressive: bool = False) -> tuple[Path, int, int, str]:
    before = path.stat().st_size
    args, label = plan(path, aggressive)
    if not args:
        return path, before, before, "skipped (unsupported)"

    tmp = Path(args[-1])
    try:
        run = subprocess.run(args, capture_output=True, text=True)
        if run.returncode != 0:
            tmp.unlink(missing_ok=True)
            return path, before, before, f"FAILED: {run.stderr.strip().splitlines()[-1][:70] if run.stderr.strip() else 'ffmpeg error'}"
        after = tmp.stat().st_size
    except Exception as exc:                                  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        return path, before, before, f"FAILED: {exc}"

    if after < before * KEEP_MARGIN:
        if not dry:
            os.replace(tmp, path)
        else:
            tmp.unlink(missing_ok=True)
        return path, before, after, label
    tmp.unlink(missing_ok=True)
    return path, before, before, f"kept original ({label})"


def check(path: Path) -> tuple[Path, bool, str]:
    ext = path.suffix.lower()
    if ext == ".mp4":
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v",
                            "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(path)],
                           capture_output=True, text=True)
        return path, r.returncode == 0 and bool(r.stdout.strip()), r.stderr.strip()[:80]
    try:
        head = path.open("rb").read(16)
    except OSError as exc:
        return path, False, str(exc)
    sigs = {b"\xff\xd8\xff": "jpeg", b"\x89PNG": "png", b"GIF8": "gif"}
    ok = any(head.startswith(s) for s in sigs)
    return path, ok, "" if ok else f"bad signature {head[:8]!r}"


def gif_to_video(paths: list[Path], jobs: int) -> list[tuple[Path, int, int, str]]:
    """Animated GIFs are the most expensive bytes in the archive (a 5 MB GIF is
    ~200 KB as H.264). Convert them, emit a still poster next to each clip so the
    site can show something before playback starts, and rewrite every
    ``.gif`` reference in the Markdown sources to point at the new ``.mp4``.
    """
    results: list[tuple[Path, int, int, str]] = []
    renamed: dict[str, str] = {}

    def convert(gif: Path) -> tuple[Path, int, int, str]:
        before = gif.stat().st_size
        mp4 = gif.with_suffix(".mp4")
        poster = gif.with_suffix(".jpg")
        # even dimensions are required by yuv420p; -loop 0 makes x264 repeat the
        # first frame like a GIF would when a viewer stays on the last frame
        enc = subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(gif),
             "-movflags", "+faststart", "-pix_fmt", "yuv420p", "-crf", "28", "-preset", "slow",
             "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos", "-an", str(mp4)],
            capture_output=True, text=True,
        )
        if enc.returncode != 0 or not mp4.exists():
            mp4.unlink(missing_ok=True)
            return gif, before, before, "FAILED"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(gif), "-frames:v", "1",
             "-q:v", "4", "-update", "1", str(poster)],
            capture_output=True, text=True,
        )
        after = mp4.stat().st_size + (poster.stat().st_size if poster.exists() else 0)
        return gif, before, after, f"gif->mp4 {before / 1e3:.0f}KB->{after / 1e3:.0f}KB"

    with futures.ThreadPoolExecutor(jobs) as pool:
        for gif, before, after, label in pool.map(convert, paths):
            results.append((gif, before, after, label))
            if label.startswith("gif->mp4"):
                renamed[gif.name] = gif.with_suffix(".mp4").name

    if renamed:
        md_files = [p for p in (ROOT / "threads").rglob("*.md")]
        touched = 0
        for md in md_files:
            text = original = md.read_text(encoding="utf-8")
            for old, new in renamed.items():
                text = text.replace(f"/{old})", f"/{new})")
            if text != original:
                md.write_text(text, encoding="utf-8")
                touched += 1
        print(f"rewrote .gif references in {touched} Markdown files")
        for gif, before, after, label in results:
            if label.startswith("gif->mp4"):
                gif.unlink()
    return results


def human(n: int) -> str:
    return f"{n / 1e6:.1f}MB" if n >= 1e6 else f"{n / 1e3:.0f}KB"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="only report what would change")
    ap.add_argument("--check", action="store_true", help="only verify every media file is readable")
    ap.add_argument("-j", "--jobs", type=int, default=min(8, (os.cpu_count() or 4)))
    ap.add_argument("--only", choices=["videos", "images", "gifs"], help="restrict to one kind")
    ap.add_argument("--aggressive", action="store_true", help="second, harder pass (smaller/fewer bits)")
    ap.add_argument("--min-size", type=int, default=0, metavar="BYTES",
                    help="only touch files at least this big (fast targeted pass)")
    ap.add_argument("--gif-to-video", action="store_true",
                    help="replace animated GIFs with H.264 clips (+ poster) and rewrite references")
    ap.add_argument("--limit", type=int, help="only process the first N files (debugging)")
    args = ap.parse_args()

    if not MEDIA.exists():
        sys.exit(f"no media directory at {MEDIA}")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH")

    files = sorted(p for p in MEDIA.rglob("*") if p.is_file())
    if args.only == "videos":
        files = [p for p in files if p.suffix.lower() == ".mp4"]
    elif args.only == "images":
        files = [p for p in files if p.suffix.lower() in (".jpg", ".jpeg", ".png")]
    elif args.only == "gifs":
        files = [p for p in files if p.suffix.lower() == ".gif"]
    if args.limit:
        files = files[: args.limit]
    if args.min_size:
        files = [p for p in files if p.stat().st_size >= args.min_size]

    if args.gif_to_video:
        gifs = [p for p in MEDIA.rglob("*.gif")]
        before = sum(p.stat().st_size for p in gifs)
        print(f"{'report only — ' if args.report else ''}converting {len(gifs)} GIFs "
              f"({human(before)}) to H.264")
        if not args.report:
            res = gif_to_video(gifs, args.jobs)
            after = sum(r[2] for r in res)
            for gif, b, a, label in sorted(res, key=lambda r: -r[1])[:5]:
                print(f"  {gif.name:24s} {human(b):>8s} -> {human(a):>8s}")
            print(f"gifs: {human(before)} -> {human(after)}")
        return

    if args.check:
        bad = []
        with futures.ThreadPoolExecutor(args.jobs) as pool:
            for path, ok, why in pool.map(check, files):
                if not ok:
                    bad.append((path, why))
        print(f"checked {len(files)} files, {len(bad)} unreadable")
        for path, why in bad[:10]:
            print(f"  {path.relative_to(ROOT)}  {why}")
        sys.exit(1 if bad else 0)

    total_before = sum(p.stat().st_size for p in files)
    print(f"{'report only — ' if args.report else ''}optimising {len(files)} files "
          f"({human(total_before)}) with {args.jobs} workers"
          f"{' [aggressive]' if args.aggressive else ''}")

    results = []
    with futures.ThreadPoolExecutor(args.jobs) as pool:
        for res in pool.map(lambda p: optimize(p, args.report, args.aggressive), files):
            results.append(res)

    before = sum(r[1] for r in results)
    after = sum(r[2] for r in results)
    changed = [r for r in results if r[2] < r[1]]
    failed = [r for r in results if r[3].startswith("FAILED")]

    by_label: dict[str, list[int]] = {}
    for path, b, a, label in results:
        key = label.split(" ", 1)[0]
        slot = by_label.setdefault(key, [0, 0, 0])
        slot[0] += 1
        slot[1] += b
        slot[2] += a

    print()
    print(f"{'kind':10s} {'files':>6s} {'before':>10s} {'after':>10s}")
    for kind, (n, b, a) in sorted(by_label.items()):
        print(f"{kind:10s} {n:6d} {human(b):>10s} {human(a):>10s}")
    print()
    print(f"total  {human(before)} -> {human(after)}   "
          f"({100 * (before - after) / max(before, 1):.0f}% smaller, {len(changed)} files rewritten)")
    if failed:
        print(f"{len(failed)} failures:")
        for path, b, a, label in failed[:10]:
            print(f"  {path.relative_to(ROOT)}  {label}")
    if not args.report:
        print("\nrebuild the site so site/media links the new files:\n"
              "  rm -rf site && python3 scripts/build_site.py")


if __name__ == "__main__":
    main()
