import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('uploader', Path(__file__).resolve().parents[1] / 'scripts/upload_drive.py')
uploader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uploader)

START = dt.date(2026, 10, 1)


def day(i):
    return (START + dt.timedelta(days=i)).isoformat()


def write_days(folder, days):
    for d in days:
        (Path(folder) / f'{d["date"]}.json').write_text(json.dumps(d))


def season(n, start_pool=12000):
    """n consecutive days, round 01 then 02 at day 15, pool mostly growing, a dip every 6th day, leader changes."""
    out, pool = [], start_pool
    for i in range(n):
        new_round = i == 15
        pool = 2000 if new_round else pool + (-50 if i % 6 == 0 else 250 + 31 * i)
        leader = 'Inne****' if i < 9 else 'Jame********' if i < 20 else 'AkaC***'
        out.append({'date': day(i), 'pool': pool, 'round': '01' if i < 15 else '02',
                    'ends': '2026-10-15' if i < 15 else '2026-10-30', 'top': [[leader, 100000.0 - i, 4000]]})
    return out


class CaptionTests(unittest.TestCase):
    def test_caption_is_derived_without_claude_caption(self):
        d = {'date': '2026-10-14', 'pool': 13053, 'top': [['Inne****', 100000, 4111]]}
        m = uploader.build_metadata(d, d['date'], today=dt.date(2026, 10, 14))
        self.assertTrue(m['caption'])
        self.assertNotIn('http', m['caption'])
        self.assertIn('$13,053', m['summary'])
        with self.assertRaises(ValueError):
            uploader.build_metadata(d, '2026-10-15')

    def test_captions_are_short_casual_and_use_the_days_real_numbers(self):
        days = season(45)
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp, days)
            prev = {}
            for d in days:
                text = uploader.build_caption(d, d['date'], tmp, today=dt.date.fromisoformat(d['date']))['text']
                lines = text.split('\n')
                self.assertLessEqual(len(lines), 2, text)
                self.assertTrue(all(0 < len(line) <= 60 for line in lines), text)
                self.assertNotRegex(text, r'https?://|www\.|#\w')
                self.assertLessEqual(len(uploader.EMOJI.findall(text)), 1, text)
                p = prev.get(d['round'])
                allowed = {f'${d["pool"]:,.0f}'} | ({f'${d["pool"] - p["pool"]:,.0f}'} if p else set())
                for amount in re.findall(r'\$[\d,]+', text):
                    self.assertIn(amount, allowed, text)
                names = {r[0][0] for r in (x['top'] for x in days)}
                for name in names - {d['top'][0][0]}:
                    self.assertNotIn(name, text)
                prev[d['round']] = d

    def test_growth_only_when_pool_rose_since_the_previous_snapshot_of_the_same_round(self):
        growth_words = re.compile(r'grew|bigger|growing|added|climbing|up \$', re.I)
        for i in range(40):
            d0, d1 = day(i), day(i + 1)
            base = {'top': [['Inne****', 1.0, 1]], 'ends': '2026-12-31'}
            cases = {
                'rose': ({**base, 'date': d0, 'pool': 1000, 'round': '01'}, {**base, 'date': d1, 'pool': 1400, 'round': '01'}),
                'fell': ({**base, 'date': d0, 'pool': 1500, 'round': '01'}, {**base, 'date': d1, 'pool': 1400, 'round': '01'}),
                'new round': ({**base, 'date': d0, 'pool': 900, 'round': '01'}, {**base, 'date': d1, 'pool': 1400, 'round': '02'}),
                'no round': ({**base, 'date': d0, 'pool': 900}, {**base, 'date': d1, 'pool': 1400}),
            }
            for name, (before, current) in cases.items():
                with tempfile.TemporaryDirectory() as tmp:
                    write_days(tmp, [before, current])
                    c = uploader.build_caption(current, d1, tmp, today=dt.date.fromisoformat(d1))
                if name == 'rose':
                    continue
                self.assertNotEqual(c['kind'], 'growth', (name, c['text']))
                self.assertNotRegex(c['text'], growth_words, (name, c['text']))
        # and the increase quoted is the real difference
        with tempfile.TemporaryDirectory() as tmp:
            seen = 0
            for i in range(60):
                before = {'date': day(i), 'pool': 1000, 'round': '01', 'top': [['Inne****', 1.0, 1]]}
                current = {'date': day(i + 1), 'pool': 1919, 'round': '01', 'top': [['Inne****', 1.0, 1]]}
                for p in Path(tmp).glob('*.json'):
                    p.unlink()
                write_days(tmp, [before, current])
                text = uploader.build_caption(current, current['date'], tmp, today=dt.date.fromisoformat(current['date']))['text']
                for amount in re.findall(r'\$[\d,]+', text):
                    self.assertIn(amount, ('$1,919', '$919'), text)
                seen += '$919' in text
            self.assertGreater(seen, 0)

    def test_openings_do_not_repeat_within_seven_days(self):
        days = season(60)
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp, days)
            picks = [(d['date'], uploader.build_caption(d, d['date'], tmp, today=dt.date.fromisoformat(d['date']))) for d in days]
        for i, (d, c) in enumerate(picks):
            for d_prev, c_prev in picks[max(0, i - 7):i]:
                self.assertNotEqual(c['opening'], c_prev['opening'], f'{d_prev} and {d}: {c["text"]}')
        kinds = [c['kind'] for _, c in picks]
        for kind in ('board', 'pool', 'growth', 'leader'):
            self.assertIn(kind, kinds)
        self.assertLess(kinds.count('leader'), len(kinds) / 3)   # leader mentions stay occasional

    def test_tonights_stream_only_when_confirmed_and_only_for_that_days_video(self):
        for i in range(30):
            d = {'date': day(i), 'pool': 5000, 'round': '01', 'top': [['Inne****', 1.0, 1]]}
            today = dt.date.fromisoformat(d['date'])
            self.assertNotIn('tonight', uploader.build_caption(d, d['date'], today=today)['text'])
            confirmed = {**d, 'stream_tonight': True}
            self.assertIn('tonight’s stream', uploader.build_caption(confirmed, d['date'], today=today)['text'])
            later = today + dt.timedelta(days=3)
            self.assertNotIn('tonight', uploader.build_caption(confirmed, d['date'], today=later)['text'])

    def test_older_videos_use_their_date_instead_of_today(self):
        days = season(30)
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp, days)
            for d in days:
                text = uploader.build_caption(d, d['date'], tmp, today=dt.date(2026, 11, 20))['text']
                self.assertNotRegex(text.lower(), r'today|tonight|right now|\bnow\b|days? left|last day', text)
                self.assertIn(uploader._date_label(d['date']), text)

    def test_reruns_give_the_same_caption(self):
        days = season(20)
        with tempfile.TemporaryDirectory() as tmp:
            write_days(tmp, days)
            d = days[-1]
            first = uploader.build_metadata(d, d['date'], tmp, today=dt.date.fromisoformat(d['date']))
            again = uploader.build_metadata(d, d['date'], tmp, today=dt.date.fromisoformat(d['date']))
        self.assertEqual(first, again)


