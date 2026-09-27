"""NG6 raw-OHLCV price panel reader (R2-1/R2-5).

Reads per-ticker bar files, keeps ONLY date/open/high/low/close/volume.
The vendor `adjusted_close` column is forbidden by R2-1 and is never read
into memory beyond the load-time projection performed here.
"""

from __future__ import annotations

import gzip
import json
import math
import os
from bisect import bisect_left, bisect_right
from dataclasses import dataclass

import numpy as np

from .tzlaw import session_close_instant, session_open_instant

# Frozen cost contract (STOCKS-AMIHUD-RETEST-V1, G3 shared control 5) — the
# DVmed60 eligibility floor lives at the book stage (entry/exit fill
# feasibility, X1/X2); only the 15%-notional CAP is an execution-stage law
# (r3 AMB-14) and is deliberately absent here.
DV_FLOOR = 2_000_000.0
DV_WINDOW = 60
DV_MIN_PRESENT = 30
COST_BANDS = ((50_000_000.0, 10.0), (10_000_000.0, 15.0), (2_000_000.0, 25.0))
OPEN_BAND_MULT = 3.35   # Q-2 conditional law: entries fill at the open band
MIDDAY_BAND_MULT = 1.0  # exits fill at the close (~midday basis)


@dataclass(frozen=True)
class BarLaws:
    """Per-bar validity under the STOCKS-AMIHUD-RETEST bar laws (B1/B2/X1),
    re-stated on RAW closes because R2-1 forbids adjusted series."""

    extreme_print: bool   # B1: |close_d/close_{d-1} - 1| >= 9 (either direction)
    zero_volume: bool     # B2/X1: unfillable


class NamePanel:
    """Sorted per-name session grid built from raw OHLCV bars.

    r3-delta: panels apply the same ingestion guards as the lane I engine
    (duplicate dates: first occurrence wins, marked before validity; bars
    with non-finite or non-positive open/close skipped) so both engines see
    byte-identical session grids — the pre-r3 panel-guard DATA_VARIANT
    class is closed by construction.
    """

    def __init__(self, ticker: str, bars: list[dict]):
        bars = sorted(bars, key=lambda b: b["date"])
        self.ticker = ticker
        self.dates: list[str] = []
        self.open: list[float] = []
        self.close: list[float] = []
        self.volume: list[float] = []
        self.dv: list[float] = []          # dollar volume = close * volume (raw)
        seen: set[str] = set()
        for b in bars:
            d = b["date"]
            if d in seen:
                continue                    # duplicate date: first wins
            seen.add(d)                     # marked BEFORE validity (lane I parity)
            try:
                o = float(b["open"]); c = float(b["close"])
            except (TypeError, ValueError):
                continue
            if not (math.isfinite(o) and math.isfinite(c)) or o <= 0 or c <= 0:
                continue
            self.dates.append(d)
            self.open.append(o)
            self.close.append(c)
            v = float(b["volume"])
            self.volume.append(v)
            self.dv.append(c * v)
        self.index: dict[str, int] = {d: i for i, d in enumerate(self.dates)}
        self._close_epoch = [int(session_close_instant(s).timestamp()) for s in self.dates]
        self._open_epoch = [int(session_open_instant(s).timestamp()) for s in self.dates]

    # -- session resolution ----------------------------------------------

    def first_session_with_close_after(self, epoch_seconds: int) -> str | None:
        """First session whose 16:00 ET close is STRICTLY after the instant."""
        i = bisect_right(self._close_epoch, epoch_seconds)
        return self.dates[i] if i < len(self.dates) else None

    def first_session_with_open_after(self, epoch_seconds: int) -> str | None:
        """First session whose 09:30 ET open is STRICTLY after the instant."""
        i = bisect_right(self._open_epoch, epoch_seconds)
        return self.dates[i] if i < len(self.dates) else None

    def next_session_after(self, date_str: str) -> str | None:
        i = self.index.get(date_str)
        if i is None or i + 1 >= len(self.dates):
            return None
        return self.dates[i + 1]

    def session_at_offset(self, date_str: str, k: int) -> str | None:
        i = self.index.get(date_str)
        if i is None:
            return None
        j = i + k
        return self.dates[j] if j < len(self.dates) else None

    def last_session(self) -> str | None:
        return self.dates[-1] if self.dates else None

    def window_between(self, start_date: str, end_date: str) -> list[str]:
        """Session dates in [start_date, end_date] inclusive (string compare)."""
        i = self.index.get(start_date)
        j = self.index.get(end_date)
        if i is None or j is None or j < i:
            return []
        return self.dates[i:j + 1]

    # -- bar law evaluation -----------------------------------------------

    def bar_laws(self, date_str: str) -> BarLaws:
        i = self.index[date_str]
        extreme = False
        if i > 0 and self.close[i - 1] > 0 and self.close[i] > 0:
            up = self.close[i] / self.close[i - 1] - 1.0
            down = self.close[i - 1] / self.close[i] - 1.0
            # symmetric order-of-magnitude law (AMB-16): >=10x in either
            # direction counts as a B1 extreme print
            extreme = up >= 9.0 or down >= 9.0
        return BarLaws(extreme_print=extreme, zero_volume=(self.volume[i] <= 0.0))

    def fillable(self, date_str: str) -> bool:
        laws = self.bar_laws(date_str)
        return (not laws.extreme_print) and (not laws.zero_volume)

    # -- DVmed60 eligibility floor (frozen cost contract, book stage) ------

    def dvmed60(self, entry_idx: int) -> float | None:
        """Trailing 60-session median dollar volume ending at the LAST
        CLOSED session before entry (entry_idx - 1, inclusive); None when
        fewer than 30 of the trailing 60 sessions exist (fail-closed).
        Identical arithmetic to the lane I engine (np.median over the same
        raw close*volume floats)."""
        i = entry_idx - 1
        if i < 0:
            return None
        lo = max(0, i - DV_WINDOW + 1)
        window = self.dv[lo:i + 1]
        if len(window) < DV_MIN_PRESENT:
            return None
        return float(np.median(window))

    def band_class_bps(self, dvmed: float | None) -> tuple[str, float]:
        """Frozen band schedule; fails closed below the $2M floor."""
        if dvmed is None or dvmed < DV_FLOOR:
            return "BELOW_FLOOR", 25.0
        for floor, bps in COST_BANDS:
            if dvmed >= floor:
                return ("A" if bps == 10.0 else "B" if bps == 15.0 else "C"), bps
        return "C", 25.0


class PanelStore:
    """Lazy loader over the restored NG6 raw panel directory."""

    def __init__(self, panel_dir: str):
        self.panel_dir = panel_dir
        self._cache: dict[str, NamePanel] = {}

    def get(self, ticker: str) -> NamePanel:
        if ticker not in self._cache:
            path = os.path.join(self.panel_dir, ticker + ".json.gz")
            with gzip.open(path, "rt") as fh:
                raw = json.load(fh)
            self._cache[ticker] = NamePanel(
                ticker,
                [{"date": r["date"], "open": r["open"], "close": r["close"],
                  "volume": r["volume"]} for r in raw],
            )
        return self._cache[ticker]
    # (no price-fallback helper: r3 AMB-6 — unpriced A2 rows are dropped,
    # never imputed from the panel)
