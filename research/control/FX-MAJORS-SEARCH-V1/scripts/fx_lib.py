"""Pair-aware Dukascopy bi5 transport + decoders for FX-MAJORS-SEARCH-V1.

Layout laws inherited from the EURUSD probes (24-byte candle `>5if`,
20-byte tick `>5i`), but the PRICE SCALE is per-pair and is VERIFIED by
fx_probe.py against tick ground truth before any corpus is trusted:
  GBPUSD: points = price*1e5 (pip 1e-4)   [same as EURUSD]
  USDJPY: points = price*1e3 (pip 1e-2)   [hypothesis verified, not assumed]
"""
import http.client
import lzma
import struct
import threading
import time
import random

HOST = "datafeed.dukascopy.com"
PAIRS = {
    "GBPUSD": {"scale": 1e5, "pip": 1e-4, "range": (0.95, 1.45)},
    "USDJPY": {"scale": 1e3, "pip": 1e-2, "range": (95.0, 165.0)},
}
USER_AGENT = "my-quantitative-research/1.0 (internal research; owner-authorized 2026-09-23)"


class KeepAliveFetcher:
    def __init__(self, pacing=(0.15, 0.35), timeout=45):
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
        self.conn = http.client.HTTPSConnection(HOST, timeout=self.timeout)

    def fetch(self, path, max_retries=8):
        attempt = 0
        while True:
            attempt += 1
            try:
                if self.conn is None:
                    self._connect()
                self.conn.request("GET", path, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
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


def candle_path(pair, year, month, day, side):
    return f"/datafeed/{pair}/{year}/{month - 1:02d}/{day:02d}/{side}_candles_min_1.bi5"


def tick_path(pair, year, month, day, hour):
    return f"/datafeed/{pair}/{year}/{month - 1:02d}/{day:02d}/{hour:02d}h_ticks.bi5"


def decode_ticks(raw, scale):
    if not raw:
        return []
    plain = lzma.decompress(raw)
    assert len(plain) % 20 == 0
    out = []
    for i in range(len(plain) // 20):
        ms, a, b, av, bv = struct.unpack_from(">5i", plain, 20 * i)
        out.append((ms, a / scale, b / scale))
    return out


def decode_min_candles(raw, scale):
    if not raw:
        return []
    plain = lzma.decompress(raw)
    assert len(plain) % 24 == 0, f"candle payload not multiple of 24: {len(plain)}"
    out = []
    for i in range(len(plain) // 24):
        sec, o, c, l, h, vol = struct.unpack_from(">5if", plain, 24 * i)
        out.append({"sec": sec, "open": o / scale, "close": c / scale,
                    "low": l / scale, "high": h / scale, "vol": vol})
    return out
