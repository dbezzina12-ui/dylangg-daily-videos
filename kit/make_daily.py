#!/usr/bin/env python3
"""Render the daily DylanGG progressive-leaderboard video.

  python3 make_daily.py --pool 13053 --main 11748 --raffle 652 --multi 652 \
      --round 01 --ends 2026-10-15 --today 2026-10-10 \
      --top '[["Inne****",276431.57,4111],["Jame********",108574.22,1762],...]' --out /path/to/outdir

--style standings (default): "Live Standings" (14 s): pool odometer, top-5 board, days-left flip clock, end card.
--style pool: "Pool Update" (13.5 s): pool counter, 3 ways to win with amounts, round end, end card.
Writes <out>/Leaderboard-<Style>-<today>-16x9.mp4 and -4x5.mp4 (30 fps, AAC), QA contact sheets
<out>/qa-16x9.png and <out>/qa-4x5.png, and prints a JSON summary.
Exits with code 2 (renders nothing) if the numbers don't hold together: 90 / 5 / 5 split of the pool,
and for standings a top list in rank order (wagered and prizes descending, prizes inside the main pool).
"""
import argparse, datetime as dt, json, os, subprocess, sys, time
from urllib.parse import urlencode

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render  # noqa: E402

FORMATS = {'h': '16x9', 'p': '4x5'}
DOW = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
MON = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']


def label(d, dow=False):
    s = f'{MON[d.month - 1]} {d.day}'
    return f'{DOW[d.weekday()]} {s}' if dow else s


def check(pool, main, raffle, multi):
    """the site splits the pool 90 / 5 / 5 (rounded) -- refuse numbers that don't add up"""
    errs = []
    if pool < 10000: errs.append(f'pool {pool} is below the $10,000 starting pool')
    tol = max(3, pool * 0.004)
    if abs(main - pool * 0.90) > tol: errs.append(f'main {main} is not ~90% of pool {pool} ({pool * 0.9:.0f})')
    for nm, v in (('raffle', raffle), ('multi', multi)):
        if abs(v - pool * 0.05) > tol: errs.append(f'{nm} {v} is not ~5% of pool {pool} ({pool * 0.05:.0f})')
    if abs(main + raffle + multi - pool) > tol: errs.append(f'prizes add to {main + raffle + multi}, pool is {pool}')
    return errs


def check_top(top, main):
    errs = []
    if not top: return ['no leaderboard rows given']
    for i, r in enumerate(top):
        if len(r) != 3 or not str(r[0]).strip(): errs.append(f'row {i + 1} is not [name, wagered, prize]: {r}'); continue
        if not (r[1] >= 0 and r[2] >= 0): errs.append(f'row {i + 1} has a negative number: {r}')
    if errs: return errs
    for i in range(1, len(top)):
        if top[i][1] > top[i - 1][1]: errs.append(f'wagered not descending at rank {i + 1}')
        if top[i][2] > top[i - 1][2]: errs.append(f'prizes not descending at rank {i + 1}')
    if sum(r[2] for r in top) > main + 3: errs.append(f'top prizes add to more than the main pool {main}')
    return errs


