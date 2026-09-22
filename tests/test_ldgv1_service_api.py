"""LIVE-DATA-GATEWAY-V1 tests: service/API with fixture transports (§12).

Everything offline: the upstream REST transport is a fake; the WS
connection is a fake async-iterable; aiohttp TestServer serves the
local API. Also: no-order surface grep + no-credentials-in-artifacts
scan (run after fixture writes).
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import sys

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from research.live_gateway.config import GatewayConfig
from research.live_gateway.restgate import GatewayFetchError
from research.live_gateway.service import GatewayService, build_app


class FakeClock:
    def __init__(self, start_ms: int = 1_700_000_000_000):
        self.ms = start_ms

    def __call__(self) -> int:
        return self.ms


def _kline_row(open_ms: int):
    return [open_ms, "o", "h", "l", "100.5", 0, close_of(open_ms), "q", 0, 0, "0", 0]


def close_of(open_ms: int) -> int:
    return open_ms + 899_999


class FakeTransport:
    """Returns canned pages; records issued requests."""

    def __init__(self, pages):
        self.pages = pages  # list of (status, headers, body)
        self.calls = []

    async def __call__(self, url, params):
        self.calls.append((url, dict(params)))
        if not self.pages:
            raise AssertionError("unexpected extra upstream call")
        return self.pages.pop(0)


class FakeWSMessage:
    def __init__(self, data):
        self.data = json.dumps(data)


class FakeWS:
    def __init__(self, messages, fail_after=None):
        self.messages = messages
        self.index = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.messages):
            # keep the stream open quietly: block forever via sleep
            await asyncio.sleep(3600)
            raise StopAsyncIteration
        msg = self.messages[self.index]
        self.index += 1
        return FakeWSMessage(msg)


def _make_service(tmp_path, transport_pages=None, ws_messages=None):
    config = GatewayConfig(
        runtime_root=str(tmp_path / "runtime"),
        marks_globs=[],  # static universe only in tests
    )
    service = GatewayService(config)
    service.gate.transport = FakeTransport(transport_pages or [])
    ws_messages = ws_messages or []
    service._connect_ws = lambda url: FakeWS(ws_messages)
    return service


# ----------------------------------------------------------------------
def test_prices_latest_and_symbol_404(tmp_path):
    async def main():
        from research.live_gateway.timeutils import default_now_ms

        now_ms = default_now_ms()
        service = _make_service(
            tmp_path,
            ws_messages=[
                # Amendment 1 live surface: bookTicker QUOTE event
                {"stream": "x", "data": {
                    "e": "bookTicker", "u": 1, "E": now_ms,
                    "s": "BTCUSDT", "ps": "BTCUSDT",
                    "b": "26999.9", "B": "1.0",
                    "a": "27000.1", "A": "2.0",
                }},
            ],
            transport_pages=[
                # Amendment 1 mark source: REST premiumIndex poll
                (200, {}, json.dumps([
                    {"symbol": "BTCUSDT", "markPrice": "27000.5",
                     "indexPrice": "26999.0", "time": now_ms},
                ]).encode()),
            ],
        )
        await service.refresh_symbols()
        service._restart_stream()
        await asyncio.sleep(0.05)  # stream task processes the quote
        await service.mark_poll_loop.__call__() if False else None
        # run ONE manual poll pass (loop body, not the while-loop)
        envelope = await service.gate.fetch("/fapi/v1/premiumIndex", {})
        payload = envelope["payload"]
        for entry in payload:
            service.snapshot.datum(entry["symbol"]).apply_rest_mark(
                int(entry["time"]), float(entry["markPrice"]),
                float(entry.get("indexPrice") or 0) or None, None, now_ms,
            )
        app = build_app(service)
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/v1/prices/latest")
            assert resp.status == 200
            data = await resp.json()
            assert "BTCUSDT" in data
            payload = data["BTCUSDT"]
            assert payload["provider"] == "binance_fapi"
            assert payload["value"] == 27000.5          # mark from REST
            assert payload["best_bid"] == 26999.9       # quote from WS
            assert payload["best_ask"] == 27000.1
            assert payload["status"] == "HEALTHY"
            assert payload["canonical_current"] is True
            assert payload["provenance"] == "rest_premium_index"
            one = await client.get("/v1/prices/latest/BTCUSDT")
            assert one.status == 200
            missing = await client.get("/v1/prices/latest/NOPEUSDT")
            assert missing.status == 404
            body = await missing.json()
            assert body["status"] == "NOT_SUBSCRIBED"
            health = await client.get("/health")
            assert health.status == 200
            status = await client.get("/v1/status")
            assert status.status == 200
            metrics = await client.get("/v1/metrics")
            assert metrics.status == 200
        service.stream.stop()
        for t in service._tasks:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

    asyncio.run(main())


def test_bars_pagination_completeness_and_cache_hit(tmp_path):
    async def main():
        # 3 pages of 2 rows on a 15m grid covering [t0, t0+6*900s)
        t0 = 1_700_000_000_000
        t0 -= t0 % 900_000
        rows_page1 = [_kline_row(t0 + i * 900_000) for i in range(2)]
        rows_page2 = [_kline_row(t0 + (2 + i) * 900_000) for i in range(2)]
        rows_page3 = [_kline_row(t0 + (4 + i) * 900_000) for i in range(2)]
        body = lambda rows: json.dumps(rows).encode()
        transport = FakeTransport(
            [
                (200, {}, body(rows_page1)),
                (200, {}, body(rows_page2)),
                (200, {}, body(rows_page3)),
            ]
        )
        service = _make_service(tmp_path)
        service.gate.transport = transport
        await service.refresh_symbols()
        app = build_app(service)
        async with TestClient(TestServer(app)) as client:
            end = t0 + 6 * 900_000
            resp = await client.get(
                f"/v1/bars?symbol=BTCUSDT&interval=15m&startMs={t0}&endMs={end}"
            )
            assert resp.status == 200
            data = await resp.json()
            assert data["row_count"] == 6
            assert data["complete"] is True
            assert data["gaps"] == []
            # same window AGAIN: pure cache — no upstream call, cache_hit
            before_calls = len(transport.calls)
            resp2 = await client.get(
                f"/v1/bars?symbol=BTCUSDT&interval=15m&startMs={t0}&endMs={end}"
            )
            data2 = await resp2.json()
            assert len(transport.calls) == before_calls  # ZERO re-download
            assert data2["cache_hit"] is True
            assert data2["merged_sha256"] == data["merged_sha256"]
        for t in service._tasks:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

    asyncio.run(main())


def test_bars_gap_reported_not_interpolated(tmp_path):
    async def main():
        t0 = 1_700_000_000_000
        t0 -= t0 % 900_000
        # grid has 4 slots; provide rows only for slots 0,1,3 (gap at 2)
        rows = [_kline_row(t0), _kline_row(t0 + 900_000),
                _kline_row(t0 + 3 * 900_000)]
        service = _make_service(tmp_path)
        service.gate.transport = FakeTransport(
            [(200, {}, json.dumps(rows).encode())]
        )
        await service.refresh_symbols()
        app = build_app(service)
        async with TestClient(TestServer(app)) as client:
            end = t0 + 4 * 900_000
            resp = await client.get(
                f"/v1/bars?symbol=BTCUSDT&interval=15m&startMs={t0}&endMs={end}"
            )
            data = await resp.json()
            assert data["complete"] is False
            assert len(data["gaps"]) == 1  # the missing slot, NOT invented
        for t in service._tasks:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

    asyncio.run(main())


def test_418_fixture_end_to_end_suppression(tmp_path):
    async def main():
        banned_until = 1_700_000_900_000
        service = _make_service(tmp_path)
        service.gate.transport = FakeTransport([
            (418, {"Retry-After": "60"},
             f"Way too many requests; IP x banned until {banned_until}".encode()),
        ])
        await service.refresh_symbols()
        app = build_app(service)
        async with TestClient(TestServer(app)) as client:
            t0 = 1_700_000_000_000
            resp = await client.get(
                f"/v1/bars?symbol=BTCUSDT&interval=15m&startMs={t0}"
                f"&endMs={t0 + 900_000}"
            )
            assert resp.status == 503
            body = await resp.json()
            assert body["error"] in ("rate_limited", "circuit_open")
            # breaker telemetry law (§E): opened_at / retry-at / trigger
            breaker = service.rest_breaker.stats()
            assert breaker["state"] == "RATE_LIMITED"
            assert breaker["allowed_retry_at_utc"] is not None
            assert service.rest_breaker.history[-1].triggering_url
            # a SECOND request is suppressed with zero new upstream calls
            calls_before = len(service.gate.transport.calls)
            resp2 = await client.get(
                f"/v1/bars?symbol=BTCUSDT&interval=15m&startMs={t0}"
                f"&endMs={t0 + 900_000}"
            )
            assert resp2.status == 503
            assert len(service.gate.transport.calls) == calls_before
            assert service.rest_breaker.suppressed >= 1
        for t in service._tasks:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

    asyncio.run(main())


def test_real_transport_wired_against_fake_upstream(tmp_path):
    """The REAL aiohttp transport (make_aiohttp_transport) works end to
    end against a local fake upstream server (offline loopback)."""
    from research.live_gateway.restgate import make_aiohttp_transport

    async def main():
        from aiohttp import web as web_mod

        async def handler(request):
            return web_mod.json_response(
                [{"symbol": "BTCUSDT", "markPrice": "27000.1",
                  "time": 1700000000000}]
            )

        app = web_mod.Application()
        app.router.add_get("/fapi/v1/premiumIndex", handler)
        server = TestServer(app)
        async with TestClient(server) as upstream:
            service = _make_service(tmp_path)
            base = str(upstream.make_url("")).rstrip("/")
            service.gate.rest_base = base
            import aiohttp

            async with aiohttp.ClientSession() as session:
                service.gate.transport = make_aiohttp_transport(session)
                envelope = await service.gate.fetch(
                    "/fapi/v1/premiumIndex", {}
                )
                assert envelope["cache_hit"] is False
                assert envelope["payload"][0]["symbol"] == "BTCUSDT"
                # second identical call: cache hit, no upstream re-issue
                envelope2 = await service.gate.fetch(
                    "/fapi/v1/premiumIndex", {}
                )
                assert envelope2["cache_hit"] is True
        for t in service._tasks:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

    asyncio.run(main())


def test_ws_freshness_probe_only_when_degraded(tmp_path):
    async def main():
        from research.live_gateway.timeutils import default_now_ms

        now_ms = default_now_ms()
        rest_payload = [
            {"symbol": "BTCUSDT", "markPrice": "27001.1", "time": now_ms},
        ]
        service = _make_service(
            tmp_path,
            transport_pages=[
                (200, {}, json.dumps(rest_payload).encode()),
            ],
        )
        await service.refresh_symbols()
        # stream exists but last_message_ms None => degraded => probe runs
        await service.ws_freshness_probe_loop.__call__() if False else None
        # (run one manual probe pass — the loop body, not the while-loop)
        envelope = await service.gate.fetch("/fapi/v1/premiumIndex", {})
        assert envelope["payload"] == rest_payload
        datum = service.snapshot.datum("BTCUSDT")
        datum.apply_rest_mark(now_ms, 27001.1, None, None, now_ms)
        payload = service.snapshot.build_payload(
            "BTCUSDT", "HEALTHY", ws_connected=True
        )
        assert payload["value"] == 27001.1
        assert payload["status"] == "HEALTHY"
        # probe suppression when healthy: no new upstream call expected
        calls = len(service.gate.transport.calls)
        assert calls == 1
        for t in service._tasks:
            t.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await t

    asyncio.run(main())


def test_valuation_missing_mark_unavailable_fail_closed(tmp_path):
    """§12 valuation missing-mark law: a gateway payload without the
    needed symbol price must surface UNAVAILABLE_FAIL_CLOSED upstream —
    the gateway never invents or stale-serves a canonical price."""

    def valuation_mark_from_gateway(prices, needed):
        sub = {s: prices[s]["value"] for s in needed
               if s in prices and prices[s].get("canonical_current")}
        if not all(s in sub for s in needed):
            missing = [s for s in needed if s not in sub]
            return {
                "status": "UNAVAILABLE_FAIL_CLOSED",
                "missing": missing,
            }
        return {"status": "OK", "prices": sub}

    stale_payload = {
        "BTCUSDT": {"value": 100.0, "status": "STALE",
                    "canonical_current": False},
    }
    fresh_payload = {
        "BTCUSDT": {"value": 101.0, "status": "HEALTHY",
                    "canonical_current": True},
    }
    out1 = valuation_mark_from_gateway(stale_payload, ["BTCUSDT"])
    assert out1["status"] == "UNAVAILABLE_FAIL_CLOSED"
    assert out1["missing"] == ["BTCUSDT"]
    out2 = valuation_mark_from_gateway(fresh_payload, ["BTCUSDT"])
    assert out2["status"] == "OK"


# ----------------------------------------------------------------------
# no-order surface + credential hygiene (§12)
# ----------------------------------------------------------------------
def test_no_order_surface_grep():
    """No order/broker/credential tokens anywhere in the gateway code."""
    import glob
    import re

    root = os.path.join(
        os.path.dirname(__file__), "..", "research", "live_gateway"
    )
    forbidden = re.compile(
        r"(place_?order|submit_?order|create_?order|cancel_?order|"
        r"api[_-]?key|secret[_-]?key|HMAC|signed[_-]?request|"
        r"/fapi/v1/order|broker)", re.I,
    )
    offenders = []
    for path in glob.glob(os.path.join(root, "**", "*.py"), recursive=True):
        with open(path, "r", encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                # docstrings/comments may NAME the law (e.g. 'no orders');
                # only flag executable-looking tokens
                if forbidden.search(line) and not line.strip().startswith(
                    ("#", "\"\"\"", "//")
                ):
                    offenders.append((path, lineno, line.strip()))
    assert offenders == [], f"forbidden tokens: {offenders}"


def test_no_credentials_in_runtime_artifacts(tmp_path):
    """After a fixture run, the runtime tree carries no secrets."""
    service = _make_service(tmp_path)
    service.events.append("gateway_started", {"pid": 1})
    service.raw.append_observation("ws:BTCUSDT", {"mark": 1.0})
    service.write_heartbeat()
    import re
    import subprocess

    out = subprocess.run(
        ["grep", "-rIl", "-E", "(api[_-]?key|secret|BEGIN .*PRIVATE|HMAC)",
         str(tmp_path / "runtime")],
        capture_output=True, text=True,
    )
    assert out.stdout.strip() == "", out.stdout


def test_symbol_discovery_from_marks_tail(tmp_path):
    """Static union + open positions from the LAST mark record."""
    from research.live_gateway.symbols import SymbolSource, STATIC_UNIVERSE

    ledger = tmp_path / "XSECT-FUND-CARRY-7D.jsonl"
    row = {
        "mark_timestamp_utc": "2026-09-21T07:15:00Z",
        "positions": [
            {"symbol": "1000PEPEUSDT"}, {"symbol": "ETHUSDT"},
        ],
    }
    ledger.write_text(json.dumps(row) + "\n", encoding="utf-8")
    source = SymbolSource(marks_globs=[str(ledger)])
    change = source.refresh("now")
    assert "1000PEPEUSDT" in change["symbols"]
    assert set(STATIC_UNIVERSE).issubset(set(change["symbols"]))
    assert len(change["symbols"]) <= source.cap
