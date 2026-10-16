import sys, json, numpy as np, soundfile as sf
from faster_whisper import WhisperModel
x, sr = sf.read(sys.argv[1], dtype="float32")
if x.ndim > 1: x = x.mean(1)
import librosa
def _wdev():  # CUDA (float16) when a GPU is present, else CPU int8
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0: return {"device": "cuda", "compute_type": "float16"}
    except Exception: pass
    return {"device": "cpu", "compute_type": "int8"}

x = librosa.resample(x, orig_sr=sr, target_sr=16000)
m = WhisperModel("small.en", **_wdev())
segs, _ = m.transcribe(x, word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
out = [{"a": round(s.start, 2), "b": round(s.end, 2), "text": s.text.strip(),
        "words": [[round(w.start, 2), round(w.end, 2), w.word.strip()] for w in (s.words or [])]} for s in segs]
json.dump(out, open(sys.argv[2], "w"), indent=1)
for s in out: print(f'{s["a"]:7.2f}-{s["b"]:7.2f}  {s["text"]}')
