#!/usr/bin/env python3
"""Upload one MP4 into a Google Drive folder, replacing a file of the same name.

  env:   GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN  (OAuth client + refresh token, scope .../auth/drive)
         GDRIVE_FOLDER_ID  (1001 Clips = 1waRIY_FHC3KJnmpEKEOgoLWfiL1d6xpT)
  usage: python3 scripts/upload_drive.py out/2026-10-10.mp4

Standard library only. Uses a resumable upload, then checks that Drive's size matches the local file.
"""
import json, os, sys, urllib.error, urllib.parse, urllib.request

API = 'https://www.googleapis.com'


def call(method, url, token=None, body=None, headers=None):
    h = dict(headers or {})
    if token: h['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.headers, r.read()
    except urllib.error.HTTPError as e:
        sys.exit(f'{method} {url.split("?")[0]} failed: HTTP {e.code} {e.read().decode(errors="replace")[:500]}')


def access_token():
    form = urllib.parse.urlencode({
        'client_id': os.environ['GDRIVE_CLIENT_ID'], 'client_secret': os.environ['GDRIVE_CLIENT_SECRET'],
        'refresh_token': os.environ['GDRIVE_REFRESH_TOKEN'], 'grant_type': 'refresh_token'}).encode()
    _, b = call('POST', 'https://oauth2.googleapis.com/token', body=form, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    return json.loads(b)['access_token']


def main(path):
    missing = [k for k in ('GDRIVE_CLIENT_ID', 'GDRIVE_CLIENT_SECRET', 'GDRIVE_REFRESH_TOKEN', 'GDRIVE_FOLDER_ID') if not os.environ.get(k)]
    if missing: sys.exit(f'Drive settings missing: {", ".join(missing)}. Add them in the repo: Settings > Secrets and variables > Actions.')
    name, size, folder = os.path.basename(path), os.path.getsize(path), os.environ['GDRIVE_FOLDER_ID']
    tok = access_token()
    q = f"name = '{name}' and '{folder}' in parents and trashed = false"
    _, b = call('GET', f'{API}/drive/v3/files?' + urllib.parse.urlencode(
        {'q': q, 'fields': 'files(id,name)', 'supportsAllDrives': 'true', 'includeItemsFromAllDrives': 'true'}), tok)
    existing = json.loads(b).get('files', [])
    meta, qs = {'name': name, 'mimeType': 'video/mp4'}, 'uploadType=resumable&supportsAllDrives=true&fields=id,name,size,webViewLink'
    if existing:            # same date uploaded before (a re-run): replace its content, keep one file
        method, url = 'PATCH', f'{API}/upload/drive/v3/files/{existing[0]["id"]}?{qs}'
    else:
        meta['parents'] = [folder]; method, url = 'POST', f'{API}/upload/drive/v3/files?{qs}'
    hdr, _ = call(method, url, tok, json.dumps(meta).encode(), {
        'Content-Type': 'application/json; charset=UTF-8', 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': str(size)})
    session = hdr.get('Location')
    if not session: sys.exit('Drive did not return an upload session URL')
    with open(path, 'rb') as f:
        _, b = call('PUT', session, tok, f.read(), {'Content-Type': 'video/mp4', 'Content-Length': str(size)})
    res = json.loads(b)
    if int(res.get('size', -1)) != size: sys.exit(f'size mismatch: Drive has {res.get("size")} bytes, local file is {size}')
    print(f'{"replaced" if existing else "uploaded"} {res["name"]} ({size / 1e6:.1f} MB): {res.get("webViewLink", res["id"])}')


if __name__ == '__main__':
    main(sys.argv[1])
