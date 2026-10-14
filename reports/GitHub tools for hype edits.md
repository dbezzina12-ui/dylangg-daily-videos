# Teach the stream scanner to read big wins

The single most valuable upgrade for Dylan's hype-edit pipeline is teaching the stream scanner to read the TOTAL WIN and BET numbers straight off the slot screen. No ready-made highlight tool can do this, because nobody has published an open-source slot win detector. The reader would be **RapidOCR**. OCR is software that reads text off an image; RapidOCR is free (Apache-2.0), had a new release on 8 Oct 2026 and is fast on a plain CPU. Two cheap checks back it up: OpenCV spots the big-win celebration screen, and a small speech detector tells Dylan's shouting apart from loud slot music. With that in place, a 1,000x hit shows up in the numbers even when Dylan is quiet. No loudness- or chat-based clipper can promise that. Behind that upgrade, a handful of free, commercially usable tools covers the other pain points:

- **Voice-aware ducking:** Silero VAD with ffmpeg's built-in sidechain compressor.
- **Voice isolation:** RoFormer separation, run only on the seconds that make the edit.
- **Music drops:** a librosa beat-plus-bass-energy drop finder, run once per song.
- **Slow-mo and upscaling:** RIFE through OpenVINO, and ESPCN/FSRCNN, both run on the zoomed crop rather than the full frame.
- **Card following and the 9:16 crop:** an OpenCV tracker smoothed with a One Euro filter.

