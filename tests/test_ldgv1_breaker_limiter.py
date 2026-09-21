"""LIVE-DATA-GATEWAY-V1 tests: circuit breaker + rate limiter + coalescer.

Offline fixtures only (plan §12). NOT_RUN stays NOT_RUN — nothing here
touches the network.
"""

from __future__ import annotations

import asyncio

import pytest

from research.live_gateway.circuit import (
    CircuitBreaker,
    classify_response,
    parse_retry_after_ms,
)
from research.live_gateway.ratelimit import (
    Coalescer,
    RateLimiter,
    backoff_delay_ms,
)


class FakeClock:
    def __init__(self, start_ms: int = 1_700_000_000_000):
        self.ms = start_ms

    def __call__(self) -> int:
        return self.ms

    def advance(self, delta_ms: int) -> None:
        self.ms += delta_ms


# ----------------------------------------------------------------------
# Retry-After / banned-until parsing (§12: header-only, body-only,
# both, neither)
# ----------------------------------------------------------------------
def test_retry_after_header_delta_seconds():
    clock = FakeClock()
    expiry = parse_retry_after_ms("30", "", clock())
    assert expiry == clock() + 30_000


def test_retry_after_http_date():
    expiry = parse_retry_after_ms(
        "Thu, 01 Jan 2026 00:00:00 GMT", "", 1_700_000_000_000
    )
    assert expiry == 1_767_225_600_000


def test_retry_after_banned_until_body_ms():
    clock = FakeClock()
    expiry = parse_retry_after_ms(None, "Way too many requests; IP banned until 1700000060000", clock())
    assert expiry == 1_700_000_060_000


def test_retry_after_banned_until_body_seconds():
    clock = FakeClock()
    expiry = parse_retry_after_ms(None, "banned until 1700000123", clock())
    assert expiry == 1_700_000_123_000


def test_retry_after_both_longer_wins():
    clock = FakeClock()
    expiry = parse_retry_after_ms(
        "10", "banned until 1700000600", clock()
    )
    assert expiry == 1_700_000_600_000  # body (seconds) longer than header


def test_retry_after_neither():
    assert parse_retry_after_ms(None, "plain error", 1) is None
    assert parse_retry_after_ms("", "", 1) is None


# ----------------------------------------------------------------------
# classification law
# ----------------------------------------------------------------------
def test_classify_418_opens_breaker():
    v = classify_response(418, None, "banned until 9999999999999", 1)
    assert v.opens_breaker and not v.retryable and not v.non_retryable


def test_classify_429_opens_breaker():
    v = classify_response(429, "20", "", 1000)
    assert v.opens_breaker and v.retry_after_ms_expiry == 21_000


def test_classify_5xx_retryable_only_without_retry_after():
    v = classify_response(503, None, "", 1)
    assert v.retryable and not v.opens_breaker
    v2 = classify_response(503, "15", "", 1000)
    assert not v2.retryable and v2.retry_after_ms_expiry == 16_000


def test_classify_403_non_retryable_fail_fast():
    v = classify_response(403, None, "Forbidden", 1)
    assert v.non_retryable and not v.retryable and not v.opens_breaker


def test_classify_200_ok():
    v = classify_response(200, None, "[]", 1)
    assert v.kind == "ok"


# ----------------------------------------------------------------------
# breaker lifecycle
# ----------------------------------------------------------------------
def test_418_opens_breaker_zero_retry_window_and_suppress_count():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    breaker.observe_response(418, "60", "banned until whatever", "u1")
    assert breaker.state == "RATE_LIMITED"
    g1 = breaker.gate("u2")
    assert g1 is not None and g1["reason"] == "circuit_open"
    assert breaker.suppressed == 1
    clock.advance(10_000)
    assert breaker.gate("u3") is not None
    assert breaker.suppressed == 2


