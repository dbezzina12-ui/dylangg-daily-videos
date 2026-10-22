#!/usr/bin/env python3
"""DylanJamesGG hype edit renderer (house style). One engine for all edits.

Usage:  python3 hype_edit.py edl.json [--preview] [--audio-only]
The EDL (JSON) describes the shots; this script does the rest: smooth speed ramps, a purposeful
virtual camera (locked board while reels land, straight zooms onto clusters, 3D perspective tilt for
scatter drops / the final big hit), whip / glitch / flash transitions, hit punches, a natural grade,
facecam cut-ins, pitch-preserving stream audio (WSOLA) with his voice tamed, real sound effects from
the sound pack (synth fallback), an optional song bed aligned to the big reveal, voice drops,
freeze frames with cartoon pop-up reactions,
a true-peak-safe loudness pass, and MP4s under the upload cap.
Outputs: OUT (main edit at out_size: 16:9 X edit, or 9:16 for phone recordings) and, with
formats ["x","ig"], OUT_ig.mp4 (Instagram 9:16 panel version, optional banner). No on-screen text.
"""
import subprocess, numpy as np, cv2, math, sys, json, os

from scipy import signal

EDL = json.load(open(sys.argv[1]))
PREVIEW = "--preview" in sys.argv
SRC = EDL["src"]
FPS = EDL.get("fps", 60); W, H = EDL.get("out_size", [1920, 1080]); SR = 48000
SW, SH = EDL.get("src_size", [W, H])        # source frame size (phone screen recordings are tall)
OUT = EDL.get("out", "hype_edit.mp4")
if PREVIEW: OUT = OUT.replace(".mp4", "_preview.mp4")
MAX_MB = EDL.get("max_mb", 29)
WORK = EDL.get("work", "work"); os.makedirs(WORK, exist_ok=True)
rng = np.random.default_rng(7)

# ---------- geometry presets from the stream layout ----------
gx, gy, gw, gh = EDL["game_rect"]          # slot game window in the 1920x1080 source
fx_, fy_, fw, fh = EDL.get("face_rect", [0, 0, 100, 100])   # webcam box in the source (none on phone clips)
BOARD = (gx + gw / 2, gy + gh / 2, min(W / gw, H / gh), 0.0)
POP = (BOARD[0], BOARD[1] - 20, BOARD[2] * 1.24, 0.0)
FACE = (fx_ + fw / 2, fy_ + fh / 2, min(W / fw, H / fh) * 1.06, 0.0)
if "board" in EDL: BOARD = tuple(EDL["board"][:3]) + (0.0,)      # explicit framing overrides (phone edits)
if "pop" in EDL: POP = tuple(EDL["pop"][:3]) + (0.0,)

def resolve_key(k):
    """[t, 'BOARD'] | [t, 'POP', rot] | [t, 'FACE', zmul, rot] | [t, cx, cy, z, rot]"""
    t = k[0]
    if isinstance(k[1], str):
        name = k[1]
        if name == "BOARD": return (t, *BOARD, 0.0, 0.0)
        if name == "POP": return (t, POP[0], POP[1], POP[2] * (k[2] if len(k) > 2 else 1.0), 0.0, 0.0, 0.0)
        if name == "FACE":
            zm = k[2] if len(k) > 2 else 1.0; rot = k[3] if len(k) > 3 else 0.0
            return (t, FACE[0], FACE[1] - 10 * (zm - 1) * 10, FACE[2] * zm, rot, 0.0, 0.0)
        raise ValueError(name)
    k = list(k) + [0.0] * (7 - len(k))          # [t, cx, cy, z, rot, yaw, pitch]
    return tuple(k[:7])

SHOTS = []
for s in EDL["shots"]:
    s = dict(s)
    s["cam"] = [resolve_key(k) for k in s["cam"]]
    s.setdefault("lock", []); s.setdefault("hits", []); s.setdefault("out", "whip")
    s["hits"] = [(h[0], h[1], bool(h[2]) if len(h) > 2 else False) for h in s["hits"]]
    SHOTS.append(s)
FX = {"hit": 1.0, "trans": 1.0, "trans_len": 1.0, **EDL.get("fx", {})}   # <1 = lighter impact punches / transitions
TRANS_OUT = 0.12 * FX["trans_len"]; TRANS_IN = 0.16 * FX["trans_len"]

