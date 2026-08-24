"""Synchronized point-in-time daily-close panel builder (Sprint V4, owner A2).

Implements the PLAN.md section 19 PIT data contract:

* Catalog bar ``ts_event`` is the exchange CLOSE stamp of each 15m bar
  (mirrors ``research.data_audit`` semantics).
* ``build_daily_closes`` resamples completed 15m bars to one close per UTC
  day boundary: for each midnight ``C`` in the window the emitted point is
  ``(ts_event, close)`` of the LAST bar whose ``ts_event <= C``. A boundary
  with no bar at-or-before it emits nothing ("days only when a bar exists by
  cutoff"). This is the PIT guarantee: a bar arriving later can never change
  an earlier day's close, because selection only looks backwards.
* ``build_btc_benchmark`` is the same construction restricted to BTCUSDT
  (benchmark context only, PLAN.md section 19.3).
* ``coverage_report`` summarises days_present/first_day/last_day per symbol
  for XG0 evidence.

No lookahead: bars are read once, filtered to ``[window_start, window_end]``
by ``ts_event``, and each boundary resolves strictly backwards. Reads are
deterministic: duplicate timestamps across parquet parts resolve to the LAST
occurrence in sorted-part order (same rule every run).
"""

from __future__ import annotations

import calendar
from datetime import datetime, timezone
from pathlib import Path

import pyarrow.parquet as pq

DAY_NS = 86_400_000_000_000
BENCHMARK_SYMBOL = "BTCUSDT"
_PRICE_SCALE = 10 ** 16  # nautilus parquet fixed-scalar encoding (verified)
_BAR_COLUMNS = ("ts_event", "open", "high", "low", "close", "volume")


# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #
def parse_iso_ns(iso: str) -> int:
    """Parse an ISO-8601 UTC timestamp/date to epoch nanoseconds."""
    text = str(iso).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt = dt.astimezone(timezone.utc)
    epoch_s = calendar.timegm(dt.utctimetuple())
    return epoch_s * 1_000_000_000 + dt.microsecond * 1000


def _window_bounds_ns(window_start_iso: str, window_end_iso: str) -> tuple[int, int]:
    start_ns = parse_iso_ns(window_start_iso)
    end_ns = parse_iso_ns(window_end_iso)
    if end_ns < start_ns:
        raise ValueError(f"window_end {window_end_iso!r} before window_start {window_start_iso!r}")
    return start_ns, end_ns


