#!/usr/bin/env python3
"""Daily pool update soundtrack: python3 audio.py out.wav [13.5]"""
import numpy as np, sys
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 13.5
N = int(SR * DUR)
RNG = np.random.default_rng(1234)


def T(d): return np.arange(int(SR * d)) / SR
def noise(d): return RNG.standard_normal(int(SR * d))
def filt(x, kind, f, order=2):
    return sosfilt(butter(order, f, kind, fs=SR, output='sos'), x)
def lp(x, f, o=2): return filt(x, 'low', f, o)
def hp(x, f, o=2): return filt(x, 'high', f, o)
def bp(x, lo, hi, o=2): return filt(x, 'band', [lo, hi], o)
def tv_lp(x, fc):
    """time-varying one-pole low-pass (fc array)"""
    a = 1 - np.exp(-2 * np.pi * np.asarray(fc) / SR); y = np.empty_like(x); s = 0.0
    for i in range(len(x)): s += a[i] * (x[i] - s); y[i] = s
    return y
def env_exp(d, tau, att=0.002):
    t = T(d); e = np.exp(-t / tau); na = max(1, int(att * SR)); e[:na] *= np.linspace(0, 1, na); return e
def midi(n): return 440.0 * 2 ** ((n - 69) / 12)


class Bus:
    def __init__(s): s.x = np.zeros((2, N))
    def add(s, sig, t, g=1.0, pan=0.0):

        i = int(round(t * SR))
        if sig.ndim == 1:
            a = (pan + 1) * np.pi / 4; sig = np.vstack([sig * np.cos(a), sig * np.sin(a)]) * np.sqrt(2)
        if i >= N: return
        j0 = max(0, -i); i = max(0, i); n = min(sig.shape[1] - j0, N - i)
        if n > 0: s.x[:, i:i + n] += g * sig[:, j0:j0 + n]


drums, bass, music, sfx, send = Bus(), Bus(), Bus(), Bus(), Bus()

# ---------------------------------------------------------------- instruments
def kick():
    t = T(0.5); f = 44 + 115 * np.exp(-t / 0.032) + 60 * np.exp(-t / 0.005)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.30)
    click = hp(noise(0.5), 1800) * np.exp(-t / 0.004) * 0.45
    return np.tanh(2.2 * body) * 0.9 + click

def clap():
    d = 0.35; t = T(d); nz = bp(noise(d), 900, 3800)
    e = np.zeros_like(t)
    for k, o in enumerate([0, 0.010, 0.021, 0.030]): e += (t >= o) * np.exp(-np.clip(t - o, 0, None) / (0.006 if k < 3 else 0.11))
    return nz * e * 0.9

def snare():
    d = 0.25; t = T(d)
    return bp(noise(d), 1200, 7000) * np.exp(-t / 0.07) * 0.8 + np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05) * 0.5

def hat(open_=False):
    d = 0.3 if open_ else 0.06; t = T(d); tau = 0.12 if open_ else 0.022
    return hp(noise(d), 7500, 4) * np.exp(-t / tau) * (0.5 if open_ else 0.6)

def saw(f, t, ph=0.0):
    """PolyBLEP band-limited saw"""
    p = (f * t + ph) % 1.0; dt = f / SR; y = 2 * p - 1
    m1 = p < dt; x = p[m1] / dt; y[m1] -= 2 * x - x * x - 1
    m2 = p > 1 - dt; x = (p[m2] - 1) / dt; y[m2] -= x * x + 2 * x + 1
    return y

def bass_note(f, d):
    t = T(d + 0.03); s = lp(saw(f, t) * 0.55 + saw(f * 1.005, t, 0.3) * 0.45, 900, 2) * 0.55 + np.sin(2 * np.pi * f / 2 * t) * 0.85
    e = np.ones_like(t); na = int(0.004 * SR); e[:na] = np.linspace(0, 1, na); nr = int(0.03 * SR); e[-nr:] = np.linspace(1, 0, nr)
    return np.tanh(1.4 * s * e)

