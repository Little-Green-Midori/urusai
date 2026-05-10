"""Gemini API client for Gemma 4 31B IT —— urusai 主代理人 LLM。

Gemma 4 31B IT 透過 Google AI Studio 的 Gemini API 呼叫，
使用 google-genai SDK。
"""
from __future__ import annotations

from google import genai

from urusai.config.settings import get_settings


DEFAULT_MODEL = "gemma-4-31b-it"


def make_gemini_client() -> genai.Client:
    """建立 Gemini API client；GEMINI_API_KEY 必須已設定。"""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set in .env; required for Gemma 4 31B IT calls"
        )
    return genai.Client(api_key=settings.gemini_api_key)
