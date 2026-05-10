# API reference

FastAPI app 在 `urusai.api.main:app`。啟動方式：

```bash
uvicorn urusai.api.main:app --reload
```

預設 host `127.0.0.1:8000`。互動式 OpenAPI 文件在 `/docs`、ReDoc 在 `/redoc`。

> Source: [`src/urusai/api/main.py`](../../src/urusai/api/main.py) / [`src/urusai/api/routes.py`](../../src/urusai/api/routes.py) / [`src/urusai/api/schemas.py`](../../src/urusai/api/schemas.py)

## 端點列表

| Method | Path | 用途 |
|---|---|---|
| `GET` | `/healthz` | 健康檢查 |
| `POST` | `/ingest` | 處理一支影片，產出 `IngestState` |
| `POST` | `/query` | 對已 ingest 的影片下 query |

---

## `GET /healthz`

健康檢查，無 request body。

**Response 200**

```json
{
  "status": "ok",
  "version": "0.0.1"
}
```

---

## `POST /ingest`

處理一支影片：跑 content inventory probe → dispatch channels → 落到 notebooks → 存進 `IngestStore`。

### Request body（`IngestRequest`）

```json
{
  "file_path": "string | null",
  "url": "string | null",
  "video_id": "string | null"
}
```

| 欄位 | 型別 | 必要 | 說明 |
|---|---|---|---|
| `file_path` | `str` | 二擇一 | 本機影片絕對 / 相對路徑 |
| `url` | `str` | 二擇一 | 影片 URL（yt-dlp 會下載到暫存檔）|
| `video_id` | `str` | 否 | 自訂 video id；省略則用自動產生的 ingest_id |

`file_path` 與 `url` **必須擇一**；若都缺則 400。

### Response 200（`IngestResponse`）

```json
{
  "ingest_id": "abc123def456",
  "inventory": {
    "video_id": "abc123def456",
    "source_path": "/tmp/urusai_video_xxx/abc.mp4",
    "inventory": {
      "has_audio": true,
      "has_speech": true,
      "has_music": false,
      "has_visual": true,
      "visual_static": false,
      "has_manual_subs": false,
      "subs_lang": null,
      "duration_sec": 240.5
    },
    "dispatched_channels": ["ASRChannel", "SceneChannel"],
    "skipped_channels": {
      "SubtitleChannel": "no manual subs available"
    }
  },
  "notebooks": {
    "dialogue": 47,
    "on_screen_text": 0,
    "scene": 12,
    "sound_event": 0,
    "holistic": 0
  }
}
```

| 欄位 | 說明 |
|---|---|
| `ingest_id` | 12-char hex；後續 `/query` 用此查找 |
| `inventory` | `InventoryReport`，見 [`schemas.md`](schemas.md) |
| `notebooks` | 各筆記吸收的 evidence 條目數 |

### Response 400

- `file_path or url required`：兩個欄位都缺
- `file not found: <path>`：file_path 指向的檔案不存在
- `yt-dlp download failed: <stderr>`：URL 下載失敗
- `yt-dlp produced no video file`：下載完成但找不到視訊檔

---

## `POST /query`

對已 ingest 的影片下 query，跑 agent loop。

### Request body（`QueryRequest`）

```json
{
  "ingest_id": "abc123def456",
  "query": "她在開頭說了什麼？"
}
```

| 欄位 | 型別 | 必要 | 說明 |
|---|---|---|---|
| `ingest_id` | `str` | 是 | 從 `/ingest` 拿到 |
| `query` | `str` | 是 | 自然語言查詢 |

### Response 200（`QueryResponse`）

```json
{
  "status": "answered",
  "answer": "她在 02:14-02:17 說『我會再想想』",
  "cited_evidence": [
    {
      "index": 3,
      "channel": "dialogue",
      "start_sec": 134.2,
      "end_sec": 137.5,
      "text": "我會再想想",
      "source_tool": "faster-whisper:large-v3-turbo:zh"
    }
  ],
  "abstain_kind": null,
  "abstain_reason": null,
  "trace": "[3] dialogue 134.20-137.50s '我會再想想' (source: faster-whisper:large-v3-turbo:zh)"
}
```

`status="abstain"` 時：

```json
{
  "status": "abstain",
  "answer": null,
  "cited_evidence": [],
  "abstain_kind": "structural" | "evidence_insufficient",
  "abstain_reason": "影片無語音也無人工字幕、對白本為空、無法回答對白相關 query。",
  "trace": "[0] dialogue 0.00-3.20s ..."  // retrieved evidence 仍序列化、便於 debug
}
```

| 欄位 | 說明 |
|---|---|
| `status` | `"answered"` 或 `"abstain"` |
| `answer` | answered 時非空、abstain 時 null |
| `cited_evidence` | answered 時 evidence 條目陣列、abstain 時為空 |
| `abstain_kind` | `"structural"`（影片本身無此層）/ `"evidence_insufficient"`（有層但檢索無命中）|
| `abstain_reason` | 人類可讀說明 |
| `trace` | retrieved evidence 序列化字串；answered 時只列 cited、abstain 時列全部 |

### Response 404

```json
{"detail": "ingest_id not found: <id>"}
```

---

## `EvidenceItem` schema

`QueryResponse.cited_evidence` 元素：

| 欄位 | 型別 | 說明 |
|---|---|---|
| `index` | `int` | 在 `retrieved_evidence` 中的索引 |
| `channel` | `str` | 對應筆記名稱 |
| `start_sec` | `float` | 起始秒 |
| `end_sec` | `float` | 結束秒 |
| `text` | `str` | claim 內容 |
| `source_tool` | `str` | 工具識別字（含版本 / 設定）|

---

## CORS / 認證

無 CORS 設定、無認證；不適合直接公開部署。