def supersaw(freqs, d, cutoff=2600, tau=0.16, att=0.003, voices=5, spread=0.012):
    t = T(d); L = np.zeros_like(t); R = np.zeros_like(t); r = np.random.default_rng(int(sum(freqs)))
    for f in freqs:
        for v in range(voices):
            det = 1 + spread * (v - (voices - 1) / 2) / ((voices - 1) / 2); s = saw(f * det, t, r.random())
            if v % 2: L += s
            else: R += s
    e = env_exp(d, tau, att); n = len(freqs) * voices / 2
    return np.vstack([lp(L, cutoff) * e / n, lp(R, cutoff) * e / n])

def boom(d=1.6, f0=62, f1=27, g_noise=0.6):
    t = T(d); f = f1 + (f0 - f1) * np.exp(-t / 0.35)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    nz = lp(noise(d), 1400) * np.exp(-t / 0.16) * g_noise
    crack = hp(noise(d), 2500) * np.exp(-t / 0.018) * 0.6
    return np.tanh(1.6 * (sub + nz + crack))

def crash(d=2.2, g=1.0):
    t = T(d); nz = hp(noise(d), 3800, 2) * np.exp(-t / 0.9)
    met = sum(np.sign(np.sin(2 * np.pi * f * t)) for f in [3170, 4230, 5390, 6810, 8120]) / 5
    met = hp(met, 3000) * np.exp(-t / 0.6) * 0.35
    return (nz * 0.6 + met) * g * np.minimum(1, t / 0.002 + 0.0001)

def riser(d, f0=300, f1=9000, tone=True):
    t = T(d); u = t / d; fc = f0 * (f1 / f0) ** (u ** 1.6)
    nz = tv_lp(noise(d), fc); nz = hp(nz, 250) * (u ** 2.2)
    if tone:
        fr = 180 * (8 ** (u ** 1.3)); ph = 2 * np.pi * np.cumsum(fr) / SR
        nz = nz * 0.8 + (np.sin(ph) + 0.4 * np.sin(2 * ph + 0.5 * np.sin(ph * 0.5))) * (u ** 2.5) * 0.22
    return nz

def whoosh(d, f0=500, f1=3500, peak=0.55):
    t = T(d); u = t / d; fc = f0 * (f1 / f0) ** u
    nz = tv_lp(noise(d), fc); nz = hp(nz, 180)
    e = np.where(u < peak, (u / peak) ** 2, ((1 - u) / (1 - peak)) ** 1.5)
    return nz * e * 2.2

def tick(f=2600, g=1.0):
    t = T(0.03); return (np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) + hp(noise(0.03), 4000) * np.exp(-t / 0.002) * 0.5) * g

def bell(f, d=0.9, tau=0.35):
    t = T(d); s = np.zeros_like(t)
    for m, a, k in [(1, 1, 1), (2.0, 0.5, 0.6), (2.76, 0.35, 0.45), (5.4, 0.18, 0.25), (8.9, 0.08, 0.15)]:
        s += a * np.sin(2 * np.pi * f * m * t) * np.exp(-t / (tau * k))
    return s * np.minimum(1, t / 0.001 + 1e-4) * 0.5

def coin():
    s = np.zeros(int(SR * 1.2)); b1 = bell(1975.5, 1.1, 0.25); b2 = bell(2637.0, 1.1, 0.45); b3 = bell(3951, 1.1, 0.3)
    s[:len(b1)] += b1 * 0.8; o = int(0.075 * SR); n2 = min(len(s) - o, len(b2))
    s[o:o + n2] += b2[:n2] * 0.9 + b3[:n2] * 0.45
    sh = hp(noise(1.2), 6000) * np.exp(-T(1.2) / 0.12) * 0.25
    return s + sh

def glass():
    d = 0.9; s = np.zeros(int(SR * d)); r = np.random.default_rng(5)
    for k in range(70):
        tt = (r.random() ** 2) * 0.55; f = 2400 + r.random() * 7000; dd = 0.12; tp = T(dd)
        p = np.sin(2 * np.pi * f * tp) * np.exp(-tp / (0.008 + r.random() * 0.03)) * (1 - tt / 0.6) * (0.3 + 0.7 * r.random())
        i = int(tt * SR); s[i:i + len(p)] += p[:len(s) - i]
    s += hp(noise(d), 2500) * np.exp(-T(d) / 0.09) * 0.8
    return s * 0.5

