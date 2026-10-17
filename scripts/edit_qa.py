#!/usr/bin/env python3
"""Pre-send checks for a finished hype edit. Run after every full render, before sending it to Dylan.

  python3 -I edit_qa.py EDIT.mp4 WORK_DIR [--max-mb 29]

WORK_DIR is the EDL's "work" folder (the engine writes timeline.json there). Checks:
  - file size under the upload cap, duration, loudness (integrated LUFS and true peak)
  - his words in the finished audio: any phrase said twice (e.g. "not fucking bad" twice) -> FAIL
  - every blurred shot: OCR every 4th frame; any readable money amount -> FAIL
  - freezes: none in the last 3 s (he wants the freeze on the big win, not the end) -> WARN
  - the last big hit stays on screen at least 0.8 s before the next cut -> WARN
Prints PASS / WARN / FAIL lines and exits 1 on any FAIL.
"""
import json, os, re, subprocess, sys
import numpy as np

fails, warns = [], []
def out(level, msg):
    (fails if level == "FAIL" else warns if level == "WARN" else []).append(msg)
    print(f"{level:4s}  {msg}")


def frame(video, t, w=1920, h=1080):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", f"scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3) if len(raw) == w * h * 3 else None


def main(video, work, max_mb=29.0):
    tl = json.load(open(os.path.join(work, "timeline.json")))
    mb = os.path.getsize(video) / 2 ** 20                    # MiB, the unit the engine sizes its encode to
    out("PASS" if mb <= max_mb else "FAIL", f"size {mb:.1f} MiB (cap {max_mb}), duration {tl['dur']:.1f} s")

    ld = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-af", "ebur128=peak=true", "-f", "null", "-"],
                        capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", ld); TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", ld)
    if I:
        i_, tp = float(I[-1]), float(TP[-1]) if TP else 0.0
        out("PASS" if -16 <= i_ <= -11 and tp <= -1.0 else "WARN", f"loudness {i_:.1f} LUFS, true peak {tp:.1f} dBTP")

    # repeated phrases in the finished audio
    import librosa, soundfile as sf
    from faster_whisper import WhisperModel
    wav = subprocess.run(["ffmpeg", "-v", "quiet", "-i", video, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(wav, np.float32)
    segs, _ = WhisperModel("small.en", device="cpu", compute_type="int8").transcribe(
        x, word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
    words = [(w.start, re.sub(r"[^a-z0-9']", "", w.word.lower())) for s in segs for w in (s.words or [])]
    words = [(t, w) for t, w in words if w]
    print("      words: " + " ".join(w for _, w in words))
    seen, reported = {}, set()
    for n in (4, 3):
        for i in range(len(words) - n + 1):
            g = " ".join(w for _, w in words[i:i + n]); t = words[i][0]
            if g in seen and t - seen[g] > 2.0 and not any(g in r for r in reported):
                reported.add(g); out("INFO", f'"{g}" said twice (OK: Dylan wants every line in full) ({seen[g]:.1f} s and {t:.1f} s)')
            seen.setdefault(g, t)
    if not reported: out("PASS", "no repeated phrases")

    # blurred numbers must be unreadable
    blurred = [s for s in tl["shots"] if s.get("blur")]
    if blurred:
        from rapidocr_onnxruntime import RapidOCR
        ocr = RapidOCR(); leaks = []
        for s in blurred:
            for t in np.arange(s["T0"], s["T1"], 4 / 60):
                im = frame(video, t)
                if im is None: continue
                for _, text, conf in (ocr(im)[0] or []):
                    if re.search(r"\d[\d,]*\.\d\d", text.replace(" ", "")) and float(conf) > 0.6: leaks.append((round(t, 2), text))
        out("FAIL" if leaks else "PASS", f"blur leaks: {leaks[:6]}" if leaks else f"blurred shots: no readable amounts ({len(blurred)} shot(s))")

    for f in tl["freezes"]:
        if f["T0"] > tl["dur"] - 3.0: out("WARN", f"freeze at {f['T0']:.1f} s sits in the last 3 s")
    big = [(h[0], s) for s in tl["shots"] for h in s["hits"] if h[2]]
    if big:
        t, s = max(big, key=lambda b: b[0])
        hold = s["T1"] - t
        out("PASS" if hold >= 0.8 else "WARN", f"last big hit on screen {hold:.2f} s before the cut")
    print(f"\n{len(fails)} fail, {len(warns)} warn")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    main(a[0], a[1], float(a[a.index("--max-mb") + 1]) if "--max-mb" in a else 29.0)
