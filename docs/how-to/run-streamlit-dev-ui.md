# How-to：跑開發測試 UI

`streamlit_app.py` 透過 in-process FastAPI TestClient 呼叫 endpoints，跟外部 HTTP client 走同一條 code path。

## 跑起來

```bash
# 確認 venv 啟用了
source .venv/bin/activate    # Windows PowerShell：.venv\Scripts\Activate.ps1

# 啟動
streamlit run streamlit_app.py
```

預設開 `http://localhost:8501`。

## 介面結構

- **Sidebar**：硬體資訊（GPU、VRAM、CUDA、torch）+ FastAPI 健康狀態
- **影片 ingest 分頁**：上傳檔案或貼 URL → 觀察 inventory probe 結果 + dispatched / skipped channels
- **5 本筆記分頁**：每本 notebook 的 entry 數
- **Query 分頁**：輸入問題 → 看 answered 答案 + cited evidence，或 abstain 理由
- **Evidence trace 分頁**：完整 serialize_trace 字串

## 常見錯誤

### `ModuleNotFoundError: No module named 'urusai'`

你的 streamlit 不在裝有 urusai 的 venv。改用：

```bash
python -m streamlit run streamlit_app.py
```

或先 `source .venv/bin/activate`。

### Sidebar 顯示 `torch installed but CUDA unavailable`

torch 是 CPU-only 版。安裝 cu128 版：

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

或直接接受 CPU 模式（faster-whisper 會慢很多）。

### `GEMINI_API_KEY not set`

照 [configure-api-keys.md](configure-api-keys.md) 設定。

### ingest 卡住

- 首次：在下載 faster-whisper 1.6 GB 模型，等。
- 後續：CPU 上 ASR 慢；或 yt-dlp URL 下載中。看 terminal log 確認。

### 想看 raw API 回應

直接打 API 看完整 JSON：

```bash
curl -X POST http://localhost:8000/ingest -H 'content-type: application/json' -d '{...}'
```

API 規格見 [`../reference/api.md`](../reference/api.md)。
