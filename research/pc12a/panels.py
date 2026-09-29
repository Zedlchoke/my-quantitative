"""M1 .bi5 panel loader — PC12A implementation lane.

Panel format (empirically pinned by the Lane D physical audit,
``poolB/data_audit/DATA_AUDIT_REPORT.md`` §B; 12,552 files, 0 anomalies):

- LZMA (alone-format) compressed; payload always 1440 x 24 bytes.
- Record = 24 bytes big-endian ``>u4 x5 + >f4``:
  (sec_offset, open, close, low, high, volume_f32).
- ``sec_offset`` = seconds from 00:00 UTC, step 60 (0..86340).
- Prices are raw integers: divide by 1e5 (EURUSD, GBPUSD) / 1e3 (USDJPY).
- ``volume_f32`` is a SIZE-WEIGHTED per-tick volume sum in Dukascopy units
  (NOT a tick count; absolute unit NOT_RUN per the audit §C). Only
  within-pair relative / ordinal constructions are lawful consumers.

Panels live OUTSIDE this worktree (read-only absolute paths recorded by the
audit); nothing here ever writes to them.

Coverage assertions are enforced on every decoded day: 1440 records, 60s
grid, ask >= bid, low <= min(o,c) <= max(o,c) <= high on both sides.
"""

from __future__ import annotations

import datetime as dt
import lzma
import os
import struct
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np

RECORD_STRUCT = struct.Struct(">5I f")  # >u4 x5 + >f4 -- 24 bytes
RECORDS_PER_DAY = 1440
RECORD_SIZE = RECORD_STRUCT.size
assert RECORD_SIZE == 24
_DAY_SECONDS = 60 * RECORDS_PER_DAY

# Default read-only panel roots as recorded by the Lane D audit
# (DATA_AUDIT_REPORT.md "Panels audited" table). Override with the
# PC12A_PANEL_ROOTS env var (JSON dict pair -> root) for relocation.
_DEFAULT_PANEL_ROOTS = {
    "EURUSD": (
        "/Users/hoangminhlong/my-quantitative/.worktrees/"
        "fx-rangefade-2m-shadow-v1/research/control/"
        "FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/M1"
    ),
    "GBPUSD": (
        "/Users/hoangminhlong/my-quantitative/.worktrees/"
        "fx-majors-search-v1/integration/research/control/"
        "FX-MAJORS-SEARCH-V1/data_local/GBPUSD/M1"
    ),
    "USDJPY": (
        "/Users/hoangminhlong/my-quantitative/.worktrees/"
        "fx-majors-search-v1/integration/research/control/"
        "FX-MAJORS-SEARCH-V1/data_local/USDJPY/M1"
    ),
}


@dataclass(frozen=True)
class PairSpec:
    """Frozen per-pair panel facts (audit §B)."""

    symbol: str
    pip_size: float
    price_divisor: float  # 1e5 for EURUSD/GBPUSD, 1e3 for USDJPY
    quote_is_usd: bool  # True for EURUSD/GBPUSD; USDJPY is quoted in JPY


PAIR_SPECS: Dict[str, PairSpec] = {
    "EURUSD": PairSpec("EURUSD", 0.0001, 1e5, True),
    "GBPUSD": PairSpec("GBPUSD", 0.0001, 1e5, True),
    "USDJPY": PairSpec("USDJPY", 0.01, 1e3, False),
}


class PanelError(RuntimeError):
    """Coverage/format assertion failure (fail-closed, never a silent skip)."""


# ---------------------------------------------------------------------------
# Low-level codec (pure, unit-tested with synthetic bytes)
# ---------------------------------------------------------------------------


def encode_bi5(
    sec: np.ndarray,
    open_raw: np.ndarray,
    close_raw: np.ndarray,
    low_raw: np.ndarray,
    high_raw: np.ndarray,
    volume: np.ndarray,
) -> bytes:
    """Serialize one day of records to .bi5 payload bytes (uncompressed).

    Used by tests to mint synthetic panels; the loader is then round-tripped
    against these arrays. Inputs are per-record values (1440 of each).
    """
    n = len(sec)
    if not (len(open_raw) == len(close_raw) == len(low_raw)
            == len(high_raw) == len(volume) == n):
        raise ValueError("column length mismatch")
    buf = bytearray()
    for i in range(n):
        buf += RECORD_STRUCT.pack(
            int(sec[i]), int(open_raw[i]), int(close_raw[i]),
            int(low_raw[i]), int(high_raw[i]), float(volume[i]),
        )
    return bytes(buf)


