import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('drive_hq_upload', ROOT / 'scripts/drive_hq_upload.py')
hq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hq)

KEY = 'test-only-key-123'
DAY = {'date': '2026-10-13', 'pool': 14200, 'main': 12780, 'raffle': 710, 'multi': 710, 'round': '01',
       'ends': '2026-10-15', 'top': [['Inne****', 420000.5, 4500], ['Jame********', 130000.0, 1900]],
       'headline': ['POOL AT $14,200']}


class FakeDrive:
    """Stands in for the Apps Script uploader and Drive's upload endpoint."""
    def __init__(self, keeps_history=True, history=None, md5_override=None, in_drive=None):
        self.keeps_history, self.saved, self.files, self.md5_override = keeps_history, list(history or []), [], md5_override
        self.requests, self.in_drive = [], dict(in_drive or {})   # name -> (id, md5) of files already in 1001 Clips

    def ask(self, payload):
        self.requests.append(payload)
        if payload.get('action') == 'history' and self.keeps_history:
            return {'ok': True, 'history': self.saved}
        if payload.get('action') == 'remember' and self.keeps_history:
            self.saved.append(payload['entry']); return {'ok': True}
        if payload.get('action') == 'file' and self.keeps_history:
            if payload['name'] not in self.in_drive:
                return {'ok': False, 'error': f'no {payload["name"]} in 1001 Clips'}
            fid, md5 = self.in_drive[payload['name']]
            return {'ok': True, 'id': fid, 'name': payload['name'], 'size': '16', 'md5Checksum': md5}
        # older uploader: anything else (including unknown actions) opens an upload, videos only
        if not self.keeps_history and not payload.get('mimeType', 'video/mp4').startswith('video/'):
            return {'ok': False, 'error': 'invalid file metadata'}
        return {'ok': True, 'uploadUrl': f'https://www.googleapis.com/upload/drive/v3/files?upload_id={len(self.requests)}',
                'pending': payload.get('name')}

    def urlopen(self, req, timeout=None):
        content = req.data
        name = self.requests[-1].get('name')
        self.files.append((name, req.get_header('Content-type'), content))
        record = {'id': f'id_{len(self.files)}', 'name': name, 'size': str(len(content)),
                  'md5Checksum': self.md5_override or hashlib.md5(content).hexdigest()}
        self.in_drive[name] = (record['id'], record['md5Checksum'])
        return contextlib.closing(io.BytesIO(json.dumps(record).encode()))


VIDEO = b'fake video bytes'


def run_upload(drive, folder, video_id=None, today=dt.date(2026, 10, 13), day=DAY):
    video = Path(folder) / f'{day["date"]}.mp4'; video.write_bytes(VIDEO)
    data = Path(folder) / f'{day["date"]}.json'; data.write_text(json.dumps(day))
    out = io.StringIO()
    with patch.dict(hq.os.environ, {'HYPE_UPLOAD_KEY': KEY}), patch.object(hq, 'ask', drive.ask), \
            patch.object(hq, '_toronto_today', lambda: today), patch.object(hq.time, 'sleep', lambda s: None), \
            patch.object(hq.urllib.request, 'urlopen', drive.urlopen), contextlib.redirect_stdout(out):
        result = hq.upload(str(video), str(data), video_id)
    return result, out.getvalue(), video.read_bytes()


