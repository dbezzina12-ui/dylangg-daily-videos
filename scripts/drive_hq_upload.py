#!/usr/bin/env python3
"""Daily video -> 1001 Clips, through Dylan's Apps Script uploader (no Google credentials needed here).

  python scripts/drive_hq_upload.py pull-history data/
      Copies the recent daily data the uploader keeps (pool, round, leader, headline...) into data/ as
      YYYY-MM-DD.json files, without overwriting files already there. Run before writing the headline,
      so headline and caption rules can see the last few days.

  python scripts/drive_hq_upload.py upload OUT/YYYY-MM-DD.mp4 data/YYYY-MM-DD.json [--video-id DRIVE_ID]
      Uploads the MP4, then YYYY-MM-DD.hq.json (Social HQ caption metadata: the same format as
      upload_drive.py, with the uploaded video's Drive ID and MD5), then stores the day's data in the
      uploader's history. --video-id: the MP4 is already in Drive (e.g. the metadata step failed); only the
      metadata is uploaded and linked to that ID.

  python scripts/drive_hq_upload.py metadata data/YYYY-MM-DD.json
      Adds YYYY-MM-DD.hq.json for a YYYY-MM-DD.mp4 that's already in 1001 Clips, without the video file:
      the uploader looks up its Drive ID and MD5. Also stores the day's data in the history.

Needs HYPE_UPLOAD_KEY in the environment. The key is never printed. Older uploader versions without
history still work: the upload goes through and captions use whatever history is in data/.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload_drive import build_metadata  # noqa: E402  (same caption builder and metadata format)

UPLOADER = os.environ.get('HYPE_UPLOAD_URL') or (
    'https://script.google.com/macros/s/AKfycbxnQKMIk9GTq1iRRNhjx7GmkTeIADc6oN6pvU-Qgwh3UwbHx7PLJxN6ApN2jEczHVFU/exec')
DAY_JSON = re.compile(r'\d{4}-\d{2}-\d{2}\.json')


def ask(payload):
    """POST to the Apps Script uploader; returns its JSON reply."""
    key = os.environ.get('HYPE_UPLOAD_KEY')
    if not key:
        raise RuntimeError('HYPE_UPLOAD_KEY is not set in this environment')
    body = json.dumps({**payload, 'key': key}).encode()
    req = urllib.request.Request(UPLOADER, data=body, method='POST', headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'uploader request failed: HTTP {e.code}') from None


def send(name, mime, content):
    """Upload one file into 1001 Clips. Returns Drive's file record; checks name, and size/MD5 when Drive reports them."""
    r = ask({'name': name, 'size': len(content), 'mimeType': mime})
    if not r.get('ok'):
        raise RuntimeError(f'uploader refused {name}: {r.get("error")}')
    target = urllib.parse.urlsplit(r.get('uploadUrl') or '')
    if target.scheme != 'https' or target.netloc != 'www.googleapis.com':
        raise RuntimeError('uploader returned an unexpected upload address')
    req = urllib.request.Request(r['uploadUrl'], data=content, method='PUT',
                                 headers={'Content-Type': mime, 'Content-Length': str(len(content))})
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            res = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'Drive upload of {name} failed: HTTP {e.code}') from None
    md5 = hashlib.md5(content).hexdigest()
    if not res.get('id') or res.get('name') != name:
        raise RuntimeError(f'Drive did not confirm {name}')
    if ('size' in res and int(res['size']) != len(content)) or ('md5Checksum' in res and res['md5Checksum'] != md5):
        raise RuntimeError(f'Drive verification failed for {name}')
    res['md5'] = md5
    res['replaced'] = bool(r.get('replaced'))
    return res


def history():
    """Recent daily data kept by the uploader, or None when this uploader version doesn't keep any."""
    r = ask({'action': 'history'})
    if r.get('ok') and isinstance(r.get('history'), list):
        return r['history']
    return None


def pull_history(data_dir):
    days = history()
    if days is None:
        print('history: not available from this uploader version (captions use the files already in data/)')
        return 0
    data_dir = Path(data_dir)
    added = 0
    for d in days:
        name = f'{d.get("date")}.json'
        if isinstance(d, dict) and DAY_JSON.fullmatch(name) and not (data_dir / name).exists():
            (data_dir / name).write_text(json.dumps(d, indent=2))
            added += 1
    print(f'history: {len(days)} recent days on record, {added} added to {data_dir}')
    return added


def upload(video_path, data_path, video_id=None):
    video, source = Path(video_path), Path(data_path)
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}\.mp4', video.name):
        raise ValueError('Name the daily video YYYY-MM-DD.mp4')
    data = json.loads(source.read_text())
    metadata = build_metadata(data, video.stem, data_dir=source.parent)   # validates before anything is uploaded

    content = video.read_bytes()
    if video_id:
        vid = {'id': video_id, 'md5': hashlib.md5(content).hexdigest(), 'replaced': None}
        print(f'video: using {video.name} already in Drive ({video_id})')
    else:
        vid = send(video.name, 'video/mp4', content)
        print(f'video: {"replaced" if vid["replaced"] else "uploaded"} {video.name} ({vid["id"]})')

    metadata.update(driveFileId=vid['id'], mediaChecksum=vid['md5'])
    sidecar = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')
    meta = send(f'{video.stem}.hq.json', 'application/json', sidecar)
    print(f'metadata: {"replaced" if meta["replaced"] else "uploaded"} {video.stem}.hq.json ({meta["id"]})')
    print('caption: ' + metadata['caption'].replace('\n', ' / '))

    remember(data)
    return vid['id'], meta['id'], metadata['caption']


def remember(data):
    r = ask({'action': 'remember', 'entry': data}) if history() is not None else None
    print('history: ' + ('saved this day\'s numbers' if r and r.get('ok') else 'not kept by this uploader version'))


def metadata_only(data_path):
    """Caption metadata for a daily video that's already in 1001 Clips (ID and MD5 come from Drive)."""
    source = Path(data_path)
    data = json.loads(source.read_text())
    day = data.get('date', '')
    metadata = build_metadata(data, day, data_dir=source.parent)
    info = ask({'action': 'file', 'name': f'{day}.mp4'})
    if not info.get('ok'):
        raise RuntimeError(f'uploader could not find {day}.mp4: {info.get("error")}')
    if not info.get('id') or not re.fullmatch(r'[0-9a-f]{32}', str(info.get('md5Checksum', ''))):
        raise RuntimeError('this needs the updated uploader script (it reports file IDs and checksums)')
    metadata.update(driveFileId=info['id'], mediaChecksum=info['md5Checksum'])
    sidecar = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')
    meta = send(f'{day}.hq.json', 'application/json', sidecar)
    print(f'metadata: {"replaced" if meta["replaced"] else "uploaded"} {day}.hq.json ({meta["id"]}) for {day}.mp4 ({info["id"]})')
    print('caption: ' + metadata['caption'].replace('\n', ' / '))
    remember(data)
    return info['id'], meta['id'], metadata['caption']


if __name__ == '__main__':
    try:
        args = sys.argv[1:]
        if args[:1] == ['pull-history'] and len(args) == 2:
            pull_history(args[1])
        elif args[:1] == ['upload'] and len(args) in (3, 5) and (len(args) == 3 or args[3] == '--video-id'):
            upload(args[1], args[2], args[4] if len(args) == 5 else None)
        elif args[:1] == ['metadata'] and len(args) == 2:
            metadata_only(args[1])
        else:
            sys.exit(__doc__)
    except (ValueError, RuntimeError, OSError, KeyError) as e:
        sys.exit(str(e))
