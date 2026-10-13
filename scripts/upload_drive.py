#!/usr/bin/env python3
"""Upload a daily MP4 and its Social HQ caption metadata to the same Drive folder.

Usage: python scripts/upload_drive.py out/YYYY-MM-DD.mp4 [data/YYYY-MM-DD.json]
Existing workflow invocation is unchanged. Captions are built from that day's data,
not required from Claude. HQ imports them as drafts requiring owner review.
"""
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

API = 'https://www.googleapis.com'
DATE_FILE = re.compile(r'\d{4}-\d{2}-\d{2}\.json')
NO_REPEAT_DAYS = 7

# Caption openings: (id, kind, wording for that day's video, wording when the video is from an earlier date,
# facts it needs). The dated wording replaces "today"/"now"/"tonight" with the video's own date.
# needs: 'increase' = the pool grew since the previous snapshot of the same round, 'same_leader' / 'new_leader'
# = compared with that snapshot, 'stream' = data says tonight's stream is confirmed (that day's video only).
OPENINGS = [
    ('board-reveal', 'board', 'And today’s leaderboard is… 👀', 'And the {date} leaderboard is… 👀', ()),
    ('board-checkin', 'board', 'Your daily leaderboard check-in.', 'Your leaderboard check-in for {date}.', ()),
    ('board-stands', 'board', 'Here’s where everyone stands today.', 'Here’s where everyone stood on {date}.', ()),
    ('board-in', 'board', 'Today’s standings are in.', 'The standings from {date}.', ()),
    ('board-update', 'board', 'Leaderboard update 📊', 'Leaderboard update for {date} 📊', ()),
    ('board-top5', 'board', 'Today’s top 5 on the leaderboard.', 'The top 5 on {date}.', ()),
    ('board-checking', 'board', 'Checking in on the leaderboard.', 'Checking in on the leaderboard for {date}.', ()),
    ('board-quicklook', 'board', 'Quick look at today’s standings.', 'A quick look at the {date} standings.', ()),
    ('board-latest', 'board', 'The latest from the leaderboard.', 'The leaderboard as of {date}.', ()),
    ('board-fresh', 'board', 'Fresh standings for today.', 'Standings as of {date}.', ()),
    ('board-daily', 'board', 'Daily standings, freshly updated.', 'Daily standings for {date}.', ()),
    ('pool-now', 'pool', 'The prize pool is now {pool}.', 'The prize pool was {pool} on {date}.', ()),
    ('pool-newday', 'pool', 'New day. Updated standings. {pool} in the pool.', '{date}: updated standings, {pool} in the pool.', ()),
    ('pool-rightnow', 'pool', '{pool} in the prize pool right now.', '{pool} in the prize pool on {date}.', ()),
    ('pool-check', 'pool', 'Prize pool check: {pool} 💰', 'Prize pool check, {date}: {pool} 💰', ()),
    ('pool-sitting', 'pool', 'The pool’s sitting at {pool} today.', 'The pool sat at {pool} on {date}.', ()),
    ('pool-today', 'pool', 'Today’s prize pool: {pool}.', 'Prize pool on {date}: {pool}.', ()),
    ('pool-board', 'pool', 'Here’s the board, with {pool} in the pool.', 'The board on {date}, with {pool} in the pool.', ()),
    ('pool-line', 'pool', '{pool} on the line this round.', '{pool} on the line as of {date}.', ()),
    ('grow-grew', 'growth', 'The pool grew by {increase} since our last update.', '{date}: the pool grew by {increase} since the previous update.', ('increase',)),
    ('grow-bigger', 'growth', 'Another day, a bigger prize pool. {pool} and counting.', 'A bigger prize pool by {date}: {pool} and counting.', ('increase',)),
    ('grow-keeps', 'growth', 'The prize pool that keeps growing. Now at {pool}.', 'The prize pool kept growing: {pool} on {date}.', ('increase',)),
    ('grow-up', 'growth', 'Pool’s up {increase} since the last update 📈', 'Pool up {increase} by {date} 📈', ('increase',)),
    ('grow-added', 'growth', '{increase} added to the pool since last time.', '{increase} added to the pool by {date}.', ('increase',)),
    ('grow-climbing', 'growth', 'Still climbing: {pool} in the pool.', 'Still climbing on {date}: {pool} in the pool.', ('increase',)),
    ('lead-holding', 'leader', '{leader} is holding the top spot. Here’s the latest.', '{leader} held the top spot on {date}.', ('same_leader',)),
    ('lead-still', 'leader', '{leader} is still out in front 👑', '{leader} was still out in front on {date} 👑', ('same_leader',)),
    ('lead-new', 'leader', 'New name at the top: {leader} 👀', 'New name at the top on {date}: {leader} 👀', ('new_leader',)),
    ('lead-way', 'leader', '{leader} leads the way today.', '{leader} led the way on {date}.', ()),
    ('lead-pace', 'leader', '{leader} sets the pace on today’s board.', '{leader} set the pace on {date}.', ()),
    ('lead-topspot', 'leader', 'Top spot today: {leader}.', 'Top spot on {date}: {leader}.', ()),
    ('stream-before', 'stream', 'Quick leaderboard update before tonight’s stream.', None, ('stream',)),
    ('stream-check', 'stream', 'Standings check before tonight’s stream 🎥', None, ('stream',)),
    ('stream-ahead', 'stream', 'Here’s the board ahead of tonight’s stream.', None, ('stream',)),
]
# Which kind of caption leads on a given day (by date), so pool, board and leader posts mix.
# Leader posts are occasional; growth falls back to pool/board when the pool didn't grow.
KIND_CYCLE = ['board', 'pool', 'growth', 'board', 'leader', 'pool', 'growth']
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿]')


