#!/usr/bin/env python3
"""Render the day described by a data file with the kit.

  usage: python3 scripts/render_day.py data/2026-10-10.json out/
  writes out/2026-10-10.mp4 (16:9, 14 s) and out/qa-16x9.png

Intro text: the data file's "headline" (1-2 short lines, written fresh each morning) is used when it is valid
and hasn't been used in the last 14 data files. Otherwise a headline is built from the day's own numbers
(pool growth since the previous file, the leader's margin, days left, ...), rotating by date and skipping
anything used in the last 14 days, so the intro text is different every day either way.
"""
import datetime as dt, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.join(HERE, '..', 'kit')
sys.path.insert(0, KIT)
from make_daily import parse_headline  # noqa: E402  (same rules the renderer enforces)

LOOKBACK = 14


def usd(v): return '$' + f'{round(v):,}'


def usd_k(v):
    v = round(v)
    if v >= 1_000_000: return f'${v / 1e6:.1f}M'.replace('.0M', 'M')
    if v >= 10_000: return f'${round(v / 1000)}K'
    return usd(v)


def history(data_dir, day):
    """earlier data files (newest first), up to LOOKBACK"""
    out = []
    for p in sorted(glob.glob(os.path.join(data_dir, '*.json')), reverse=True):
        nm = os.path.basename(p)[:-5]
        if nm >= day: continue
        try: out.append(json.load(open(p)))
        except Exception: continue
        if len(out) >= LOOKBACK: break
    return out


def norm(lines): return ' | '.join(x.strip().upper() for x in lines)


def sig(lines): return ''.join('#' if ch.isdigit() else ch for ch in norm(lines))   # same kind of line, numbers aside


def candidates(d, prev, left, day):
    """factual one/two-liners from today's numbers. Fixed order; the date picks where to start, so the kind
    of headline moves on every day. Kinds that don't apply today (no growth, no round end, ...) are skipped."""
    top, pool = d['top'], d['pool']
    lead = str(top[0][0]).upper()
    since = None
    if prev and pool > prev.get('pool', pool):
        yday = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        since = 'SINCE YESTERDAY' if prev.get('date') == yday else 'SINCE LAST UPDATE'
    c = [
        ['+' + usd(pool - prev['pool']), since] if since else None,
        [f'{lead} LEADS', f'BY {usd_k(top[0][1] - top[1][1])}'] if len(top) >= 2 else None,
        [f'{usd(pool)} POOL', 'AND CLIMBING'] if since else [usd(pool), 'IN THE POOL'],   # the pool card already says NO MAX CAP
        ([f'{left} DAY{"S" if left != 1 else ""} LEFT', 'TO CATCH UP'] if left >= 1 else ['FINAL DAY', 'OF THE ROUND']) if left is not None else None,
        [f'#1 IS ON {usd(top[0][2])}', 'RIGHT NOW'],
        [f'{usd_k(sum(r[1] for r in top))} WAGERED', 'BY THE TOP 5'],
        [f'#5 IS ON {usd(top[4][2])}', 'WHO TAKES IT?'] if len(top) >= 5 else None,
        [f'RAFFLE: {usd(d["raffle"])}', f'MULTI: {usd(d["multi"])}'],
    ]
    return [x if x and not parse_headline('|'.join(x))[1] else None for x in c]


def pick_headline(d, day, data_dir):
    hist = history(data_dir, day)
    recorded = [h['headline'] for h in hist if isinstance(h.get('headline'), list)]
    used = {norm(h) for h in recorded}
    given = d.get('headline')
    if isinstance(given, list) and given:
        lines, errs = parse_headline('|'.join(map(str, given)))
        if not errs and norm(lines) not in used: return lines, 'data file'
        print(f'headline {given!r} not used: {"; ".join(errs) or "repeats one from the last 14 days"}', file=sys.stderr)
    left = None
    if d.get('ends'):
        left = (dt.date.fromisoformat(d['ends']) - dt.date.fromisoformat(day)).days
        if left < 0: left = None
    prev = hist[0] if hist else None
    lead = str(d['top'][0][0]).upper()
    if prev and prev.get('top') and str(prev['top'][0][0]).upper() != lead:   # a new leader beats everything else
        x = ['NEW #1:', lead]
        if not parse_headline('|'.join(x))[1] and norm(x) not in used: return x, 'generated'
    c = candidates(d, prev, left, day)
    recent = {sig(h) for h in recorded[:3]}
    k = dt.date.fromisoformat(day).toordinal()
    order = [c[(k + i) % len(c)] for i in range(len(c))]
    for strict in (True, False):
        for x in order:
            if x and norm(x) not in used and (not strict or sig(x) not in recent): return x, 'generated'
    return next(x for x in order if x), 'generated (all recent)'


def main():
    src, out = sys.argv[1], sys.argv[2]
    d = json.load(open(src))
    day = os.path.basename(src)[:-len('.json')]
    if d.get('date') != day: sys.exit(f'{src}: "date" is {d.get("date")!r}, expected {day!r}')
    for k in ('pool', 'main', 'raffle', 'multi', 'top'):
        if k not in d: sys.exit(f'{src}: missing "{k}"')
    hl, how = pick_headline(d, day, os.path.dirname(os.path.abspath(src)))
    # intro style rotates with the date; switch to the plain slam when the headline would clash with it
    intro = dt.date.fromisoformat(day).toordinal() % 4
    text = ' '.join(hl)
    if intro == 2 and (usd(d['pool'])[1:] in text or usd_k(d['pool']) in text): intro = 0   # scramble hides the pool total
    if intro == 3 and 'DAY' in text: intro = 0                                              # countdown already says days left
    print(f'intro {intro}, headline ({how}): {" / ".join(hl)}', flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as f: f.write(f'**{day}** intro {intro} · headline ({how}): `{" / ".join(hl)}`\n')
    args = [sys.executable, os.path.join(KIT, 'make_daily.py'), '--style', 'standings', '--formats', 'h', '--date-name',
            '--today', day, '--out', out, '--pool', str(d['pool']), '--main', str(d['main']), '--raffle', str(d['raffle']),
            '--multi', str(d['multi']), '--top', json.dumps(d['top']), '--headline', '|'.join(hl), '--intro', str(intro)]
    if d.get('ends'): args += ['--ends', d['ends']]
    if d.get('round'): args += ['--round', str(d['round'])]
    sys.exit(subprocess.run(args).returncode)   # 2 = numbers failed the checks (nothing rendered), 3 = output check failed


if __name__ == '__main__':
    main()
