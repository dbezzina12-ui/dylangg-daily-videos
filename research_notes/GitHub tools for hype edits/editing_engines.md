# Open-source editing engines, motion-graphics frameworks, effect packs and auto-shorts generators for the hype-edit pipeline (as of 14 Oct 2026)

Method note: star counts, last-push dates, licences and archived flags come from the GitHub repository search API, queried on 2026-10-14. Release versions and dates come from the PyPI and npm registry JSON, queried the same day. The render-speed numbers labelled "local benchmark" were measured by this researcher inside the project's own cloud container on 2026-10-14. That container has 4 vCPUs, no GPU, ffmpeg 6.1.1 (Ubuntu build), OpenCV 5.0.0 and numpy 2.5.3. The test clip was a synthetic `testsrc2` clip, 1920x1080 at 60 fps, 5 s long (300 frames). Synthetic content encodes faster than real stream footage, so treat the absolute times as lower bounds and the ratios as the useful signal.

## Q1. Programmatic editing in Python: which libraries could replace parts of hype_edit.py or cut its ~10-minute CPU render?

### Takeaway
No Python library will replace the custom engine wholesale. The engine's per-frame virtual camera, motion blur and glitch work is already what MoviePy, movis and others do, and MoviePy's own README says it is slower than calling ffmpeg directly. Faster decoders (Decord, torchcodec) would not help either, because decoding is only about 1% of the frame budget. The realistic speed-ups are three: render frames in parallel (multiprocessing per segment), lighten the x264 settings or split the encode, and hand ffmpeg only the cheap whole-frame operations (`tmix`, `lut3d`, `xfade`). In the local test, ffmpeg's own `perspective`, `rgbashift` and `gblur` chain was slower than the same operations done in OpenCV.