def probe(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration,size:stream=codec_type,width,height',
                          '-of', 'json', path], capture_output=True, text=True, check=True).stdout
    j = json.loads(out); v = [s for s in j['streams'] if s['codec_type'] == 'video'][0]
    return {'duration': round(float(j['format']['duration']), 2), 'mb': round(int(j['format']['size']) / 1e6, 1),
            'size': f"{v['width']}x{v['height']}", 'audio': any(s['codec_type'] == 'audio' for s in j['streams'])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pool', type=float, required=True)
    ap.add_argument('--main', type=float); ap.add_argument('--raffle', type=float); ap.add_argument('--multi', type=float)
    ap.add_argument('--round', default='')
    ap.add_argument('--ends', default='', help='round end date YYYY-MM-DD (blank = hide)')
    ap.add_argument('--today', default=dt.date.today().isoformat())
    ap.add_argument('--out', required=True)
    ap.add_argument('--formats', default='h,p')
    ap.add_argument('--force', action='store_true', help='render even if the 90/5/5 check fails')
    ap.add_argument('--qa-only', action='store_true', help='only write the QA contact sheets')
    ap.add_argument('--style', choices=['standings', 'pool'], default='standings')
    ap.add_argument('--top', default='', help='JSON list of up to 5 [name, wagered, prize] rows in rank order (standings)')
    ap.add_argument('--intro', type=int, default=None, help='intro style 0-3 (default: rotates with the date)')
    ap.add_argument('--date-name', action='store_true', help='name the 16:9 file just <today>.mp4 (4:5 becomes <today>-4x5.mp4)')
    ap.add_argument('--no-plate', action='store_true', help='standings: ignore assets/plate.mp4 and use the drawn black stage')
    a = ap.parse_args()

    pool = round(a.pool)
    main_ = round(a.main if a.main is not None else pool * 0.9)
    raffle = round(a.raffle if a.raffle is not None else pool * 0.05)
    multi = round(a.multi if a.multi is not None else pool * 0.05)
    errs = check(pool, main_, raffle, multi)
    top = []
    if a.style == 'standings':
        try: top = [[str(r[0]), float(r[1]), float(r[2])] for r in json.loads(a.top or '[]')][:5]
        except Exception as e: errs.append(f'--top is not valid JSON rows: {e}')
        errs += check_top(top, main_) if not errs else []
    if errs and not a.force:
        print(json.dumps({'ok': False, 'errors': errs})); sys.exit(2)

    today = dt.date.fromisoformat(a.today)
    q = {'pool': pool, 'main': main_, 'raffle': raffle, 'multi': multi, 'date': label(today, True), 'round': a.round}
    plate = os.path.join(HERE, 'assets', 'plate.mp4')
    plate = plate if (a.style == 'standings' and not a.no_plate and os.path.exists(plate)) else None
    if plate: q['plate'] = 1          # graphics render transparent and are composited over the Higgsfield footage plate
    if a.style == 'standings':
        q['top'] = json.dumps(top, separators=(',', ':'))
        day = today.toordinal()                     # the intro changes every day: 4 styles, 5 headlines for the slam style
        q['intro'] = a.intro if a.intro is not None else day % 4
        q['head'] = (day // 4) % 5
    page, audio, dur, name, qt = (('standings.html', 'audio_standings.py', 14.0, 'Live-Standings', [0.8, 3.3, 6.0, 7.8, 10.2, 12.9])
                                  if a.style == 'standings' else
                                  ('index.html', 'audio.py', 13.5, 'Pool-Update', [0.9, 3.0, 4.6, 7.8, 9.8, 12.9]))
    if a.ends:
        ends = dt.date.fromisoformat(a.ends); left = (ends - today).days
        if left >= 0: q.update({'ends': label(ends), 'left': left})
        else: q.update({'ends': '', 'left': -1})       # stale round dates: fall back to the BI-WEEKLY card
    else:
        q.update({'ends': '', 'left': -1})
    os.makedirs(a.out, exist_ok=True)
    wav = os.path.join(a.out, 'audio.wav')
    subprocess.run([sys.executable, os.path.join(HERE, audio), wav, str(dur)], check=True)

    res = {'ok': True, 'style': a.style, 'plate': bool(plate), 'numbers': {'pool': pool, 'main': main_, 'raffle': raffle, 'multi': multi, 'top': top}, 'query': q, 'files': {}}
    for f in a.formats.split(','):
        tag = FORMATS[f]; query = urlencode({'fmt': f, **q})
        qa = os.path.join(a.out, f'qa-{tag}.png')
        render.stills(qa, query, qt, cols=6 if f == 'p' else 3, thumb=540, page=page, plate=plate if f == 'h' else None)
        res['files'][f'qa-{tag}'] = qa
        if a.qa_only: continue
        fn = (f'{today.isoformat()}.mp4' if f == 'h' else f'{today.isoformat()}-{tag}.mp4') if a.date_name else f'Leaderboard-{name}-{today.isoformat()}-{tag}.mp4'
        mp4 = os.path.join(a.out, fn)
        t0 = time.time(); render.video(mp4, wav, query, page=page, plate=plate if f == 'h' else None)
        info = probe(mp4); info['render_s'] = round(time.time() - t0)
        if abs(info['duration'] - dur) > 0.2 or not info['audio']: res['ok'] = False
        res['files'][tag] = {'path': mp4, **info}
    os.remove(wav)
    print(json.dumps(res, indent=1))
    sys.exit(0 if res['ok'] else 3)


if __name__ == '__main__':
    main()
