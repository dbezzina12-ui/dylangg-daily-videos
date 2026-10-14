# Audio tools for the slot-stream hype-edit pipeline (voice/game separation, beat/drop detection, CPU transcription, loudness/ducking)

Research date: 2026-10-14. Star counts, last-push dates, archive flags and licenses come from the GitHub repository search API, queried on 2026-10-14. PyPI versions and upload dates come from `pypi.org/pypi/<pkg>/json`, queried the same day. "Last push" is the repo's `pushed_at` timestamp.

**Environment observations (measured in this research session, not from a third-party source).** The research container had 4 vCPU (Intel Xeon @ 2.80 GHz), 15 GB RAM, Python 3.13.16, numpy 2.5.3, onnxruntime 1.29.0 and ffmpeg. It had no torch. Its egress proxy rejected CONNECT to these hosts:
- huggingface.co
- download.pytorch.org (the CPU-only torch wheel index)
- dl.fbaipublicfiles.com
- cloud.cp.jku.at (the beat_this weights)
- modelscope.cn
- openaipublic.azureedge.net (the OpenAI Whisper weights)
- essentia.upf.edu
- hf-mirror.com

PyPI and raw.githubusercontent.com were reachable. A `faster-whisper` model load failed with `ProxyError: 403 Forbidden` from Hugging Face. If the production render container has the same egress policy, every ML model below needs its weights staged ahead of time, for example vendored into the repo or an artifact store. The pip install alone is not enough. The two exceptions are Silero VAD, whose model ships inside the pip wheel, and pure-DSP tools (librosa, pyloudnorm, ffmpeg).

## Q1. Separating the voice from the game audio on CPU (Demucs, audio-separator/UVR, Spleeter, Open-Unmix, speech enhancement)

### Takeaway
The cleanest open vocal separators today are the RoFormer models (BS-RoFormer and MelBand RoFormer), with vocal SDR of about 12.4–12.9 dB. htdemucs_ft scores about 10.8 dB and htdemucs about 10.0 dB. `python-audio-separator` (MIT, actively maintained, release 0.47.0 in Aug 2026) is the easiest Python wrapper for all of them. Demucs is only "officially maintained" in Défossez's fork; the Meta repo is archived. On CPU, Demucs is documented at about 1.5× the track duration, so a 2-minute clip takes about 3 minutes with htdemucs, and htdemucs_ft is "4 times more time". No published CPU timing exists for RoFormer models. They are known to be heavy on CPU.

Spleeter cannot install on Python ≥3.12. Open-Unmix's default weights and Facebook Denoiser are non-commercial. Speech-enhancement models (DeepFilterNet, Resemble Enhance, ClearerVoice) are noise suppressors rather than music separators. They are fast; DeepFilterNet runs at RTF 0.05–0.19 on a single core.

### Cited Findings

