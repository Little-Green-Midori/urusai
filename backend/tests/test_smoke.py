"""Smoke tests: package imports cleanly and settings load with defaults."""


def test_import_package():
    import urusai

    assert urusai.__version__


def test_settings_loads_with_defaults():
    """All API key env vars are optional; settings must load without error."""
    from urusai.config.settings import get_settings

    settings = get_settings()
    assert isinstance(settings.gemini_api_keys, list)
    assert isinstance(settings.openai_api_keys, list)
    assert isinstance(settings.anthropic_api_keys, list)