def thud(f0=110, f1=50):
    t = T(0.5); f = f1 + (f0 - f1) * np.exp(-t / 0.05)
    return np.tanh(1.5 * (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16) + lp(noise(0.5), 700) * np.exp(-t / 0.05) * 0.6))

def clank():
    t = T(0.6); s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / k) for f, a, k in [(412, 1, .18), (1033, .7, .12), (1721, .5, .09), (2894, .35, .06), (4410, .2, .04)])
    return (s + hp(noise(0.6), 3000) * np.exp(-t / 0.01)) * 0.45

def blip(f0=700, f1=2200, d=0.09):
    t = T(d); f = f0 * (f1 / f0) ** (t / d); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) * 0.6

def zip_(d=0.35):
    t = T(d); nz = bp(noise(d), 3000, 9000); am = 0.5 + 0.5 * np.sign(np.sin(2 * np.pi * (40 + 120 * t / d) * t))
    return nz * am * np.sin(np.pi * t / d) * 0.5

def rev_cymbal(d):
    c = crash(d, 1.0)[::-1]; return c * np.linspace(0, 1, len(c)) ** 2



# =====================================================================
#   LIVE STANDINGS arrangement (14.0 s, 120 BPM, G minor, half-time trap groove)
#   locked to the engine timeline in st_timeline.js
# =====================================================================
X1, C0, C1, M0 = 1.5, 1.75, 3.0, 3.45
ROWS = [6.5, 5.5, 5.0, 4.5, 4.0]          # 1st .. 5th
X2, FLIP, X3 = 9.0, 9.5, 10.5
E0 = 10.55; FIN = 13.0

CH = {'Gm': [55, 58, 62, 67], 'Eb': [51, 55, 58, 63], 'Bb': [50, 53, 58, 62], 'F': [53, 57, 60, 65], 'Cm': [48, 51, 55, 60]}
ROOT = {'Gm': 43, 'Eb': 39, 'Bb': 46, 'F': 41, 'Cm': 36}
SEGS = [(0.0, 1.5, 'Gm'), (1.5, 2.9, 'Eb'), (3.0, 4.0, 'Gm'), (4.0, 5.0, 'Gm'), (5.0, 6.0, 'Eb'), (6.0, 6.4, 'F'),
        (6.5, 8.5, 'Gm'), (8.5, 9.0, 'F'), (9.0, 10.5, 'Eb'), (10.5, 12.0, 'Gm'), (12.0, FIN, 'F')]
def chord_at(t):
    for a, b, c in SEGS:
        if a <= t < b: return c
    return 'Gm'
def hz(ns): return [midi(n) for n in ns]
GAPS = [(2.9, 3.0), (6.4, 6.5)]
def in_gap(t): return any(a <= t < b for a, b in GAPS)
DROP = lambda t: (C1 <= t < 4.0) or (6.5 <= t < 8.5) or (E0 + 0.15 <= t < FIN)

def k808(f, d=0.55):
    t = T(d); fr = f * (1 + 1.2 * np.exp(-t / 0.02))
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / 0.32)
    e = np.minimum(1, t / 0.003); return np.tanh(2.0 * s * e) * 0.9

# ---- drums: half-time. kick on 1 + "and of 2", clap on 3, hats in 8ths with 16th/32nd rolls into hits
KICK = kick(); CLAP = clap()
KICKS = [0.0]
for bar in np.arange(1.5, FIN, 2.0):
    for o in (0.0, 0.75, 1.25):
        tk = bar + o
        if tk < FIN and not in_gap(tk): KICKS.append(tk)