def test_half_open_single_probe_then_heal():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    breaker.observe_response(418, "1", "", "u")  # open, 1 s window
    clock.advance(2_000)  # window expired
    assert breaker.gate("probe") is None  # exactly one probe allowed
    breaker.observe_success()
    assert breaker.state == "HEALTHY"


def test_half_open_failure_doubles_window_capped():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    breaker.observe_response(418, "1", "", "u")  # open, RA-driven 1 s window
    assert breaker.window_ms == 1_000
    clock.advance(2_000)  # window expired
    assert breaker.gate("p1") is None  # single half-open probe
    breaker.observe_response(429, None, "", "p1")  # re-banned, no RA
    assert breaker.state == "RATE_LIMITED"
    assert breaker.window_ms == 2_000  # doubled from the RA-driven window
    # still suppressed right after reopening
    assert breaker.gate("x")["reason"] == "circuit_open"


def test_consecutive_5xx_degraded():
    breaker = CircuitBreaker("rest", now_ms=FakeClock())
    for status in (500, 502, 503):
        breaker.observe_response(status, None, "", "u")
    assert breaker.state == "DEGRADED"


def test_403_fail_fast_records_non_retryable_no_retry_consumption():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    before = len(breaker.history)
    v = breaker.observe_response(403, None, "forbidden", "u")
    assert v.non_retryable
    assert breaker.state == "DEGRADED"
    assert len(breaker.history) == before + 1
    # a success heals
    breaker.observe_success()
    assert breaker.state == "HEALTHY"


def test_error_history_never_truncated():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    for _ in range(20):
        for status in (500, 502, 503):  # 3 consecutive => DEGRADED record
            clock.advance(1)
            breaker.observe_response(status, None, "", "u")
        breaker.observe_success()  # => HEALTHY record
    assert len(breaker.history) == 40  # 2 records per cycle, none dropped


# ----------------------------------------------------------------------
# rate limiter
# ----------------------------------------------------------------------
def test_min_gap_enforced():
    clock = FakeClock()
    limiter = RateLimiter(now_ms=clock)
    limiter.note_issued()
    wait = limiter.gap_wait_ms()
    assert 0 < wait <= 250
    clock.advance(300)
    assert limiter.gap_wait_ms() == 0


def test_rpm_cap_blocks():
    clock = FakeClock()
    limiter = RateLimiter(now_ms=clock, max_rpm=3)
    for _ in range(3):
        assert limiter.budget_block("/fapi/v1/klines") is None
        limiter.note_issued()
    block = limiter.budget_block("/fapi/v1/klines")
    assert block and "rpm cap" in block
    clock.advance(61_000)
    assert limiter.budget_block("/fapi/v1/klines") is None


def test_weight_budgets_soft_hard():
    clock = FakeClock()
    limiter = RateLimiter(now_ms=clock)
    limiter.observe_weight_header("1250")
    # essential endpoint still allowed at soft
    assert limiter.budget_block("/fapi/v1/klines") is None
    # non-essential stopped at soft
    assert limiter.budget_block("/fapi/v1/time") is not None
    limiter.observe_weight_header("1801")
    assert limiter.budget_block("/fapi/v1/klines") is not None  # hard stop


def test_backoff_bounded_with_jitter():
    for attempt in range(6):
        for _ in range(50):
            d = backoff_delay_ms(attempt)
            base = min(2_000 * (2**attempt), 30_000)
            assert 0 <= d <= int(base * 1.25) + 1


# ----------------------------------------------------------------------
# coalescer
# ----------------------------------------------------------------------
def test_coalescing_suppresses_duplicate_calls():
    runs = []

    async def main():
        co = Coalescer()

        async def factory():
            runs.append(1)
            await asyncio.sleep(0.05)
            return "value"

        results = await asyncio.gather(
            *[co.run("key", factory) for _ in range(5)]
        )
        return co, results

    co, results = asyncio.run(main())
    assert results == ["value"] * 5
    assert runs == [1]
    assert co.suppressed_duplicates == 4
