import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('uploader', Path(__file__).resolve().parents[1] / 'scripts/upload_drive.py')
uploader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uploader)


class UploadTests(unittest.TestCase):
    def test_caption_is_derived_without_claude_caption(self):
        d = {'date': '2026-10-14', 'pool': 13053, 'top': [['Inne****', 100000, 4111]]}
        m = uploader.build_metadata(d, d['date'])
        self.assertIn('$13,053', m['caption'])
        self.assertIn('Inne****', m['caption'])
        self.assertNotIn('http', m['caption'])
        with self.assertRaises(ValueError):
            uploader.build_metadata(d, '2026-10-15')

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
