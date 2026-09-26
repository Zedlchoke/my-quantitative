"""Dukascopy datafeed bi5 transport + decoders — ERP1-TRACKA-COHORT-1.

PORT LINEAGE: ported from EURUSD-RANGEEXP-SCORED-V1/scripts/duka_lib.py
(checked out at .worktrees/fx-rangefade-2m-shadow-v1; sha of the ancestor
file recorded in DATAGATE_REPORT.md). The ancestor hard-codes symbol
EURUSD and PRICE_SCALE=1e5 — the plan §5.2 BLOCKING PORT DEFECT. Every
per-pair constant (symbol, pip, price_scale, tradability band) lives in
PairConfig (pair_config.py), whose values are DERIVED FROM PROBE TICKS by
probe_pair.py — never assumed (USDJPY 1e-3-scale precedent, plan §5.1).

Transport (unchanged from ancestor): polite GET, one persistent HTTPS
connection (keep-alive dropped per-file latency from ~6 s to <1 s),
0.15–0.35 s pacing between requests, exponential backoff + connection
rebuild on 429/5xx/network errors. No account, no login, no cookies:
public datafeed endpoints only. Bytes on disk are exactly the response
body (raw SHA-256 recorded by callers).

Formats (verified empirically on EURUSD 2026-09-23 by the ancestor probe;
RE-PROVEN PER PAIR by probe_pair.py against tick ground truth — the probe
must pass before any PairConfig is marked proven):
  tick bi5   (hour files)   records of 20 bytes, big-endian >5i:
                             (ms_offset_in_hour, ask, bid, ask_vol, bid_vol)
  candle bi5 (day files)    records of 24 bytes, big-endian >5if:
                             (sec_offset_in_day, open, close, low, high,
                              volume_float32)  -> up to 1440 M1 bars/day
  prices are integer POINTS; the points divisor is PairConfig.price_scale.
  NOTE the ancestor build_bars.py docstring order (open, close, low, high)
  was verified by its probe; the ancestor's 15m aggregation then read the
  CLOSE column for high/low (lineage quirk, recorded in DATAGATE_REPORT.md
  as LINEAGE-NOTE-1; this port reads the true low/high columns).

LAYOUT TRAP (documented in the ancestor, asserted here): the 20-byte tick
layout and the 24-byte candle layout share the LZMA container, so a candle
payload can pass len%20 while len%24 is the real candle invariant —
decoders assert their own record size, and probe_pair.py additionally
cross-checks CONTENT (tick-aggregated OHLC vs candle OHLC), because layout
asserts alone cannot always catch a cross-decode.
"""
from __future__ import annotations

import http.client
import lzma
import random
import struct
import threading
import time
import urllib.error
import urllib.request

USER_AGENT = "my-quantitative-research/1.0 (internal research; owner-authorized 2026-09-23)"
HOST = "datafeed.dukascopy.com"

TICK_RECORD = 20   # bytes per tick record (>5i)
CANDLE_RECORD = 24  # bytes per M1 candle record (>5if)


def month0(m: int) -> int:  # calendar month (1..12) -> path month index (0..11)
    return m - 1


def candle_path(symbol: str, year: int, month: int, day: int, side: str) -> str:
    """M1 day-candle path; month is CALENDAR month 1..12; side BID|ASK."""
    return f"/datafeed/{symbol}/{year}/{month0(month):02d}/{day:02d}/{side}_candles_min_1.bi5"


def tick_path(symbol: str, year: int, month: int, day: int, hour: int) -> str:
    """Tick hour-file path; calendar month 1..12."""
    return f"/datafeed/{symbol}/{year}/{month0(month):02d}/{day:02d}/{hour:02d}h_ticks.bi5"


