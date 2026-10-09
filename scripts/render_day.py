#!/usr/bin/env python3
"""Render the day described by a data file with the kit.

  usage: python3 scripts/render_day.py data/2026-10-10.json out/
  writes out/2026-10-10.mp4 (16:9, 14 s) and out/qa-16x9.png
"""
import json, os, subprocess, sys

src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src))
day = os.path.basename(src)[:-len('.json')]
if d.get('date') != day: sys.exit(f'{src}: "date" is {d.get("date")!r}, expected {day!r}')
for k in ('pool', 'main', 'raffle', 'multi', 'top'):
    if k not in d: sys.exit(f'{src}: missing "{k}"')
kit = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'kit')
args = [sys.executable, os.path.join(kit, 'make_daily.py'), '--style', 'standings', '--formats', 'h', '--date-name',
        '--today', day, '--out', out, '--pool', str(d['pool']), '--main', str(d['main']), '--raffle', str(d['raffle']),
        '--multi', str(d['multi']), '--top', json.dumps(d['top'])]
if d.get('ends'): args += ['--ends', d['ends']]
if d.get('round'): args += ['--round', str(d['round'])]
sys.exit(subprocess.run(args).returncode)   # 2 = numbers failed the checks (nothing rendered), 3 = output check failed
