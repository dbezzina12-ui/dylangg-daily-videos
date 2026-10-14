# Win detection and OCR: GitHub tools for finding big slot moments in long Kick VODs (CPU-only)

Scope: OCR engines for on-screen numbers, slot/casino and game-stream highlight detectors, audio excitement and scene-change tools, and template-matching or classifier approaches for "big win" banners. Out of scope (covered by other researchers): source separation, beat detection, interpolation, upscaling, tracking, reframing, Kick downloaders, social scheduling.

Method note: star counts, `pushed_at` (last push to any branch, used here as the proxy for "last commit"), archived flag and detected license come from the GitHub REST search API, queried on 2026-10-14. Latest-release dates come from the PyPI JSON API on the same day. In the tables below, the GitHub URL is the source for stars, push date and license, and the PyPI URL is the source for release dates. None of the repos listed are archived (`archived=false` for all). "Inactive 2y+" means the last push was before 2024-10-14.

Several sites (paddleocr.ai, rapidai.github.io, invoicedataextraction.com, tildalice.io) did not resolve from the research sandbox. Figures attributed to them come from search-engine summaries, not from reading the page, and are flagged as such.

---

## 1. Which OCR engines read small UI numbers and stylised game digits best and run fast on CPU?

### Takeaway
For reading a fixed, pre-cropped field ("TOTAL WIN $3,915.60", "BALANCE", "BET") many times per minute on CPU, the best fit is **RapidOCR in recognition-only mode** (`use_det=False`). It runs PaddleOCR's PP-OCR models on ONNX Runtime or OpenVINO, its default is now the PP-OCRv6 model released in June 2026, and it is Apache-2.0. PaddleOCR's own published CPU latency for a mobile recognition model is about 3.6–21 ms per text line. PP-OCRv6 reports large gains on its "Screen", "Industrial" and "Artistic" text categories, which are the closest published proxies for game UI and glowing digits. **Tesseract (via tesserocr) with PSM 7 and a digit whitelist** is the fastest fallback for clean, static fields but is weak on stylised digits. The other options are heavier, older or restricted:
- **EasyOCR** has had no PyPI release since 2024-09.
- **Surya** is now a vision-language model (VLM) that needs a llama.cpp server on CPU, and its weights carry a revenue-limited license.
- **CnOCR's digit-only models** cannot output "." or ",".
- **ddddocr + dddd_trainer** is the easiest path if a custom model for animated popup digits is ever needed.

### Cited Findings

**OCR engine metadata (GitHub API / PyPI, 2026-10-14)**