def _date_label(day):
    return dt.date.fromisoformat(day).strftime('%b %d').replace(' 0', ' ')


def _rank(day, key):
    return hashlib.sha256(f'{day}:{key}'.encode()).hexdigest()


def _valid_day(data):
    pool, top = data.get('pool'), data.get('top')
    return (not isinstance(pool, bool) and isinstance(pool, (int, float)) and math.isfinite(pool) and pool >= 0
            and isinstance(top, list) and top and isinstance(top[0], list) and len(top[0]) == 3
            and isinstance(top[0][0], str) and top[0][0].strip())


def _same_round(a, b):
    """Two snapshots are from the same round only when both name it and nothing contradicts that."""
    if not a.get('round') or a.get('round') != b.get('round'):
        return False
    return not (a.get('ends') and b.get('ends') and a['ends'] != b['ends'])


def _toronto_today():
    try:
        return dt.datetime.now(ZoneInfo('America/Toronto')).date()
    except ZoneInfoNotFoundError:
        return (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=5)).date()


def _choose_caption(data, day, history, previous, is_today):
    """Pick the opening and an optional second line. history: [(day, choice)] for earlier days, oldest first;
    previous: the latest earlier snapshot from the same round (or None)."""
    pool, leader = data['pool'], data['top'][0][0]
    increase = round(pool - previous['pool']) if previous else 0
    facts = {
        'increase': increase >= 1,
        'same_leader': bool(previous) and previous['top'][0][0] == leader,
        'new_leader': bool(previous) and previous['top'][0][0] != leader,
        'stream': is_today and data.get('stream_tonight') is True,
    }
    values = {'pool': f'${pool:,.0f}', 'increase': f'${increase:,}', 'leader': leader, 'date': _date_label(day)}

    cutoff = (dt.date.fromisoformat(day) - dt.timedelta(days=NO_REPEAT_DAYS)).isoformat()
    recent = [c for d, c in history if d >= cutoff]
    used = {c['opening'] for c in recent}
    yesterday_kind = recent[-1]['kind'] if recent else None
    leader_lately = any(c['mentions_leader'] for c in recent[-2:])
    question_lately = any(c['question'] for d, c in history if d >= (dt.date.fromisoformat(day) - dt.timedelta(days=6)).isoformat())

    # Kind order: today's slot in the cycle first; a confirmed stream leads; yesterday's kind and (after a
    # recent leader mention) leader posts go last.
    start = dt.date.fromisoformat(day).toordinal() % len(KIND_CYCLE)
    order = list(dict.fromkeys(KIND_CYCLE[start:] + KIND_CYCLE[:start]))
    demote = {yesterday_kind} | ({'leader'} if leader_lately else set())
    order = [k for k in order if k not in demote] + [k for k in order if k in demote]
    if facts['stream']:
        order.insert(0, 'stream')

    def eligible(o):
        return all(facts[need] for need in o[4]) and (is_today or o[3] is not None)

    pick = None
    for kind in order:
        options = sorted((o for o in OPENINGS if o[1] == kind and eligible(o) and o[0] not in used), key=lambda o: _rank(day, o[0]))
        if options:
            pick = options[0]
            break
    if pick is None:   # every eligible opening was used in the last week (only possible with very little variety)
        last_used = {c['opening']: d for d, c in history}
        pick = min((o for o in OPENINGS if eligible(o)), key=lambda o: (last_used.get(o[0], ''), _rank(day, o[0])))

    first = (pick[2] if is_today else pick[3]).format(**values)
    mentions = {k for k in ('pool', 'increase', 'leader') if '{' + k + '}' in (pick[2] if is_today else pick[3])}

    # Optional second line: a fact the opening didn't already give, or nothing.
    seconds = [('none', '')]
    if 'pool' not in mentions:
        seconds += [('pool', f'{values["pool"]} in the pool.'), ('pool-b', f'Prize pool: {values["pool"]}.')]
    ends = data.get('ends')
    if is_today and isinstance(ends, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', ends):
        left = (dt.date.fromisoformat(ends) - dt.date.fromisoformat(day)).days
        if left >= 0:
            seconds.append(('days', 'Last day of the round.' if left == 0 else f'{left} day{"" if left == 1 else "s"} left in the round.'))
    if 'leader' not in mentions and not leader_lately and int(_rank(day, 'leader-line'), 16) % 3 == 0:
        seconds.append(('leader', f'{leader} leads.' if is_today else f'{leader} was leading.'))
    if not question_lately and not EMOJI.search(first) and int(_rank(day, 'question'), 16) % 4 == 0:
        seconds.append(('question', 'Who’s making a move? 👀'))
    second = min(seconds, key=lambda s: _rank(day, 'second:' + s[0]))
    text = first if not second[1] else f'{first}\n{second[1]}'
    return {'text': text, 'opening': pick[0], 'kind': pick[1],
            'mentions_leader': 'leader' in mentions or second[0] == 'leader', 'question': second[0] == 'question'}


def _snapshots_before(day, data_dir):
    """Earlier daily data files (oldest first) that look valid; the caption history is rebuilt from these."""
    if not data_dir:
        return []
    out = []
    for p in sorted(Path(data_dir).glob('*.json')):
        if not DATE_FILE.fullmatch(p.name) or p.stem >= day:
            continue
        try:
            d = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(d, dict) and d.get('date') == p.stem and _valid_day(d):
            out.append(d)
    return out


def build_caption(data, day, data_dir=None, today=None):
    """Short 1-2 line caption from the day's real numbers. Earlier data files (same folder) give the history:
    the previous same-round snapshot for pool growth / leader changes, and the openings used in the last
    seven days, which are not repeated. Deterministic, so a rerun gives the same caption."""
    today = today or _toronto_today()
    history, earlier = [], []
    for snap in _snapshots_before(day, data_dir):
        prev = next((p for p in reversed(earlier) if _same_round(snap, p)), None)
        history.append((snap['date'], _choose_caption(snap, snap['date'], history, prev, is_today=True)))
        earlier.append(snap)
    prev = next((p for p in reversed(earlier) if _same_round(data, p)), None)
    return _choose_caption(data, day, history, prev, is_today=dt.date.fromisoformat(day) >= today)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def call(method, url, token=None, body=None, headers=None):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or parsed.netloc not in ('www.googleapis.com', 'oauth2.googleapis.com'):
        raise ValueError('Unexpected Google API destination')
    h = dict(headers or {})
    if token:
        h['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=600) as r:
            return r.headers, r.read()
    except urllib.error.HTTPError as e:
        # Never print token responses, credentials, or resumable session URLs.
        raise RuntimeError(f'Google {method} request failed: HTTP {e.code}') from None


def access_token():
    form = urllib.parse.urlencode({
        'client_id': os.environ['GDRIVE_CLIENT_ID'],
        'client_secret': os.environ['GDRIVE_CLIENT_SECRET'],
        'refresh_token': os.environ['GDRIVE_REFRESH_TOKEN'],
        'grant_type': 'refresh_token'}).encode()
    _, b = call('POST', 'https://oauth2.googleapis.com/token', body=form,
                headers={'Content-Type': 'application/x-www-form-urlencoded'})
    return json.loads(b)['access_token']


def build_metadata(data, day, data_dir=None, today=None):
    if data.get('date') != day or dt.date.fromisoformat(day).isoformat() != day:
        raise ValueError('Video date and source data date must match')
    pool, top = data.get('pool'), data.get('top')
    if isinstance(pool, bool) or not isinstance(pool, (int, float)) or not math.isfinite(pool) or pool < 0:
        raise ValueError('Source data needs a valid pool total')
    if not isinstance(top, list) or not top or not isinstance(top[0], list) or len(top[0]) != 3:
        raise ValueError('Source data needs the ranked leaderboard')
    leader = top[0][0]
    if not isinstance(leader, str) or not leader.strip() or len(leader) > 40 or '\n' in leader:
        raise ValueError('Use the displayed leaderboard name')
    summary = f'Prize pool: ${pool:,.0f}. {leader} currently leads the standings.'
    caption = build_caption(data, day, data_dir, today)['text']
    if sum(2 if ord(c) > 127 else 1 for c in caption) > 280:
        raise ValueError('Generated caption exceeds the X limit')
    return {'schemaVersion': 1, 'kind': 'video', 'title': f'Daily leaderboard | {day}',
            'summary': summary, 'keyPoints': [], 'caption': caption,
            'sourceUrl': 'https://dylanjames.gg/', 'creator': 'Claude daily video pipeline'}


def upload(tok, folder, name, mime, content):
    if not re.fullmatch(r'[\w.-]+', name) or not re.fullmatch(r'[\w-]+', folder):
        raise ValueError('Invalid Drive filename or folder')
    q = f"name = '{name}' and '{folder}' in parents and trashed = false"
    _, b = call('GET', f'{API}/drive/v3/files?' + urllib.parse.urlencode({
        'q': q, 'fields': 'nextPageToken,incompleteSearch,files(id,name)',
        'supportsAllDrives': 'true', 'includeItemsFromAllDrives': 'true', 'pageSize': 100}), tok)
    listing = json.loads(b)
    existing = listing.get('files', [])
    if listing.get('nextPageToken') or listing.get('incompleteSearch') or len(existing) > 1:
        raise ValueError(f'Duplicate or incomplete Drive match for {name}; no file replaced')
    meta = {'name': name, 'mimeType': mime}
    qs = 'uploadType=resumable&supportsAllDrives=true&fields=id,name,size,md5Checksum,webViewLink'
    if existing:
        method, url = 'PATCH', f'{API}/upload/drive/v3/files/{existing[0]["id"]}?{qs}'
    else:
        meta['parents'] = [folder]
        method, url = 'POST', f'{API}/upload/drive/v3/files?{qs}'
    hdr, _ = call(method, url, tok, json.dumps(meta).encode(), {
        'Content-Type': 'application/json; charset=UTF-8', 'X-Upload-Content-Type': mime,
        'X-Upload-Content-Length': str(len(content))})
    session = hdr.get('Location')
    if not session:
        raise RuntimeError('Drive did not return an upload session')
    _, b = call('PUT', session, tok, content, {'Content-Type': mime, 'Content-Length': str(len(content))})
    res = json.loads(b)
    checksum = hashlib.md5(content).hexdigest()
    if int(res.get('size', -1)) != len(content) or res.get('md5Checksum') != checksum:
        raise RuntimeError(f'Drive verification failed for {name}')
    print(f'{"replaced" if existing else "uploaded"} {name}; size and MD5 verified')
    return res


def main(path, data_path=None):
    missing = [k for k in ('GDRIVE_CLIENT_ID', 'GDRIVE_CLIENT_SECRET', 'GDRIVE_REFRESH_TOKEN', 'GDRIVE_FOLDER_ID') if not os.environ.get(k)]
    if missing:
        raise ValueError(f'Drive settings missing: {", ".join(missing)}')
    video = Path(path)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}\.mp4', video.name):
        raise ValueError('Name the daily video YYYY-MM-DD.mp4')
    source = Path(data_path) if data_path else Path(__file__).resolve().parents[1] / 'data' / f'{video.stem}.json'
    metadata = build_metadata(json.loads(source.read_text()), video.stem, data_dir=source.parent)
    tok, folder = access_token(), os.environ['GDRIVE_FOLDER_ID']
    uploaded = upload(tok, folder, video.name, 'video/mp4', video.read_bytes())
    metadata.update(driveFileId=uploaded['id'], mediaChecksum=uploaded['md5Checksum'])
    sidecar = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')
    upload(tok, folder, f'{video.stem}.hq.json', 'application/json', sidecar)
    print('Video and matching caption metadata ready for Social HQ intake; no social post created.')


if __name__ == '__main__':
    try:
        main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    except (ValueError, RuntimeError, OSError, KeyError) as e:
        sys.exit(str(e))
