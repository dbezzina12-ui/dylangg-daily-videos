#!/usr/bin/env python3
"""Prepare one win for editing: exact 1080p clip, voice/game stems, word transcript, contact sheet.

  python3 prep_edit.py WIN.json OUTDIR [--pad-before 20] [--pad-after 12] [--max 420]          (phase 1: clip, transcript, sheets)
  python3 prep_edit.py WIN.json OUTDIR --sep "12.0-30.5,61-118"                              (phase 2: voice/game stems)
Phase 1 transcribes the MIX (fast). Phase 2 separates ONLY the given clip-time ranges (the source ranges your shots use, +1 s
each side; Roformer costs ~11 s of CPU per second of audio, so never separate dead time), then re-transcribes the voice stem
inside those ranges for exact word timings and merges it into voice_words.json. Outside the ranges stems/voice.wav = the mix.

WIN.json is one doc from the Stream Win Picks page (date, bonus_start, hit, banner, end ...; TRUE stream times).
Writes OUTDIR/: clip.mp4 (clip t = 0 at stream time T0, printed + saved in prep.json), mix.wav, stems/voice.wav, stems/game.wav,
voice_words.json ([[start, end, word], ...] on the clip timeline), sheet_*.jpg (1 frame / 0.5 s, stamped with CLIP time), prep.json.
CPU-heavy steps (separation, transcription) take /tmp/hype_cpu.lock so parallel editors queue instead of fighting.
"""
import fcntl, json, os, subprocess, sys
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SP, "scan")); import scan_vod as sv
MODEL = "model_bs_roformer_ep_317_sdr_12.9755.ckpt"
def arg(n, d): return float(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
class cpu_lock:
    def __enter__(self): self.f = open("/tmp/hype_cpu.lock", "w"); fcntl.flock(self.f, fcntl.LOCK_EX); return self
    def __exit__(self, *a): fcntl.flock(self.f, fcntl.LOCK_UN); self.f.close()
def run(*c): subprocess.run([str(x) for x in c], check=True)

w = json.load(open(sys.argv[1])); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
t = {k: sv.secs(w[k]) for k in ("bonus_start", "hit", "banner", "end") if w.get(k) and ":" in str(w[k])}
start = t.get("bonus_start", t.get("hit", 0) - 90); stop = max(t.get("end", 0), t.get("banner", 0), t.get("hit", 0)) + arg("--pad-after", 12)
T0 = max(0.0, start - arg("--pad-before", 20)); T1 = min(stop, T0 + arg("--max", 420))
clip = os.path.join(out, "clip.mp4")
if not os.path.exists(clip): sv.clip(w["date"], T0, T1, clip)
mix = os.path.join(out, "mix.wav")
if not os.path.exists(mix): run("ffmpeg", "-v", "error", "-y", "-i", clip, "-vn", "-ac", "2", "-ar", "44100", mix)
st = os.path.join(out, "stems"); os.makedirs(st, exist_ok=True)
voice, game = os.path.join(st, "voice.wav"), os.path.join(st, "game.wav")
words = os.path.join(out, "voice_words.json")
def transcribe(path, t0=0.0, t1=None):
    from faster_whisper import WhisperModel
    import soundfile as sf, librosa
    x, sr = sf.read(path, dtype="float32"); x = x.mean(1) if x.ndim > 1 else x
    x = x[int(t0 * sr):int(t1 * sr) if t1 else None]
    x = librosa.resample(x, orig_sr=sr, target_sr=16000)
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(
        x, word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
    return [[round(t0 + q.start, 2), round(t0 + q.end, 2), q.word.strip()] for s in segs for q in (s.words or [])]
if "--sep" in sys.argv:
    rng = [tuple(map(float, r.split("-"))) for r in sys.argv[sys.argv.index("--sep") + 1].split(",") if r.strip()]
    import soundfile as sf
    with cpu_lock():
        sep = os.path.join(out, "sep"); subprocess.run(["rm", "-rf", sep]); os.makedirs(sep)
        y, sr = sf.read(mix, dtype="float32"); args = []
        for k, (a, b) in enumerate(rng):
            a = max(0.0, a - 1.0); b = min(len(y) / sr, b + 1.0)
            part = os.path.join(sep, f"r{k}.wav"); sf.write(part, y[int(a * sr):int(b * sr)], sr)
            run("audio-separator", part, "--model_filename", MODEL, "--model_file_dir", "/tmp/audio-separator-models",
                "--output_dir", sep, "--output_format", "WAV", "--mdxc_overlap", "2")
            fs = os.listdir(sep)
            v = next(f for f in fs if f.startswith(f"r{k}_") and "Vocals" in f); g = next(f for f in fs if f.startswith(f"r{k}_") and "Instrumental" in f)
            args += [os.path.join(sep, g), os.path.join(sep, v), f"{a:.3f}"]
        run("python3", os.path.join(SP, "oct11", "make_stems2.py"), mix, voice, game, *args)
        old = json.load(open(words)) if os.path.exists(words) else []
        new = []
        for (a, b) in rng: new += transcribe(voice, max(0.0, a - 1.0), b + 1.0)
        inside = lambda w: any(a - 1.0 <= w[0] <= b + 1.0 for a, b in rng)
        json.dump(sorted([w for w in old if not inside(w)] + new), open(words, "w"))
        subprocess.run(["rm", "-rf", sep])
    print("stems ready:", voice, game, "| ranges", rng); sys.exit(0)
if not os.path.exists(words):
    with cpu_lock(): json.dump(transcribe(mix), open(words, "w"))
# contact sheets on the CLIP timeline: 2 fps, 6 x 8 per sheet
raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", clip, "-vf", "fps=2,scale=320:180", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                     capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 180, 320, 3)
for k in range(0, len(fr), 48):
    ims = []
    for j, f in enumerate(fr[k:k + 48]):
        im = f.copy(); cv2.putText(im, f"{(k + j) / 2:.1f}", (4, 22), 0, 0.7, (0, 255, 255), 2); ims.append(im)
    while len(ims) % 6: ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(os.path.join(out, f"sheet_{k // 48:02d}.jpg"), np.vstack([np.hstack(ims[i:i + 6]) for i in range(0, len(ims), 6)]),
                [cv2.IMWRITE_JPEG_QUALITY, 82])
rel = {k: round(v - T0, 2) for k, v in t.items()}
json.dump({"T0": T0, "T1": T1, "clip_times": rel, "win": w}, open(os.path.join(out, "prep.json"), "w"), indent=1)
print(f"ready: {out}  clip {T1 - T0:.0f} s from {sv.hms(T0)}; win moments on the clip timeline: {rel}")
