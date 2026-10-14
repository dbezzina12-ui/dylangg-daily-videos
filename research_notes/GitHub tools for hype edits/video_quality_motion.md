# Video quality and motion tools (CPU-only) for the hype-edit pipeline: frame interpolation, upscaling, object tracking, auto-reframing

Method note: star counts, last-push dates, archived flags and license IDs were all pulled from the GitHub repository search API on 2026-10-14. "Pushed" is the date of the last push to any branch, which is usually close to the last commit. A license of "None" or "NOASSERTION" means GitHub could not detect a standard license. Treat those as all-rights-reserved until the LICENSE file is checked. Speed numbers are given only where a source reports them. CPU-only numbers are rare, and the gaps are listed under each question.

## Q1. Frame interpolation on CPU (RIFE, FILM, IFRNet, EMA-VFI, GMFSS, ffmpeg minterpolate, OpenVINO/ONNX builds): which gives clean 2-4x slow-mo on game UIs and cards at acceptable CPU speed?

### Takeaway
RIFE v4.x is the only learned interpolator with a documented, usable CPU speed. Run through OpenVINO, RIFE v4.4 does about 14 fps at 1920x1088 on a 32-core Zen4 server and about 28 fps at 640x384 on a Core Ultra 7 155H laptop CPU (vs-mlrt wiki). That is fast enough for 0.33-0.6x slow-mo segments within the 10-minute budget, especially if you interpolate only the zoom crop. FILM is archived. GMFSS, EMA-VFI and IFRNet have no CPU builds or CPU numbers. ffmpeg minterpolate is single-threaded and slow, and its output is cruder than RIFE's.

