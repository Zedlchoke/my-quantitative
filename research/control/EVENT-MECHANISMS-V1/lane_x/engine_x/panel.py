"""NG6 raw-OHLCV price panel reader (R2-1/R2-5).

Reads per-ticker bar files, keeps ONLY date/open/high/low/close/volume.
The vendor `adjusted_close` column is forbidden by R2-1 and is never read
into memory beyond the load-time projection performed here.
"""

from __future__ import annotations

import gzip
import json
import os
from bisect import bisect_left, bisect_right
from dataclasses import dataclass

from .tzlaw import session_close_instant, session_open_instant


@dataclass(frozen=True)
class BarLaws:
    """Per-bar validity under the STOCKS-AMIHUD-RETEST bar laws (B1/B2/X1),
    re-stated on RAW closes because R2-1 forbids adjusted series."""

    extreme_print: bool   # B1: |close_d/close_{d-1} - 1| >= 9 (either direction)
    zero_volume: bool     # B2/X1: unfillable


class NamePanel:
    """Sorted per-name session grid built from raw OHLCV bars."""

    def __init__(self, ticker: str, bars: list[dict]):
        bars = sorted(bars, key=lambda b: b["date"])
        self.ticker = ticker
        self.dates: list[str] = [b["date"] for b in bars]
        self.open = [float(b["open"]) for b in bars]
        self.close = [float(b["close"]) for b in bars]
        self.volume = [float(b["volume"]) for b in bars]
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

    def raw_close_on_or_before(self, ticker: str, date_str: str) -> float | None:
        p = self.get(ticker)
        i = bisect_right(p.dates, date_str) - 1
        if i < 0:
            return None
        return p.close[i]
