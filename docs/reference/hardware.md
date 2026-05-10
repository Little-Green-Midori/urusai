# 硬體 + 環境基線

## 開發機規格（截至 2026-05-08）

| 項目 | 值 |
|---|---|
| GPU | NVIDIA GeForce RTX 2060 |
| VRAM | 6 GB |
| Driver | 591.59 |
| CUDA runtime | 12.8 |
| torch | 2.11.0+cu128 |
| Python | 3.11 |

**這是當前開發機的資源約束，不是 `urusai` 系統架構的能力上限**。模型選型、tier 表、Phase 規劃皆按 [`audio-understanding-models.md`](audio-understanding-models.md) 的 high / mid / low / backup 四 tier 列出，與 dev 環境跑哪一 tier 解耦。

## 主流硬體假設

- 2026 主流個人 PC GPU 至少 **RTX 3060 12 GB**（中階 mass-market 標準）。
- 中階使用者可跑 7B–13B int4 quantized LLM、PaddleOCR、SmolVLM-2.2B、TinyMU、MERT、CLAP、PANNs 等 mid-tier 模型。
- 高階使用者（RTX 4090 / 5090、cloud A100/H100）可跑 high-tier 模型（Music Flamingo 8B、Qwen3.5-Omni 30B MoE、video-SALMONN-2+ 7B 等）。

`urusai` 架構不鎖死在最低規格——dev 期 default 是 6 GB 友善的工具組合，但設計表保留所有 tier 的選型，未來升級或部署到主流 / 高階機器時可向上切換。

## VRAM 約束（dev 環境 6 GB 範圍內）

6 GB VRAM 屬輕量 tier，多模型同時載入需排程：

| 模型類別 | 估算 VRAM | 6 GB 可行性 |
|---|---|---|
| LVLM（Gemini 3.1 / GPT-5.5 / Claude Opus 4.7 vision）| API 為主 | 走 API、不本地 |
| Gemma 4 31B IT | API 為主（local int4 ~16 GB）| 走 Gemini API、不本地 |
| faster-whisper large-v3-turbo（float16）| ≈ 1.6 GB | 可 |
| faster-whisper large-v3 | ≈ 3 GB | 可（需排程，不與其他模型並載）|
| BS-RoFormer / Mel-Band Roformer | 2–4 GB | 可（單獨跑）|
| YOLO26 nano / small | < 500 MB / 1–3 GB | 可 |
| PaddleOCR 3.4.0（PP-OCRv5）| ≈ 1 GB | 可 |
| PaddleOCR-VL-1.5（0.9B 文件 VLM）| ≈ 2 GB | 可 |
| PANNs / YAMNet | < 500 MB | 可 |
| TinyMU（229M）| ~900 MB | 可 |
| MERT-v1-95M / 330M | 380 MB / 1.3 GB | 可 |
| CLAP / MuQ-MuLan | 800 MB / 2.8 GB | 可 |
| SmolVLM-2.2B | ~4 GB | 可（單獨跑）|

**多模型同時載入會超出 VRAM 上限**——agent loop 採 sequential load / unload，不假設全模型常駐。

## GPU 偏好

- audio-separator：用現有 cu128 torch（**不**裝 `[cpu]` extra，會覆蓋 GPU torch）
- faster-whisper：走 ctranslate2 自動 CUDA detection
- paddleocr：要裝 paddlepaddle-gpu 對應 CUDA 版本
- PANNs / YAMNet：torch 自動 CUDA

## 規劃中：系統健康度檢測 sidecar

dev 環境 6 GB VRAM 跑多模型容易踩瓶頸。規劃 lightweight monitoring sidecar：

- **資源指標**：VRAM 使用率、GPU utilization、CPU load、RAM、disk I/O。
- **觸發行為**：
  - VRAM > 80% → 拒絕載入新模型，強制 unload 最舊。
  - CPU 持續 100% 超過閾值 → 暫停 schedule，避免溫度持續攀升。
  - 溫度超標 → 同上。
- **介面**：可被 agent loop 詢問「目前剩多少 budget 跑 X」、可被 user 從 dashboard 觀察。
- **實作層**：獨立 module（如 `urusai.health` / `urusai.observability`），不雜入 channels。

優先級：第一輪實驗跑通後再做，避免 design 階段提前優化。
