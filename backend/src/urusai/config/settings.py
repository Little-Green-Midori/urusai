"""Settings for URUSAI backend.

Loaded from backend/.env (via pydantic-settings). Every LLM / search API key
field supports comma-separated multi-token rotation
(see the multi-token entries in backend/.env.example).

NoDecode is required on every list[str] field because pydantic-settings v2
tries json.loads() first on list-typed env values. With NoDecode, the
field_validator (mode=before) sees the raw string and splits on commas.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _split_tokens(v: str | list[str] | None) -> list[str]:
    """Parse a comma-separated env value into a clean list of tokens."""
    if v is None:
        return []
    if isinstance(v, list):
        return [t.strip() for t in v if t and t.strip()]
    if isinstance(v, str):
        return [t.strip() for t in v.split(",") if t.strip()]
    return []


# Type alias keeps annotations readable.
TokenList = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    """URUSAI runtime settings.

    All `*_api_keys: TokenList` fields are parsed from comma-separated env
    values and consumed by `urusai.providers.rotation.TokenRotator`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # LLM provider tokens (multi-token rotation).
    gemini_api_keys: TokenList = Field(default_factory=list, alias="GEMINI_API_KEY")
    openai_api_keys: TokenList = Field(default_factory=list, alias="OPENAI_API_KEY")
    anthropic_api_keys: TokenList = Field(default_factory=list, alias="ANTHROPIC_API_KEY")
    groq_api_keys: TokenList = Field(default_factory=list, alias="GROQ_API_KEY")
    dashscope_api_keys: TokenList = Field(default_factory=list, alias="DASHSCOPE_API_KEY")

    # ASR fallback (hosted).
    deepgram_api_keys: TokenList = Field(default_factory=list, alias="DEEPGRAM_API_KEY")
    assemblyai_api_keys: TokenList = Field(default_factory=list, alias="ASSEMBLYAI_API_KEY")

    # HF gated models. Canonical env var: HF_TOKEN (auto-picked by huggingface_hub).
    huggingface_tokens: TokenList = Field(default_factory=list, alias="HF_TOKEN")

    # Escalator: external search / fetch.
    jina_api_keys: TokenList = Field(default_factory=list, alias="JINA_API_KEY")
    exa_api_keys: TokenList = Field(default_factory=list, alias="EXA_API_KEY")
    tavily_api_keys: TokenList = Field(default_factory=list, alias="TAVILY_API_KEY")

    # Postgres (single connection — no rotation).
    # pg_password default is for local docker-compose dev only; production
    # MUST override via the PG_PASSWORD env var.
    pg_host: str = "127.0.0.1"
    pg_port: int = 5433
    pg_user: str = "urusai"
    pg_password: str = "urusai_dev_pw"
    pg_database: str = "urusai"

    # Milvus (single connection).
    milvus_uri: str = "http://127.0.0.1:19531"
    milvus_token: str = ""

    # PaddleOCR-VL local backend.
    paddleocr_vl_backend: str = "llama-cpp-server"
    paddleocr_vl_server_url: str = "http://127.0.0.1:8111/v1"

    # Runtime.
    run_events_retention_hours: int = 24

    @field_validator(
        "gemini_api_keys", "openai_api_keys", "anthropic_api_keys",
        "groq_api_keys", "dashscope_api_keys", "deepgram_api_keys",
        "assemblyai_api_keys", "huggingface_tokens",
        "jina_api_keys", "exa_api_keys", "tavily_api_keys",
        mode="before",
    )
    @classmethod
    def _split_token_list(cls, v):
        return _split_tokens(v)

    @property
    def langgraph_postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    @property
    def sqlalchemy_async_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """FastAPI dependency-injectable settings singleton."""
    return Settings()
