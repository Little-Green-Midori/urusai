"""Channel registry — maps channel concept → provider name → provider class.

Providers self-register at import time via the `@ChannelRegistry.register`
decorator. Importing `urusai.channels` triggers loading of all subpackages,
which triggers their provider imports, which triggers registration.

A channel concept without registered providers is a reserved slot (e.g. `ocr`,
`vlm`) — `list_providers(channel)` returns `[]` and `build()` raises
`KeyError`. No stub provider is registered.
"""
from __future__ import annotations

from typing import Callable, ClassVar

from pydantic import BaseModel

from urusai.channels.base import ChannelSpec, Provider


class ChannelRegistry:
    """Channel concept → provider name → provider class.

    Reserved slots (always present, may be empty):
      asr, scene, ocr, vlm, audio_event, mss
    """

    _channels: ClassVar[dict[str, dict[str, type[Provider]]]] = {
        "asr": {},
        "scene": {},
        "ocr": {},
        "vlm": {},
        "audio_event": {},
        "mss": {},
    }

    @classmethod
    def register(cls, *, channel: str, name: str) -> Callable[[type[Provider]], type[Provider]]:
        """Decorator: register a provider class under (channel, name)."""

        def decorator(provider_cls: type[Provider]) -> type[Provider]:
            cls._channels.setdefault(channel, {})[name] = provider_cls
            return provider_cls

        return decorator

    @classmethod
    def get(cls, channel: str, provider: str) -> type[Provider]:
        try:
            return cls._channels[channel][provider]
        except KeyError as exc:
            raise KeyError(
                f"channel={channel!r} provider={provider!r} not registered"
            ) from exc

    @classmethod
    def build(
        cls,
        channel: str,
        provider: str,
        config: dict | BaseModel | None = None,
    ) -> Provider:
        """Instantiate a provider with given config dict / BaseModel / None (defaults)."""
        provider_cls = cls.get(channel, provider)
        if config is None:
            cfg = provider_cls.config_class()  # type: ignore[call-arg]
        elif isinstance(config, BaseModel):
            cfg = config
        else:
            cfg = provider_cls.config_class(**config)  # type: ignore[call-arg]
        return provider_cls(cfg)  # type: ignore[call-arg]

    @classmethod
    def list_channels(cls) -> list[str]:
        return list(cls._channels.keys())

    @classmethod
    def list_providers(cls, channel: str) -> list[str]:
        return list(cls._channels.get(channel, {}).keys())

    @classmethod
    def spec(cls, channel: str, provider: str, config: BaseModel) -> ChannelSpec:
        """Build a `ChannelSpec` from a (channel, provider, config) triple."""
        return ChannelSpec(channel=channel, provider=provider, config=config.model_dump())
