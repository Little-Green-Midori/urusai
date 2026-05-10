# Changelog

本檔記錄 `urusai` 對外可見的行為變更。格式參考 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/)，版本號遵循 [SemVer](https://semver.org/lang/zh-TW/)。

## [0.0.1] - 2026-05-08

### Added

**Domain**

- `EvidenceClaim`：channel、time_range、claim_text、source_tool、confidence、可選 inference chain
- `TimeRange`、`ConfidenceMarker`、`InferenceStrength` enum
- `InventoryReport` + `ChannelAvailability`：content inventory probe 結果
- `Notebook` Protocol + 五個具體 Notebook（`DialogueNotebook`、`OnScreenTextNotebook`、`SceneNotebook`、`SoundEventNotebook`、`HolisticNotebook`）
- `TimeAxis`：跨 channel 時間軸 substrate（intervaltree-based）
- `StaticGraph` + `DynamicGraph`：圖層基底（節點、觀察邊、推論邊、audit history）

**Channels**

- `inventory_probe.run_inventory_probe()`：ffprobe + 音訊 / 影片 / 字幕 probe
- `SubtitleChannel`：人工字幕經 yt-dlp 抓取，pysrt / webvtt-py 解析
- `ASRChannel`：faster-whisper large-v3-turbo（CUDA + float16）
- `SceneChannel`：PySceneDetect ContentDetector

**Agent**

- `make_gemini_client()`：google-genai SDK 包裝
- `orchestrator_node`：rule-based dispatch（inventory check → 結構性 abstain 或 retrieve）
- `integrator_node`：Gemma 4 31B IT 呼叫，`response_mime_type="application/json"`
- `serialize_trace()` / `has_complete_trace()`
- `AgentState` Pydantic model

**Storage**

- `IngestState` dataclass + `IngestStore`（thread-safe in-memory dict）

**API**

- `POST /ingest`：file_path 或 url（yt-dlp 自動下載）
- `POST /query`：ingest_id + query
- `GET /healthz`

**UI**

- Streamlit 開發測試介面（透過 in-process FastAPI TestClient 呼叫 endpoints）

[0.0.1]: https://github.com/Little-Green-Midori/urusai/releases/tag/v0.0.1
