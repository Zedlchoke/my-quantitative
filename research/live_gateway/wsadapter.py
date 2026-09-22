"""Binance fapi combined mark-price WebSocket adapter (plan §4).

One connection, combined streams ``<sym>@markPrice@1s`` (payload:
markPrice, indexPrice, fundingRate, nextFundingTime, event time E).
Reconnect with bounded jittered exponential backoff (base 2 s, cap
60 s); reconnect_count tracked; per-symbol duplicates and out-of-order
events counted; wall-clock gap diagnostic (no venue sequence on this
stream — honest labeling per plan §4(7)).
"""

from __future__ import annotations

import asyncio
import json
import random
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, Optional

from .timeutils import NowMs, default_now_ms, ms_to_iso_z

WS_BASE = "wss://fstream.binance.com/stream"
RECONNECT_BASE_MS = 2_000
RECONNECT_CAP_MS = 60_000
JITTER = 0.20


def reconnect_delay_ms(attempt: int, rng: Optional[random.Random] = None) -> int:
    rng = rng or random
    base = min(RECONNECT_BASE_MS * (2 ** attempt), RECONNECT_CAP_MS)
    return int(base * (1.0 + rng.uniform(-JITTER, JITTER)))


@dataclass
class BinanceStream:
    """Combined-stream client. ``connect_fn(url)`` must yield an async
    context manager whose object is async-iterable over messages with a
    ``.data`` (str/bytes) attribute — aiohttp ClientWebSocketResponse
    shape; tests inject a fake."""

    symbols: List[str]
    on_event: Callable[[dict, int], Awaitable[None]]  # (parsed, received_ms)
    connect_fn: Callable[[str], Any]
    now_ms: NowMs = field(default=default_now_ms)
    sleeper: Callable[[float], Awaitable[None]] = field(
        default=lambda s: asyncio.sleep(s / 1000.0)
    )
    rng: Optional[random.Random] = None
    ws_base: str = WS_BASE
    stream_name: str = "bookTicker"  # Amendment 1: quote-only surface

    state: str = "DISCONNECTED"  # DISCONNECTED|CONNECTING|CONNECTED
    reconnect_count: int = 0
    last_message_utc: Optional[str] = None
    last_message_ms: Optional[int] = None
    messages_received: int = 0
    parse_errors: int = 0
    _stop: bool = False

    def url(self) -> str:
        streams = "/".join(
            f"{sym.lower()}@{self.stream_name}" for sym in self.symbols
        )
        return f"{self.ws_base}/stream?streams={streams}"

    def stop(self) -> None:
        self._stop = True

    async def run(self) -> None:
        """Reconnect loop; never raises (operator reads state/telemetry)."""
        attempt = 0
        while not self._stop:
            self.state = "CONNECTING"
            try:
                async with self.connect_fn(self.url()) as ws:
                    self.state = "CONNECTED"
                    attempt = 0
                    async for msg in ws:
                        if self._stop:
                            break
                        await self._handle(msg)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001 - reconnect on any failure
                pass
            if self._stop:
                break
            self.state = "DISCONNECTED"
            self.reconnect_count += 1
            await self.sleeper(reconnect_delay_ms(attempt, self.rng))
            attempt += 1
        self.state = "DISCONNECTED"

    async def _handle(self, msg: Any) -> None:
        raw = getattr(msg, "data", None)
        if raw is None:
            return
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            envelope = json.loads(raw)
            data = envelope.get("data", envelope)
        except (ValueError, UnicodeDecodeError, AttributeError):
            self.parse_errors += 1
            return
        if not isinstance(data, dict):
            return
        received = self.now_ms()
        self.messages_received += 1
        self.last_message_ms = received
        self.last_message_utc = ms_to_iso_z(received)
        await self.on_event(data, received)

    def stats(self) -> dict:
        return {
            "state": self.state,
            "reconnect_count": self.reconnect_count,
            "last_message_utc": self.last_message_utc,
            "messages_received": self.messages_received,
            "parse_errors": self.parse_errors,
            "subscribed_symbols": len(self.symbols),
            "stream_url": self.url(),
        }


def parse_mark_event(data: dict) -> Optional[dict]:
    """Normalize one markPrice stream event to gateway fields.

    Amendment 1 (2026-09-22): this stream is venue-unavailable on this
    machine (0 payload across every egress); retained for a future
    venue policy change but NOT subscribed by default."""
    symbol = data.get("s")
    if not isinstance(symbol, str):
        return None
    e_ms = data.get("E")

    def _f(name: str) -> Optional[float]:
        raw = data.get(name)
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    return {
        "symbol": symbol,
        "event_e_ms": int(e_ms) if isinstance(e_ms, (int, float)) else None,
        "mark_price": _f("p"),
        "index_price": _f("i"),
        "funding_rate": _f("r"),
        "next_funding_time_ms": (
            int(data["T"]) if data.get("T") is not None else None
        ),
    }


def parse_book_ticker_event(data: dict) -> Optional[dict]:
    """Normalize one futures bookTicker event (Amendment 1 live
    surface): best bid/ask + last-quantities, event fields e/s/u/b/a.
    QUOTE-ONLY: never a mark source (plan §4 amended law)."""
    symbol = data.get("s")
    if not isinstance(symbol, str):
        return None

    def _f(name: str) -> Optional[float]:
        raw = data.get(name)
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    ts_ms = data.get("E") or data.get("T")
    return {
        "symbol": symbol,
        "event_e_ms": int(ts_ms) if isinstance(ts_ms, (int, float)) else None,
        "best_bid": _f("b"),
        "best_ask": _f("a"),
        "bid_qty": _f("B"),
        "ask_qty": _f("A"),
    }