### Cited Findings
**Library-by-library facts (stars / last push / latest release / licence)**
- **MoviePy**, https://github.com/Zulko/moviepy. 14,983 stars, last push 2026-08-26, MIT, not archived ([GitHub](https://github.com/Zulko/moviepy)). The latest PyPI release is 2.2.1 (2025-05-21), so there has been no release for about 17 months. The v2 line was 2.0.0 (2024-11-20), 2.1.0 (2024-11-24), 2.1.2 (2025-01-10) and 2.2.0/2.2.1 (2025-05-21) ([PyPI](https://pypi.org/project/moviepy/)).
- The MoviePy README says the project "recently upgraded to v2.0, introducing major breaking changes", that "v1 is no longer maintained", and "Maintainers wanted!". It also says the library "has only been kept afloat by the involvement of its maintainers" ([GitHub README](https://github.com/Zulko/moviepy)).
- The MoviePy README admits MoviePy is "slower than using ffmpeg directly due to heavier data import/export operations", because media is converted to numpy arrays ([GitHub README](https://github.com/Zulko/moviepy)).
- MoviePy 2.x uses Pillow for TextClip by default. ImageMagick is only needed for caption-style wrapping. This tip comes from a third-party skills page, not official docs ([skills.sh](https://skills.sh/terminalskills/skills/moviepy)).
- A search found no documented MoviePy-2-specific `write_videofile` regression. The general complaint is CPU-only slowness, for example a 720p24 job taking hours on PythonAnywhere ([PythonAnywhere forum](https://www.pythonanywhere.com/forums/topic/14752/)).
- **PyAV** (Pythonic bindings to FFmpeg's libav* libraries), https://github.com/PyAV-Org/PyAV. 3,309 stars, last push 2026-10-03, BSD-3-Clause ([GitHub](https://github.com/PyAV-Org/PyAV)). The latest PyPI `av` release is 19.0.1 (2026-10-03) ([PyPI](https://pypi.org/project/av/)).
- **ffmpeg-python**, https://github.com/kkroening/ffmpeg-python. 11,010 stars, Apache-2.0, last push 2024-08-04 ([GitHub](https://github.com/kkroening/ffmpeg-python)). The last PyPI release is 0.2.0 from 2019-07-06 ([PyPI](https://pypi.org/project/ffmpeg-python/)), so the project is effectively unmaintained.
- **typed-ffmpeg** ("Type-safe FFmpeg bindings for Python & TypeScript — filters, typing, and docs"). The repo now lives at https://github.com/lucemia/typed-ffmpeg: 1,163 stars, MIT, last push 2026-10-08 ([GitHub](https://github.com/lucemia/typed-ffmpeg)). PyPI 4.5 was released 2026-08-22 ([PyPI](https://pypi.org/project/typed-ffmpeg/)). The old `livingbio/typed-ffmpeg-playground` repo is archived ([GitHub search result](https://github.com/livingbio/typed-ffmpeg-playground)).
- **VidGear** ("High-performance cross-platform Video Processing Python framework"), https://github.com/abhiTronix/vidgear. 3,725 stars, Apache-2.0, last push 2026-05-18 ([GitHub](https://github.com/abhiTronix/vidgear)). PyPI 0.3.5 was released 2026-05-17 ([PyPI](https://pypi.org/project/vidgear/)).
- **Decord**, https://github.com/dmlc/decord. 2,525 stars, Apache-2.0, last push 2024-07-17 ([GitHub](https://github.com/dmlc/decord)). The last PyPI release is 0.6.0 from 2021-06-14 ([PyPI](https://pypi.org/project/decord/)), so it is inactive.
- **torchcodec** ("Media decoding and encoding for PyTorch: videos, images, and audio, on CPU and GPU"). The repo has moved to https://github.com/meta-pytorch/torchcodec: 1,184 stars, BSD-3-Clause, last push 2026-10-13 ([GitHub](https://github.com/meta-pytorch/torchcodec)). PyPI 0.17.0 was released 2026-09-30 ([PyPI](https://pypi.org/project/torchcodec/)).
- torchcodec's Dec 2024 launch post says it is "competitive on the CPU with seek-heavy use cases such as random and uniform sampling". It attributes the seek cost to frame-accurate seeking with an initial linear scan. The benchmark machine had 22 cores and the clip was 960x540 ([PyTorch blog](https://pytorch.org/?p=2820)).
- A torchcodec benchmark PR excludes TorchVision's pyav backend because it "doesn't support accurate seeks" ([torchcodec PR #330](https://github.com/meta-pytorch/torchcodec/pull/330/files)). One independent harness concluded that PyAV "is not the Linux performance answer" and that TorchCodec "is the most promising maintained library candidate" ([Cosmos video benchmark](https://docs.polli.ai/cosmos/video-benchmark/)). I found no published head-to-head CPU numbers.
- **VapourSynth** ("A video processing framework with simplicity in mind", a Python-scripted frame server), https://github.com/vapoursynth/vapoursynth. 2,114 stars, LGPL-2.1, last push 2026-10-12 ([GitHub](https://github.com/vapoursynth/vapoursynth)). PyPI release "81" came out 2026-10-04 ([PyPI](https://pypi.org/project/vapoursynth/)).
- **imageio-ffmpeg** (FFmpeg wrapper with a bundled binary), https://github.com/imageio/imageio-ffmpeg. 305 stars, BSD-2-Clause, last push 2025-01-16. Release 0.6.0 is dated 2025-01-16 ([GitHub](https://github.com/imageio/imageio-ffmpeg), [PyPI](https://pypi.org/project/imageio-ffmpeg/)).
- **movis**, https://github.com/rezoo/movis. Describes itself as a "Python library for video editing, presentation video generation, motion graphics, shader art coding". 485 stars, MIT, last push 2024-05-25 ([GitHub](https://github.com/rezoo/movis)). The last PyPI release is 0.7.1 from 2023-11-25 ([PyPI](https://pypi.org/project/movis/)), so it is inactive.
- movis is built around compositions and layers. Each layer has position, anchor, scale, rotation, opacity and blending mode, and the README claims "sub-pixel precision". Its other features ([GitHub README](https://github.com/rezoo/movis)):
  - keyframes with easing, and nested compositions
  - "Photoshop-level blending modes"
  - drop shadow, grow, blur and chromakey effects
  - text with multiple outlines
  - layers that can be plain functions returning `(H,W,4)` uint8 numpy arrays
  - caching of static layers and 1/2 or 1/4 draft rendering
  - no published benchmarks, and testing confirmed only on Python 3.9–3.11
- **mosaico** ("programmatic video composition framework with AI capabilities for Python"), https://github.com/FolhaSP/mosaico. 18 stars, GPL-3.0, last push 2025-12-03 ([GitHub](https://github.com/FolhaSP/mosaico)). PyPI 0.6.0 was released 2025-07-23 ([PyPI](https://pypi.org/project/mosaico/)).
- **MLT Multimedia Framework** (the engine under Shotcut and Kdenlive), https://github.com/mltframework/mlt. 1,862 stars, LGPL-2.1, last push 2026-10-12 ([GitHub](https://github.com/mltframework/mlt)).
- **libopenshot** (the OpenShot engine, C++ with Python bindings), https://github.com/OpenShot/libopenshot. 1,577 stars, LGPL-3.0, last push 2026-10-06 ([GitHub](https://github.com/OpenShot/libopenshot)).
- **skia-python** (Python binding to Skia), https://github.com/skia-python/skia-python. 329 stars, BSD-3-Clause, last push 2026-10-10 ([GitHub](https://github.com/skia-python/skia-python)). PyPI 144.0.post2 was released 2026-03-19 ([PyPI](https://pypi.org/project/skia-python/)). It is a candidate for antialiased text, glow and shadow overlays drawn into numpy buffers.
- Audio-side helpers, listed only because the engine has a mixer and loudnorm stage:
  - **spotify/pedalboard** (6,354 stars, **GPL-3.0**, 0.9.26 released 2026-10-07) ([GitHub](https://github.com/spotify/pedalboard), [PyPI](https://pypi.org/project/pedalboard/)).
  - **slhck/ffmpeg-normalize** ("Audio Normalization for Python/ffmpeg"). 1,538 stars. GitHub shows the licence as NOASSERTION while PyPI says MIT. Release 1.43.0 is dated 2026-10-14 ([GitHub](https://github.com/slhck/ffmpeg-normalize), [PyPI](https://pypi.org/project/ffmpeg-normalize/)).
  - **pyrubberband** (ISC, 0.4.0 released 2024-09-30) ([PyPI](https://pypi.org/project/pyrubberband/)).

**ffmpeg filter-graph building blocks (all present in the container's ffmpeg 6.1.1)**
- `xfade`, `perspective`, `gblur`, `rgbashift`, `lagfun`, `tmix`, `lut3d` and `chromashift` all report "slice threading supported". `zoompan` and `dblur` (directional blur) do not ([local `ffmpeg -h filter=…`](https://ffmpeg.org/ffmpeg-filters.html)).
- ffmpeg 6.1.1's built-in `xfade` transitions are: fade, wipeleft/right/up/down, slideleft/right/up/down, circlecrop, rectcrop, distance, fadeblack, fadewhite, radial, smoothleft/right/up/down, circleopen/close, vertopen/close, horzopen/close, dissolve, pixelize, diagtl/tr/bl/br, hlslice/hrslice/vuslice/vdslice, hblur, fadegrays, wipetl/tr/bl/br, squeezeh/v, zoomin, fadefast, fadeslow, hlwind/hrwind/vuwind/vdwind, coverleft/right/up/down, revealleft/right/up/down, and `custom` (expression-based) ([local `ffmpeg -h filter=xfade`](https://ffmpeg.org/ffmpeg-filters.html#xfade)).

**Local benchmark: 300 frames of 1080p60 on 4 vCPU, ffmpeg 6.1.1, x264 CRF 20 (method in the header note)**

| Test | Time | Per frame |
|---|---|---|
| Decode only (`ffmpeg -f null`) | 1.12 s | ~3.7 ms |
| Decode + x264 `-preset medium` | 9.63 s | ~32 ms |
| Decode + x264 `-preset veryfast` | 4.74 s | |
| ffmpeg-native `perspective` + `rgbashift` + `gblur` + x264 medium | **28.85 s** | |
| Same three ops in Python/OpenCV (`warpPerspective`, channel roll, `GaussianBlur`), raw-piped to x264 medium | **21.80 s** | 12.15 s of Python/OpenCV work (~40 ms/frame) |
| Same OpenCV chain, 4 worker processes, each piping its segment to its own x264 (`-threads 1`), preset medium | 18.56 s | |
| Same, 4 processes, preset veryfast | **11.87 s** | |
| ffmpeg `tmix=frames=4` (frame-blend motion blur) + scale + x264 medium | 6.42 s | |

### Inferences
- **Decode is not the bottleneck.** The engine renders 30 s at 60 fps (1,800 frames) in about 10 minutes, which is roughly 330 ms per frame. Decode costs about 4 ms per frame (local benchmark), so Decord, torchcodec or VidGear could save at most about 1%. Decord is also dormant since 2021, and torchcodec pulls in PyTorch. Neither is worth adopting for speed.
- **Encode is a real but secondary cost.** x264 medium costs about 32 ms per frame on synthetic 1080p60 with 4 vCPU, which is about 1 minute per pass for 1,800 frames. Real footage will be slower. Two options:
  - Run the first pass of the 2-pass encode with a faster preset, or encode per-segment in parallel. 4 processes with veryfast took 11.9 s against 21.8 s single-process with medium, roughly a 1.8x end-to-end gain on the test chain.
  - That would trade some quality per byte under the 29 MB cap.
- **The engine's own effects are the dominant cost.** The simple warp, RGB-shift and blur chain costs about 40 ms per frame, so the remaining ~290 ms per frame is most likely multi-sample motion blur, radial zoom blur, and full-res compositing of the 9:16 panel and blurred background.
  - The highest-leverage changes are algorithmic: fewer motion-blur sub-samples, blurring at half resolution, caching the blurred background per shot, and doing the radial blur on a downscaled copy.
  - The other lever is shot-level or segment-level multiprocessing. The EDL is already shot-based, so segments are natural units, but stateful effects (shake, count-up) need deterministic per-frame seeding.
- **Do not port the virtual camera to ffmpeg filters.** `perspective` and `gblur` were slower than OpenCV in the local test. `zoompan` is not slice-threaded and works on single-image inputs with integer-ish steps, so it suits stills, not 60 fps camera moves.
- **ffmpeg filters that do fit the engine:**
  - `tmix` or `lagfun` for cheap frame-blend motion blur and trails on high-fps sources
  - `lut3d` for colour grading (replacing the hand-written desaturation)
  - `xfade` for standard transitions in a final assembly pass
  - typed-ffmpeg (active, typed, MIT) for building those graphs. Prefer it to the dormant ffmpeg-python.
- **PyAV** (BSD, actively released) is the cleanest swap for the current ffmpeg subprocess pipes. It encodes numpy frames in-process and gives frame-accurate seeking control. Expect only small speed gains, since the pipe copy is a minor share of the cost. Its main benefit is control (per-segment encoders, audio frames in the same API).
- **MoviePy v2** would be a regression in both speed and control for this engine. It is numpy-in, numpy-out like the current engine, but adds overhead, has had no release since May 2025, and is short of maintainers. Its useful parts (TextClip via Pillow, CompositeVideoClip) are already covered by the engine's own code.
- **movis** has the closest mental model to an After Effects-style overlay layer (keyframes, blending modes, nested compositions). It is unmaintained since 2024, so borrow its ideas or code (MIT) rather than depend on it.
- **MLT and libopenshot** are mature, LGPL engines with Python bindings, but adopting either means rewriting the EDL into their timeline model. That is high integration difficulty for little gain over the custom engine.
- **VapourSynth** (LGPL, very active) only makes sense if you want a lazily evaluated, multithreaded frame server with its plugin ecosystem. It does not natively speak numpy-per-frame Python callbacks efficiently, so integration difficulty is high.
- **Licence flags in this group:**
  - pedalboard is GPL-3.0 and mosaico is GPL-3.0. Both are fine for internal use, but distribution of derived code triggers copyleft.
  - MLT, libopenshot and VapourSynth are LGPL.
  - Everything else listed is permissive.

### Gaps
- No published CPU benchmarks compare MoviePy v2, PyAV and OpenCV on full edit pipelines. The local numbers above are one synthetic micro-benchmark, not a profile of hype_edit.py. Profiling the real engine per effect is the necessary next step.
- I did not verify whether pedalboard exposes a pitch-preserving time-stretch, as a WSOLA replacement, in its current release.
- VidGear's actual throughput gain over raw ffmpeg pipes is not documented in sources I fetched.

## Q2. Code-driven motion graphics: Remotion, Revideo, Motion Canvas, Manim, editly/FFCreator, and newer HTML-to-video engines. Which suit templated hype edits and overlays, and which render headless on CPU?

### Takeaway
For the daily leaderboard, which is already HTML plus Playwright, the strongest options in 2026 are two:
- **HyperFrames** (HeyGen): Apache-2.0, extremely active, a headless Chrome and FFmpeg renderer with a catalog of transitions and overlays, and explicitly "no per-render fees or commercial-use thresholds".
- **Revideo**: MIT, with a headless `renderVideo()` and parallel workers.

**Remotion** is the most mature, but it uses a company licence. It is free for an individual or a for-profit with up to 3 people. Larger teams pay $25 per seat per month, or $0.01 per render with a $100/month minimum. A draft 5.0 licence would also count contractors toward team size.

Motion Canvas has no official headless CLI. Manim is math-oriented. editly and FFCreator are stale.

### Cited Findings
- **Remotion**, https://github.com/remotion-dev/remotion. 64,045 stars, last push 2026-10-14. GitHub shows its licence as NOASSERTION (custom licence) ([GitHub](https://github.com/remotion-dev/remotion)). npm `remotion` 4.0.535 was released 2026-10-12 ([npm](https://www.npmjs.com/package/remotion)).
- Remotion LICENSE.md, free licence eligibility: "an individual", "a for-profit organization with up to 3 employees", "a non-profit or not-for-profit organization", or someone evaluating the software ([LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)).
- Remotion LICENSE.md, permitted and forbidden use:
  - Free users may use it "non-commercially or commercially for the purpose of creating videos and images".
  - It is "not allowed to copy or modify Remotion code for the purpose of selling, renting, licensing, relicensing, or sublicensing your own derivate of Remotion."
  - Everyone else needs a Company License ([LICENSE.md](https://github.com/remotion-dev/remotion/blob/main/LICENSE.md)).
- Remotion company pricing, from a search summary of remotion.dev pricing pages; a direct fetch of remotion.dev failed with a DNS error ([remotion.dev pricing](https://www.remotion.dev/docs/license/pricing)):
  - "Creators" costs $25 per seat per month with no minimum.
  - "Automators" costs $0.01 per render with a $100/month minimum, covering code that calls `renderMedia()` or uses the Player.
  - Enterprise starts at $500/month.
  - "Free License Users may build automations without purchasing Renders."
- The Remotion 5.0 licence change is a **draft** PR (#3750), not merged, with last activity 9–10 Aug 2026 ([PR #3750](https://github.com/remotion-dev/remotion/pull/3750)):
  - Contractors would count toward team size.
  - The licence would be tied to new terms and conditions.
  - A follow-up commit prohibits operating a "bring-your-own-code rendering service".
- **HyperFrames**, https://github.com/heygen-com/hyperframes. "Write HTML. Render video. Built for agents." 63,358 stars, Apache-2.0, last push 2026-10-14 ([GitHub](https://github.com/heygen-com/hyperframes)). npm `hyperframes` 0.8.157 was released 2026-10-14 ([npm](https://www.npmjs.com/package/hyperframes)).
- HyperFrames rendering, from its README ([GitHub README](https://github.com/heygen-com/hyperframes)):
  - "The renderer seeks each frame in headless Chrome and encodes the result with FFmpeg" (Puppeteer).
  - It requires Node 22+ and FFmpeg, and is deterministic ("the same input produces the same video").
  - It renders locally or on AWS Lambda.
- HyperFrames animation adapters cover "GSAP, CSS animations, Lottie, Three.js, Anime.js, WAAPI, or a custom runtime". It ships a catalog of blocks for "transitions, overlays, captions, charts, maps, and effects" (e.g. `flash-through-white` shader transition, `instagram-follow` overlay) and a `shader-transitions` WebGL package. Licence text: "no per-render fees or commercial-use thresholds". The README gives no speed benchmarks and no Python API ([GitHub README](https://github.com/heygen-com/hyperframes)).
- **Revideo**, now at https://github.com/midrender/revideo (formerly redotvideo/revideo). 4,107 stars, MIT, last push 2026-07-15 ([GitHub](https://github.com/midrender/revideo)). npm `@revideo/core` and `@revideo/renderer` 0.11.0 were released 2026-07-10 ([npm](https://www.npmjs.com/package/@revideo/core)).
- Revideo describes itself as "a rendering engine for creating videos in code". Scenes are written in TypeScript, and it has a headless `renderVideo()` and a CLI render endpoint. It runs "anywhere Node and a headless browser run" including Cloud Run, and supports parallel rendering split across workers. It is "the engine behind Midrender". No benchmark numbers are published ([GitHub README](https://github.com/midrender/revideo)).
- **Motion Canvas**, https://github.com/motion-canvas/motion-canvas. 19,324 stars, MIT, last push 2026-07-02 ([GitHub](https://github.com/motion-canvas/motion-canvas)). The last npm `@motion-canvas/core` release is 3.17.2 from 2024-12-14, so there has been no release for about 22 months ([npm](https://www.npmjs.com/package/@motion-canvas/core)).
- Motion Canvas rendering setup:
  - Its FFmpeg exporter is a Vite plugin selected in the editor's Video Settings tab, and the docs call it "relatively new" ([Motion Canvas docs](https://motioncanvas.io/docs/rendering/video), [exporters repo](https://github.com/motion-canvas/exporters)).
  - A search found no official headless CLI. Community agent tooling still needs the editor open in a browser ([search summary](https://openskillindex.com/skills/videozero-skills-motion-canvas-agent)).
- **Manim**:
  - The community edition, https://github.com/ManimCommunity/manim, has 41,523 stars, MIT, last push 2026-10-12, and PyPI 0.22.0 released 2026-10-08 ([GitHub](https://github.com/ManimCommunity/manim), [PyPI](https://pypi.org/project/manim/)).
  - 3b1b/manim, https://github.com/3b1b/manim, has 95,066 stars, MIT, last push 2026-09-09. Its last PyPI `manimgl` release is 1.7.2 from 2024-12-13 ([GitHub](https://github.com/3b1b/manim), [PyPI](https://pypi.org/project/manimgl/)).
  - Both describe themselves as "Animation engine for explanatory math videos".
- **editly** ("Slick, declarative command line video editing & API", Node), https://github.com/mifi/editly. 5,525 stars, MIT, last push 2025-05-12 ([GitHub](https://github.com/mifi/editly)). The latest npm release is still 0.14.2 from 2022-12-23 ([npm](https://www.npmjs.com/package/editly)).
- editly features and requirements ([GitHub README](https://github.com/mifi/editly)):
  - gl-transitions support, and layer types for title, subtitle, slide-in-text, canvas, fabric and `gl` shaders
  - Ken Burns zoom, picture-in-picture, audio ducking and crossfades
  - a JSON5 spec and a "fast" preview mode
  - it relies on `headless-gl` for shader and canvas layers, is ESM-only, and is "maintained by one person"
- **FFCreator** ("A fast video processing library based on node.js"), https://github.com/tnfe/FFCreator. 3,164 stars, MIT, last push 2024-12-19, npm 7.5.8 released 2024-07-27, so it is inactive ([GitHub](https://github.com/tnfe/FFCreator), [npm](https://www.npmjs.com/package/ffcreator)).
- **Diffusion Studio Core**, https://github.com/diffusionstudio/core. A "browser based video compositing engine powered by WebCodecs". 1,247 stars, last push 2025-11-18, npm 4.0.3 released 2025-11-30 ([GitHub](https://github.com/diffusionstudio/core), [npm](https://www.npmjs.com/package/@diffusionstudio/core)).
  - Its licence is MPL-2.0, but free use requires keeping a "Made with Diffusion Studio" watermark unless you buy a key.
  - The README says to use Remotion if you "need to render videos server side" ([GitHub README](https://github.com/diffusionstudio/core)).
- **etro** ("Typescript video-editing library for the browser"), https://github.com/etro-js/etro. 1,151 stars, **GPL-3.0**, last push 2026-10-12, npm 0.14.1 released 2026-08-12 ([GitHub](https://github.com/etro-js/etro), [npm](https://www.npmjs.com/package/etro)).
- **WebVideoCreator** (Node, Puppeteer, Chrome and FFmpeg web-animation renderer), https://github.com/Vinlic/WebVideoCreator. 245 stars, Apache-2.0, last push 2024-01-05 ([GitHub](https://github.com/Vinlic/WebVideoCreator)).
- **timecut** (records smooth movies of web pages with JS animations), https://github.com/tungs/timecut. 654 stars, BSD-3-Clause, last push 2023-07-18 ([GitHub](https://github.com/tungs/timecut)).
- WebVideoCreator and timecut are both inactive.

### Inferences
- **Leaderboard video.** HyperFrames is the most natural upgrade. It uses the same paradigm as the existing Playwright renderer (HTML pages captured frame by frame in headless Chrome, then FFmpeg), but adds deterministic seeking, GSAP and Lottie adapters, and a ready catalog of transitions and social overlays. The Apache-2.0 licence has no thresholds, and the 0.8.x npm cadence shows very active development, though also a pre-1.0 API.
  - Revideo is the MIT alternative with a programmatic render API and parallel workers.
  - Both require Node in the container. Integration from Python is subprocess or HTTP: the Python side writes JSON data, and the Node CLI renders an MP4 or a transparent overlay.
- **Remotion** is legally usable for free by a solo creator or a company of 3 or fewer, even for automated commercial renders. The pipeline would need a paid licence if the business grows past 3 people, and the draft 5.0 licence would count contractors. That is a real risk for a creator who hires editors. Remotion's ecosystem, including captions, Lottie and audio visualisation, is the largest of the group.
- **Hype edits themselves** (camera moves on stream footage) are a poor fit for browser-based engines. Seeking 60 fps 1080p source video frame-by-frame in headless Chrome on a 4-vCPU box will very likely be slower than the numpy engine. Use these frameworks for overlays and templated cards instead: count-up numbers, banners and leaderboards, rendered as ProRes 4444 or PNG-sequence alpha overlays and composited by the Python engine or ffmpeg `overlay`.
- **Motion Canvas** has no official headless render and has had no npm release since Dec 2024. Prefer its headless fork lineage (Revideo).
- **Manim** is CPU-renderable (Cairo) and well maintained. Its strengths are math typesetting and vector animation, not hype-edit aesthetics, so it is low value here.
- **editly and FFCreator** encode a JSON-spec editing model similar to the EDL, with built-in gl-transitions. However, editly's npm release is from 2022, FFCreator's from 2024, and both rely on `headless-gl` native builds. They are not worth adopting in 2026, though editly's spec format is a useful reference.
- **Diffusion Studio and etro** are browser-only. Diffusion Studio adds a watermark requirement, and etro is GPL. Neither fits a headless Python cloud pipeline.

### Gaps
- No source gives CPU-only render speed for Remotion, Revideo or HyperFrames at 1080x1920. Benchmarking against the existing Playwright renderer would be needed.
- I could not fetch remotion.dev directly (DNS failure from this container), so the pricing figures come from a search-engine summary of remotion.dev pages, not a direct read.
- Whether headless Chrome WebGL (needed for HyperFrames shader transitions) works on CPU via SwiftShader in this container was not verified.

## Q3. Effect and transition collections: gl-transitions on CPU, glitch and datamosh tools, LUTs, shader runners

### Takeaway
The CPU-friendly way to get gl-transitions-style transitions into an ffmpeg pipeline is **xfade-easing** (MIT). It ports about 80 GL Transitions to ffmpeg `xfade` custom expressions and adds Penner easings, which makes the existing whip and glitch transitions far easier to vary.

The GLSL route needs an OpenGL context:
- ffmpeg-gl-transition is unlicensed and stale.
- ModernGL is MIT and active, with headless mode (unverified on this container).

Most datamosh tools are AVI or GUI hacks. Glitch effects are better done in numpy (as now) or via ffglitch.

No significant open LUT pack surfaced on GitHub. ffmpeg's `lut3d` combined with any `.cube` file is the integration path.

### Cited Findings
- **gl-transitions** ("The open collection of GL Transitions"), https://github.com/gl-transitions/gl-transitions. 2,151 stars, last push 2026-10-14. GitHub licence: NOASSERTION ([GitHub](https://github.com/gl-transitions/gl-transitions)). npm `gl-transitions` 1.75.0 was published 2026-10-14 ([npm](https://www.npmjs.com/package/gl-transitions)).
- gl-transitions API and licensing ([GitHub README](https://github.com/gl-transitions/gl-transitions)):
  - Each transition is GLSL `vec4 transition(vec2 uv)` using `getFromColor`, `getToColor`, `progress` and `ratio`, with uniforms for parameters.
  - Licences are declared per transition in each file header (the example shows MIT).
  - The npm package exposes all GLSL sources, and every merge to master auto-publishes an npm minor release.
- **ffmpeg-gl-transition** ("FFmpeg filter for applying GLSL transitions between video streams"), https://github.com/transitive-bullshit/ffmpeg-gl-transition. 720 stars, **no licence file** (GitHub licence: None), last push 2024-07-23 ([GitHub](https://github.com/transitive-bullshit/ffmpeg-gl-transition)).
- **xfade-easing**, https://github.com/scriptituk/xfade-easing. 124 stars, MIT ([GitHub README](https://github.com/scriptituk/xfade-easing)). Its README says:
  - It ports "roughly 80" GL Transitions to FFmpeg `xfade` custom expressions that "run per pixel on the CPU", and adds the Penner easings (quad through bounce, elastic, back) plus squareroot, cuberoot, flipelastic and flipback.
  - The expression mode works with stock ffmpeg but requires `-filter_complex_threads 1` and is typically "10–50 times slower" than native.
  - The optional patched `vf_xfade.c` build adds `easing` and `reverse` options and CSS easings. It renders most transitions in about 1 s at SD and about 2.5 s at HD on a 2018 Mac mini.
  - The patch targets only the latest stable FFmpeg, and the author distributes no binaries.
- **ModernGL** ("Modern OpenGL binding for Python"), https://github.com/moderngl/moderngl. 2,329 stars, MIT, last push 2026-10-07, PyPI 5.13.0 released 2026-10-07 ([GitHub](https://github.com/moderngl/moderngl), [PyPI](https://pypi.org/project/moderngl/)).
- **glslViewer** ("Console-based GLSL Sandbox for 2D/3D shaders"), https://github.com/patriciogonzalezvivo/glslViewer. 5,340 stars, BSD-3-Clause, last push 2026-09-27 ([GitHub](https://github.com/patriciogonzalezvivo/glslViewer)).
- **ShaderFlow** ("Modular shader engine designed for simplicity and speed", Python), https://github.com/BrokenSource/ShaderFlow. 148 stars, **AGPL-3.0**, last push 2026-10-10, PyPI 0.11.3 released 2026-07-31 ([GitHub](https://github.com/BrokenSource/ShaderFlow), [PyPI](https://pypi.org/project/shaderflow/)).
  - The README claims "Fastest video exporting not seen anywhere" via "TurboPipe", but this is unbenchmarked. It supports supersampling and audio-reactive scenes, and says commercial use is "allowed and encouraged through sponsorship tiers" ([GitHub README](https://github.com/BrokenSource/ShaderFlow)).
- **glitch-this** ("Glitchify images and GIF"), https://github.com/TotallyNotChase/glitch-this. 1,796 stars, MIT, last push 2024-06-06, PyPI 1.0.3 released 2024-03-11. It works on images and GIFs only ([GitHub](https://github.com/TotallyNotChase/glitch-this), [PyPI](https://pypi.org/project/glitch-this/)).
- **Datamosher-Pro** ("GUI based … automatic datamoshing application … 30+ cool glitch effects", Python), https://github.com/Akascape/Datamosher-Pro. 479 stars, MIT, last push 2026-04-24 ([GitHub](https://github.com/Akascape/Datamosher-Pro)).
  - It has a "Custom Script" mode for ffglitch scripts. Sources conflict on whether that mode is free or paid ([search summary of mirror](https://git.terata.org/eessppeelllloo/Datamosher-Pro/src/branch/Datamosher-Pro-master/Readme.md)).
- **tomato** ("avi index breaker", Python), https://github.com/itsKaspar/tomato. 166 stars, MIT, last push 2024-08-04 ([GitHub](https://github.com/itsKaspar/tomato)).
- Other datamosh tools ([GitHub search](https://github.com/search?q=datamosh&type=repositories)):
  - **supermosh**, https://github.com/supermosh/supermosh.github.io. 376 stars. Datamosh in the browser.
  - **moshpit**, https://github.com/CrushedPixel/moshpit. 132 stars. Go command-line datamoshing tool built on ffmpeg.
  - **you-can-datamosh-on-linux**, https://github.com/happyhorseskull/you-can-datamosh-on-linux. 90 stars. Python script.
  - **KinoDatamosh**, https://github.com/keijiro/KinoDatamosh. 539 stars. Unity-only.
  - **GlitchNodes**, https://github.com/pxl-pshr/GlitchNodes. 76 stars. ComfyUI glitch and dither nodes.
- ffglitch-based Python wrappers (mosh.py, vector_motion.py) drive ffglitch's `ffedit` and `ffgac` with a custom JavaScript that rewrites motion vectors. The output is MPG and may need re-encoding ([search summary](https://git.terata.org/eessppeelllloo/datamoshing)).
- LUT tooling:
  - **pycubelut** ("Tool for Applying Adobe Cube LUTs to Images"), https://github.com/yoonsikp/pycubelut. 108 stars ([GitHub search](https://github.com/yoonsikp/pycubelut)).
  - **pillow-lut-tools**, https://github.com/homm/pillow-lut-tools. 58 stars, MIT, last push 2025-09-02 ([GitHub](https://github.com/homm/pillow-lut-tools)).
  - ffmpeg's built-in `lut3d` filter is slice-threaded ([local ffmpeg -h](https://ffmpeg.org/ffmpeg-filters.html#lut3d)).
  - A GitHub search for LUT `.cube` repos with more than 100 stars returned only pycubelut.

### Inferences
- **Best CPU transition upgrade:** generate xfade-easing expressions (or apply its native patch to a self-built ffmpeg) to get about 80 extra transitions with easing curves. Use them on short (≤0.3 s) transition windows in a final assembly pass.
  - At about 2.5 s per HD transition natively, or 10–50x that in expression mode, a hype edit with 10 transitions is cheap natively and noticeably costly in expression mode.
  - Integration difficulty is low (ffmpeg filter strings).
  - Alternatively, port favourite gl-transitions GLSL to numpy or OpenCV by hand. The API is a pure function of uv and progress, so many (zoom, directional warp, crosshatch, glitch-displace) are only 10–30 lines of vectorised numpy.
- **GLSL on CPU** would mean ModernGL with an EGL or Mesa llvmpipe headless context, rendering gl-transitions shaders to numpy. This is plausible but not verified here.
  - ffmpeg-gl-transition has no licence, so legally it should not be copied, and it needs a custom ffmpeg build. Avoid it.
- **ShaderFlow** is AGPL-3.0: usable internally, but any network-served derivative triggers source disclosure. glslViewer (BSD) is a shader sandbox rather than a compositor.
- **Glitch.** The engine's numpy pixel-band and RGB-split glitch already covers what glitch-this does (images only). Real codec-level datamosh (I-frame removal, P-frame bloom) needs ffglitch or AVI-index tools (tomato, moshpit). It is best applied as a pre-rendered transition clip, because it breaks frame-accurate seeking. Datamosher-Pro is a GUI wrapper and is not suitable for headless automation.
- **Colour.** Replace the custom desaturation with `.cube` LUTs applied via ffmpeg `lut3d` in the final encode, or via pillow-lut-tools or pycubelut on numpy frames. LUT packs must be sourced elsewhere, since no notable OSS LUT pack exists on GitHub per this search.

### Gaps
- I did not verify gl-transitions' total transition count or the exact licence mix across files.
- I did not test ModernGL headless EGL on this container (no GPU, possible missing Mesa EGL libs).
- I did not test ffglitch itself, so its current version, licence and scripting languages are unverified (ffglitch is distributed from ffglitch.org, not GitHub).
- I found no reputable CPU benchmark of gl-transitions via headless-gl or llvmpipe.

## Q4. Automatic short-form generators: what is worth borrowing (silence cutting, transcript-based clip selection, captions, reframing)?

### Takeaway
None of these replaces the hype-edit renderer, since they target talking-head clipping. Three parts are worth borrowing:
- **auto-editor** (Unlicense, very active) for audio-loudness and motion dead-space cutting, and for exporting cut lists to NLE timelines. It is the most mature and easiest to drive from Python as a CLI.
- **OpenShorts** (MIT core) for its reframing-mode taxonomy (track, blurred background, split, screencast) and its CPU-only Docker path.
- **FunClip** (MIT, active) for transcript and LLM-driven clip selection with SRT output.

ClipsAI and ShortGPT are stale.

### Cited Findings
- **auto-editor**, https://github.com/WyattBlue/auto-editor. 5,513 stars, **Unlicense**, written in Nim, last push 2026-10-12 ([GitHub](https://github.com/WyattBlue/auto-editor)). The last PyPI release is 29.3.1 from 2025-11-04, which suggests distribution has moved to the binaries and installers at auto-editor.com ([PyPI](https://pypi.org/project/auto-editor/)).
- auto-editor features ([GitHub README](https://github.com/WyattBlue/auto-editor)):
  - It cuts by audio loudness (`--edit audio:threshold=0.04` is the default) or motion (`motion:threshold=0.02`), and the two can be combined with `(or …)`.
  - `--margin` defaults to 0.2 s.
  - It exports to Premiere, Resolve, Final Cut Pro, Shotcut, Kdenlive and clip sequences.
- **ClipsAI**, https://github.com/ClipsAI/clipsai. 549 stars, MIT, last push 2024-01-17, PyPI 0.2.1 released 2024-01-15, so it is inactive ([GitHub](https://github.com/ClipsAI/clipsai), [PyPI](https://pypi.org/project/clipsai/)).
  - It is "designed for audio-centric, narrative-based videos".
  - It transcribes with WhisperX (word-level timestamps), then `ClipFinder` picks clips from the transcript.
  - `resize()` uses Pyannote speaker diarization (with a HuggingFace token) to reframe 16:9 to 9:16 ([GitHub README](https://github.com/ClipsAI/clipsai)).
- **AI-Youtube-Shorts-Generator**, now at https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator. A search for the SamurAIGPT path returned this repo instead. It has 5,341 stars, MIT, and last push 2026-10-11 ([GitHub](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator)).
  - It is an "Open-source alternative to Opus Clip … LLM highlight detection, Whisper transcription, and auto vertical cropping" ([GitHub](https://github.com/Anil-matcha/AI-Youtube-Shorts-Generator)).
- **ShortGPT** ("Experimental AI framework for youtube shorts / tiktok channel automation"), https://github.com/RayVentura/ShortGPT. 8,028 stars, MIT, last push 2025-02-10, so it has been inactive for about 20 months ([GitHub](https://github.com/RayVentura/ShortGPT)).
- **FunClip**, https://github.com/modelscope/FunClip. 6,393 stars, MIT code, last push 2026-10-08 ([GitHub](https://github.com/modelscope/FunClip)).
  - FunASR Paraformer-Large ASR, Chinese by default with an English model via `-l en`.
  - CAM++ speaker IDs as clip targets, and LLM-based clip selection.
  - SRT export, with subtitles burned via Pillow.
  - A Gradio UI plus a CLI (`funclip/videoclipper.py`).
  - Recent releases: v2.2.0 (2026-08-30) and v2.2.1 (2026-09-01) ([GitHub README](https://github.com/modelscope/FunClip)).
- **OpenShorts**, https://github.com/mutonby/openshorts. It is a fork of kamilstanuch/Autocrop-vertical, so it is absent from default GitHub search results, and the page snapshot shows about 6.5k stars ([GitHub README](https://github.com/mutonby/openshorts)). Licence: **MIT core, but the `cloud/` directory is under a source-available "OpenShorts Commercial License"** ([GitHub README](https://github.com/mutonby/openshorts)).
- OpenShorts pipeline ([GitHub README](https://github.com/mutonby/openshorts)):
  - Gemini picks 3–15 moments of 15–60 s from transcript and scene boundaries.
  - Per-scene reframe modes are TRACK (MediaPipe + YOLOv8 face tracking), GENERAL (blurred background), SPLIT (two speakers stacked) and SCREENCAST.
  - faster-whisper provides word-level burned captions, and FFmpeg renders.
  - The default Docker image is CPU-only, and an 8-minute video takes "about 5-8 minutes on CPU".
- **MoneyPrinterTurbo** ("Generate HD short videos from a topic or keyword"), https://github.com/harry0703/MoneyPrinterTurbo. 130,761 stars, MIT, last push 2026-10-14 ([GitHub](https://github.com/harry0703/MoneyPrinterTurbo)).
- **captacity** ("Add Automatic Captions to YouTube Shorts with AI"), https://github.com/unconv/captacity. 139 stars, MIT, last push 2024-06-07 ([GitHub](https://github.com/unconv/captacity)).

### Inferences
- **auto-editor** is the most directly useful of these for this pipeline. It can be driven by subprocess on raw stream VODs to strip dead air before shot selection, using either its loudness or its motion threshold. Its timeline export can then be translated into the EDL JSON. The Unlicense is the most permissive licence available. Integration difficulty is low: a CLI that outputs a cut list.
- **Reframing.** The 9:16 layout is already a fixed panel with a blurred background and a banner, which matches OpenShorts' GENERAL mode. Borrowing its per-scene mode switch (TRACK, GENERAL or SPLIT) is a design idea rather than a dependency. Face tracking is out of scope here, as other researchers cover object tracking.
- **Captions.** FunClip (Pillow subtitle burn plus SRT), OpenShorts (faster-whisper word timings) and captacity (stale) show the standard recipe: word-level ASR timestamps, then per-word styled text. The engine's text system (slam-in, glow, shake) could consume such word timings directly.
- **Transcript-based clip selection** (ClipsAI, FunClip, AI-Youtube-Shorts-Generator, OpenShorts) is designed for speech-heavy content. Slot and stream hype moments are driven by on-screen numbers and audio spikes, which are covered by other researchers, so this is low value except for talking-segment clips.
- **Avoid as dependencies:** ClipsAI (dead since Jan 2024), ShortGPT (dead since Feb 2025), and the OpenShorts `cloud/` code (commercial licence). MoneyPrinterTurbo is a stock-footage-plus-TTS generator and not relevant beyond its MoviePy assembly code.

### Gaps
- I could not confirm whether SamurAIGPT/AI-Youtube-Shorts-Generator was transferred to Anil-matcha or is a separate repo. A search for the name returned only the Anil-matcha repo.
- OpenShorts' exact star count and last-commit date came from a page snapshot, not the API. GitHub search excludes forks by default.
- I found no CPU timing data for auto-editor or FunClip on 1080p60 inputs.
