"""Dukascopy datafeed bi5 transport + decoders for EURUSD-OPEN-SEARCH-V1.

Transport: polite GET with 429/5xx backoff. Bytes on disk are exactly the
response body (raw SHA-256 recorded by callers). No account, no login, no
cookies: public datafeed endpoints only.

Formats (verified empirically 2026-09-23 by probe_decode_20240304.py;
UTC conventions inherited from EURUSD-DATA-QUALIFICATION-V1):
  tick bi5   (hour files)   records of 20 bytes, big-endian >5i:
                             (ms_offset_in_hour, ask, bid, ask_vol, bid_vol)
  candle bi5 (day files)    records of 24 bytes, big-endian >5if:
                             (sec_offset_in_day, open, close, low, high,
                              volume_float32)  -> 1440 M1 bars/day
  prices are integer points; EURUSD scale = 1e5.
Layouts are VALIDATED by the probe against tick ground truth, not assumed:
OHLC invariants and tick-vs-candle cross-check must pass or callers fail
closed.
"""
import http.client
import lzma
import struct
import threading
import time
import urllib.request
import urllib.error
import random

BASE = "https://datafeed.dukascopy.com/datafeed/EURUSD"
PRICE_SCALE = 1e5
USER_AGENT = "my-quantitative-research/1.0 (internal research; owner-authorized 2026-09-23)"


class KeepAliveFetcher:
    """Persistent-connection polite fetcher (one HTTPS connection per instance).

    Keep-alive matters here: a fresh TLS handshake per ~11KB file dominated
    latency in the first download attempt (~6s/file). Reused connections
    drop it to well under 1s. Still rate-polite: sleep between requests,
    exponential backoff + connection rebuild on 429/5xx/network errors.
    """

    def __init__(self, pacing=(0.15, 0.35), timeout=45):
        self.host = "datafeed.dukascopy.com"
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
            except (OSError, http.client.HTTPException) as e:
                if attempt > max_retries:
                    raise
                time.sleep(1.0 * attempt + random.random())
                self._connect()


def month0(m):  # calendar month (1..12) -> path month index (0..11)
    return m - 1


def candle_path(year, month, day, side):  # month is CALENDAR month 1..12
    return f"/datafeed/EURUSD/{year}/{month0(month):02d}/{day:02d}/{side}_candles_min_1.bi5"


def tick_path(year, month, day, hour):  # calendar month 1..12
    return f"/datafeed/EURUSD/{year}/{month0(month):02d}/{day:02d}/{hour:02d}h_ticks.bi5"


def candle_url(year, month, day, side):
    return f"{BASE}/{year}/{month0(month):02d}/{day:02d}/{side}_candles_min_1.bi5"


def tick_url(year, month, day, hour):
    return f"{BASE}/{year}/{month0(month):02d}/{day:02d}/{hour:02d}h_ticks.bi5"


def fetch_bytes(url, max_retries=6, base_sleep=1.0, timeout=60):
    """One-shot urllib fetch (kept for probes)."""
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
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt <= max_retries:
                time.sleep(base_sleep * attempt + random.random())
                continue
            raise


def decode_records(raw):
    """bi5 -> list of 5-int tuples (raw, unscaled)."""
    if not raw:
        return []
    plain = lzma.decompress(raw)
    assert len(plain) % 20 == 0, f"bi5 payload not multiple of 20: {len(plain)}"
    return [struct.unpack_from(">5i", plain, 20 * i) for i in range(len(plain) // 20)]


def decode_ticks(raw):
    """Hour tick file -> list of (ms_offset, ask, bid, ask_vol, bid_vol) floats scaled."""
    out = []
    for ms, a, b, av, bv in decode_records(raw):
        out.append((ms, a / PRICE_SCALE, b / PRICE_SCALE, av, bv))
    return out


def decode_min_candles(raw):
    """Day M1 candle file -> list of dicts, UTC minute-of-day + OHLC scaled.

    EMPIRICALLY VERIFIED layout (2026-09-23, vs tick ground truth):
    24-byte records, big-endian `>5if`:
        (sec_offset_in_day, open, close, low, high, volume_f32)
    The 20-byte tick layout and the 24-byte candle layout share the LZMA
    container, so len%20 can pass while len%24 is the real invariant.
    """
    if not raw:
        return []
    plain = lzma.decompress(raw)
    assert len(plain) % 24 == 0, f"bi5 candle payload not multiple of 24: {len(plain)}"
    out = []
    for i in range(len(plain) // 24):
        sec, o, c, l, h, vol = struct.unpack_from(">5if", plain, 24 * i)
        out.append(
            {
                "sec": sec,
                "open": o / PRICE_SCALE,
                "close": c / PRICE_SCALE,
                "low": l / PRICE_SCALE,
                "high": h / PRICE_SCALE,
                "vol": vol,
            }
        )
    return out