# ---------- freeze frames + cartoon pop-ups ----------
# "freezes": [{"src": 119.8, "dur": "auto", "pop": "auto" | {"char": "coin", "line": "damn_thats_nice", "corner": "br"} | null,
#              "push": 0.06}]
# The picture holds on src for dur s instead of slowing down (his voice never stretches): the stream audio rings out
# under it, the frame dims a touch, and a cartoon character from the pop-up pack bounces up from a corner, says its line
# and pops away as the picture restarts. "popups": {"dir": pack with pack.json, "size": 0.40 (of the frame height),
# "gain": 1.0, "corner": "br"}. Auto picks take the least recently used character, then its least recently used line
# (history.json in the pack), never repeating inside an edit; the picks are pinned in WORK/pop_picks.json so a preview
# and the full render match.
POPS = EDL.get("popups") or {}
PACKP = json.load(open(os.path.join(POPS["dir"], "pack.json"))) if POPS else None
FRZ = [dict(f) for f in EDL.get("freezes", [])]
POP_IN, VOICE_DELAY = 0.06, 0.12                    # character lands, then speaks
def load_audio(path):
    raw_ = subprocess.run(["ffmpeg", "-v", "quiet", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw_, np.float32).reshape(-1, 2).astype(np.float64)
if FRZ and PACKP:
    import zlib
    pins_p = os.path.join(WORK, "pop_picks.json"); hist_p = os.path.join(POPS["dir"], "history.json")
    pins = json.load(open(pins_p)) if os.path.exists(pins_p) else {}
    pins0 = json.dumps(pins, sort_keys=True)
    hist = json.load(open(hist_p)) if os.path.exists(hist_p) else []
    def last_use(k): return max([i for i, h in enumerate(hist) if h == k], default=-1)
    def tiebreak(k): return zlib.crc32((OUT + k).encode()) / 2 ** 32
    used, fresh = set(), []
    for f in FRZ:
        p = f.get("pop", "auto")
        if p is None: continue
        p = {} if p == "auto" else dict(p)
        pin = pins.get(f'{f["src"]:.2f}')
        if pin and "char" not in p: p.update(pin)
        if "char" not in p:
            p["char"] = min((c for c in PACKP["chars"] if c not in used), key=lambda c: (last_use("c:" + c), tiebreak(c)))
        lines = PACKP["chars"][p["char"]]["lines"]
        if "line" not in p:
            p["line"] = min(lines, key=lambda l: (last_use("l:" + p["char"] + "/" + l["id"]), tiebreak(l["id"])))["id"]
        used.add(p["char"])
        if pins.get(f'{f["src"]:.2f}') != {"char": p["char"], "line": p["line"]}:
            pins[f'{f["src"]:.2f}'] = {"char": p["char"], "line": p["line"]}; fresh += ["c:" + p["char"], "l:" + p["char"] + "/" + p["line"]]
        ln = next(l for l in lines if l["id"] == p["line"])
        p["_aud"] = load_audio(os.path.join(POPS["dir"], ln["file"])) * POPS.get("gain", 1.0)
        p["_len"] = len(p["_aud"]) / SR
        e_ = np.sqrt(np.convolve((p["_aud"] ** 2).mean(1), np.ones(SR // 30) / (SR // 30), mode="same"))
        p["_env"] = e_[::SR // FPS] / max(1e-6, e_.max())                     # mouth / bounce envelope per output frame
        p["_img"] = os.path.join(POPS["dir"], PACKP["chars"][p["char"]]["img"])
        p.setdefault("corner", POPS.get("corner", "br"))
        f["pop"] = p
        print(f'freeze at {f["src"]:.2f}: {p["char"]} says "{ln.get("text", p["line"])}"')
    if json.dumps(pins, sort_keys=True) != pins0 or not os.path.exists(pins_p):
        json.dump(pins, open(pins_p, "w"), indent=1)
    if fresh and not PREVIEW: json.dump(hist + fresh, open(hist_p, "w"))
for f in FRZ:
    p = f.get("pop") if isinstance(f.get("pop"), dict) and "_aud" in f["pop"] else None
    f["pop"] = p
    if f.get("dur", "auto") == "auto":
        f["dur"] = min(2.4, max(1.0, p["_len"] + POP_IN + VOICE_DELAY + 0.25)) if p else 1.0
    f["_si"] = max(i for i, s_ in enumerate(SHOTS) if s_["a"] - 1e-6 <= f["src"] < s_["b"])   # last showing of that moment

# ---------- time map (smoothed speed ramps) ----------
tau = 0.06; alpha = 1 - math.exp(-(1 / FPS) / tau)
frames = []
for si, s in enumerate(SHOTS):
    t = s["a"]; sp = s["speeds"][0][1]; n0 = len(frames)
    pend = sorted((f for f in FRZ if f["_si"] == si), key=lambda f: f["src"])
    while t < s["b"]:
        if pend and t >= pend[0]["src"] - 1e-9:        # hold this frame (speed 0) for the freeze
            f = pend.pop(0); f["_f0"] = len(frames)
            frames += [[si, t, 0.0] for _ in range(int(round(f["dur"] * FPS)))]
            f["_f1"] = len(frames)
        tgt = [v for (k, v) in s["speeds"] if t >= k - 1e-9][-1]
        sp += (tgt - sp) * alpha
        frames.append([si, t, sp]); t += sp / FPS
    s["f0"], s["f1"] = n0, len(frames)
N = len(frames); DUR = N / FPS
for f in FRZ: f["_T0"], f["_T1"] = f["_f0"] / FPS, f["_f1"] / FPS
def out_time(s, st):
    for i in range(s["f0"], s["f1"]):
        if frames[i][1] >= st - 1e-6: return i / FPS
    return s["f1"] / FPS
for s in SHOTS:
    s["T0"], s["T1"] = s["f0"] / FPS, s["f1"] / FPS
    s["hits_out"] = [(out_time(s, ht), I, boom) for ht, I, boom in s["hits"]]
    s["camT"] = [(out_time(s, k[0]),) + tuple(k[1:]) for k in s["cam"]]
    s["lockT"] = [(out_time(s, a), out_time(s, b)) for a, b in s["lock"]]
    print(f'{s["kind"]:5s} src {s["a"]:7.2f}-{s["b"]:7.2f}  out {s["T0"]:6.2f} +{s["T1"] - s["T0"]:.2f}s  -> {s["out"]}')
HITS = [(t, I) for s in SHOTS for t, I, _ in s["hits_out"]]
# fast-forward shots: {"ff": {"label": "x8", "caption": "NOTHING HAPPENED UNTIL..."}} -> VHS look, VCR badge, typed caption,
# the stream audio ducked under a tape whir, and a "PLAY" badge as the next shot comes back to real speed
FFR = [(s_["T0"], s_["T1"], s_["ff"]) for s_ in SHOTS if s_.get("ff")]
# "mask_text": [{"text": "NOT BAD", "src": t, "until_src": t2, "y": 0.34, "size": 330}] on a face shot -> the caption slams in
# BEHIND him (person cut out with rembg isnet and laid back over the text)
for s_ in SHOTS:
    if s_.get("mask_words"):          # [{"text": "NOT", "src": t, "color": [r,g,b]}, ...] -> one caption per word, each replaced by the next
        ws = s_["mask_words"]
        for k, w_ in enumerate(ws):
            s_.setdefault("mask_text", []).append({"style": "glitch", "y": 0.30, "size": 360, **w_,
                                                   "until_src": ws[k + 1]["src"] if k + 1 < len(ws) else s_["b"], "_cut": k + 1 < len(ws)})
    for mt in s_.get("mask_text", []):
        mt["_t0"] = out_time(s_, mt["src"]); mt["_t1"] = out_time(s_, mt.get("until_src", s_["b"]))
def src_out(src_t):
    """output time of source time src_t. A moment shown twice (a cold-open tease and the real thing) maps to its
    last showing, so sounds, overlays and the song drop land on the real moment."""
    inside = [s for s in SHOTS if s["a"] - 1e-6 <= src_t < s["b"]]
    if inside: return out_time(inside[-1], src_t)
    return next((i / FPS for i, f in enumerate(frames) if f[1] >= src_t - 1e-6), N / FPS)
DESAT = EDL.get("desat")                              # optional colour drain to black & white (overlays stay in colour)
if DESAT:
    DESAT["_t0"] = src_out(DESAT["src"])
print(f"total {DUR:.2f}s")
json.dump({"dur": DUR, "shots": [{k: s_[k] for k in ("kind", "a", "b", "T0", "T1", "out")} | {"blur": s_.get("blur", []),
           "hits": [[t_, I_, b_] for t_, I_, b_ in s_["hits_out"]]} for s_ in SHOTS],
           "freezes": [{"src": f["src"], "T0": f["_T0"], "T1": f["_T1"]} for f in FRZ]},
          open(os.path.join(WORK, "timeline.json"), "w"), indent=1)      # read by edit_qa.py

def ease(u): return u * u * (3 - 2 * u)
from scipy.interpolate import PchipInterpolator
for s in SHOTS:
    if s.get("cam_interp") == "smooth":
        ks = {}
        for k in s["camT"]: ks[round(k[0], 4)] = k          # keys landing on the same output frame: last one wins
        ks = sorted(ks.values())
        s["camT"] = ks
        if len(ks) > 1:
            s["spline"] = PchipInterpolator([k[0] for k in ks], np.array([k[1:] for k in ks]), axis=0, extrapolate=False)
def cam_base(si, T):
    ks = SHOTS[si]["camT"]
    if "spline" in SHOTS[si]:
        T_ = min(max(T, ks[0][0]), ks[-1][0])
        return [float(v) for v in SHOTS[si]["spline"](T_)]
    if T <= ks[0][0]: return list(ks[0][1:])
    for j in range(len(ks) - 1):
        if ks[j][0] <= T <= ks[j + 1][0]:
            e = ease((T - ks[j][0]) / max(1e-6, ks[j + 1][0] - ks[j][0]))
            return [ks[j][k] + (ks[j + 1][k] - ks[j][k]) * e for k in range(1, 7)]
    return list(ks[-1][1:])
def motion_amt(si, T):
    m = 1.0
    for a, b in SHOTS[si]["lockT"]:
        if a <= T <= b: m = 0.0
        elif b < T < b + 0.3: m = min(m, (T - b) / 0.3)
    return m

def fx_state(si, T):
    cx, cy, z, rot, yaw, pitch = cam_base(si, T); s = SHOTS[si]
    for f in FRZ:
        if f["_T0"] <= T < f["_T1"] + 0.25:
            u = ease(min(1.0, (T - f["_T0"]) / max(1e-3, f["_T1"] - f["_T0"])))
            z *= 1 + f.get("push", 0.06) * u * (1 - ease(min(1.0, max(0.0, T - f["_T1"]) / 0.25)))
    # no idle drift: the camera only moves when a key tells it to (zoom on the thing that's landing)
    kick = shake = flash = ca = rb = glitch = 0.0
    for ht, I in HITS:
        d = T - ht
        if -0.001 <= d < 1.5:
            I = I * FX["hit"]
            kick += 0.24 * I * math.exp(-d * 9) * (1 - math.exp(-d * 140))
            shake += 30 * I * math.exp(-d * 6.5)
            flash += 0.3 * I * math.exp(-d * 16)
            ca += 16 * I * math.exp(-d * 9)
            rb += 0.10 * I * math.exp(-d * 14)
    if T > s["T1"] - TRANS_OUT and s["out"] in ("whip", "glitch", "flash"):
        p = (T - (s["T1"] - TRANS_OUT)) / TRANS_OUT; tk = FX["trans"]
        if s["out"] == "whip": kick += 0.45 * tk * p * p; rb += 0.22 * tk * p * p
        if s["out"] == "glitch": glitch = max(glitch, p * tk)
        if s["out"] == "flash": flash += 0.9 * tk * p * p
    if si > 0 and T < s["T0"] + TRANS_IN:
        p = 1 - (T - s["T0"]) / TRANS_IN; prev = SHOTS[si - 1]["out"]; tk = FX["trans"]
        if prev == "whip": kick += 0.4 * tk * p * p; rb += 0.2 * tk * p * p; ca += 6 * tk * p
        if prev == "glitch": glitch = max(glitch, p * 0.9 * tk)
        if prev == "flash": flash += 0.9 * tk * p
    z *= 1 + kick
    if shake > 0.3:
        cx += shake * math.sin(T * 91) / z * 1.6; cy += shake * math.cos(T * 77) / z * 1.3
    end = 0.0
    if s["out"] == "end" and T > DUR - 0.45:
        glitch = max(glitch, (T - (DUR - 0.45)) / 0.45); end = (T - (DUR - 0.45)) / 0.45
    sat = 1.0
    if DESAT:
        u = (T - DESAT["_t0"]) / max(1e-3, DESAT.get("dur", 0.8))
        if u > 0: sat = 1 + (DESAT.get("to", 0.0) - 1) * ease(min(1.0, u))
    return dict(cx=cx, cy=cy, z=z, rot=rot, yaw=yaw, pitch=pitch, flash=flash, ca=ca, rb=rb, glitch=glitch, end=end, sat=sat)

FOC = W * 1.1
def mat(cx, cy, z, rot, yaw=0.0, pitch=0.0, ow=None, oh=None):
    """source -> output homography: flat zoom/rotate about (cx,cy), then a 3D tilt of the image plane (yaw/pitch, deg)"""
    ow = ow or W; oh = oh or H
    M = cv2.getRotationMatrix2D((cx, cy), rot, z); M[0, 2] += ow / 2 - cx; M[1, 2] += oh / 2 - cy
    A = np.vstack([M, [0, 0, 1]])
    if abs(yaw) < 1e-3 and abs(pitch) < 1e-3: return A
    ya, pa = math.radians(yaw), math.radians(pitch)
    Ry = np.array([[math.cos(ya), 0, math.sin(ya)], [0, 1, 0], [-math.sin(ya), 0, math.cos(ya)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(pa), -math.sin(pa)], [0, math.sin(pa), math.cos(pa)]])
    R = Ry @ Rx
    # rotate the picture plane about its centre and view it from distance FOC
    C = np.array([[1, 0, -ow / 2], [0, 1, -oh / 2], [0, 0, 0], [0, 0, 1]], float)        # 2D -> 3D plane (z=0)
    T3 = np.eye(4); T3[:3, :3] = R; T3[2, 3] = FOC
    K = np.array([[FOC, 0, ow / 2, 0], [0, FOC, oh / 2, 0], [0, 0, 1, 0]], float)
    P = K @ T3 @ C
    return P @ A

class Reader:
    """sequential frame reader for one shot. With `region` set it also finds the frames where that region
    really changed (live-casino feeds run ~20-25 fps inside a 60 fps capture) so interp() can rebuild the
    in-between frames with optical flow instead of showing each feed frame 2-4 times (judder)."""
    def __init__(self, a, b, region=None):
        self.p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.3:.3f}", "-i", SRC,
                                   "-vf", f"scale={SW}:{SH}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
        self.buf = {}; self.next = 0
        self.region = [int(v) for v in region] if region else None; self.dist = []; self.prev_small = None; self.flow = (None, None)
        if self.region:
            x, y, w, h = self.region
            self.gx, self.gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
            self.dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    def get(self, k):
        while self.next <= k:
            raw = self.p.stdout.read(SW * SH * 3)
            self.buf[self.next] = self.buf[self.next - 1] if len(raw) < SW * SH * 3 else np.frombuffer(raw, np.uint8).reshape(SH, SW, 3)
            if self.region:
                x, y, w, h = self.region
                sm = cv2.cvtColor(cv2.resize(self.buf[self.next][y:y + h, x:x + w], (w // 4, h // 4), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
                if self.prev_small is None or np.abs(sm - self.prev_small).mean() > 0.3: self.dist.append(self.next)
                self.prev_small = sm
            self.next += 1
        for old in [j for j in self.buf if j < k - 16]: del self.buf[old]
        self.dist = [j for j in self.dist if j >= k - 16]
        return self.buf[k]
    def interp(self, fk):
        k0 = int(fk); base = self.get(k0); self.get(k0 + 6)
        a = next((j for j in reversed(self.dist) if j <= fk + 1e-6), None)
        b = next((j for j in self.dist if j > fk + 1e-6), None)
        if a is None or b is None or b - a > 8 or a not in self.buf or b not in self.buf: return base.astype(np.float32)
        u = (fk - a) / (b - a); x, y, w, h = self.region
        A = self.buf[a][y:y + h, x:x + w]; B = self.buf[b][y:y + h, x:x + w]
        if self.flow[0] != (a, b):
            ga = cv2.cvtColor(cv2.resize(A, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
            gb = cv2.cvtColor(cv2.resize(B, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
            F = cv2.resize(self.dis.calc(ga, gb, None), (w, h)) * 2; G = cv2.resize(self.dis.calc(gb, ga, None), (w, h)) * 2
            self.flow = ((a, b), (F, G))
        F, G = self.flow[1]
        Ft0 = -(1 - u) * u * F + u * u * G; Ft1 = (1 - u) ** 2 * F - u * (1 - u) * G     # flow from time u back to A / on to B
        Aw = cv2.remap(A, self.gx + Ft0[..., 0], self.gy + Ft0[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        Bw = cv2.remap(B, self.gx + Ft1[..., 0], self.gy + Ft1[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        out = base.astype(np.float32); out[y:y + h, x:x + w] = Aw.astype(np.float32) * (1 - u) + Bw.astype(np.float32) * u
        return out
    def close(self): self.p.stdout.close(); self.p.kill()
# "feed_interp": ["game"] (or ["game","face"]) -> optical-flow in-betweens for those shot kinds (live-casino tables)
FEED = EDL.get("feed_interp", [])
if FEED is True: FEED = ["game"]
def feed_region(kind): return EDL["game_rect"] if kind == "game" else EDL["face_rect"]

# ---------- video ----------
FORMATS = EDL.get("formats", ["x"])               # "x" = the main edit at out_size; "ig" = extra 9:16 Instagram panel version (16:9 stream sources only)
VW, VH = 1080, 1920
PW, PH = 1080, 830                                  # vertical: one near-square panel, centred, over a blurred copy of itself
PY = (VH - PH) // 2
# "ig_layout": "stack" -> full-bleed 9:16: his live webcam in a band on top, the game below, a Kick-green seam between them.
# Game shots: webcam band ig_cam_h tall, game band fills the rest (framed on the board, the X edit's push-ins scaled to it).
# Face shots: the webcam band grows to ig_face_h (he is the shot, word captions sit behind him), the game runs in the strip below.
# No reaction PiPs (he is always on screen). The banner rides the seam. Reels UI safe zone: nothing important below VH - IG_SAFE_B.
# "ig_layout": "ghost" (Dylan, 2026-10-22: "just the slot screen, 16:9, with ghosting top and bottom, and make me bigger once it
# shows me") -> the X edit's own 16:9 picture full-width in the middle over a blurred, darkened copy of itself; his reactions
# swing in as a big tilted webcam card in the ghost space above it (not over the game); face shots become a tall panel of him.
IGL = EDL.get("ig_layout", "panel")
CAMH = EDL.get("ig_cam_h", 700); FACEH = EDL.get("ig_face_h", 1240); IG_SAFE_B = 330
IG_OV_SCALE = 0.75                                  # overlays (total slam etc.) at "ig_pos", default the middle of the game band
def vignette(h, w):
    y_, x_ = np.mgrid[0:h, 0:w].astype(np.float32)
    return (np.clip(np.sqrt(((x_ - w / 2) / (w / 2)) ** 2 + ((y_ - h / 2) / (h / 2)) ** 2) / 1.414, 0, 1) ** 2.2)[..., None]
VIGS = {}
def post(img, st):
    """colour split, glitch, grade, flash, fade -- works on any frame size"""
    h, w = img.shape[:2]
    if st["ca"] > 0.8:
        o = int(round(st["ca"] * w / W)); b_, g_, r_ = cv2.split(img); img = cv2.merge([np.roll(b_, -o, 1), g_, np.roll(r_, o, 1)])
    if st["glitch"] > 0.02:
        g = st["glitch"]; blk = int(8 + 40 * g)
        pix = cv2.resize(cv2.resize(img, (w // blk, h // blk), interpolation=cv2.INTER_AREA), (w, h), interpolation=cv2.INTER_NEAREST)
        out = img.copy(); y = 0
        while y < h:
            hgt = int(rng.integers(20, 140))
            if rng.random() < 0.35 + 0.55 * g:
                sb = pix if rng.random() < 0.6 else img
                out[y:y + hgt] = np.roll(sb[y:y + hgt], int(rng.integers(-1, 2) * rng.integers(0, int(60 * g) + 1)), axis=1)
            y += hgt
        o = int(6 + 20 * g); b_, g_, r_ = cv2.split(out); img = cv2.merge([np.roll(b_, -o, 1), g_, np.roll(r_, o, 1)])
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[..., None]
    img = gray + (img - gray) * 1.05 * st.get("sat", 1.0)
    img = (img - 128) * 1.03 + 128
    if (h, w) not in VIGS: VIGS[(h, w)] = vignette(h, w)
    img = img * (1 - 0.18 * VIGS[(h, w)])
    if st["flash"] > 0.01: img = img + (255 - img) * min(0.5, st["flash"])
    if st["end"] > 0: img = img * (1 - st["end"])
    return np.clip(img, 0, 255).astype(np.uint8)

def warp_cam(src, st, st0, ow=None, oh=None):
    """virtual camera with motion blur (sub-frame samples) + radial zoom blur"""
    ow = ow or W; oh = oh or H
    disp = math.hypot((st["cx"] - st0["cx"]) * st["z"], (st["cy"] - st0["cy"]) * st["z"]) + abs(st["z"] - st0["z"]) * 900 + abs(st["rot"] - st0["rot"]) * 25 + (abs(st["yaw"] - st0["yaw"]) + abs(st["pitch"] - st0["pitch"])) * 30
    nsub = int(min(6, max(1, disp / 10)))
    if nsub == 1:
        img = cv2.warpPerspective(src, mat(st["cx"], st["cy"], st["z"], st["rot"], st["yaw"], st["pitch"], ow, oh), (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    else:
        acc = None
        for j in range(nsub):
            f = j / (nsub - 1)
            c = [st0[k] + (st[k] - st0[k]) * f for k in ("cx", "cy", "z", "rot", "yaw", "pitch")]
            wi = cv2.warpPerspective(src, mat(*c, ow, oh), (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            acc = wi if acc is None else acc + wi
        img = acc / nsub
    if st["rb"] > 0.01:
        acc = img.copy()
        for j in range(1, 6):
            acc += cv2.warpAffine(img, cv2.getRotationMatrix2D((ow / 2, oh / 2), 0, 1 + st["rb"] * j / 6), (ow, oh), borderMode=cv2.BORDER_REFLECT)
        img = acc / 6
    return img

def vcam(st, kind, pw=PW, ph=PH, prop=False):
    """map a 16:9 camera state to a vertical panel: same centre and horizontal framing on close-ups,
    but never zoomed out past the game window / webcam height (so no stream overlays creep in).
    prop=True (stack game band): the X edit's BOARD framing = the whole game height, push-ins damped from there (the band is
    narrow, a full-strength push would cut wide banners like MEGA WIN off at the sides)"""
    v = dict(st)
    if kind == "face":
        zmin = ph / fh; top, bot = fy_, fy_ + fh; left, right = fx_, fx_ + fw
    else:
        zmin = ph / gh; top, bot = gy, gy + gh; left, right = gx, gx + gw
    v["z"] = zmin * 1.01 * max(1.0, st["z"] / BOARD[2]) ** 0.35 if prop else max(st["z"] * pw / W, zmin * 1.01)
    hh = ph / v["z"] / 2; hw = pw / v["z"] / 2
    v["cy"] = min(max(v["cy"], top + hh), bot - hh)
    v["cx"] = min(max(v["cx"], left + hw), right - hw) if right - left > 2 * hw else (left + right) / 2
    return v

_ig_ban = {}
def ig_banner_rgba(wpx):
    if wpx not in _ig_ban:
        im = cv2.imread(EDL["ig_banner"], cv2.IMREAD_UNCHANGED)
        a_ = im[..., 3]; ys, xs = np.where(a_ > 8); im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        im = cv2.resize(im, (wpx, int(im.shape[0] * wpx / im.shape[1])), interpolation=cv2.INTER_AREA).astype(np.float32)
        _ig_ban[wpx] = (im[..., :3], im[..., 3:4] / 255.0)
    return _ig_ban[wpx]
def ig_stack(src, raw_, st, st0, s, t, T, i):
    """9:16 stack frame (before the grade): webcam band on top, game band below, seam line, captions behind him"""
    face = s["kind"] == "face"; seam = FACEH if face else CAMH
    canvas = np.empty((VH, VW, 3), np.float32)
    if face:                                                    # the X edit's face camera, re-framed for the tall band
        top = warp_cam(src, vcam(st, "face", VW, seam), vcam(st0, "face", VW, seam), VW, seam)
        if s.get("mask_text"):                                  # tall band: behind him they'd hide behind his head, so in front, on his chest
            top = mask_text_fx(top, s, T, i, _seg_ig, x=0.5, y=EDL.get("ig_caption_y", 0.74), k=1.3, behind=False)
    else:                                                       # his live webcam, slow push over the shot
        u = min(1.0, max(0.0, (t - s["a"]) / max(0.1, s["b"] - s["a"])))
        z = max(VW / fw, seam / fh) * EDL.get("ig_cam_zoom", 1.12) * (1.0 + 0.05 * u)
        c = raw_[fy_:fy_ + fh, fx_:fx_ + fw]
        c = cv2.addWeighted(c, 1.5, cv2.GaussianBlur(c, (0, 0), 2.0), -0.5, 0)    # webcams are soft: sharpen before upscaling
        cx, cy = EDL.get("ig_cam_center", [fw / 2, fh * 0.45])     # webcam coords; he sits a little above centre
        M = np.float32([[z, 0, VW / 2 - z * cx], [0, z, seam / 2 - z * cy]])
        top = cv2.warpAffine(c, M, (VW, seam), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    canvas[:seam] = top
    gh_ = VH - seam
    if face:                                                    # strip below his face: the game, board framing
        gs = dict(st, cx=BOARD[0], cy=BOARD[1], z=BOARD[2], rot=0.0, yaw=0.0, pitch=0.0)
        canvas[seam:] = warp_cam(raw_, vcam(gs, "game", VW, gh_), vcam(gs, "game", VW, gh_), VW, gh_)
    else:
        canvas[seam:] = warp_cam(src, vcam(st, "game", VW, gh_, True), vcam(st0, "game", VW, gh_, True), VW, gh_)
    canvas[seam:seam + 36] *= np.linspace(0.55, 1.0, 36, dtype=np.float32)[:, None, None]   # soft shadow under the seam
    canvas[seam - 4:seam + 4] = (24, 252, 83)                   # Kick green seam
    return canvas
GH_FACE = EDL.get("ig_face_h", 1240)
GH_PIC = EDL.get("ig_ghost_h", 1050)                 # the X picture's height on the 9:16 canvas: its sides are cropped to fill the phone
                                                     # (Dylan: "so much room, zoom in more on mobile"); 608 = the whole 16:9 frame
def ig_ghost(xpic, src, raw_, st, st0, s, T, i):
    """9:16 ghost frame (graded): the 16:9 X picture (or a tall face panel) centred over a blurred copy of itself"""
    if s["kind"] == "face":
        panel = post(warp_cam(src, vcam(st, "face", VW, GH_FACE), vcam(st0, "face", VW, GH_FACE), VW, GH_FACE), st)
        if s.get("mask_text"):                                  # tall panel: behind him they'd hide behind his head, so in front, on his chest
            panel = mask_text_fx(panel, s, T, i, _seg_ig, x=0.5, y=EDL.get("ig_caption_y", 0.76), k=1.3, behind=False)
    else:
        cw = min(W, int(round(H * VW / GH_PIC))); x0_ = (W - cw) // 2                 # centre crop to VW:GH_PIC
        panel = cv2.resize(xpic[:, x0_:x0_ + cw], (VW, min(GH_PIC, VW * H // cw)), interpolation=cv2.INTER_AREA)
    ph = panel.shape[0]; y0 = (VH - ph) // 2
    small = cv2.GaussianBlur(cv2.resize(panel, (96, max(8, 96 * ph // VW)), interpolation=cv2.INTER_AREA), (0, 0), 2.2)
    bw = int(VH * VW / ph); bg = cv2.resize(small, (bw, VH), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    canvas = bg[:, (bw - VW) // 2:(bw - VW) // 2 + VW] * 0.38
    f = 28                                                      # feathered top/bottom edge: the picture melts into its ghost
    ramp = np.linspace(0, 1, f, dtype=np.float32)[:, None, None]
    pf = panel.astype(np.float32)
    canvas[y0 + f:y0 + ph - f] = pf[f:ph - f]
    canvas[y0:y0 + f] = canvas[y0:y0 + f] * (1 - ramp) + pf[:f] * ramp
    canvas[y0 + ph - f:y0 + ph] = canvas[y0 + ph - f:y0 + ph] * ramp + pf[ph - f:] * (1 - ramp)
    if s["kind"] != "face": canvas = draw_reactions(canvas, raw_, i, vert=y0)
    return np.clip(canvas, 0, 255).astype(np.uint8), y0, ph
def ig_ghost_finish(o, y0, ph, T):
    """banner just under the picture (kept above the Reels caption zone), fades with the edit"""
    if not EDL.get("ig_banner"): return o
    rgb, al = ig_banner_rgba(int(VW * 0.5))
    fade = min(1.0, T / 0.3) * min(1.0, max(0.0, (DUR - 0.05 - T) / 0.45))
    if fade <= 0: return o
    out = o.astype(np.float32)
    _blit(out, rgb, al, (VW - al.shape[1]) // 2, min(y0 + ph + 26, VH - IG_SAFE_B - al.shape[0]), fade)
    return np.clip(out, 0, 255).astype(np.uint8)
def ig_stack_finish(o, s, T):
    """after the grade: banner on the seam (fades with the edit), so it moves with the layout and never sits on his face"""
    if not EDL.get("ig_banner"): return o
    seam = FACEH if s["kind"] == "face" else CAMH
    rgb, al = ig_banner_rgba(int(VW * 0.5))
    fade = min(1.0, T / 0.3) * min(1.0, max(0.0, (DUR - 0.05 - T) / 0.45))
    if fade <= 0: return o
    out = o.astype(np.float32)
    _blit(out, rgb, al, (VW - al.shape[1]) // 2, seam - al.shape[0] - 22, fade)
    return np.clip(out, 0, 255).astype(np.uint8)
def vertical(panel):
    """9:16 frame: the panel centred, a zoomed, blurred, darkened copy of it filling the background"""
    small = cv2.GaussianBlur(cv2.resize(panel, (108, 83), interpolation=cv2.INTER_AREA), (0, 0), 2.0)
    bw = int(VH * PW / PH); bg = cv2.resize(small, (bw, VH), interpolation=cv2.INTER_LINEAR)
    x0 = (bw - VW) // 2
    canvas = bg[:, x0:x0 + VW] * 0.42
    canvas[PY:PY + PH] = panel
    return canvas

# ---------- text overlays (opt-in): e.g. {"src": 57.0, "from": 0, "to": 2000, "fmt": "-${:,}", "count": 0.45,
#   "pos": [540, 820], "size": 200, "font": ".../Poppins-BoldItalic.ttf", "color": [255, 46, 62], "darken": 0.35, "focus": [540, 600]}
# counts up from `from` to `to` over `count` s (ease-out), then slams in (scale pop + shake), darkens the rest of the frame
# around `focus`, holds to the end and fades with the end glitch. Drawn in output pixels, after the grade.
# Wins: "color": [60, 230, 120], "stroke": [0, 60, 24], "wash": [0, 34, 10] (defaults are the red loss look).
OVERLAYS = EDL.get("overlays", [])
for ov in OVERLAYS:
    ov["_t0"] = src_out(ov["src"]); ov["_t1"] = src_out(ov["until_src"]) if "until_src" in ov else None
_txt_cache = {}
def text_rgba(text, ov):
    key = (text, ov.get("size", 200), tuple(ov.get("color", [255, 46, 62])))
    if key not in _txt_cache:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        font = ImageFont.truetype(ov["font"], ov.get("size", 200))
        l, t, r, b = font.getbbox(text, stroke_width=10)
        pad = 60; w, h = r - l + 2 * pad, b - t + 2 * pad
        col = tuple(ov.get("color", [255, 46, 62]))
        glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(glow).text((pad - l, pad - t), text, font=font, fill=col + (255,), stroke_width=14, stroke_fill=col + (255,))
        glow = glow.filter(ImageFilter.GaussianBlur(22))
        shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).text((pad - l + 8, pad - t + 12), text, font=font, fill=(0, 0, 0, 200), stroke_width=10, stroke_fill=(0, 0, 0, 200))
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        face = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(face).text((pad - l, pad - t), text, font=font, fill=col + (255,), stroke_width=7, stroke_fill=tuple(ov.get("stroke", [70, 0, 8])) + (255,))
        img = Image.alpha_composite(Image.alpha_composite(glow, shadow), face)
        a = np.asarray(img).astype(np.float32)
        _txt_cache[key] = (a[..., [2, 1, 0]], a[..., 3:4] / 255.0)        # BGR, alpha
    return _txt_cache[key]
def draw_overlays(o, T, scale=1.0, ig=False):
    if not OVERLAYS: return o
    out = None
    for ov in OVERLAYS:
        d = T - ov["_t0"]
        if d < 0 or (ov["_t1"] is not None and T > ov["_t1"] + 0.2): continue
        style = ov.get("style", "slam")
        if out is None: out = o.astype(np.float32)
        h_, w_ = out.shape[:2]
        cnt = ov.get("count", 0.45); fade_end = 1.0
        if T > DUR - 0.45: fade_end = max(0.0, 1 - (T - (DUR - 0.45)) / 0.45)
        if ov["_t1"] is not None and T > ov["_t1"]: fade_end = min(fade_end, max(0.0, 1 - (T - ov["_t1"]) / 0.2))
        u = min(1.0, d / cnt) if cnt > 0 else 1.0
        e = 1 - (1 - u) ** 3
        val = int(round(ov.get("from", 0) + (ov.get("to", 0) - ov.get("from", 0)) * e))
        text = ov.get("fmt", "{}").format(val)
        ds = d - cnt                                             # time since the count finished (the slam)
        if style == "pop":                                       # springy scale-in, no slam
            sc = 1.0 + (0.0 - 1.0) * math.exp(-d * 9) * math.cos(d * 22) if d < 0.6 else 1.0
            sc = max(0.05, sc)
        elif style == "glitch": sc = 1.0
        elif ds < 0: sc = 0.75 + 0.25 * e
        else: sc = 1.0 + 0.35 * math.exp(-ds * 18)
        rgb, al = text_rgba(text, ov)
        sc *= scale
        rgb = cv2.resize(rgb, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR); al = cv2.resize(al, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
        if al.ndim == 2: al = al[..., None]
        # darken around the focus point after the slam (spotlight on the balance + number)
        dk = ov.get("darken", 0.0) * min(1.0, max(0.0, ds) / 0.25) * fade_end
        if dk > 0:
            fx_, fy_ = ov.get("ig_pos", [VW / 2, (CAMH + VH - IG_SAFE_B) / 2]) if ig else [v * scale for v in ov.get("focus", ov["pos"])]
            yy, xx = np.ogrid[:h_, :w_]
            r = np.sqrt(((xx - fx_) / (w_ * 0.55)) ** 2 + ((yy - fy_) / (h_ * 0.30)) ** 2)
            out *= (1 - dk * np.clip(r - 0.35, 0, 1)[..., None])
            if ds >= 0:                                          # brief colour wash (RGB, default red)
                for ch, amt in zip((2, 1, 0), ov.get("wash", [40, 0, 0])):
                    if amt: out[..., ch] = np.minimum(255, out[..., ch] + amt * dk * math.exp(-ds * 3))
        shake = 0.0 if (ds < 0 or style != "slam") else 26 * scale * math.exp(-ds * 9)
        if style == "glitch" and ds < 0.35:                      # RGB-split + sliced jitter while it locks in
            gk = 1.0 if ds < 0 else 1 - ds / 0.35
            off = int((10 + 26 * gk) * scale)
            b_, g_, r_ = rgb[..., 0], rgb[..., 1], rgb[..., 2]
            rgb = np.stack([np.roll(b_, -off, 1), g_, np.roll(r_, off, 1)], -1)
            al = np.maximum(al, np.roll(al, off, 1) * 0.6)
            hh = rgb.shape[0]; yb_ = 0
            while yb_ < hh:
                bh = int(rng.integers(6, 28) * scale + 1)
                if rng.random() < 0.5 * gk:
                    sh = int(rng.integers(-40, 41) * gk * scale)
                    rgb[yb_:yb_ + bh] = np.roll(rgb[yb_:yb_ + bh], sh, 1); al[yb_:yb_ + bh] = np.roll(al[yb_:yb_ + bh], sh, 1)
                yb_ += bh
            if rng.random() < 0.25 * gk: al = al * 0.35                   # flicker
        px_, py_ = ov.get("ig_pos", [VW / 2, (CAMH + VH - IG_SAFE_B) / 2]) if ig else (ov["pos"][0] * scale, ov["pos"][1] * scale)
        cx = px_ + shake * math.sin(d * 97); cy = py_ + shake * math.cos(d * 83)
        th, tw = al.shape[:2]; x0 = int(cx - tw / 2); y0 = int(cy - th / 2)
        xa, ya = max(0, x0), max(0, y0); xb, yb = min(w_, x0 + tw), min(h_, y0 + th)
        if xb <= xa or yb <= ya: continue
        a_ = al[ya - y0:yb - y0, xa - x0:xb - x0] * fade_end * min(1.0, d / 0.06)
        out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - a_) + rgb[ya - y0:yb - y0, xa - x0:xb - x0] * a_
    return o if out is None else np.clip(out, 0, 255).astype(np.uint8)

_ff_cache = {}
def _ff_text(text, font, size, fill, stroke, sw):
    key = (text, font, size, fill, stroke, sw)
    if key not in _ff_cache:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        f_ = ImageFont.truetype(font, size); l, t, r, b = f_.getbbox(text, stroke_width=sw); pad = 24
        im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 5, pad - t + 7), text, font=f_, fill=(0, 0, 0, 170), stroke_width=sw, stroke_fill=(0, 0, 0, 170))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(5)))
        ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f_, fill=fill + (255,), stroke_width=sw, stroke_fill=stroke + (255,))
        a_ = np.asarray(im).astype(np.float32); _ff_cache[key] = (a_[..., [2, 1, 0]], a_[..., 3:4] / 255.0)
    return _ff_cache[key]
def _blit(out, rgb, al, x0, y0, alpha=1.0):
    h_, w_ = out.shape[:2]; th, tw = al.shape[:2]
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(w_, x0 + tw), min(h_, y0 + th)
    if xb <= xa or yb <= ya: return
    a_ = al[ya - y0:yb - y0, xa - x0:xb - x0] * alpha
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - a_) + rgb[ya - y0:yb - y0, xa - x0:xb - x0] * a_
def _font(path, local):   # the Linux font, else the copy in <repo>/pack/fonts (Windows PC)
    alt = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pack", "fonts", local)
    return path if os.path.exists(path) or not os.path.exists(alt) else alt
OSD_FONT = _font("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "consolab.ttf")
_seg = {"sess": None, "prev": None, "k": None}
_seg_ig = {"sess": None, "prev": None, "k": None}                 # the 9:16 stack's face band has its own matte history
def person_mask(img, key, _seg=_seg):
    """soft person matte of the output frame (computed every other frame, smoothed over time)"""
    if _seg["k"] is not None and key - _seg["k"] < 2 and _seg["prev"] is not None and _seg["prev"].shape == img.shape[:2]: return _seg["prev"]
    from rembg import new_session, remove
    from PIL import Image
    if _seg["sess"] is None:
        try:
            import onnxruntime; onnxruntime.preload_dlls()  # without torch imported, ORT can't find the pip CUDA/cuDNN DLLs and drops to CPU
        except Exception: pass
        _seg["sess"] = new_session("isnet-general-use")
    small = cv2.resize(np.clip(img, 0, 255).astype(np.uint8), (img.shape[1] // 2, img.shape[0] // 2), interpolation=cv2.INTER_AREA)
    m = np.asarray(remove(Image.fromarray(small[..., ::-1]), session=_seg["sess"], only_mask=True)).astype(np.float32) / 255.0
    m = cv2.resize(m, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_LINEAR)
    m = np.clip((m - 0.15) / 0.7, 0, 1)
    if _seg["prev"] is not None and _seg["prev"].shape == m.shape and _seg["k"] is not None and key - _seg["k"] <= 3: m = 0.55 * m + 0.45 * _seg["prev"]
    _seg["prev"], _seg["k"] = m, key
    return m
def mask_text_fx(img, s, T, key, seg=_seg, x=None, y=None, k=1.0, behind=True):
    act = [mt for mt in s.get("mask_text", []) if mt["_t0"] <= T < mt["_t1"] + 0.25]
    if not act: return img
    out = img.astype(np.float32); h_, w_ = out.shape[:2]; base = out.copy()
    for mt in act:
        d = T - mt["_t0"]; fade = min(1.0, max(0.0, 1 - (T - mt["_t1"]) / 0.25)) * min(1.0, d / 0.05)
        if mt.get("_cut") and T >= mt["_t1"]: continue                     # word captions cut straight to the next word
        if mt.get("_cut"): fade = min(1.0, d / 0.03)
        glitchy = mt.get("style") == "glitch"
        sc = (1.0 + 0.22 * math.exp(-d * 18)) if glitchy else (1.0 + 0.45 * math.exp(-d * 14))
        rgb, al = _ff_text(mt["text"], mt.get("font", CAP_FONT), int(mt.get("size", 330) * w_ / W * k), tuple(mt.get("color", [255, 255, 255])),
                           tuple(mt.get("stroke", [255, 255, 255])), 0)
        rgb = cv2.resize(rgb, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR); al = cv2.resize(al, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
        if al.ndim == 2: al = al[..., None]
        if glitchy:                                                          # RGB split + sliced jitter as it lands, a flicker now and then
            gk = max(0.0, 1 - d / 0.22) + (0.35 if (int(T * 30) % 17 == 0) else 0.0)
            if gk > 0:
                off = int((6 + 34 * gk) * w_ / W)
                rgb = np.stack([np.roll(rgb[..., 0], -off, 1), rgb[..., 1], np.roll(rgb[..., 2], off, 1)], -1)
                al = np.maximum(al, np.roll(al, off, 1) * 0.7)
                yb_ = 0; hh_ = rgb.shape[0]
                while yb_ < hh_:
                    bh = int(rng.integers(6, 26) * w_ / W) + 1
                    if rng.random() < 0.55 * min(1.0, gk):
                        shf = int(rng.integers(-48, 49) * min(1.0, gk) * w_ / W)
                        rgb[yb_:yb_ + bh] = np.roll(rgb[yb_:yb_ + bh], shf, 1); al[yb_:yb_ + bh] = np.roll(al[yb_:yb_ + bh], shf, 1)
                    yb_ += bh
        sh = 14 * math.exp(-d * 9) * w_ / W
        x0 = int(w_ * (mt.get("x", 0.5) if x is None else x) - al.shape[1] / 2 + sh * math.sin(d * 97)); y0 = int(h_ * (mt.get("y", 0.34) if y is None else y) - al.shape[0] / 2 + sh * math.cos(d * 83))
        _blit(out, rgb, al, x0, y0, fade)
    if not behind: return np.clip(out, 0, 255).astype(np.uint8) if img.dtype == np.uint8 else out.astype(img.dtype)
    m = person_mask(base, key, seg)[..., None]
    res = base * m + out * (1 - m)
    return np.clip(res, 0, 255).astype(np.uint8) if img.dtype == np.uint8 else res.astype(img.dtype)
CAP_FONT = _font("/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf", "InterDisplay-BlackItalic.otf")
_scan = {}
def ff_fx(o, T):
    if not FFR: return o
    cur = next((r for r in FFR if r[0] <= T < r[1]), None)
    play = next((r for r in FFR if r[1] <= T < r[1] + 0.8 and not any(q[0] <= T < q[1] for q in FFR)), None)
    if cur is None and play is None: return o
    h_, w_ = o.shape[:2]; sc = w_ / W; out = o.astype(np.float32)
    if cur:
        T0, T1, cfg = cur; d = T - T0
        gray = cv2.cvtColor(o, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]
        out = gray + (out - gray) * 0.62                                  # washed-out tape colour
        out = (out - 128) * 1.12 + 128; out[..., 0] += 10; out[..., 2] -= 4
        k = max(1, int(4 * sc)); b_, g_, r_ = cv2.split(out)               # chroma bleed
        out = cv2.merge([np.roll(b_, -k, 1), g_, np.roll(r_, k, 1)])
        if (h_, w_) not in _scan:
            m_ = np.ones((h_, 1, 1), np.float32); m_[::max(2, int(4 * sc))] = 0.8; _scan[(h_, w_)] = m_
        out *= _scan[(h_, w_)]
        burst = max(0.0, 1 - d / 0.22)                                    # tracking burst on the way in
        bands = [((T * 0.55) % 1.25 - 0.1, 0.05 + 0.12 * burst)]
        if burst > 0: bands.append((0.5 + 0.4 * math.sin(T * 40), 0.25 * burst))
        for yc, bh in bands:
            y0 = int(yc * h_); y1 = min(h_, y0 + int(bh * h_)); y0 = max(0, y0)
            if y1 <= y0: continue
            yb_ = y0
            while yb_ < y1:
                hh = int(rng.integers(3, 12) * sc) + 1
                out[yb_:yb_ + hh] = np.roll(out[yb_:yb_ + hh], int(rng.integers(-38, 39) * sc * (0.5 + burst)), 1)
                yb_ += hh
            nz = rng.random((y1 - y0, w_, 1)).astype(np.float32)
            out[y0:y1] = out[y0:y1] * 0.75 + (nz > 0.93) * 200 + 25
        jit = int(rng.integers(0, 3) * sc)
        if jit: out = np.roll(out, jit, 0)
        rgb, al = _ff_text("\u25B6\u25B6 " + cfg.get("label", "x8"), OSD_FONT, int(78 * sc), (255, 255, 255), (20, 20, 20), max(1, int(3 * sc)))
        _blit(out, rgb, al, int(70 * sc), int(52 * sc), 0.92 if int(T * 6) % 6 else 0.75)
        cap = cfg.get("caption")
        if cap:
            n_ = max(1, min(len(cap), int(len(cap) * (d - 0.15) / 0.45) + 1)) if d > 0.15 else 0   # typed on
            if n_:
                rgb, al = _ff_text(cap, CAP_FONT, int(cfg.get("size", 96) * sc), (255, 255, 255), (0, 0, 0), max(2, int(9 * sc)))
                full_w = al.shape[1]
                rgb2, al2 = _ff_text(cap[:n_], CAP_FONT, int(cfg.get("size", 96) * sc), (255, 255, 255), (0, 0, 0), max(2, int(9 * sc)))
                _blit(out, rgb2, al2, int(w_ / 2 - full_w / 2), int(h_ * cfg.get("y", 0.80) - al.shape[0] / 2))
    else:
        rgb, al = _ff_text("\u25B6 PLAY", OSD_FONT, int(78 * sc), (255, 255, 255), (20, 20, 20), max(1, int(3 * sc)))
        _blit(out, rgb, al, int(70 * sc), int(52 * sc), min(1.0, (play[1] + 0.8 - T) / 0.2))
    return np.clip(out, 0, 255).astype(np.uint8)

vid = f"{WORK}/video_only.mp4"; vid_ig = f"{WORK}/video_only_ig.mp4"
AUDIO_ONLY = "--audio-only" in sys.argv and os.path.exists(vid)   # re-mix audio onto the last rendered picture(s)
if os.environ.get("HYPE_SYNC_ONLY"): AUDIO_ONLY = True                # voice-sync check only: no picture, exits after the voice plan
def _has_nvenc():
    """NVIDIA hardware encoder available (e.g. Dylan's RTX 2070 Super)? Checked with a real 1-frame test encode."""
    if os.environ.get("HYPE_NO_GPU"): return False
    try:
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.1", "-c:v", "h264_nvenc", "-f", "null", "-"],
                           capture_output=True, timeout=20)
        return r.returncode == 0
    except Exception: return False
NVENC = _has_nvenc()
def venc_args(final=False, vbr=None):
    if NVENC:
        q = ["-c:v", "h264_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "19" if final else "16", "-b:v", "0"]
        return q + (["-maxrate", f"{vbr}k", "-bufsize", f"{vbr * 2}k"] if vbr else [])
    q = ["-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "medium", "-crf", "18" if final else "17"]
    return q + (["-maxrate", f"{vbr}k", "-bufsize", f"{vbr * 2}k"] if vbr else [])
def encoder(path, w, h):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(FPS),
                             "-i", "-", *venc_args(), "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
# parallel picture render: "--parallel N" splits the frames into N chunks rendered by N copies of this script ("--part k/N"),
# then joins them without re-encoding. Default N = number of CPU cores (HYPE_PARALLEL=1 turns it off).
PART = next((a_.split("=", 1)[1] if "=" in a_ else sys.argv[sys.argv.index(a_) + 1] for a_ in sys.argv if a_.startswith("--part")), None)
PAR = int(os.environ.get("HYPE_PARALLEL", next((sys.argv[sys.argv.index(a_) + 1] if a_ == "--parallel" else a_.split("=", 1)[1] for a_ in sys.argv if a_ == "--parallel" or a_.startswith("--parallel=")), os.cpu_count() or 1)))
if NVENC and "HYPE_PARALLEL" not in os.environ: PAR = min(PAR, 5)   # GeForce cards cap concurrent NVENC sessions (5 on older drivers)
# per-shot "blur": [{"rect": [x, y, w, h] (source px), "t": [src_a, src_b] (optional, 0.08 s fades), "sigma": 22,
#   "darken": 0.15, "feather": 18}] -> hides a number (e.g. the win on a cold-open tease) without hiding the moment
def blur_rect(src, b, t):
    k = 1.0
    if "t" in b: k = max(0.0, min(1.0, (t - b["t"][0]) / 0.08, (b["t"][1] - t) / 0.08))
    if k <= 0: return src
    x, y, w, h = [int(v) for v in b["rect"]]; pad = int(b.get("feather", 18))
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(src.shape[1], x + w + pad), min(src.shape[0], y + h + pad)
    roi = src[y0:y1, x0:x1]
    bl = cv2.GaussianBlur(roi, (0, 0), b.get("sigma", 22)) * (1 - b.get("darken", 0.15))
    m = np.zeros(roi.shape[:2], np.float32); m[y - y0:y - y0 + h, x - x0:x - x0 + w] = 1
    m = (cv2.GaussianBlur(m, (0, 0), max(1, pad / 2)) * k)[..., None]
    src = src.copy(); src[y0:y1, x0:x1] = roi * (1 - m) + bl * m
    return src
# "age_tag": 18+ badge, bottom-left, over everything for the first seconds. ON by default; "age_tag": null turns it off.
#   {"text": "18+", "from": 0.0, "to": 1.8, "size": 0.085 (diameter, of the frame's short side), "font": ttf}
AGE = EDL.get("age_tag", {})
if AGE is not None: AGE = {"text": "18+", "from": 0.0, "to": 1.8, "size": 0.085, **AGE}
_age = {}
def age_badge(dpx):
    if dpx not in _age:
        from PIL import Image, ImageDraw, ImageFont
        k = 4; D = dpx * k; im = Image.new("RGBA", (D, D), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
        g.ellipse([0, 0, D - 1, D - 1], fill=(255, 255, 255, 255))                        # white ring
        r = int(D * 0.075); g.ellipse([r, r, D - 1 - r, D - 1 - r], fill=(214, 32, 39, 255))   # red disc
        fonts = [AGE.get("font"), os.path.join(EDL.get("sfx_dir") or "", "tools/Poppins-BoldItalic.ttf"),
                 "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 _font("/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf", "Inter-ExtraBold.otf")]
        font = next(ImageFont.truetype(f, int(D * 0.40)) for f in fonts if f and os.path.exists(f))
        l, t, r_, b = g.textbbox((0, 0), AGE["text"], font=font)
        g.text(((D - (r_ - l)) / 2 - l, (D - (b - t)) / 2 - t), AGE["text"], font=font, fill=(255, 255, 255, 255))
        a = np.asarray(im.resize((dpx, dpx), Image.LANCZOS)).astype(np.float32)
        al = a[..., 3] / 255.0
        _age[dpx] = (a[..., [2, 1, 0]] * al[..., None], al)
    return _age[dpx]
def draw_age_tag(o, T, ow=None, oh=None):
    if not AGE: return o
    d = T - AGE["from"]; fade = min(1.0, max(0.0, (AGE["to"] - T) / 0.25))
    if d < 0 or fade <= 0: return o
    ow_, oh_ = ow or W, oh or H; base = min(ow_, oh_)
    sc = max(0.0, 1 - math.exp(-d * 16) * math.cos(d * 18))                    # quick pop in
    D = max(8, int(AGE["size"] * base * sc))
    rgb, al = age_badge(D)
    m = int(0.03 * base)
    cx = int(0.035 * base * 16 / 9) + int(AGE["size"] * base) // 2 if ow_ > oh_ else m + int(AGE["size"] * base) // 2
    cy = (oh_ if ow_ > oh_ else (VH - IG_SAFE_B if IGL in ("stack", "ghost") else PY + PH)) - m - int(AGE["size"] * base) // 2     # 9:16: clear of the app UI
    x0, y0 = cx - D // 2, cy - D // 2
    out = o.astype(np.float32); a_ = al[..., None] * fade
    sh = cv2.GaussianBlur(al, (0, 0), max(1, D / 18))[..., None] * fade * 0.45
    ys, xs = slice(y0 + D // 24, y0 + D // 24 + D), slice(x0 + D // 30, x0 + D // 30 + D)
    out[ys, xs] *= (1 - sh)
    out[y0:y0 + D, x0:x0 + D] = out[y0:y0 + D, x0:x0 + D] * (1 - a_) + rgb * fade
    return np.clip(out, 0, 255).astype(np.uint8)
_spr = {}
def sprite(path, hpx):
    """pop-up character cut-out (BGRA png) at hpx tall -> premultiplied BGR, alpha"""
    if (path, hpx) not in _spr:
        im = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        im = cv2.resize(im, None, fx=hpx / im.shape[0], fy=hpx / im.shape[0], interpolation=cv2.INTER_AREA).astype(np.float32)
        al = im[..., 3:4] / 255.0
        _spr[(path, hpx)] = (im[..., :3] * al, al[..., 0])
    return _spr[(path, hpx)]
def pop_out_t(f):
    p = f["pop"]; return max(f["_T1"] - 0.08, f["_T0"] + POP_IN + VOICE_DELAY + p["_len"] - 0.15)
def freeze_dim(T):
    k = 0.0
    for f in FRZ:
        if f["_T0"] <= T < f["_T1"] + 0.15:
            k = max(k, min(1.0, (T - f["_T0"]) / 0.12) * min(1.0, max(0.0, f["_T1"] + 0.15 - T) / 0.15))
    return k
def draw_pops(o, T, ow=None, oh=None):
    """springy pop-up: rises from its corner with an overshoot and a wobble, bobs with its own voice, shrinks away"""
    out = None
    for f in FRZ:
        p = f["pop"]
        if not p: continue
        d = T - (f["_T0"] + POP_IN); e = (T - pop_out_t(f)) / 0.18
        if d < 0 or e >= 1: continue
        if out is None: out = o.astype(np.float32)
        ow_, oh_ = ow or W, oh or H; base = min(ow_, oh_)            # sized off the short side: same look on 16:9 and 9:16
        hpx = int(p.get("size", POPS.get("size", 0.40)) * base)       # per-pop "size" for tall full-body art
        rgb, al = sprite(p["_img"], hpx); sh_, sw_ = al.shape
        sc = 1 - math.exp(-d * 9) * math.cos(d * 20)                 # 0 -> overshoot ~1.25 -> settle at 1
        vi = int((T - (f["_T0"] + POP_IN + VOICE_DELAY)) * FPS)
        env = float(p["_env"][vi]) if 0 <= vi < len(p["_env"]) else 0.0
        ky = 1 + 0.06 * env; kx = 1 - 0.03 * env                      # talks: stretches a little with its voice
        if e > 0: sc *= (1 - e) ** 1.5 * (1 + 0.6 * e)
        sc = max(sc, 0.0)
        right = p["corner"].endswith("r"); top = p["corner"].startswith("t")
        mx = int(0.035 * base * 16 / 9) if ow_ > oh_ else int(0.035 * ow_); my = int(0.03 * base)
        ax = ow_ - mx - sw_ / 2 if right else mx + sw_ / 2
        ay = (my + sh_) if top else oh_ - my                             # the sprite's bottom centre sits here
        if oh_ > ow_ and not top: ay = min(ay, VH - IG_SAFE_B if IGL in ("stack", "ghost") else PY + PH + int(0.12 * PH))  # 9:16: panel edge / above the Reels UI
        ay += base * 0.22 * math.exp(-d * 12) + (base * 0.12 * e if e > 0 else 0)
        rot = (-7 if right else 7) + 14 * math.exp(-d * 5) * math.sin(d * 16) + (25 * e if e > 0 else 0) * (1 if right else -1)
        c, s_ = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        A = np.array([[c * sc * kx, -s_ * sc * ky], [s_ * sc * kx, c * sc * ky]])
        M = np.hstack([A, (np.array([ax, ay]) - A @ np.array([sw_ / 2, sh_]))[:, None]])
        a_ = cv2.warpAffine(al, M, (ow_, oh_), flags=cv2.INTER_LINEAR, borderValue=0)
        if a_.max() <= 0: continue
        Ms = M.copy(); Ms[:, 2] += (0.0045 * base * 16 / 9, 0.012 * base)
        shd = cv2.GaussianBlur(cv2.warpAffine(al, Ms, (ow_, oh_), flags=cv2.INTER_LINEAR, borderValue=0), (0, 0), 9)
        out *= (1 - 0.4 * shd)[..., None]
        out = out * (1 - a_)[..., None] + cv2.warpAffine(rgb, M, (ow_, oh_), flags=cv2.INTER_LINEAR, borderValue=0)
    return o if out is None else np.clip(out, 0, 255).astype(np.uint8)
# ---------- his reaction over the game (Dylan, 2026-10-17: "I can hear him reacting but can't see him") ----------
# "reactions": [{"src0": a, "src1": b, "style": "pip" | "ghost", "side": "r" | "l", "size": .., "alpha": .., "tilt": .., "pos": [x, y]}]
# on game shots whose picture is inside src0..src1 (source times) his webcam (face_rect of the SAME frame, so it is live) is shown:
#   pip   - a white-framed webcam window, tilted in perspective, that swings in from the side, sways a little while the webcam
#           view pushes in and pans across him, and swings back out (size = width as a share of the frame, default 0.36)
#   ghost - his whole webcam laid big and semi-transparent over the win with soft oval edges, rising from the bottom edge
#           (side "c" | "r" | "l", default "c"; size = height share, default 0.62; alpha default 0.45; "matte": true cuts him out
#           of his background instead, which loses him when he leans out of frame)
REACT = [dict(r) for r in EDL.get("reactions", [])]
for r in REACT:
    idx = [i for i, (si_, t_, _) in enumerate(frames) if SHOTS[si_]["kind"] != "face" and r["src0"] <= t_ <= r["src1"]]
    runs_ = []                                          # the longest unbroken run only (a cold open reusing the moment isn't part of it)
    for i in idx:
        if runs_ and i == runs_[-1][1] + 1: runs_[-1][1] = i
        else: runs_.append([i, i])
    r["_i0"], r["_i1"] = max(runs_, key=lambda x: x[1] - x[0]) if runs_ else (1, 0)
_rseg = {"sess": None, "prev": None, "k": None}
def _face_matte(crop, key):
    if _rseg["k"] is not None and 0 <= key - _rseg["k"] < 2 and _rseg["prev"] is not None and _rseg["prev"].shape == crop.shape[:2]:
        return _rseg["prev"]
    from rembg import new_session, remove
    from PIL import Image
    if _rseg["sess"] is None:
        try:
            import onnxruntime; onnxruntime.preload_dlls()
        except Exception: pass
        _rseg["sess"] = new_session("isnet-general-use")
    m = np.asarray(remove(Image.fromarray(np.clip(crop, 0, 255).astype(np.uint8)[..., ::-1]), session=_rseg["sess"], only_mask=True))
    m = np.clip((m.astype(np.float32) / 255.0 - 0.15) / 0.7, 0, 1)
    if _rseg["prev"] is not None and _rseg["prev"].shape == m.shape and _rseg["k"] is not None and key - _rseg["k"] <= 3:
        m = 0.55 * m + 0.45 * _rseg["prev"]
    _rseg["prev"], _rseg["k"] = m, key
    return m
def draw_reactions(o, raw_, i, vert=None):
    """vert = top of the 16:9 picture on the 9:16 ghost canvas: every reaction becomes a big pip centred in the space above it"""
    act = [r for r in REACT if r["_i0"] <= i <= r["_i1"]]
    if not act: return o
    out = o.astype(np.float32); H_, W_ = out.shape[:2]
    for r in act:
        if vert is not None:
            r = {k: v for k, v in r.items() if k not in ("pos", "size", "style", "tilt")}
            r.update(style="pip", size=EDL.get("ig_react_size", 0.72), pos=[W_ / 2, max(0.0, vert / 2 + 20)])
        fx_, fy_, fw_, fh_ = [int(v) for v in r.get("rect", EDL["face_rect"])]      # "rect": a tighter crop when he sits in one part of the cam
        crop = raw_[fy_:fy_ + fh_, fx_:fx_ + fw_].astype(np.float32)
        crop = cv2.addWeighted(crop, 1.6, cv2.GaussianBlur(crop, (0, 0), 2.0), -0.6, 0)    # webcams are soft: sharpen before upscaling
        n_ = max(1, r["_i1"] - r["_i0"]); u = (i - r["_i0"]) / n_
        e_in = min(1.0, (i - r["_i0"]) / (0.3 * FPS)); e_in = 1 - (1 - e_in) ** 3
        e_out = min(1.0, max(0.0, (r["_i1"] - i) / (0.25 * FPS))); e_out = e_out * e_out * (3 - 2 * e_out)
        sd = 1 if r.get("side", "r") == "r" else -1
        if r.get("style", "pip") == "ghost":
            th = int(H_ * r.get("size", 0.62) * (1 + 0.05 * u)); tw = int(th * fw_ / fh_)
            big = cv2.resize(crop, (tw, th), interpolation=cv2.INTER_CUBIC)
            yy, xx = np.mgrid[0:th, 0:tw].astype(np.float32)
            d_ = np.sqrt(((xx - tw / 2) / (tw * 0.56)) ** 2 + ((yy - th * 0.55) / (th * 0.62)) ** 2)
            al = np.clip((1.0 - d_) / 0.3, 0, 1) ** 1.2                                           # soft oval, no webcam edges
            if r.get("matte"): al = al * cv2.resize(_face_matte(cv2.resize(crop, (fw_ * 2, fh_ * 2), interpolation=cv2.INTER_CUBIC), i), (tw, th))
            al = al * r.get("alpha", 0.45) * min(e_in, e_out)
            sd_ = r.get("side", "c")
            x0 = (W_ - tw) // 2 if sd_ == "c" else (W_ - tw - int(0.01 * W_) if sd_ == "r" else int(0.01 * W_))
            y0 = H_ - th + int((1 - e_in) * 0.25 * th) + int((1 - e_out) * 0.25 * th)              # rises in, sinks out
            if "pos" in r: x0, y0 = int(r["pos"][0] - tw / 2), int(r["pos"][1] - th / 2)
            _blit(out, big, al[..., None].astype(np.float32), x0, y0)
        else:
            pw = int(W_ * r.get("size", 0.36)); ph = int(pw * fh_ / fw_)
            z = 1.0 + 0.12 * u; cw, ch = fw_ / z, fh_ / z                                          # push in on him ...
            cx = fw_ / 2 + sd * (0.5 - u) * (fw_ - cw) * 0.9; cy = fh_ / 2 - (fh_ - ch) * 0.25       # ... and pan across
            pic = cv2.resize(cv2.getRectSubPix(crop, (int(cw), int(ch)), (cx, cy)), (pw, ph), interpolation=cv2.INTER_CUBIC)
            bd = max(6, pw // 55)
            card = cv2.copyMakeBorder(pic, bd, bd, bd, bd, cv2.BORDER_CONSTANT, value=(255, 255, 255)); kh, kw = card.shape[:2]
            ang = math.radians(r.get("tilt", -6.0 * sd) + sd * 16 * (1 - e_in) + 1.2 * math.sin(u * 2 * math.pi))
            yaw = sd * (0.10 + 0.04 * math.sin(u * math.pi)) * (1 + 1.5 * (1 - e_in))                # perspective: near edge taller
            sc_ = 0.9 + 0.1 * e_in
            pos = r.get("pos", [W_ - kw / 2 - 0.035 * W_ if sd > 0 else kw / 2 + 0.035 * W_, kh / 2 + 0.07 * H_])
            sw_ = 0.55 * W_ if vert is None else 1.1 * W_                                            # 9:16: swings in from off-frame
            px = pos[0] + sd * (1 - e_in) * sw_ + sd * (1 - e_out) * sw_; py = pos[1]
            base = [(-kw / 2, -kh / 2 * (1 - yaw)), (kw / 2, -kh / 2 * (1 + yaw)), (kw / 2, kh / 2 * (1 + yaw)), (-kw / 2, kh / 2 * (1 - yaw))]
            dst = np.float32([[px + sc_ * (bx * math.cos(ang) - by * math.sin(ang)), py + sc_ * (bx * math.sin(ang) + by * math.cos(ang))]
                              for bx, by in base])
            M_ = cv2.getPerspectiveTransform(np.float32([[0, 0], [kw, 0], [kw, kh], [0, kh]]), dst)
            wc = cv2.warpPerspective(card, M_, (W_, H_), flags=cv2.INTER_LINEAR, borderValue=0)
            al = cv2.warpPerspective(np.ones((kh, kw), np.float32), M_, (W_, H_), flags=cv2.INTER_LINEAR, borderValue=0)
            shd = cv2.GaussianBlur(np.roll(np.roll(al, 16, 0), 12 * sd, 1), (0, 0), 14)
            out *= (1 - 0.5 * shd)[..., None]
            out = out * (1 - al[..., None]) + wc * al[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
if REACT: print("reactions: " + ", ".join(f'{r.get("style", "pip")} {r["src0"]}-{r["src1"]} (out {r["_i0"] / FPS:.2f}-{r["_i1"] / FPS:.2f})' for r in REACT))
RUN_LOOP = not AUDIO_ONLY
if not AUDIO_ONLY and PART is None and PAR > 1 and N > 600:
    import time as _time; _t0 = _time.time()
    args_, skip_ = [], False
    for a_ in sys.argv[1:]:                             # drop "--parallel N" / "--parallel=N" only
        if skip_: skip_ = False; continue
        if a_ == "--parallel": skip_ = True; continue
        if not a_.startswith("--parallel="): args_.append(a_)
    procs = [subprocess.Popen([sys.executable, os.path.abspath(__file__), *args_, "--part", f"{k}/{PAR}"]) for k in range(PAR)]
    codes = [p_.wait() for p_ in procs]
    if any(codes): sys.exit(f"parallel render failed: {codes}")
    for fmt_, out_ in (("x", vid), ("ig", vid_ig)):
        if fmt_ not in FORMATS: continue
        lst = os.path.join(WORK, f"parts_{fmt_}.txt")
        with open(lst, "w") as fh: fh.writelines(f"file '{os.path.join(WORK, f'part_{fmt_}_{k}.mp4')}'\n" for k in range(PAR))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out_], check=True)
    print(f"parallel picture: {PAR} parts in {_time.time() - _t0:.0f}s", flush=True)
    RUN_LOOP = False
if RUN_LOOP:
    sc = 0.5 if PREVIEW else 1.0
    if PART is not None:
        pk, pn = [int(v) for v in PART.split("/")]; FR0, FR1 = N * pk // pn, N * (pk + 1) // pn
        vid_p, vid_ig_p = os.path.join(WORK, f"part_x_{pk}.mp4"), os.path.join(WORK, f"part_ig_{pk}.mp4")
    else: FR0, FR1, vid_p, vid_ig_p = 0, N, vid, vid_ig
    enc = encoder(vid_p, int(W * sc), int(H * sc)) if "x" in FORMATS else None
    enc_ig = encoder(vid_ig_p, int(VW * sc), int(VH * sc)) if "ig" in FORMATS else None
    reader = None; cur = -1; prev_k = None
    for i, (si, t, sp) in enumerate(frames):
        if i < FR0 or i >= FR1: continue
        T = i / FPS; s = SHOTS[si]
        if si != cur:
            if reader: reader.close()
            reader = Reader(s["a"], s["b"], feed_region(s["kind"]) if s["kind"] in FEED else None); cur = si; prev_k = None
        fk = (t - s["a"]) * FPS; k0 = int(fk); w = fk - k0
        if s["kind"] in FEED and sp <= 1.35:
            raw_ = reader.interp(fk)
        elif sp > 1.35 and prev_k is not None and k0 - prev_k >= 2:
            raw_ = np.mean([reader.get(k).astype(np.float32) for k in range(max(prev_k + 1, k0 - 3), k0 + 1)], axis=0)
        elif w > 0.05 and sp < 0.9:
            raw_ = cv2.addWeighted(reader.get(k0).astype(np.float32), 1 - w, reader.get(k0 + 1).astype(np.float32), w, 0)
        else:
            raw_ = reader.get(k0).astype(np.float32)
        prev_k = k0
        src = cv2.addWeighted(raw_, 1.5, cv2.GaussianBlur(raw_, (0, 0), 2.0), -0.5, 0) if s["kind"] == "face" else raw_
        for b_ in s.get("blur", []): src = blur_rect(src, b_, t)
        st = fx_state(si, T); st0 = fx_state(si, T - 0.6 / FPS)
        img = warp_cam(src, st, st0)
        if s.get("mask_text"): img = mask_text_fx(img, s, T, i)
        base_ = ff_fx(post(img, st), T) if (enc or (enc_ig and IGL == "ghost")) else None
        if enc:
            o = draw_overlays(draw_reactions(base_, raw_, i), T)
            dk = freeze_dim(T)
            if dk > 0: o = (o.astype(np.float32) * (1 - 0.2 * dk)).astype(np.uint8)
            o = draw_age_tag(draw_pops(o, T), T)
            if PREVIEW: o = cv2.resize(o, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
            enc.stdin.write(o.tobytes())
        if enc_ig:
            if IGL == "ghost":
                o, gy0, gph = ig_ghost(draw_overlays(base_, T), src, raw_, st, st0, s, T, i); o = ig_ghost_finish(o, gy0, gph, T)
            elif IGL == "stack":
                o = ig_stack_finish(draw_overlays(ff_fx(post(ig_stack(src, raw_, st, st0, s, t, T, i), st), T), T, IG_OV_SCALE, ig=True), s, T)
            else:
                panel = warp_cam(src, vcam(st, s["kind"]), vcam(st0, s["kind"]), PW, PH)
                o = post(vertical(panel), st)
            dk = freeze_dim(T)
            if dk > 0: o = (o.astype(np.float32) * (1 - 0.2 * dk)).astype(np.uint8)
            o = draw_age_tag(draw_pops(o, T, VW, VH), T, VW, VH)
            if PREVIEW: o = cv2.resize(o, (VW // 2, VH // 2), interpolation=cv2.INTER_AREA)
            enc_ig.stdin.write(o.tobytes())
        if i % 300 == 0: print("frame", i, "/", N, flush=True)
    reader.close()
    for e_ in (enc, enc_ig):
        if e_: e_.stdin.close(); e_.wait()
    if PART is not None: sys.exit(0)                    # parts render picture only; the parent does audio + finish

# ---------- audio: the stream's own audio, pitch-preserved, + a few sfx ----------
raw = f"{WORK}/src_audio.f32"
if not os.path.exists(raw):
    has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", SRC], capture_output=True, text=True).stdout.strip()
    if has_audio:   # async fills corrupt-packet gaps so audio stays in sync
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", EDL.get("src_audio", SRC), "-vn", "-af", "aresample=async=1:first_pts=0", "-ac", "2", "-ar", str(SR), "-f", "f32le", raw], check=True)
    else:           # silent screen recording (phone clips): song + sfx only
        d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", SRC]))
        np.zeros((int((d + 1) * SR), 2), np.float32).tofile(raw)
srca = np.fromfile(raw, np.float32).reshape(-1, 2)
ns = int(DUR * SR); fi = np.arange(ns) / SR * FPS
pos = np.interp(fi, np.arange(N), [f[1] for f in frames]) * SR
def wsola(x, pos, L=1536, tol=360, plan=None):
    """pitch-preserving time map. Returns (audio, grain plan); passing a plan back replays the exact same grains
    on another signal (a separated stem), so stems and the mix stay phase-locked and can be crossfaded cleanly."""
    Hs = L // 2; win = np.hanning(L + 1)[:L].astype(np.float32)
    n = len(pos); y = np.zeros((n + L, 2), np.float32); mono = x.mean(1); prev = None; ps = []
    for k, o in enumerate(range(0, n, Hs)):
        if plan is not None:
            p = plan[k]
        else:
            p = int(pos[min(o, n - 1)]) - L // 2
            if prev is not None and abs(p - (prev + Hs)) < 3 * Hs:      # continuous: find best-matching continuation
                ref = mono[max(0, prev + Hs):max(0, prev + Hs) + L]
                lo = max(0, p - tol); hi = min(len(mono) - L, p + tol)
                if hi > lo and len(ref) == L:
                    p = lo + int(np.argmax(np.correlate(mono[lo:hi + L], ref, mode="valid")))
            p = min(max(p, 0), len(x) - L); ps.append(p)
        p = min(max(p, 0), len(x) - L)
        y[o:o + L] += x[p:p + L] * win[:, None]; prev = p
    return y[:n], (plan if plan is not None else ps)
a, PLAN = wsola(srca, pos); a = a.astype(np.float64)
STEMS = EDL.get("stems")      # {"game": wav (the separated no-voice stem), "keep_speed": 1.02, "mute": [[src_a, src_b], ...],
                              #  "keep": [[src_a, src_b], ...] (reactions kept even when sped up), "fade": 0.08}
S2 = EDL.get("stems2")
if STEMS and not S2:
    # his voice stays (the untouched mix) at normal speed, on facecam and in "keep" ranges; on speed-ups and in "mute"
    # ranges the mix crossfades to the game-only stem, replayed with the mix's own grains
    ag_ = wsola(load_audio(STEMS["game"]).astype(np.float32), pos, plan=PLAN)[0].astype(np.float64)
    keep_ = np.array([1.0 if ((sp_ <= STEMS.get("keep_speed", 1.02) or SHOTS[si_]["kind"] == "face")
                              and not any(m0 <= t_ < m1 for m0, m1 in STEMS.get("mute", [])))
                      or any(k0 <= t_ < k1 for k0, k1 in STEMS.get("keep", [])) else 0.0 for si_, t_, sp_ in frames])
    gv_ = np.interp(fi, np.arange(N), keep_)
    k_ = max(1, int(STEMS.get("fade", 0.08) * SR)); gv_ = np.convolve(gv_, np.ones(k_) / k_, mode="same")
    a = ag_ + (a - ag_) * (gv_ * STEMS.get("voice_gain", 1.0))[:, None]
    print(f"voice on for {gv_.mean() * 100:.0f}% of the edit")
if S2:
    # separate voice and game tracks, each time-stretched per constant-speed run with rubberband (formant-preserving):
    # no second copy of the game is ever crossfaded in (that comb-filtered = "flanger"), and his voice stays on speed-ups
    # up to voice_max_speed. The game is ducked under whatever voice actually ends up in the edit.
    def _rb(x, tempo, game=False):
        if len(x) < 64: return np.zeros((0, 2), np.float32)
        if abs(tempo - 1) < 1e-3: return x.astype(np.float32)
        if game and tempo < S2.get("vari_below", 0.97):
            # slow-mo: rubberband-stretching the game below ~0.95x warbles/flanges (Dylan, 2026-10-17: "whenever it gets slowed
            # down the audio gets busted"). Varispeed instead: plain resampling, pitch drops like a tape slow-down, zero phasing.
            n = int(round(len(x) / tempo)); t = np.linspace(0, len(x) - 1, n)
            y = np.stack([np.interp(t, np.arange(len(x)), x[:, c]) for c in range(2)], 1).astype(np.float32)
            return y * np.float32(10 ** (S2.get("vari_gain_db", -3.0) / 20))
        af = (f"rubberband=tempo={tempo:.6f}:transients=mixed:detector=compound:phase=laminar:window=standard:"
              f"smoothing=on:formant=preserved:pitchq=quality:channels=together")
        r = subprocess.run(["ffmpeg", "-v", "quiet", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", af,
                            "-f", "f32le", "-ar", str(SR), "-ac", "2", "-"], input=x.astype(np.float32).tobytes(), capture_output=True)
        return np.frombuffer(r.stdout, np.float32).reshape(-1, 2)
    V_src = load_audio(S2["voice"]).astype(np.float32); G_src = load_audio(S2["game"]).astype(np.float32)
    runs = []; i = 0
    def _tgt(si, t, sp):
        if sp == 0.0: return 0.0
        return [v for (k, v) in SHOTS[si]["speeds"] if t >= k - 1e-9][-1]
    while i < N:
        si, t, sp = frames[i]; key = (si, _tgt(si, t, sp)); j = i + 1
        while j < N and (frames[j][0], _tgt(*frames[j])) == key: j += 1
        runs.append((i, j, key[0], key[1])); i = j
    Vo = np.zeros((ns, 2), np.float32); Go = np.zeros((ns, 2), np.float32); vmask = np.zeros(ns, np.float32)
    PAD = int(0.15 * SR); XF = int(S2.get("xfade", 0.025) * SR)
    # each constant-speed run is rendered XF past both of its ends and the neighbours overlap-crossfade over 2*XF,
    # so a speed change or a cut never leaves a gap (a 4 ms butt-join left a ~10 ms hole = a click at every ramp)
    for (i0, i1, si, tg) in runs:
        o0, o1 = int(i0 / FPS * SR), min(ns, int(i1 / FPS * SR)); n_out = o1 - o0
        if n_out <= 0 or tg == 0.0: continue                      # freezes: silence here, the ring-out fills it below
        s0 = frames[i0][1]; s1 = frames[i1 - 1][1] + frames[i1 - 1][2] / FPS
        a0, a1 = int(s0 * SR), int(s1 * SR); tempo = max(1e-3, (a1 - a0) / n_out)
        lo, hi = max(0, a0 - PAD), min(len(V_src), a1 + PAD)
        e0, e1 = max(0, o0 - XF), min(ns, o1 + XF); L = e1 - e0
        for src_, dst_ in (((G_src, Go),) if S2.get("overlay") else ((V_src, Vo), (G_src, Go))):
            y = _rb(src_[lo:hi], tempo, game=src_ is G_src); off = int(round((a0 - lo) / tempo)) - (o0 - e0)
            if off < 0: y = np.vstack([np.zeros((-off, 2), np.float32), y]); off = 0
            y = y[off:off + L]
            if len(y) < L: y = np.vstack([y, np.zeros((L - len(y), 2), np.float32)])
            w = np.ones(L, np.float32); r0 = min(2 * XF, L // 2) if e0 > 0 else 0; r1 = min(2 * XF, L // 2) if e1 < ns else 0
            if r0: w[:r0] = np.sin(np.linspace(0, np.pi / 2, r0)) ** 2
            if r1: w[-r1:] = np.cos(np.linspace(0, np.pi / 2, r1)) ** 2
            dst_[e0:e1] += y * w[:, None]
        if tg <= S2.get("voice_max_speed", 2.0) or SHOTS[si]["kind"] == "face": vmask[o0:o1] = 1.0
    if S2.get("overlay") and S2.get("voice_mode", "live") == "live":
        # Dylan, 2026-10-17: "during whatever clip is happening it should have the voice still active... if the voice is there for
        # the whole clip it doesn't do that [sound terrible]. If we need to fade it out we can also do that."
        # LIVE voice: every shot plays his voice stem continuously at 1.0x from the shot's first frame, in sync with the picture, for
        # the whole shot. Nothing is picked out or queued. Where the picture runs slower than him (slow-mo, freezes) his voice keeps
        # going and then waits in his next pause until the picture catches up; where the picture is ahead it skips through a pause.
        # At a cut to a different moment, the word running at the cut finishes (max voice_tail) and fades out under the next shot.
        Wd = json.load(open(S2["words"])) if S2.get("words") else []
        hop = SR / FPS; vm = V_src.mean(1); nb = int(len(vm) // hop)
        e_ = np.sqrt(np.array([(vm[int(k * hop):int((k + 1) * hop)] ** 2).mean() for k in range(nb)]) + 1e-12); edb = 20 * np.log10(e_)
        loud0 = edb > np.percentile(edb, 95) + S2.get("gap_db", -26)
        loud = np.convolve(loud0.astype(float), np.ones(7), mode="same") > 0         # ~0.05 s either side of any sound
        talking = loud.copy(); inword = np.zeros(nb, bool)
        for w0, w1, _ in Wd:
            talking[max(0, int((w0 - 0.08) * FPS)):min(nb, int((w1 + 0.15) * FPS) + 1)] = True
            inword[max(0, int(w0 * FPS) + 1):min(nb, int(w1 * FPS))] = True        # the frame where two words touch stays free
        # defaults = the PC redo Dylan called "fucking perfect" (Xposed 848k): plain 1.0x through the shot, 0.25 s fade at a cut, no
        # re-sync. "sync_tol": 0.12 + "max_off": 1.0 turn on waiting in pauses / skipping to catch up after slow-mo or ramps.
        tol, max_tail, max_off = S2.get("sync_tol", 99.0), S2.get("voice_tail", 0.25), S2.get("max_off", 99.0)
        def seam(b):   # between two words, at a dip in his level (a breath): a 20 ms crossfade here is inaudible
            return 0 <= b < nb and not inword[b] and edb[b] <= edb[max(0, b - 3):b + 4].min() + 2.0
        def gap(v, off=0.0):
            # a real pause; or, once he is out of sync by more than max_off (behind) / 2x that (ahead, e.g. a long freeze), a seam
            b = int(v * FPS)
            return b >= nb or not talking[b] or (off > max_off and seam(b))
        sync_log = []; segs = []; vend = None; worst = []                                  # seg: [out frame, src time, frames, fade_in, fade_out]
        for si_, sh in enumerate(SHOTS):
            if sh.get("voice") is False: vend = None; continue
            f0_, f1_ = sh["f0"], sh["f1"]; v = frames[f0_][1]
            cont = vend is not None and abs(v - vend) < 0.06 and segs and segs[-1][0] + segs[-1][2] == f0_
            if cont: v = vend
            cur = None; off_max = 0.0
            for i in range(f0_, f1_):
                p = frames[i][1]
                if v - p > tol and gap(v, (v - p) / 2):                                     # he's ahead of the picture and quiet: wait
                    if cur: segs.append(cur); cur = None
                    continue
                if p - v > tol and gap(v, p - v):                              # behind and quiet: skip ahead through the pause
                    b = int(v * FPS)
                    if p - v > max_off:                                        # (far behind: re-sync, landing on a seam near the picture)
                        cand = [c for c in range(max(int(v * FPS) + 1, int((p - 0.8) * FPS)), min(nb, int((p + 0.2) * FPS) + 1)) if seam(c)]
                        b = min(cand, key=lambda c: abs(c / FPS - p)) if cand else int(v * FPS)
                    while b < min(int(p * FPS), nb) and not talking[b]: b += 1
                    if b / FPS > v + 1e-6:
                        if cur: segs.append(cur); cur = None
                        v = b / FPS
                if cur is None:
                    if cont and i == f0_ and segs: cur = segs.pop(); cur[4] = 0.012   # same moment as the last shot: keep going
                    else: cur = [i, v, 0, 0.03 if i == f0_ else 0.012, 0.012]
                sync_log.append([round(i / FPS, 3), round(p, 3), round(v, 3)])
                cur[2] += 1; v += 1 / FPS; off_max = max(off_max, abs(v - p - 1 / FPS))
            if cur:
                nxt = SHOTS[si_ + 1] if si_ + 1 < len(SHOTS) else None
                joins = nxt is not None and nxt.get("voice") is not False and abs(frames[nxt["f0"]][1] - v) < 0.06
                if not joins:                                                  # finish the word at the cut, fade it under the next shot
                    k = 0
                    while k < int(max_tail * FPS) and int(v * FPS) + k < nb and talking[int(v * FPS) + k]: k += 1
                    cur[2] += k; v += k / FPS; cur[4] = max(0.08, k / FPS)
                segs.append(cur)
            vend = v; worst.append(off_max)
        Vo[:] = 0
        for i0, sv, nf, fi_, fo_ in segs:
            o0, a0 = int(i0 / FPS * SR), int(sv * SR); n = min(int(round(nf / FPS * SR)), ns - o0, len(V_src) - a0)
            if n <= 0 or o0 < 0: continue
            seg = V_src[a0:a0 + n].astype(np.float32).copy(); w = np.ones(n, np.float32)
            r0, r1 = min(int(fi_ * SR), n // 2), min(int(fo_ * SR), n // 2)
            if r0: w[:r0] = np.sin(np.linspace(0, np.pi / 2, r0)) ** 2
            if r1: w[-r1:] = np.cos(np.linspace(0, np.pi / 2, r1)) ** 2
            Vo[o0:o0 + n] += seg * w[:, None]
        for ev in EDL.get("extra_sfx", []):                                # his voice dips (not cut) under a voice-over line
            if ev.get("duck_voice") is None: continue
            T_ = src_out(ev["src"]) + ev.get("offset", 0.0)
            L_ = ev.get("len") or float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                                        ev["file"]], capture_output=True, text=True).stdout or 2.5)
            d0, d1 = int((T_ - 0.08) * SR), int((T_ + L_ + 0.15) * SR); r_ = int(0.08 * SR)
            env_ = np.zeros(ns, np.float32); env_[max(0, d0):max(0, min(ns, d1))] = 1
            env_ = np.convolve(env_, np.ones(r_) / r_, mode="same")
            Vo *= (1 - env_ * (1 - 10 ** (-abs(ev["duck_voice"]) / 20)))[:, None]
        json.dump(sync_log, open(f"{WORK}/voice_sync.json", "w"))   # [out time, picture source time, voice source time]
        if os.environ.get("HYPE_SYNC_ONLY"): print("voice sync written", [round(x, 2) for x in worst]); sys.exit(0)
        print(f"voice LIVE: {len(segs)} stretches at 1.0x; most his voice drifts from the picture in each shot (slow-mo/freezes: it runs "
              f"on, then waits in his next pause): " + ", ".join(f"{sh['T0']:.1f}s {w_:.1f}" for sh, w_ in zip([s_ for s_ in SHOTS if s_.get("voice") is not False], worst)))
        vmask[:] = 1.0
    elif S2.get("overlay"):
        # his voice NEVER changes speed: words (from "words", [[start, end, text], ...] on the source timeline) are grouped into
        # phrases at pauses; each phrase starts where its first word lands in the cut and plays from the clean voice stem at 1.0x.
        # Muted words are dropped whole. A phrase that would overlap the previous one waits (up to max_delay) or is dropped.
        Wd = json.load(open(S2["words"])); gap = S2.get("phrase_gap", 0.2)
        # Dylan, 2026-10-17: "don't cut off their talking at all... even if I'm repeating myself play my whole voice clip".
        # voice_full (default): no mutes, no trimmed tails, and a line that starts in a shot plays to the end of its sentence
        # (words keep coming while the pauses stay short), even past the cut. "voice_full": false restores the old behaviour.
        FULL = S2.get("voice_full", True)
        mutes = [] if FULL else S2.get("mute", [])
        lead, tail, mdel = 0.06, 0.12, (1e9 if FULL else S2.get("max_delay", 0.35))
        def muted(w): return any(m0 < w[1] and w[0] < m1 for m0, m1 in mutes)
        sched = []; used = set()                                       # [T_start, [words...]] in output order
        for si_, sh in enumerate(SHOTS):
            if sh.get("voice") is False: continue
            ws = [w for w in Wd if sh["a"] - 0.02 <= w[0] < sh["b"] - 0.05 and not muted(w)]
            if FULL and ws:                                            # finish the sentence that is running at the cut
                rest = [w for w in Wd if w[0] >= sh["b"] - 0.05]
                for w in rest:
                    if w[0] - ws[-1][1] <= S2.get("finish_gap", 0.6): ws.append(w)
                    else: break
            if FULL:                                                   # a finished sentence isn't replayed by the next shot (the cold open doesn't count)
                ws = [w for w in ws if round(w[0], 2) not in used]
                if si_ > 0: used.update(round(w[0], 2) for w in ws)
            phr = []
            for w in ws:
                if phr and w[0] - phr[-1][-1][1] <= gap and not muted([phr[-1][-1][1], w[0]]): phr[-1].append(w)
                else: phr.append([w])
            for ph in phr: sched.append([out_time(sh, max(sh["a"], ph[0][0])) - lead, ph])
        def dur(ph): return ph[-1][1] - ph[0][0] + lead + tail
        import re
        DANGLE = {"i", "a", "an", "the", "to", "be", "me", "my", "and", "but", "so", "of", "in", "on", "it's", "we", "you", "not", "that",
                  "just", "give", "might", "is", "are", "with", "for", "this", "if", "we're", "i'm", "your", "its", "it", "or", "like", "get"}
        trimmed = []; delayed = 0; late = []
        for k in range(1, len(sched)):
            T, ph = sched[k]
            j = k - 1
            while j >= 0 and not sched[j][1]: j -= 1
            if j < 0: continue
            prevT, prev = sched[j]
            over = prevT + dur(prev) + 0.04 - T
            while over > mdel and len(prev) > 0:                          # the NEW line wins: cut the earlier line's last words
                trimmed.append(prev.pop()[2]); over = (prevT + dur(prev) + 0.04 - T) if prev else 0
            if trimmed and prev:                                            # never leave a line hanging on a function word ("I might be", "not")
                while prev and (re.sub(r"[^a-z']", "", prev[-1][2].lower()) in DANGLE or len(prev) == 1 and len(prev[0][2]) <= 3):
                    trimmed.append(prev.pop()[2])
            if over > 0: sched[k][0] = T + over; delayed += 1
            if over > S2.get("max_late", 1.0): late.append(f"{over:.1f}s late: " + " ".join(w[2] for w in ph))
        Vo[:] = 0; placed = 0; cut_end = []
        for T, ph in sched:
            if not ph: continue
            a0, a1 = ph[0][0] - lead, ph[-1][1] + tail
            i0_ = int(T * SR); n = int((a1 - a0) * SR)
            if i0_ >= ns or i0_ < 0: cut_end.append(" ".join(w[2] for w in ph)); continue
            if i0_ + n > ns: cut_end.append(" ".join(w[2] for w in ph))
            n = min(n, ns - i0_); seg = V_src[int(a0 * SR):int(a0 * SR) + n].astype(np.float32)
            f = min(int(0.012 * SR), n // 2)
            if f: seg[:f] *= np.linspace(0, 1, f)[:, None]; seg[-f:] *= np.linspace(1, 0, f)[:, None]
            Vo[i0_:i0_ + len(seg)] += seg; placed += 1
        print(f"voice overlay: {placed} phrases at 1.0x, {delayed} nudged later, {len(trimmed)} words trimmed: {' '.join(reversed(trimmed))}")
        if late: print(f"WARNING voice drift (lines queued behind earlier talking; give them room, see EDIT_BRIEF rule 3): {' | '.join(late)}")
        if cut_end: print(f"WARNING voice runs past the end of the edit (lengthen the last shot): {' | '.join(cut_end)}")
        vmask[:] = 1.0
    else:
        src_t = pos / SR
        for m0, m1 in S2.get("mute", []): vmask[(src_t >= m0) & (src_t < m1)] = 0.0
        k_ = int(0.03 * SR); vmask = np.convolve(vmask, np.ones(k_) / k_, mode="same")
        Vo *= vmask[:, None]
    # light compression on his voice alone (yells), then duck the game under it
    env = np.sqrt(signal.sosfiltfilt(signal.butter(1, 10, fs=SR, output="sos"), (Vo.astype(np.float64) ** 2).mean(1)).clip(1e-12))
    thr = 10 ** (S2.get("voice_thresh_db", -24) / 20)
    Vo = Vo * np.where(env > thr, (thr / env) ** (1 - 1 / 3.0), 1.0)[:, None].astype(np.float32)
    talk = (env > 10 ** (-42 / 20)).astype(np.float64); sm = np.zeros(ns); up, dn = 1 - math.exp(-1 / (0.02 * SR)), 1 - math.exp(-1 / (0.3 * SR))
    hop_ = 240; tk = talk[::hop_]; smk = np.zeros(len(tk)); u_, d_ = 1 - math.exp(-hop_ / (0.02 * SR)), 1 - math.exp(-hop_ / (0.3 * SR))
    for k in range(1, len(tk)): smk[k] = smk[k - 1] + (tk[k] - smk[k - 1]) * (u_ if tk[k] > smk[k - 1] else d_)
    sm = np.interp(np.arange(ns), np.arange(len(tk)) * hop_, smk)
    Go = Go * (10 ** (-S2.get("duck_db", 8) * sm / 20))[:, None].astype(np.float32)
    a = (Vo * S2.get("voice_gain", 1.0) + Go).astype(np.float64)
    print(f"stems2: {len(runs)} runs, voice on for {vmask.mean() * 100:.0f}% of the edit")
if FFR:
    duck_ = np.ones(N)
    for T0, T1, cfg in FFR: duck_[int(T0 * FPS):int(T1 * FPS)] = cfg.get("duck", 0.9)
    dk_ = np.interp(fi, np.arange(N), duck_); k_ = int(0.04 * SR); dk_ = np.convolve(dk_, np.ones(k_) / k_, mode="same")
    a = a * dk_[:, None]

# voice taming (his mic and the slot share one mono mix, so work on the voice band only)
VT = EDL.get("voice_tame", {"ratio": 4.0, "thresh_db": -32.0, "game_duck_db": -4.0})
if S2: VT = None                                      # stems2 already compresses the voice and ducks the game
if VT:
    lo = signal.sosfiltfilt(signal.butter(4, 250, fs=SR, output="sos"), a, axis=0)
    hi = signal.sosfiltfilt(signal.butter(4, 3500, btype="high", fs=SR, output="sos"), a, axis=0)
    mid = a - lo - hi
    e = np.sqrt(signal.sosfiltfilt(signal.butter(1, 8, fs=SR, output="sos"), (mid ** 2).mean(1)).clip(1e-12))
    thr = 10 ** (VT["thresh_db"] / 20)
    g = np.where(e > thr, (thr / e) ** (1 - 1 / VT["ratio"]), 1.0)          # compress yells in the voice band
    face = np.zeros(ns)
    for s_ in SHOTS:
        if s_["kind"] == "face": face[int(s_["T0"] * SR):int(s_["T1"] * SR)] = 1
    face = np.convolve(face, np.ones(4800) / 4800, mode="same")
    g = g * (10 ** (VT["game_duck_db"] / 20) * (1 - face) + face)           # full level on facecam cuts
    a = lo + hi + mid * g[:, None]

def ringout(pre, L):
    """what the stream sounds like when time stops: the last moment rings out as a dark, decaying reverb tail"""
    t_ = np.arange(len(pre) + L) / SR
    ir = rng.standard_normal(len(t_)) * np.exp(-t_ / 0.32)
    ir = signal.sosfilt(signal.butter(2, 2800, fs=SR, output="sos"), ir); ir /= np.sqrt((ir ** 2).sum())
    y = np.stack([signal.fftconvolve(pre[:, c], ir)[len(pre):len(pre) + L] for c in range(2)], -1)
    ref = np.sqrt((pre[-int(0.08 * SR):] ** 2).mean()) + 1e-9; got = np.sqrt((y[:int(0.08 * SR)] ** 2).mean()) + 1e-9
    return y * (EDL.get("freeze_ring", 0.55) * ref / got)
popa = np.zeros_like(a)
def pop_sfx(up=True):
    n = int(0.11 * SR); t_ = np.arange(n) / SR
    f_ = (260 + 900 * (t_ / t_[-1]) ** 0.6) if up else (900 - 600 * (t_ / t_[-1]))
    return 0.5 * np.sin(2 * np.pi * np.cumsum(f_) / SR) * np.exp(-t_ * 28) * (1 - np.exp(-t_ * 900))
def add_to(buf, x, t0, gain=1.0):
    i0 = int(t0 * SR); x = x[:, None] if x.ndim == 1 else x
    if i0 < 0: x = x[-i0:]; i0 = 0
    n_ = min(len(x), ns - i0)
    if n_ > 0: buf[i0:i0 + n_] += gain * x[:n_]
for f in FRZ:
    i0, i1 = int(f["_T0"] * SR), min(ns, int(f["_T1"] * SR))
    if i1 > i0:
        tail = ringout(a[max(0, i0 - int(0.35 * SR)):i0], i1 - i0)
        xf = min(int(0.012 * SR), i1 - i0); r_ = np.linspace(0, 1, xf)[:, None]
        tail[:xf] = a[i0:i0 + xf] * (1 - r_) + tail[:xf] * r_
        a[i0:i1] = tail
        fi_ = min(int(0.05 * SR), ns - i1); a[i1:i1 + fi_] *= np.linspace(0, 1, fi_)[:, None]      # picture and sound restart together
    p = f["pop"]
    if p:
        add_to(popa, pop_sfx(True), f["_T0"] + POP_IN - 0.01, 0.35)
        add_to(popa, p["_aud"], f["_T0"] + POP_IN + VOICE_DELAY)
        add_to(popa, pop_sfx(False), pop_out_t(f), 0.22)

sfx = np.zeros_like(a)
EVENTS = []                         # (samples, start index, role) when auto-levelling is on
_role = [None]
def add(x, t0, gain=1.0):
    if AUTO and _role[0] in AUTO_ROLES:
        EVENTS.append((gain * (x[:, None] if x.ndim == 1 else x), int(t0 * SR))); return
    i0 = int(t0 * SR)
    if i0 < 0: x = x[-i0:]; i0 = 0
    n = min(len(x), ns - i0)
    if n > 0: sfx[i0:i0 + n] += gain * (x[:n, None] if x.ndim == 1 else x[:n])
def sweep_sine(f0, f1, dec, L):
    t = np.arange(int(L * SR)) / SR; return np.sin(2 * np.pi * np.cumsum(f1 + (f0 - f1) * np.exp(-t * dec)) / SR), t
def boom(I):
    s_, t = sweep_sine(160, 38, 14, 1.8); s_ *= np.exp(-t * (2.6 - 0.7 * min(I, 1.4)))
    nz = signal.sosfilt(signal.butter(2, 3500, fs=SR, output="sos"), rng.standard_normal(len(t))) * np.exp(-t * 28)
    return np.tanh(1.7 * (0.9 * s_ + 0.4 * nz)) * min(1.0, 0.45 + 0.45 * I)
def whoosh(L):
    n = int(L * SR); t = np.arange(n) / SR; nz = rng.standard_normal(n); out = np.zeros(n)
    for j in range(0, n, 512):
        fc = 300 + 5500 * (j / n) ** 1.5
        out[j:j + 512] = signal.sosfilt(signal.butter(2, [fc * 0.7, min(fc * 1.4, 20000)], btype="band", fs=SR, output="sos"), nz[j:j + 512])
    return out * (t / L) ** 2.5 * 2.4
def glitch_sfx(L=0.22):
    n = int(L * SR); t = np.arange(n) / SR
    x = np.round(rng.standard_normal(n) * (np.sin(2 * np.pi * 37 * t) > 0) * 4) / 4
    x = signal.sosfilt(signal.butter(2, 4000, fs=SR, output="sos"), x)
    return 0.45 * x * np.exp(-t * 6)
def riser(L):
    """soft airy swell (filtered noise opening up), no pitched sweep"""
    n = int(L * SR); t = np.arange(n) / SR; p = t / L; nz = rng.standard_normal(n); out = np.zeros(n)
    for j in range(0, n, 512):
        fc = 400 + 2000 * (j / n) ** 2
        out[j:j + 512] = signal.sosfilt(signal.butter(2, fc, fs=SR, output="sos"), nz[j:j + 512])
    return out * p ** 2.5 * 0.35

# ---- sound design: real samples from the sound pack when mapped, synth fallback otherwise ----
PACK = EDL.get("sfx_dir")
ROLE_GAIN = EDL.get("sfx_role_gain", {})
# "sfx_auto_level": {"over_db": 4, "max_boost_db": 18, "roles": ["glitch", "whip", "_x"]} -> each of those sounds is raised
# until it sits over_db above whatever is playing under it (song + stream audio); never lowered, the song is never ducked
AUTO = EDL.get("sfx_auto_level"); AUTO_ROLES = set(AUTO.get("roles", ["glitch", "whip", "_x"])) if AUTO else set()        # per-role level trim, e.g. {"glitch": 4.4} when a song bed would bury the cut sounds
SMAP = EDL.get("sfx_map", {})
_cache = {}
def sample(rel):
    if rel not in _cache:
        raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", os.path.join(PACK, rel), "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
        n = int(0.05 * SR); k = max(1, len(x) // n)
        env = np.sqrt((x[:k * n].mean(1).reshape(k, n) ** 2).mean(1))
        _cache[rel] = (x, int(np.argmax(env)) * n)               # audio, sample index of its loudest moment
    return _cache[rel]
def place(role, t, gain=1.0, align="peak", synth=None, maxlen=None):
    """put the mapped sample so its loudest moment ('peak') or its start lands at output time t"""
    gain *= ROLE_GAIN.get(role, 1.0); _role[0] = role
    if role in SMAP and PACK:
        x, pk = sample(SMAP[role])
        if maxlen: x = x[:int(maxlen * SR)].copy(); x[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))[:, None]
        t0 = t - (pk / SR if align == "peak" else 0.0)
        add(x * gain, t0)
    elif synth is not None:
        add(*synth)

for s in SHOTS:
    for ht, I, bm in s["hits_out"]:
        if bm:
            place("impact", ht, 0.9, synth=(boom(I), ht - 0.004, 0.85))
            place("flash", ht, 0.5)
            if s["kind"] == "game" and ht - s["T0"] > 1.0 and "riser" not in SMAP: add(riser(1.0), ht - 1.0, 0.4)
for s in SHOTS[:-1]:
    ct = s["T1"]
    if s["out"] == "whip": place("whip", ct, 0.6, synth=(whoosh(0.32), ct - 0.3, 0.3))
    if s["out"] == "glitch": place("glitch", ct, 0.55, synth=(glitch_sfx(), ct - 0.1, 0.3))
    if s["out"] == "flash": place("whip", ct, 0.6, synth=(whoosh(0.5), ct - 0.48, 0.4))
    if s.get("tension"):
        hit = [h for h, I, bm in s["hits_out"] if bm]
        if hit and "riser" in SMAP: place("riser", hit[0], 0.55)              # riser peaks exactly on the reveal
        elif not hit: add(riser(s["T1"] - s["T0"] - 0.2), s["T0"] + 0.2, 0.55)
def tape_whir(L):
    """fast-forward tape: band-limited hiss with a wobbling squeal, spun up at the start and clunked off at the end"""
    n = int(L * SR); t = np.arange(n) / SR
    nz = signal.sosfilt(signal.butter(2, [900, 5200], btype="band", fs=SR, output="sos"), rng.standard_normal(n))
    spin = np.clip(t / 0.18, 0, 1) ** 1.5
    f_ = (900 + 2300 * spin) * (1 + 0.06 * np.sin(2 * np.pi * 11 * t))
    sq = np.sin(2 * np.pi * np.cumsum(f_) / SR) * 0.10
    env = spin * (0.75 + 0.25 * np.sin(2 * np.pi * 7.3 * t)) * np.clip((L - t) / 0.05, 0, 1)
    x = (0.32 * nz + sq) * env
    cl = int(0.09 * SR); tc = np.arange(cl) / SR
    clunk = (np.sin(2 * np.pi * 95 * tc) * 0.8 + rng.standard_normal(cl) * 0.25) * np.exp(-tc * 45)
    out = np.zeros(n + cl); out[:n] = x; out[n - int(0.01 * SR):n - int(0.01 * SR) + cl] += clunk
    return out
for T0, T1, cfg in FFR:
    add(tape_whir(T1 - T0), T0, cfg.get("whir", 0.11))
place("glitch", DUR - 0.25, 0.4, synth=(glitch_sfx(0.45), DUR - 0.45, 0.3))
# extra one-off sounds: [{"file": rel, "src": source_time, "offset": s, "gain": g, "align": "start"|"peak", "len": s}]
def out_at(src_t): return src_out(src_t)
for ev in EDL.get("extra_sfx", []):
    T = out_at(ev["src"]) + ev.get("offset", 0.0)
    SMAP["_x"] = ev["file"]; place("_x", T, ev.get("gain", 1.0), align=ev.get("align", "start"), maxlen=ev.get("len"))
# music bed: song time `at` lands on source time `align_src` (e.g. the drop on the big reveal)
music = np.zeros_like(sfx)
if EDL.get("music"):
    M = EDL["music"]
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", M["file"], "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    song = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    off = int((M["at"] - out_at(M["align_src"])) * SR)       # song sample playing at output t=0
    seg = song[max(0, off):max(0, off) + ns]
    music[max(0, -off):max(0, -off) + len(seg)] = seg[:ns - max(0, -off)]
    fi_ = int(0.15 * SR); music[:fi_] *= np.linspace(0, 1, fi_)[:, None]
    if "end_src" in M:                                        # song cuts out here (short fade so it doesn't click)
        e0 = int((out_at(M["end_src"]) + M.get("end_offset", 0.0)) * SR); ef = int(M.get("end_fade", 0.06) * SR)
        if 0 <= e0 < ns and M.get("end_style") == "tapestop":   # the song slows to a stop (pitch drops)
            L = min(ef, ns - e0); src0 = max(0, off) + e0 - max(0, -off)
            tt = np.arange(L) / SR; D = L / SR
            pos_ = src0 + (tt - tt ** 2 / (2 * D)) * SR          # playback rate falls linearly from 1 to 0
            seg = np.stack([np.interp(pos_, np.arange(len(song)), song[:, c]) for c in range(2)], -1)
            seg *= np.linspace(1, 0.0, L)[:, None] ** 0.6
            music[e0:e0 + L] = seg * 10 ** (0 / 20); music[e0 + L:] = 0
        elif 0 <= e0 < ns:
            music[e0:e0 + ef] *= np.linspace(1, 0, len(music[e0:e0 + ef]))[:, None]; music[e0 + ef:] = 0
    music *= 10 ** (M.get("gain_db", 0) / 20)
    if M.get("duck_db"):                                       # dip the song under each cut so the transition sounds cut through
        env = np.ones(ns); g = 10 ** (-M["duck_db"] / 20); rmp = int(0.03 * SR)
        for s_ in SHOTS[:-1]:
            c0, c1 = int((s_["T1"] - 0.08) * SR), int((s_["T1"] + 0.20) * SR)
            c0, c1 = max(0, c0), min(ns, c1)
            if c1 - c0 > 2 * rmp:
                seg = np.full(c1 - c0, g); seg[:rmp] = np.linspace(1, g, rmp); seg[-rmp:] = np.linspace(g, 1, rmp)
                env[c0:c1] = np.minimum(env[c0:c1], seg)
        music *= env[:, None]
SFX_GAIN = 0.7 * 10 ** (EDL.get("sfx_gain_db", 0.0) / 20)      # sound-effects level vs the stream audio / song
if AUTO:
    bed = (a + music).mean(1); win = int(0.15 * SR)
    def _rms_db(v): return 10 * np.log10((v ** 2).mean() + 1e-12) if len(v) else -120.0
    for x, i0 in EVENTS:
        xm = x.mean(1) * SFX_GAIN
        if i0 < 0: xm = xm[-i0:]; x = x[-i0:]; i0 = 0
        n_ = min(len(xm), ns - i0)
        if n_ <= 0: continue
        e = np.convolve(xm[:n_] ** 2, np.ones(win) / win, mode="same"); pk = int(np.argmax(e))   # loudest 150 ms of the sound
        lo, hi = max(0, pk - win // 2), min(n_, pk + win // 2)
        need = (_rms_db(bed[i0 + lo:i0 + hi]) + AUTO.get("over_db", 4.0)) - _rms_db(xm[lo:hi])
        g = 10 ** (min(AUTO.get("max_boost_db", 18.0), max(0.0, need)) / 20)
        sfx[i0:i0 + n_] += x[:n_] * g
if FRZ and np.any(popa):
    pe = np.convolve(np.abs(popa).mean(1), np.ones(int(0.1 * SR)) / int(0.1 * SR), mode="same")
    duck = 1 - 0.55 * np.clip(pe / (pe.max() + 1e-9) * 4, 0, 1)
    music *= duck[:, None]; sfx *= duck[:, None]
mix = a + sfx * SFX_GAIN + music + popa
if EDL.get("debug_stems"):
    sfx.astype(np.float32).tofile(f"{WORK}/stem_sfx.f32"); music.astype(np.float32).tofile(f"{WORK}/stem_music.f32")
fade = int(0.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix = (np.tanh(mix * 1.15) * 0.95).astype(np.float32)
mix.tofile(f"{WORK}/mix.f32")
def finish(vpath, out, banner=None):
    full = out.replace(".mp4", "_full_tmp.mp4")
    if banner:   # IG: banner in the gap between the Reels header and the panel, fades with the edit
        bv = vpath.replace(".mp4", "_banner.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vpath, "-loop", "1", "-i", banner, "-filter_complex",
                        f"[1:v]{'scale=iw/2:-1,' if PREVIEW else ''}format=rgba,fade=in:st=0:d=0.3:alpha=1,fade=out:st={DUR - 0.5:.2f}:d=0.45:alpha=1[b];[0:v][b]overlay=0:{EDL.get('banner_y', 330) if not PREVIEW else EDL.get('banner_y', 330) // 2}:shortest=1,format=yuv420p[v]",
                        "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast" if PREVIEW else "medium", "-crf", "17", bv], check=True)
        vpath = bv
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", vpath, "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", f"{WORK}/mix.f32",
                    "-af", "loudnorm=I=-14:TP=-3:LRA=11,alimiter=limit=0.63:level=false", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", out if PREVIEW else full], check=True)
    if not PREVIEW:   # one pass, quality-targeted but capped (VBV) so the file always lands under the upload cap
        vbr = int(min(9000, (MAX_MB * 8 * 1024 * 0.95) / DUR - 200))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", full, *venc_args(final=True, vbr=vbr), "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", out], check=True)
        if os.path.getsize(out) > MAX_MB * 1024 * 1024:    # safety net: classic 2-pass at a lower target
            vb2 = int(vbr * 0.9); com = ["-c:v", "libx264", "-preset", "medium", "-b:v", f"{vb2}k", "-maxrate", f"{int(vb2 * 1.3)}k", "-bufsize", f"{vb2 * 2}k"]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", full, *com, "-pass", "1", "-passlogfile", f"{WORK}/2p", "-an", "-f", "null", os.devnull], check=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", full, *com, "-pass", "2", "-passlogfile", f"{WORK}/2p", "-c:a", "copy", "-movflags", "+faststart", out], check=True)
        os.remove(full)
    print("done", out, f"{os.path.getsize(out) / 1e6:.1f} MB", f"{DUR:.1f}s")
if "x" in FORMATS: finish(vid, OUT)
if "ig" in FORMATS: finish(vid_ig, OUT.replace(".mp4", "_ig.mp4"), None if IGL in ("stack", "ghost") else EDL.get("ig_banner"))
