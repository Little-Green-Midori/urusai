"""Project settings —— API keys 跟 runtime 預設值。

Env vars 從 `.env` 讀（dev）或 process env（prod）。所有欄位預設空字串、
runtime 真要 call 才驗。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Primary LLM —— Gemma 4 31B IT via Google AI Studio (Gemini API)
    gemini_api_key: str = ""

    # 備援 LLM / VLM API
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    groq_api_key: str = ""

    # AI search / fetch APIs（escalation channel）
    jina_api_key: str = ""
    exa_api_key: str = ""

    # 選用 ASR providers（local faster-whisper 不需要）
    deepgram_api_key: str = ""
    assemblyai_api_key: str = ""


def get_settings() -> Settings:
    return Settings()
