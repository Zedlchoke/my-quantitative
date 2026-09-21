"""A7 impl-r1 remediation regression tests + §12 gaps closed.

Covers: FND-1 raw append persistence (3 rows survive), FND-2 half-open
single-flight latch, FND-3 fresh banned-until honored on re-open,
FND-4 rest-sourced datum labels, FND-6 separate 5xx budget (<=2),
plus previously-missing §12 tests: WS reconnect, one-upstream-
connection, bounded network timeout, 5xx bounded retry.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os

from research.live_gateway.circuit import CircuitBreaker
from research.live_gateway.persistence import RawStore
from research.live_gateway.restgate import (
    GatewayFetchError,
    RestGate,
    TransportExhaustedError,
)
from research.live_gateway.reststore import RestCache
from research.live_gateway.ratelimit import RateLimiter
from research.live_gateway.snapshot import SnapshotStore
from research.live_gateway.wsadapter import BinanceStream


class FakeClock:
    def __init__(self, start_ms: int = 1_700_000_000_000):
        self.ms = start_ms

    def __call__(self) -> int:
        return self.ms

    def advance(self, delta_ms: int) -> None:
        self.ms += delta_ms


# ----------------------------------------------------------------------
# FND-1: raw rows must PERSIST across appends (the old tmp+rename wiped)
# ----------------------------------------------------------------------
def test_raw_append_keeps_all_rows(tmp_path):
    import gzip

    clock = FakeClock()
    raw = RawStore(str(tmp_path), now_ms_=clock)
    wrote = [
        raw.append_observation("ws:BTCUSDT", {"mark": float(i)})
        for i in range(5)
    ]
    assert all(wrote)
    day = None
    for f in os.listdir(str(tmp_path)):
        if f.endswith(".jsonl.gz"):
            day = f
    with gzip.open(os.path.join(str(tmp_path), day), "rt", encoding="utf-8") as h:
        rows = [json.loads(line) for line in h]
    assert len(rows) == 5
    assert [r["mark"] for r in rows] == [0.0, 1.0, 2.0, 3.0, 4.0]


# ----------------------------------------------------------------------
# FND-2: half-open single-flight — exactly ONE probe at window expiry
# ----------------------------------------------------------------------
def test_half_open_single_flight_under_concurrency():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    breaker.observe_response(418, "1", "", "u")  # 1 s window
    clock.advance(2_000)  # expired
    first = breaker.gate("p1")
    assert first is None  # THE probe
    for i in range(10):
        blocked = breaker.gate(f"other-{i}")
        assert blocked is not None
        assert blocked["reason"] == "half_open_probe_inflight"
    breaker.observe_success()  # probe concludes -> latch cleared
    assert breaker.state == "HEALTHY"


def test_dead_probe_unstuck_after_grace():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    breaker.observe_response(418, "1", "", "u")
    clock.advance(2_000)
    assert breaker.gate("probe") is None
    # probe dies without conclusion (timeout path): grace unsticks it
    clock.advance(31_000)
    assert breaker.gate("probe2") is None  # re-probe allowed


# ----------------------------------------------------------------------
# FND-3: fresh LONGER banned-until wins over doubling on re-open
# ----------------------------------------------------------------------
def test_reopen_honors_fresh_banned_until():
    clock = FakeClock()
    breaker = CircuitBreaker("rest", now_ms=clock)
    breaker.observe_response(418, "1", "", "u")  # open, 1 s window
    clock.advance(2_000)
    assert breaker.gate("p") is None
    # probe re-banned with banned-until +114 min
    banned_until_ms = clock() + 114 * 60 * 1000
    breaker.observe_response(
        418, None, f"banned until {banned_until_ms}", "p"
    )
    allowed = breaker.allowed_retry_at_ms()
    assert allowed is not None
    assert allowed >= banned_until_ms - 1_000  # venue window honored
    # and a probe attempt inside the venue window is suppressed
    clock.advance(60_000)
    assert breaker.gate("x")["reason"] == "circuit_open"


# ----------------------------------------------------------------------
# FND-4: REST-sourced datum labeled rest in source/provenance
# ----------------------------------------------------------------------
def test_rest_sourced_datum_labels():
    store = SnapshotStore(now_ms=FakeClock())
    d = store.datum("BTCUSDT")
    d.apply_ws_event(1_000, 100.0, None, None, None, 1_500)
    ws_payload = store.build_payload("BTCUSDT", "HEALTHY", True)
    assert ws_payload["source"].endswith("@markPrice@1s")
    assert ws_payload["provenance"] == "ws_event"
    d.apply_rest_mark(2_000, 100.5, None, None, 2_500)
    rest_payload = store.build_payload("BTCUSDT", "HEALTHY", True)
    assert rest_payload["source"] == "GET /fapi/v1/premiumIndex"
    assert rest_payload["provenance"] == "rest_premium_index"
    assert rest_payload["value"] == 100.5


# ----------------------------------------------------------------------
# FND-6 + §12: bounded 5xx retry (<=2) separate from transport budget
# ----------------------------------------------------------------------
def _gate_with(pages, tmp_path):
    async def transport(url, params):
        page = pages.pop(0)
        return page

    cache = RestCache(str(tmp_path))
    gate = RestGate(
        rest_base="https://example.invalid",
        cache=cache,
        breaker=CircuitBreaker("rest", now_ms=FakeClock()),
        limiter=RateLimiter(now_ms=FakeClock()),
        transport=transport,
    )
    gate.sleeper = _no_sleep
    return gate


async def _no_sleep(ms):
    return None


def test_5xx_budget_exhausted_after_two_retries(tmp_path):
    gate = _gate_with(
        [(503, {}, b"")] * 5, tmp_path
    )

    async def main():
        try:
            await gate.fetch("/fapi/v1/premiumIndex", {})
            raised = None
        except GatewayFetchError as exc:
            raised = exc
        return raised

    raised = asyncio.run(main())
    assert isinstance(raised, TransportExhaustedError)
    assert raised.kind == "server_error_budget_exhausted"
    # exactly 3 upstream attempts: 1 original + 2 bounded 5xx retries
    assert gate.counts["upstream_calls"] == 3


def test_network_timeout_bounded(tmp_path):
    async def timing_out(url, params):
        raise asyncio.TimeoutError()

    cache = RestCache(str(tmp_path))
    gate = RestGate(
        rest_base="https://example.invalid",
        cache=cache,
        breaker=CircuitBreaker("rest", now_ms=FakeClock()),
        limiter=RateLimiter(now_ms=FakeClock()),
        transport=timing_out,
    )
    gate.sleeper = _no_sleep

    async def main():
        try:
            await gate.fetch("/fapi/v1/premiumIndex", {})
            raised = None
        except GatewayFetchError as exc:
            raised = exc
        return raised

    raised = asyncio.run(main())
    assert isinstance(raised, TransportExhaustedError)
    assert gate.counts["upstream_calls"] == 5  # 1 + 4 transport retries


# ----------------------------------------------------------------------
# §12: WS reconnect + one-upstream-connection
# ----------------------------------------------------------------------
class FlakyConnect:
    """Fails the first N connection attempts, then yields FakeWS."""

    def __init__(self, messages, fail_first=1):
        self.messages = messages
        self.fail_first = fail_first
        self.attempts = 0

    def __call__(self, url):
        self.attempts += 1
        if self.attempts <= self.fail_first:
            return _FailingWS()
        return _OkWS(self.messages)


class _FailingWS:
    async def __aenter__(self):
        raise ConnectionError("boom")

    async def __aexit__(self, *exc):
        return False


class _OkWS:
    def __init__(self, messages):
        self.messages = messages

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.messages:
            class M:
                def __init__(self, data):
                    self.data = data

            return M(json.dumps(self.messages.pop(0)))
        await asyncio.sleep(3600)


def test_ws_reconnect_after_failure():
    async def main():
        flaky = FlakyConnect(
            [{"stream": "x", "data": {
                "s": "BTCUSDT", "E": 1_700_000_000_000,
                "p": "27000.1", "i": "1", "r": "0", "T": 0,
            }}],
            fail_first=2,
        )
        seen = []

        async def on_event(data, received):
            seen.append(data)

        stream = BinanceStream(
            symbols=["BTCUSDT"], on_event=on_event, connect_fn=flaky,
        )
        stream.sleeper = _no_sleep
        task = asyncio.get_event_loop().create_task(stream.run())
        for _ in range(200):
            if seen:
                break
            await asyncio.sleep(0.01)
        stream.stop()
        with contextlib.suppress(asyncio.TimeoutError, asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)
        return stream, seen

    stream, seen = asyncio.run(main())
    assert stream.reconnect_count == 2  # two failures -> two reconnects
    assert seen and seen[0]["s"] == "BTCUSDT"


# ----------------------------------------------------------------------
# A7 impl-r2 R2-FND-1: truncated gzip member must not crash startup
# ----------------------------------------------------------------------
def test_truncated_gzip_tail_does_not_crash_restart(tmp_path):
    clock = FakeClock()
    raw = RawStore(str(tmp_path), now_ms_=clock)
    raw.append_observation("ws:BTCUSDT", {"mark": 1.0})
    day_file = [
        os.path.join(str(tmp_path), f)
        for f in os.listdir(str(tmp_path))
        if f.endswith(".jsonl.gz")
    ][0]
    # simulate a crash mid-append: chop the file's last 20 bytes
    size = os.path.getsize(day_file)
    with open(day_file, "r+b") as handle:
        handle.truncate(size - 20)
    raw2 = RawStore(str(tmp_path), now_ms_=clock)  # must NOT raise
    assert raw2._tail_degraded is True
    # and the store keeps working (new appends continue)
    assert raw2.append_observation("ws:ETHUSDT", {"mark": 2.0}) is True


def test_one_upstream_connection_under_190_symbols():
    calls = []
    flaky = _OkWS([])
    tracker = lambda url: (calls.append(url), flaky)[1]

    async def main():
        async def on_event(data, received):
            return None

        stream = BinanceStream(
            symbols=[f"S{i}USDT" for i in range(190)],
            on_event=on_event,
            connect_fn=tracker,
        )
        task = asyncio.get_event_loop().create_task(stream.run())
        await asyncio.sleep(0.05)
        stream.stop()
        with contextlib.suppress(asyncio.TimeoutError, asyncio.CancelledError):
            await asyncio.wait_for(task, timeout=2)

    asyncio.run(main())
    assert len(calls) == 1  # ONE combined-stream connection
    assert calls[0].count("@markPrice@1s") == 190
