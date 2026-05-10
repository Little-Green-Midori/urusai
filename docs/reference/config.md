# Configuration reference

Settings 走 `pydantic-settings` 的 `BaseSettings`，從 `.env`（dev）或 process env（prod）讀取。所有欄位預設空字串，runtime 真要 call 才驗。

> Source: [`src/urusai/config/settings.py`](../../src/urusai/config/settings.py) / [`.env.example`](../../.env.example)

## 環境變數對照

| 變數 | 必要 | 對應 setting field | 用途 |
|---|---|---|---|
| `GEMINI_API_KEY` | **是** | `gemini_api_key` | 主代理人 LLM（Gemma 4 31B IT）+ Gemini family vision / audio call |
| `OPENAI_API_KEY` | 否 | `openai_api_key` | 備援；Whisper API fallback、GPT vision |
| `ANTHROPIC_API_KEY` | 否 | `anthropic_api_key` | 備援；Claude vision |
| `GROQ_API_KEY` | 否 | `groq_api_key` | 備援；Whisper-Turbo on Groq（低成本 ASR API）|
| `JINA_API_KEY` | 否 | `jina_api_key` | Jina Reader（URL → markdown）|
| `EXA_API_KEY` | 否 | `exa_api_key` | Exa（語意 / 深度搜尋）|
| `DEEPGRAM_API_KEY` | 否 | `deepgram_api_key` | hosted ASR + diarization |
| `ASSEMBLYAI_API_KEY` | 否 | `assemblyai_api_key` | hosted ASR + diarization |

> 只強制 `GEMINI_API_KEY`。其餘皆為備援，實際 channel 用到才驗。

## 載入位置

- 開發：`.env` 在 repo 根目錄。`pip install -e .[dev]` 後 `pydantic-settings` 自動讀。
- 生產：直接走 process env。

## 取得 settings

```python
from urusai.config.settings import get_settings

settings = get_settings()
if not settings.gemini_api_key:
    raise RuntimeError("GEMINI_API_KEY not set")
```

每次 `get_settings()` 會新建 `Settings()` instance（讀 env），無 LRU cache；高頻呼叫的 module 應該自己 cache：

```python
# 例：urusai.agent.llm_client.make_gemini_client()
def make_gemini_client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY not set in .env...")
    return genai.Client(api_key=settings.gemini_api_key)
```

## Settings 行為

- `extra="ignore"`：未知 env var 不報錯
- `env_file=".env"`：自動找 repo 根目錄的 `.env`
- `env_file_encoding="utf-8"`

## API key 配額對照

主要免費 tier（依使用者 Google AI Studio console 快照、未來可能變動）：

| 服務 | RPM | RPD | TPM |
|---|---|---|---|
| Gemma 4 31B IT | 15 | 1500 | 不限 |
| Gemma 3 27B | 30 | 14400 | 15K |
| Gemini 3.1 Flash Lite | 15 | 500 | 250K |
| Gemini 3.1 Pro | 0 | 0 | 0 |
| Gemini Embedding 2 | 100 | 1000 | 30K |
| Search grounding（Gemini 2 / 2.5）| - | 1500 | - |

> 數字依使用者實際 console 為準。生產 / 高負載環境建議付費 tier。

## 安全注意

- `.env` 已在 `.gitignore`，**不要** commit 帶 key 的 `.env`。
- 若不慎 commit 過，立即 revoke key 重發。
- 不要在 docs / commit message / public log 印出 key 值。