KICKS += [C1, ROWS[0], X2, FLIP, FIN]
KICKS = sorted(set(round(k, 3) for k in KICKS))
for tk in KICKS: drums.add(KICK, tk, 0.95)
for bar in np.arange(1.5, FIN, 2.0):
    tc = bar + 1.0
    if tc < FIN and not in_gap(tc): drums.add(CLAP, tc, 0.62); send.add(CLAP, tc, 0.22)
def hat_roll(a, b, step, g0, g1):
    tt = a
    while tt < b - 1e-6:
        u = (tt - a) / max(1e-6, b - a); drums.add(hat(False), tt, g0 + (g1 - g0) * u, pan=0.2 * np.sin(tt * 9)); tt += step
for i in range(int(0.5 / 0.25), int(FIN / 0.25)):
    tt = i * 0.25
    if in_gap(tt) or any(a - 0.01 <= tt < b for a, b in [(2.5, 2.9), (5.9, 6.4), (8.75, 9.0), (10.25, 10.5)]): continue
    drums.add(hat(False), tt, 0.15 if i % 2 == 0 else 0.09, pan=-0.15 if i % 2 else 0.1)
hat_roll(2.5, 2.9, 0.0625, 0.07, 0.2); hat_roll(5.9, 6.4, 0.03125, 0.05, 0.22)
hat_roll(8.75, 9.0, 0.0625, 0.08, 0.18); hat_roll(10.25, 10.5, 0.0625, 0.08, 0.18)
for tt in np.arange(1.75, FIN, 0.5):
    if not in_gap(tt): drums.add(hat(True), tt, 0.10, pan=0.25)
SN = snare(); tt = 5.95
while tt < 6.4:
    u = (tt - 5.95) / 0.45; drums.add(SN, tt, 0.2 + 0.5 * u); send.add(SN, tt, 0.1 * u); tt += 0.0625 if u < 0.5 else 0.03125

# ---- 808 bass follows the kicks, root of the chord
for tk in KICKS:
    if tk < 1.5 and tk != 0.0: continue
    f = midi(ROOT[chord_at(tk + 0.01)]); bass.add(k808(f, 0.5 if DROP(tk) else 0.42), tk, 0.62)

# ---- pads + plucked arp + drop stabs
for a_, b_, c in SEGS:
    pad = supersaw(hz(CH[c]), b_ - a_ + 0.25, cutoff=1500 if a_ >= 1.5 else 1000, tau=4.0, att=0.08, voices=5, spread=0.011)
    music.add(pad, a_, 0.17)
for i in range(int(1.5 / 0.125), int(FIN / 0.125)):
    tt = i * 0.125
    if in_gap(tt) or (2.5 <= tt < 3.0): continue
    ns = CH[chord_at(tt)]; n = ns[[0, 2, 1, 3, 2, 1, 3, 2][i % 8]] + 12
    pl = bell(midi(n), 0.35, 0.09); music.add(pl, tt, 0.035 if not DROP(tt) else 0.025, pan=0.35 if i % 2 else -0.35); send.add(pl, tt, 0.03)
for i in range(int(C1 / 0.25), int(FIN / 0.25)):
    tt = i * 0.25
    if not DROP(tt) or i % 4 not in (1, 3): continue
    st = supersaw(hz([n + 12 for n in CH[chord_at(tt)]]), 0.28, cutoff=3400, tau=0.07)
    music.add(st, tt, 0.26); send.add(st, tt, 0.12)

def hit(tt, chord, g=1.0, big=False, oct_=0):
    sfx.add(boom(1.8 if big else 1.2), tt, 0.85 * g)
    st = supersaw(hz([n + 12 * oct_ for n in CH[chord]]), 1.4 if big else 0.7, cutoff=4200 if big else 3200, tau=0.35 if big else 0.16)
    music.add(st, tt, 0.42 * g); send.add(st, tt, 0.25 * g)
    if big: sfx.add(crash(2.4), tt, 0.5 * g); send.add(crash(2.4), tt, 0.1)

