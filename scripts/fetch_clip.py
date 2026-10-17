#!/usr/bin/env python3
"""Download a viral clip on Dylan's PC (YouTube blocks cloud servers) and hand it to the cloud session through this repo.

  python scripts/fetch_clip.py URL [NAME]        e.g. python scripts/fetch_clip.py https://www.youtube.com/watch?v=4jrrWgDn-Rs wemby

Downloads the video at <= 720p (yt-dlp, installed if missing), keeps at most the first 60 s, re-encodes it small,
saves viral/<YYYY-MM-DD>_<NAME>.mp4, then commits and pushes it to the current branch so the cloud can pull it.
"""
import datetime, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
url = sys.argv[1]; name = sys.argv[2] if len(sys.argv) > 2 else "clip"
try:
    import yt_dlp  # noqa: F401
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"], check=True)
out_dir = os.path.join(ROOT, "viral"); os.makedirs(out_dir, exist_ok=True)
raw = os.path.join(out_dir, "_raw.%(ext)s")
subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "-f", "bv*[height<=720]+ba/b[height<=720]/b", "--merge-output-format", "mp4",
                "-o", raw, url], check=True)
src = next(os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith("_raw."))
dst = os.path.join(out_dir, f"{datetime.date.today():%Y-%m-%d}_{name}.mp4")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-t", "60", "-vf", "scale=-2:720", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "20", "-c:a", "aac", "-b:a", "160k", dst], check=True)
os.remove(src)
subprocess.run(["git", "-C", ROOT, "add", dst], check=True)
subprocess.run(["git", "-C", ROOT, "commit", "-m", f"Viral clip for the daily video: {os.path.basename(dst)} ({url})"], check=True)
subprocess.run(["git", "-C", ROOT, "pull", "--rebase"], check=True)
subprocess.run(["git", "-C", ROOT, "push"], check=True)
print("pushed", dst, f"({os.path.getsize(dst) / 1e6:.1f} MB)")
