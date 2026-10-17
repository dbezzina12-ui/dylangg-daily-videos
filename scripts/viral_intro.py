#!/usr/bin/env python3
"""Viral fail intro for the daily Live Standings video (Dylan, 2026-10-17): 1-2 s of a viral fail, cut on the impact with a
white flash + hit into the standings.

  python3 scripts/viral_intro.py find WORK [--hours 36] [--n 8]
      Lists the newest short clips from the viral-clip agencies on Dailymotion (WooGlobe, Jukin Media; YouTube and Reddit block
      cloud servers), downloads the --n best candidates (fail/funny titles first) into WORK/, and writes WORK/<id>.jpg contact
      sheets (one frame per 0.25 s, stamped with the clip time) plus WORK/candidates.json. Look at the sheets and pick ONE clip
      with a clear, funny impact moment (a fall, a crash, something breaking); note the impact time.
  python3 scripts/viral_intro.py build CLIP START IMPACT BASE.mp4 OUT.mp4
      Puts CLIP[START..IMPACT] (keep it 1.5-2.0 s, ending exactly on the impact frame) in front of BASE.mp4 (the rendered standings
      video): vertical clips sit over a blurred copy of themselves, a slow push-in, then a white flash, impact + whoosh + flash
      sounds on the cut, and the standings play in full after it.
Needs yt-dlp (pip install yt-dlp) and ffmpeg.
"""
import json, os, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); SFX = os.path.join(HERE, "..", "kit", "assets", "sfx")
OWNERS = ["WooGlobe", "JukinVideo"]   # Dailymotion usernames (Jukin Media posts as JukinVideo)
FUNNY = ("fail", "falls", "fall", "slip", "tumble", "crash", "knock", "smash", "faceplant", "breaks", "collapse", "drops", "wipeout",
         "lands", "flies", "ruins", "hits", "trips", "flip", "bounce", "goes wrong", "instantly")
SKIP = ("fire", "flood", "storm", "dies", "dead", "killed", "accident", "police", "war", "shooting", "injur", "hospital", "tornado")

def api(url):
    for i in range(3):
        try: return json.loads(urllib.request.urlopen(url, timeout=30).read())
        except Exception:
            if i == 2: raise
            time.sleep(3)

def find(work, hours, n):
    os.makedirs(work, exist_ok=True); since = int(time.time() - hours * 3600); vids = []
    for owner in OWNERS:
        for page in (1, 2, 3):
            try: d = api(f"https://api.dailymotion.com/user/{owner}/videos?sort=recent&limit=100&page={page}"
                    f"&fields=id,title,duration,created_time,views_total")
            except Exception as e: print(f"skipping {owner}: {e}", file=sys.stderr); break
            vids += [dict(v, owner=owner) for v in d.get("list", []) if v["created_time"] >= since]
            if not d.get("has_more"): break
    def score(v):
        t = v["title"].lower()
        if any(s in t for s in SKIP) or not (4 <= v["duration"] <= 70): return -1
        return sum(w in t for w in FUNNY) * 10 + min(v.get("views_total", 0), 5000) / 1000
    vids = sorted((v for v in vids if score(v) >= 0), key=score, reverse=True)[:n]
    import cv2, numpy as np
    for v in vids:
        f = os.path.join(work, v["id"] + ".mp4")
        if not os.path.exists(f):
            subprocess.run([sys.executable, "-m", "yt_dlp", "-q", "-f", "b", "-o", f, f"https://www.dailymotion.com/video/{v['id']}"])
        if not os.path.exists(f): continue
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", f, "-vf", "fps=4,scale=160:-2", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                             capture_output=True).stdout
        w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                        "-of", "csv=p=0", f], capture_output=True, text=True).stdout.split(",")[:2])
        hh = int(round(160 * h / w / 2)) * 2; fr = np.frombuffer(raw, np.uint8)[:len(raw) // (160 * hh * 3) * 160 * hh * 3].reshape(-1, hh, 160, 3)
        ims = [cv2.putText(x.copy(), f"{k / 4:.2f}", (3, 14), 0, 0.45, (0, 255, 255), 1) for k, x in enumerate(fr)]
        cols = 12; ims += [np.zeros_like(ims[0])] * (-len(ims) % cols)
        cv2.imwrite(os.path.join(work, v["id"] + ".jpg"), np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]))
        v["file"] = f; v["sheet"] = os.path.join(work, v["id"] + ".jpg")
    json.dump(vids, open(os.path.join(work, "candidates.json"), "w"), indent=1)
    for v in vids: print(f'{v["id"]}  {v["duration"]:>3}s  {v["owner"]:<10} {v["title"]}')

def build(clip, start, impact, base, out):
    start, impact = float(start), float(impact); L = impact - start
    w, h = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=width,height",
                                    "-of", "csv=p=0", clip], capture_output=True, text=True).stdout.split(",")[:2])
    if h > w * 0.75:   # vertical / square: centre it over a blurred copy of itself
        vid = (f"[0:v]fps=30,split[a][b];[a]scale=1920:-2,crop=1920:1080,boxblur=30:3,eq=brightness=-0.12[bg];"
               f"[b]scale=w=-2:h='1080*(1+0.10*t/{L})':eval=frame,crop=w='min(iw,1100)':h=1080:x='(iw-ow)/2':y='(ih-oh)*0.4'[fg];"
               f"[bg][fg]overlay=x='(W-w)/2':y=0")
    else:
        vid = (f"[0:v]fps=30,scale=w='1920*(1+0.10*t/{L})':h=-2:eval=frame,crop=1920:1080:x='(in_w-1920)/2':y='(in_h-1080)/2'")
    has_a = bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", clip],
                                capture_output=True, text=True).stdout.strip())
    ia = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.3,afade=t=out:st={L - 0.15:.3f}:d=0.15[ia];" if has_a else
          f"anullsrc=r=48000:cl=stereo,atrim=0:{L:.3f}[ia];")
    ms = int(L * 1000)
    fc = (f"{vid},setsar=1,format=yuv420p,fade=t=out:st={L - 0.12:.3f}:d=0.12:color=white[iv];"
          f"[1:v]fade=t=in:st=0:d=0.22:color=white,setsar=1,format=yuv420p[bv];[iv][bv]concat=n=2:v=1:a=0[v];"
          f"{ia}[1:a]aresample=48000,aformat=channel_layouts=stereo[ba];[ia][ba]concat=n=2:v=0:a=1[main];"
          f"[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms - 30}|{ms - 30},volume=0.95[hit];"
          f"[3:a]aresample=48000,aformat=channel_layouts=stereo,adelay={max(0, ms - 300)}|{max(0, ms - 300)},volume=0.5[wh];"
          f"[4:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms - 50}|{ms - 50},volume=0.5[fl];"
          f"[main][hit][wh][fl]amix=inputs=4:duration=first:normalize=0,alimiter=limit=0.95[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{L:.3f}", "-i", clip, "-i", base,
                    "-i", os.path.join(SFX, "deep-hit-3.mp3"), "-i", os.path.join(SFX, "whoosh-short-2.mp3"),
                    "-i", os.path.join(SFX, "vintage-flash.mp3"), "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out],
                   check=True)
    print("wrote", out)

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    if a[0] == "find":
        find(a[1], float(a[a.index("--hours") + 1]) if "--hours" in a else 36, int(a[a.index("--n") + 1]) if "--n" in a else 8)
    elif a[0] == "build": build(*a[1:6])
    else: sys.exit(__doc__)
