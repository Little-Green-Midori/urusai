#!/usr/bin/env bash
# URUSAI third-party weights downloader.
#
# Downloads to <repo-root>/models/ via huggingface-cli.
# After running, update THIRD_PARTY_MODELS.md with commit SHAs + acceptance date.
#
# Required env: HUGGINGFACE_API_KEY (for gated pyannote repos).
#
# Usage: bash backend/scripts/download_models.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODELS_DIR="$REPO_ROOT/models"
THIRD_PARTY="$REPO_ROOT/THIRD_PARTY_MODELS.md"

mkdir -p "$MODELS_DIR"

if [ -z "${HUGGINGFACE_API_KEY:-}" ]; then
  HUGGINGFACE_API_KEY="$(grep -E '^HUGGINGFACE_API_KEY=' "$REPO_ROOT/backend/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"' || true)"
fi

if [ -z "${HUGGINGFACE_API_KEY:-}" ]; then
  echo "WARNING: HUGGINGFACE_API_KEY not set; pyannote gated repos will fail."
fi

echo "=== Downloading PaddleOCR-VL-1.5-GGUF (Apache-2.0, OCR channel) ==="
huggingface-cli download PaddlePaddle/PaddleOCR-VL-1.5-GGUF \
  --local-dir "$MODELS_DIR/paddleocr-vl" \
  --include "PaddleOCR-VL-1.5.gguf" "PaddleOCR-VL-1.5-mmproj.gguf"

echo "=== Downloading BEATs (MIT, audio_event channel) ==="
huggingface-cli download microsoft/BEATs \
  --local-dir "$MODELS_DIR/beats" \
  --include "BEATs_iter3_plus_AS2M.pt"

echo "=== Downloading Mel-Band RoFormer Kim Vocal 2 (MIT post-relicense, mss channel) ==="
huggingface-cli download KimberleyJSN/melbandroformer \
  --local-dir "$MODELS_DIR/melbandroformer"

if [ -n "${HUGGINGFACE_API_KEY:-}" ]; then
  echo "=== Downloading pyannote/segmentation-3.0 (MIT + gated, diarization) ==="
  huggingface-cli download pyannote/segmentation-3.0 \
    --local-dir "$MODELS_DIR/pyannote-segmentation-3.0" \
    --token "$HUGGINGFACE_API_KEY"

  echo "=== Downloading pyannote/speaker-diarization-3.1 (MIT + gated, diarization) ==="
  huggingface-cli download pyannote/speaker-diarization-3.1 \
    --local-dir "$MODELS_DIR/pyannote-diarization-3.1" \
    --token "$HUGGINGFACE_API_KEY"
fi

echo ""
echo "=== Models downloaded. Remember to update THIRD_PARTY_MODELS.md ==="
echo "    with commit SHAs + acceptance date."
echo ""
echo "faster-whisper large-v3-turbo: downloaded automatically on first ASR invocation."
