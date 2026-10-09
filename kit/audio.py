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
#   DAILY POOL UPDATE arrangement (13.5 s, 120 BPM), locked to engine TL
# =====================================================================
END_T = 10.0                     # TL.end   (end card)
FIN = 12.5                       # TL.fin   (final button)
C0, C1 = 2.0, 3.5                # counter start / landing
WAYS = 5.28                      # triptych drop
SLAM = 9.0                       # OCT 15 slam

CH = {'Fm': [53, 56, 60, 65], 'Db': [49, 53, 56, 61], 'Ab': [56, 60, 63, 68], 'Eb': [51, 55, 58, 63]}
ROOT = {'Fm': 41, 'Db': 37, 'Ab': 44, 'Eb': 39}
SEGS = [(0.0, 1.5, 'Fm'), (1.5, 3.4, 'Eb'), (3.5, 5.0, 'Fm'), (5.0, 7.0, 'Db'), (7.0, 8.5, 'Ab'), (8.5, 10.0, 'Eb'), (10.0, 11.5, 'Fm'), (11.5, FIN, 'Eb')]
def chord_at(t):
    for a, b, c in SEGS:
        if a <= t < b: return c
    return 'Fm'
def hz(ns): return [midi(n) for n in ns]
GAP = (3.4, 3.5)
def in_gap(t): return GAP[0] <= t < GAP[1]
DROP = lambda t: (C1 <= t < 5.0) or (SLAM <= t < 9.88) or (END_T + 0.15 <= t < FIN)

# ---- drums
KICKS = [0.0, 0.5, 1.0] + [1.5 + k * 0.5 for k in range(int((FIN - 1.5) / 0.5))] + [FIN]
KICKS = [k for k in KICKS if not in_gap(k)]
KICK = kick()
for tk in KICKS: drums.add(KICK, tk, 0.95 if tk >= 1.5 or tk == 0 else 0.7)
CLAP = clap()
for k in range(int((FIN - 1.5) / 0.5)):
    tb = 1.5 + k * 0.5
    if k % 2 == 1 and not (2.5 <= tb < 3.5): drums.add(CLAP, tb, 0.55); send.add(CLAP, tb, 0.18)
for i in range(int(0.5 / 0.125), int(FIN / 0.125)):
    tt = i * 0.125
    if in_gap(tt): continue
    acc = 1.0 if i % 2 == 0 else 0.55
    drums.add(hat(False), tt, (0.16 if tt >= 1.5 else 0.10) * acc, pan=0.25 if i % 4 == 1 else -0.1)
for k in range(int((FIN - 1.5) / 0.5)):
    tt = 1.5 + k * 0.5 + 0.25
    if in_gap(tt): continue
    drums.add(hat(True), tt, 0.13, pan=0.15)
SN = snare(); tt = 2.5
while tt < 3.38:
    u = (tt - 2.5) / 0.88; step = 0.125 if u < 0.4 else 0.0625 if u < 0.75 else 0.03125
    drums.add(SN, tt, 0.2 + 0.45 * u); send.add(SN, tt, 0.08 * u); tt += step

# ---- bass
for i in range(int(1.5 / 0.125), int(FIN / 0.125)):
    tt = i * 0.125; c = chord_at(tt); f = midi(ROOT[c])
    if in_gap(tt): continue
    if DROP(tt):
        if i % 2 == 1 or i % 8 != 0: bass.add(bass_note(f * (2 if i % 4 == 3 else 1), 0.1), tt, 0.5)
    elif i % 4 == 2: bass.add(bass_note(f, 0.2), tt, 0.55)

# ---- pad + stabs
for a_, b_, c in SEGS:
    pad = supersaw(hz(CH[c]), b_ - a_ + 0.2, cutoff=2400 if (a_, c) == (1.5, 'Eb') else 1300, tau=4.0, att=0.06, voices=5, spread=0.010)
    music.add(pad, a_, 0.16 if a_ < 1.5 else 0.20)
for i in range(int(C1 / 0.25), int(FIN / 0.25)):
    tt = i * 0.25
    if not DROP(tt) or i % 2 == 0: continue
    st = supersaw(hz([n + 12 for n in CH[chord_at(tt)]]), 0.3, cutoff=3200, tau=0.08)
    music.add(st, tt, 0.28); send.add(st, tt, 0.12)

