# URUSAI

> Video RAG agent that refuses to answer without grounded evidence.

URUSAI extracts per-modality evidence from a video — subtitles, ASR, scene boundaries, on-screen text, speaker turns, visual descriptions, audio events — and answers questions by retrieving and citing those evidence claims. Every answer must point back to a timestamped source; when evidence is missing, URUSAI abstains rather than guess.

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16 (App Router) + React 19 + Vercel AI SDK v5 + Tailwind v4 + shadcn/ui (base-ui) |
| Backend | Python 3.11 + FastAPI + LangGraph 1.x + SQLAlchemy async + pymilvus |
| Orchestration | LangGraph `AsyncPostgresSaver` over thread / run / interrupt / job resources |
| Storage | Postgres 16 (channel-open schema) + Milvus 2.5 (multi-vector hybrid: dense + BM25 sparse) |
| Channels | dialogue / subtitle / scene / ocr / diarization / vlm / audio_event / mss |
| LLM | Gemini family (default) + OpenAI / Anthropic / Qwen / Groq / Deepgram / AssemblyAI (fallbacks) |
| Streaming | SSE with deterministic event_id + `Last-Event-ID` resume |

## Repo layout

```
urusai/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── THIRD_PARTY_MODELS.md
├── pnpm-workspace.yaml
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── scripts/
│   └── src/urusai/{domain,providers,ingest,rag,agent,api,config,db}/
└── frontend/
    ├── package.json
    └── src/{app,components,lib}/
```

## Quick start

### 1. Infra

```bash
docker compose up -d
```

Brings up Postgres (host port 5433), Milvus 2.5 (gRPC host port 19531), etcd, MinIO, Attu. Non-default host ports avoid collisions with other local Postgres / Milvus installs.

### 2. Backend

```bash
conda activate urusai
cd backend
pip install -e ".[dev]"
cp .env.example .env   # fill in GEMINI_API_KEY at minimum
alembic upgrade head
uvicorn urusai.api.main:app --reload --port 8000
```

`GET http://localhost:8000/healthz` → `{"status":"ok"}`.

### 3. Frontend

```bash
cd ..                   # repo root
pnpm install
pnpm --filter @urusai/frontend dev
```

Dev server at `http://localhost:3000`.

## Configuration

`backend/.env` (copy from `backend/.env.example`):

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Main LLM + `gemini-embedding-2`. Comma-separated values enable multi-token rotation. |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | No | LLM + vision fallback (OpenAI also unlocks `text-embedding-3` + Whisper API). |
| `GROQ_API_KEY` / `DASHSCOPE_API_KEY` / `COHERE_API_KEY` / `MISTRAL_API_KEY` / `XAI_API_KEY` / `TOGETHER_API_KEY` / `FIREWORKS_API_KEY` / `OPENROUTER_API_KEY` | No | Additional LLM / VLM fallbacks (Cohere also unlocks Embed v3 + Rerank v3.5; Mistral also unlocks Pixtral vision; Fireworks also unlocks hosted Llama-Vision; OpenRouter fans out to 100+ models). |
| `VOYAGE_API_KEY` | No | Voyage AI embeddings + reranker. |
| `DEEPGRAM_API_KEY` / `ASSEMBLYAI_API_KEY` / `ELEVENLABS_API_KEY` / `GLADIA_API_KEY` | No | Hosted ASR + diarization fallback. |
| `HF_TOKEN` | No | HuggingFace User Access Token (auto-picked by huggingface_hub / transformers / pyannote.audio for gated weights). |
| `JINA_API_KEY` / `EXA_API_KEY` / `TAVILY_API_KEY` / `BRAVE_SEARCH_API_KEY` / `SERPER_API_KEY` / `PERPLEXITY_API_KEY` | No | External fetch + search for escalation (HITL-gated). Jina key also unlocks Jina Embeddings + Reranker. |
| `PG_*` / `MILVUS_*` | Yes | Match `docker-compose.yml` defaults. |

Full reference: [`backend/.env.example`](backend/.env.example).

## Development

```bash
# Backend
cd backend
pytest
ruff check src/ tests/
ruff format src/ tests/

# Frontend (from repo root)
pnpm --filter @urusai/frontend typecheck
pnpm --filter @urusai/frontend lint
pnpm --filter @urusai/frontend build
```

## License

Apache 2.0. See [`LICENSE`](LICENSE).
