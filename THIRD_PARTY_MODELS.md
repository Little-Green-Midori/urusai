# URUSAI Third-Party Models Registry

Records all third-party model weights / gated assets used by URUSAI, including
license, acceptance date (where gated), and intended use.

GPL / AGPL / SSPL **never accepted**. Pre-relicense versions of dual-licensed
models (e.g. Kim Vocal 2 pre-2026-04-22) **never accepted**. Every concrete
model ID / version recorded in this file must be traceable to an upstream
source (HF repo URL, release tag, or vendor documentation).

---

## Format per entry

```
### <model-id>

- **Repo**: <HF / ModelScope / other URL>
- **License**: <SPDX + gated terms summary>
- **Commit SHA**: <pinned revision (HF revision hash)>
- **Acceptance date**: YYYY-MM-DD (only required for HF gated repos)
- **Accepted by**: <user identifier / "team" if shared>
- **Used in URUSAI**: channel=<asr/scene/ocr/...> provider=<name>
- **Storage path**: ./models/<subdir>/
```

---

## Entries

_Populated by `urusai models download` (`backend/scripts/models/download.{sh,ps1}`). Empty on initial scaffold._

Expected first-download set:

- `PaddlePaddle/PaddleOCR-VL-1.5-GGUF` (Apache-2.0, OCR channel)
- `microsoft/BEATs_iter3_plus_AS2M` (MIT, audio_event channel)
- `KimberleyJSN/melbandroformer` (MIT post 2026-04-22 relicense, mss channel)
- `pyannote/segmentation-3.0` (MIT + HF gated, diarization channel)
- `pyannote/speaker-diarization-3.1` (MIT + HF gated, diarization channel)

Plus `faster-whisper large-v3-turbo` (CTranslate2 weights, MIT) — auto-downloaded on first ASR invocation.
