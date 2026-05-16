"""Provider selection — auto vs manual.

Provider selection: auto picks based on inventory probe + channel auto-rules; manual lets the caller override.

The auto rule per channel is registered by each channel's `__init__.py` via
`register_auto_rule(channel, fn)`. resolve_provider then either:

- mode="manual" + channel in overrides → build the override
- otherwise → call the channel's auto rule with the InventoryReport
"""
from __future__ import annotations

from typing import Awaitable, Callable, Literal, Protocol

from pydantic import BaseModel, Field

from urusai.domain.inventory import InventoryReport


class ProviderSelection(BaseModel):
    """Request-side knob: which providers to use for a given ingest / run."""

    mode: Literal["auto", "manual"] = "auto"
    overrides: dict[str, str] = Field(default_factory=dict)


class _AnyProvider(Protocol):
    """Common surface of all Provider Protocols (used for typing only)."""

    name: str


AutoRuleFn = Callable[[InventoryReport], Awaitable[_AnyProvider]]
_auto_rules: dict[str, AutoRuleFn] = {}


def register_auto_rule(channel: str, fn: AutoRuleFn) -> None:
    """Channel-side hook: register the auto-mode rule for this channel."""
    _auto_rules[channel] = fn


class ProviderRegistry:
    """Maps `"<channel>:<provider_id>"` strings to provider builders."""

    _builders: dict[str, Callable[[], _AnyProvider]] = {}

    @classmethod
    def register(cls, key: str, builder: Callable[[], _AnyProvider]) -> None:
        cls._builders[key] = builder

    @classmethod
    def build(cls, key: str) -> _AnyProvider:
        if key not in cls._builders:
            raise KeyError(f"no provider registered under key: {key!r}")
        return cls._builders[key]()

    @classmethod
    def known(cls) -> list[str]:
        return sorted(cls._builders.keys())


async def resolve_provider(
    channel: str,
    inventory: InventoryReport,
    selection: ProviderSelection,
) -> _AnyProvider:
    """Pick a concrete provider for a channel for this ingest.

    Manual mode overrides take priority. Otherwise the channel's registered
    auto rule is invoked.
    """
    if selection.mode == "manual" and channel in selection.overrides:
        return ProviderRegistry.build(selection.overrides[channel])
    if channel not in _auto_rules:
        raise KeyError(
            f"no auto rule registered for channel {channel!r}; "
            f"either register one or use manual mode with explicit overrides"
        )
    return await _auto_rules[channel](inventory)