def hit(tt, chord, g=1.0, big=False, oct_=0):
    sfx.add(boom(1.8 if big else 1.2), tt, 0.85 * g)
    st = supersaw(hz([n + 12 * oct_ for n in CH[chord]]), 1.4 if big else 0.7, cutoff=4200 if big else 3200, tau=0.35 if big else 0.16)
    music.add(st, tt, 0.42 * g); send.add(st, tt, 0.25 * g)
    if big: sfx.add(crash(2.4), tt, 0.5 * g); send.add(crash(2.4), tt, 0.1)

# ---- hook: POOL UPDATE snaps in, LIVE pill pops
hit(0.0, 'Fm', 1.0, big=True, oct_=1)
sfx.add(blip(900, 1800, 0.07), 0.30, 0.28)
for k in range(3): sfx.add(tick(3600, 0.12), 0.32 + k * 0.25, pan=0.2)          # live "blink"
sfx.add(riser(0.48, 600, 7000, False), 0.9, 0.3)
sfx.add(whoosh(0.34, 700, 7000, 0.5), 1.30, 0.6)
# ---- graph: $10,000 drops in
hit(1.5, 'Eb', 0.55)
c_ = coin(); sfx.add(c_, 1.56, 0.4); send.add(c_, 1.56, 0.25)
for k in range(8): sfx.add(tick(3200 + 300 * (k % 3), 0.18), 1.5 + k * 0.035)
b_ = bell(1046.5, 0.8, 0.3); sfx.add(b_, 1.7, 0.16); send.add(b_, 1.7, 0.2)
for k in range(26): sfx.add(tick(3000 + 250 * (k % 3), 0.12), 2.05 + k / 75)      # tagline typing
# ---- count up: riser + accelerating ticks (one per 1/40th of the climb)
sfx.add(riser(1.5, 250, 11000), C0, 0.72); sfx.add(rev_cymbal(0.9), C1 - 0.9, 0.28)
for k in range(1, 41):
    tt = C0 + (C1 - C0) * (k / 40) ** (1 / 1.8)
    if tt < C1 - 0.01: sfx.add(tick(1800 + 1800 * (k / 40), 0.28), tt)
# ---- landing: today's pool
hit(C1, 'Fm', 1.25, big=True, oct_=1)
c_ = coin(); sfx.add(c_, C1 + 0.03, 0.55); send.add(c_, C1 + 0.03, 0.3)
c_ = coin(); sfx.add(c_, C1 + 0.16, 0.35, pan=0.3); send.add(c_, C1 + 0.16, 0.2)
sfx.add(boom(2.2, 55, 24, 0.8), C1, 0.8)
sfx.add(crash(2.6), C1 + 0.02, 0.35, pan=0.3)
sfx.add(thud(), C1 + 0.1, 0.6)                                                     # NO MAX CAP slam
sfx.add(whoosh(0.3, 1500, 5000, 0.4), C1 + 0.3, 0.14, pan=-0.3)
# ---- 3 ways to win, with amounts rolling up and locking
sfx.add(whoosh(0.34, 700, 7000, 0.5), 4.9, 0.7)
hit(WAYS, 'Db', 1.1, big=True, oct_=1); sfx.add(thud(), WAYS, 0.9)
sfx.add(blip(600, 2000), WAYS + 0.14, 0.35, pan=0.1); sfx.add(clank(), WAYS + 0.16, 0.5, pan=0.5)
for i, ta in enumerate([5.50, 5.66, 5.82]):
    pan = [-0.4, 0.0, 0.4][i]
    for k in range(14): sfx.add(tick(2600 + 300 * i + 150 * (k % 2), 0.13), ta + 0.05 + 0.7 * (k / 14) ** 1.6, pan=pan)
    c_ = coin(); sfx.add(c_, ta + 0.8, 0.32, pan=pan); send.add(c_, ta + 0.8, 0.18)
# ---- round ends
sfx.add(riser(0.5, 400, 6000, False), 8.0, 0.3)
sfx.add(whoosh(0.32, 500, 6000, 0.55), 8.38, 0.55)
sfx.add(blip(900, 1800, 0.07), 8.62, 0.25)
for k in range(4): sfx.add(tick(1900 if k % 2 == 0 else 1500, 0.55), 8.5 + k * 0.125, pan=0.15 * (1 if k % 2 else -1))   # clock tick-tock
hit(SLAM, 'Eb', 1.15, big=True, oct_=1); sfx.add(boom(1.6, 64, 28, 0.6), SLAM, 0.6)
sfx.add(blip(700, 2400), SLAM + 0.16, 0.3)
for k in range(6): sfx.add(tick(2000 if k % 2 == 0 else 1600, 0.35), SLAM + 0.25 + k * 0.125, pan=0.15 * (1 if k % 2 else -1))
# ---- end card (same moves as the main promo)
E0 = END_T
sfx.add(whoosh(0.32, 500, 6000, 0.55), E0 - 0.2, 0.7)
for k, n in enumerate([77, 80, 84, 89, 92, 96]):
    b_ = bell(midi(n), 0.8, 0.25); sfx.add(b_, E0 - 0.04 + k * 0.04, 0.12, pan=-0.5 + k * 0.1); send.add(b_, E0 - 0.04 + k * 0.04, 0.15)
