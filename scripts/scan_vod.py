#!/usr/bin/env python3
"""Scan one of Dylan's Kick VODs for edit-worthy wins.

  python3 scan_vod.py list                         -> every VOD: date, id, hours
  python3 scan_vod.py sheets DATE OUTDIR [--step 15] -> pulls the 160p rendition, writes OUTDIR/sheet_NN.jpg contact sheets
                                                       (one frame every --step s, 6x8 per sheet, stamped with stream time h:mm:ss),
                                                       OUTDIR/loud.txt (loudest 10 s windows) and OUTDIR/clips.txt (chat clips that day)
  python3 scan_vod.py frame DATE T OUT.jpg [--crop x,y,w,h]   -> one 1080p frame at stream time T (seconds or h:mm:ss)
  python3 scan_vod.py strip DATE T0 T1 OUT.jpg [--step 1]     -> 1080p game-window strip T0..T1 (for confirming a win)
  python3 scan_vod.py clip DATE T0 T1 OUT.mp4                 -> exact 1080p60 clip for editing
All times are TRUE stream times (segment durations from the playlist; contact-sheet stamps and 1080p frames agree).

DATE is the stream's start date (UTC, YYYY-MM-DD) as `list` prints it. The 160p .ts is deleted after the sheets are made.
"""
import json, os, re, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np, cv2

UA = {"User-Agent": "Mozilla/5.0"}
def get(url, timeout=30):
    for i in range(6):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()
        except Exception:
            if i == 5: raise
            import time; time.sleep(2 ** i + 1)
def vods():
    return json.loads(get("https://kick.com/api/v2/channels/dylanjamesgg/videos"))
def vod(date):
    for v in vods():
        if (v.get("start_time") or "").startswith(date): return v
    sys.exit(f"no VOD starting {date}")
def segs(v, rend, durs=False):
    """segment urls (and their real durations: Kick's segments are NOT all 10 s, so never index by t // 10)"""
    base = v["source"].rsplit("/", 1)[0] + f"/{rend}/"
    pl = get(base + "playlist.m3u8").decode(); urls, d = [], []
    for l in pl.splitlines():
        if l.startswith("#EXTINF:"): d.append(float(l[8:].split(",")[0]))
        elif l and not l.startswith("#"): urls.append(base + l)
    return (urls, d) if durs else urls
def locate(d, t):
    """true stream time t -> (segment index, offset inside it)"""
    acc = 0.0
    for i, x in enumerate(d):
        if t < acc + x: return i, t - acc
        acc += x
    return len(d) - 1, d[-1] - 0.01
def hms(t): t = int(t); return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"
def secs(s): return sum(float(p) * 60 ** i for i, p in enumerate(reversed(str(s).split(":"))))
def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default

def sheets(date, out, step):
    os.makedirs(out, exist_ok=True); v = vod(date); urls = segs(v, "160p30")
    parts = os.path.join(out, "parts"); os.makedirs(parts, exist_ok=True)
    def dl(iu):
        i, u = iu; p = os.path.join(parts, f"{i:05d}.ts")
        if not os.path.exists(p): open(p, "wb").write(get(u))
    with ThreadPoolExecutor(16) as ex: list(ex.map(dl, enumerate(urls)))
    ts = os.path.join(out, "vod160.ts")
    with open(ts, "wb") as fh:
        for i in range(len(urls)): fh.write(open(os.path.join(parts, f"{i:05d}.ts"), "rb").read())
    subprocess.run(["rm", "-rf", parts])
    dur = int(sum(segs(v, "160p30", True)[1]))
    # frames every `step` s at 320x180 in one ffmpeg pass
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", ts, "-vf", f"fps=1/{step},scale=320:180", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 180, 320, 3)
    per = 48
    for k in range(0, len(fr), per):
        ims = []
        for j, f in enumerate(fr[k:k + per]):
            im = f.copy(); cv2.putText(im, hms((k + j) * step), (4, 20), 0, 0.6, (0, 255, 255), 2); ims.append(im)
        while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(os.path.join(out, f"sheet_{k // per:02d}.jpg"), np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)]),
                    [cv2.IMWRITE_JPEG_QUALITY, 82])
    # loudness per 10 s
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "quiet", "-i", ts, "-vn", "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                                     capture_output=True).stdout, np.float32)
    w = 80000; rms = [20 * np.log10(np.sqrt((a[i:i + w] ** 2).mean()) + 1e-9) for i in range(0, len(a) - w, w)]
    order = sorted(range(len(rms)), key=lambda i: -rms[i])[:25]
    open(os.path.join(out, "loud.txt"), "w").write("\n".join(f"{hms(i * 10)}  {rms[i]:.1f} dB" for i in sorted(order)))
    # chat clips from that stream
    try:
        cl = json.loads(get("https://kick.com/api/v2/channels/dylanjamesgg/clips?sort=date&time=all"))
        cl = cl.get("clips", cl) if isinstance(cl, dict) else cl
        st = v["start_time"]; from datetime import datetime
        t0 = datetime.fromisoformat(st)
        lines = []
        for c in cl:
            ca = (c.get("created_at") or "")[:19].replace("T", " ")
            if not ca: continue
            dt = (datetime.fromisoformat(ca) - t0).total_seconds()
            if 0 <= dt <= dur + 600: lines.append(f"{hms(dt)}  {c.get('title', '')}  ({c.get('duration', '')} s)")
        open(os.path.join(out, "clips.txt"), "w").write("\n".join(lines) or "none")
    except Exception as e:
        open(os.path.join(out, "clips.txt"), "w").write(f"clips unavailable: {e}")
    os.remove(ts)
    json.dump({"date": date, "id": v["id"], "duration_s": dur, "title": v.get("session_title"), "source": v["source"], "step": step},
              open(os.path.join(out, "vod.json"), "w"), indent=1)
    print(f"{date}: {dur / 3600:.2f} h, {len(fr)} frames -> {len(range(0, len(fr), per))} sheets in {out}")

