#!/usr/bin/env python3
"""Drive the canvas engine (index.html + engine.js) in headless Chromium.
   stills: python3 render.py stills out.png "<query>" t1 t2 ...
   video:  python3 render.py video  out.mp4 audio.wav "<query>"
   <query> is the URL query string, e.g. "fmt=p&pool=13053&main=11748&raffle=652&multi=652"
"""
import sys, time, subprocess, base64, os, socket
import numpy as np, cv2
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def server(port):
    p = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1', '--directory', ROOT],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(('127.0.0.1', port), timeout=0.2).close(); break
        except OSError:
            time.sleep(0.1)
    return p


def size_of(query):
    fmt = dict(kv.split('=', 1) for kv in query.split('&') if '=' in kv).get('fmt', 'h')
    return {'p': (1080, 1350), 'v': (1080, 1920)}.get(fmt, (1920, 1080))


def launch(p):
    exe = '/opt/pw-browsers/chromium'
    kw = {'executable_path': exe} if os.path.exists(exe) and os.path.isfile(exe) else {}
    try:
        return p.chromium.launch(args=['--disable-gpu', '--force-color-profile=srgb'], **kw)
    except Exception:
        return p.chromium.launch(args=['--disable-gpu', '--force-color-profile=srgb'])


def open_page(p, port, query, w, h, page='index.html'):
    b = launch(p)
    pg = b.new_page(viewport={'width': w, 'height': h}, device_scale_factor=1)
    pg.on('console', lambda m: print('[console]', m.text) if m.type in ('error', 'warning') else None)
    pg.on('pageerror', lambda e: print('[pageerror]', e))
    pg.goto(f'http://127.0.0.1:{port}/{page}?{query}')
    pg.wait_for_function('window.ready === true', timeout=60000)
    cdp = pg.context.new_cdp_session(pg)
    if 'plate=1' in query:   # transparent page: graphics only, composited over the footage plate below
        cdp.send('Emulation.setDefaultBackgroundColorOverride', {'color': {'r': 0, 'g': 0, 'b': 0, 'a': 0}})
    return b, pg, cdp


def grab(cdp, w, h, alpha=False):
    d = cdp.send('Page.captureScreenshot', {'format': 'png', 'optimizeForSpeed': True,
                                            'clip': {'x': 0, 'y': 0, 'width': w, 'height': h, 'scale': 1}})
    return cv2.imdecode(np.frombuffer(base64.b64decode(d['data']), np.uint8), cv2.IMREAD_UNCHANGED if alpha else cv2.IMREAD_COLOR)


# ------------------------------------------------------------------ footage plate (plate mode)
PLATE_DIM = [(0.0, 0.92), (1.5, 0.86), (4.0, 0.62), (9.0, 0.88), (10.5, 0.95)]   # (start s, brightness) per plate shot


def plate_grade(fr, t):
    k = [v for t0, v in PLATE_DIM if t >= t0 - 1e-6][-1]
    return cv2.convertScaleAbs(fr, alpha=k, beta=0)


def composite(ov, base):
    """ov: BGRA overlay (straight alpha) from the transparent page, base: BGR plate frame"""
    if ov.shape[2] == 3: return ov
    a = ov[:, :, 3:4].astype(np.float32) / 255.0
    return (ov[:, :, :3].astype(np.float32) * a + base.astype(np.float32) * (1 - a)).astype(np.uint8)