# ---- hook
hit(0.0, 'Gm', 1.0, big=True, oct_=1)
sfx.add(blip(900, 1800, 0.07), 0.32, 0.28)
for k in range(3): sfx.add(tick(3600, 0.12), 0.34 + k * 0.25, pan=0.2)
sfx.add(riser(0.5, 600, 7000, False), 0.85, 0.32)
for k in range(7): sfx.add(whoosh(0.12, 1500, 6000, 0.4), X1 - 0.2 + k * 0.03, 0.12, pan=(-0.6 if k % 2 else 0.6))   # shutter slats
sfx.add(thud(120, 55), X1, 0.6)
# ---- pool odometer
c_ = coin(); sfx.add(c_, X1 + 0.06, 0.35); send.add(c_, X1 + 0.06, 0.2)
for k in range(8): sfx.add(tick(3200 + 300 * (k % 3), 0.16), X1 + 0.02 + k * 0.035)
sfx.add(riser(C1 - C0, 250, 11000), C0, 0.72); sfx.add(rev_cymbal(0.8), C1 - 0.8, 0.28)
for k in range(1, 41):
    tt = C0 + (C1 - C0) * (k / 40) ** (1 / 1.8)
    if tt < C1 - 0.01: sfx.add(tick(1800 + 1800 * (k / 40), 0.28), tt)
hit(C1, 'Gm', 1.25, big=True, oct_=1)
c_ = coin(); sfx.add(c_, C1 + 0.03, 0.55); send.add(c_, C1 + 0.03, 0.3)
sfx.add(boom(2.2, 55, 24, 0.8), C1, 0.8); sfx.add(thud(), C1 + 0.1, 0.55)
sfx.add(whoosh(0.5, 400, 5000, 0.5), M0, 0.5)                                       # pool flies into the header
# ---- rows: 5th..2nd on the beat, 1st with a build
for j, tr in enumerate(ROWS[::-1]):                     # 5th, 4th, 3rd, 2nd, 1st
    lead = tr == ROWS[0]
    sfx.add(whoosh(0.22, 800, 7000, 0.6), tr - 0.16, 0.35, pan=0.5)
    sfx.add(thud(100 + 12 * j, 50), tr, 0.55 if not lead else 0.2)
    for k in range(12): sfx.add(tick(2400 + 200 * j + 120 * (k % 2), 0.11), tr + 0.7 * (k / 12) ** 1.6, pan=-0.2)
    b_ = bell(midi([74, 77, 79, 82, 86][j]), 0.7, 0.22); sfx.add(b_, tr + 0.12, 0.16); send.add(b_, tr + 0.12, 0.18)
    c_ = coin(); sfx.add(c_, tr + 0.12, 0.25 if not lead else 0.5, pan=0.4); send.add(c_, tr + 0.12, 0.15)
sfx.add(riser(0.85, 300, 9000), 5.65, 0.55); sfx.add(rev_cymbal(0.6), 5.9, 0.3)
hit(ROWS[0], 'Gm', 1.3, big=True, oct_=1); sfx.add(boom(2.2, 58, 24, 0.8), ROWS[0], 0.7)
for k, n in enumerate([79, 82, 86, 91, 94]):
    b_ = bell(midi(n), 0.9, 0.3); sfx.add(b_, ROWS[0] + 0.05 + k * 0.05, 0.12, pan=-0.4 + k * 0.2); send.add(b_, ROWS[0] + 0.05 + k * 0.05, 0.16)
sfx.add(blip(600, 2000), 4.1, 0.3, pan=-0.5)                                          # ticker slides up
# ---- flip clock
for k in range(7): sfx.add(whoosh(0.12, 1500, 6000, 0.4), X2 - 0.2 + k * 0.03, 0.12, pan=(-0.6 if k % 2 else 0.6))
sfx.add(thud(120, 55), X2, 0.55)
for k in range(4): sfx.add(tick(1900 if k % 2 == 0 else 1500, 0.55), X2 + 0.05 + k * 0.11, pan=0.15 * (1 if k % 2 else -1))
hit(FLIP, 'Eb', 1.05, big=True, oct_=1); sfx.add(clank(), FLIP + 0.02, 0.6); sfx.add(thud(140, 60), FLIP + 0.18, 0.5)
for k in range(5): sfx.add(tick(2000 if k % 2 == 0 else 1600, 0.35), FLIP + 0.35 + k * 0.125, pan=0.15 * (1 if k % 2 else -1))
# ---- end card (same moves as the main promo)
for k in range(7): sfx.add(whoosh(0.12, 1500, 6000, 0.4), X3 - 0.2 + k * 0.03, 0.12, pan=(-0.6 if k % 2 else 0.6))
for k, n in enumerate([79, 82, 86, 91, 94, 98]):
    b_ = bell(midi(n), 0.8, 0.25); sfx.add(b_, E0 - 0.04 + k * 0.04, 0.12, pan=-0.5 + k * 0.1); send.add(b_, E0 - 0.04 + k * 0.04, 0.15)
