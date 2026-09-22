"""GatewayService: wires every component into one asyncio process.

Sidecar law (plan §9.1): until the owner GO, NO existing worker,
dashboard or ledger is modified — this service only reads mark-ledger
tails read-only, opens its own keyless upstream connections and
serves 127.0.0.1.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import random
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import web

from . import GATEWAY_SCHEMA, __version__
from .circuit import CircuitBreaker, SURFACE_REST, SURFACE_WS
from .config import GatewayConfig
from .fanout import Fanout
from .persistence import (
    EventLog,
    PersistedCounters,
    RawStore,
    atomic_write_json,
    read_json,
)
from .ratelimit import RateLimiter
from .restgate import RestGate
from .reststore import RestCache
from .snapshot import SnapshotStore
from .symbols import SymbolSource
from .timeutils import default_now_ms, ms_to_iso_z
from .wsadapter import BinanceStream, parse_mark_event

log = logging.getLogger("live_gateway")

HEARTBEAT_INTERVAL_S = 15.0
SYMBOL_REFRESH_S = 3600.0
GAP_SCAN_S = 5.0
RETENTION_SCAN_S = 3600.0
#: Amendment 1 (2026-09-22): the venue suppresses the futures markPrice
#: stream on every machine egress — marks come from REST premiumIndex
#: through the full §5 law at a 5 s cadence (cache TTL 5 s); the WS
#: surface is bookTicker on the 3 majors, QUOTE-ONLY (liveness +
#: display; never a mark source).
MARK_POLL_S = 5.0
QUOTE_SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
QUOTE_PUBLISH_MIN_INTERVAL_MS = 1_000  # sample hot quotes to 1/s/symbol


class GatewayService:
    def __init__(
        self,
        config: GatewayConfig,
        session: Optional[aiohttp.ClientSession] = None,
        rng: Optional[random.Random] = None,
    ):
        self.config = config
        self.started_ms = default_now_ms()
        self.rng = rng or random.Random()
        self.session = session

        root = config.runtime_root
        os.makedirs(root, exist_ok=True)
        self.events = EventLog(os.path.join(root, "events", "events.jsonl"))
        self.raw = RawStore(
            os.path.join(root, "raw"), now_ms_=default_now_ms
        )
        self.counters = PersistedCounters(
            os.path.join(root, "snapshot", "metrics.json")
        )
        self.counters.load()

        self.rest_breaker = CircuitBreaker(SURFACE_REST)
        self.ws_breaker = CircuitBreaker(SURFACE_WS)
        self.limiter = RateLimiter()
        self.cache = RestCache(root)
        self.gate = RestGate(
            rest_base=config.rest_base,
            cache=self.cache,
            breaker=self.rest_breaker,
            limiter=self.limiter,
            rng=self.rng,
        )
        # durable §5/§7 events straight into the append-only log
        self.gate.event_sink = lambda kind, detail: self.events.append(
            kind, detail
        )
        self.snapshot = SnapshotStore()
        self.fanout = Fanout(os.path.join(root, "snapshot", "seq.json"))
        self.fanout.load_seq()
        self.symbol_source = SymbolSource(
            marks_globs=list(config.marks_globs),
            extra_symbols=list(config.extra_symbols),
            cap=config.symbol_cap,
        )
        self.stream: Optional[BinanceStream] = None
        self._tasks: List[asyncio.Task] = []
        self._stopping = asyncio.Event()
        self.shutdown_clean = False
        self.symbols: List[str] = []
        self._latency_acc: List[int] = []
        self._quote_last_publish: Dict[str, int] = {}

    # ------------------------------------------------------------------
    def surface_state(self) -> str:
        """Aggregate surface state for price payloads."""
        ws_state = self.ws_breaker.state
        if self.stream is not None and self.stream.state != "CONNECTED":
            if ws_state != "RATE_LIMITED":
                ws_state = "DISCONNECTED"
        rest_state = self.rest_breaker.state
        # datum statuses derive from the WS surface; REST state is
        # reported separately in /v1/status. For prices, WS wins.
        return ws_state

    async def on_ws_event(self, data: dict, received_ms: int) -> None:
        """Amendment 1: the WS surface is bookTicker (QUOTE-ONLY).
        Quotes update the quote clock + (sampled 1/s/symbol) fanout and
        raw store; they NEVER touch mark fields."""
        from .wsadapter import parse_book_ticker_event

        parsed = parse_book_ticker_event(data)
        if parsed is None:
            # tolerate a future venue policy change back to markPrice
            mark_parsed = parse_mark_event(data)
            if mark_parsed is None or mark_parsed["event_e_ms"] is None:
                return
            await self._apply_ws_mark(mark_parsed, received_ms)
            return
        symbol = parsed["symbol"]
        if symbol not in QUOTE_SYMBOLS:
            return
        if self.ws_breaker.state == "GAP_DETECTED":
            self.ws_breaker.observe_success()  # fresh quote heals
        datum = self.snapshot.datum(symbol)
        datum.apply_quote(
            parsed["event_e_ms"], parsed["best_bid"], parsed["best_ask"],
            received_ms,
        )
        latency_ms = received_ms - (parsed["event_e_ms"] or received_ms)
        self._latency_acc.append(max(0, latency_ms))
        last_pub = self._quote_last_publish.get(symbol, 0)
        if received_ms - last_pub >= QUOTE_PUBLISH_MIN_INTERVAL_MS:
            self._quote_last_publish[symbol] = received_ms
            mid = None
            if parsed["best_bid"] and parsed["best_ask"]:
                mid = (parsed["best_bid"] + parsed["best_ask"]) / 2.0
            event = {
                "type": "quote",
                "symbol": symbol,
                "best_bid": parsed["best_bid"],
                "best_ask": parsed["best_ask"],
                "mid": mid,
                "received_at_utc": ms_to_iso_z(received_ms),
            }
            self.fanout.publish(event)
            self.raw.append_observation(
                f"quote:{symbol}",
                {
                    "ts_utc": ms_to_iso_z(received_ms),
                    "bid": parsed["best_bid"],
                    "ask": parsed["best_ask"],
                },
            )

    async def _apply_ws_mark(self, parsed: dict, received_ms: int) -> None:
        """Legacy markPrice-stream path (unused under Amendment 1 until
        the venue unsuppresses the stream)."""
        symbol = parsed["symbol"]
        if symbol not in self.symbol_source.last_discovered:
            return
        datum = self.snapshot.datum(symbol)
        outcome = datum.apply_ws_event(
            parsed["event_e_ms"],
            parsed["mark_price"],
            parsed["index_price"],
            parsed["funding_rate"],
            parsed["next_funding_time_ms"],
            received_ms,
        )
        self.counters.bump(f"ws_{outcome}")
        if outcome != "applied":
            return
        self.fanout.publish({
            "type": "mark",
            **{k: v for k, v in parsed.items()},
            "received_at_utc": ms_to_iso_z(received_ms),
        })
        self.raw.append_observation(
            f"ws:{symbol}",
            {
                "provider_ts_utc": ms_to_iso_z(parsed["event_e_ms"]),
                "mark": parsed["mark_price"],
                "index": parsed["index_price"],
                "funding": parsed["funding_rate"],
            },
        )

    def latency_stats(self) -> dict:
        acc = self._latency_acc[-3000:]
        if not acc:
            return {"p50_ms": None, "p95_ms": None, "p99_ms": None, "n": 0}
        def pct(p: float) -> int:
            idx = min(len(acc) - 1, int(len(acc) * p))
            return sorted(acc)[idx]
        return {
            "p50_ms": pct(0.50),
            "p95_ms": pct(0.95),
            "p99_ms": pct(0.99),
            "n": len(acc),
        }

    # ------------------------------------------------------------------
    async def refresh_symbols(self) -> None:
        change = self.symbol_source.refresh(ms_to_iso_z(default_now_ms()))
        self.symbols = change["symbols"]
        if change["added"] or change["removed"]:
            self.events.append(
                "symbols_changed",
                {
                    "added": change["added"],
                    "removed": change["removed"],
                    "count": len(self.symbols),
                },
            )
            self._restart_stream()
        else:
            self.symbols = change["symbols"]

    def _restart_stream(self) -> None:
        if self.stream is not None:
            self.stream.stop()
        # Amendment 1: quote-only bookTicker surface on the 3 majors
        self.stream = BinanceStream(
            symbols=list(QUOTE_SYMBOLS),
            on_event=self.on_ws_event,
            connect_fn=self._connect_ws,
            rng=self.rng,
            ws_base=self.config.ws_base,
        )
        task = asyncio.get_event_loop().create_task(self._run_stream())

        async def _log_finish(t: asyncio.Task) -> None:
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await t

        self._tasks.append(asyncio.get_event_loop().create_task(_log_finish(task)))

    async def _run_stream(self) -> None:
        stream = self.stream
        if stream is None:
            return
        try:
            await stream.run()
        except asyncio.CancelledError:
            raise

    def _connect_ws(self, url: str):
        assert self.session is not None, "session required for live ws"
        # NO client-side heartbeat (Amendment 1 ops fix 2026-09-22):
        # measured — connections WITH aiohttp heartbeat=20 get killed by
        # the venue/path (0 msgs + instant reconnect loops) while the
        # same streams without it flow thousands of frames/8s. Server
        # pings are still answered automatically (autoping).
        return self.session.ws_connect(url)

    # ------------------------------------------------------------------
    async def heartbeat_loop(self) -> None:
        while not self._stopping.is_set():
            self.write_heartbeat()
            try:
                await asyncio.wait_for(
                    self._stopping.wait(), timeout=HEARTBEAT_INTERVAL_S
                )
            except asyncio.TimeoutError:
                continue

    def write_heartbeat(self, extra: Optional[dict] = None) -> None:
        payload = self.status_payload()
        if extra:
            payload.update(extra)
        atomic_write_json(
            self.config.runtime_dir("snapshot", "heartbeat.json"), payload
        )
        self.counters.save()

    def status_payload(self) -> dict:
        ws_stats = self.stream.stats() if self.stream else {
            "state": "DISCONNECTED", "reconnect_count": 0,
            "last_message_utc": None, "messages_received": 0,
            "parse_errors": 0, "subscribed_symbols": 0, "stream_url": None,
        }
        from .timeutils import default_now_ms as _now

        now_ms = _now()
        return {
            "schema": GATEWAY_SCHEMA,
            "version": __version__,
            "pid": os.getpid(),
            "started_utc": ms_to_iso_z(self.started_ms),
            "uptime_s": round((now_ms - self.started_ms) / 1000.0, 1),
            "now_utc": ms_to_iso_z(now_ms),
            "bind": self.config.bind,
            "port": self.config.port,
            "ws": ws_stats,
            "ws_breaker": self.ws_breaker.stats(),
            "rest_breaker": self.rest_breaker.stats(),
            "rest": self.gate.stats(),
            "source_latency": self.latency_stats(),
            "stale_symbols": self.snapshot.stale_symbols(self.symbols),
            "symbols": self.symbols,
            "symbol_refresh_utc": self.symbol_source.last_refresh_utc,
            "fanout": self.fanout.stats(),
            "snapshot": self.snapshot.ws_stats(),
            "disk": {
                "raw_bytes": self.raw.disk_bytes(),
                "cache_bytes": self.cache.disk_bytes(),
                "raw_rows_written": self.raw.rows_written,
                "raw_duplicates_suppressed": self.raw.duplicates_suppressed,
            },
            "counters": dict(self.counters.counters),
            "breaker_history_tail": [
                r.as_dict() for r in (self.rest_breaker.history[-10:])
            ],
            "events_tail": self.events.tail(10),
            "shutdown_clean": self.shutdown_clean,
        }

    # ------------------------------------------------------------------
    async def gap_scan_loop(self) -> None:
        while not self._stopping.is_set():
            flagged = self.snapshot.mark_gaps(self.symbols)
            for sym in flagged:
                self.events.append(
                    "mark_gap_detected",
                    {"symbol": sym, "threshold_ms": 10000},
                )
                self.counters.bump("mark_gap_detected")
            # quote-surface gap (Amendment 1): quote clock silent >10s
            from .timeutils import default_now_ms as _now
            _now_ms = _now()
            quote_silent = [
                sym for sym in QUOTE_SYMBOLS
                if (d := self.snapshot.data.get(sym)) is None
                or d.quote_ts_ms is None
                or _now_ms - d.quote_ts_ms > 10_000
            ]
            if quote_silent and self.ws_breaker.state not in (
                "RATE_LIMITED", "DISCONNECTED",
            ):
                self.ws_breaker.state = "GAP_DETECTED"
                self.events.append(
                    "quote_gap_detected", {"symbols": quote_silent}
                )
            try:
                await asyncio.wait_for(
                    self._stopping.wait(), timeout=GAP_SCAN_S
                )
            except asyncio.TimeoutError:
                continue

    async def symbol_refresh_loop(self) -> None:
        while not self._stopping.is_set():
            try:
                await self.refresh_symbols()
            except Exception as exc:  # noqa: BLE001
                self.events.append(
                    "symbol_refresh_error", {"error": repr(exc)}
                )
            try:
                await asyncio.wait_for(
                    self._stopping.wait(), timeout=SYMBOL_REFRESH_S
                )
            except asyncio.TimeoutError:
                continue

    async def retention_loop(self) -> None:
        while not self._stopping.is_set():
            try:
                removed = self.raw.enforce_retention()
                evicted = self.cache.enforce_budget()
                if removed:
                    self.events.append(
                        "raw_retention_removed", {"days": removed}
                    )
                if evicted:
                    self.events.append(
                        "cache_evicted_bytes", {"bytes": evicted}
                    )
            except Exception as exc:  # noqa: BLE001
                self.events.append("retention_error", {"error": repr(exc)})
            try:
                await asyncio.wait_for(
                    self._stopping.wait(), timeout=RETENTION_SCAN_S
                )
            except asyncio.TimeoutError:
                continue

    # ------------------------------------------------------------------
    async def mark_poll_loop(self) -> None:
        """Amendment 1 mark source: REST premiumIndex through the FULL
        §5 law every MARK_POLL_S (5 s; cache TTL 5 s -> each poll is a
        bounded fresh fetch). The §5 budgets cap this at 12 calls/min,
        weight ~120/min against the soft 1200 — and any 418/429 opens
        the breaker exactly as frozen."""
        from .timeutils import default_now_ms as _now

        while not self._stopping.is_set():
            try:
                if self.symbols:
                    envelope = await self.gate.fetch(
                        "/fapi/v1/premiumIndex", {}
                    )
                    payload = envelope["payload"]
                    received = _now()
                    if isinstance(payload, list):
                        wanted = set(self.symbols)
                        applied = 0
                        for entry in payload:
                            if not isinstance(entry, dict):
                                continue
                            sym = entry.get("symbol")
                            if sym not in wanted:
                                continue
                            try:
                                ts_ms = int(entry.get("time"))
                                mark = (
                                    float(entry["markPrice"])
                                    if entry.get("markPrice") is not None
                                    else None
                                )
                                idx = (
                                    float(entry["indexPrice"])
                                    if entry.get("indexPrice") is not None
                                    else None
                                )
                            except (TypeError, ValueError, KeyError):
                                continue
                            datum = self.snapshot.datum(sym)
                            datum.apply_rest_mark(
                                ts_ms, mark, idx, None, received,
                            )
                            applied += 1
                        self.counters.bump("mark_polls_ok")
                        self.counters.bump("marks_applied", applied)
                        if applied:
                            self.raw.append_observation(
                                "rest:premiumIndex_bulk",
                                {
                                    "ts_utc": ms_to_iso_z(received),
                                    "applied": applied,
                                    "digest": envelope["pages"][0][
                                        "response_sha256"
                                    ][:16],
                                },
                            )
            except Exception as exc:  # noqa: BLE001 - poll failure is data
                self.counters.bump("mark_polls_failed")
                self.events.append(
                    "mark_poll_error", {"error": repr(exc)[:300]}
                )
            try:
                await asyncio.wait_for(
                    self._stopping.wait(), timeout=MARK_POLL_S
                )
            except asyncio.TimeoutError:
                continue

    async def start_background(self) -> None:
        await self.refresh_symbols()
        if self.session is None:
            self.session = aiohttp.ClientSession()
        if self.gate.transport is None:
            from .restgate import make_aiohttp_transport

            self.gate.transport = make_aiohttp_transport(self.session)
        self._restart_stream()
        self._tasks = [
            asyncio.get_event_loop().create_task(coro())
            for coro in (
                self.heartbeat_loop,
                self.symbol_refresh_loop,
                self.gap_scan_loop,
                self.retention_loop,
                self.mark_poll_loop,
            )
        ]
        self.events.append(
            "gateway_started",
            {"pid": os.getpid(), "symbols": len(self.symbols)},
        )

    async def shutdown(self) -> None:
        self._stopping.set()
        if self.stream is not None:
            self.stream.stop()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self.fanout.shutdown_flush()
        self.shutdown_clean = True
        self.write_heartbeat()
        self.events.append(
            "gateway_stopped", {"clean": True, "pid": os.getpid()}
        )
        if self.session is not None:
            with contextlib.suppress(Exception):
                await self.session.close()


def build_app(service: GatewayService) -> web.Application:
    """The §6 REST/WS API over one GatewayService."""
    routes = web.RouteTableDef()

    @routes.get("/health")
    async def health(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "ok": True,
                "pid": os.getpid(),
                "uptime_s": round(
                    (default_now_ms() - service.started_ms) / 1000.0, 1
                ),
                "ws_state": (
                    service.stream.state if service.stream else "DISCONNECTED"
                ),
            }
        )

    @routes.get("/v1/status")
    async def status(request: web.Request) -> web.Response:
        return web.json_response(service.status_payload())

    def _price_payload(symbol: str) -> dict:
        return service.snapshot.build_payload(
            symbol,
            surface_state=service.surface_state(),
            ws_connected=(
                service.stream is not None
                and service.stream.state == "CONNECTED"
            ),
            subscribed=symbol in service.symbols,
        )

    @routes.get("/v1/prices/latest")
    async def prices_latest(request: web.Request) -> web.Response:
        return web.json_response(
            {sym: _price_payload(sym) for sym in service.symbols}
        )

    @routes.get("/v1/prices/latest/{symbol}")
    async def price_one(request: web.Request) -> web.Response:
        symbol = request.match_info["symbol"].upper()
        payload = _price_payload(symbol)
        if payload["status"] == "NOT_SUBSCRIBED":
            return web.json_response(payload, status=404)
        return web.json_response(payload)

    @routes.get("/v1/bars")
    async def bars(request: web.Request) -> web.Response:
        return await _historical(request, "/fapi/v1/klines")

    @routes.get("/v1/basis")
    async def basis(request: web.Request) -> web.Response:
        return await _historical(request, "/futures/data/basis")

    @routes.get("/v1/funding")
    async def funding(request: web.Request) -> web.Response:
        return await _historical(request, "/fapi/v1/fundingRate")

    INTERVAL_MS = {
        "1m": 60_000, "5m": 300_000, "15m": 900_000, "30m": 1_800_000,
        "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000,
    }

    async def _historical(request: web.Request, path: str) -> web.Response:
        from .restgate import GatewayFetchError

        q = request.query
        try:
            start_ms = int(q.get("startMs", "0"))
            end_ms = int(q.get("endMs", "0"))
        except ValueError:
            return web.json_response(
                {"error": "startMs/endMs must be integer ms"}, status=400
            )
        if not start_ms or not end_ms or start_ms > end_ms:
            return web.json_response(
                {"error": "startMs and endMs required (ms, start<=end)"},
                status=400,
            )
        params: Dict[str, Any] = {}
        grid_ms: Optional[int] = None
        key_field = "0"
        if path == "/fapi/v1/klines":
            symbol = q.get("symbol", "").upper()
            interval = q.get("interval", "15m")
            if not symbol:
                return web.json_response({"error": "symbol required"}, status=400)
            grid_ms = INTERVAL_MS.get(interval)
            if grid_ms is None:
                return web.json_response(
                    {"error": f"unsupported interval {interval}"}, status=400
                )
            params = {"symbol": symbol, "interval": interval}
            key_field = "0"
        elif path == "/futures/data/basis":
            pair = q.get("pair", q.get("symbol", "")).upper()
            period = q.get("period", q.get("interval", "15m"))
            if not pair:
                return web.json_response({"error": "pair required"}, status=400)
            grid_ms = INTERVAL_MS.get(period)
            params = {
                "pair": pair, "contractType": "PERPETUAL", "period": period,
            }
            key_field = "timestamp"
        else:
            symbol = q.get("symbol", "").upper()
            if not symbol:
                return web.json_response({"error": "symbol required"}, status=400)
            params = {"symbol": symbol}
            key_field = "fundingTime"
        refresh = q.get("refresh") == "1"
        try:
            result = await service.gate.fetch_window(
                path, grid_ms, key_field, params, start_ms, end_ms
            )
            return web.json_response(result)
        except GatewayFetchError as exc:
            status = 503 if exc.kind in (
                "circuit_open", "rate_limited", "budget_blocked",
                "transport_exhausted",
            ) else 502
            return web.json_response(
                {"error": exc.kind, "detail": exc.detail}, status=status
            )

    @routes.get("/v1/metrics")
    async def metrics(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "counters": dict(service.counters.counters),
                "rest": service.gate.stats(),
                "fanout": service.fanout.stats(),
                "snapshot": service.snapshot.ws_stats(),
                "source_latency": service.latency_stats(),
                "disk": {
                    "raw_bytes": service.raw.disk_bytes(),
                    "cache_bytes": service.cache.disk_bytes(),
                },
            }
        )

    @routes.get("/ws/market")
    async def ws_market(request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)
        name = request.query.get("name") or f"consumer-{id(ws):x}"
        replay_n = int(request.query.get("replay", "0") or 0)
        consumer = service.fanout.attach(name, ms_to_iso_z(default_now_ms()))
        service.events.append("consumer_connected", {"name": name})
        if replay_n > 0:
            replay = service.fanout.replay(replay_n)
            await ws.send_json(
                {"type": "replay_banner", **{k: replay[k] for k in (
                    "replay_served", "replay_requested", "replay_truncated",
                    "last_seq")}}
            )
            for envelope in replay["replay"]:
                await ws.send_json(envelope)
        sender_task = asyncio.get_event_loop().create_task(
            _pump(ws, consumer.queue)
        )
        try:
            async for _msg in ws:
                pass  # client->server traffic unused; keepalive only
        finally:
            sender_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await sender_task
            service.fanout.detach(name, "ws closed")
            service.events.append(
                "consumer_disconnected",
                {"name": name, "last_seq": consumer.last_delivered_seq},
            )
        return ws

    async def _pump(ws: web.WebSocketResponse, queue: asyncio.Queue) -> None:
        while True:
            envelope = await queue.get()
            await ws.send_json(envelope)

    app = web.Application()
    app.add_routes(routes)
    app["service"] = service
    return app


async def run_service(config: GatewayConfig) -> None:
    """Entry: build service, start background, serve until SIGTERM."""
    service = GatewayService(config)
    app = build_app(service)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, config.bind, config.port)
    await site.start()
    await service.start_background()

    stop = asyncio.Event()
    loop = asyncio.get_event_loop()
    import signal

    for sig in (signal.SIGTERM, signal.SIGINT):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)
    service.events.append(
        "gateway_listening",
        {"bind": config.bind, "port": config.port},
    )
    await stop.wait()
    await service.shutdown()
    await runner.cleanup()