class UploadTests(unittest.TestCase):

    def test_video_and_sidecar_share_verified_identity(self):
        d = {'date': '2026-10-14', 'pool': 13053, 'top': [['Inne****', 100000, 4111]]}
        uploaded = []
        def fake_upload(tok, folder, name, mime, content):
            uploaded.append((name, mime, content))
            return {'id': 'real_video_fixture', 'md5Checksum': hashlib.md5(content).hexdigest()}
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / '2026-10-14.mp4'; video.write_bytes(b'video fixture')
            data = Path(tmp) / '2026-10-14.json'; data.write_text(json.dumps(d))
            with patch.dict(uploader.os.environ, {k: 'test-only' for k in ('GDRIVE_CLIENT_ID', 'GDRIVE_CLIENT_SECRET', 'GDRIVE_REFRESH_TOKEN', 'GDRIVE_FOLDER_ID')}), patch.object(uploader, 'access_token', return_value='test-only'), patch.object(uploader, 'upload', fake_upload):
                uploader.main(str(video), str(data))
        self.assertEqual([f[0] for f in uploaded], ['2026-10-14.mp4', '2026-10-14.hq.json'])
        metadata = json.loads(uploaded[1][2])
        self.assertEqual(set(metadata), {'schemaVersion', 'kind', 'title', 'summary', 'keyPoints', 'caption',
                                         'creator', 'driveFileId', 'mediaChecksum'})
        self.assertEqual(metadata['schemaVersion'], 1)
        self.assertEqual(metadata['driveFileId'], 'real_video_fixture')
        self.assertEqual(metadata['mediaChecksum'], hashlib.md5(uploaded[0][2]).hexdigest())

    def test_replacement_and_corruption_checks(self):
        content = b'fixture'
        calls = []
        def fake_call(method, url, *args):
            calls.append(method)
            if method == 'GET':
                return {}, json.dumps({'files': [{'id': 'existing'}]}).encode()
            if method == 'PATCH':
                return {'Location': 'https://www.googleapis.com/upload/drive/v3/files?session=test'}, b''
            return {}, json.dumps({'id': 'existing', 'size': len(content), 'md5Checksum': hashlib.md5(content).hexdigest()}).encode()
        with patch.object(uploader, 'call', fake_call):
            self.assertEqual(uploader.upload('test', 'folder', '2026-10-14.mp4', 'video/mp4', content)['id'], 'existing')
        self.assertEqual(calls, ['GET', 'PATCH', 'PUT'])
        with patch.object(uploader, 'call', return_value=({}, json.dumps({'files': [{'id': 'a'}, {'id': 'b'}]}).encode())):
            with self.assertRaises(ValueError):
                uploader.upload('test', 'folder', '2026-10-14.mp4', 'video/mp4', content)
        with self.assertRaises(ValueError):
            uploader.call('PUT', 'https://untrusted.example/upload', token='never-send')


if __name__ == '__main__':
    unittest.main()