class DriveHqUploadTests(unittest.TestCase):
    def test_video_then_matching_metadata_then_history(self):
        drive = FakeDrive()
        with tempfile.TemporaryDirectory() as tmp:
            (video_id, meta_id, caption), out, video = run_upload(drive, tmp)
        self.assertEqual([f[0] for f in drive.files], ['2026-10-13.mp4', '2026-10-13.hq.json'])
        self.assertEqual(drive.files[0][1], 'video/mp4')
        self.assertEqual(drive.files[1][1], 'application/json')
        sidecar = json.loads(drive.files[1][2])
        self.assertEqual(set(sidecar), {'schemaVersion', 'kind', 'title', 'summary', 'keyPoints', 'caption',
                                        'creator', 'driveFileId', 'mediaChecksum'})
        self.assertEqual((sidecar['schemaVersion'], sidecar['kind'], sidecar['creator']), (1, 'video', 'Claude'))
        self.assertIn('Prize pool: $14,200.', sidecar['keyPoints'])
        self.assertIn('#1 Inne****: $420,000 wagered, $4,500 prize.', sidecar['keyPoints'])
        self.assertLessEqual(len(sidecar['caption']), 240)
        self.assertEqual(sidecar['driveFileId'], video_id)
        self.assertEqual(sidecar['mediaChecksum'], hashlib.md5(video).hexdigest())
        self.assertEqual(sidecar['caption'], caption)
        self.assertEqual(drive.saved[-1]['date'], '2026-10-13')
        self.assertNotIn(KEY, out)

    def test_older_uploader_still_takes_the_video_and_says_how_to_add_the_metadata(self):
        drive = FakeDrive(keeps_history=False)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RuntimeError) as err:
            run_upload(drive, tmp)
        self.assertEqual([f[0] for f in drive.files], ['2026-10-13.mp4'])
        self.assertIn('deploy the updated scripts/drive_uploader.gs', str(err.exception))
        self.assertIn('--video-id id_1', str(err.exception))
        self.assertFalse(any(r.get('action') == 'remember' for r in drive.requests))

    def test_video_already_in_drive_only_adds_metadata(self):
        drive = FakeDrive(in_drive={'2026-10-13.mp4': ('existing_video_id', hashlib.md5(VIDEO).hexdigest())})
        with tempfile.TemporaryDirectory() as tmp:
            (video_id, _, _), _, video = run_upload(drive, tmp, video_id='existing_video_id')
        self.assertEqual([f[0] for f in drive.files], ['2026-10-13.hq.json'])
        sidecar = json.loads(drive.files[0][2])
        self.assertEqual(sidecar['driveFileId'], 'existing_video_id')
        self.assertEqual(sidecar['mediaChecksum'], hashlib.md5(video).hexdigest())

    def test_expired_video_is_not_uploaded_or_redated(self):
        drive = FakeDrive()
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError) as err:
            run_upload(drive, tmp, today=dt.date(2026, 10, 14))
        self.assertEqual(drive.files, [])
        self.assertIn('never moved to a later posting date', str(err.exception))

    def test_failed_metadata_upload_is_retried_without_sending_the_video_again(self):
        drive = FakeDrive()
        real_urlopen, fails = drive.urlopen, {'left': 1}

        def flaky(req, timeout=None):
            if drive.requests[-1].get('name', '').endswith('.hq.json') and fails['left']:
                fails['left'] -= 1
                raise hq.urllib.error.HTTPError(req.full_url, 503, 'busy', {}, None)
            return real_urlopen(req, timeout)
        drive.urlopen = flaky
        with tempfile.TemporaryDirectory() as tmp:
            run_upload(drive, tmp)
        self.assertEqual([f[0] for f in drive.files], ['2026-10-13.mp4', '2026-10-13.hq.json'])

    def test_upload_stops_when_drive_cannot_confirm_the_files(self):
        drive = FakeDrive()
        real_ask = drive.ask
        drive.ask = lambda p: {'ok': False, 'error': 'no such file'} if p.get('action') == 'file' else real_ask(p)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RuntimeError) as err:
            run_upload(drive, tmp)
        self.assertIn('could not confirm', str(err.exception))

    def test_the_posted_opening_is_remembered_and_not_reused_within_a_week(self):
        drive = FakeDrive()
        with tempfile.TemporaryDirectory() as tmp:
            first = run_upload(drive, tmp)[0][2]
            stored = drive.saved[-1]['caption_choice']
            self.assertEqual(stored['text'], first)
            nxt = {**DAY, 'date': '2026-10-14', 'pool': 14300}
            second = run_upload(drive, tmp, today=dt.date(2026, 10, 14), day=nxt)[0][2]
        self.assertNotEqual(first.split('\n')[0], second.split('\n')[0])

    def test_bad_drive_checksum_stops_before_metadata(self):
        drive = FakeDrive(md5_override='0' * 32)
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RuntimeError):
            run_upload(drive, tmp)
        self.assertEqual([f[0] for f in drive.files], ['2026-10-13.mp4'])

    def test_upload_address_must_be_google(self):
        drive = FakeDrive()
        drive.ask = lambda payload: {'ok': True, 'uploadUrl': 'https://example.com/steal'}
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(RuntimeError):
            run_upload(drive, tmp)
        self.assertEqual(drive.files, [])

    def test_pull_history_adds_missing_days_without_overwriting(self):
        earlier = {**DAY, 'date': '2026-10-12', 'pool': 13972}
        mine = {**DAY, 'date': '2026-10-11', 'pool': 1}
        drive = FakeDrive(history=[earlier, {**DAY, 'date': '2026-10-11', 'pool': 999}, {'date': '../evil'}])
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / '2026-10-11.json').write_text(json.dumps(mine))
            with patch.object(hq, 'ask', drive.ask), contextlib.redirect_stdout(io.StringIO()):
                hq.pull_history(tmp)
            self.assertEqual(json.loads((Path(tmp) / '2026-10-12.json').read_text())['pool'], 13972)
            self.assertEqual(json.loads((Path(tmp) / '2026-10-11.json').read_text())['pool'], 1)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['2026-10-11.json', '2026-10-12.json'])

    def test_history_makes_growth_captions_possible(self):
        earlier = {**DAY, 'date': '2026-10-12', 'pool': 13972}
        drive = FakeDrive(history=[earlier])
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(hq, 'ask', drive.ask), contextlib.redirect_stdout(io.StringIO()):
                hq.pull_history(tmp)
            (_, _, caption), _, _ = run_upload(drive, tmp)
        for amount in __import__('re').findall(r'\$[\d,]+', caption):
            self.assertIn(amount, ('$14,200', '$228'))

    def test_metadata_for_a_video_already_in_drive_uses_drives_id_and_md5(self):
        drive = FakeDrive(in_drive={'2026-10-13.mp4': ('drive_video_id', 'ab' * 16)})
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / '2026-10-13.json'; data.write_text(json.dumps(DAY))
            with patch.object(hq, 'ask', drive.ask), patch.object(hq.urllib.request, 'urlopen', drive.urlopen), \
                    contextlib.redirect_stdout(io.StringIO()):
                video_id, _, caption = hq.metadata_only(str(data))
        self.assertEqual([f[0] for f in drive.files], ['2026-10-13.hq.json'])
        sidecar = json.loads(drive.files[0][2])
        self.assertEqual((video_id, sidecar['driveFileId'], sidecar['mediaChecksum']), ('drive_video_id', 'drive_video_id', 'ab' * 16))
        self.assertEqual(sidecar['caption'], caption)
        self.assertEqual(drive.saved[-1]['date'], '2026-10-13')

    def test_metadata_only_stops_when_the_video_is_missing_or_the_uploader_is_older(self):
        for drive in (FakeDrive(), FakeDrive(keeps_history=False)):
            with tempfile.TemporaryDirectory() as tmp:
                data = Path(tmp) / '2026-10-13.json'; data.write_text(json.dumps(DAY))
                with patch.object(hq, 'ask', drive.ask), patch.object(hq.urllib.request, 'urlopen', drive.urlopen), \
                        contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                    hq.metadata_only(str(data))
            self.assertEqual(drive.files, [])


if __name__ == '__main__':
    unittest.main()
