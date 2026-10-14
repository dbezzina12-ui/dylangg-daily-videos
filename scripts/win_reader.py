#!/usr/bin/env python3
"""Find big slot wins in a stream VOD by reading the game's own numbers (RapidOCR, CPU only).

  python scripts/win_reader.py read VOD.ts reads.json [--every 2] [--game 38,230,1288,695] [--workers 4]
      Samples the game window every N seconds and reads the BET, WIN / TOTAL WIN and BALANCE fields
      (the label, then the number under or beside it) plus any big popup numbers.
  python scripts/win_reader.py rank reads.json [--top 15] [--min-x 50]
      Lists the biggest wins: each WIN value divided by the bet in play, merged within 30 s, with the
      stream time, so the edit can start from the right moment.

Works at 480p and up (the game rect is given in 1920x1080 stream coordinates and scaled to the video).
Needs: pip install rapidocr_onnxruntime (its models ship inside the wheel; nothing is downloaded).
"""
import json
from multiprocessing import Pool
import re
import subprocess
import sys

import numpy as np

NUM = re.compile(r'^(?:C?\$|CA\$|€|£)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)$')
_ocr = None


def number(text):
    m = NUM.match(text.replace(' ', '').replace('O', '0'))
    if not m:
        return None
    digits = m.group(1)
    if ',' in digits and not re.fullmatch(r'\d{1,3}(,\d{3})+(\.\d{1,2})?', digits):
        return None                                   # "1,23,4" is a misread, not a number
    try:
        return float(digits.replace(',', ''))
    except ValueError:
        return None


def label(text):
    t = re.sub(r'[^A-Z]', '', text.upper())
    if t in ('BET', 'TOTALBET', 'BETAMOUNT', 'STAKE'):
        return 'bet'
    if t in ('WIN', 'TOTALWIN', 'WINS', 'WINAMOUNT', 'TOTALWINS'):
        return 'win'
    if t in ('BALANCE', 'CREDIT', 'CASH'):
        return 'balance'
    return None


def parse(tokens):
    """tokens: [(x0, y0, x1, y1, text, conf)] in 1920x1080-scale game-window pixels -> field values."""
    labels = [(label(t[4]), t) for t in tokens if label(t[4])]
    values = [(number(t[4]), t) for t in tokens]
    values = [(v, t) for v, t in values if v is not None]
    out = {}
    for kind, L in labels:
        lx, ly = (L[0] + L[2]) / 2, (L[1] + L[3]) / 2
        h = max(8.0, L[3] - L[1])
        best = None
        for v, t in values:
            vx, vy = (t[0] + t[2]) / 2, (t[1] + t[3]) / 2
            below = 0 < vy - ly < 3.2 * h and abs(vx - lx) < 140
            beside = abs(vy - ly) < 0.8 * h and 0 < t[0] - L[2] < 260
            if below or beside:
                d = abs(vx - lx) + abs(vy - ly)
                if best is None or d < best[0]:
                    best = (d, v)
        if best and kind not in out:
            out[kind] = best[1]
    big = [v for v, t in values if (t[3] - t[1]) >= 40 and '.' in t[4] and v >= 1]   # popup amounts: tall, with cents
    if big:
        out['big'] = max(big)
    return out


def _init():
    global _ocr
    from rapidocr_onnxruntime import RapidOCR
    _ocr = RapidOCR()


def _read(job):
    t, img = job
    res, _ = _ocr(img)
    toks = []
    for box, text, conf in res or []:
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        toks.append((min(xs), min(ys), max(xs), max(ys), text, float(conf)))
    return {'t': t, **parse(toks)}


def frames(video, every, game):
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                            '-of', 'csv=p=0', video], capture_output=True, text=True).stdout.split()[0].split(',')
    W, H = int(probe[0]), int(probe[1])
    s = W / 1920
    gx, gy, gw, gh = [round(v * s) for v in game]
    ow, oh = 1288, round(1288 * gh / gw)             # read at stream scale: OCR likes ~30 px digits
    cmd = ['ffmpeg', '-v', 'error', '-i', video, '-vf', f'fps=1/{every},crop={gw}:{gh}:{gx}:{gy},scale={ow}:{oh}:flags=lanczos',
           '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = 0
    while True:
        buf = p.stdout.read(ow * oh * 3)
        if len(buf) < ow * oh * 3:
            break
        yield n * every, np.frombuffer(buf, np.uint8).reshape(oh, ow, 3)
        n += 1


def read(video, out, every=2.0, game=(38, 230, 1288, 695), workers=4):
    rows = []
    with Pool(workers, initializer=_init) as pool:
        for i, r in enumerate(pool.imap(_read, frames(video, every, game), chunksize=4)):
            rows.append(r)
            if i % 300 == 0:
                print(f'read {r["t"] / 60:.0f} min', flush=True)
    json.dump(rows, open(out, 'w'))
    print(f'{len(rows)} samples -> {out}')


def clock(t):
    t = int(t)
    return f'{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}'


def rank(reads, top=15, min_x=50.0):
    """Biggest wins by the game's own WIN / TOTAL WIN field (popups, buy menus and lobby jackpots alone never count).
    A popup number only adds the moment it appeared, when the WIN field confirms it within 40 s."""
    rows = json.load(open(reads))
    bet = None
    hits = []
    for r in rows:
        if r.get('bet') and 0.1 <= r['bet'] <= 1000:
            bet = r['bet']
        v = r.get('win')
        if bet and v and v / bet >= min_x and v <= 100_000:
            hits.append({'t': r['t'], 'win': v, 'bet': bet, 'x': v / bet})
    hits.sort(key=lambda h: -h['x'])
    picked = []
    for h in hits:                                   # one entry per bonus: keep the biggest reading within 60 s
        if all(abs(h['t'] - p['t']) > 60 for p in picked):
            picked.append(h)
    for h in picked:
        pops = [r for r in rows if r.get('big') and 0 < h['t'] - r['t'] <= 40 and 0.5 <= r['big'] / h['win'] <= 1.05]
        h['popup_t'] = pops[0]['t'] if pops else None
    out = sorted(picked[:top], key=lambda h: h['t'])
    for h in out:
        pop = f"  popup from {clock(h['popup_t'])}" if h['popup_t'] is not None else ''
        print(f"{clock(h['t'])}  ${h['win']:>9,.2f} on ${h['bet']:,.2f}  = {h['x']:>6,.0f}x{pop}")
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    opt = lambda k, d: type(d)(a[a.index(k) + 1]) if k in a else d
    if a[:1] == ['read'] and len(a) >= 3:
        game = tuple(int(v) for v in opt('--game', '38,230,1288,695').split(','))
        read(a[1], a[2], opt('--every', 2.0), game, opt('--workers', 4))
    elif a[:1] == ['rank'] and len(a) >= 2:
        rank(a[1], opt('--top', 15), opt('--min-x', 50.0))
    else:
        sys.exit(__doc__)