def frame_at(v, t, rend="1080p60"):
    urls, d_ = segs(v, rend, True); i, off = locate(d_, t)
    d = f"/tmp/_seg_{os.getpid()}"; os.makedirs(d, exist_ok=True)          # per-process cache, keeps the newest 6 segments (~11 MB each)
    p = f"{d}/{v['id']}_{i}.ts"
    if not os.path.exists(p):
        open(p, "wb").write(get(urls[i]))
        for old in sorted((os.path.join(d, f) for f in os.listdir(d)), key=os.path.getmtime)[:-6]: os.remove(old)
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{off:.2f}", "-i", p, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1080, 1920, 3).copy() if len(raw) == 1920 * 1080 * 3 else None

def clip(date, t0, t1, out):
    """exact 1080p60 clip of true stream time t0..t1 (what the editor's clip.mp4 is made from)"""
    v = vod(date); urls, d = segs(v, "1080p60", True); i0, o0 = locate(d, t0); i1, _ = locate(d, t1)
    tmp = out + ".parts.ts"
    with open(tmp, "wb") as fh:
        for i in range(i0, i1 + 1): fh.write(get(urls[i], 60))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{o0:.3f}", "-i", tmp, "-t", f"{t1 - t0:.3f}", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "16", "-c:a", "aac", "-b:a", "192k", out], check=True)
    os.remove(tmp); print("wrote", out, f"({t1 - t0:.0f} s from {hms(t0)})")
import atexit, shutil
atexit.register(lambda: shutil.rmtree(f"/tmp/_seg_{os.getpid()}", ignore_errors=True))
if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "list":
        for v in vods(): print(v["start_time"][:10], v["id"], f"{int(v['duration']) / 3.6e6:.2f} h")
    elif a[0] == "sheets": sheets(a[1], a[2], int(arg("--step", 15)))
    elif a[0] == "frame":
        im = frame_at(vod(a[1]), secs(a[2]))
        if "--crop" in a: x, y, w, h = map(int, arg("--crop", "").split(",")); im = im[y:y + h, x:x + w]
        cv2.imwrite(a[3], im); print("wrote", a[3])
    elif a[0] == "clip": clip(a[1], secs(a[2]), secs(a[3]), a[4])
    elif a[0] == "strip":
        v = vod(a[1]); t0, t1, st = secs(a[2]), secs(a[3]), float(arg("--step", 1)); ims = []
        t = t0
        while t <= t1:
            im = frame_at(v, t)
            if im is not None:
                g = cv2.resize(im[230:925, 38:1326], (480, 259)); cv2.putText(g, hms(t) + f".{int(t * 10) % 10}", (6, 24), 0, 0.7, (0, 255, 255), 2); ims.append(g)
            t += st
        while len(ims) % 4: ims.append(np.zeros_like(ims[0]))
        cv2.imwrite(a[4], np.vstack([np.hstack(ims[i:i + 4]) for i in range(0, len(ims), 4)]), [cv2.IMWRITE_JPEG_QUALITY, 85]); print("wrote", a[4])