def compress_bi5(payload: bytes) -> bytes:
    """LZMA alone-format container exactly like the staged files."""
    return lzma.compress(payload, format=lzma.FORMAT_ALONE)


def decode_bi5(data: bytes) -> np.ndarray:
    """Decode raw .bi5 file bytes -> structured array (raw integer prices)."""
    try:
        payload = lzma.decompress(data)
    except lzma.LZMAError as exc:  # pragma: no cover - defensive
        raise PanelError(f"undecodable .bi5 (lzma): {exc}") from exc
    if len(payload) % RECORD_SIZE != 0:
        raise PanelError(f"payload {len(payload)} not a multiple of {RECORD_SIZE}")
    n = len(payload) // RECORD_SIZE
    rec = np.frombuffer(payload, dtype=np.dtype(
        [("t", ">u4"), ("o", ">u4"), ("c", ">u4"), ("l", ">u4"),
         ("h", ">u4"), ("v", ">f4")]), count=n)
    return rec


@dataclass
class SideBar:
    """One side (BID or ASK) of one decoded day, prices already divided."""

    sec: np.ndarray        # int64 seconds offset, 60-step grid
    open: np.ndarray       # float64 price
    close: np.ndarray
    low: np.ndarray
    high: np.ndarray
    volume: np.ndarray     # float64 size-weighted volume (opaque unit)


@dataclass
class DayPanel:
    """BID+ASK pairing for one pair-day with the audit's coverage gates."""

    symbol: str
    date: dt.date
    bid: SideBar
    ask: SideBar

    @property
    def mid_open(self) -> np.ndarray:
        return (self.bid.open + self.ask.open) / 2.0

    @property
    def mid_close(self) -> np.ndarray:
        return (self.bid.close + self.ask.close) / 2.0

    def tradable_mask(self) -> np.ndarray:
        """Per PIT_COST_FREEZE App. B: bid AND ask present with volume > 0
        both sides. Carry-forward minutes (weekends/holidays) are excluded."""
        return (self.bid.volume > 0) & (self.ask.volume > 0)


def _assert_side(rec: np.ndarray, symbol: str, side: str) -> SideBar:
    n = len(rec)
    if n == 0:
        raise PanelError(f"{symbol} {side}: empty day")
    sec = rec["t"].astype(np.int64)
    grid = np.arange(0, _DAY_SECONDS, 60, dtype=np.int64)
    if n != RECORDS_PER_DAY or not np.array_equal(sec, grid):
        raise PanelError(
            f"{symbol} {side}: expected 1440 records on the 60s grid, got n={n}")
    div = PAIR_SPECS[symbol].price_divisor
    o = rec["o"].astype(np.float64) / div
    c = rec["c"].astype(np.float64) / div
    lo = rec["l"].astype(np.float64) / div
    hi = rec["h"].astype(np.float64) / div
    bad = (lo > np.minimum(o, c)) | (hi < np.maximum(o, c))
    if bad.any():
        raise PanelError(
            f"{symbol} {side}: OHLC invariant violated on {int(bad.sum())} records")
    return SideBar(sec, o, c, lo, hi, rec["v"].astype(np.float64))


def load_day_from_bytes(symbol: str, date: dt.date, bid_bytes: bytes,
                        ask_bytes: bytes, enforce_spread: bool = True) -> DayPanel:
    """Decode + validate one pair-day from raw file bytes (both sides)."""
    if symbol not in PAIR_SPECS:
        raise PanelError(f"unknown pair {symbol}")
    bid = _assert_side(decode_bi5(bid_bytes), symbol, "BID")
    ask = _assert_side(decode_bi5(ask_bytes), symbol, "ASK")
    if enforce_spread:
        neg = (ask.open < bid.open) | (ask.close < bid.close)
        if neg.any():
            raise PanelError(
                f"{symbol} {date}: negative spread on {int(neg.sum())} minutes")
    return DayPanel(symbol, date, bid, ask)


# ---------------------------------------------------------------------------
# Loader with per-day cache
# ---------------------------------------------------------------------------


