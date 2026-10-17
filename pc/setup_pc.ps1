# One-time setup of Dylan's PC (Windows 10/11, RTX 2070 Super, 8 GB VRAM) for the hype-edit pipeline.
# Run in PowerShell:  powershell -ExecutionPolicy Bypass -File setup_pc.ps1
# Installs Python 3.12 + ffmpeg (with NVENC) via winget, then CUDA builds of torch / onnxruntime / faster-whisper.
$ErrorActionPreference = "Stop"
winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
# ffmpeg 9.x needs NVENC API 13.1 (driver 610+); 8.0.1 runs NVENC on the 572 driver. Pinned so winget upgrade keeps it.
winget install -e --id Gyan.FFmpeg --version 8.0.1 --accept-package-agreements --accept-source-agreements
winget pin add --id Gyan.FFmpeg --version 8.0.*
winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
$root = "$env:USERPROFILE\hype"; New-Item -ItemType Directory -Force $root | Out-Null; Set-Location $root
py -3.12 -m venv venv; $py = "$root\venv\Scripts\python.exe"
& $py -m pip install -U pip
# torch with CUDA 12.4 (Turing / 2070 Super is supported), then the GPU onnxruntime used by rembg + rapidocr
& $py -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124
& $py -m pip install "numpy>=2.3" opencv-python pillow scipy soundfile librosa pyloudnorm audioread rapidocr_onnxruntime `
    "faster-whisper==1.2.*" "audio-separator[gpu]==0.47.*" "rembg[gpu]" silero-vad speechmos "rotary-embedding-torch==0.6.5" nvidia-cublas-cu12 nvidia-cudnn-cu12
# onnxruntime-gpu newer than 1.22 is built for CUDA 13 (wants cublasLt64_13.dll); 1.22 matches torch cu124 / CUDA 12
& $py -m pip uninstall -y onnxruntime onnxruntime-gpu; & $py -m pip install "onnxruntime-gpu==1.22.0"
# sanity: NVENC, CUDA torch, CUDA onnxruntime, CUDA whisper
ffmpeg -v error -f lavfi -i color=c=black:s=256x256:d=0.1 -c:v h264_nvenc -f null - ; if ($LASTEXITCODE -eq 0) { "NVENC ok" } else { "NVENC MISSING - update the NVIDIA driver" }
& $py -c "import torch, onnxruntime as o, ctranslate2 as c; o.preload_dlls(); print('torch cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0)); print('onnx', o.get_available_providers()); print('whisper cuda devices', c.get_cuda_device_count())"
& $py -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cuda', compute_type='float16'); print('whisper ready')"
& $py -c "from audio_separator.separator import Separator; s = Separator(output_dir='.', model_file_dir='models'); s.load_model('model_bs_roformer_ep_317_sdr_12.9755.ckpt'); print('separator ready')"
& $py -c "import onnxruntime as o; o.preload_dlls(); from rembg import new_session; s = new_session('isnet-general-use'); p = s.inner_session.get_providers()[0]; print('rembg ready' if p == 'CUDAExecutionProvider' else 'rembg ON CPU: ' + p)"
"setup done -> $root"
# keep the PC awake overnight while plugged in (screen may still turn off)
powercfg /change standby-timeout-ac 0; powercfg /change hibernate-timeout-ac 0
New-Item -ItemType Directory -Force "$root\.claude", "$root\out", "$root\vods", "$root\pack" | Out-Null
