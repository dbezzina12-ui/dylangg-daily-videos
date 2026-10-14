# New GitHub tools for the hype-edit pipeline (round 2, 14 Oct 2026)

Stars, licence and last push come from GitHub search metadata; release dates and Python ranges come from PyPI JSON. Nothing was installed or benchmarked, so CPU speeds are estimates unless a README states them. Tools from the first report are skipped unless something changed.

## 1. Hit detection beyond OCR
- **[benfmiller/audalign](https://github.com/benfmiller/audalign)** finds known sounds by fingerprint and cross-correlation. Record each slot's "big win" sting once, then search the game stem for it. MIT · 151★ · last push May 2026 (PyPI 1.3.1, Mar 2025) · CPU-trivial. **Try.** A numpy cross-correlation over the mel spectrogram does the same job with no new dependency.
- **[microsoft/CLAP](https://github.com/microsoft/CLAP)** (`msclap`) does zero-shot audio tagging from text prompts such as "jackpot jingle", "man shouting" or "crowd cheering". MIT · 678★ · **archived** (pip 1.3.4, May 2025, lists Python 3.13) · CPU is fine on short windows. **Try** as a second opinion to PANNs. [LAION-AI/CLAP](https://github.com/LAION-AI/CLAP) (code CC0, 2.3k★, last push May 2025) is the alternative. I did not verify its checkpoint licences.
- **Excitement in Dylan's voice:** I found no commercially usable "arousal" model. audeering's dimensional-emotion model is CC-BY-NC-SA, and [emotion2vec](https://github.com/ddlBoJack/emotion2vec) has no licence file. [SpeechBrain](https://github.com/speechbrain/speechbrain) (Apache-2.0, 11.9k★, 1.1.1 Aug 2026) ships an IEMOCAP emotion model, but it only gives 4 classes and is weak for "hype". **Skip models.** Instead, z-score pitch (librosa pyin), RMS and words per second (from faster-whisper timings) against his own baseline.
- **Kick chat velocity:** no maintained Python library replays Kick VOD chat. [VXsz/ReKick](https://github.com/VXsz/ReKick) (Go, 9★, no licence, one push Oct 2025) is reading material only. [zazenss/vod-chat-heatmap](https://github.com/zazenss/vod-chat-heatmap) (MIT, 1★) shows the heat-map idea. The `kick-chat` PyPI package is live-only and GPL-3. **DIY:** count messages per 5 s bucket, score each against a rolling 5-min median, and add counts of hype tokens (W, LETS GO, emotes, "$"). Shift the result back about 5–15 s to allow for chat lag.

## 2. Timeline export for human tweaks
- **[OpenTimelineIO](https://github.com/AcademySoftwareFoundation/OpenTimelineIO):** Apache-2.0 · 2.0k★ · pushed today · pip 0.18.1 (Nov 2025, lists Python 3.13). DaVinci Resolve 18.5+ imports `.otio` natively according to the Resolve manual (not tested here). **Adopt.** Write cuts on V1 and pre-rendered pop-ups/captions as alpha MOVs on V2/V3, so an editor can nudge timings without a re-render.
- **[otio-fcp-adapter](https://github.com/OpenTimelineIO/otio-fcp-adapter)** writes Premiere/FCP7 XML and **[otio-fcpx-xml-adapter](https://github.com/OpenTimelineIO/otio-fcpx-xml-adapter)** writes FCPXML. Both are Apache-2.0, but their last PyPI release was 1.0.0 in 2023 (repos pushed Apr 2026 and Jun 2024). **Try** if the editor uses Premiere or FCP.
- **[GuanYixuan/pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft)** generates CapCut/JianYing drafts. Apache-2.0 · 4.6k★ · very active (pip 0.3.1 today). It targets **JianYing (China)**. On Linux it can only *generate* drafts; export still needs the Windows app. Its CapCut-international sibling [pyCapCut](https://github.com/GuanYixuan/pyCapCut) (705★) has **no licence**. [VectCutAPI](https://github.com/sun-guannan/VectCutAPI) (Apache-2.0, 2.3k★) is an HTTP draft server. **Skip** unless a human editor really lives in CapCut desktop.

## 3. Render caching and proxies
No library is worth adopting here; it's a pattern. Key each segment on `sha256(segment-spec JSON + source hash + engine version)`. Encode every segment with identical codec, GOP, fps and timebase, then join them with the ffmpeg concat demuxer using `-c copy`. Render audio once over the whole timeline and mux it last, which avoids AAC gaps at the joins. For previews, render the same spec at 540×960 with `-preset ultrafast`. For storage, [joblib.Memory](https://github.com/joblib/joblib) (BSD-3, active) or [python-diskcache](https://github.com/grantjenks/python-diskcache) (Apache-2.0, last release 2023, stable) both work. Making the OTIO file the spec doubles as the cache key. **Adopt the pattern.**

## 4. Automated QA
- **ffmpeg built-ins:** `blackdetect`, `freezedetect`, `silencedetect` and `ebur128`. **Adopt**; no dependency.
- **[slhck/ffmpeg-normalize](https://github.com/slhck/ffmpeg-normalize):** two-pass EBU R128 to −14 LUFS / −1 dBTP. MIT (per PyPI) · 1.5k★ · 1.43.0 released today · Python 3.10–3.15. **Adopt.**
- **[RapidFuzz](https://github.com/rapidfuzz/RapidFuzz)** detects duplicated phrases when you re-transcribe the render and compare n-gram windows. MIT · 4.2k★ · 3.14.6 (Aug 2026, Python 3.11+). **Adopt.**
- **[ffmpeg-quality-metrics](https://github.com/slhck/ffmpeg-quality-metrics)** gives SSIM/VMAF regression checks against "golden" renders. MIT · 3.13.0 today. **Try.**
- **Blur check:** run the existing RapidOCR on blurred boxes and assert that no digit regex matches; add a Laplacian-variance floor. No new tool needed.
- **[TransNetV2](https://github.com/soCzech/TransNetV2):** MIT but dormant since 2023 and not on PyPI. PySceneDetect 0.7.2 (12 Oct 2026) is enough for checking cut lengths. **Skip.**

## 5. Talking cartoon pop-ups
- **[rhubarb-lip-sync](https://github.com/DanielSWolf/rhubarb-lip-sync)** turns audio (plus the known TTS script) into 6–9 mouth shapes with timings. MIT · 2.7k★ · v1.14.0 (Apr 2025, year inferred) · fast CLI binary. **Adopt.** Pair it with one PNG per mouth shape (Higgsfield can make these) and a small head bob. That is the realistic "Live2D-lite".
- **[rlottie-python](https://github.com/laggykiller/rlottie-python)** renders Lottie stickers to PIL frames on CPU. LGPL-2.1 (dynamic linking is fine) · 1.3.8 (Aug 2025) · Python 3.13 wheel status unverified. **Try.** python-lottie (`lottie` on PyPI) is **AGPL**, so **skip** it. [Inochi2D](https://github.com/Inochi2D/inochi2d) (BSD-2) is a D-language app that needs a GPU and GUI. **Skip.**

## 6. Voice
- **Chatterbox-Turbo / Nano** ([repo](https://github.com/resemble-ai/chatterbox), MIT, 27k★): the 110M Nano is "3× realtime on 8 CPU cores" per its README and supports `[laugh]`-style tags. It is English-only, and pip 0.1.7 (Mar 2026) may predate Nano. **Adopt (test first)**, since you already use Chatterbox.
- **[kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx)** has US and UK voices but no cloning. MIT code, Apache weights · 2.8k★ · 0.6.1 (Aug 2026, Python 3.10–3.13) · very fast on CPU. **Adopt** for narrator lines. Avoid `kokoro` itself, which requires Python <3.13.
- **[NeuTTS Air](https://github.com/neuphonic/neutts)** does 3-s cloning, ships GGUF builds for CPU and watermarks its output. Air weights are Apache-2.0; the Nano variants use "NeuTTS Open License 1.0" (unread). pip 1.4.1 (Jul 2026). **Try.**
- **[OpenVoice v2](https://github.com/myshell-ai/OpenVoice)** offers explicit accent choice (MeloTTS EN-US/BR/AU/India speakers) plus a tone-colour clone. MIT · 37.9k★ · dormant since Apr 2025, with old MeloTTS deps that may not work on 3.13. **Try only if accent control is a must.**
- **Skip on licence or CPU grounds:**
  - **F5-TTS:** MIT code, but the official weights are CC-BY-NC.
  - **Seed-VC:** GPL-3 and archived.
  - **IndexTTS2:** bilibili licence; commercial use needs contact.
  - **Higgs Audio v3:** non-commercial.
  - **VibeVoice TTS:** code removed by Microsoft.
  - **Dia (1.6B), Orpheus (3B, Llama licence), Zonos:** GPU-class models; Zonos is dormant.
- **RVC** (MIT, 38.7k★) needs per-voice training. **Skip for now.**

## 7. Word-level animated captions
- **[pysubs2](https://github.com/tkarabela/pysubs2)** writes ASS files. Feed it faster-whisper `word_timestamps`, use `\k` karaoke tags or per-word `\t` pop-scale tags, and burn in with ffmpeg's `subtitles` filter. MIT · 1.9.0 (Aug 2026, Python 3.12+). **Adopt** (no new models needed).
- **[pycaps](https://github.com/francozanardi/pycaps)** offers CSS-styled TikTok-style templates. MIT · 226★ · active Sep 2026. It is alpha, installs from git, needs Playwright/Chromium, and is tested on 3.10–3.12. **Try** it for style ideas.
- **[whisperX](https://github.com/m-bain/whisperX)** improves word timing with forced alignment. BSD-2 · 24.5k★ · 3.8.6 (May 2026, Python <3.14) · heavy dependencies. **Try only if word timing drifts.**

## 8. Background removal
- **[rembg](https://github.com/danielgatis/rembg)** runs ONNX on CPU and has an `isnet-anime` model suited to cartoon art; BiRefNet models are also available through it. MIT · 25k★ · 2.0.85 (Sep 2026, Python 3.11–3.15). **Adopt.** Avoid its `bria-rmbg` model, which is non-commercial. Model files must be copied into the container.
- **[BiRefNet](https://github.com/ZhengPeng7/BiRefNet)** (MIT, 4.3k★, active) gives the best edges but takes seconds per image on CPU, so use it through rembg.

## 9. Other clip finders
I found no new serious open-source clipper: a GitHub search for highlight/clipper repos with 300+ stars pushed since March 2026 returned nothing. [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) (MIT, 131k★) generates stock-footage videos and is a toy for this use case. **Skip.** The first report's verdicts on auto-editor, ClipsAI and the shorts generators still stand.

## Top 5
1. **OTIO export with layered alpha overlays.** Human tweaks in Resolve without re-rendering, and the timeline becomes the cache key.
2. **Segment cache, concat `-c copy`, 540p proxies, plus an ffmpeg QA pass** (blackdetect/freezedetect, ffmpeg-normalize, RapidFuzz dupes, OCR blur assert).
3. **pysubs2 karaoke ASS from faster-whisper words.** Short-form captions at almost zero cost.
4. **rhubarb-lip-sync mouth-flap with rembg `isnet-anime` cut-outs.** Cartoon characters that talk.
5. **Chatterbox-Nano/Turbo, with kokoro-onnx UK/US voices as a fast fallback.** Add audalign/CLAP for win-jingle hits once the above are in.

**Unverified:** CPU speeds (none were benchmarked), rhubarb's release year, CLAP weight licences, the NeuTTS Open License terms, whether rlottie-python and Chatterbox-Nano work on Python 3.13, and Resolve's OTIO import (from the manual, not tested). Model hosts may still be blocked in the container.
