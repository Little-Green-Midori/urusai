# urusai

> 一個會看影片、但拒絕憑印象答題的代理人。每個答案都要指回筆記、指不回就承認看不到。

## 是什麼

`urusai` 是 Video RAG agent。把 Video RAG 視為**資訊調度**問題、不是**影片理解**問題：VLM / LVLM 已能理解短片段，但**長影片**、**fine-grained timing**、**跨段聚合**、**長尾領域**、**token cost** 這五道邊界仍在；`urusai` 不重造 VLM，而是補這些邊界。

## 目前狀態

- 單影片 + in-memory ingest store
- 對白本：manual SUB（yt-dlp）+ faster-whisper local 已接
- 場景本：PySceneDetect 已接
- Agent：sequential `orchestrator → integrator`，主 LLM 為 Gemma 4 31B IT via Gemini API
- API：`POST /ingest`、`POST /query`、`GET /healthz`
- Streamlit dev UI：in-process TestClient 呼叫 API

## 系統需求

- Python 3.11+
- `ffmpeg`、`yt-dlp` 在 PATH 上
- **`GEMINI_API_KEY`**（必要）：主代理人 LLM 與 Gemini 系列 vision/audio 呼叫共用 key
- CUDA-capable GPU（建議）：local ASR（`faster-whisper`）效能；無 GPU 可走 CPU 但慢
- 選用：`OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GROQ_API_KEY` / `DEEPGRAM_API_KEY` / `ASSEMBLYAI_API_KEY` / `JINA_API_KEY` / `EXA_API_KEY` 為備援 provider

## 安裝

```bash
pip install -e .[dev]
cp .env.example .env   # 填入 API key（至少 GEMINI_API_KEY）
```

## Quick start

### REST API

```bash
uvicorn urusai.api.main:app --reload
```

```bash
# 上傳本機檔案、或丟 URL（yt-dlp 會抓下來）
curl -X POST http://localhost:8000/ingest \
  -H 'content-type: application/json' \
  -d '{"file_path": "/path/to/video.mp4"}'

# -> {"ingest_id": "abc123...", "inventory": {...}, "notebooks": {...}}

# 問問題
curl -X POST http://localhost:8000/query \
  -H 'content-type: application/json' \
  -d '{"ingest_id": "abc123...", "query": "她在開頭說了什麼？"}'

# -> {"status": "answered" | "abstain", "answer": ..., "cited_evidence": [...], "trace": "..."}
```

### Streamlit dev UI

```bash
streamlit run streamlit_app.py
```

Streamlit UI 透過 in-process FastAPI TestClient 呼叫 endpoints，跟外部 HTTP client 走同一條 code path。

## 系統架構

```
        video file / URL
               │
               ▼
   ┌────────────────────────┐
   │  inventory probe       │  has_speech / has_visual / has_music ...
   └──────────┬─────────────┘
              │ dispatch
   ┌──────────┴──────────┐
   ▼                     ▼
 SubtitleChannel  ASRChannel   SceneChannel
              │
              ▼
      五本筆記  +  共同時間軸
              │
              ▼
   ┌────────────────────────┐
   │  query                 │
   │   ↓                    │
   │  orchestrator          │   →  retrieve evidence
   │   ↓                    │
   │  integrator            │   →  Gemma 4 31B IT (via Gemini API)
   │   ↓                    │       answered (cite indices) | abstain
   │  evidence trace        │
   └────────────────────────┘
```

## 文件

文件遵循 [Diátaxis](https://diataxis.fr/) 四象限：

- [`docs/tutorials/`](docs/tutorials/)——入門範例
- [`docs/how-to/`](docs/how-to/)——任務 recipe
- [`docs/reference/`](docs/reference/)——API、設定、schema、module map、硬體基線

## 設定

`.env` 完整列表見 `.env.example`：

| 變數 | 必要 | 用途 |
|---|---|---|
| `GEMINI_API_KEY` | 是 | 主代理人 LLM（Gemma 4 31B IT）與 Gemini family vision / audio call |
| `OPENAI_API_KEY` | 否 | 備援；Whisper API fallback 或 GPT vision |
| `ANTHROPIC_API_KEY` | 否 | 備援；Claude vision |
| `GROQ_API_KEY` | 否 | 備援；Whisper-Turbo on Groq 為低成本 ASR API |
| `DEEPGRAM_API_KEY` / `ASSEMBLYAI_API_KEY` | 否 | hosted ASR + diarization |
| `JINA_API_KEY` / `EXA_API_KEY` | 否 | 外部查證 |

## 開發

```bash
# 測試
pytest

# Lint / format
ruff check .
ruff format .
```

## License

Apache 2.0；見 [`LICENSE`](LICENSE)。
