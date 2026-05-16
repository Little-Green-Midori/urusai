"""Multi-token rotation for API providers.

TokenRotator over multi-key provider configs with quota tracking, cooldown, and a 3-failure circuit breaker.

NOTE: Mid-stream hot-swap is NOT supported. KV cache locality on provider side
means a stream cannot be continued with a different token. Caller must:

- TTFT-pre failure  → silently retry with `rotator.acquire()` (next token)
- TTFT-post failure → keep partial, emit data-error event, abort run
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


class NoAvailableTokenError(RuntimeError):
    """All tokens are in cooldown — caller must abstain / fail run."""


@dataclass
class TokenRotator:
    """Token pool with quota tracking + cooldown + circuit breaker.

    Usage:
        rot = TokenRotator(settings.gemini_api_keys)
        try:
            tok = rot.acquire()
            # ... call provider with tok ...
            rot.update_quota(tok, remaining=int(resp.headers["X-RateLimit-Remaining"]))
        except RateLimitError:
            rot.mark_rate_limited(tok)
            # retry with next token (TTFT-pre only)
    """

    tokens: list[str]
    cooldown_sec: int = 60
    _cooldown: dict[str, float] = field(default_factory=dict)
    _quota_estimate: dict[str, int] = field(default_factory=dict)
    _failure_count: dict[str, int] = field(default_factory=dict)

    def acquire(self) -> str:
        """Pick a non-cooled-down token, prefer ones with higher estimated quota."""
        now = time.monotonic()
        candidates = sorted(
            (t for t in self.tokens if now >= self._cooldown.get(t, 0)),
            key=lambda t: -self._quota_estimate.get(t, 999_999),
        )
        if not candidates:
            raise NoAvailableTokenError("all tokens cooling down")
        return candidates[0]

    def mark_rate_limited(self, token: str, cooldown_sec: int | None = None) -> None:
        """Mark token as 429'd; circuit-breaker after 3 consecutive failures."""
        self._cooldown[token] = time.monotonic() + (cooldown_sec or self.cooldown_sec)
        self._failure_count[token] = self._failure_count.get(token, 0) + 1
        if self._failure_count[token] >= 3:
            # Circuit breaker: 5-minute cooldown
            self._cooldown[token] = time.monotonic() + 300

    def update_quota(self, token: str, remaining: int) -> None:
        """Update remaining quota estimate; success resets failure counter."""
        self._quota_estimate[token] = remaining
        self._failure_count[token] = 0

    def status(self) -> dict[str, dict[str, float | int]]:
        """For `/v1/system/limits` diagnostic endpoint."""
        now = time.monotonic()
        return {
            tok: {
                "cooldown_remaining_sec": max(0.0, self._cooldown.get(tok, 0) - now),
                "quota_estimate": self._quota_estimate.get(tok, -1),
                "failure_count": self._failure_count.get(tok, 0),
            }
            for tok in self.tokens
        }
