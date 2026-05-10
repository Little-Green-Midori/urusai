# How-to：配置 API keys

讓 urusai 拿到必要 / 可選的 API key。

## 必要：`GEMINI_API_KEY`

主代理人 LLM（Gemma 4 31B IT）跟 Gemini family vision / audio 都靠這把 key。

1. 到 [Google AI Studio](https://aistudio.google.com/apikey) 申請（免費 tier）。
2. 編輯 repo 根目錄 `.env`：

   ```
   GEMINI_API_KEY=AIzaSy...
   ```

3. 重啟 uvicorn / streamlit 讓 settings 重新讀。

驗證：

```bash
python -c "from urusai.config.settings import get_settings; s = get_settings(); print('ok' if s.gemini_api_key else 'EMPTY')"
```

## 可選：備援 LLM / VLM

| Key | 用途 |
|---|---|
| `OPENAI_API_KEY` | Whisper API fallback、GPT vision |
| `ANTHROPIC_API_KEY` | Claude vision |
| `GROQ_API_KEY` | Groq Whisper-Turbo（低成本 ASR API）|

## 可選：hosted ASR providers

| Key | 用途 |
|---|---|
| `DEEPGRAM_API_KEY` | Deepgram Nova-3（含 diarization）|
| `ASSEMBLYAI_API_KEY` | AssemblyAI Universal-3 Pro |

## 可選：外部查證

| Key | 用途 |
|---|---|
| `JINA_API_KEY` | Jina Reader（URL → markdown 抽正文）|
| `EXA_API_KEY` | Exa（語意 / 深度搜尋）|

## 安全注意

- `.env` 已在 `.gitignore`，**不要** commit。
- 不慎 commit 立即 revoke key、重發。
- 不要在 docs / commit message / log 印 key 值。

完整變數對照見 [`../reference/config.md`](../reference/config.md)。
