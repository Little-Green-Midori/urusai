"""Smoke test —— 確認 package 可 import、settings 可 load。"""


def test_import_package():
    import urusai

    assert urusai.__version__


def test_settings_loads_with_defaults():
    """所有 env vars 都可缺、settings 不該炸（runtime 才驗 key 是否非空）。"""
    from urusai.config.settings import get_settings

    settings = get_settings()
    assert isinstance(settings.gemini_api_key, str)
    assert isinstance(settings.openai_api_key, str)
    assert isinstance(settings.anthropic_api_key, str)
