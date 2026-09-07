"""V6-P0b (A3): Stooq daily CSV parsing + adjustment-behavior detection.

Parse convention contract for ``https://stooq.com/q/d/l/?s=<symbol>&i=d``
(the endpoint verified against the site's own chart-page "Download data"
link during the light phase; see p0b_license_evidence.json):

* header exactly ``Date,Open,High,Low,Close,Volume``;
* date format ``YYYY-MM-DD`` (ISO), one row per trading day;
* OHLC decimal numbers, ``Volume`` integer (``0`` on non-traded rows);
* ordering as served by the source is preserved by the parser; the probe
  runner FAILS LOUD if the served order is not ascending by date, because
  an unordered series silently corrupts return computations downstream.

Adjustment semantics are NOT assumed. The module only provides detection
helpers used by the L7 corporate-action cross-check:

* ``daily_log_returns`` — consecutive-day returns of the retrieved series;
* ``split_window_continuity`` — given an SEC-evidenced split window and the
  raw-split price impact implied by the recorded ratio, checks whether the
  retrieved series shows a discontinuity of that magnitude inside the
  window. A series that shows NO such discontinuity is behaving like a
  SPLIT-ADJUSTED series; one that shows the discontinuity is behaving like
  a RAW series. The verdict is recorded as measured evidence, never as an
  assumed convention.

The module deliberately contains no dividend-adjustment inference: a single
adjusted series cannot identify dividend adjustment factors without an
external raw reference, and inventing one would violate the evidence
discipline (handbook section 11).
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Sequence, Tuple

EXPECTED_HEADER = ["Date", "Open", "High", "Low", "Close", "Volume"]


class StooqParseError(RuntimeError):
    """Raised on any parse-contract violation (fail-loud, never skipped)."""


@dataclass(frozen=True)
class DailyBar:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


def parse_stooq_daily_csv(text: str) -> List[DailyBar]:
    """Parse a Stooq daily CSV document, enforcing the parse contract."""
    if text is None or not text.strip():
        raise StooqParseError("empty document")
    lowered = text[:8192].lower()
    if "requires javascript to verify your browser" in lowered or "/__verify" in lowered:
        raise StooqParseError("document is an anti-bot challenge page, not CSV")
    if text.lstrip().startswith("<!DOCTYPE") or text.lstrip().startswith("<html"):
        raise StooqParseError("document is HTML, not CSV")

    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if r and any(cell.strip() for cell in r)]
    if not rows:
        raise StooqParseError("no rows in CSV")
    header = [c.strip() for c in rows[0]]
    if header != EXPECTED_HEADER:
        raise StooqParseError(f"unexpected header {header}; expected {EXPECTED_HEADER}")

    bars: List[DailyBar] = []
    for lineno, row in enumerate(rows[1:], start=2):
        if len(row) != len(EXPECTED_HEADER):
            raise StooqParseError(f"line {lineno}: expected {len(EXPECTED_HEADER)} fields, got {len(row)}")
        try:
            d = date.fromisoformat(row[0].strip())
        except ValueError as exc:
            raise StooqParseError(f"line {lineno}: bad date {row[0]!r}") from exc
        try:
            o, h, l, c = (float(row[i]) for i in (1, 2, 3, 4))
            v = int(float(row[5]))
        except ValueError as exc:
            raise StooqParseError(f"line {lineno}: bad numeric field {row!r}") from exc
        for name, val in (("open", o), ("high", h), ("low", l), ("close", c)):
            if math.isnan(val) or math.isinf(val) or val <= 0.0:
                raise StooqParseError(f"line {lineno}: non-positive/invalid {name}={val}")
        if h < l:
            raise StooqParseError(f"line {lineno}: high {h} < low {l}")
        if h < max(o, c) - 1e-9 or l > min(o, c) + 1e-9:
            raise StooqParseError(f"line {lineno}: OHLC interval violated (o={o} h={h} l={l} c={c})")
        if v < 0:
            raise StooqParseError(f"line {lineno}: negative volume {v}")
        bars.append(DailyBar(d, o, h, l, c, v))

    if bars and any(bars[i].date >= bars[i + 1].date for i in range(len(bars) - 1)):
        raise StooqParseError("dates are not strictly ascending as served")
    return bars


def daily_log_returns(bars: Sequence[DailyBar]) -> List[Tuple[date, float]]:
    out: List[Tuple[date, float]] = []
    for prev, cur in zip(bars, bars[1:]):
        out.append((cur.date, math.log(cur.close / prev.close)))
    return out


def split_window_continuity(
    bars: Sequence[DailyBar],
    window_start: date,
    window_end: date,
    split_ratio: float,
    raw_impact_return_tolerance: float = 0.5,
) -> dict:
    """Detect whether a raw split discontinuity appears inside the window.

    ``split_ratio`` is shares-new per share-old (2.0 = 2:1, 50.0 = 50:1).
    For a forward split, a RAW series must show a return of approximately
    ``1/ratio - 1`` on the effective day. ``raw_impact_return_tolerance``
    bounds how close to the raw impact counts as "raw-like" (default 0.5
    means a measured return within 50% relative distance of the raw impact
    classifies the series as raw-like at that day).
    """
    raw_impact = 1.0 / split_ratio - 1.0
    rets = daily_log_returns(bars)
    in_window = [
        (d, r) for d, r in rets if window_start <= d <= window_end
    ]
    if not in_window:
        return {
            "verdict": "NO_DATA_IN_WINDOW",
            "raw_impact_return": raw_impact,
            "min_return_in_window": None,
            "measured_days": 0,
        }
    min_day, min_r = min(in_window, key=lambda dr: dr[1])
    # use additive returns for interpretability
    additive = [(d, math.exp(r) - 1.0) for d, r in in_window]
    min_day, min_add = min(additive, key=lambda dr: dr[1])
    raw_like = raw_impact < 0 and min_add <= raw_impact * raw_impact_return_tolerance
    return {
        "verdict": "RAW_LIKE_DISCONTINUITY" if raw_like else "NO_RAW_DISCONTINUITY_ADJUSTED_LIKE",
        "raw_impact_return": raw_impact,
        "min_return_in_window_additive": min_add,
        "min_return_day": min_day.isoformat(),
        "measured_days": len(in_window),
    }
