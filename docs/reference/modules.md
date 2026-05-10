# Module map

`src/urusai/` 各 sub-package 的職責與依賴方向。

> Source tree：[`src/urusai/`](../../src/urusai/)

## 整體圖

```
urusai/
├── domain/      ← 純資料模型，無外部 service 依賴
├── channels/    ← 從影片抽 evidence，依賴 domain + 各工具 SDK
├── store/       ← ingest 結果儲存
├── config/      ← settings / env vars
├── agent/       ← query 階段 orchestrator + integrator
└── api/         ← FastAPI HTTP 層
```

依賴方向（上層依賴下層）：

```
api  →  agent  →  store  →  channels  →  domain
                ↑           ↑
                └─ config ──┘
```

無循環依賴。

---

## `urusai.domain`

純資料模型 + Protocol。**不允許 import 任何外部 service SDK**。

| 檔 | 內容 |
|---|---|
| `evidence.py` | `EvidenceClaim`、`TimeRange`、`ConfidenceMarker`、`InferenceStrength` |
| `inventory.py` | `ChannelAvailability`、`InventoryReport` |
| `notebook.py` | `Notebook` Protocol + 5 個具體 Notebook 實作 |
| `time_axis.py` | `TimeAxis`（intervaltree wrapper）|
| `graph.py` | `StaticGraph` / `DynamicGraph`、`NodeType`、`ObservationEdgeType`、`InferenceEdgeType` |

詳細 schema 見 [`schemas.md`](schemas.md)。

---

## `urusai.channels`

從影片抽 evidence。每個 channel 一個 module，繼承 `Channel` Protocol。

| 檔 | 內容 |
|---|---|
| `base.py` | `Channel` Protocol（`name`、`async extract`）|
| `inventory_probe.py` | ffprobe + DSP audio probe + DSP video probe + yt-dlp 字幕清單 |
| `subtitle.py` | yt-dlp 抓人工字幕 + pysrt / webvtt-py 解析 |
| `asr.py` | faster-whisper large-v3-turbo（CUDA + float16）|
| `scene.py` | PySceneDetect ContentDetector |
| `ocr.py` | 空模組 |
| `vlm.py` | 空模組 |
| `audio_event.py` | 空模組 |
| `mss.py` | 空模組 |

### Channel 介面

```python
class Channel(Protocol):
    name: str

    async def extract(
        self,
        source: Path,
        time_range: tuple[float, float] | None = None,
        **kwargs,
    ) -> list[EvidenceClaim]: ...
```

`extract()` 為 async（多數工具有 IO 或 GPU 工作）。`time_range` 為 None 表示整支影片。

每個 channel 產出的 `EvidenceClaim` 必須帶：

- 對應 `channel` 名稱
- `source_tool` 含版本 / 設定（範例：`"faster-whisper:large-v3-turbo:zh"`、`"PaddleOCR:3.4.0"`、`"PySceneDetect:ContentDetector:t=27.0"`）
- 合理 `confidence_marker`（不要全標 `clear`）

---

## `urusai.store`

| 檔 | 內容 |
|---|---|
| `ingest_store.py` | `IngestState` dataclass + `IngestStore`（thread-safe in-memory dict）+ `get_default_store()` singleton |

`IngestState` 內含五本 `Notebook` + `TimeAxis` + `StaticGraph` + `created_at`。`absorb(claims)` 把 channel claims 落到對應 notebook + time_axis。

---

## `urusai.config`

| 檔 | 內容 |
|---|---|
| `settings.py` | `Settings`（`pydantic-settings.BaseSettings`）+ `get_settings()` |

詳見 [`config.md`](config.md)。

---

## `urusai.agent`

Query 階段。

| 檔 | 內容 |
|---|---|
| `llm_client.py` | `make_gemini_client()` / `DEFAULT_MODEL = "gemma-4-31b-it"` |
| `prompts.py` | `INTEGRATOR_SYSTEM` system prompt + `integrator_user_prompt()` builder |
| `state.py` | `AgentState` Pydantic model + `MAX_TURNS = 10` |
| `nodes.py` | `orchestrator_node()` rule-based + `integrator_node()` Gemma 4 31B IT call |
| `trace.py` | `serialize_trace()` / `has_complete_trace()` |
| `graph.py` | `run_query(query, ingest)` 串 orchestrator → integrator |

### LLM 呼叫

`integrator_node` 用 `google-genai` SDK 呼叫 Gemma 4 31B IT：

```python
client.models.generate_content(
    model=DEFAULT_MODEL,  # "gemma-4-31b-it"
    contents=user_msg,
    config=types.GenerateContentConfig(
        system_instruction=INTEGRATOR_SYSTEM,
        response_mime_type="application/json",
        temperature=0.1,
    ),
)
```

`response_mime_type="application/json"` 強制結構化輸出。Schema 在 system prompt 內定義（status / answer / cited_evidence_indices / abstain_kind / abstain_reason）。

---

## `urusai.api`

| 檔 | 內容 |
|---|---|
| `main.py` | `create_app()` → FastAPI app；`/healthz` |
| `routes.py` | `POST /ingest` + `POST /query` 處理 |
| `schemas.py` | `IngestRequest` / `IngestResponse` / `QueryRequest` / `QueryResponse` / `EvidenceItem` |

詳見 [`api.md`](api.md)。

---

## `streamlit_app.py`（repo 根目錄、非 package 內）

開發測試 UI。透過 `fastapi.testclient.TestClient` in-process 呼叫 API endpoints，跟外部 HTTP client 走同一條 code path。

---

## `tests/`

| 檔 | 內容 |
|---|---|
| `test_smoke.py` | smoke test |

PR 必須跑 `pytest`。新增 channel / agent node 必須附 unit test。
