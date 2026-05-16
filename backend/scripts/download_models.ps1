# URUSAI third-party weights downloader (Windows / PowerShell).
# Same scope as download_models.sh; uses huggingface-cli from active Python env.

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$ModelsDir = Join-Path $RepoRoot "models"
New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null

# Pull HF token from backend/.env if not in env
if (-not $env:HUGGINGFACE_API_KEY) {
    $envFile = Join-Path $RepoRoot "backend\.env"
    if (Test-Path $envFile) {
        $line = (Get-Content $envFile | Where-Object { $_ -match "^HUGGINGFACE_API_KEY=" } | Select-Object -First 1)
        if ($line) {
            $env:HUGGINGFACE_API_KEY = ($line -split "=", 2)[1].Trim('"')
        }
    }
}

if (-not $env:HUGGINGFACE_API_KEY) {
    Write-Warning "HUGGINGFACE_API_KEY not set; pyannote gated repos will fail."
}

Write-Host "=== Downloading PaddleOCR-VL-1.5-GGUF (Apache-2.0, OCR channel) ===" -ForegroundColor Cyan
huggingface-cli download PaddlePaddle/PaddleOCR-VL-1.5-GGUF `
    --local-dir (Join-Path $ModelsDir "paddleocr-vl") `
    --include "PaddleOCR-VL-1.5.gguf" "PaddleOCR-VL-1.5-mmproj.gguf"

Write-Host "=== Downloading BEATs (MIT, audio_event channel) ===" -ForegroundColor Cyan
huggingface-cli download microsoft/BEATs `
    --local-dir (Join-Path $ModelsDir "beats") `
    --include "BEATs_iter3_plus_AS2M.pt"

Write-Host "=== Downloading Mel-Band RoFormer Kim Vocal 2 (MIT post-relicense) ===" -ForegroundColor Cyan
huggingface-cli download KimberleyJSN/melbandroformer `
    --local-dir (Join-Path $ModelsDir "melbandroformer")

if ($env:HUGGINGFACE_API_KEY) {
    Write-Host "=== Downloading pyannote/segmentation-3.0 (MIT + gated) ===" -ForegroundColor Cyan
    huggingface-cli download pyannote/segmentation-3.0 `
        --local-dir (Join-Path $ModelsDir "pyannote-segmentation-3.0") `
        --token $env:HUGGINGFACE_API_KEY

    Write-Host "=== Downloading pyannote/speaker-diarization-3.1 (MIT + gated) ===" -ForegroundColor Cyan
    huggingface-cli download pyannote/speaker-diarization-3.1 `
        --local-dir (Join-Path $ModelsDir "pyannote-diarization-3.1") `
        --token $env:HUGGINGFACE_API_KEY
}

Write-Host ""
Write-Host "=== Models downloaded. Update THIRD_PARTY_MODELS.md with commit SHAs + date. ===" -ForegroundColor Green
Write-Host "    faster-whisper large-v3-turbo: auto-downloads on first ASR invocation."