class KeepAliveFetcher:
    """Persistent-connection polite fetcher (one HTTPS connection per instance).

    Unchanged semantics from the ancestor: pacing sleep after every 200,
    exponential backoff with connection rebuild on 429/500/502/503 and on
    network errors, stable 404 -> None.
    """

    def __init__(self, pacing=(0.15, 0.35), timeout=45):
        self.host = HOST
        self.pacing = pacing
        self.timeout = timeout
        self.conn = None
        self.lock = threading.Lock()

    def _connect(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
        self.conn = http.client.HTTPSConnection(self.host, timeout=self.timeout)

    def fetch(self, path, max_retries=8):
        """GET path -> bytes or None on stable 404. Raises after retries."""
        attempt = 0
        while True:
            attempt += 1
            try:
                if self.conn is None:
                    self._connect()
                self.conn.request(
                    "GET", path, headers={"User-Agent": USER_AGENT, "Accept": "*/*"}
                )
                resp = self.conn.getresponse()
                body = resp.read()
                if resp.status == 200:
                    time.sleep(random.uniform(*self.pacing))
                    return body
                if resp.status == 404:
                    time.sleep(0.05)
                    return None
                if resp.status in (429, 500, 502, 503) and attempt <= max_retries:
                    time.sleep(1.5 * (2 ** (attempt - 1)) + random.random())
                    self._connect()
                    continue
                raise RuntimeError(f"HTTP {resp.status} for {path}")
            except (OSError, http.client.HTTPException):
                if attempt > max_retries:
                    raise
                time.sleep(1.0 * attempt + random.random())
                self._connect()

    def close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None


def fetch_bytes(url, max_retries=6, base_sleep=1.0, timeout=60):
    """One-shot urllib fetch (kept for ad-hoc probes)."""
    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                time.sleep(0.35 + random.random() * 0.3)  # polite pacing
                return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                time.sleep(0.3)
                return None
            if e.code in (429, 500, 502, 503) and attempt <= max_retries:
                sleep = base_sleep * (2 ** (attempt - 1)) + random.random()
                time.sleep(sleep)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt <= max_retries:
                time.sleep(base_sleep * attempt + random.random())
                continue
            raise


# ---------------- raw (unscaled) decoders — scale applied by callers --------


def decompress(raw: bytes) -> bytes:
    """bi5 (LZMA) -> plain bytes; empty input -> b''."""
    if not raw:
        return b""
    return lzma.decompress(raw)


def decode_tick_records(raw: bytes):
    """Tick hour file -> list of raw 5-int tuples (unscaled points).

    Asserts the 20-byte tick layout invariant (see module docstring trap).
    """
    plain = decompress(raw)
    if len(plain) % TICK_RECORD:
        raise AssertionError(
            f"bi5 tick payload not multiple of {TICK_RECORD}: {len(plain)}"
        )
    return [
        struct.unpack_from(">5i", plain, TICK_RECORD * i)
        for i in range(len(plain) // TICK_RECORD)
    ]


def decode_candle_records(raw: bytes):
    """Day M1 candle file -> list of raw 6-field tuples (unscaled points).

    Layout (empirically verified by the ancestor probe + re-proven per
    pair): 24-byte records, big-endian >5if:
        (sec_offset_in_day, open, close, low, high, volume_f32)
    Asserts the 24-byte candle layout invariant.
    """
    plain = decompress(raw)
    if len(plain) % CANDLE_RECORD:
        raise AssertionError(
            f"bi5 candle payload not multiple of {CANDLE_RECORD}: {len(plain)}"
        )
    return [
        struct.unpack_from(">5if", plain, CANDLE_RECORD * i)
        for i in range(len(plain) // CANDLE_RECORD)
    ]


def decode_ticks(raw: bytes, price_scale: float):
    """Hour tick file -> list of (ms_offset, ask, bid, ask_vol, bid_vol)."""
    return [
        (ms, a / price_scale, b / price_scale, av, bv)
        for ms, a, b, av, bv in decode_tick_records(raw)
    ]


def decode_min_candles(raw: bytes, price_scale: float):
    """Day M1 candle file -> list of dicts (UTC sec-of-day + OHLC scaled)."""
    out = []
    for sec, o, c, l, h, vol in decode_candle_records(raw):
        out.append(
            {
                "sec": sec,
                "open": o / price_scale,
                "close": c / price_scale,
                "low": l / price_scale,
                "high": h / price_scale,
                "vol": vol,
            }
        )
    return out