class Plate:
    def __init__(s, path, w, h, fps=30):
        s.cap = cv2.VideoCapture(path); s.w, s.h, s.fps, s.idx, s.last = w, h, fps, -1, None
        s.n = int(s.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def at(s, t):
        want = min(int(round(t * s.fps)), max(0, s.n - 1))
        if want != s.idx + 1: s.cap.set(cv2.CAP_PROP_POS_FRAMES, want)
        ok, fr = s.cap.read()
        if ok:
            s.idx, s.last = want, fr
            if fr.shape[1] != s.w or fr.shape[0] != s.h: s.last = cv2.resize(fr, (s.w, s.h), interpolation=cv2.INTER_AREA)
        return plate_grade(s.last if s.last is not None else np.zeros((s.h, s.w, 3), np.uint8), t)


def stills(out, query, times, n=8, cols=None, thumb=480, page='index.html', plate=None):
    w, h = size_of(query); cols = cols or (6 if w < h else 4)
    pl = Plate(plate, w, h) if plate else None
    port = free_port(); srv = server(port)
    try:
        with sync_playwright() as p:
            b, pg, cdp = open_page(p, port, query, w, h, page)
            ims = []
            for t in times:
                pg.evaluate(f'renderFrame({t},{n})')
                im = composite(grab(cdp, w, h, alpha=True), pl.at(t)) if pl else grab(cdp, w, h); sc = thumb / w
                im = cv2.resize(im, (int(w * sc), int(h * sc)), interpolation=cv2.INTER_AREA)
                cv2.putText(im, f'{t:.2f}', (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                ims.append(im)
            b.close()
    finally:
        srv.kill()
    rows = []
    for i in range(0, len(ims), cols):
        r = ims[i:i + cols]
        while len(r) < cols: r.append(np.zeros_like(ims[0]))
        rows.append(np.hstack(r))
    cv2.imwrite(out, np.vstack(rows))


class Post:
    """radial chromatic aberration on impacts + fine film grain"""
    def __init__(s, cues, w, h):
        s.imp = cues['IMPACTS']; s.w, s.h = w, h
        r = np.random.default_rng(3)
        s.grain = [r.normal(0, 2.2, (h, w)).astype(np.float32) for _ in range(6)]

    def __call__(s, im, t, f):
        ca = 0.0
        for ti, a, k in s.imp:
            if t >= ti: ca += a * 0.26 * np.exp(-(t - ti) * 11)
        out = im
        if ca > 0.35:
            b, g, r = cv2.split(im); cx, cy = s.w / 2, s.h / 2
            def sc(ch, k):
                M = np.float32([[k, 0, cx * (1 - k)], [0, k, cy * (1 - k)]])
                return cv2.warpAffine(ch, M, (s.w, s.h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            d = ca / (s.w / 2)
            out = cv2.merge([sc(b, 1 - d), g, sc(r, 1 + d)])
        gr = s.grain[f % len(s.grain)]
        return np.clip(out.astype(np.float32) + gr[..., None], 0, 255).astype(np.uint8)


def video(out, audio, query, fps=30, crf=18, sub=8, page='index.html', plate=None):
    w, h = size_of(query)
    pl = Plate(plate, w, h, fps) if plate else None
    port = free_port(); srv = server(port)
    try:
        with sync_playwright() as p:
            b, pg, cdp = open_page(p, port, query, w, h, page)
            dur = pg.evaluate('window.DURATION'); cues = pg.evaluate('window.CUES')
            post = Post(cues, w, h)
            cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}', '-r', str(fps), '-i', '-']
            if audio: cmd += ['-i', audio]
            cmd += ['-c:v', 'libx264', '-preset', 'slow', '-crf', str(crf), '-maxrate', '14M', '-bufsize', '28M', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
                    '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-movflags', '+faststart']
            if audio: cmd += ['-c:a', 'aac', '-b:a', '256k', '-shortest']
            cmd += [out]
            ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            nfr = int(round(dur * fps)); st = time.time()
            for f in range(nfr):
                t = f / fps
                pg.evaluate(f'renderFrame({t},{sub if t < dur - 1.2 else max(2, sub // 2)})')
                fr = composite(grab(cdp, w, h, alpha=True), pl.at(t)) if pl else grab(cdp, w, h)
                ff.stdin.write(post(fr, t, f).tobytes())
                if f % 60 == 0: print(f'{os.path.basename(out)}: frame {f}/{nfr}  {time.time() - st:.0f}s', flush=True)
            ff.stdin.close(); ff.wait(); b.close()
            if ff.returncode != 0: raise RuntimeError('ffmpeg failed')
    finally:
        srv.kill()


if __name__ == '__main__':
    mode = sys.argv[1]
    page = os.environ.get('PAGE', 'index.html')
    if mode == 'stills':
        stills(sys.argv[2], sys.argv[3], [float(x) for x in sys.argv[4:]], page=page)
    elif mode == 'video':
        video(sys.argv[2], None if sys.argv[3] == '-' else sys.argv[3], sys.argv[4], page=page)
