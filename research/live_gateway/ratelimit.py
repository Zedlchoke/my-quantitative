"""Machine-wide request budget + request coalescing (plan §5).

All gateway-originated upstream REST calls pass through ONE
RateLimiter: min-gap pacing, requests/minute cap, IP weight budgets
(soft 1200 / hard 1800, measured from X-MBX-USED-WEIGHT-1M) and
bounded jittered exponential backoff. Concurrent identical canonical
requests share a single inflight call (Coalescer).
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .timeutils import NowMs, default_now_ms

MIN_GAP_S = 0.25
MAX_RPM = 60
SOFT_WEIGHT = 1200
HARD_WEIGHT = 1800
BACKOFF_BASE_S = 2.0
BACKOFF_FACTOR = 2.0
BACKOFF_CAP_S = 30.0
JITTER = 0.20
MAX_TRANSPORT_RETRIES = 4
CALL_TIMEOUT_S = 20.0
NON_ESSENTIAL_ENDPOINTS = (
    "/fapi/v1/time",
    "/fapi/v1/exchangeInfo",
)


def backoff_delay_ms(attempt: int, rng: Optional[random.Random] = None) -> int:
    """Bounded jittered exponential backoff in ms (±20%)."""
    rng = rng or random
    base = min(
        BACKOFF_BASE_S * (BACKOFF_FACTOR**attempt), BACKOFF_CAP_S
    )
    jittered = base * (1.0 + rng.uniform(-JITTER, JITTER))
    return int(max(0.0, jittered) * 1000)


@dataclass
class RateLimiter:
    """Pacing + budget gate for upstream REST calls."""

    now_ms: NowMs = field(default=default_now_ms)
    min_gap_ms: int = 250
    max_rpm: int = MAX_RPM
    soft_weight: int = SOFT_WEIGHT
    hard_weight: int = HARD_WEIGHT
    last_request_ms: Optional[int] = None
    request_times_ms: list = field(default_factory=list)
    used_weight: Optional[int] = None
    counts: Dict[str, int] = field(default_factory=lambda: {
        "issued": 0, "rate_gap_waits": 0, "rpm_waits": 0,
        "soft_weight_stops": 0, "hard_weight_stops": 0,
    })

    def observe_weight_header(self, value: Optional[str]) -> None:
        if value and value.strip().isdigit():
            self.used_weight = int(value.strip())

    def budget_block(self, path: str) -> Optional[str]:
        """Return a block reason if a request to path must not issue."""
        if self.used_weight is not None and self.used_weight >= self.hard_weight:
            self.counts["hard_weight_stops"] += 1
            return f"hard weight stop ({self.used_weight} >= {self.hard_weight})"
        if (
            self.used_weight is not None
            and self.used_weight >= self.soft_weight
            and path in NON_ESSENTIAL_ENDPOINTS
        ):
            self.counts["soft_weight_stops"] += 1
            return f"soft budget stop ({self.used_weight} >= {self.soft_weight})"
        now = self.now_ms()
        # rpm window
        self.request_times_ms = [
            t for t in self.request_times_ms if now - t < 60_000
        ]
        if len(self.request_times_ms) >= self.max_rpm:
            self.counts["rpm_waits"] += 1
            return f"rpm cap ({len(self.request_times_ms)} >= {self.max_rpm})"
        return None

    def note_issued(self) -> None:
        now = self.now_ms()
        self.last_request_ms = now
        self.request_times_ms.append(now)
        self.counts["issued"] += 1

    def gap_wait_ms(self) -> int:
        """ms to wait for the min-gap law (0 = no wait)."""
        if self.last_request_ms is None:
            return 0
        delta = self.now_ms() - self.last_request_ms
        if delta >= self.min_gap_ms:
            return 0
        self.counts["rate_gap_waits"] += 1
        return self.min_gap_ms - delta

    def stats(self) -> dict:
        return {
            "issued_total": self.counts["issued"],
            "rate_gap_waits": self.counts["rate_gap_waits"],
            "rpm_waits": self.counts["rpm_waits"],
            "soft_weight_stops": self.counts["soft_weight_stops"],
            "hard_weight_stops": self.counts["hard_weight_stops"],
            "used_weight_1m": self.used_weight,
            "soft_weight": self.soft_weight,
            "hard_weight": self.hard_weight,
            "max_rpm": self.max_rpm,
        }


class Coalescer:
    """Concurrent identical canonical requests share ONE inflight call.

    Every suppressed duplicate increments ``suppressed_duplicates``.
    """

    def __init__(self) -> None:
        self._inflight: Dict[str, asyncio.Future] = {}
        self.suppressed_duplicates = 0

    async def run(self, key: str, factory):
        """Factory is a zero-arg coroutine producing the result."""
        existing = self._inflight.get(key)
        if existing is not None:
            self.suppressed_duplicates += 1
            return await asyncio.shield(existing)
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._inflight[key] = future
        try:
            result = await factory()
            if not future.done():
                future.set_result(result)
            return result
        except BaseException as exc:  # noqa: BLE001 - propagate to all waiters
            if not future.done():
                future.set_exception(exc)
            raise
        finally:
            self._inflight.pop(key, None)
