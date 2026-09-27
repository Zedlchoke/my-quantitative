"""Raw-OHLCV price panel with an explicit column allowlist (R2-1/R2-5).

The on-disk NG6 panel carries a vendor `adjusted_close` column. It is
FORBIDDEN (R2-1). This module is the single reader of panel bytes; it only
ever extracts the allowlisted keys, and any attempt to request a forbidden
column raises ForbiddenColumnError.
"""
from __future__ import annotations

import gzip
import json
import math
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import config as C
from .loaders import ForbiddenColumn, PANEL_FORBIDDEN_COLUMNS

ALLOWED = frozenset({"date", "open", "high", "low", "close", "volume"})


def load_name_bars(ticker: str, columns: Optional[Sequence[str]] = None) -> List[dict]:
    """Read one name's panel file, extracting ONLY allowlisted columns.

    `columns` must be a subset of the allowlist. Requesting anything else
    (including `adjusted_close`) raises ForbiddenColumnError — the
    test-failable enforcement of R2-1.
    """
    if columns is not None:
        req = set(columns)
        bad = req - ALLOWED
        if bad:
            raise ForbiddenColumn(
                f"columns outside raw-OHLCV allowlist requested: {sorted(bad)}"
            )
    else:
        req = set(ALLOWED)
    path = f"{C.PANEL_DIR}/{ticker}.json.gz"
    bars: List[dict] = []
    with gzip.open(path, "rt") as f:
        rows = json.load(f)
    for r in rows:
        out = {}
        for k in r:
            if k in PANEL_FORBIDDEN_COLUMNS:
                continue  # never extracted, never stored, never read
            if k in req:
                out[k] = r[k]
        bars.append(out)
    return bars


class NameSeries:
    """Guarded per-name raw arrays (basis: raw OHLCV only, R2-1)."""

    __slots__ = ("ticker", "dates", "idx", "open", "high", "low", "close",
                 "vol", "dv", "fill_ok")

    def __init__(self, ticker: str) -> None:
        self.ticker = ticker
        self.dates: List[str] = []
        self.idx: Dict[str, int] = {}
        self.open: List[float] = []
        self.high: List[float] = []
        self.low: List[float] = []
        self.close: List[float] = []
        self.vol: List[float] = []
        self.dv: List[float] = []       # dollar volume = close * volume (raw)
        self.fill_ok: List[bool] = []   # B1 extreme-print / B2 volume-0 law

    def __len__(self) -> int:
        return len(self.dates)


def build_name_series(ticker: str, counters: Optional[dict] = None) -> Optional[NameSeries]:
    bars = load_name_bars(ticker, columns=["date", "open", "high", "low", "close", "volume"])
    if not bars:
        return None
    ns = NameSeries(ticker)
    seen_dates = set()
    for b in bars:
        d = b["date"]
        if d in seen_dates:
            if counters is not None:
                counters["duplicate_dates"] = counters.get("duplicate_dates", 0) + 1
            continue
        seen_dates.add(d)
        o = float(b["open"]); c = float(b["close"]); v = float(b["volume"])
        if not (math.isfinite(o) and math.isfinite(c)) or o <= 0 or c <= 0:
            if counters is not None:
                counters["nonpositive_or_nonfinite"] = counters.get("nonpositive_or_nonfinite", 0) + 1
            continue
        ns.dates.append(d)
        ns.idx[d] = len(ns.dates) - 1
        ns.open.append(o)
        ns.high.append(float(b["high"]))
        ns.low.append(float(b["low"]))
        ns.close.append(c)
        ns.vol.append(v)
        ns.dv.append(c * v)
        ns.fill_ok.append(False)  # pass 2
    if not ns.dates:
        return None
    # pass 2: B1 extreme prints (both directions) + B2 volume-0 (X1/X2 law)
    for i in range(len(ns.dates)):
        ok = ns.vol[i] > 0.0
        if not ok and counters is not None:
            counters["zero_volume_bars_b2"] = counters.get("zero_volume_bars_b2", 0) + 1
        if i > 0 and ok:
            if abs(math.log(ns.close[i] / ns.close[i - 1])) >= C.EXTREME_PRINT_LOG:
                ok = False
                if counters is not None:
                    counters["extreme_print_bars_b1"] = counters.get("extreme_print_bars_b1", 0) + 1
        ns.fill_ok[i] = ok
    return ns


class Panel:
    """All cohort names in memory (raw arrays)."""

    def __init__(self, tickers: Sequence[str], counters: Optional[dict] = None) -> None:
        self.names: Dict[str, NameSeries] = {}
        for t in tickers:
            ns = build_name_series(t, counters)
            if ns is not None:
                self.names[t] = ns

    def get(self, ticker: str) -> Optional[NameSeries]:
        return self.names.get(ticker)

    def truncate_at(self, cutoff_instant_et_epoch_by_date: Dict[str, str]) -> "Panel":
        """Panel truncated per name: keep only bars with date <= cutoff date.

        Used by the panel-truncation replay (E6d). Cutoffs are bar dates
        (a session's last byte of information is its close, 16:00 ET).
        """
        p = Panel.__new__(Panel)
        p.names = {}
        for t, ns in self.names.items():
            cut = cutoff_instant_et_epoch_by_date.get(t)
            if cut is None:
                p.names[t] = ns
                continue
            k = ns.idx.get(cut)
            if k is None:
                # cutoff date not a bar date: keep bars strictly before the
                # first bar after the cutoff (searchsorted on dates)
                k = _last_idx_le(ns.dates, cut)
            ns2 = NameSeries(t)
            ns2.dates = ns.dates[: k + 1]
            ns2.idx = {d: i for i, d in enumerate(ns2.dates)}
            ns2.open = ns.open[: k + 1]
            ns2.high = ns.high[: k + 1]
            ns2.low = ns.low[: k + 1]
            ns2.close = ns.close[: k + 1]
            ns2.vol = ns.vol[: k + 1]
            ns2.dv = ns.dv[: k + 1]
            ns2.fill_ok = ns.fill_ok[: k + 1]
            p.names[t] = ns2
        return p


def _last_idx_le(dates: List[str], cut: str) -> int:
    lo, hi = 0, len(dates) - 1
    ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if dates[mid] <= cut:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def dvmed60(ns: NameSeries, i: int, decision_instant_check=None) -> Optional[float]:
    """Trailing 60-session median dollar volume ending at bar i (inclusive).

    Unfinished-window guard (E6c): bar i must itself be closed at decision
    time; the caller asserts that. Returns None when fewer than DV_MIN_PRESENT
    of the trailing DV_WINDOW sessions exist (fail-closed).
    """
    lo = max(0, i - C.DV_WINDOW + 1)
    window = ns.dv[lo : i + 1]
    if len(window) < C.DV_MIN_PRESENT:
        return None
    return float(np.median(window))


def band_class_bps(dvmed: Optional[float]) -> Tuple[str, float]:
    """Frozen band schedule; fails closed at band-C below the floor."""
    if dvmed is None or dvmed < C.DV_FLOOR:
        return "BELOW_FLOOR", 25.0
    for floor, bps in C.COST_BANDS:
        if dvmed >= floor:
            return ("A" if bps == 10.0 else "B" if bps == 15.0 else "C"), bps
    return "C", 25.0
