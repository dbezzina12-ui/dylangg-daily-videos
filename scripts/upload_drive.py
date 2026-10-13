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

API = 'https://www.googleapis.com'


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


def build_metadata(data, day):
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
    date = dt.date.fromisoformat(day).strftime('%b %d, %Y').replace(' 0', ' ')
    summary = f'Prize pool: ${pool:,.0f}. {leader} currently leads the standings.'
    caption = f'{date} leaderboard update\n\n{summary}\n\nWho finishes on top?'
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
    metadata = build_metadata(json.loads(source.read_text()), video.stem)
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