hit(E0 + 0.15, 'Gm', 0.95, big=True)
for k in range(int(0.6 / 0.022)): sfx.add(tick(2200 + (k % 5) * 250, 0.22), E0 + 0.15 + k * 0.022, pan=-0.3)
for i in range(7): sfx.add(tick(3000 + i * 180, 0.55), E0 + 0.35 + i * 0.07, pan=-0.3)
c_ = coin(); sfx.add(c_, E0 + 0.8, 0.55); send.add(c_, E0 + 0.8, 0.3)
sfx.add(whoosh(0.34, 400, 3000, 0.7), E0 + 0.42, 0.6, pan=0.6); sfx.add(thud(120, 55), E0 + 0.78, 0.7, pan=0.4)
for k in range(10): sfx.add(tick(3400, 0.14), E0 + 0.7 + k / 40)
for ts in (E0 + 1.5, FIN - 0.08):
    for k, n in enumerate([91, 94, 98, 103]):
        b_ = bell(midi(n), 0.6, 0.18); sfx.add(b_, ts + 0.1 + k * 0.05, 0.07); send.add(b_, ts + 0.1 + k * 0.05, 0.08)
hit(FIN, 'Gm', 1.2, big=True, oct_=1)

# ---------------------------------------------------------------- mix
tax = np.arange(N) / SR
duck = np.ones(N)
for tk in KICKS:
    i = int(tk * SR); n = min(N - i, int(0.45 * SR)); tt = np.arange(n) / SR
    duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.65 * np.exp(-tt / 0.09))
music.x[:, :] *= (0.4 + 0.6 * duck)
bass.x *= np.where(tax < FIN + 0.5, 1, 0)
ir_d = 1.7; ti = T(ir_d)
irL = lp(RNG.standard_normal(len(ti)), 6500) * np.exp(-ti / 0.45); irR = lp(RNG.standard_normal(len(ti)), 6500) * np.exp(-ti / 0.45)
pd = int(0.018 * SR); irL[:pd] = 0; irR[:pd] = 0
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
verb = np.vstack([fftconvolve(send.x[0], irL)[:N], fftconvolve(send.x[1], irR)[:N]]) * 0.9
G = {'drums': 0.58, 'bass': 0.85, 'music': 3.4, 'sfx': 0.75, 'verb': 1.3}
mix = drums.x * G['drums'] + bass.x * G['bass'] + music.x * G['music'] + sfx.x * G['sfx'] + verb * G['verb']
mix = hp(mix, 28, 2)
rms0 = np.sqrt((mix ** 2).mean()); mix *= 10 ** (-14.0 / 20) / rms0
k = 0.62; a_ = np.abs(mix); mix = np.where(a_ < k, mix, np.sign(mix) * (k + (1 - k) * np.tanh((a_ - k) / (1 - k))))
mix *= 10 ** (-1.0 / 20) / max(1.0, np.abs(mix).max())
fi = int(0.004 * SR); mix[:, :fi] *= np.linspace(0, 1, fi)
fo = int(0.35 * SR); mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
rms = np.sqrt((mix ** 2).mean()); print('audio peak', round(float(np.abs(mix).max()), 3), 'rms dBFS', round(float(20 * np.log10(rms)), 1))
wavfile.write(sys.argv[1] if len(sys.argv) > 1 else 'track.wav', SR, (mix.T * 32767).astype(np.int16))