Render time falls most from using all four CPU cores (about 1.8x faster in a test in the project's own container), not from switching editing engines. Kick VODs should come through the pipeline's own playlist fetch, because yt-dlp's Kick VOD support has been broken since July 2026. Postiz is the strongest open-source scheduler, but it needs its own always-on server. Avoid three kinds of tool:

- **AGPL and non-commercial licences:** Ultralytics YOLO, Essentia, madmom's models, CoTracker.
- **Archived projects:** Meta's Demucs repo, Google FILM, AutoFlip.
- **Unofficial posting clients that put his accounts at risk:** instagrapi, the TikTok uploaders.

One practical catch applies to every AI tool here. The cloud container's network policy blocked Hugging Face, PyTorch and other model hosts during this research, so model files must be copied in, or those hosts allowlisted, before any of it runs.

## What to adopt first, in order of payoff

Each item says what it would do for the edits. Links, licences and caveats follow in the later sections. "Free" here means open-source under a licence that allows commercial use.

1. **A win reader for the scanner (RapidOCR).** It reads TOTAL WIN, BET and BALANCE off the slot screen once or twice a second and works out the multiplier. It flags every hit above a threshold Dylan picks, say 100x, so quiet wins get found too. Effort is low, but its model files have to be copied into the container first.
2. **A celebration-screen and reaction spotter (OpenCV plus Silero VAD).** It notices when the "BIG WIN" screen flashes up, and whether Dylan is actually shouting rather than the slot jingle just being loud. Each candidate moment gets a reaction score, and the edit starts on the right beat. OpenCV is already in the engine; Silero VAD adds one tiny MIT model that comes inside its pip package.
3. **Faster renders that use all four CPU cores.** Each shot renders in its own process, with a quicker encoder setting where quality allows. In the container this cut a sample render from 21.8 s to 11.9 s. No new tool is needed, just a change in how hype_edit.py runs.
4. **Ducking that follows his voice (Silero VAD plus ffmpeg's sidechaincompress).** Music and slot sound dip exactly when Dylan talks and come back when he stops, with no hand-tuned voice-band tricks. For the rare clip where his voice must be truly isolated, run audio-separator's RoFormer model on just those 10–40 seconds.
5. **Kick downloads that grab only what is needed, plus chat replay.** It downloads just the 10-second pieces of the VOD around a win instead of the whole stream, and pulls the VOD's chat to see where chat exploded. It uses the pipeline's own Kick playlist call, not yt-dlp's currently broken Kick VOD extractor.
6. **A music-drop finder (librosa).** It finds the drop in each song bed once and saves it, so the engine can land the win reveal on the drop. No AI download is needed.
7. **A steady card-following camera and smarter 9:16 crop (OpenCV tracker plus One Euro filter).** It locks onto the dealt card or the win area and glides instead of jittering. The same smoothed path drives the Instagram crop.
8. **Polish: RIFE slow motion and fast upscaling.** RIFE is the only AI frame-interpolator with published, workable CPU speeds for 2–4x slow-mo. ESPCN/FSRCNN sharpen zoomed crops and small phone recordings in about a hundredth of a second per frame. Effort is medium; it is worth doing once items 1–7 are in.

Later, and only if the Social HQ queue stops being enough: Postiz, or the platforms' official APIs, for automatic scheduled posting.

## No slot win detector exists, so the scanner has to read the screen

A search of GitHub turned up nothing that detects slot wins from video. The slot-related projects are a manual bonus-hunt tracker ([JereUR/bonus-hunt-tracker](https://github.com/JereUR/bonus-hunt-tracker)), a 2022 Stake overlay with no licence ([LezdCS/stake-twitch-overlay](https://github.com/LezdCS/stake-twitch-overlay)), and a proof of concept that runs on mock data ([Rydell85/big-wins](https://github.com/Rydell85/big-wins)). General stream-highlight tools exist, but they are tiny. They judge moments by loudness, Twitch chat or a transcript, and none reads on-screen numbers. Transcript-driven clippers such as [FunClip](https://github.com/modelscope/FunClip) and [AI-Youtube-Shorts-Generator](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator) cannot see a win at all.

Two existing designs are worth copying.

- **SparkReel** (MIT, 3 stars) combines nine signals, among them loudness, frame differences and chat bursts. It weights them in a settings file, then picks peaks with a minimum gap between them. It processed 70 s of footage in about 18 s ([SparkReel](https://github.com/mimimaomao1117/sparkreel)).
- **Shooter and hockey clippers** read a fixed region of the screen, such as a kill feed or scoreboard, and cut a clip when it changes ([HockeyHighlightExtractor](https://github.com/ThomasMcCrossin/HockeyHighlightExtractor), [montage_maker](https://github.com/rlmsinclair/montage_maker)). A slot win field needs exactly this pattern.

### RapidOCR reads the win, bet and balance fields best on CPU

| Tool | Role | Licence | Status (Oct 2026) | CPU fit | Verdict |
|---|---|---|---|---|---|
| [RapidOCR](https://github.com/RapidAI/RapidOCR) | Runs PaddleOCR's models on ONNX Runtime/OpenVINO | Apache-2.0 | Release 3.10.0 on 8 Oct 2026 ([PyPI](https://pypi.org/project/rapidocr/)) | Good | **Adopt** |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) (PP-OCRv6) | The underlying models | Apache-2.0 | 3.7.0, Jun 2026 | Heavier install, slow cold start | Use through RapidOCR |
| [Tesseract](https://github.com/tesseract-ocr/tesseract) via [tesserocr](https://github.com/sirfz/tesserocr) | Classic OCR | Apache-2.0 / MIT | tesserocr 2.11.0, Aug 2026 | Fastest | Fallback for clean fields |
| [EasyOCR](https://github.com/JaidedAI/EasyOCR) | Deep-learning OCR | Apache-2.0 | No release since Sep 2024 | Slower; needs PyTorch | Skip |
| [Surya](https://github.com/datalab-to/surya) | Vision-language OCR | Code Apache-2.0; weights limited by revenue | Active | Very slow on CPU | Avoid |
| [CnOCR](https://pypi.org/project/cnocr/) digit models | Digit-only OCR | Apache 2.0 | 2.3.3, Jul 2026 | Fast | Skip: cannot output "." or "," |
| [ddddocr](https://github.com/sml2h3/ddddocr) + [dddd_trainer](https://github.com/sml2h3/dddd_trainer) | Small retrainable OCR | MIT / Apache-2.0 | 1.6.1, Mar 2026 | Fast | Later, for animated popup digits |

RapidOCR's default model is PP-OCRv6 "small" ([config.yaml](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/config.yaml)). PP-OCRv6 shipped in June 2026 and claims "major improvements in digital displays" ([PaddleOCR on PyPI](https://pypi.org/project/paddleocr/)). On Paddle's own benchmark it reads screen text with **79.7% accuracy for v6 small, against 57.6% for the older v5 mobile model** ([PP-OCRv6 doc](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-OCRv6/PP-OCRv6.en.md)). Screen text is the closest published stand-in for slot UI.

Speed is not a concern. PaddleOCR's mobile recognition models take about **3.6–21 ms per line of text** on an 8-thread Xeon ([PaddleOCR recognition doc](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/module_usage/text_recognition.en.md)). The fields never move on screen, so RapidOCR can skip its "find the text" step and only read pre-cut boxes. Tesseract is the fastest option on clean, flat fields but struggles with glowing or gradient digits. The usual fix is single-line mode plus an allowed-character list ([AutoIt forum](https://www.autoitscript.com/forum/topic/207435-tesseract-not-picking-up-a-number/)).

The scanner would work like this:

1. ffmpeg decodes the VOD at 1–2 frames per second and crops to the game window.
2. The scanner cuts out the TOTAL WIN, BET and BALANCE boxes, enlarges them 2–3x and sharpens the contrast.
3. RapidOCR reads each box.
4. A value counts only once it holds steady for two or three readings in a row. Count-up animations produce junk numbers in between.
5. Win divided by bet gives the multiplier, and hits above the threshold become candidates.

Three fields twice a second for three hours is about 64,800 reads, roughly **5–23 CPU-minutes** at the published speeds. That is an estimate, because nobody has benchmarked tiny number crops.

Leave the big animated popup digits (like "1,957x") alone at first. Use the steady TOTAL WIN field as the truth and treat the popup only as a visual trigger. If popup digits ever need reading, the lowest-effort route is to retrain ddddocr on a few hundred labelled crops using the characters `0123456789.,x$`.

Three things remain untested. No engine has been benchmarked on stylised slot digits. Nobody has confirmed that "$" and "," come through. And the recognition-only mode has not been verified with v6 out of the box; the one example found used v5. A test on 50–100 crops from Dylan's own VODs is the first job.

### Cheap checks find the celebration screen and the scream

| Tool | Role | Licence | Status | CPU fit | Verdict |
|---|---|---|---|---|---|
| OpenCV `matchTemplate` ([forum guide](https://forum.opencv.org/t/template-matching-with-video-input/6563/5)) | Finds fixed words like "BIG WIN" / "TOTAL WIN" | Apache-2.0 | Already in the engine | Easy | **Adopt** |
| [Silero VAD](https://github.com/snakers4/silero-vad) | Detects when someone is speaking | MIT | 6.2.3, Sep 2026 | Under 1 ms per audio chunk | **Adopt** |
| [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm) / ffmpeg `ebur128` | Measures loudness | MIT | 0.2.0, Jan 2026 | Easy | **Adopt** |
| [EfficientAT](https://github.com/fschmid56/EfficientAT) | Tags Shout, Yell, Screaming, Laughter, Cheering | MIT | Last push Nov 2024 | Tiny models (about 1–5M parameters) | Add, on candidate windows only |
| [panns_inference](https://github.com/qiuqiangkong/panns_inference) | Same tagging, older | MIT | Inactive since Mar 2024 | OK | Backup |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | Flags big visual changes | BSD-3 | 0.7.2, 12 Oct 2026 | Easy | Optional |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Spots "let's go", "no way" | MIT | Pushed Oct 2026 | OK on short windows | Later |
| [open_clip](https://github.com/mlfoundations/open_clip) | Labels frames ("big-win screen?") from a text prompt, no training | MIT on PyPI | Active | Untested | Later experiment |
| [ImageHash](https://pypi.org/project/ImageHash/) | Notices when the bonus-hunt table changes | BSD-2 | 4.3.2, Feb 2025 | Easy | Optional |

The celebration screen is the easiest thing to catch. Big-win popups are bright, saturated and glowing, so a sudden jump in brightness inside the game window flags a candidate. OpenCV then confirms it by searching for the fixed words ("BIG WIN", "MEGA WIN", "TOTAL WIN") cut from real frames, at two or three sizes. Template matching only works on elements that stay the same frame to frame ([OpenCV forum](https://forum.opencv.org/t/templatematch-detecting-valorant-game-kills-from-player/9821)). Pragmatic, Hacksaw and Nolimit each draw these words differently, so expect a small template bank per game.

Reactions come from audio. Loudness peaks are the cheap first pass. Around each candidate, the sound tagger scores ±10 seconds for **Shout, Yell, Screaming, Whoop, Laughter and Cheering**, all among the 527 sound types it knows ([class list](https://github.com/qiuqiangkong/audioset_tagging_cnn/blob/master/metadata/class_labels_indices.csv)). The same list includes "Coin (dropping)" and "Cash register". Those fire on slot sounds, which helps find wins but blurs the reaction score. Running Silero VAD alongside, so that only moments with speech count, keeps slot jingles from inflating it.

Three more signals can sit on top:

- **Kick viewer-clip timestamps**, which the scanner already uses, add a crowd signal.
- **Chat spikes** can come later. Chat lags the moment, so clipping guides start clips about 30 seconds before a spike ([Opus guide](https://www.opus.pro/mcp/inspiration/clip-the-moments-your-live-chat-exploded)).
- **The Bonus Hunt table** in the top-right corner can be read whenever its image hash changes. A change means a row was just filled in, which gives the exact time each bonus opened and what it paid.

## Kick downloads should bypass yt-dlp's broken VOD support

[yt-dlp](https://github.com/yt-dlp/yt-dlp) is the standard downloader (Unlicense, 197.7k stars, latest stable release 2026.08.19). Its Kick VOD extractor has **returned 404 errors since about July 2026**, after Kick changed how VOD URLs are built ([issue #17284](https://github.com/yt-dlp/yt-dlp/issues/17284)). The fix, [PR #17322](https://github.com/yt-dlp/yt-dlp/pull/17322), was still open in late September. One tester also found playback still blocked with a 403 unless `--impersonate chrome` was added.

Kick sits behind Cloudflare, and 403 blocks keep returning. A yt-dlp maintainer blamed one wave on blocked browser fingerprints or **the reputation of the IP address** ([issue #16012](https://github.com/yt-dlp/yt-dlp/issues/16012)). A cloud container's datacenter IP is a worse starting point than a home connection. The same issue thread also reports ad trouble: one master playlist downloaded only a 30-second pre-roll ad, and another VOD with mid-stream ads played only its intro ad.

The pipeline already gets the master playlist from `/api/v2/channels/dylanjamesgg/videos`, so it can skip the broken extractor:

1. Pick a quality and fetch only the 10-second segments that cover the wanted range (segment number = time ÷ 10, rounded down).
2. Join them with `ffmpeg -c copy`, so nothing is re-encoded.
3. Check the playlist for ad breaks (`#EXT-X-DISCONTINUITY` markers) and for the expected length.

Keep yt-dlp with curl_cffi as a backup and for clips, since the Kick clip extractor did not appear in any breakage report. For datacenter blocks, [streamlink](https://raw.githubusercontent.com/streamlink/streamlink/master/src/streamlink/plugins/kick.py) (BSD-2) shows one way through. When it hits a 403 it opens a headless Chromium to pass Cloudflare's browser check, then reuses the cookies for 30 days.

Chat is harder. Kick's official API has **no endpoints for VODs, clips or chat history**. For live chat it offers only a `chat.message.sent` webhook ([docs.kick.com](https://docs.kick.com/llms.txt), [event types](https://docs.kick.com/events/event-types.md)).

VOD chat replay is available only through an undocumented endpoint, `kick.com/api/v2/channels/{channel_id}/messages?start_time=…`, read forward one time step at a time. [Enmn/KickApi](https://raw.githubusercontent.com/Enmn/KickApi/main/kickapi/kickapi.py) (MIT) wraps it. [tourist1159/kick-comment-fetcher](https://raw.githubusercontent.com/tourist1159/kick-comment-fetcher/main/kick_comment_fetch.py) shows it still working daily in October 2026. After an empty page it moves the clock 5 seconds forward. Otherwise it jumps to 1 second after the last message, waiting 1 second between requests. That script has no licence, so write a similar poller of about 100 lines rather than copying it. Then count messages per second to find bursts of "W", "LETS GO" and emote floods.

Because the replay endpoint could break without warning, also **log live chat during every stream**. There are two ways to do it:

- **Kick's official webhook**, received with [kickcom.py](https://github.com/PredaaA/kickcom.py) (MIT, which checks the webhook signatures). This is the safe route under Kick's rules, but it needs a public HTTPS address and an OAuth app.
- **Kick's unofficial Pusher websocket.** It needs no login and is used in [42 Python files on GitHub](https://github.com/search?q=%2232cbd69e4b950bf97679%22+chatrooms+language%3APython&type=code). It is easier to run inside a container, but it can change without notice.

Reading chat without logging in does not put Dylan's account at risk. Logging a bot in with his session cookies, as [kick-js](https://github.com/retconned/kick-js) does in write mode, could.

| Tool | Role | Licence | Status | Verdict |
|---|---|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | VODs and clips | Unlicense | VOD extractor broken; clips appear OK | Backup and clips |
| [streamlink](https://github.com/streamlink/streamlink) | Kick plugin that gets past Cloudflare | BSD-2 | Pushed Oct 2026 | Model for a Cloudflare fallback |
| [StreamKeep](https://github.com/SysAdminDoc/StreamKeep) | GUI app with a Kick chat websocket module | MIT | Sep 2026, 11 stars | Reference code only |
| [jonathanhecl](https://github.com/jonathanhecl/kick-vod-downloader), [siuramka](https://github.com/siuramka/KickDownloader), [kick-dl](https://github.com/juliogarciape/kick-dl) | Dedicated downloaders | MIT / MIT / GPL-3.0 | Inactive since 2023–2025 | Skip |
| [kickcom.py](https://github.com/PredaaA/kickcom.py) | Official API and webhook server | MIT | Sep 2026 | Live chat via webhook |
| [Enmn/KickApi](https://github.com/Enmn/KickApi) | Unofficial wrapper including chat replay | MIT | Nov 2025 | Reference for the replay poller |

## Duck with a speech detector; separate voice only for the seconds that make the edit

### Separating Dylan's voice from the slot audio

Real voice separation is good now, but slow on a CPU. The best open models are the RoFormer family, reached through [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) (MIT, release 0.47.0 in Aug 2026). They score about **12.4–12.9 dB** on vocal SDR, the standard measure of how cleanly a voice is pulled out. Demucs scores 10.8 dB with htdemucs_ft and 10.0 dB with htdemucs ([audio-separator README](https://raw.githubusercontent.com/nomadkaraoke/python-audio-separator/main/README.md)). All of those scores come from sung music, not shouting over slot music.

On CPU, Demucs takes **about 1.5 times the length of the audio**, and htdemucs_ft takes four times longer than that ([Demucs README](https://raw.githubusercontent.com/adefossez/demucs/main/README.md)). A 30-second window therefore costs roughly 45 seconds, more on a 4-vCPU box. No CPU timing has been published for the RoFormer models. Separating a whole three-hour VOD is out of the question.

The cheaper design gets most of the benefit. Silero VAD finds where Dylan is speaking in the mixed audio. Those regions drive ffmpeg's `sidechaincompress`, which turns one track down whenever a second track is active ([FFmpeg filter docs](https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/doc/filters.texi)). That costs seconds, not minutes.

Sometimes the edit needs the reverse: Dylan's voice pushed down under a big slot hit. For that, run audio-separator on just that 10–40 second window, save the stems, and key the voice track from the separated game stem. Two more fixes help the mix:

- **Sound-effect levels:** set them with pyloudnorm, 4 dB above the bed's measured loudness, rather than by raw volume.
- **Final loudness:** run ffmpeg's two-pass `loudnorm` with `-ar 48000`. Without it, the filter's dynamic mode raises the sample rate to 192 kHz.

| Tool | Licence | Status | CPU speed | Verdict |
|---|---|---|---|---|
| [Silero VAD](https://github.com/snakers4/silero-vad) + ffmpeg `sidechaincompress` | MIT / ffmpeg | Active | Seconds per clip | **Adopt for ducking** |
| [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | MIT | 0.47.0, Aug 2026 | Slow; no published figure | **Adopt for short windows** |
| [Demucs, maintained fork](https://github.com/adefossez/demucs) (v4.1.0) | MIT | Bug fixes only, "no new feature" | About 1.5x the audio length | Alternative |
| [DeepFilterNet](https://github.com/Rikorose/DeepFilterNet) | MIT/Apache-2.0 | Inactive for about 2 years | 10 min of audio in about 27 s on one core ([review](https://www.creativeainews.com/articles/deepfilternet-vs-rnnoise-vs-ffmpeg-noise-removal-2026/)) | Optional clean-up of a separated voice |
| [ClearerVoice-Studio](https://github.com/modelscope/ClearerVoice-Studio) | Apache-2.0 | Aug 2025 | Not measured | Optional |
| [Spleeter](https://pypi.org/project/spleeter/) | MIT | Needs Python below 3.12 | n/a | Blocked: the container runs Python 3.13 |

The Kim Mel-Band RoFormer model is one of audio-separator's top vocal models, but its home repo shows **no licence** ([GitHub](https://github.com/KimberleyJensen/Mel-Band-Roformer-Vocal-Model)). Check the licence of whichever model file gets used. Separation also does not reliably improve speech-to-text. One study found isolated vocals made most Whisper models worse ([Jam-ALT](https://arxiv.org/pdf/2408.06370)). Another found separation helped only as a guide to where speech starts and stops ([arXiv 2506.15514](https://arxiv.org/html/2506.15514v1)).

### Landing reveals on the music drop

No mature open-source tool detects "the drop". Every drop-detector repo found has 0 to 21 stars, for example [emjjkk/beat-detection](https://github.com/emjjkk/beat-detection) and [here-comes-the-drop](https://raw.githubusercontent.com/hPerezz/here-comes-the-drop/main/README.md). The practical recipe takes three steps:

1. **Find beats and downbeats** with **librosa** ([GitHub](https://github.com/librosa/librosa): ISC licence, version 1.0.0 from Aug 2026, needs Python 3.12 or later and so suits the container). **beat_this** works too ([README](https://raw.githubusercontent.com/CPJKU/beat_this/main/README.md): MIT for code and weights, with an 8.1 MB "small" model).
2. **Score each downbeat** by how much bass energy (below 150 Hz) and overall loudness jump from the 2–8 bars before it to the 1–2 bars after.
3. **Pick the strongest jump** after the first 15 seconds.

In the research container, librosa's beat tracking took 0.64 s on a 120-second track, after a one-off 14.1 s warm-up on its first call. That is the team's own measurement, not a published figure. Song beds come from a fixed library, so work out each drop once and save it in a small JSON file next to the song. Send low-confidence picks to the review page for Dylan to check.

| Tool | Licence | Status | Verdict |
|---|---|---|---|
| [librosa](https://github.com/librosa/librosa) | ISC | 1.0.0, Aug 2026 | **Adopt**; no download needed |
| [beat_this](https://github.com/CPJKU/beat_this) | MIT (code and weights) | 1.1.0, Apr 2026 | Optional upgrade; weight host blocked |
| [madmom](https://raw.githubusercontent.com/CPJKU/madmom/main/README.rst) | Code BSD; **models CC BY-NC-SA** | Last PyPI release 2018 | Avoid |
| [BeatNet](https://github.com/mjhydri/BeatNet) | CC BY 4.0 | Offline mode depends on madmom | Skip |
| [All-In-One](https://github.com/mir-aidj/all-in-one) | MIT | Inactive since May 2024; Python up to 3.11 only | Skip |
| [SongFormer](https://github.com/ASLP-lab/SongFormer) | CC BY 4.0 | GPU-oriented; no "drop" label | Skip |
| [Essentia](https://github.com/MTG/essentia) | **AGPL-3.0** | Active | Avoid |

## Picture quality: interpolate and upscale the crop, never the full frame

### Smooth slow motion

**RIFE** is the only AI frame-interpolator with published, workable CPU speeds. It runs through OpenVINO, Intel's engine for running AI models on CPUs. RIFE v4.4 reaches **about 14 fps at 1920x1088 on a 32-core server CPU** ([vs-mlrt wiki](https://github.com/AmusementClub/vs-mlrt/wiki/AMD-EPYC-Zen4)). It reaches **about 28 fps at 640x384 on a Core Ultra 7 laptop CPU** ([vs-mlrt wiki](https://github.com/AmusementClub/vs-mlrt/wiki/Intel-Core-Ultra-7-155H)).

Here is what that means for one segment. A 0.4x slow-mo of 4 seconds of 60 fps footage makes 600 output frames, about 360 of them invented. At full 1080p, on a box with a quarter to an eighth of that server's power, that works out to roughly 1.5–3 minutes per segment. A zoom crop is about 530x300 to 960x540 pixels, close to the laptop test size. On the crop, the same extrapolation drops the cost to tens of seconds. So **interpolate the crop, before zooming or upscaling**. These figures are estimates, and the project's container has only 4 vCPUs.

RIFE v4 can also make frames at any point between two real ones, not just the halfway point. That lets it lift the ~22 fps live-casino feeds or variable-rate phone footage straight to 60 fps.

There is one known risk. Interpolators can smear fixed text and card edges when large motion passes over them, and nobody has tested this on slot or blackjack screens. The fix is to copy fixed UI areas from the nearest real frame.

| Tool | Licence | Status | CPU fit | Verdict |
|---|---|---|---|---|
| RIFE models from [Practical-RIFE](https://github.com/hzwer/Practical-RIFE) (v4.25 recommended) | MIT | Pushed Aug 2026 | The PyTorch version needs Python ≤3.11 | Use the models through OpenVINO |
| [vs-mlrt](https://github.com/AmusementClub/vs-mlrt) RIFE ONNX via OpenVINO | GPL-3.0 (plugin code) | Active, Sep 2026 | Best documented CPU speed | **Adopt (medium effort)** |
| [rife-ncnn-vulkan](https://github.com/nihui/rife-ncnn-vulkan) / [TNTwise fork](https://github.com/TNTwise/rife-ncnn-vulkan) | MIT | Original stale since Jan 2024; fork Feb 2026 | Has a CPU mode; no speed figures | Simple command-line backup |
| [FILM](https://github.com/google-research/frame-interpolation) | Apache-2.0 | **Archived** | n/a | Avoid |
| [IFRNet](https://github.com/ltkong218/IFRNet), [EMA-VFI](https://github.com/MCG-NJU/EMA-VFI) | MIT / Apache-2.0 | Inactive since 2023–24 | No CPU build | Skip |
| ffmpeg `minterpolate` | ffmpeg | Built in | Uses one core only ([ffmpeg-devel](https://ffmpeg.org/pipermail/ffmpeg-devel/2022-March/294793.html)) | Skip |

### Upscaling phone recordings and zoomed crops

AI upscalers that invent detail are slow on a CPU. Compact Real-ESRGAN runs at about **2.6 fps on a 640x360 input** on a laptop CPU ([vs-mlrt wiki](https://github.com/AmusementClub/vs-mlrt/wiki/Intel-Core-Ultra-7-155H)). That is roughly 4 minutes for 10 seconds of zoomed 60 fps output, too much on top of everything else.

The fast options are the ESPCN and FSRCNN models in OpenCV's dnn_superres module, part of the opencv-contrib package. They take **about 12 ms per 768x512 image** at 4x. Their gain over plain bicubic resizing is modest: a PSNR sharpness score of 26.55 against 26.06 ([opencv_contrib dnn_superres](https://github.com/opencv/opencv_contrib/tree/4.x/modules/dnn_superres)). ArtCNN's smallest model runs at about 30 fps at 640x360 on CPU ([vs-mlrt wiki](https://github.com/AmusementClub/vs-mlrt/wiki/Intel-Core-Ultra-7-155H)).

The right choice depends on the footage:

- **Zoomed crops:** upscale 2x with ESPCN or FSRCNN, then finish with Lanczos resizing and a light sharpen. Upscale only the real source frames, before interpolation.
- **Phone screen recordings:** these are mostly UI text and flat graphics. Detail-inventing upscalers can produce wrong-looking characters, which is dangerous on numbers, so stay with ESPCN/FSRCNN or Lanczos plus sharpening. The 1008x2244 recordings already exceed the output size and need no upscaling.
- **Slot art:** it is flat and cartoon-like, so anime-tuned models (Real-CUGAN, ArtCNN, waifu2x) may suit it better than photo models. That is untested.

| Tool | Licence | Status | CPU fit | Verdict |
|---|---|---|---|---|
| [OpenCV dnn_superres](https://github.com/opencv/opencv_contrib/tree/4.x/modules/dnn_superres) (ESPCN/FSRCNN) | Apache-2.0 | Active | About 12 ms per image | **Adopt** |
| [Real-ESRGAN](https://github.com/xinntao/Real-ESRGAN) | BSD-3 | Inactive since Aug 2024 | About 2.6 fps at 640x360 | Very short clips only |
| [Real-ESRGAN-ncnn-vulkan](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan) | MIT (per README) | Inactive | No documented CPU mode | Skip |
| [realcugan-ncnn-vulkan](https://github.com/nihui/realcugan-ncnn-vulkan) | MIT | Inactive since 2023 | Has a CPU mode; no speed figures | Optional |
| [nunif (waifu2x)](https://github.com/nagadomi/nunif) | MIT | Very active | Slow models | Optional |
| [SwinIR](https://github.com/JingyunLiang/SwinIR) / [HAT](https://github.com/XPixelGroup/HAT) | Apache-2.0 | Inactive since 2024 | Impractical on CPU | Skip |

### Following cards being dealt

The practical choice is OpenCV's own trackers. **VitTrack** takes about **2 ms per frame on a 4-thread desktop i3** and gives a confidence score that shows when it has lost the target. It is Apache-2.0 ([opencv_zoo VitTrack](https://github.com/opencv/opencv_zoo/tree/main/models/object_tracking_vittrack)), but its model is now hosted on Hugging Face, which the container blocks. **CSRT** comes in OpenCV's contrib package and needs no model download. It is accurate but slower ([PyImageSearch](https://pyimagesearch.com/2018/07/30/opencv-object-tracking/)).

How to get a steady camera:

1. **Track something rigid and high-contrast**, such as a dealt card or the box around all the cards, not the hand.
2. **Run the tracker on a 960x540 copy of the frame**, and restart it whenever its confidence drops.
3. **Smooth the camera path with a One Euro filter**, a standard smoother for jittery tracking data. Tune it so the camera stays steady but keeps up with a fast deal. The [reference repo](https://github.com/casiez/OneEuroFilter) has no detected licence, and the algorithm is only a few lines long, so rewrite it rather than copy it.
4. **Use look-ahead.** Rendering happens offline, so the engine can smooth the path forwards and backwards, or mark where each card lands and ease between those points. That beats any frame-by-frame tracker for smoothness.

Following several cards and chips at once would need a card detector trained on labelled frames. The permissive choices are [YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) (Apache-2.0, exports to OpenVINO) or [RF-DETR](https://github.com/roboflow/rf-detr) in its Nano to Large sizes (Apache-2.0), plus [supervision's](https://github.com/roboflow/supervision) ByteTrack tracker (MIT). Three alternatives carry problems:

- **Licence:** [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) and [BoxMOT](https://github.com/mikel-brostrom/boxmot) are **AGPL-3.0**. [CoTracker](https://github.com/facebookresearch/co-tracker) is mostly **CC-BY-NC**, which rules it out for monetised content.
- **Speed:** [SAM 2](https://github.com/facebookresearch/sam2) and [EfficientTAM](https://github.com/yformer/EfficientTAM) are too slow on CPU for anything beyond occasional frames. EfficientTAM needs 261 ms per frame even on an iPhone 15 Pro Max ([paper](https://arxiv.org/html/2411.18933v1)).

### Auto-reframing 16:9 to 9:16

No maintained, permissively licensed reframer understands game footage:

- **Google's AutoFlip:** support ended on 1 Mar 2023 ([MediaPipe guide](https://developers.google.com/edge/mediapipe/solutions/guide)).
- **ClipsAI's `resize`:** follows whoever is talking, needs a Hugging Face token, and has been inactive since January 2024 ([ClipsAI](https://github.com/ClipsAI/clipsai)).
- **[Autocrop-vertical](https://github.com/kamilstanuch/Autocrop-vertical):** has no licence and is built on the AGPL YOLOv8.

Face-following reframers only help with the webcam box. They cannot tell where the action is inside a slot or blackjack window.

The Instagram layout is a 1080x830 panel over a blurred background, so it needs only a crop of about 1.3:1 from the game area. Three inputs can steer that crop: a saved layout per game, the amount of motion inside the game window (which catches reel spins, banners and deals), and the card tracker above. Keep the crop inside the game window and smooth it the same way as the card camera.

[OpenShorts](https://github.com/mutonby/openshorts) is worth borrowing one idea from. Its core is MIT, but its `cloud/` folder is under a commercial licence. It switches mode per scene between tracking, blurred background, split screen and screen recording, and its blurred-background mode matches Dylan's layout.

## Using all four CPU cores speeds renders about 1.8x; a new engine would not

The engine renders a 30-second, 60 fps edit (1,800 frames) in about 10 minutes, roughly 330 ms per frame. On 14 Oct 2026 the research team ran a timing test in the project's own 4-vCPU container. It used a synthetic 1080p60 clip, so the times are best cases.

Decoding cost **about 3.7 ms per frame**, and x264 encoding at the "medium" preset **about 32 ms per frame**. That leaves most of the 330 ms for the engine's own effects: motion-blur samples, radial zoom blur, and full-resolution compositing of the 9:16 panel and blurred background.

| Test: 300 frames of 1080p60 on 4 vCPU (team's own measurement) | Time |
|---|---|
| Decode only | 1.12 s |
| Decode and x264 medium encode | 9.63 s |
| Warp, RGB shift and blur as ffmpeg filters, x264 medium | 28.85 s |
| Same three effects in OpenCV, piped to x264 medium | 21.80 s |
| Same OpenCV chain in 4 processes, x264 medium | 18.56 s |
| Same OpenCV chain in 4 processes, x264 veryfast | **11.87 s** |

The test settles three points:

- **Faster decoders would not help.** Decord, torchcodec or VidGear could save about 1% at most.
- **Moving the virtual camera into ffmpeg filters would make it slower,** not faster.
- **The gains come from changing how hype_edit.py renders.**
  - Render each shot in its own process. The edit list is already split into shots, but effects like shake and count-up need a fixed random seed per frame so every process draws them the same way.
  - Use fewer motion-blur samples, blur at half resolution, reuse the blurred background within a shot, and run the radial blur on a smaller copy.
  - A faster encoder preset costs some quality per megabyte, which matters under the 29 MB cap, so measure before switching.

Profiling the real hype_edit.py effect by effect is the necessary first step. The table above comes from one synthetic test.

| Tool | Licence | Status | Verdict |
|---|---|---|---|
| [PyAV](https://github.com/PyAV-Org/PyAV) | BSD-3 | 19.0.1, Oct 2026 | Optional: cleaner encoding inside Python, small speed gain |
| [typed-ffmpeg](https://github.com/lucemia/typed-ffmpeg) | MIT | 4.5, Aug 2026 | Use instead of [ffmpeg-python](https://pypi.org/project/ffmpeg-python/), which has had no release since 2019 |
| [xfade-easing](https://github.com/scriptituk/xfade-easing) | MIT | 124 stars | **Adopt for transitions**: about 80 GL Transitions as ffmpeg `xfade` expressions with easing curves. The expression mode is 10–50x slower than native. |
| [auto-editor](https://github.com/WyattBlue/auto-editor) | Unlicense | Pushed Oct 2026 | Optional: trims dead air by loudness or motion before shot selection |
| [MoviePy](https://github.com/Zulko/moviepy) | MIT | No release since May 2025; "Maintainers wanted!" | Skip: its own README says it is slower than calling ffmpeg directly |
| [movis](https://github.com/rezoo/movis) | MIT | Inactive since 2023 | Borrow its layer and keyframe ideas only |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | Apache-2.0 | npm 0.8.157, 14 Oct 2026 | Best upgrade for the HTML-based leaderboard and overlays; "no per-render fees" |
| [Revideo](https://github.com/midrender/revideo) | MIT | 0.11.0, Jul 2026 | Alternative to HyperFrames |
| [Remotion](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md) | Custom company licence | Very active | Free only for individuals, non-profits and companies of up to 3 people; a draft 5.0 licence would count contractors ([PR #3750](https://github.com/remotion-dev/remotion/pull/3750)) |

Browser-based engines suit overlays, count-ups and the leaderboard. They can render these as transparent layers for the Python engine to lay over the footage. They do not suit camera moves on 60 fps stream footage. There, stepping through frames in headless Chrome on 4 vCPUs would almost certainly be slower than the current engine.

## Postiz leads open-source scheduling, but platform rules set the limits

Social HQ already holds the approval queue, so the question is what actually posts once Dylan approves.

[Postiz](https://github.com/gitroomhq/postiz-app) leads the open-source options. It is AGPL-3.0, has 37.2k stars and released v2.25.1 on 11 Oct 2026. It posts to X, Instagram, TikTok, YouTube and more, and has a public REST API. A script uploads the media, then creates a post as a draft, as scheduled, or to go out immediately ([API controller](https://raw.githubusercontent.com/gitroomhq/postiz-app/main/apps/backend/src/public-api/routes/v1/public.integrations.controller.ts)). The default limit is 30 API calls an hour ([docker-compose](https://raw.githubusercontent.com/gitroomhq/postiz-app/main/docker-compose.yaml)), plenty for a few posts a day.

Postiz is heavy to self-host: about nine containers, including Temporal, Elasticsearch, Postgres and Redis. It must run as an always-on, publicly reachable HTTPS service, because the platforms' login callbacks and Instagram's media fetch both need to reach it. That rules out the short-lived render container. Run it on a small always-on server, or use Postiz Cloud. The AGPL matters only if the Postiz code is modified and offered to others as a service.

The other schedulers each fall short somewhere:

- **[BrightBean Studio](https://github.com/brightbeanxyz/brightbean-studio)** (AGPL, Django) is lighter and has approval stages, but **no X support**.
- **[TryPost](https://github.com/trypostit/trypost)** (AGPL, Laravel) covers all four platforms but has only existed since January 2026.
- **[Mixpost](https://github.com/inovector/mixpost)** Lite (MIT) posts only to Facebook, X and Mastodon. Instagram, TikTok and YouTube need the paid Pro version ([comparison](https://www.blotato.com/blog/mixpost-vs-postiz)).

The lightest option skips a scheduler and has a timed job call the official APIs directly:

- **X:** [tweepy](https://github.com/tweepy/tweepy) or X's [xdk](https://github.com/xdevplatform/xdk).
- **Instagram Reels:** plain Graph API calls.
- **YouTube:** [google-api-python-client](https://github.com/googleapis/google-api-python-client).

The platforms' own rules matter more than the tool, because they apply to all of them:

| Platform | Rule for API posting | What it means for Dylan |
|---|---|---|
| X | Pay per post: **about $0.015, or $0.20 if the post contains a link** ([MediaNama](https://www.medianama.com/2026/02/223-x-developer-api-pricing-pay-per-use-model/), [bundle.social](https://bundle.social/blog/x-api-pricing-2026-costs-limits)); secondary sources | Cheap at a few posts a day; put the Kick link in a reply or the bio, not the caption |
| Instagram | Professional account; **100 API posts per 24 h**; video fetched from a public URL ([bundle.social](https://bundle.social/blog/instagram-graph-api)) | A private Google Drive link will not work; host the file publicly first |
| TikTok | Posts from unaudited apps stay **private** ([TikTok docs](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post)) | Post as private or draft and publish by hand, or wait out an audit |
| YouTube | Uploads from unverified API projects stay private until audited ([videos.insert](https://developers.google.cn/youtube/v3/docs/videos/insert)) | Same: make each upload public by hand, or get the project audited |

## Tools to avoid: licence traps, dead projects and account risks

In plain terms, each licence type has its own catch:

- **AGPL:** if the code is changed and offered to others as a service, or shared, its source must be published. Running an unmodified AGPL app such as Postiz privately is fine. Building AGPL code into hype_edit.py is the trap, especially if the engine might one day be sold or shared.
- **Non-commercial (NC):** these licences forbid use in monetised content. Dylan's edits promote a monetised channel, so treat them as commercial.
- **GPL-3.0** (pedalboard, matchering, vs-mlrt): fine for private internal use; obligations start only when the code is distributed.

This is general guidance, not legal advice.

| Avoid | Why | Use instead |
|---|---|---|
| [Ultralytics YOLO](https://github.com/ultralytics/ultralytics), [BoxMOT](https://github.com/mikel-brostrom/boxmot), [Segment-and-Track-Anything](https://github.com/z-x-yang/Segment-and-Track-Anything), [Autocrop-vertical](https://github.com/kamilstanuch/Autocrop-vertical) | AGPL-3.0 (Autocrop-vertical: no licence, built on Ultralytics) | YOLOX or RF-DETR with supervision; OpenCV trackers |
| [video2x](https://github.com/k4yt3x/video2x), [REAL-Video-Enhancer](https://github.com/TNTwise/REAL-Video-Enhancer), [upscayl](https://github.com/upscayl/upscayl), [ShaderFlow](https://github.com/BrokenSource/ShaderFlow) | AGPL-3.0, and mostly desktop apps | RIFE via OpenVINO; OpenCV dnn_superres |
| [Essentia](https://github.com/MTG/essentia), [whisper-timestamped](https://github.com/linto-ai/whisper-timestamped) | AGPL-3.0 | librosa; faster-whisper |
| [madmom](https://raw.githubusercontent.com/CPJKU/madmom/main/README.rst) models (and BeatNet offline, beat_this `--dbn`) | Models are CC BY-NC-SA (non-commercial); PyPI release from 2018 | librosa, or beat_this without `--dbn` |
| [CoTracker](https://github.com/facebookresearch/co-tracker), [Open-Unmix `umxl`](https://raw.githubusercontent.com/sigsep/open-unmix-pytorch/master/README.md), [Facebook Denoiser](https://github.com/facebookresearch/denoiser) | Non-commercial (Denoiser also archived) | OpenCV trackers; audio-separator |
| [Surya](https://pypi.org/project/surya-ocr/) weights | Free only below $5M funding or revenue | RapidOCR |
| [autoclipper](https://github.com/VadlapatiKarthik/autoclipper), [ffmpeg-gl-transition](https://github.com/transitive-bullshit/ffmpeg-gl-transition), [bilibili/ailab](https://github.com/bilibili/ailab), [kick-comment-fetcher](https://github.com/tourist1159/kick-comment-fetcher) | No licence: read for ideas, do not copy code | Write your own version |
| [facebookresearch/demucs](https://github.com/facebookresearch/demucs), [FILM](https://github.com/google-research/frame-interpolation), [stable-ts](https://github.com/jianfch/stable-ts), [cibere/kick.py](https://github.com/cibere/kick.py) | Archived | The adefossez Demucs fork; RIFE; faster-whisper; kickcom.py |
| [AutoFlip](https://developers.google.com/edge/mediapipe/solutions/guide), [ClipsAI](https://github.com/ClipsAI/clipsai), [ShortGPT](https://github.com/RayVentura/ShortGPT), [All-In-One](https://github.com/mir-aidj/all-in-one), [Decord](https://pypi.org/project/decord/), [editly](https://www.npmjs.com/package/editly) | Support ended, or dormant for 1–5 years | The custom crop path; the existing engine |
| [Spleeter](https://pypi.org/project/spleeter/), [Practical-RIFE's PyTorch code](https://github.com/hzwer/Practical-RIFE) | Will not run on the container's Python 3.13 (Spleeter needs below 3.12, Practical-RIFE 3.11 or lower) | audio-separator; RIFE ONNX via OpenVINO |
| [instagrapi](https://github.com/subzeroid/instagrapi), [TiktokAutoUploader](https://github.com/makiisthenes/TiktokAutoUploader), [tiktok-uploader](https://github.com/wkaisertexas/tiktok-uploader) | Unofficial posting clients: risk of account checkpoints and bans, especially from datacenter IPs. instagrapi's own README points business accounts to the official APIs. | Postiz or the official APIs |
| [Kickerz](https://github.com/KldIA6666/Kickerz), [omkarcloud/kick-scraper](https://github.com/omkarcloud/kick-scraper), [sarperavci/kick-unofficial-api](https://github.com/sarperavci/kick-unofficial-api), [kick-js](https://github.com/retconned/kick-js) write mode | View-botting, Cloudflare/Kasada-bypass tooling, or bot logins with session cookies | Read-only replay polling; the official webhook |

## Every AI model needs its files copied in, because the container blocks the download sites

During this research, the container's network proxy refused connections to the main model-hosting sites:

- huggingface.co and hf-mirror.com
- download.pytorch.org, the CPU-only PyTorch index
- dl.fbaipublicfiles.com
- cloud.cp.jku.at, which hosts beat_this's weights
- modelscope.cn
- openaipublic.azureedge.net, which hosts OpenAI's Whisper weights
- essentia.upf.edu

PyPI and raw.githubusercontent.com were reachable. A test load of faster-whisper failed with "ProxyError: 403 Forbidden" from Hugging Face. The container had 4 vCPUs, 15 GB of RAM, Python 3.13 and ONNX Runtime, and no PyTorch. These are direct observations from the research session, not published facts. They mean that **installing a package with pip is not enough** for any AI model in this report.

Some tools work as they are, because they need no separate model download:

- Silero VAD, whose model ships inside its pip package
- librosa, pyloudnorm and ffmpeg's filters
- OpenCV template matching and the CSRT and KCF trackers
- PySceneDetect

Everything else needs its model files placed in the container ahead of time:

- RapidOCR or PaddleOCR. Check where RapidOCR pulls its models from, since ModelScope and Hugging Face were both blocked.
- faster-whisper
- audio-separator and Demucs 4.1, whose models are hosted on Hugging Face
- beat_this
- VitTrack, now hosted on Hugging Face
- EfficientAT and PANNs
- the RIFE and Real-ESRGAN ONNX files

The OpenCV ESPCN and FSRCNN weight files live in GitHub repos, so they are probably fetchable, but that is unconfirmed. The missing PyTorch matters too. Tools that run on ONNX Runtime or OpenVINO avoid PyTorch entirely and should be preferred. Those include RapidOCR, Silero's ONNX build, faster-whisper's CTranslate2 engine and the vs-mlrt RIFE models.

Dylan has two ways to fix this:

1. **Allowlist the hosts.** Open the environment's settings (the cloud environment menu in the session's title bar, then **Edit**). Under Network access, add the needed hosts to Allowed domains and leave "Allow package managers" ticked ([steps](https://code.claude.com/docs/en/cloud-environments#network-access)).
2. **Copy the files in.** Download the model files once somewhere with access, and store them with the project or in an artifact store. They range from about 8 MB (beat_this small) to hundreds of MB; whisper small is 466 MiB in whisper.cpp form ([README](https://raw.githubusercontent.com/ggml-org/whisper.cpp/master/README.md)).

## Conclusion

Because no open-source slot win detector exists, the win reader would put Dylan's scanner ahead of every public clipping tool, not just bring it level. The tools needed are mature, free and light. What is missing is a few hundred labelled crops and templates from his own VODs. Labelling them is the real first task. It also tests the two biggest unknowns: how well OCR reads glowing slot digits, and whether "$" and "," come through.

One principle runs through every area: spend the expensive AI only on the seconds that make the edit. Interpolate and upscale the zoomed crop, separate voice only inside the clip window, tag reactions only around candidates the numbers already found, and work out song drops once per song. On a 4-vCPU box, that habit plus rendering on all four cores matters more than which repo gets picked. Most of what remains is setup: copying in model files or allowlisting their hosts, and checking licences.
