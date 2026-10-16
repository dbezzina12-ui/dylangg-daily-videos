# make_stems2.py MIX.wav OUT_VOICE.wav OUT_GAME.wav [GAME_SEC.wav VOICE_SEC.wav OFFSET_S ...]
# separate voice and game tracks on the source timeline, for the engine's "stems2" audio path:
#   voice = Roformer vocals inside the separated sections, the untouched mix elsewhere (facecam cuts outside them)
#   game  = Roformer game lifted GAIN_DB and compressed (jingles can't blast), silent outside the sections
import os, sys, numpy as np, soundfile as sf
def tame(y, sr, thresh_db=-27.0, ratio=4.0):
    m = y.mean(1); hop = int(0.01 * sr); n = max(1, len(m) // hop)
    e = np.array([np.sqrt(np.mean(m[k * hop:(k + 1) * hop] ** 2) + 1e-12) for k in range(n)])
    over = np.maximum(0.0, 20 * np.log10(e + 1e-9) - thresh_db) * (1 - 1 / ratio)
    sm = np.zeros(n); a_up, a_dn = 1 - np.exp(-1 / 0.5), 1 - np.exp(-1 / 25)
    for k in range(1, n): sm[k] = sm[k - 1] + (over[k] - sm[k - 1]) * (a_up if over[k] > sm[k - 1] else a_dn)
    return y * np.interp(np.arange(len(m)) / hop, np.arange(n), 10 ** (-sm / 20)).astype(np.float32)[:, None]
def level(y, sr, target_db=-23.0, max_up=14.0, max_down=10.0):
    """slow leveler: brings the game bed to a steady level (400 ms windows, 150 ms attack, 600 ms release)"""
    m = y.mean(1); hop = int(0.05 * sr); n = max(1, len(m) // hop); win = 8
    e = np.array([np.sqrt(np.mean(m[max(0, (k - win // 2) * hop):(k + win // 2) * hop] ** 2) + 1e-12) for k in range(n)])
    want = np.clip(target_db - 20 * np.log10(e + 1e-9), -max_down, max_up)
    want[20 * np.log10(e + 1e-9) < -75] = 0.0                      # true silence stays silent (no noise pumping)
    sm = np.zeros(n); sm[0] = want[0]; a_up, a_dn = 1 - np.exp(-1 / 3.0), 1 - np.exp(-1 / 12.0)
    for k in range(1, n): sm[k] = sm[k - 1] + (want[k] - sm[k - 1]) * (a_dn if want[k] > sm[k - 1] else a_up)
    return y * np.interp(np.arange(len(m)) / hop, np.arange(n), 10 ** (sm / 20)).astype(np.float32)[:, None]
G = 10 ** (float(os.environ.get("GAIN_DB", "16")) / 20)
mix, sr = sf.read(sys.argv[1], dtype="float32"); voice = mix.copy(); game = np.zeros_like(mix); xf = int(0.03 * sr)
for fg, fv, off in zip(sys.argv[4::3], sys.argv[5::3], sys.argv[6::3]):
    g, _ = sf.read(fg, dtype="float32"); v, _ = sf.read(fv, dtype="float32")
    i0 = int(round(float(off) * sr)); n = min(len(g), len(mix) - i0)
    w = np.ones(n, np.float32); w[:xf] = np.linspace(0, 1, xf); w[-xf:] = np.linspace(1, 0, xf)
    voice[i0:i0 + n] = voice[i0:i0 + n] * (1 - w[:, None]) + v[:n] * w[:, None]
    game[i0:i0 + n] = tame(level(G * g[:n], sr), sr) * w[:, None]
sf.write(sys.argv[2], voice, sr, subtype="FLOAT"); sf.write(sys.argv[3], game, sr, subtype="FLOAT")
print("voice peak", round(20 * np.log10(np.abs(voice).max()), 1), "game peak", round(20 * np.log10(np.abs(game).max() + 1e-9), 1))