**Demucs (Meta, archived) — https://github.com/facebookresearch/demucs**
- 10,372 stars. **ARCHIVED** (archived=true), last push 2024-04-24, MIT. — [GitHub](https://github.com/facebookresearch/demucs)
- The README says: "As I am no longer working at Meta, **this repository is not maintained anymore**. I've created a fork at github.com/adefossez/demucs… only important bug fixes will be processed on the new repo." — [README](https://raw.githubusercontent.com/facebookresearch/demucs/main/README.md)

**Demucs (maintained fork) — https://github.com/adefossez/demucs**
- 3,340 stars. Last push 2026-08-31, MIT. The README calls it "the officially maintained Demucs", but adds "I'm not actively working on Demucs anymore, so expect slow replies and no new feature". — [README](https://raw.githubusercontent.com/adefossez/demucs/main/README.md)
- News entry: "11/07/2026: Released Demucs v4.1.0 with modernized packaging, lighter inference dependencies, numerous fixes, and pretrained models hosted on Hugging Face." The PyPI `demucs` 4.1.0 package was uploaded 2026-07-11 and requires Python ≥3.10. — [README](https://raw.githubusercontent.com/adefossez/demucs/main/README.md), [PyPI](https://pypi.org/project/demucs/)
- Model list:
  - `htdemucs` is the default.
  - `htdemucs_ft` is "fine-tuned… separation will take 4 times more time but might be a bit better".
  - Also listed: `htdemucs_6s`, `hdemucs_mmi`, and the quantized `mdx_q`/`mdx_extra_q`.
  - Hybrid Transformer models support a maximum segment of 7.8 s.

  — [README](https://raw.githubusercontent.com/adefossez/demucs/main/README.md)
- CPU speed: "simply add `-d cpu`… With Demucs, processing time should be roughly equal to 1.5 times the duration of the track." — [README](https://raw.githubusercontent.com/adefossez/demucs/main/README.md)
- Quality: the paper's htdemucs gets 9.00 dB overall SDR on MUSDB HQ, and 9.20 dB with sparse attention and fine-tuning. — [README](https://raw.githubusercontent.com/adefossez/demucs/main/README.md). Per-stem vocal SDR as listed by audio-separator: htdemucs_ft 10.8, hdemucs_mmi 10.3, htdemucs 10.0, htdemucs_6s 9.7. — [audio-separator README](https://raw.githubusercontent.com/nomadkaraoke/python-audio-separator/main/README.md)
- Model size: converted to ggml f16, each 4-source htdemucs model is 81 MB, so htdemucs_ft is 4 × 81 MB. htdemucs_6s is 53 MB and hdemucs_mmi is 160 MB. — [demucs.cpp README](https://raw.githubusercontent.com/sevagh/demucs.cpp/main/README.md)

**demucs.cpp — https://github.com/sevagh/demucs.cpp**
- 178 stars, last push 2024-12-01, MIT. It is a C++17 port using Eigen and ggml that supports htdemucs, htdemucs_6s, htdemucs_ft and hdemucs_mmi, and it is "designed for low-memory environments by sacrificing the speed of the Torch implementation". — [README](https://raw.githubusercontent.com/sevagh/demucs.cpp/main/README.md)
- CPU timings for a 4-minute song on a Ryzen 5950X (16 cores):
  - Single-model program: 10m23s.
  - Multi-threaded program (4 std::threads × 4 OMP threads): 4m09s.
  - v3 `hdemucs_mmi` multi-threaded: 2m35s.

  — [PERFORMANCE.md](https://raw.githubusercontent.com/sevagh/demucs.cpp/main/.github/PERFORMANCE.md)

**python-audio-separator — https://github.com/nomadkaraoke/python-audio-separator**
- 1,416 stars, last push 2026-10-01, MIT. PyPI `audio-separator` 0.47.0 was uploaded 2026-08-27 and requires Python ≥3.10 and !=3.14.1. — [GitHub](https://github.com/nomadkaraoke/python-audio-separator), [PyPI](https://pypi.org/project/audio-separator/)
- It wraps the UVR model families: MDX-Net (`.onnx`), VR Arch, Demucs, and MDXC/RoFormer (`.ckpt`). The CPU install is `pip install "audio-separator[cpu]"`. Docker images exist for CPU on amd64 and arm64. FFmpeg is required. — [README](https://raw.githubusercontent.com/nomadkaraoke/python-audio-separator/main/README.md)
- Top vocal models in the README's `--list_filter=vocals` table:

  | Model file | Vocal SDR | Notes |
  |---|---|---|
  | `model_bs_roformer_ep_317_sdr_12.9755.ckpt` (BS-Roformer-Viperx-1297) | 12.9 | instrumental 17.0 |
  | `vocals_mel_band_roformer.ckpt` (MelBand Roformer by Kimberley Jensen) | 12.6 | |
  | `melband_roformer_big_beta4.ckpt` | 12.5 | |
  | `mel_band_roformer_kim_ft_unwa.ckpt` | 12.4 | |

  — [README](https://raw.githubusercontent.com/nomadkaraoke/python-audio-separator/main/README.md)
- Python API:
  ```python
  from audio_separator.separator import Separator
  separator.load_model(model_filename='model_bs_roformer_ep_317_sdr_12.9755.ckpt')
  separator.separate('audio.wav')
  ```
  — [README](https://raw.githubusercontent.com/nomadkaraoke/python-audio-separator/main/README.md)
- Other features:
  - Ensemble presets: `vocal_balanced` (avg_fft), `vocal_clean` ("minimal instrument bleed", min_fft), `vocal_full`, `karaoke`.
  - `--chunk_duration` handles long files.
  - RoFormer models run on CPU in fp32 or autocast, and optional `torch.compile` is supported on CPU.

  — [README](https://raw.githubusercontent.com/nomadkaraoke/python-audio-separator/main/README.md)
- The README publishes no CPU speed numbers. A third-party Replicate wrapper of MDX-Net quotes "3-minute song: 15-30 seconds (GPU)" against "2-5 minutes (CPU)". — [Replicate readme](https://replicate.com/gianpaj/audio_separator/readme)

**Ultimate Vocal Remover GUI — https://github.com/Anjok07/ultimatevocalremovergui**
- 26,609 stars, last push 2026-10-06, MIT. It is a desktop GUI and the origin of the MDX/VR model zoo that audio-separator uses. It is not suited to a headless pipeline. — [GitHub](https://github.com/Anjok07/ultimatevocalremovergui)

**Training and inference code for the RoFormer models**
- **Music-Source-Separation-Training** — https://github.com/ZFTurbo/Music-Source-Separation-Training. 1,577 stars, last push 2026-10-14, MIT. It holds the training and inference code used by the community RoFormer models. — [GitHub](https://github.com/ZFTurbo/Music-Source-Separation-Training)
- **BS-RoFormer** — https://github.com/lucidrains/BS-RoFormer. 981 stars, last push 2026-06-14, MIT. It is an architecture implementation of Band-Split RoFormer. — [GitHub](https://github.com/lucidrains/BS-RoFormer)

**Mel-Band-Roformer-Vocal-Model (Kim) — https://github.com/KimberleyJensen/Mel-Band-Roformer-Vocal-Model**
- 425 stars, last push 2025-01-12. **GitHub reports no license**, which is a legal ambiguity for commercial use. — [GitHub](https://github.com/KimberleyJensen/Mel-Band-Roformer-Vocal-Model)
- The default `chunk_size` is 352800 samples, which is 8 s. Raising `num_overlap` (up to 8) reduces artifacts but makes "inference times longer". — [README](https://raw.githubusercontent.com/KimberleyJensen/Mel-Band-Roformer-Vocal-Model/main/README.md)
- An issue reports that the model is optimised for GPU. CPU-only users see "high CPU usage and suboptimal latency", and the issue asks for ONNX or TorchScript export. — [issue mirror](https://forgejo.us2.navan.dev/github/Mel-Band-Roformer-Vocal-Model/issues/3)

**melband-roformer-infer — https://github.com/openmirlab/melband-roformer-infer**
- 19 stars. An inference-only package with torch or mlx backends and an explicit `cpu` device option. — [GitHub](https://github.com/openmirlab/melband-roformer-infer), [search summary](https://github.com/openmirlab/melband-roformer-infer)

**Spleeter — https://github.com/deezer/spleeter**
- 28,485 stars, last push 2026-06-18, MIT. PyPI 2.4.2 was uploaded 2025-04-03 and **requires Python <3.12**, so it is incompatible with a Python 3.12/3.13 engine. It is TensorFlow-based. — [PyPI](https://pypi.org/project/spleeter/), [README](https://raw.githubusercontent.com/deezer/spleeter/master/README.md)
- Its 4-stem separation runs "100x faster than real-time when run on a GPU". The README also promotes the commercial "Spleeter Pro". — [README](https://raw.githubusercontent.com/deezer/spleeter/master/README.md)
- Overall SDR is 5.9, compared with 7.7–9.0 for Demucs v3/v4. — [Demucs README table](https://raw.githubusercontent.com/adefossez/demucs/main/README.md)

**Open-Unmix — https://github.com/sigsep/open-unmix-pytorch**
- 1,515 stars, last push 2024-06-17. The code is MIT. PyPI `openunmix` 1.3.0 dates from 2024-04-16. — [GitHub](https://github.com/sigsep/open-unmix-pytorch), [PyPI](https://pypi.org/project/openunmix/)
- **The default `umxl` weights are "only licensed for non-commercial use (CC BY-NC-SA 4.0)".** `umxhq` is trained on MUSDB18-HQ. — [README](https://raw.githubusercontent.com/sigsep/open-unmix-pytorch/master/README.md)
- Overall SDR is 5.3 for the original UMX. — [Demucs README table](https://raw.githubusercontent.com/adefossez/demucs/main/README.md)

**DeepFilterNet — https://github.com/Rikorose/DeepFilterNet**
- 4,820 stars. Last push 2024-10-17, so it has been inactive for about 2 years. Dual MIT/Apache-2.0 license. PyPI `deepfilternet` 0.5.6 dates from 2023-08-31. — [GitHub](https://github.com/Rikorose/DeepFilterNet), [LICENSE](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/LICENSE), [PyPI](https://pypi.org/project/deepfilternet/)
- It does full-band (48 kHz) speech enhancement. A prebuilt Rust `deep-filter` binary has "no python dependencies", but "only wav files with a sampling rate of 48kHz are supported". A LADSPA plugin is also available. — [README](https://raw.githubusercontent.com/Rikorose/DeepFilterNet/main/README.md)
- The paper reports an RTF of 0.19 on a single-threaded notebook CPU. — [arXiv 2305.08227](https://arxiv.org/abs/2305.08227v1)
- A 2026 third-party review measured DFN3 processing 10 minutes of audio in 27.34 s on one pinned core, an RTF of about 0.045. It also found DFN3 costs about 7–11× the CPU of RNNoise and did not get faster with more cores. — [creativeainews review](https://www.creativeainews.com/articles/deepfilternet-vs-rnnoise-vs-ffmpeg-noise-removal-2026/)

**Resemble Enhance — https://github.com/resemble-ai/resemble-enhance**
- 2,456 stars, last push 2024-12-03, MIT. PyPI 0.0.1 dates from 2023-12-14. — [GitHub](https://github.com/resemble-ai/resemble-enhance), [PyPI](https://pypi.org/project/resemble-enhance/)
- It pairs a denoiser with an enhancer that does bandwidth extension and distortion restoration, trained on 44.1 kHz speech. — [README](https://raw.githubusercontent.com/resemble-ai/resemble-enhance/main/README.md)

**Facebook Denoiser — https://github.com/facebookresearch/denoiser**
- 1,899 stars. **ARCHIVED**, last push 2023-03-14. **License: CC BY-NC 4.0 (non-commercial).** — [GitHub](https://github.com/facebookresearch/denoiser), [LICENSE](https://raw.githubusercontent.com/facebookresearch/denoiser/main/LICENSE)
- It is a causal model that "runs in real-time on a laptop CPU" (tested on a 2 GHz quad-core i5), with dns48, dns64 and master64 models. — [README](https://raw.githubusercontent.com/facebookresearch/denoiser/main/README.md)

**ClearerVoice-Studio — https://github.com/modelscope/ClearerVoice-Studio**
- 4,549 stars, last push 2025-08-14, Apache-2.0. — [GitHub](https://github.com/modelscope/ClearerVoice-Studio)
- Capabilities:
  - Speech enhancement at 16 and 48 kHz, using the FRCRN and MossFormer models.
  - Speech separation at 8 and 16 kHz, super-resolution, and target-speaker extraction.
  - Install with `pip install clearvoice`.
  - A NumPy-in/NumPy-out interface was added in 2025.6.

  — [README](https://raw.githubusercontent.com/modelscope/ClearerVoice-Studio/main/README.md)

**sherpa-onnx — https://github.com/k2-fsa/sherpa-onnx**
- 15,272 stars, last push 2026-10-14, Apache-2.0. It provides STT, VAD, speech enhancement and source separation on onnxruntime with no internet connection. — [GitHub](https://github.com/k2-fsa/sherpa-onnx)

**Does separating vocals help Whisper?** The evidence is mixed and comes from sung lyrics, not shouted speech.
- Jam-ALT found that feeding isolated vocals (+demucs) to Whisper "tends to substantially degrade the results", with large-v2 on English as the exception. — [arXiv 2408.06370](https://arxiv.org/pdf/2408.06370)
- A 2025 study found that using separation as a *vocal-activity detector* for segment boundaries consistently reduced WER compared with Whisper's native long-form decoding. On MUSDB-ALT, WER went from 23.59% (mix) to 20.00% with the mdx_extra separator, and separator quality was the deciding variable. — [arXiv 2506.15514](https://arxiv.org/html/2506.15514v1)

### Inferences
- **Best voice/game split:** a MelBand-RoFormer (Kim) or BS-RoFormer vocal model through `audio-separator`. These lead on vocal SDR by about 2 dB over htdemucs_ft. SDR is measured on sung music; there is no benchmark for shouting over slot-game music. Game music is mostly synthetic and instrumental, which should favour vocal-versus-rest models. That is untested.
- **Estimated CPU time for a 2-minute clip:**
  - htdemucs: about 3 min (1.5 × 120 s).
  - htdemucs_ft: about 12 min (4× that).
  - RoFormer: probably as slow as or slower than htdemucs. No number was found.

  On a 4-vCPU cloud box these could be slower still. Run separation only on the 10–40 s window that is actually used in the edit, not on the whole VOD, and cache the stems.
- **Light alternative that keeps the current ducking design:** skip separation. Detect Dylan's speech regions with Silero VAD on the mix (see Q3), then key ffmpeg `sidechaincompress` (see Q4) or the voice-band compressor from those regions. This costs well under 1 s per 2 minutes.
- **Speech enhancers** (DeepFilterNet, Denoiser, Resemble, ClearerVoice) are trained to remove noise, not music. They are fast enough to use as a post-cleaning pass on an already-separated vocal stem, for example DeepFilterNet's `deep-filter` binary on a 48 kHz stem. They should not be the primary separator. Avoid Denoiser and Open-Unmix `umxl` if the edits are monetised, because both are non-commercial.
- **Integration difficulty:**
  - audio-separator: low. It is pip-installable, takes file paths, and writes WAVs that numpy can load.
  - Demucs 4.1: low (`demucs.api` / CLI).
  - demucs.cpp: medium (C++ build, then a subprocess).
  - Spleeter: blocked on Python ≥3.12.

  All of them need torch, except ONNX MDX models run through onnxruntime, demucs.cpp, and DeepFilterNet's Rust binary.

### Gaps
- No published CPU wall-clock figure was found for BS-RoFormer or MelBand-RoFormer inference per minute of audio.
- No benchmark covers separating *shouted speech* from *game music/SFX*. All SDRs are MUSDB-style singing.
- RoFormer checkpoint file sizes (`.ckpt`) could not be verified because huggingface.co was blocked for both fetch tools.
- A local CPU benchmark of Demucs and RoFormer could not run: download.pytorch.org and the Hugging Face model hosts were blocked in this container.

## Q2. Beat, downbeat and drop/section detection (librosa, madmom, BeatNet, beat_this, All-In-One, essentia, drop detectors)

### Takeaway
No mature open-source project detects "the drop" directly. Every drop-detector repo found has 0–21 stars. The practical path is:
1. Get beats and downbeats from **beat_this** (MIT code and weights, CPU fallback, 8 MB "small" model) or **librosa** (no model).
2. Score candidate downbeats with a bass-energy/RMS/onset "impact" heuristic.
3. Optionally use structure models (All-In-One, SongFormer) for section boundaries. Both are GPU-oriented and heavy, and All-In-One is unmaintained.

madmom's PyPI release dates from 2018 and its *models* are CC BY-NC-SA (non-commercial). Essentia is AGPL-3.0.

### Cited Findings

**librosa — https://github.com/librosa/librosa**
- 8,678 stars, last push 2026-10-06, ISC. **librosa 1.0.0 was released on PyPI 2026-08-11 and requires Python ≥3.12.** — [GitHub](https://github.com/librosa/librosa), [PyPI](https://pypi.org/project/librosa/)
- Measured in this container (4 vCPU Xeon 2.8 GHz, librosa 1.0.0, a synthetic 120 s 120-BPM bed with speech):

  | Step | Time |
  |---|---|
  | `librosa.load` with resample to 22.05 kHz | 0.91 s |
  | `beat.beat_track`, first call (numba JIT) | 14.1 s |
  | `beat.beat_track`, warm | 0.64 s |
  | STFT plus bass-band, RMS and onset envelopes | 0.22 s |

  Detected tempo was 117.5 BPM against the true 120. — *own measurement (scratchpad script `lbbench.py`), not externally published*

**madmom — https://github.com/CPJKU/madmom**
- 1,726 stars, last push 2026-03-20. **The source code is BSD, but "all model and data files are distributed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 license".** — [README](https://raw.githubusercontent.com/CPJKU/madmom/main/README.rst)
- PyPI is still at **0.16.1 (2018)**, and CHANGES.rst lists 0.17.dev0 as unreleased. — [PyPI](https://pypi.org/project/madmom/), [CHANGES](https://raw.githubusercontent.com/CPJKU/madmom/main/CHANGES.rst)
- The beat_this README says madmom must be installed "with `pip install git+https://github.com/CPJKU/madmom.git`, as the current version on PyPI only supports Python<3.10 and numpy<1.20". — [beat_this README](https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md)
- Reported breakages include removed numpy aliases (`np.float`) and "numpy.ndarray size changed" binary-incompatibility errors. — [madmom issue mirror #478](https://git.tdem.in/CPJKU/madmom/issues/478), [#527](https://git.tdem.in/CPJKU/madmom/issues/527)

**beat_this (CPJKU, ISMIR 2024) — https://github.com/CPJKU/beat_this**
- 421 stars, last push 2026-05-28. **MIT for both code and published weights**, with a caveat that some training data is copyrighted. PyPI `beat-this` 1.1.0 was uploaded 2026-04-14. — [GitHub](https://github.com/CPJKU/beat_this), [README](https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md), [PyPI](https://pypi.org/project/beat-this/)
- Models: `final0..2` are about 78 MB each; `small0..2` are about 8.1 MB each. It falls back to CPU automatically, and `--gpu=-1` forces CPU. — [README](https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md)
- API: `File2Beats(checkpoint_path="final0", device=..., dbn=False)` returns `beats, downbeats`. `Audio2Beats` accepts an in-memory tensor plus sample rate. No DBN is needed; the optional `--dbn` pulls in madmom. — [README](https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md)
- The weights download from cloud.cp.jku.at, which was blocked in this container. — [README](https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md) plus own proxy check

**BeatNet — https://github.com/mjhydri/BeatNet**
- 523 stars, last push 2026-04-13. **CC BY 4.0** (attribution; commercial use allowed). PyPI 1.1.3 dates from 2023-11-28. — [GitHub](https://github.com/mjhydri/BeatNet), [LICENSE](https://raw.githubusercontent.com/mjhydri/BeatNet/main/LICENSE), [PyPI](https://pypi.org/project/BeatNet/)
- It does joint beat, downbeat, tempo and meter tracking in stream, realtime, online and offline modes. Offline mode uses madmom's DBN, so it inherits madmom's install problems. — [README](https://raw.githubusercontent.com/mjhydri/BeatNet/main/README.md)

**All-In-One (mir-aidj) — https://github.com/mir-aidj/all-in-one**
- 860 stars, MIT. **Last push 2024-05-09, so it has been inactive for about 2.5 years.** PyPI `allin1` 1.1.0 dates from 2023-10-10, and its classifiers stop at Python 3.11. — [GitHub](https://github.com/mir-aidj/all-in-one), [PyPI](https://pypi.org/project/allin1/), [pyproject](https://raw.githubusercontent.com/mir-aidj/all-in-one/main/pyproject.toml)
- It predicts tempo, beats, downbeats, segment boundaries and labels (intro, verse, chorus, bridge, outro). It requires NATTEN built manually on Linux, madmom from git, and Demucs (it separates sources first). — [README](https://raw.githubusercontent.com/mir-aidj/all-in-one/main/README.md)
- Speed: "With an RTX 4090 GPU and Intel i9-10940X CPU… processed 10 songs (33 minutes) in 73 seconds". No CPU-only figure is given. — [README](https://raw.githubusercontent.com/mir-aidj/all-in-one/main/README.md)

**SongFormer (ASLP-lab, 2025) — https://github.com/ASLP-lab/SongFormer**
- 179 stars. The repo was created 2025-09 and updated 2026-10. **LICENSE file: CC BY 4.0.** — [GitHub](https://github.com/ASLP-lab/SongFormer), [LICENSE](https://raw.githubusercontent.com/ASLP-lab/SongFormer/main/LICENSE)
- Labels: intro, verse, chorus, bridge, inst, outro, silence and pre-chorus. There is no "drop" label. — [README](https://raw.githubusercontent.com/ASLP-lab/SongFormer/main/README.md)
- Speed: "2-4 seconds" per song on an NVIDIA L40 GPU, against 9–12 s for All-In-One. It uses the MuQ and MusicFM SSL encoders, and its scripts assume CUDA. — [README](https://raw.githubusercontent.com/ASLP-lab/SongFormer/main/README.md), [arXiv 2510.02797](https://arxiv.org/html/2510.02797v2)

**msaf — https://github.com/urinieto/msaf**
- 560 stars, updated 2026-09. It is a classic Music Structure Analysis Framework (boundary and label algorithms, no deep model). — [GitHub](https://github.com/urinieto/msaf)

**Essentia — https://github.com/MTG/essentia**
- 3,772 stars, last push 2026-10-14. **AGPL-3.0, a strong copyleft licence that can affect a networked service.** — [GitHub](https://github.com/MTG/essentia)
- The latest PyPI dev build (2.1b6.dev1438, 2026-05-19) lists only cp314 wheels. — [PyPI](https://pypi.org/project/essentia/)

**Drop-detection repos.** All are tiny or new; treat them as reference code, not dependencies.
- **emjjkk/beat-detection** — https://github.com/emjjkk/beat-detection. 21 stars, created 2025-12. Its Essentia script does "beat, drop, and transient detection" with loudness filtering and onset snapping. A librosa script covers beats and onsets. It exports EDL markers for Resolve and Premiere. — [GitHub](https://github.com/emjjkk/beat-detection), [README](https://raw.githubusercontent.com/emjjkk/beat-detection/main/README.md)
- **hPerezz/here-comes-the-drop** — https://github.com/hPerezz/here-comes-the-drop. 0 stars. It extracts RMS energy, bass RMS, spectral centroid, spectral flux and onset strength. From these it computes a "Tension Score" for build-ups and an "Impact Score" for sudden energy releases. It has a Streamlit UI and optional ML. — [README](https://raw.githubusercontent.com/hPerezz/here-comes-the-drop/main/README.md)
- **atigun64/dropsync-music-aligner** — 2 stars. "AI-assisted drop detection and timeline alignment for video editing workflows." **Sc4rville/tsunami** — 0 stars, MIT. "numpy drop detection, one generated ffmpeg filter graph per video". — [GitHub search](https://github.com/atigun64/dropsync-music-aligner), [tsunami](https://github.com/Sc4rville/tsunami)
- **FastLED DropDetector (C++)** is a design reference. It combines energy flux, bass energy surge and spectral novelty. — [FastLED docs](https://fastled.io/docs/db/d79/drop_8h_source.html)

### Inferences
- **Recommended drop finder.** This replaces the hand-picked RMS approach and needs nothing beyond numpy and librosa.
  1. Compute beats and downbeats with beat_this `small0` (8 MB, MIT) or librosa `beat_track`.
  2. Compute frame envelopes: bass-band (<150 Hz) energy, full-band RMS and onset strength.
  3. Score each downbeat as the jump in bass energy and RMS from the preceding 2–8 bars (the build/breakdown) to the following 1–2 bars.
  4. Pick the highest-scoring downbeat after the first ~15 s.

  EDM and trap drops are characterised by the kick and sub returning after a filtered or bass-less build. Aligning the reveal frame to a downbeat also keeps cuts on-grid. A cheap human check is still needed; flag low-confidence picks.
- Structure models (All-In-One, SongFormer) output chorus/inst boundaries, which in EDM often coincide with drops. On a CPU-only box they are not worth it: GPU-tuned, heavy encoders, and NATTEN/madmom install friction for All-In-One. Song beds are a fixed library, so drops can also be computed once per song and cached in a JSON sidecar. That makes even slow models acceptable offline.
- **License hygiene:** avoid madmom's bundled models (NC). This also covers BeatNet offline/DBN and beat_this `--dbn`. Avoid Essentia (AGPL) if the engine is ever distributed or served.
- **Integration difficulty:**
  - librosa: trivial (numpy arrays in and out).
  - beat_this: low, but needs torch and staged weights.
  - BeatNet: medium (madmom dependency).
  - All-In-One: high.
  - SongFormer: high.

### Gaps
- No public benchmark or labelled dataset for EDM "drop" detection accuracy was found.
- No CPU timing was found for beat_this or All-In-One. It could not be measured here because torch and the JKU weight hosts were blocked.
- msaf's license and Python 3.13 compatibility were not checked.

## Q3. Transcription with word timestamps on CPU (faster-whisper, whisper.cpp, WhisperX, distil-whisper, Moonshine, others)

### Takeaway
For CPU with word timestamps, **faster-whisper** with `small.en`/`distil-small.en` int8, `word_timestamps=True` and `vad_filter=True` is the default choice. Its official CPU benchmark runs about 7.6× real-time for the small model, and about 15× with batching (8 threads, i7-12700K). That suggests roughly 8–16 s for a 2-minute clip on a fast desktop, and likely 2–3× longer on 4 cloud vCPUs.

whisper.cpp is equally fast and lighter, but its word timestamps are "experimental". WhisperX gives the most accurate word boundaries through wav2vec2 alignment, but it is heavier (torch). **onnx-asr** (Parakeet, numpy plus onnxruntime only, RTFx 36 on a desktop CPU) and **Moonshine** (MIT, `word_timestamps` option) are torch-free, fast alternatives. **Silero VAD** gives clean cut points at under 1 ms per chunk. stable-ts is archived and whisper-timestamped is AGPL.

Shouting over loud music is a known weak spot. Disable `condition_on_previous_text` and use VAD-based segmentation.

### Cited Findings

**faster-whisper — https://github.com/SYSTRAN/faster-whisper**
- 25,856 stars, last push 2026-10-13, MIT. PyPI 1.2.1 dates from 2025-10-31. — [GitHub](https://github.com/SYSTRAN/faster-whisper), [PyPI](https://pypi.org/project/faster-whisper/)
- Official CPU benchmark: **13 minutes** of audio, **small** model, beam 5, 8 threads on an i7-12700K.

  | Implementation | Time | RAM |
  |---|---|---|
  | openai/whisper fp32 | 6m58s | 2335 MB |
  | whisper.cpp fp32 | 2m05s | 1049 MB |
  | whisper.cpp + OpenVINO | 1m45s | — |
  | faster-whisper fp32 | 2m37s | — |
  | faster-whisper int8 | 1m42s | 1477 MB |
  | faster-whisper int8 batch_size=8 | 51s | 3608 MB |

  — [README](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/README.md)
- Features:
  - `model.transcribe(..., word_timestamps=True)`.
  - `vad_filter=True` uses Silero VAD and by default only removes silence longer than 2 s; it is tunable through `vad_parameters`.
  - Supports distil-large-v3 and `turbo`.
  - CTranslate2 models auto-download from Hugging Face.

  — [README](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/README.md)

**whisper.cpp — https://github.com/ggml-org/whisper.cpp**
- 54,373 stars, last push 2026-10-12, MIT. — [GitHub](https://github.com/ggml-org/whisper.cpp)
- Model disk and memory use:

  | Model | Disk | Memory |
  |---|---|---|
  | tiny | 75 MiB | ~273 MB |
  | base | 142 MiB | ~388 MB |
  | small | 466 MiB | ~852 MB |
  | medium | 1.5 GiB | ~2.1 GB |
  | large | 2.9 GiB | ~3.9 GB |

  Quantization (e.g. q5_0) is supported. — [README](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/README.md)
- "Word-level timestamp (experimental)" via `-ml 1`. A `--vad` option uses Silero-VAD to pass only speech segments to Whisper. — [README](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/README.md)
- The Python binding `pywhispercpp` 1.5.1 dates from 2026-08-22. — [PyPI](https://pypi.org/project/pywhispercpp/)

**WhisperX — https://github.com/m-bain/whisperX**
- 24,541 stars, last push 2026-09-26, BSD-2-Clause. PyPI 3.8.6 dates from 2026-05-25 and requires Python ≥3.10 and <3.14. — [GitHub](https://github.com/m-bain/whisperX), [PyPI](https://pypi.org/project/whisperx/)
- "70x realtime with large-v2" applies to batched inference on GPU. It gives "Accurate word-level timestamps using wav2vec2 alignment" plus VAD preprocessing. CPU usage: `whisperx audio.wav --compute_type int8 --device cpu`. In 2026 it added context-aware batching. — [README](https://raw.githubusercontent.com/m-bain/whisperX/main/README.md)
- Limitations:
  - Words whose characters are missing from the alignment model's dictionary, such as "2014." or "£13.60", "cannot be aligned and therefore are not given a timing".
  - "Overlapping speech is not handled particularly well".

  — [README](https://raw.githubusercontent.com/m-bain/whisperX/main/README.md)

**distil-whisper — https://github.com/huggingface/distil-whisper**
- 4,118 stars, MIT. Last push 2025-01-08, so it is little-maintained. — [GitHub](https://github.com/huggingface/distil-whisper)
- It is English-only: "6 times faster, 49% smaller… within 1% WER". `distil-small.en` has 166M parameters and runs "within 4% WER of Whisper large-v3". The README points to Whisper turbo for multilingual use. It runs inside faster-whisper. — [README](https://raw.githubusercontent.com/huggingface/distil-whisper/main/README.md), [faster-whisper README](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/README.md)

**Moonshine Voice — https://github.com/moonshine-ai/moonshine**
- 11,225 stars, last push 2026-10-02. The code is MIT, and models are "MIT by default… the only exceptions are the legacy non-streaming models for languages other than English", which are under the non-commercial Moonshine Community License. — [LICENSE](https://raw.githubusercontent.com/moonshine-ai/moonshine/main/LICENSE), [README](https://raw.githubusercontent.com/moonshine-ai/moonshine/main/README.md)
- Install with `pip install moonshine-voice` (0.1.5, 2026-08-24). Its claim: models "from higher accuracy than Whisper Large V3 down to tiny 1MB models". Everything runs on-device. — [README](https://raw.githubusercontent.com/moonshine-ai/moonshine/main/README.md), [PyPI](https://pypi.org/project/moonshine-voice/)
- Option `word_timestamps` (default false): "Fill each line's `words` array. Needs the attention decoder asset." — [options doc](https://raw.githubusercontent.com/moonshine-ai/moonshine/main/docs/api/options.md)

**onnx-asr — https://github.com/istupakov/onnx-asr**
- 383 stars, last push 2026-10-09, MIT. It needs only numpy and onnxruntime (no torch), supports Python 3.10–3.14 and numpy 1.22–2.4+, and accepts WAV files or numpy arrays. — [README](https://raw.githubusercontent.com/istupakov/onnx-asr/main/README.md)
- Models: Parakeet v2 (English) and v3 (multilingual), Canary, GigaAM and Whisper. It returns "token-level timestamps". The maximum is 20–30 s per call, so VAD is needed for long audio. — [README](https://raw.githubusercontent.com/istupakov/onnx-asr/main/README.md)
- Speed (RTFx) on a Ryzen 9800X3D CPU: Parakeet v2/v3 36, Canary v2 8, GigaAM v3 CTC 59. — [README](https://raw.githubusercontent.com/istupakov/onnx-asr/main/README.md)

**Silero VAD — https://github.com/snakers4/silero-vad**
- 10,435 stars, last push 2026-09-29, MIT. PyPI 6.2.3 dates from 2026-09-23, and an `onnx-cpu` extra needs only onnxruntime and numpy. — [GitHub](https://github.com/snakers4/silero-vad), [README](https://raw.githubusercontent.com/snakers4/silero-vad/master/README.md)
- "One audio chunk (30+ ms) takes less than 1ms to be processed on a single CPU thread". The JIT model is "around two megabytes". — [README](https://raw.githubusercontent.com/snakers4/silero-vad/master/README.md)

**Other repos**
- **stable-ts** — https://github.com/jianfch/stable-ts. 2,282 stars. **ARCHIVED**: "Development on this repository is indefinitely paused." PyPI 2.19.1 dates from 2025-08-16. — [README](https://raw.githubusercontent.com/jianfch/stable-ts/main/README.md), [PyPI](https://pypi.org/project/stable-ts/)
- **whisper-timestamped** — https://github.com/linto-ai/whisper-timestamped. 2,855 stars, last push 2026-09-28. **AGPL-3.0 (copyleft).** — [GitHub](https://github.com/linto-ai/whisper-timestamped)
- **openai/whisper** — 110,511 stars, last push 2026-08-31, MIT. It is the reference implementation and the slowest on CPU, at 6m58s for 13 min with the small model. — [GitHub](https://github.com/openai/whisper), [faster-whisper benchmark](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/README.md)

**Whisper with loud music**
- A small, non-peer-reviewed 2026 benchmark reports that `condition_on_previous_text=True` is "catastrophic for music" (+28 WER points), and that Demucs vocal separation helped large-v3 by −2.2 WER points on average. — [lyrics-bench paper](https://lyrics-bench.onrender.com/papers/paper.html)
- Contradicting evidence: Jam-ALT found that separated vocals degraded most Whisper models. — [arXiv 2408.06370](https://arxiv.org/pdf/2408.06370)

### Inferences
- **For the hype pipeline:**
  1. Run Silero VAD (ONNX, about 2 MB, bundled in the wheel, so no Hugging Face fetch is needed) on the clip to get speech islands. Use these as "do not cut inside" zones.
  2. Run faster-whisper `small.en` or `distil-small.en` with int8, `word_timestamps=True`, `condition_on_previous_text=False` and `language="en"` on those islands to find "let's go", "no way" and similar.

  Scaling the official benchmark (13 min in 1m42s, int8, 8 threads) gives roughly 15–20 s per 2-minute clip on a fast 8-thread desktop. A 4-vCPU cloud Xeon is likely 2–3× slower, though this was not measured because the Hugging Face block prevented downloading the models.
- For keyword spotting, small or base models are enough. Hype phrases are short, high-frequency English words. Matching on fuzzy word lists with timestamps is more robust than trusting full sentences.
- **When to use what:**
  - WhisperX: only if word boundaries must be tight, for example to cut exactly between words. It adds a torch wav2vec2 model.
  - onnx-asr Parakeet: the fastest torch-free option, at roughly 3–4 s per 2-minute clip if desktop RTFx 36 carries over at about one-third speed. It gives token rather than word timestamps, so words must be grouped.
- If transcription quality on the raw mix is poor, the literature suggests using the vocal stem from Q1 as a *segmentation/VAD signal* rather than feeding it directly to Whisper.
- **Integration difficulty:**
  - faster-whisper: low (pure pip, no torch, returns Python objects).
  - onnx-asr and Silero ONNX: low (numpy in).
  - pywhispercpp: low to medium.
  - WhisperX: medium (torch, alignment models, version pins).
  - All of them need staged model weights if Hugging Face is blocked in production.

### Gaps
- No published benchmark of Whisper-family models on *shouted speech over game music* was found.
- No CPU benchmark exists in the WhisperX or Moonshine READMEs, and Moonshine model parameter counts were not found in the fetched docs.
- The local faster-whisper benchmark failed because huggingface.co returned 403 through the proxy.

## Q4. Loudness, mixing, sidechain/ducking helpers (pyloudnorm, pedalboard, matchering, ffmpeg)

### Takeaway
**pyloudnorm** (MIT, BS.1770-4) is the right in-Python meter for measuring stems and SFX. It is useful for making "SFX 4 dB above the bed" a true loudness offset instead of a peak or RMS one, and it takes about 0.1 s per 2 minutes. **ffmpeg** already covers ducking (`sidechaincompress`) and final normalisation (`loudnorm`, with a two-pass linear mode for files). **pedalboard** (GPL-3.0) adds fast in-numpy Compressor, Limiter and Gain plus VST3 hosting. **matchering** (GPL-3.0) can tone- and loudness-match a song bed to a reference hype edit. Both are copyleft, so check before distributing the engine.

### Cited Findings

**pyloudnorm — https://github.com/csteinmetz1/pyloudnorm**
- 783 stars, last push 2026-01-04, MIT. PyPI 0.2.0 dates from 2026-01-04. — [GitHub](https://github.com/csteinmetz1/pyloudnorm), [PyPI](https://pypi.org/project/pyloudnorm/)
- It implements ITU-R BS.1770-4 with `pyln.Meter(rate).integrated_loudness(data)`, `pyln.normalize.loudness(...)` and `pyln.normalize.peak(data, -1.0)`, all on numpy arrays. — [README](https://raw.githubusercontent.com/csteinmetz1/pyloudnorm/master/README.md)
- Measured here: integrated loudness of a 120 s, 22.05 kHz clip took 0.10 s. — *own measurement*

**pedalboard (Spotify) — https://github.com/spotify/pedalboard**
- 6,354 stars, last push 2026-10-07. **GPL-3.0.** PyPI 0.9.26 dates from 2026-10-07 and requires Python ≥3.10. — [GitHub](https://github.com/spotify/pedalboard), [PyPI](https://pypi.org/project/pedalboard/)
- Effects include `Compressor`, `Gain` and `Limiter`, plus resampling, MP3/GSM compression and Bitcrush (useful for "glitch" SFX). It hosts VST3 and Audio Unit plugins. — [README](https://raw.githubusercontent.com/spotify/pedalboard/master/README.md)
- It processes audio "up to 300x faster than pySoX" and reads files "up to 4x faster than librosa.load". — [README](https://raw.githubusercontent.com/spotify/pedalboard/master/README.md)

**matchering — https://github.com/sergree/matchering**
- 2,658 stars, last push 2026-10-07. **GPL-3.0.** PyPI 2.0.6 dates from 2022-10-19. — [GitHub](https://github.com/sergree/matchering), [PyPI](https://pypi.org/project/matchering/)
- It gives a TARGET "the same RMS, FR [frequency response], peak amplitude and stereo width as the REFERENCE". It includes its own open-source "Hyrax" brickwall limiter and requires a "4 GB RAM machine". — [README](https://raw.githubusercontent.com/sergree/matchering/master/README.md)

**ffmpeg filters** (from the docs source on GitHub)
- `sidechaincompress`: "acts like normal compressor but has the ability to compress detected signal using second input signal. It needs two input streams… First input stream will be processed depending on second stream signal." Options include threshold, ratio, attack, release, makeup and mode (downward or upward). — [FFmpeg doc/filters.texi](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/doc/filters.texi)
- `loudnorm`: "EBU R128 loudness normalization. Includes both dynamic and linear normalization modes. Support for both single pass… and double pass (files) modes… In dynamic mode, to accurately detect true peaks, the audio stream will be upsampled to 192 kHz. Use the `-ar` option or aresample filter to explicitly set an output sample rate." — [FFmpeg doc/filters.texi](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/doc/filters.texi)

### Inferences
- **Ducking:** feed the game/music bed as input 1 and a voice key as input 2 to `sidechaincompress`. The voice key can be the separated vocal stem, or the mix gated by Silero VAD speech regions. This replaces hand-rolled voice-band ducking with a standard, tunable filter.
- **The current "duck his voice under the slot" logic** is the reverse direction. To duck voice under big slot hits, key the voice track from the separated game stem instead.
- **SFX levelling:** measure the bed's short-term loudness with pyloudnorm over the SFX window, then set the SFX gain to (bed LUFS + 4 dB). Raw RMS over-weights bass-heavy impacts.
- **Final loudness:** use two-pass `loudnorm` (measure, then `linear=true` with `measured_*` values). It is more transparent than single-pass dynamic mode for short clips. Add `-ar 48000`, since dynamic mode upsamples to 192 kHz.
- **pedalboard** is worth adding only if numpy-side effects such as compression, limiting or bitcrush glitches are wanted without ffmpeg round-trips. **matchering** fits making phone-recording song beds sound consistent with a "house" reference. Mind GPL-3.0 for both if the engine is distributed.
- **Integration difficulty:** pyloudnorm trivial; ffmpeg filters trivial (already used); pedalboard low; matchering low.

### Gaps
- It was not confirmed whether pedalboard's `Compressor` supports an external sidechain input. The README excerpt lists only Compressor, Gain and Limiter, so assume it does not and use ffmpeg `sidechaincompress`.
- No benchmark compares ffmpeg `loudnorm` single-pass and two-pass results on short (<60 s) social clips.