hit(E0 + 0.15, 'Fm', 0.95, big=True)
for k in range(int(0.6 / 0.022)): sfx.add(tick(2200 + (k % 5) * 250, 0.22), E0 + 0.15 + k * 0.022, pan=-0.3)
for i in range(7): sfx.add(tick(3000 + i * 180, 0.55), E0 + 0.35 + i * 0.07, pan=-0.3)
c_ = coin(); sfx.add(c_, E0 + 0.8, 0.55); send.add(c_, E0 + 0.8, 0.3)
sfx.add(whoosh(0.34, 400, 3000, 0.7), E0 + 0.42, 0.6, pan=0.6); sfx.add(thud(120, 55), E0 + 0.78, 0.7, pan=0.4)
for k in range(10): sfx.add(tick(3400, 0.14), E0 + 0.7 + k / 40)
sfx.add(whoosh(0.3, 1500, 5000, 0.4), E0 + 0.95, 0.12)
for ts in (E0 + 1.5, FIN - 0.08):
    for k, n in enumerate([89, 92, 96, 101]):
        b_ = bell(midi(n), 0.6, 0.18); sfx.add(b_, ts + 0.1 + k * 0.05, 0.07); send.add(b_, ts + 0.1 + k * 0.05, 0.08)
hit(FIN, 'Fm', 1.2, big=True, oct_=1)

# ---------------------------------------------------------------- mix
tax = np.arange(N) / SR
duck = np.ones(N)
for tk in KICKS:
    i = int(tk * SR); n = min(N - i, int(0.45 * SR)); tt = np.arange(n) / SR
    duck[i:i + n] = np.minimum(duck[i:i + n], 1 - 0.72 * np.exp(-tt / 0.085))
bass.x *= duck; music.x[:, :] *= (0.35 + 0.65 * duck)
bass.x *= np.where(tax < FIN + 0.02, 1, 0)
ir_d = 1.7; ti = T(ir_d)
irL = lp(RNG.standard_normal(len(ti)), 6500) * np.exp(-ti / 0.45); irR = lp(RNG.standard_normal(len(ti)), 6500) * np.exp(-ti / 0.45)
pd = int(0.018 * SR); irL[:pd] = 0; irR[:pd] = 0
irL /= np.sqrt((irL ** 2).sum()); irR /= np.sqrt((irR ** 2).sum())
verb = np.vstack([fftconvolve(send.x[0], irL)[:N], fftconvolve(send.x[1], irR)[:N]]) * 0.9
G = {'drums': 0.55, 'bass': 0.95, 'music': 3.6, 'sfx': 0.75, 'verb': 1.3}
mix = drums.x * G['drums'] + bass.x * G['bass'] + music.x * G['music'] + sfx.x * G['sfx'] + verb * G['verb']
mix = hp(mix, 28, 2)
rms0 = np.sqrt((mix ** 2).mean()); mix *= 10 ** (-14.0 / 20) / rms0
k = 0.62; a_ = np.abs(mix); mix = np.where(a_ < k, mix, np.sign(mix) * (k + (1 - k) * np.tanh((a_ - k) / (1 - k))))
mix *= 10 ** (-1.0 / 20) / max(1.0, np.abs(mix).max())
fi = int(0.004 * SR); mix[:, :fi] *= np.linspace(0, 1, fi)
fo = int(0.35 * SR); mix[:, -fo:] *= np.linspace(1, 0, fo) ** 1.5
rms = np.sqrt((mix ** 2).mean()); print('audio peak', round(float(np.abs(mix).max()), 3), 'rms dBFS', round(float(20 * np.log10(rms)), 1))
wavfile.write(sys.argv[1] if len(sys.argv) > 1 else 'track.wav', SR, (mix.T * 32767).astype(np.int16))
