#!/usr/bin/env bash
# Fresh cloud session -> everything the hype-edit pipeline needs (CPU only, ~6 GB of model downloads).
# Needs network access to pypi.org, huggingface.co (+ *.hf.co), github.com and its release-assets host.
# Usage: bash setup_env.sh [--no-voice]   (--no-voice skips the 5 GB voice generator)
set -euo pipefail
PIP="pip install -q --root-user-action=ignore"

# reading the game (win reader), transcripts, voice/game separation, audio helpers
$PIP rapidocr_onnxruntime "faster-whisper==1.2.*" "audio-separator[cpu]==0.47.*" audioread librosa pyloudnorm soundfile silero-vad
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"
python3 - <<'EOF'
from audio_separator.separator import Separator
s = Separator(output_dir="/tmp", model_file_dir="/tmp/audio-separator-models"); s.load_model("UVR-MDX-NET-Voc_FT.onnx")
EOF

if [ "${1:-}" != "--no-voice" ]; then
  # Chatterbox multilingual (MIT) = our own voice generator for the pop-up characters.
  # torchaudio 2.11 runs fine on the container's newer torch when installed without deps (only kaldi fbank + resample are used);
  # setuptools<81 keeps pkg_resources, which the Perth audio watermarker needs (leave the watermark on).
  $PIP --no-deps "torchaudio==2.11.0"
  $PIP "transformers==5.2.0" "diffusers>=0.31" resemble-perth "conformer==0.3.2" omegaconf einops "setuptools<81" "piper-tts==1.8.*"
  $PIP --no-deps "s3tokenizer==0.3.0" "chatterbox-tts==0.1.7"
  python3 - <<'EOF'
from huggingface_hub import snapshot_download
snapshot_download("ResembleAI/chatterbox", allow_patterns=["ve.pt", "t3_mtl23ls_v2.safetensors", "s3gen.pt",
                  "grapheme_mtl_merged_expanded_v1.json", "conds.pt", "Cangjie5_TC.json"])
EOF
  python3 -c "from chatterbox.mtl_tts import ChatterboxMultilingualTTS; import perth; assert perth.PerthImplicitWatermarker; print('voice generator ready')"
fi
echo "setup done"