class PanelStore:
    """Read-only .bi5 access with an in-memory per-day cache.

    Paths default to the Lane-D-audited absolute roots; the loader never
    writes to them. Coverage assertions run on every (first) decode.
    """

    def __init__(self, roots: Optional[Dict[str, str]] = None):
        if roots is None:
            env = os.environ.get("PC12A_PANEL_ROOTS")
            if env:
                import json

                roots = json.loads(env)
        self.roots = dict(roots or _DEFAULT_PANEL_ROOTS)
        missing = {p: r for p, r in self.roots.items() if not os.path.isdir(r)}
        if missing:
            raise PanelError(f"panel root(s) missing: {missing}")
        self._cache: Dict[tuple, DayPanel] = {}

    def _path(self, symbol: str, side: str, date: dt.date) -> str:
        return os.path.join(self.roots[symbol], side, f"{date.isoformat()}.bi5")

    def load_day(self, symbol: str, date: dt.date) -> DayPanel:
        key = (symbol, date)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        with open(self._path(symbol, "BID", date), "rb") as fh:
            bid_bytes = fh.read()
        with open(self._path(symbol, "ASK", date), "rb") as fh:
            ask_bytes = fh.read()
        if not bid_bytes or not ask_bytes:
            raise PanelError(f"{symbol} {date}: zero-byte panel file")
        day = load_day_from_bytes(symbol, date, bid_bytes, ask_bytes)
        self._cache[key] = day
        return day

    def load_range(self, symbol: str, start: dt.date,
                   end: dt.date) -> Dict[dt.date, DayPanel]:
        """Load consecutive calendar days [start, end] inclusive."""
        out: Dict[dt.date, DayPanel] = {}
        d = start
        while d <= end:
            out[d] = self.load_day(symbol, d)
            d += dt.timedelta(days=1)
        return out

    def panel_digest(self, symbol: str, days) -> str:
        """Deterministic sha256 over (date, bytes, sha256) of the loaded days.

        Mirrors the audit §E method so the dry-run report can pin the exact
        data snapshot it consumed.
        """
        import hashlib

        lines = []
        for d in sorted(days):
            for side in ("BID", "ASK"):
                raw = open(self._path(symbol, side, d), "rb").read()
                lines.append(f"{d.isoformat()}|{side}|{len(raw)}|"
                             f"{hashlib.sha256(raw).hexdigest()}")
        return hashlib.sha256("\n".join(lines).encode()).hexdigest()


def synthetic_day_bytes(
    symbol: str,
    date: dt.date,
    mid_level: float,
    spread_pips: float = 0.4,
    vol_pattern: Optional[np.ndarray] = None,
    minute_range_pips: float = 0.2,
    seed: int = 0,
) -> tuple:
    """Mint a plausible synthetic pair-day of raw BID/ASK .bi5 bytes.

    Deterministic (own LCG, no global RNG state). Prices walk around
    ``mid_level`` with per-minute range ``minute_range_pips``; the quoted
    spread is held at ``spread_pips``; volume follows ``vol_pattern`` (or a
    default two-session hump). Weekends/holidays can be emulated by passing
    vol_pattern=zeros (carry-forward day). Returns (bid_bytes, ask_bytes).
    """
    spec = PAIR_SPECS[symbol]
    rng = np.random.default_rng(seed)
    n = RECORDS_PER_DAY
    sec = np.arange(0, _DAY_SECONDS, 60, dtype=np.int64)
    steps = rng.normal(0.0, 0.5 * spec.pip_size, size=n).cumsum()
    mid_open = mid_level + steps
    mid_close = mid_open + rng.normal(0.0, 0.5 * spec.pip_size, size=n)
    half = spread_pips * spec.pip_size / 2.0
    r = minute_range_pips * spec.pip_size
    bid_open = mid_open - half
    ask_open = mid_open + half
    bid_close = mid_close - half
    ask_close = mid_close + half
    bid_low = np.minimum(bid_open, bid_close) - r / 2.0
    ask_low = np.minimum(ask_open, ask_close) - r / 2.0
    bid_high = np.maximum(bid_open, bid_close) + r / 2.0
    ask_high = np.maximum(ask_open, ask_close) + r / 2.0
    if vol_pattern is None:
        # London/NY hump, quiet Asia, thin 21-23Z -- activity-shaped.
        hour = sec // 3600
        base = 40 + 220 * np.exp(-((hour - 14.0) ** 2) / 18.0) \
            + 60 * np.exp(-((hour - 1.0) ** 2) / 8.0)
        base[(hour >= 21) & (hour < 23)] *= 0.15
        vol_pattern = base * rng.uniform(0.5, 1.5, size=n)
    vol = np.round(vol_pattern.astype(np.float64), 2)
    scale = spec.price_divisor

    def q(x):
        return np.clip(np.rint(x * scale), 1, 2 ** 31 - 1).astype(np.uint32)

    bid_payload = encode_bi5(sec, q(bid_open), q(bid_close), q(bid_low),
                             q(bid_high), vol.astype(np.float32))
    ask_payload = encode_bi5(sec, q(ask_open), q(ask_close), q(ask_low),
                             q(ask_high), vol.astype(np.float32))
    return compress_bi5(bid_payload), compress_bi5(ask_payload)