| Repo | Stars | Last push | License | Latest PyPI release | Source |
|---|---|---|---|---|---|
| PaddlePaddle/PaddleOCR | 91,095 | 2026-09-16 | Apache-2.0 | paddleocr 3.7.0 (2026-06-11); paddlepaddle 3.3.1 (2026-03-26) | [GitHub](https://github.com/PaddlePaddle/PaddleOCR), [PyPI](https://pypi.org/project/paddleocr/) |
| RapidAI/RapidOCR | 8,135 | 2026-10-14 | Apache-2.0 | rapidocr 3.10.0 (2026-10-08) | [GitHub](https://github.com/RapidAI/RapidOCR), [PyPI](https://pypi.org/project/rapidocr/) |
| tesseract-ocr/tesseract | 76,990 | 2026-10-10 | Apache-2.0 | (C++ binary; distro packages) | [GitHub](https://github.com/tesseract-ocr/tesseract) |
| sirfz/tesserocr (Cython wrapper) | 2,177 | 2026-08-04 | MIT | tesserocr 2.11.0 (2026-08-04) | [GitHub](https://github.com/sirfz/tesserocr), [PyPI](https://pypi.org/project/tesserocr/) |
| madmaze/pytesseract (subprocess wrapper) | 6,394 | 2026-10-12 | Apache-2.0 | pytesseract 0.3.13 (2024-08-16) | [GitHub](https://github.com/madmaze/pytesseract), [PyPI](https://pypi.org/project/pytesseract/) |
| JaidedAI/EasyOCR | 30,065 | 2025-12-05 | Apache-2.0 | easyocr 1.7.2 (2024-09-24): no release for 2y+ | [GitHub](https://github.com/JaidedAI/EasyOCR), [PyPI](https://pypi.org/project/easyocr/) |
| mindee/doctr | 6,385 | 2026-10-13 | Apache-2.0 | python-doctr 1.1.0 (2026-08-21) | [GitHub](https://github.com/mindee/doctr), [PyPI](https://pypi.org/project/python-doctr/) |
| felixdittrich92/OnnxTR (docTR on ONNX) | 198 | 2026-10-09 | Apache-2.0 | onnxtr 0.9.0 (2026-08-24) | [GitHub](https://github.com/felixdittrich92/OnnxTR), [PyPI](https://pypi.org/project/onnxtr/) |
| datalab-to/surya | 21,493 | 2026-09-11 | Code Apache-2.0; weights modified OpenRAIL-M | surya-ocr 0.22.1 (2026-07-20) | [GitHub](https://github.com/datalab-to/surya), [PyPI](https://pypi.org/project/surya-ocr/) |
| sml2h3/ddddocr (captcha OCR, ONNX) | 14,834 | 2026-03-10 | MIT | ddddocr 1.6.1 (2026-03-11) | [GitHub](https://github.com/sml2h3/ddddocr), [PyPI](https://pypi.org/project/ddddocr/) |
| sml2h3/dddd_trainer (trainer for ddddocr) | 1,061 | 2025-03-06 | Apache-2.0 | n/a | [GitHub](https://github.com/sml2h3/dddd_trainer) |
| breezedeus/CnOCR | (not returned by GitHub search) | n/a | Apache 2.0 | cnocr 2.3.3 (2026-07-05) | [PyPI](https://pypi.org/project/cnocr/) |
| Topdu/OpenOCR (SVTRv2) | 1,470 | 2026-09-21 | Apache-2.0 | openocr-python 0.1.5 (2026-02-12) | [GitHub](https://github.com/Topdu/OpenOCR), [PyPI](https://pypi.org/project/openocr-python/) |
| jingsongliujing/OnnxOCR | 1,875 | 2026-06-11 | Apache-2.0 | onnxocr 4.0.0 (2026-10-02) | [GitHub](https://github.com/jingsongliujing/OnnxOCR), [PyPI](https://pypi.org/project/onnxocr/) |
| open-mmlab/mmocr | 4,750 | 2024-11-27 (about 1.9y, near-inactive) | Apache-2.0 | n/a | [GitHub](https://github.com/open-mmlab/mmocr) |
| baudm/parseq | 743 | 2024-05-29 (**inactive 2y+**) | Apache-2.0 | n/a | [GitHub](https://github.com/baudm/parseq) |
| clovaai/deep-text-recognition-benchmark | 3,940 | 2024-03-04 (**inactive 2y+**) | Apache-2.0 | n/a | [GitHub](https://github.com/clovaai/deep-text-recognition-benchmark) |
| faustomorales/keras-ocr | 1,473 | 2025-09-22 | MIT | n/a | [GitHub](https://github.com/faustomorales/keras-ocr) |
| Ucas-HaoranWei/GOT-OCR2.0 (VLM OCR) | 8,222 | 2025-02-10 | none detected by GitHub | n/a | [GitHub](https://github.com/Ucas-HaoranWei/GOT-OCR2.0) |

**PaddleOCR / PP-OCR models (recognition-only latency on CPU)**
- PaddleOCR's recognition-module table gives per-line CPU latency (normal mode / high-performance mode):

  | Model | CPU latency (ms) | Size | Accuracy |
  |---|---|---|---|
  | PP-OCRv5_mobile_rec | 21.20 / 5.32 | 16 MB | 81.29% |
  | PP-OCRv5_server_rec | 31.21 / 31.21 | 81 MB | 86.38% |
  | PP-OCRv4_mobile_rec | 17.48 / 3.61 | 10.5 MB | 78.74% |
  | en_PP-OCRv4_mobile_rec | 17.20 / 4.18 | 7.5 MB | 70.39% |
  | en_PP-OCRv5_mobile_rec | (no timing given) | 7.5 MB | 85.25% |

  Test machine: Intel Xeon Gold 6271C @ 2.60 GHz, 8 threads, FP32. High-performance mode uses the best backend (Paddle, OpenVINO or TensorRT). — [PaddleOCR text_recognition doc](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_recognition.en.md)
- The same table lists PP-OCRv6 recognition models with no timing yet. Accuracy figures are on an internal set. — [same doc](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_recognition.en.md)
  - PP-OCRv6_tiny_rec: 4.4 MB, 73.5%
  - PP-OCRv6_small_rec: 20.4 MB, 81.3%
  - PP-OCRv6_medium_rec: 73.3 MB, 83.2%
- PP-OCRv6 shipped in PaddleOCR 3.7.0 on 2026-06-11. It comes in three tiers: tiny (1.5M params), small (7.7M) and medium (34.5M). It claims "major improvements in digital displays, dot-matrix characters, tire prints, and industrial text recognition" and a "5.2× CPU speedup (OpenVINO)". — [PaddleOCR README on PyPI](https://pypi.org/project/paddleocr/)
- PP-OCRv6 recognition accuracy (%) on the categories that best match game UI (Paddle's in-house benchmark). — [PP-OCRv6 technical doc](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv6/PP-OCRv6.en.md)

  | Model | Screen | Industrial | Artistic |
  |---|---|---|---|
  | PP-OCRv6_medium | 82.5 | 77.4 | 71.2 |
  | PP-OCRv6_small | 79.7 | 76.4 | 68.4 |
  | PP-OCRv6_tiny | 71.2 | 62.1 | 54.7 |
  | PP-OCRv5_server | 68.1 | 70.2 | 64.0 |
  | PP-OCRv5_mobile | 57.6 | 59.3 | 54.0 |

- PP-OCRv6 end-to-end speed (detection + recognition, seconds per full image, 200 general/document images) on an Intel Xeon 8350C. — [PP-OCRv6 technical doc](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv6/PP-OCRv6.en.md)

  | Backend | v6 medium | v6 small | v6 tiny | v5 server | v5 mobile |
  |---|---|---|---|---|---|
  | OpenVINO | 1.40 | 0.59 | 0.20 | 7.30 | 0.78 |
  | ONNX Runtime | 3.31 | 0.61 | 0.22 | 6.36 | 0.61 |

**RapidOCR**
- RapidOCR converts PaddleOCR models to ONNX and supports these engines: ONNX Runtime, OpenVINO, MNN, PaddlePaddle, TensorRT and PyTorch. Install with `pip install rapidocr onnxruntime`. Code is Apache-2.0, and the converted models keep PaddleOCR's Apache-2.0 terms. — [RapidOCR README](https://github.com/RapidAI/RapidOCR)
- RapidOCR's current `config.yaml` has `use_det: true`, `use_cls: true`, `use_rec: true` and `text_score: 0.5`. The default detection and recognition models are `ocr_version: "PP-OCRv6"`, `model_type: "small"`, `engine_type: "onnxruntime"`. The default classifier is PP-OCRv4 mobile. — [config.yaml](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/config.yaml)
- RapidOCR's `OCRVersion` enum includes PP-OCRv4, v5 and v6. Its `ModelType` options are mobile, server, tiny, small and medium. — [typings.py](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/utils/typings.py)
- A community blog shows a recognition-only RapidOCR call (`use_det=False, use_cls=False, use_rec=True`) with the recognizer set to PPOCRV5. — [CSDN post, via search summary](https://aicoding.csdn.net/6a68817510ee7a33f2937d77.html)
- Community ONNX conversions of PP-OCRv6 det/rec exist. — [HF cmack64/PP-OCRv6_tiny_rec_onnx](https://huggingface.co/cmack64/PP-OCRv6_tiny_rec_onnx)
- Roboflow's `inference-models` runs PP-OCRv6 as single-line recognition when built with `det_model=None`. — [Roboflow docs, via search summary](https://inference-models.roboflow.com/models/pp-ocrv6/)

**Cross-engine CPU comparisons (secondary sources, single tests)**
- One 2026 test on a single 800x600 invoice, Apple M-series CPU: Tesseract 5.5.2 took 0.162 s, RapidOCR 1.2.3 0.212 s, EasyOCR 1.7.2 0.656 s and PaddleOCR 3.4.0 4.85 s. The PaddleOCR figure came from a separate earlier test. — [invoicedataextraction.com, via search summary; page not directly fetched](https://invoicedataextraction.com/blog/python-ocr-library-comparison-invoices)
- Cold start on CPU: about 4.2 s for PaddleOCR, 2.8 s for EasyOCR and under 0.3 s for Tesseract. — [tildalice.io, via search summary; page not directly fetched](https://tildalice.io/ocr-tesseract-easyocr-paddleocr-benchmark/)
- A deployment-estimate article ranks RapidOCR fastest (about 0.5–1 s per page), which conflicts with the invoice test above. — [search summary of imagetotable.ai / gigagpu comparisons](https://imagetotable.ai/blog/best-open-source-ocr-tools-2026)
- No reproducible multi-engine CPU benchmark on the same dataset was found. — [same search summary](https://www.codesota.com/ocr/best-for-python)

**Tesseract**
- tesserocr releases the GIL while Tesseract runs, so Python threads can OCR several crops concurrently. It also exposes `SetRectangle`, `SetVariable` and PSM/OEM modes. — [tesserocr PyPI README](https://pypi.org/project/tesserocr/)
- A Tesseract issue from the 4.00-alpha era reported that `tessedit_char_whitelist` had no effect with the LSTM-only engine (`--oem 1`) but worked with the legacy engine. — [tesseract issue #998](https://github.com/tesseract-ocr/tesseract/issues/998)
- A forum user fixed number reading with a digit whitelist plus `--psm 7` (single text line). — [AutoIt forum](https://www.autoitscript.com/forum/topic/207435-tesseract-not-picking-up-a-number/)

**EasyOCR**
- `Reader(..., gpu=False)` runs on CPU only. — [EasyOCR README on PyPI](https://pypi.org/project/easyocr/)
- `readtext()` and `recognize()` accept `allowlist` / `blocklist`, which restrict output characters (for example to digits and `.,$x`). — [easyocr.py source](https://github.com/JaidedAI/EasyOCR/blob/master/easyocr/easyocr.py)

**Surya**
- Code is Apache-2.0. Model weights use a modified AI Pubs Open Rail-M license: free for research, personal use and startups under $5M funding/revenue. — [surya-ocr PyPI README](https://pypi.org/project/surya-ocr/)
- Layout, OCR and table recognition now share one VLM served by vllm (NVIDIA GPU) or `llama.cpp` (CPU / Apple Silicon). — [same README](https://pypi.org/project/surya-ocr/)

**CnOCR**
- `number-*` models recognise only the digits 0–9, so they cannot output "." or ",". `ocr_for_single_line()` skips detection and is "more than 2× faster". CPU install is `pip install cnocr[ort-cpu]`. — [cnocr PyPI README](https://pypi.org/project/cnocr/)

**ddddocr**
- A single-line ONNX recogniser for captchas (letters and digits) that defaults to CPU (`use_gpu=False`).
- It can output per-character probabilities.
- Custom-trained models load through `import_onnx_path` + `charsets_path`, and training uses `dddd_trainer`.
- Docs are in Chinese.

— [ddddocr PyPI README](https://pypi.org/project/ddddocr/)

**OnnxTR / docTR**
- OnnxTR ships 8-bit quantized models "for faster inference on CPU", which can reduce accuracy.
- It supports CPU, OpenVINO and CoreML providers and has a `cpu-headless` install that uses opencv-headless.
- Its recognition architectures include `parseq`.

— [onnxtr PyPI README](https://pypi.org/project/onnxtr/)

**OpenOCR**
- Its SVTRv2-based OCR system is offered as server and mobile models and claims +4.5% accuracy over a PP-OCRv4 baseline at "quite similar inference speed". It supports ONNX export and has fine-tuning docs. It makes no CPU-specific claim and does not compare against PP-OCRv5/v6. — [OpenOCR README](https://github.com/Topdu/OpenOCR)

**Runtime versions**
- ONNX Runtime is at 1.31.0 (2026-10-09). — [PyPI](https://pypi.org/project/onnxruntime/)
- opencv-python-headless is at 5.0.0.93 (2026-07-02). — [PyPI](https://pypi.org/project/opencv-python-headless/)

### Inferences

**Recommended pipeline shape (OCR)**
1. Decode once with ffmpeg at 1–2 fps, cropping only the game window, e.g. `-vf "fps=2,crop=1288:695:0:0"`.
2. In NumPy, slice the fixed sub-rectangles for TOTAL WIN, BALANCE and BET.
3. Upscale 2–3×, threshold or invert, and pass each crop to RapidOCR with `use_det=False, use_cls=False`.
4. Parse the text with a regex like `\$?[\d,]+\.\d{2}`.
5. Accept a value only when it is stable across 2–3 consecutive samples. Glowing count-up animations produce intermediate garbage, and the final settled value is what matters.
6. Compute win multiplier = TOTAL WIN / BET. Flag events where it is at least some threshold (e.g. 100×), or where BALANCE jumps by more than X.

**Throughput estimate**
- At about 5–21 ms per crop (PaddleOCR's Xeon numbers for mobile recognition models), 3 fields × 2 fps × 3 hours ≈ 64,800 crops ≈ 5–23 CPU-minutes.
- In practice, ffmpeg decoding of a 1080p VOD probably costs more than the OCR.
- This is an extrapolation; no source benchmarks tiny numeric crops directly.

**Engine ranking for this job**
1. RapidOCR with PP-OCRv6 small (default) or tiny. Apache-2.0, ONNX, lightest dependency, active (release 2026-10-08), and PP-OCRv6 targets "digital displays" and screen text.
2. PaddleOCR itself. Same models, heavier paddlepaddle dependency, slower cold start.
3. tesserocr with PSM 7 and a whitelist. Fastest on clean static fields, but expect failures on gradients and glow.
4. OnnxTR (parseq, 8-bit). A reasonable alternative.
5. EasyOCR. Works and has `allowlist`, but pulls in PyTorch, is slower, and has had no release since 2024-09.

**Engines to avoid for this job**
- Surya and GOT-OCR2.0: VLM-class, very slow per frame on CPU, and license-restricted or unlicensed.
- CnOCR `number-*` models: no decimal point or comma.
- mmocr, parseq and clovaai DTRB: inactive or near-inactive.

**Stylised animated popup digits** ("3009.70", "1,957x")
- Do not try to OCR these first. Use the static TOTAL WIN field as ground truth, and treat the popup as a visual trigger (see section 4).
- If popup digits must be read, a ddddocr model custom-trained with `dddd_trainer` on a few hundred labelled crops, using charset `0123456789.,x$`, is probably the lowest-effort route. Fine-tuning a PP-OCR rec model is the more accurate but heavier route.

**Character set**
- PP-OCR English/Chinese dictionaries are believed to include "$", "," and ".", but this was not verified in this research. Test "$3,915.60" directly.

### Gaps
- No public benchmark measures recognition-only OCR on small cropped numeric UI fields (game HUDs, casino UIs) across engines on CPU. Accuracy on stylised, glowing slot digits is undocumented for every engine; it needs a local test on about 50–100 crops from Dylan's VODs.
- PP-OCRv6 recognition-only CPU latency per line is not yet published: the table shows "-".
- Whether RapidOCR's recognition-only path with PP-OCRv6 works out of the box was not verified. The only example found used PPOCRV5, although the config defaults to v6.
- The invoice and cold-start benchmark pages could not be fetched directly (DNS failure in the sandbox); the figures are from search summaries.
- Whether the Tesseract 5.x LSTM engine fully honours `tessedit_char_whitelist` was not confirmed beyond the 4.0-alpha issue report.
- CnOCR GitHub stars and push date were not retrievable; GitHub search did not return the main repo.

---

## 2. Are there open-source projects for slot/casino stream analysis or game-stream highlight detection?

### Takeaway
**No open-source project was found that detects slot big wins, OCRs multipliers or tracks bonus hunts from video.** The slot-related repos are manual web trackers, a 2022 Stake overlay and a mock-data proof of concept.

General stream-highlight tools exist, but all are small (under 60 stars) or LLM/transcript-driven. Their signals are:
- RMS loudness peaks
- chat-rate spikes (Twitch or YouTube chat only)
- Whisper keywords
- frame differencing
- audio tagging
- for shooters, kill-feed OCR

The most reusable designs are:
- **SparkReel**: a nine-signal weighted fusion with smoothing and peak-picking. MIT, CPU, no Kick.
- **artkulak's metamodel**: AudioSet tagging plus chat sentiment plus motion, fed to logistic regression. Inactive since 2021.
- **Kill-feed and scoreboard OCR clippers**: the same "read a fixed HUD region, trigger a clip" pattern needed for slot win fields.

Kick has no official chat-history API, so chat spikes are hard to use for Kick VODs.

### Cited Findings

**Slot/casino-specific repos (all tiny, none do video detection)**
- **JereUR/bonus-hunt-tracker**: "Tracker for slots bonus hunt". JavaScript, 0 stars, updated 2024-05. — [GitHub](https://github.com/JereUR/bonus-hunt-tracker)
- **atimof40-lang/bonus-hunt-tool**: browser bonus-hunt tracker with manual entry. 0 stars, 2026. — [GitHub](https://github.com/atimof40-lang/bonus-hunt-tool)
- **LezdCS/stake-twitch-overlay**: shows Stake wager progression and the current slot to the stream audience. 7 stars, last push 2022-08-18 (**inactive 2y+**), no license. — [GitHub](https://github.com/LezdCS/stake-twitch-overlay)
- **Rydell85/big-wins**: "POC for Big Wins". 0 stars. A search summary says it uses mock data and does no screen detection. — [GitHub](https://github.com/Rydell85/big-wins)
- Non-GitHub "streamer big wins" databases exist, e.g. "1,033 recorded slot hits with clips". These are commercial sites, not code. — [casinosincanada.com](https://casinosincanada.com/big-wins/), [spindex.net](https://spindex.net/streamer-wins)

**General stream-highlight detectors**

| Repo | Stars | Last push | License | How it detects highlights | Source |
|---|---|---|---|---|---|
| artkulak/twitch-stream-highlights-detection | 58 | 2021-05-26 (**inactive 2y+**) | Unlicense | Audio tagging (PANNs audioset_tagging_cnn), chat sentiment (transformers) and movement scoring. Extracted per 10-second clip and fed to a logistic-regression metamodel that outputs P(highlight). Needs Google Cloud. | [GitHub](https://github.com/artkulak/twitch-stream-highlights-detection); [TDS write-up](https://towardsdatascience.com/how-i-created-an-app-for-live-stream-highlight-detection-for-twitch-532f4027987e) |
| mimimaomao1117/sparkreel | 3 | 2026-07-16 | MIT | Nine signals: RMS energy plus burst/peak detection, spectral centroid/flux, chat-volume bursts, slang-dictionary chat sentiment, OpenCV frame differencing, colour-histogram divergence (scene change), Haar face detection, transcript keyword dictionary. Fusion is `fused(t)=Σwᵢsᵢ(t)/Σwᵢ`, then smoothing, then threshold peak-picking with minimum gap and cap, then window expansion. Weights live in `config/default.yaml`. Requires Python ≥3.10 + ffmpeg. Reports about 18 s to process 70 s of footage locally (hardware unstated). No Kick, no OCR. | [GitHub](https://github.com/mimimaomao1117/sparkreel) |
| LuisSotelo/vod-to-viral | 12 | 2026-06-15 | MIT (per README) | RMS volume peaks (`--peak-height`, `--min-peak-distance-sec`), Twitch chat activity weighted toward mods/VIPs (via TwitchDownloaderCLI), faster-whisper keywords. Whisper on CPU described as slow. No Kick. | [GitHub](https://github.com/LuisSotelo/vod-to-viral) |
| VadlapatiKarthik/autoclipper | 37 | 2025-05-07 | **none** | Description: detects highlights from YouTube and Twitch/Kick live streams "via audience-retention data, chat spikes and timestamped comments". Whisper subtitles; FastAPI + Celery. | [GitHub](https://github.com/VadlapatiKarthik/autoclipper) |
| xurei/twitch-highlights-logger | 35 | 2025-05-13 | GPL-3.0 | Loads full Twitch chat and counts filter-matching messages per time window; flags windows above a threshold. JavaScript desktop app. | [GitHub](https://github.com/xurei/twitch-highlights-logger) |
| nirvagold/stream-clipper | 3 | 2025-12-31 | MIT | Audio and chat analysis. Tauri + Rust + Svelte desktop app. | [GitHub](https://github.com/nirvagold/stream-clipper) |
| jBahrVR/jBahrs-Clip-Generator | 5 | 2026-10-12 | **none** | Local Whisper (GPU), per-segment RMS loudness tags, percussive-transient "combat" tags; a cloud LLM picks moments from the tagged transcript. Self-described "vibe coded". | [GitHub](https://github.com/jBahrVR/jBahrs-Clip-Generator) |
| dscig/twitch-highlight-detection | 19 | 2021-06-21 (**inactive 2y+**) | none | (no README detail) | [GitHub](https://github.com/dscig/twitch-highlight-detection) |
| leonnovacki/twitch-auto-highlights | 0 | 2024-07-23 (**inactive 2y+**) | none | Twitch chat-activity tracking | [GitHub](https://github.com/leonnovacki/twitch-auto-highlights) |
| Anil-matcha/AI-Youtube-Shorts-Generator | 5,341 | 2026-10-11 | MIT | LLM highlight detection over a Whisper transcript, plus auto vertical crop | [GitHub](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) |
| modelscope/FunClip | 6,393 | 2026-10-08 | MIT | FunASR transcription plus LLM-assisted clipping (Gradio UI) | [GitHub](https://github.com/modelscope/FunClip) |
| ClipsAI/clipsai | 549 | 2024-01-17 (**inactive 2y+**) | MIT | Transcript-based long-to-short clipping | [GitHub](https://github.com/ClipsAI/clipsai) |
| line/lighthouse | 272 | 2026-09-17 | Apache-2.0 | Library for video moment retrieval and highlight detection (text-query-based research models; also audio moment retrieval) | [GitHub](https://github.com/line/lighthouse) |
| showlab/UniVTG | 380 | 2024-05-08 (**inactive 2y+**) | MIT | ICCV 2023 video-language temporal grounding / highlight detection (research) | [GitHub](https://github.com/showlab/UniVTG) |

**Kill-feed and scoreboard OCR clippers (same pattern as reading a slot win field)**
- **rlmsinclair/montage_maker**: uses Tesseract to read the kill feed, matches the user's in-game name and marks kills on a timeline before building clips. 0 stars, pushed 2026-06-12, no license. — [GitHub](https://github.com/rlmsinclair/montage_maker); description via [search summary](https://github.com/rlmsinclair/montage_maker)
- **Alexmalware26/CS2-CLIP-IA**: CS2 clips (kills, multi-kills, aces, clutches) from kill-feed OCR. FastAPI + Celery + React. 0 stars, pushed 2026-08-06, no license. — [GitHub](https://github.com/Alexmalware26/CS2-CLIP-IA)
- **saurabhsingh1312/bgmi-kill-feed-extractor**: video processing plus OCR to extract BGMI/PUBG kill-feed stats. 0 stars, updated 2025-08-28. — [GitHub](https://github.com/saurabhsingh1312/bgmi-kill-feed-extractor)
- **ThomasMcCrossin/HockeyHighlightExtractor**: OCR scoreboard detection to extract game time and cut highlight clips. 0 stars, pushed 2026-10-09, MIT. — [GitHub](https://github.com/ThomasMcCrossin/HockeyHighlightExtractor)

**Chat-spike methods and research**
- A hobbyist Twitch bot tracked message frequency, length and emotes, and used an exponentially weighted moving average to flag surges. — [HdM Stuttgart blog](https://blog.mi.hdm-stuttgart.de/index.php/2019/08/21/evaluating-and-visualizing-statistical-bot-data/)
- A clipping-tool guide flags windows where chat velocity jumps several times above baseline and starts clips about 30 s before the spike, because chat lags the moment. — [Opus guide](https://www.opus.pro/mcp/inspiration/clip-the-moments-your-live-chat-exploded)
- Academic work:
  - Ringer's 2022 University of York PhD thesis covers multimodal (audio, visual, chat) livestream highlight detection. — [White Rose eTheses](https://etheses.whiterose.ac.uk/32406/)
  - Gutsche's 2022 University of Malta dissertation pre-trains "TwitchLeagueBert" on League of Legends chat for highlight detection and reports +0.01 F-score over the prior state of the art. — [UM OAR](https://www.um.edu.mt/library/oar/handle/123456789/137285)

**Chat sources**
- lay295/TwitchDownloader downloads, renders and replays chat for Twitch only. 3,975 stars, pushed 2026-10-06, MIT. — [GitHub](https://github.com/lay295/TwitchDownloader)
- xenova/chat-downloader handles livestream and past-broadcast chat (Twitch/YouTube). 1,197 stars, pushed 2025-11-05, MIT, last PyPI release 0.2.8 (2023-09-03). — [GitHub](https://github.com/xenova/chat-downloader), [PyPI](https://pypi.org/project/chat-downloader/)
- An Apify Kick chat archiver states there is no official Kick API for chat history; it captures live chat via Kick's Pusher websocket and cannot recover earlier messages. — [Apify kick-chat-archive](https://apify.com/DevilScrapes/kick-chat-archive)
- Another Apify actor says it calls reverse-engineered internal Kick Android-app APIs, including a REST chat-history endpoint. — [Apify kick-all-in-one-api](https://apify.com/romy/kick-all-in-one-api.md)
- Kick added chat replay on VODs and clips in 2024. — [Lindsey Gamble](https://www.lindseygamble.com/blog/kick-adds-chat-replays-and-clip-download-features)

### Inferences
- A slot-specific detector would have to be built. The closest templates are:
  - SparkReel's fusion-and-peak-picking design (MIT, readable YAML weights), adapted by adding an "OCR win multiplier" signal and a "popup present" signal.
  - The kill-feed OCR repos' fixed-ROI read-then-clip loop.
- For Dylan, OCR of TOTAL WIN / BET is a far more precise trigger than loudness or chat. A 1,000× hit is unambiguous in the numbers even if Dylan is quiet. Audio excitement then ranks or confirms candidates and finds the reaction peak for the edit.
- autoclipper (Kick chat spikes) and jBahr have **no license**. Read them for ideas only; do not copy code. xurei is GPL-3.0, which is a copyleft concern if code is vendored.
- Chat-spike detection on Kick VODs needs an undocumented internal endpoint. Kick viewer-clip timestamps, which the scanner already uses, are a more robust crowd signal. Clip creation also lags the moment by roughly 10–30 s, similar to chat.
- LLM/transcript tools (AI-Youtube-Shorts-Generator, FunClip, ClipsAI) cannot see on-screen wins and are a poor fit as the primary detector for slot streams.

### Gaps
- No open-source slot/casino win detector, multiplier-OCR tool or video-based bonus-hunt parser was found on GitHub or the web (searches: "slot win detection", "slot bonus hunt", "casino stream", "slot multiplier ocr"). Private or commercial tools may exist but were not found.
- The exact Kick chat-replay endpoint and its parameters were not confirmed. The Apify docs did not show the path.
- Detection quality (precision/recall) is not reported for any of the hobby highlight tools.

---

## 3. Which CPU-usable tools detect audio excitement and reactions (shouting, laughter, crowd energy) and scene or shot changes?

### Takeaway
On CPU, use loudness (ffmpeg `ebur128`/`astats` or pyloudnorm) as the cheap first pass. Then run an **AudioSet tagger** on candidate windows:
- **EfficientAT** mn04/mn10/dymn04 (about 1–5M params, 0.1–0.6 GMACs, MIT)
- **PANNs** Cnn14 via `panns_inference` (MIT, inactive since 2024 but stable)

Both output the 527 AudioSet classes, which include **Shout, Yell, Screaming, Whoop, Laughter, Cheering, Applause, Crowd**, and even **Coin (dropping)** and **Cash register**. **Silero VAD** (<1 ms per chunk on one CPU thread) separates speech from game audio. `jrgillick/laughter-detection` gives dedicated laughter segments but has old dependencies.

For scene and shot changes, **PySceneDetect** is active, BSD-3 and CPU-native. TransNetV2 is a neural alternative that has been inactive since 2023.

### Cited Findings

**Metadata**

| Repo | Stars | Last push | License | Latest PyPI release | Source |
|---|---|---|---|---|---|
| Breakthrough/PySceneDetect | 5,239 | 2026-10-12 | BSD-3-Clause | scenedetect 0.7.2 (2026-10-12) | [GitHub](https://github.com/Breakthrough/PySceneDetect), [PyPI](https://pypi.org/project/scenedetect/) |
| soCzech/TransNetV2 | 1,053 | 2023-12-04 (**inactive 2y+**) | MIT | not on PyPI | [GitHub](https://github.com/soCzech/TransNetV2) |
| fschmid56/EfficientAT | 367 | 2024-11-20 (about 1.9y) | MIT | n/a | [GitHub](https://github.com/fschmid56/EfficientAT) |
| qiuqiangkong/panns_inference | 275 | 2024-03-05 (**inactive 2y+**) | MIT | panns-inference 0.1.1 (2023-03-26) | [GitHub](https://github.com/qiuqiangkong/panns_inference), [PyPI](https://pypi.org/project/panns-inference/) |
| qiuqiangkong/audioset_tagging_cnn | 1,785 | 2024-07-25 (**inactive 2y+**) | MIT | n/a | [GitHub](https://github.com/qiuqiangkong/audioset_tagging_cnn) |
| jrgillick/laughter-detection | 296 | 2024-07-25 (**inactive 2y+**) | MIT | n/a | [GitHub](https://github.com/jrgillick/laughter-detection) |
| snakers4/silero-vad | 10,435 | 2026-09-29 | MIT | silero-vad 6.2.3 (2026-09-23) | [GitHub](https://github.com/snakers4/silero-vad), [PyPI](https://pypi.org/project/silero-vad/) |
| LAION-AI/CLAP | 2,307 | 2025-05-15 | CC0-1.0 | laion-clap 1.1.7 (2025-05-04) | [GitHub](https://github.com/LAION-AI/CLAP), [PyPI](https://pypi.org/project/laion-clap/) |
| tyiannak/pyAudioAnalysis | 6,269 | 2026-10-09 | Apache-2.0 | pyAudioAnalysis 0.3.14 (2022-02-07) | [GitHub](https://github.com/tyiannak/pyAudioAnalysis), [PyPI](https://pypi.org/project/pyAudioAnalysis/) |
| amsehili/auditok | 861 | 2026-07-28 | MIT | auditok 0.5.2 (2026-07-28) | [GitHub](https://github.com/amsehili/auditok), [PyPI](https://pypi.org/project/auditok/) |
| csteinmetz1/pyloudnorm | 783 | 2026-01-04 | MIT | pyloudnorm 0.2.0 (2026-01-04) | [GitHub](https://github.com/csteinmetz1/pyloudnorm), [PyPI](https://pypi.org/project/pyloudnorm/) |
| librosa/librosa | 8,678 | 2026-10-06 | ISC | librosa 1.0.0 (2026-08-11) | [GitHub](https://github.com/librosa/librosa), [PyPI](https://pypi.org/project/librosa/) |
| SYSTRAN/faster-whisper | 25,856 | 2026-10-13 | MIT | faster-whisper 1.2.1 (2025-10-31) | [GitHub](https://github.com/SYSTRAN/faster-whisper), [PyPI](https://pypi.org/project/faster-whisper/) |

**AudioSet classes relevant to streamer reactions**
- The 527-class label file includes these (index: name): 8 "Shout", 10 "Whoop", 11 "Yell", 12 "Battle cry", 13 "Children shouting", 14 "Screaming", 16 "Laughter", 18 "Giggle", 20 "Belly laugh", 21 "Chuckle, chortle", 66 "Cheering", 67 "Applause", 69 "Crowd", 70 "Hubbub, speech noise, speech babble", 380 "Coin (dropping)", 414 "Cash register". — [class_labels_indices.csv](https://github.com/qiuqiangkong/audioset_tagging_cnn/blob/master/metadata/class_labels_indices.csv)

**EfficientAT**
- AudioSet-pretrained MobileNetV3 and dynamic MobileNet taggers. — [EfficientAT README](https://github.com/fschmid56/EfficientAT)

  | Model | Params (M) | GMACs | mAP |
  |---|---|---|---|
  | mn04_as | 0.983 | 0.11 | 43.2 |
  | mn05_as | 1.43 | 0.16 | 44.3 |
  | mn10_as | 4.88 | 0.54 | 47.1 |
  | dymn04_as | 1.97 | 0.12 | 45.0 |
  | dymn10_as | 10.57 | 0.58 | 47.7 |
  | mn40_as | 68.43 | 8.03 | 48.4 |

- Models were trained in float16, so float32 CPU inference may show "a slight performance degradation". No CPU latency is given. The CLI is `python inference.py --model_name=dymn10_as --audio_path=...`. — [same README](https://github.com/fschmid56/EfficientAT)

**PANNs**
- `panns_inference` exposes `AudioTagging(checkpoint_path=None, device=...)` and `SoundEventDetection(...)` (frame-level). The default checkpoint is `Cnn14_mAP=0.431.pth`. — [panns_inference README](https://github.com/qiuqiangkong/panns_inference)

**Laughter detection**
- Segments laughter with a Switchboard-trained model (Gillick et al., Interspeech 2021). CLI options include `--threshold` (default 0.5) and `--min_length` (default 0.2 s). It outputs start/end segments and optional WAVs or TextGrid.
- It was tested with Python 3.6.1, PyTorch 1.3.1 and librosa 0.8.1.

— [laughter-detection README](https://github.com/jrgillick/laughter-detection)
- The script falls back to CPU automatically when CUDA is absent. — [segment_laughter.py](https://github.com/jrgillick/laughter-detection/blob/master/segment_laughter.py)

**Silero VAD**
- "One audio chunk (30+ ms) takes less than 1ms to be processed on a single CPU thread." It has an `onnx-cpu` extra and needs a CPU with AVX/AVX2/AVX-512/AMX. — [silero-vad PyPI README](https://pypi.org/project/silero-vad/)

**PySceneDetect**
- Detectors include `ContentDetector` (default), `AdaptiveDetector` (a "two-pass version" that handles fast camera movement better) and `ThresholdDetector` (fade in/out).
- The Python API is `detect('video.mp4', ContentDetector())`. Splitting uses ffmpeg or mkvmerge.

— [PySceneDetect README](https://github.com/Breakthrough/PySceneDetect)

**Prior use of audio tagging for Twitch highlights**
- artkulak's Twitch highlight project used the PANNs audioset_tagging_cnn code for its audio features. — [artkulak README](https://github.com/artkulak/twitch-stream-highlights-detection)

### Inferences

**Suggested audio stack for 1–3 h VODs on CPU**
1. Extract 16/32 kHz mono once with ffmpeg.
2. Compute short-term loudness (pyloudnorm or ffmpeg `ebur128`) and a rolling z-score.
3. Take the top-N peaks plus every OCR-detected win time.
4. Run EfficientAT mn10_as or PANNs Cnn14 only on ±10 s windows around those candidates.
5. Score "reaction" as the max probability of Shout/Yell/Screaming/Whoop/Cheering/Laughter.

This keeps the tagger off most of the audio. Tagging the full VOD with mn04/mn10 (about 0.1–0.5 GMACs per clip) is also plausible on CPU, but no published latency confirms it.

**Mixed audio problem**
- Slot game audio (win jingles, coin sounds) is mixed with Dylan's voice. "Coin (dropping)" and "Cash register" may fire on game sounds, which helps find wins but adds noise to reaction scoring.
- Silero VAD can restrict the reaction score to windows with speech. Source separation is out of scope here (covered elsewhere).

**Laughter model**
- jrgillick's laughter model is accurate for its niche, but its 2019–2021-era dependency pins make it Medium–High effort in a modern container. The AudioSet "Laughter" class from EfficientAT/PANNs is the lower-friction substitute.

**Scene detection**
- PySceneDetect is of limited value for a static stream layout, because the camera never cuts. It is useful mainly as a cheap "big visual change in the game window" detector: run it on the cropped game region with a lowered threshold, so full-screen win popups, bonus-round intros and game switches register as "scene changes".
- TransNetV2 adds little here and is inactive.

**Transcript keywords**
- faster-whisper (MIT, CPU int8 supported by CTranslate2) could add "let's go / oh my god / no way" keyword hits. Full-VOD transcription on CPU is slow (vod-to-viral notes Whisper on CPU is slow), so run it only on candidate windows.

### Gaps
- No published CPU latency figures were found for EfficientAT, PANNs Cnn14, laughter-detection or TransNetV2.
- PySceneDetect's speed tips (downscale, frame skip, PyAV vs OpenCV backends) and its HistogramDetector/HashDetector were not confirmed from the fetched page. Its benchmark page (scenedetect.com/benchmarks) was not reachable.
- No source evaluates AudioSet shout/laughter classes on streamer microphone audio mixed with loud game sound.

---

## 4. What template-matching, popup-detection or small-classifier approaches are used to detect "big win" banners?

### Takeaway
No published project detects slot "BIG WIN" or "TOTAL WIN" banners. The established approach from game-VOD tooling is **OpenCV `matchTemplate` (TM_CCOEFF_NORMED) on a fixed, cropped region with a score threshold and frame skipping**, as in brawl-template-matcher (Brawlhalla) and downsmash/segment (Smash Melee). Templates must be **static** screen elements.

Glowing, animated popups are better handled by one of:
- cheap change detectors: frame differencing or perceptual hash on the game-window crop
- template-matching a static word ("TOTAL WIN", "BIG WIN") rather than the changing digits
- a zero-shot or small CLIP classifier (open_clip, active) on sampled frames

### Cited Findings
- **CrossyChainsaw/brawl-template-matcher** "scans an .mp4 for a given image, capturing screenshots and timestamps of matches". Inputs include a minimum-accuracy threshold and a frame-skip value. Python/cv2, 2 stars, pushed 2026-01-26, no license. — [GitHub](https://github.com/CrossyChainsaw/brawl-template-matcher); parameter details via [search summary](https://github.com/CrossyChainsaw/brawl-template-matcher)
- **downsmash/segment** parses Super Smash Bros. Melee VODs and returns JSON with start/end times of each game segment. Stars and activity were not retrieved. — [GitHub, via search summary](https://github.com/downsmash/segment)
- **multi-template-matching/MultiTemplateMatching-Python**: "Object-recognition using multiple templates in python". 221 stars, pushed 2025-10-28, MIT. — [GitHub](https://github.com/multi-template-matching/MultiTemplateMatching-Python)
- **OpenCV guidance**
  - Template matching needs a template that stays the same across frames, i.e. a static HUD element, not the whole changing frame.
  - Cropping the search to the region where the event appears speeds processing.
  - The usual call is `cv2.matchTemplate(..., TM_CCOEFF_NORMED)` + `cv2.minMaxLoc`, where the peak score is the similarity.

  — [OpenCV forum: template matching with video input](https://forum.opencv.org/t/template-matching-with-video-input/6563/5); [OpenCV forum: detecting Valorant kills](https://forum.opencv.org/t/templatematch-detecting-valorant-game-kills-from-player/9821); [HackerNoon guide](https://www.hackernoon.com/how-to-make-a-gaming-bot-that-beats-human-using-python-and-opencv)
- **mlfoundations/open_clip**: open-source CLIP, 14,195 stars, pushed 2026-09-30. GitHub reports the license as NOASSERTION; PyPI lists MIT. open_clip_torch 3.3.0 was released 2026-02-27. — [GitHub](https://github.com/mlfoundations/open_clip), [PyPI](https://pypi.org/project/open-clip-torch/)
- **ImageHash** (perceptual hashing): 4.3.2 released 2025-02-01, 2-clause BSD. — [PyPI](https://pypi.org/project/ImageHash/)
- SparkReel's visual signals are OpenCV frame differencing ("motion") and colour-histogram divergence ("scene"), both CPU-only. — [SparkReel README](https://github.com/mimimaomao1117/sparkreel)

### Inferences

**Recommended popup and banner detector for Dylan's layout** (all OpenCV, CPU, Low effort):
1. On the 1–2 fps game-window crop, compute the mean absolute frame difference and the HSV saturation/brightness of the centre region. Big-win popups are bright, saturated and glowing, so a jump flags a candidate.
2. Template-match static words cut from real frames ("TOTAL WIN", "BIG WIN", "MEGA WIN", "BONUS") at 2–3 scales. Use TM_CCOEFF_NORMED on grayscale or edge maps, with thresholds of about 0.7–0.8 tuned on samples. Every provider (Pragmatic, Hacksaw, Nolimit) draws these differently, so keep a small template bank per frequently played game.
3. Confirm with OCR of the static TOTAL WIN field after the popup settles (section 1).

**Small-classifier option**
- Label about 200–500 sampled frames from past VODs as popup / no-popup / bonus-intro, then fine-tune a tiny MobileNet or linear-probe CLIP embeddings.
- Or use zero-shot open_clip prompts such as "a slot machine big win celebration screen" on 1 fps crops. CLIP ViT-B/32 on CPU is likely about tens of ms per image.
- This is unverified; no benchmark was found in this research.

**Bonus Hunt overlay (top-right table)**
- OCR it every 15–60 s, or only when an imagehash of the overlay crop changes. A hash change means a row was filled in, i.e. a bonus was opened and paid. That gives an exact timestamp for each bonus result and its payout.

**Integration difficulty**
- ffmpeg crop/fps → NumPy → OpenCV is Low.
- Template banks per game are Medium (maintenance).
- A CLIP or MobileNet classifier is Medium (needs labelled frames and a torch or ONNX runtime).

### Gaps
- No public dataset, template set or trained model for slot "big win" popups was found.
- No CPU throughput figures were found for open_clip zero-shot frame classification.
- downsmash/segment's detection method and repo metadata, and brawl-template-matcher's accuracy, were not verified beyond search summaries.
