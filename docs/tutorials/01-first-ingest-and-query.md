# Tutorial 01：第一次 ingest 與 query

從零開始，跑通 urusai 的完整流程：安裝 → 設定 → ingest 一支影片 → 問問題 → 看 evidence trace。

預計時間：15–30 分鐘（首次 ASR 模型下載約 1.6 GB）。

## 你會學到

- 如何安裝 urusai 開發環境
- 如何啟動 FastAPI server 跟 Streamlit 介面
- ingest 流程實際輸出長什麼樣
- query 後 cited evidence 與 trace 怎麼讀
- abstain 兩類在實際情境中的觸發條件

## 前置需求

- Python 3.11+
- `ffmpeg`、`yt-dlp` 在 `PATH` 上
- Google AI Studio API key（[從這裡申請](https://aistudio.google.com/apikey)）
- 一支影片檔（建議 1〜5 分鐘的有對白影片，本地 mp4 或 YouTube URL 皆可）
- CUDA-capable GPU（建議；無 GPU faster-whisper 走 CPU 但慢）

## 步驟 1：安裝

```bash
git clone https://github.com/Little-Green-Midori/urusai.git
cd urusai
python -m venv .venv
source .venv/bin/activate    # Windows PowerShell：.venv\Scripts\Activate.ps1
pip install -e .[dev]
```

## 步驟 2：設定 API key

```bash
cp .env.example .env
```

編輯 `.env`、把 `GEMINI_API_KEY=` 那行填上你的 key：

```
GEMINI_API_KEY=AIzaSy...
```

其他 key 都可空著。

> 完整變數對照見 [`../reference/config.md`](../reference/config.md)。

## 步驟 3：起 API server

```bash
uvicorn urusai.api.main:app --reload
```

預期看到：

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
INFO:     Application startup complete.
```

驗證：

```bash
curl http://localhost:8000/healthz
# {"status":"ok","version":"0.0.1"}
```

## 步驟 4：起 Streamlit dev UI

開新 terminal、同樣啟動 venv：

```bash
streamlit run streamlit_app.py
```

瀏覽器會自動開 `http://localhost:8501`。左側 sidebar 應顯示 GPU / VRAM 資訊，以及 `FastAPI in-process · v0.0.1`。

## 步驟 5：ingest 第一支影片

在 Streamlit 的「**影片 ingest**」分頁：

- 上傳本機影片，或
- 貼 YouTube URL（`yt-dlp` 會自動下載到暫存）

點「開始 ingest」，等待。首次會下載 faster-whisper large-v3-turbo 模型（約 1.6 GB），之後 cache 在本地。

完成後會顯示：

- **Inventory probe 結果**：duration、has_speech、has_visual、has_music、visual_static、manual_subs
- **dispatched channels**：實際跑的 channel 列表（例如 `ASRChannel`、`SceneChannel`）
- **skipped channels**：因 inventory 為空跳過的 channel

切到「**5 本筆記**」分頁，會看到對白本（`dialogue`）跟場景本（`scene`）有 entry 數。

## 步驟 6：第一個 query

切到「**Query**」分頁，輸入問題。試試這幾類：

### 6.1 對白引用 query（適合短影片）

```
她在開頭說了什麼？
```

預期 `status: answered`，下方列出 cited evidence（例如對白本第 0〜2 條），並附 `source_tool` 標註是 `faster-whisper:large-v3-turbo:zh`（或對應 lang）。

### 6.2 結構性 abstain（如果上傳的是純音樂或純畫面影片）

```
她說了什麼？
```

如果 inventory 顯示 `has_speech=false` 且 `has_manual_subs=false`，預期 `status: abstain`、`abstain_kind: structural`，理由「影片無語音也無人工字幕、對白本為空」。

### 6.3 證據不足 abstain

問一個對白本沒抓到的內容：

```
她有提到任何科幻名詞嗎？
```

如果對白本沒有相關內容、ASR 也沒匹配，可能：

- LLM 直接回 abstain，`abstain_kind: evidence_insufficient`
- 或勉強答但 cited evidence 弱、trace 標源頭

## 步驟 7：讀 Evidence trace

切到「**Evidence trace**」分頁，看完整序列化字串：

```
[0] dialogue 0.20-3.40s '大家好，今天要分享...' (source: faster-whisper:large-v3-turbo:zh)
[1] dialogue 3.50-7.20s '一個關於 Video RAG 的想法' (source: faster-whisper:large-v3-turbo:zh)
[2] scene 0.00-15.50s 'scene 1' (source: PySceneDetect:ContentDetector:t=27.0)
...
```

每行格式：`[index] channel start-end claim_text (source: source_tool)`。

answered 時：trace 只列 cited 的條目。
abstain 時：trace 列**全部** retrieved evidence，便於 debug。

## 步驟 8：直接打 API（不用 UI）

```bash
# ingest
curl -X POST http://localhost:8000/ingest \
  -H 'content-type: application/json' \
  -d '{"file_path": "/abs/path/to/video.mp4"}'
# -> {"ingest_id": "abc123def456", "inventory": {...}, "notebooks": {...}}

# query
curl -X POST http://localhost:8000/query \
  -H 'content-type: application/json' \
  -d '{"ingest_id": "abc123def456", "query": "她在開頭說了什麼？"}'
```

完整 schema 見 [`../reference/api.md`](../reference/api.md)。

## 你現在會什麼

- 跑通 urusai 完整 pipeline
- 看懂 inventory probe 報告 + dispatched channels
- 解讀 cited evidence + source_tool
- 區分 structural vs evidence_insufficient abstain
- 讀 evidence trace 序列化字串

## 接下來

- 完整 API 規格：[`../reference/api.md`](../reference/api.md)
- Domain schemas：[`../reference/schemas.md`](../reference/schemas.md)
- 加新 channel：[`../how-to/add-a-new-channel.md`](../how-to/add-a-new-channel.md)

## 常見問題

**Q：ingest 卡很久沒回應？**
A：首次跑 faster-whisper 會下載 1.6 GB 模型；後續會快很多。如果用 CPU、ASR 處理速度約 0.3〜0.5× real-time。

**Q：`GEMINI_API_KEY not set` error？**
A：確認 `.env` 在 repo 根目錄、且該行沒被註解掉。重啟 uvicorn 讓 settings 重新讀 env。

**Q：Streamlit `ModuleNotFoundError: urusai`？**
A：你的 streamlit 不在裝有 urusai 的 venv。用 `python -m streamlit run streamlit_app.py`，或先 activate venv。

**Q：query 一直回 abstain？**
A：先看 inventory：`has_speech` 是 false 嗎？是的話就是純畫面 / 純音樂影片。否則檢查 trace 裡 retrieved evidence 是否有相關內容。

**Q：ASR lang 抓錯？**
A：`ASRChannel` 自動偵測 lang。多語混合影片可能掉準度。