### Cited Findings
**RIFE family**
- **hzwer/Practical-RIFE** (https://github.com/hzwer/Practical-RIFE): the maintained "practical" RIFE model line. MIT. 1,029 stars, pushed 2026-08-27, active — [GitHub](https://github.com/hzwer/Practical-RIFE)
  - The newest listed models are 4.26 (2024-09-21) and 4.25.lite (2024-10-20). The README says "it is recommended to choose 4.25 by default for most scenes" and that 4.25 "anime scenes have been significantly improved." Every version has a "lite" variant with lower compute cost — [Practical-RIFE README](https://github.com/hzwer/Practical-RIFE)
  - `inference_video.py` options: `--multi` (2/4x), `--exp`, `--fps`, `--scale` (0.5 recommended for 4K), `--UHD`, `--montage`. Requires Python <= 3.11. The README gives no CPU statement or speed figures and has no notes on UI or text artifacts — [Practical-RIFE README](https://github.com/hzwer/Practical-RIFE)
- **hzwer/ECCV2022-RIFE** (https://github.com/hzwer/ECCV2022-RIFE): the paper repo. MIT. 5,612 stars, pushed 2025-09-10. Its README claims 30+ fps for 2x 720p on a 2080Ti GPU and gives no CPU figure (this claim was seen via a search-result summary of the README, not read directly) — [GitHub](https://github.com/hzwer/ECCV2022-RIFE)
- **nihui/rife-ncnn-vulkan** (https://github.com/nihui/rife-ncnn-vulkan): a C++ ncnn/Vulkan CLI. MIT. 1,109 stars, last push 2024-01-02, stale for about 2.5 years. Bundled models go up to rife-v4.6. `-g -1` selects CPU, `-s` sets an arbitrary timestep (0-1), `-n` sets the target frame count, `-u` turns on UHD mode, and `-j load:proc:save` sets thread counts. No speed numbers are given — [rife-ncnn-vulkan README](https://github.com/nihui/rife-ncnn-vulkan)
- **TNTwise/rife-ncnn-vulkan** (https://github.com/TNTwise/rife-ncnn-vulkan): a maintained fork. MIT. 65 stars, pushed 2026-02-05. It is the ncnn backend used by TNTwise's REAL-Video-Enhancer — [GitHub](https://github.com/TNTwise/rife-ncnn-vulkan)
- **AmusementClub/vs-mlrt** (https://github.com/AmusementClub/vs-mlrt): VapourSynth plugins that ship ONNX models for RIFE, waifu2x, DPIR, RealESRGANv2/v3, Real-CUGAN, SCUNet and ArtCNN. Backends include **vsov (OpenVINO, "pure CPU" and Intel GPU)** and **vsort (ONNX Runtime CPU/CUDA/CoreML)**, plus TensorRT, ncnn and MIGraphX. GPL-3.0. 484 stars, pushed 2026-09-25, active — [vs-mlrt README](https://github.com/AmusementClub/vs-mlrt)
  - **CPU benchmark (OV_CPU, vs-mlrt v13.1, Zen4 Genoa 32C/64T @3.4 GHz, num_streams=1, num_threads=64, 1920x1080 input): RIFE v4.4 (implementation=1, 1920x1088) = 14.3 fps FP32 / 21.5 fps BF16** — [vs-mlrt wiki: AMD EPYC Zen4](https://github.com/AmusementClub/vs-mlrt/wiki/AMD-EPYC-Zen4)
  - **CPU benchmark (OpenVINO 2024.1, Core Ultra 7 155H CPU, FP32): RIFE v4.4 at 640x384 = 27.96 fps.** The same chip's iGPU does 50.96 fps — [vs-mlrt wiki: Intel Core Ultra 7 155H](https://github.com/AmusementClub/vs-mlrt/wiki/Intel-Core-Ultra-7-155H)
- **HolyWu/vs-rife** (https://github.com/HolyWu/vs-rife): a PyTorch RIFE function for VapourSynth. MIT. 153 stars, pushed 2026-05-10 — [GitHub](https://github.com/HolyWu/vs-rife)
- SVP's RIFE requirements table only lists GPU tiers for real-time 1080p at 48 fps, for example ">= RTX 3070" generic and ">= RTX 2060" with TensorRT. No CPU tier exists — [SVP wiki](https://www.svp-team.com/wiki/RIFE_AI_interpolation)
- Anecdote: an SVP forum user says RIFE "produces way too many artifacts for live content" unless the content is mainly anime. This is a user opinion about films, not about game UIs — [SVP forum](https://www.svp-team.com/forum/viewtopic.php?pid=87861)

**FILM (Google)**
- **google-research/frame-interpolation** (https://github.com/google-research/frame-interpolation): FILM ("Frame Interpolation for Large Motion", ECCV 2022). Apache-2.0. 3,153 stars. **Archived; last push 2024-08-10.** It is TensorFlow-based — [GitHub](https://github.com/google-research/frame-interpolation)
- **dajes/frame-interpolation-pytorch** (https://github.com/dajes/frame-interpolation-pytorch): a PyTorch port of FILM. Apache-2.0. 185 stars, last push 2023-12-24 (inactive) — [GitHub](https://github.com/dajes/frame-interpolation-pytorch)
- Practical-RIFE 4.17 added "a gram loss from FILM", which means FILM's large-motion ideas partly live on in RIFE — [Practical-RIFE README](https://github.com/hzwer/Practical-RIFE)

**IFRNet / EMA-VFI / GMFSS**
- **ltkong218/IFRNet** (https://github.com/ltkong218/IFRNet), CVPR 2022: MIT. 348 stars, last push 2024-02-19 (inactive). The README says time and FLOPs are "measured on 1280 x 720", but the numbers are only in an image. Demos cover 2x and 8x. Arbitrary timestep is not stated — [IFRNet README](https://github.com/ltkong218/IFRNet)
- **MCG-NJU/EMA-VFI** (https://github.com/MCG-NJU/EMA-VFI), CVPR 2023: Apache-2.0. 503 stars, last push 2023-05-29 (inactive). It supports "fixed- and arbitrary-timestep interpolation" and has `ours` and `ours_small` variants plus `demo_Nx.py`. Runtime is shown only in an image (figs/time.png), and no ONNX or ncnn build exists — [EMA-VFI README](https://github.com/MCG-NJU/EMA-VFI)
- **98mxr/GMFSS_Fortuna** (https://github.com/98mxr/GMFSS_Fortuna): GMFlow plus softmax-splatting interpolation (anime-focused). MIT. 82 stars, pushed 2026-01-27. **HolyWu/vs-gmfss_fortuna** is MIT with 20 stars and was last pushed 2023-04-08 — [GitHub](https://github.com/98mxr/GMFSS_Fortuna); [GitHub](https://github.com/HolyWu/vs-gmfss_fortuna)

**ffmpeg minterpolate**
- A 2022 ffmpeg-devel thread asks for multi-threading in minterpolate. Users report that it runs on a single core — [ffmpeg-devel 2022-03](https://ffmpeg.org/pipermail/ffmpeg-devel/2022-March/294793.html)
- A 2019 user found `mc_mode=aobmc` "very slow" and `mi_mode=blend` faster but cruder. The usual high-quality string is `mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1` — [ffmpeg-user 2019-07](https://ffmpeg.org/pipermail/ffmpeg-user/2019-July/044777.html)
- Splitting the video into chunks and running parallel jobs breaks at the chunk seams, because the transition between chunks also needs interpolation — [Level1Techs forum](https://forum.level1techs.com/t/converting-videos-to-60-fps-with-ffmpeg/223600)
- The filter has no GPU path. Doom9 users recommend SVPflow or MVTools instead. SVPflow is faster but produces more artifacts, and MVTools is slower — [Doom9](https://forum.doom9.org/showthread.php?p=1958483)

**All-in-one apps (mostly GPU-oriented; licence flags)**
- **k4yt3x/video2x** (https://github.com/k4yt3x/video2x): an ML upscaling and interpolation framework. **AGPL-3.0.** 22,240 stars, pushed 2026-03-07 — [GitHub](https://github.com/k4yt3x/video2x)
- **TNTwise/REAL-Video-Enhancer** (https://github.com/TNTwise/REAL-Video-Enhancer): an interpolation, upscaling and denoising app. **AGPL-3.0.** 2,326 stars, pushed 2026-09-02 — [GitHub](https://github.com/TNTwise/REAL-Video-Enhancer)
- **n00mkrad/flowframes** (https://github.com/n00mkrad/flowframes): a Windows GUI using RIFE (CUDA/ncnn) and DAIN. **GPL-3.0.** 2,062 stars, pushed 2026-05-20. Windows-only, so it does not fit a Linux container — [GitHub](https://github.com/n00mkrad/flowframes)
- **styler00dollar/VSGAN-tensorrt-docker** (https://github.com/styler00dollar/VSGAN-tensorrt-docker): VapourSynth with SR and interpolation models. BSD-3. 360 stars, pushed 2026-06-22. **TensorRT/GPU only** — [GitHub](https://github.com/styler00dollar/VSGAN-tensorrt-docker)

### Inferences
- **Speed estimate for this pipeline:** A 0.4x slow-mo of 4 s of 60 fps source gives 10 s (600 frames) of output, of which about 360 are synthesized. At the Zen4 rate (14.3 fps at 1080p) that is about 25 s. If the cloud container has about 1/4 to 1/8 of that compute (8-16 vCPU), expect roughly 2-4 fps at 1080p, or 1.5-3 min per slow-mo segment. This is extrapolated from the vs-mlrt tables, not measured.
- **Interpolate the crop, not the full frame.** A 2-3.6x zoom crop of 1080p is about 530x300 to 960x540 px, which is near the 640x384 case that runs at about 28 fps on a laptop CPU. Do the interpolation before the zoom/upscale step. That should keep RIFE costs to seconds per segment.
- **For the ~22 fps live-casino feeds,** RIFE v4.x arbitrary timesteps (`-s` in rife-ncnn-vulkan, or calling the v4 model with any `timestep` in Python) let the engine map 22 to 60 fps or VFR phone footage to 60 fps directly, rather than only 2x/4x.
- **Static HUD/UI text and card faces:** flow-based interpolators (DIS, minterpolate, RIFE) can smear or ghost text and card edges when large motion crosses them. No source tested this on slot or blackjack UIs, so it is a known risk with no published evidence. A practical mitigation is to mask static UI regions, either copying them from the nearest real frame or blending, and to interpolate only the moving region.
- **Integration difficulty with Python + OpenCV + ffmpeg:**
  - Practical-RIFE (PyTorch, CPU device): medium. Copy `train_log` and the model class and call `model.inference(img0, img1, timestep)` on numpy frames. Watch the Python <= 3.11 pin.
  - vs-mlrt RIFE ONNX models via `openvino` or `onnxruntime` Python without VapourSynth: medium-high. You need to reproduce its padding to multiples of 32 or 64 (e.g. 1920x1088) and its input layout.
  - rife-ncnn-vulkan CLI: low-medium (frames on disk to frames out), but its models stop at v4.6.
  - Of the three, OpenVINO on CPU is the most likely fastest.
  - ffmpeg minterpolate: trivial to use but slow and lower quality. It offers little over the existing DIS path.
- FILM, GMFSS, EMA-VFI and IFRNet are not recommended. FILM is archived, and the other three are research code with no CPU or ONNX path and heavier models. GMFSS is also anime-tuned.

### Gaps
- I found no published CPU fps for Practical-RIFE PyTorch on CPU, for rife-ncnn-vulkan with `-g -1`, or for FILM, IFRNet, EMA-VFI or GMFSS on CPU. Benchmark locally.
- I did not confirm whether rife-ncnn-vulkan's CPU path handles v4.x models correctly or quickly. Its README documents `-1=cpu` but gives no numbers.
- I could not reach arXiv or CVF to pull the comparative runtime/PSNR tables for EMA-VFI, IFRNet, RIFE and FILM; those sites were not resolvable from this environment.
- No source evaluated interpolation artifacts on game HUDs, slot reels or playing cards specifically.
- I did not check which newer RIFE versions (4.7-4.26) the TNTwise ncnn fork or vs-mlrt ship.

## Q2. Upscaling and restoration on CPU (Real-ESRGAN, Real-CUGAN, waifu2x, SwinIR/HAT, Anime4K, OpenCV dnn_superres FSRCNN/ESPCN, video SR): what is practical for 2-3x zoomed slot-game crops and phone recordings?

### Takeaway
On CPU, GAN-class SR is slow but workable only for short zoomed segments. Compact Real-ESRGAN ("realesrgan v2") runs about 2.6 fps on a 640x360 input on a laptop CPU and about 1.2 fps on a 1080p input even with 64 threads. Transformer SR (SwinIR/HAT/swin_unet) is far slower. The fast CPU options are OpenCV dnn_superres ESPCN/FSRCNN (about 12 ms per 768x512 x4 image) and the light ArtCNN C4F32 (about 30 fps at 640x360 on CPU), but their quality gain over bicubic is modest.

### Cited Findings
**Benchmarks (vs-mlrt OpenVINO CPU)**
- Zen4 32C/64T, OV_CPU, 1920x1080 input, FP32/BF16 fps:
  - realesrgan v2 (compact): 1.21 / 2.72
  - waifu2x cunet / Real-CUGAN: 0.83 / 1.45
  - waifu2x swin_unet_art: 0.26 / 0.62
  - waifu2x upconv7: 0.40 / 0.79
  - DPIR denoise: 0.39 / 0.80

  Source: [vs-mlrt wiki: AMD EPYC Zen4](https://github.com/AmusementClub/vs-mlrt/wiki/AMD-EPYC-Zen4)
- Core Ultra 7 155H CPU, FP32, 640x360 input, fps:
  - realesrgan: 2.62
  - waifu2x cunet: 1.62
  - waifu2x upconv7: 2.70
  - waifu2x upresnet10: 3.20
  - **artcnn c4f32: 29.96**
  - artcnn c16f64: 2.53
  - artcnn r16f96: 0.39
  - dpir color: 0.74

  Source: [vs-mlrt wiki: Intel Core Ultra 7 155H](https://github.com/AmusementClub/vs-mlrt/wiki/Intel-Core-Ultra-7-155H)

**OpenCV dnn_superres** (in opencv_contrib, Apache-2.0, 10,216 stars, pushed 2026-10-09)
- Usable as `cv2.dnn_superres` with pip `opencv-contrib-python`. Models: EDSR x2/3/4, ESPCN x2/3/4, FSRCNN, LapSRN x2/4/8 — [opencv_contrib dnn_superres](https://github.com/opencv/opencv_contrib/tree/4.x/modules/dnn_superres)
- The module's x4 benchmark on a 768x512 image, CPU:

  | Model | Time | PSNR |
  |---|---|---|
  | ESPCN | 0.0116 s | 26.55 |
  | FSRCNN | 0.0130 s | 26.56 |
  | LapSRN | 0.283 s | 26.73 |
  | EDSR | 3.27 s | 29.24 |
  | Bicubic | 0.0003 s | 26.06 |
  | Lanczos | 0.0010 s | 25.91 |

  Source: [opencv_contrib dnn_superres](https://github.com/opencv/opencv_contrib/tree/4.x/modules/dnn_superres)
- The model weight repos are inactive but static, so weights still work:
  - **Saafke/EDSR_Tensorflow**: Apache-2.0, 284 stars, 2023-03
  - **Saafke/FSRCNN_Tensorflow**: Apache-2.0, 137 stars, 2020-10
  - **fannymonori/TF-ESPCN**: Apache-2.0, 89 stars, 2019-08

  Sources: [EDSR](https://github.com/Saafke/EDSR_Tensorflow); [FSRCNN](https://github.com/Saafke/FSRCNN_Tensorflow); [ESPCN](https://github.com/fannymonori/TF-ESPCN)

**Real-ESRGAN family**
- **xinntao/Real-ESRGAN** (https://github.com/xinntao/Real-ESRGAN): BSD-3-Clause. 37,091 stars. **Last push 2024-08-06 (about 2 years inactive)** — [GitHub](https://github.com/xinntao/Real-ESRGAN)
- A docs mirror ranks `realesr-general-x4v3` as the fastest and lowest-memory Real-ESRGAN model (about 17 MB, "Fast", "Good" quality, below x4plus). The anime video model is quoted at about 66 fps at 640x480 on a V100 GPU. This is mirror content, so verify against the repo docs — [mintlify mirror: general models](https://mintlify.com/xinntao/Real-ESRGAN/models/general-models); [video models](https://mintlify.com/xinntao/Real-ESRGAN/models/video-models)
- **xinntao/Real-ESRGAN-ncnn-vulkan** (https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan): 2,256 stars, last push 2024-05-10 (inactive). GitHub reports the license as NOASSERTION, while the README badge says MIT. **The `-g` option does not document `-1`/CPU**, so it is effectively Vulkan-GPU only. Models: realesr-animevideov3 (default), realesrgan-x4plus, -x4plus-anime, realesrnet-x4plus. Scale 2/3/4 — [README](https://github.com/xinntao/Real-ESRGAN-ncnn-vulkan)
- A Hugging Face OpenVINO port of RealESRGAN_x4plus claims "up to 13x faster than PyTorch" on Intel CPUs. This is the uploader's claim and is unverified — [HF ibrhr/Real-ESRGAN-OpenVINO](https://huggingface.co/ibrhr/Real-ESRGAN-OpenVINO)
- **HolyWu/vs-realesrgan**: BSD-3, 98 stars, pushed 2025-03-10. PyTorch/TensorRT oriented — [GitHub](https://github.com/HolyWu/vs-realesrgan)

**Real-CUGAN / waifu2x**
- **bilibili/ailab** (Real-CUGAN origin, https://github.com/bilibili/ailab): 5,879 stars, last push 2023-08-02. **No license detected — flag** — [GitHub](https://github.com/bilibili/ailab)
- **nihui/realcugan-ncnn-vulkan** (https://github.com/nihui/realcugan-ncnn-vulkan): MIT. 929 stars, last push 2023-03-12 (inactive). **`-g -1` = CPU is documented.** Options: `-s` 1/2/3/4, `-n` denoise -1..3, `-c` syncgap 0-3, `-t` tile. No speed numbers — [README](https://github.com/nihui/realcugan-ncnn-vulkan)
- **nihui/waifu2x-ncnn-vulkan** (https://github.com/nihui/waifu2x-ncnn-vulkan): MIT. 3,482 stars, pushed 2026-04-13. The description says it "runs fast on intel / amd / nvidia / apple-silicon" — [GitHub](https://github.com/nihui/waifu2x-ncnn-vulkan)
- **nagadomi/nunif** (https://github.com/nagadomi/nunif): "latest version of waifu2x", PyTorch. MIT. 3,498 stars, pushed 2026-10-13 (very active) — [GitHub](https://github.com/nagadomi/nunif)

**Transformer SR (slow on CPU)**
- **JingyunLiang/SwinIR**: Apache-2.0, 5,607 stars, last push 2024-05-14 — [GitHub](https://github.com/JingyunLiang/SwinIR)
- **XPixelGroup/HAT**: Apache-2.0, 1,602 stars, last push 2024-06-02 — [GitHub](https://github.com/XPixelGroup/HAT)
- The only CPU proxy found is the Swin-based waifu2x swin_unet_art at 0.26 fps for 1080p even on 64 threads — [vs-mlrt wiki: AMD EPYC Zen4](https://github.com/AmusementClub/vs-mlrt/wiki/AMD-EPYC-Zen4)

**Anime4K**
- **bloc97/Anime4K** (https://github.com/bloc97/Anime4K): GLSL real-time upscaler shaders. MIT. 21,514 stars, last push 2024-08-17. It is a shader for mpv and similar players, i.e. GPU — [GitHub](https://github.com/bloc97/Anime4K)
- **TianZerL/Anime4KCPP** (https://github.com/TianZerL/Anime4KCPP): v3, CNN-based. It has a **CPU path with SIMD (SSE/AVX2/AVX512/NEON...)**, optional OpenCL and CUDA, and a pybind11 Python binding (build option). **Dual license: GPL-3.0 for the video module, MIT for the others.** 2,038 stars, pushed 2026-07-04. No CPU fps published — [README](https://github.com/TianZerL/Anime4KCPP)

**Efficient SR / model sources**
- **hongyuanyu/SPAN** (https://github.com/hongyuanyu/SPAN): "Swift Parameter-free Attention Network for Efficient Super-Resolution". Apache-2.0. 283 stars, pushed 2026-02-28 — [GitHub](https://github.com/hongyuanyu/SPAN)
- **OpenModelDB/open-model-database** (GPL-3.0, 558 stars, pushed 2026-08-14) is a database of community SR models. **Phhofm/models** has 648 stars, no license, pushed 2025-11-14 — [OpenModelDB](https://github.com/OpenModelDB/open-model-database); [Phhofm](https://github.com/Phhofm/models)
- **the-database/traiNNer-redux** (Apache-2.0, 132 stars, pushed 2026-10-09) can train compact or SPAN models on your own game frames — [GitHub](https://github.com/the-database/traiNNer-redux)

**Video SR**
- **ckkelvinchan/RealBasicVSR**: Apache-2.0, 1,118 stars, last push 2023-06-05 — [GitHub](https://github.com/ckkelvinchan/RealBasicVSR)
- **ckkelvinchan/BasicVSR_PlusPlus**: Apache-2.0, 833 stars, last push 2023-12-27 — [GitHub](https://github.com/ckkelvinchan/BasicVSR_PlusPlus)
- Both are inactive research code with no CPU build.

**GUIs (not engine-embeddable; licence flags)**
- **upscayl/upscayl**: **AGPL-3.0**, 50,562 stars, pushed 2026-10-05, Electron app — [GitHub](https://github.com/upscayl/upscayl)
- **chaiNNer-org/chaiNNer**: GPL-3.0, 6,074 stars, pushed 2026-10-11, node GUI — [GitHub](https://github.com/chaiNNer-org/chaiNNer)

### Inferences
- **Zoomed slot-game crops (2-3.6x):** the crop is about 530x300 to 960x540 px. At the 155H CPU rate, compact Real-ESRGAN takes about 0.4 s per frame for a 640x360 crop. For 10 s of zoomed 60 fps output (600 frames) that is about 4 minutes. That is too much on top of everything else unless the container is much bigger.
- **Cheaper options for zoomed crops:**
  - Run SR at the source fps before interpolation (60 fps rather than 60 fps plus synthesized frames).
  - Upscale only the source frames (e.g. every frame at the 22-30 fps feed rate).
  - Use a 2x model and finish with Lanczos.
  - Use ArtCNN C4F32 or ESPCN/FSRCNN (tens of fps) with a mild unsharp mask.
- Slot art is flat-shaded and cartoon-like, closer to anime and art content. Anime and art models (realesr-animevideov3, Real-CUGAN, ArtCNN, waifu2x) may suit it better than photo models, but this is untested.
- **Phone screen recordings (574x1280 to 1080x1920, about 1.5-1.9x):** these are mostly UI text and flat graphics. GAN SR can hallucinate glyphs. ESPCN/FSRCNN x2 then downscale, or Lanczos plus sharpening, is the low-risk and real-time-capable path. The 1008x2244 recordings already exceed the target and need no SR.
- **Integration difficulty:**
  - `cv2.dnn_superres`: trivial (pip `opencv-contrib-python`; `readModel`, `setModel("espcn", 2)`, `upsample`).
  - Real-ESRGAN via vs-mlrt ONNX plus OpenVINO or onnxruntime Python: medium.
  - realcugan-ncnn-vulkan CLI with `-g -1`: low-medium, frames through files.
  - Real-ESRGAN PyTorch package: medium. The repo is inactive and has known torchvision import breakages; not verified here.
  - SwinIR/HAT: impractical on CPU for video.

### Gaps
- No CPU fps was found for realesr-general-x4v3 specifically, for Real-ESRGAN PyTorch on CPU, or for realcugan-ncnn-vulkan with `-g -1`. Anime4KCPP's CPU throughput is also unpublished.
- I did not verify whether waifu2x-ncnn-vulkan also documents `-g -1` (likely the same CLI pattern as realcugan-ncnn-vulkan).
- No quality comparison of SR models on slot-game or casino UI footage exists in the sources found.
- I could not open ArtCNN's own repo to confirm its license or stars. It is referenced via vs-mlrt only.

## Q3. Object tracking for following cards and chips, and smoothing a steady virtual camera (OpenCV CSRT/KCF, ByteTrack/BoT-SORT/OC-SORT, Ultralytics YOLO, SAM 2/EfficientTAM, CoTracker/TAPIR, One Euro filter)

### Takeaway
For following one dealt card or hand on CPU, OpenCV's built-in trackers are the practical choice. VitTrack (`cv2.TrackerVit`) runs in about 2-4 ms per frame on a desktop CPU, gives a confidence score to detect loss, and is Apache-2.0. CSRT is the classic accurate fallback. Smooth the result with a One Euro filter. Detector-plus-MOT stacks (YOLO + ByteTrack) need a trained card/chip detector, and Ultralytics and BoxMOT are AGPL-3.0. SAM 2, EfficientTAM and CoTracker are GPU-first. CoTracker is also CC-BY-NC (non-commercial).

### Cited Findings
**OpenCV trackers**
- **opencv/opencv** (https://github.com/opencv/opencv): Apache-2.0, 91,179 stars, pushed 2026-10-14 — [GitHub](https://github.com/opencv/opencv)
- **VitTrack** (opencv/opencv_zoo, Apache-2.0):
  - Described as "a much better model for real-time object tracking" than NanoTrack. It outputs a confidence score that indicates when the target is lost. Requires OpenCV > 4.8.0.
  - Latency with onnxruntime: **Intel i3-10105 3.84 ms (1 thread) / 2.01 ms (4 threads)**; Apple M2 4.18 / 1.46 ms.
  - LaSOT AUC 48.6 vs NanoTrack 46.8.

  Source: [opencv_zoo VitTrack](https://github.com/opencv/opencv_zoo/tree/main/models/object_tracking_vittrack)
- **opencv/opencv_zoo**: 1,086 stars, pushed 2026-05-28. It says the project "is now hosted in Hugging Face" (huggingface.co/opencv) — [opencv_zoo](https://github.com/opencv/opencv_zoo)
- **CSRT vs KCF:** CSRT is more accurate but slower, KCF is faster, and MOSSE is the fastest — [PyImageSearch](https://pyimagesearch.com/2018/07/30/opencv-object-tracking/)
- One report gives KCF about 201 fps and CSRT about 80 fps on CPU on LaSOT — [VNTU repository](https://ir.lib.vntu.edu.ua/handle/123456789/50083). This conflicts with an OpenCV 3.4.1 user reporting KCF about 30 fps and CSRT about 4 fps on 1920x1080 video — [OpenCV Q&A](https://answers.opencv.org/question/201389/how-to-change-the-fps-of-the-trackers-in-opencv-341-in-c). Speed depends strongly on frame and ROI size.
- A forum thread is titled "TrackerCSRT is extremely slow with OpenCV 4.10.0", a possible regression in recent versions. Only the title was checked — [OpenCV forum](https://forum.opencv.org/t/trackercsrt-is-extremely-slow-with-opencv-4-10-0/19072)

**Detectors and multi-object trackers**
- **FoundationVision/ByteTrack** (https://github.com/FoundationVision/ByteTrack): MIT, 6,743 stars, last push 2024-06-19 (inactive) — [GitHub](https://github.com/FoundationVision/ByteTrack)
- **NirAharon/BoT-SORT**: MIT, 1,564 stars, last push 2024-08-08 (inactive) — [GitHub](https://github.com/NirAharon/BoT-SORT)
- **noahcao/OC-SORT** (https://github.com/noahcao/OC-SORT): did not return in the API query, so no stats or license were collected.
- **mikel-brostrom/boxmot** (https://github.com/mikel-brostrom/boxmot): pluggable ByteTrack, BoT-SORT, OC-SORT, DeepOCSORT, StrongSORT and BoostTrack. **AGPL-3.0.** 8,314 stars, pushed 2026-10-13 — [GitHub](https://github.com/mikel-brostrom/boxmot)
- **roboflow/supervision** (https://github.com/roboflow/supervision): MIT. 51,205 stars, pushed 2026-10-13. CV utilities including tracking (it ships a ByteTrack implementation) — [GitHub](https://github.com/roboflow/supervision)
- **ultralytics/ultralytics** (https://github.com/ultralytics/ultralytics): YOLO26/YOLO27/YOLO11/YOLOv8 with built-in tracking. **AGPL-3.0.** 62,499 stars, pushed 2026-10-14 — [GitHub](https://github.com/ultralytics/ultralytics)
  - Ultralytics offers a paid Enterprise License to avoid AGPL obligations. This comes from a competitor's (vendor) blog — [Roboflow blog](https://blog.roboflow.com/roboflow-vs-ultralytics/)
- **roboflow/rf-detr** (https://github.com/roboflow/rf-detr): ICLR 2026. Apache-2.0 code. 9,797 stars, pushed 2026-10-14. Core Nano-Large checkpoints are Apache-2.0, while **XL/2XL checkpoints are under Roboflow's Platform Model License**. Vendor-sourced; check each checkpoint's license — [Roboflow blog](https://blog.roboflow.com/rf-detr-is-free-to-use-commercially/)
- **Megvii-BaseDetection/YOLOX** (https://github.com/Megvii-BaseDetection/YOLOX): Apache-2.0, 10,659 stars, last push 2025-06-08. **ONNX, ncnn and OpenVINO exports supported** — [GitHub](https://github.com/Megvii-BaseDetection/YOLOX)

**Segmentation and point tracking**
- **facebookresearch/sam2** (https://github.com/facebookresearch/sam2): Apache-2.0, 20,004 stars, pushed 2026-05-30 — [GitHub](https://github.com/facebookresearch/sam2)
- **yformer/EfficientTAM** (https://github.com/yformer/EfficientTAM): Apache-2.0, 829 stars, last push 2025-01-06 (inactive). About 2x faster than SAM 2 (HieraB+) on A100 with about 2.4x fewer parameters. It runs at **261 ms per frame (about 10 fps) on iPhone 15 Pro Max** for video object segmentation — [EfficientTAM paper](https://arxiv.org/html/2411.18933v1); [GitHub](https://github.com/yformer/EfficientTAM)
- **ChaoningZhang/MobileSAM**: Apache-2.0, 5,892 stars. Image segmentation only, not video memory — [GitHub](https://github.com/ChaoningZhang/MobileSAM)
- **z-x-yang/Segment-and-Track-Anything**: **AGPL-3.0**, 3,141 stars — [GitHub](https://github.com/z-x-yang/Segment-and-Track-Anything)
- **facebookresearch/co-tracker** (https://github.com/facebookresearch/co-tracker): 5,152 stars, pushed 2026-03-03.
  - **"The majority of CoTracker is licensed under CC-BY-NC" (non-commercial flag).**
  - CoTracker3 was released 2024-10-15 and has an online sliding-window mode.
  - "A GPU is strongly recommended", though small tasks can run on CPU.

  Source: [co-tracker README](https://github.com/facebookresearch/co-tracker)
- **google-deepmind/tapnet** (https://github.com/google-deepmind/tapnet): TAPIR/BootsTAPIR point tracking. Apache-2.0. 2,215 stars, pushed 2026-09-15 — [GitHub](https://github.com/google-deepmind/tapnet)

**Smoothing and stabilization**
- **casiez/OneEuroFilter** (https://github.com/casiez/OneEuroFilter): the 1€ filter ("filter noisy signals for high precision and responsiveness"), C++ with other language versions. 259 stars, pushed 2026-08-05. **No license detected by GitHub — flag** — [GitHub](https://github.com/casiez/OneEuroFilter)
- **georgmartius/vid.stab** (https://github.com/georgmartius/vid.stab): the library behind ffmpeg `vidstabdetect`/`vidstabtransform`. 965 stars, pushed 2026-08-14. License NOASSERTION — [GitHub](https://github.com/georgmartius/vid.stab)
- **AdamSpannbauer/python_video_stab**: OpenCV-based stabilizer. MIT. 779 stars, last push 2023-07-19 (inactive) — [GitHub](https://github.com/AdamSpannbauer/python_video_stab)

### Inferences
- **Card following in blackjack:** the earlier hand tracker was shaky. Track a rigid, high-contrast target (the dealt card or the card cluster bounding box) instead.
  - Seed `cv2.TrackerVit` (or CSRT) from a keyed or auto-detected box on a downscaled frame (e.g. 960x540), and re-seed when the confidence drops.
  - Feed the box center and scale through a One Euro filter: a low min_cutoff for steadiness and a beta tuned so the camera keeps up with a deal.
  - Alternatively, compute the whole path offline and smooth it bidirectionally (e.g. Savitzky-Golay or a forward-backward low-pass), since rendering is offline.
- An offline engine can use look-ahead, which real-time trackers cannot. For example, keyframe only the card-landing positions detected by tracking and ease between them. This likely gives a smoother "virtual camera" than per-frame tracking.
- Multi-object detection plus ByteTrack requires a custom card/chip detector. YOLOX (Apache, OpenVINO export) or RF-DETR Nano-Large (Apache) avoid the AGPL that Ultralytics and BoxMOT impose. AGPL matters if the engine is ever offered as a network service or distributed. For purely private internal use it is less of a concern; confirm with legal judgment.
- SAM 2 and EfficientTAM would give pixel-accurate card masks, but they are likely 0.3-2 s per frame on CPU (extrapolated from 261 ms on an iPhone NPU/GPU), so they suit sparse keyframes only.
- CoTracker should be avoided for monetized content because of CC-BY-NC.
- **Integration difficulty:**
  - OpenCV trackers plus a One Euro filter: low (pure Python and OpenCV).
  - YOLOX/RF-DETR + supervision ByteTrack: medium (needs labeled training data).
  - SAM 2 / EfficientTAM / TAPIR: medium-high, and slow on CPU.

### Gaps
- No measured CPU fps was found for TrackerVit inside `cv2` (the numbers are onnxruntime), for SAM 2/EfficientTAM on x86 CPU, or for TAPIR/CoTracker on CPU.
- OC-SORT stats and license were not collected.
- No public card or chip detection model was evaluated.
- The OneEuroFilter repo license is unclear. The algorithm is simple enough to reimplement in a few lines.

## Q4. Auto-reframing 16:9 to 9:16 (MediaPipe AutoFlip status, ClipsAI resize, saliency/face reframers, motion-smoothed crop paths)

### Takeaway
No maintained open-source auto-reframer fits game footage. AutoFlip's support ended on 2023-03-01 (as-is code only, C++/Bazel). ClipsAI's `resize` is a speaker-diarization and face reframer for talking-head video and has been inactive since January 2024. Other repos are face- or person-based, often on AGPL YOLO. For a game window plus webcam, a custom ROI and motion-energy crop path with One Euro or offline smoothing is the realistic route.

### Cited Findings
- **google-ai-edge/mediapipe** (https://github.com/google-ai-edge/mediapipe): Apache-2.0, 37,281 stars, pushed 2026-10-14, active overall. However, **AutoFlip is listed as a legacy solution with "Support ended"**. Legacy support stopped on 2023-03-01 and there is no upgrade path. The code and binaries remain available as-is — [MediaPipe Solutions guide](https://developers.google.com/edge/mediapipe/solutions/guide)
- AutoFlip takes a video and a target shape and analyzes content to build tracking and cropping strategies. It detects scene changes to process scenes separately, and it is built on the MediaPipe C++ graph framework — [Google Research blog (2020)](https://research.google/blog/autoflip-an-open-source-framework-for-intelligent-video-reframing/)
- **ClipsAI/clipsai** (https://github.com/ClipsAI/clipsai): MIT, 549 stars, **last push 2024-01-17 (inactive)**.
  - `resize(video_file_path, pyannote_auth_token, aspect_ratio=(9,16))` returns `crops.segments`. It "focuses on the current speaker" using Pyannote diarization and needs a Hugging Face token.
  - Dependencies: WhisperX, libmagic, ffmpeg. It is aimed at audio-centric, narrative (talking-head) videos.

  Source: [ClipsAI README](https://github.com/ClipsAI/clipsai)
- **kamilstanuch/Autocrop-vertical** (https://github.com/kamilstanuch/Autocrop-vertical): "Smart video converter using YOLOv8 and FFmpeg" for horizontal-to-vertical conversion. 420 stars, pushed 2026-02-15. **No license file. It also depends on Ultralytics YOLOv8, which is AGPL** — [GitHub](https://github.com/kamilstanuch/Autocrop-vertical)
- **smartcrop/smartcrop.py**: image-level content-aware crop. MIT, 271 stars, pushed 2026-03-06 — [GitHub](https://github.com/smartcrop/smartcrop.py)
- **jwagner/smartcrop.js**: the original JavaScript version. MIT, 12,958 stars, last push 2024-03-16 — [GitHub](https://github.com/jwagner/smartcrop.js)
- **rickyyuan07/FaceTracker**: detects, tracks and crops a specific face given a reference image, with bounding-box smoothing. It prioritizes quality over real-time speed — [GitHub](https://github.com/rickyyuan07/FaceTracker)
- Community advice for DIY reframing: compute a face-centred 9:16 crop per frame, smooth the crop centre with a moving average, then crop with FFmpeg or OpenCV — [Reddit snapshot](https://reddit.sentinel-team.org/posts/1qa5ira/snapshots/2026-01-12T03%3A21%3A30.45965Z) (aggregator mirror; low confidence)
- ffmpeg's `vidstabdetect`/`vidstabtransform` (vid.stab) can smooth an existing camera path. 965 stars, pushed 2026-08-14 — [vid.stab](https://github.com/georgmartius/vid.stab)

### Inferences
- The Instagram layout is a 1080x830 panel on a blurred background, not a full 9:16 crop, so it only needs a crop window of about 1.3:1 from the game area plus the webcam.
- Face, speaker and person reframers (ClipsAI, Autocrop-vertical, FaceTracker) only help with the webcam region. They do not help find where the action is in a slot or blackjack game window.
- For game content, a better signal is one of:
  - a known fixed layout, i.e. a per-game ROI template;
  - frame-difference motion energy inside the game window, which catches reel spins, win banners and card deals;
  - the card tracker from Q3.

  Feed that signal into a crop centre, clamp it to the game window, and smooth it with a One Euro filter or offline bidirectional smoothing.
- OpenCV contrib's `cv2.saliency` (spectral residual and fine-grained static saliency) is a cheap CPU saliency map that could serve as an additional signal. Its usefulness on flashing slot UIs is untested and not sourced here.
- AutoFlip is not worth adopting. Its support has ended, it needs a C++/Bazel build, and its signals (faces, objects, saliency) are tuned for live action.
- **Integration difficulty:**
  - Custom ROI/motion crop path in Python/OpenCV: low.
  - ClipsAI resize: medium. It needs a pyannote token and is the wrong signal type for this footage.
  - AutoFlip: high. It means a Bazel build of legacy, unmaintained code.

### Gaps
- No maintained, permissively licensed, game-aware video reframer was found.
- No published CPU speed numbers were found for ClipsAI resize or AutoFlip.
- I could not reach the MediaPipe AutoFlip docs page directly (ai.google.dev was not resolvable from this environment). The "support ended" status comes from the developers.google.com guide as returned by search.
- ClipsAI's face-detection backend is not stated in the README.