def _day_boundaries(start_ns: int, end_ns: int) -> list[int]:
    """All UTC midnights C with start_ns <= C <= end_ns (epoch-aligned)."""
    first = ((start_ns + DAY_NS - 1) // DAY_NS) * DAY_NS
    last = (end_ns // DAY_NS) * DAY_NS
    if last < first:
        return []
    return list(range(first, last + 1, DAY_NS))


def _boundary_of(ts_ns: int) -> int:
    """The UTC midnight boundary this closing bar feeds (next midnight)."""
    return ((ts_ns + DAY_NS - 1) // DAY_NS) * DAY_NS


def _iso_date(ts_ns: int) -> str:
    return datetime.fromtimestamp(ts_ns // 1_000_000_000, tz=timezone.utc).strftime("%Y-%m-%d")


# --------------------------------------------------------------------------- #
# Catalog reading (pyarrow-direct, mirrors research.data_audit conventions)
# --------------------------------------------------------------------------- #
def _bar_type(instrument_id: str) -> str:
    return f"{instrument_id}-15-MINUTE-LAST-EXTERNAL"


def _decode_fixed16(raw: bytes) -> float:
    """Decode nautilus parquet fixed_size_binary(16) scalar to float."""
    return int.from_bytes(raw, "little", signed=True) / _PRICE_SCALE


def _bar_type_dir(catalog_path: str | Path, instrument_id: str) -> Path:
    return Path(catalog_path) / "data" / "binance_bar" / _bar_type(instrument_id)


def _read_bars(
    catalog_path: str | Path,
    instrument_id: str,
    start_ns: int,
    end_ns: int,
) -> list[tuple[int, float, float, float, float, float]]:
    """Read one symbol's 15m bars as (ts_event, open, high, low, close, volume).

    Sorted ascending by ts_event; duplicate ts_event resolve to the value from
    the lexically-last parquet part (deterministic last-write-wins).
    """
    directory = _bar_type_dir(catalog_path, instrument_id)
    files = sorted(directory.rglob("*.parquet"))
    if not files:
        return []
    table = pq.read_table([str(f) for f in files], columns=list(_BAR_COLUMNS))
    ts_col = table.column("ts_event").to_pylist()
    value_cols = {
        name: table.column(name).to_pylist() for name in _BAR_COLUMNS[1:]
    }
    by_ts: dict[int, tuple[float, float, float, float, float]] = {}
    for i, ts in enumerate(ts_col):
        if start_ns <= ts <= end_ns:
            by_ts[ts] = tuple(
                _decode_fixed16(value_cols[name][i]) for name in _BAR_COLUMNS[1:]
            )
    return [
        (ts, *by_ts[ts]) for ts in sorted(by_ts)
    ]


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def load_bars_15m(
    catalog_path: str | Path,
    symbols: list[str],
    window_start_iso: str,
    window_end_iso: str,
) -> dict[str, list[tuple[int, float, float, float, float, float]]]:
    """Load raw 15m bars per symbol for the shared-capital engine input."""
    start_ns, end_ns = _window_bounds_ns(window_start_iso, window_end_iso)
    return {
        sym: _read_bars(catalog_path, sym, start_ns, end_ns) for sym in symbols
    }


def build_daily_closes(
    catalog_path: str | Path,
    symbols: list[str],
    window_start_iso: str,
    window_end_iso: str,
) -> dict[str, list[tuple[int, float]]]:
    """Resample completed 15m bars to daily closes (PIT-safe).

    For each UTC midnight boundary ``C`` in the window, emit the
    ``(ts_event, close)`` of the last bar with ``ts_event <= C``; boundaries
    with no earlier bar emit nothing. Deterministic and backward-looking.
    """
    start_ns, end_ns = _window_bounds_ns(window_start_iso, window_end_iso)
    boundaries = _day_boundaries(start_ns, end_ns)
    panel: dict[str, list[tuple[int, float]]] = {}
    for sym in symbols:
        bars = _read_bars(catalog_path, sym, start_ns, end_ns)
        stamps = [b[0] for b in bars]
        series: list[tuple[int, float]] = []
        for cutoff in boundaries:
            idx = _last_index_at_or_before(stamps, cutoff)
            if idx is not None:
                series.append((stamps[idx], bars[idx][4]))
        panel[sym] = series
    return panel


def build_btc_benchmark(
    catalog_path: str | Path,
    window_start_iso: str,
    window_end_iso: str,
) -> dict[str, list[tuple[int, float]]]:
    """Daily closes for the BTCUSDT benchmark only (same shape/semantics)."""
    return build_daily_closes(
        catalog_path, [BENCHMARK_SYMBOL], window_start_iso, window_end_iso
    )


def _last_index_at_or_before(stamps: list[int], cutoff_ns: int) -> int | None:
    lo, hi, ans = 0, len(stamps) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if stamps[mid] <= cutoff_ns:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def coverage_report(
    panel: dict[str, list[tuple[int, float]]],
    window_start_iso: str,
    window_end_iso: str,
) -> dict[str, dict]:
    """XG0 evidence: days_present / first_day / last_day per symbol.

    ``first_day``/``last_day`` are the UTC dates of the earliest/latest
    closing bars contributing a daily close (the economic close days).
    """
    _window_bounds_ns(window_start_iso, window_end_iso)  # validate arguments
    report: dict[str, dict] = {}
    for sym in sorted(panel):
        series = panel[sym] or []
        if series:
            first_ts, last_ts = series[0][0], series[-1][0]
            report[sym] = {
                "days_present": len(series),
                "first_day": _iso_date(first_ts),
                "last_day": _iso_date(last_ts),
            }
        else:
            report[sym] = {"days_present": 0, "first_day": None, "last_day": None}
    return report
