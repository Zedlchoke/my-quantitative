"""Read-only staged-data loader for A5-V15-F1-ELITE-SIZE-ASYM.

Reads the machine-local staged parquet root recorded in
``staged_root.json`` (layout ``<root>/{metrics,klines,funding}/<SYM>.parquet``)
through a single wiring point, with the frozen availability and integrity
semantics.  NOTHING here is used by the tests' synthetic fixtures beyond the
schema they must reproduce.

Frozen obligations implemented (authorities in the package docstring):

* availability: a decision at date ``D`` may only read metrics rows with
  ``metrics_date <= D - 3`` (MEASURED_BOUND_LAG_3D, p3_freeze binding);
  the runner enforces the window arithmetic, this loader only stamps rows
  with their metrics_date.
* label semantics (probe_verdict_v15): start-of-period on current published
  bytes -- the labeled-T metrics row carries the stock snapshot at T+5min;
  the daily observation of a metrics_date is its 00:00 UTC labeled row.
* global defect dates (amendment_1 measured census): 2025-07-21, 2025-07-22,
  2025-08-29, 2026-08-12 are dropped entirely (excluded, never readable).
* metrics-day cell integrity (p3_freeze row_integrity, per (symbol, date)):
  exactly 288 rows, 288 unique labels, full 00:00..23:55 grid, and finite
  ``count_toptrader_long_short_ratio`` / ``sum_toptrader_long_short_ratio``
  on the single 00:00 row.  A day failing the check is a MISSING cell that
  feeds the amendment_1 >10% window-hole refusal rule -- it is NOT a crash
  (amendment_1: ONGUSDT is runnable and "expected to refuse decisions under
  the window rule").
* fail closed (raise) on structural malformation only: missing symbol file,
  missing required columns, unparsable ``create_time``, symbol-column
  mismatch, missing 15m kline bars / misaligned 15m grid (klines are zero
  tolerance per amendment_1), funding stamps duplicated, or
  ``|funding_rate| > 0.0375`` (documented extreme cap; measured -0.02 floor
  events are legitimate data).  Data holes are never synthesized and never
  silently dropped.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import pyarrow.parquet as pq

from research.v15.families.elite_size_asym.frozen_identity import (
    FUNDING_RATE_ABS_BOUND,
    GLOBAL_DEFECT_DATES,
    UNIVERSE,
)

STAGED_ROOT_JSON = Path(__file__).resolve().parent / "staged_root.json"

METRICS_REQUIRED_COLUMNS = (
    "create_time",
    "symbol",
    "count_toptrader_long_short_ratio",
    "sum_toptrader_long_short_ratio",
)
KLINES_REQUIRED_COLUMNS = (
    "open_time_ms",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time_ms",
)
FUNDING_REQUIRED_COLUMNS = ("funding_time_ms", "funding_rate")

_CREATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class FailClosed(RuntimeError):
    """Structural input malformation -- the loader never synthesizes."""


def staged_data_root() -> Path:
    """The absolute staged root recorded in this family's staged_root.json."""
    payload = json.loads(STAGED_ROOT_JSON.read_text(encoding="utf-8"))
    root = Path(str(payload["data_root"]))
    if not root.is_absolute():
        raise FailClosed(f"staged root must be absolute, got {root}")
    for subtree in ("metrics", "klines", "funding"):
        if not (root / subtree).is_dir():
            raise FailClosed(f"staged subtree missing: {root / subtree}")
    return root


def parse_metrics_date(raw: str) -> date:
    """Parse a metrics ``create_time`` label ("YYYY-MM-DD HH:MM:SS", UTC)."""
    label = str(raw)
    # fast path for the fixed-width frozen format, strptime fallback
    if len(label) == 19 and label[4] == "-" and label[7] == "-" and label[10] == " " and label[13] == ":" and label[16] == ":":
        try:
            return date(int(label[0:4]), int(label[5:7]), int(label[8:10]))
        except ValueError:
            pass
    try:
        stamp = datetime.strptime(label, _CREATE_TIME_FORMAT).replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise FailClosed(f"unparsable metrics create_time {raw!r}: {exc}") from exc
    return stamp.date()


def _metrics_grid_times() -> Tuple[str, ...]:
    return tuple(
        (datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=5 * i))
        .strftime("%H:%M:%S")
        for i in range(288)
    )


_GRID_TIMES = _metrics_grid_times()


@dataclass(frozen=True)
class MetricCell:
    """One (symbol, metrics_date) staged cell."""

    count_ratio_00: Optional[float]
    sum_ratio_00: Optional[float]
    ok: bool


def _excluded(date_value: date) -> bool:
    return date_value.isoformat() in GLOBAL_DEFECT_DATES


def load_metric_cells(
    data_root: Path | str, symbol: str, *, min_date: Optional[date] = None
) -> Dict[date, MetricCell]:
    """Per-(date) staged metrics cell for one symbol (00:00 UTC observation).

    The four global defect dates are dropped entirely (never readable).  A
    cell is ``ok`` only under the full frozen row-integrity check (288 rows,
    288 unique labels, full 00:00..23:55 grid, single 00:00 row with finite
    authorized ratio fields); anything else is a MISSING cell for the
    amendment_1 window-hole census.  ``min_date`` drops earlier days from
    the census entirely (they fall before every decision window).
    """
    path = Path(data_root) / "metrics" / f"{symbol}.parquet"
    if not path.is_file():
        raise FailClosed(f"staged metrics file missing: {path}")
    table = pq.read_table(path)
    columns = set(table.column_names)
    missing = [c for c in METRICS_REQUIRED_COLUMNS if c not in columns]
    if missing:
        raise FailClosed(f"{symbol}: metrics columns missing: {sorted(missing)}")
    create_time = table.column("create_time").to_pylist()
    symbol_col = table.column("symbol").to_pylist()
    count_col = table.column("count_toptrader_long_short_ratio").to_pylist()
    sum_col = table.column("sum_toptrader_long_short_ratio").to_pylist()

    # single pass: per-day row count, distinct-label count, and the 00:00 row
    day_rows: Dict[date, int] = {}
    day_labels: Dict[date, set] = {}
    midnight: Dict[date, Tuple[float, float]] = {}
    midnight_n: Dict[date, int] = {}
    date_cache: Dict[str, date] = {}
    for raw_time, row_symbol, count, total in zip(
        create_time, symbol_col, count_col, sum_col
    ):
        label = str(raw_time)
        prefix = label[:10]
        day = date_cache.get(prefix)
        if day is None:
            day = parse_metrics_date(label)
            date_cache[prefix] = day
        if _excluded(day):
            continue
        if str(row_symbol) != symbol:
            raise FailClosed(
                f"{symbol}: metrics row symbol mismatch: {row_symbol!r}"
            )
        if min_date is not None and day < min_date:
            continue
        day_rows[day] = day_rows.get(day, 0) + 1
        labels = day_labels.get(day)
        if labels is None:
            day_labels[day] = labels = set()
        labels.add(label)
        if label.endswith("00:00:00"):
            midnight_n[day] = midnight_n.get(day, 0) + 1
            if count is not None and total is not None:
                try:
                    midnight[day] = (float(count), float(total))
                except (TypeError, ValueError):
                    pass

    expected = set(_GRID_TIMES)
    cells: Dict[date, MetricCell] = {}
    for day, n_rows in day_rows.items():
        labels = day_labels[day]
        ok = (
            n_rows == 288
            and len(labels) == 288
            and {label[-8:] for label in labels} == expected
            and midnight_n.get(day, 0) == 1
        )
        pair = midnight.get(day)
        if ok and pair is not None and math.isfinite(pair[0]) and math.isfinite(pair[1]):
            cells[day] = MetricCell(pair[0], pair[1], True)
        else:
            cells[day] = MetricCell(None, None, False)
    return cells


@dataclass(frozen=True)
class KlineBars:
    """Validated 15m klines for one symbol (execution authority)."""

    opens: Dict[date, float]
    last_bar_close_ns: int
    last_bar_close_price: float


def load_klines(data_root: Path | str, symbol: str) -> KlineBars:
    """00:00 UTC bar opens per day for one symbol; grid fail-closed.

    Klines are the staged execution authority with zero defect tolerance
    (amendment_1): every day present in the file must carry exactly 96
    15-minute bars on an aligned grid, else :class:`FailClosed`.
    """
    path = Path(data_root) / "klines" / f"{symbol}.parquet"
    if not path.is_file():
        raise FailClosed(f"staged klines file missing: {path}")
    table = pq.read_table(path)
    missing = [c for c in KLINES_REQUIRED_COLUMNS if c not in set(table.column_names)]
    if missing:
        raise FailClosed(f"{symbol}: klines columns missing: {sorted(missing)}")
    open_time_ms = table.column("open_time_ms").to_pylist()
    open_col = table.column("open").to_pylist()
    close_col = table.column("close").to_pylist()

    opens: Dict[date, float] = {}
    rows_by_day: Dict[date, list[Tuple[int, float, float]]] = {}
    for open_ms, bar_open, bar_close in zip(open_time_ms, open_col, close_col):
        open_ms = int(open_ms)
        if open_ms % 900_000 != 0:
            raise FailClosed(f"{symbol}: kline open_time_ms off 15m grid: {open_ms}")
        day = datetime.fromtimestamp(open_ms / 1000.0, tz=timezone.utc).date()
        rows_by_day.setdefault(day, []).append((open_ms, float(bar_open), float(bar_close)))
    for day, rows in sorted(rows_by_day.items()):
        if len(rows) != 96:
            raise FailClosed(
                f"{symbol}: klines day {day.isoformat()} has {len(rows)} bars != 96"
            )
        stamps = [r[0] for r in rows]
        if stamps != list(range(stamps[0], stamps[0] + 96 * 900_000, 900_000)):
            raise FailClosed(
                f"{symbol}: klines day {day.isoformat()} grid not contiguous 15m"
            )
        midnight = [r for r in rows if r[0] % 86_400_000 == 0]
        if len(midnight) != 1:
            raise FailClosed(
                f"{symbol}: klines day {day.isoformat()} lacks one 00:00 bar"
            )
        opens[day] = midnight[0][1]
    last = max(rows_by_day[max(rows_by_day)], key=lambda r: r[0])
    return KlineBars(
        opens=opens,
        last_bar_close_ns=(last[0] + 900_000) * 1_000_000,
        last_bar_close_price=last[2],
    )


def load_funding(
    data_root: Path | str, symbol: str
) -> Tuple[Tuple[int, float], ...]:
    """Validated native funding settlement rows ``(ms_utc, rate)`` ascending.

    Settlement stamps are unique and strictly ascending; every rate obeys the
    amendment_1 documented extreme cap ``|rate| <= 0.0375`` (measured -0.02
    floor-clamp events are legitimate settlements and pass the cap).
    """
    path = Path(data_root) / "funding" / f"{symbol}.parquet"
    if not path.is_file():
        raise FailClosed(f"staged funding file missing: {path}")
    table = pq.read_table(path)
    missing = [
        c for c in FUNDING_REQUIRED_COLUMNS if c not in set(table.column_names)
    ]
    if missing:
        raise FailClosed(f"{symbol}: funding columns missing: {sorted(missing)}")
    stamps = table.column("funding_time_ms").to_pylist()
    rates = table.column("funding_rate").to_pylist()
    rows = sorted((int(ms), float(rate)) for ms, rate in zip(stamps, rates))
    for (ms_a, rate_a), (ms_b, rate_b) in zip(rows, rows[1:]):
        if ms_a == ms_b:
            raise FailClosed(f"{symbol}: duplicate funding stamp {ms_a}")
        if not math.isfinite(rate_a):
            raise FailClosed(f"{symbol}: non-finite funding rate at {ms_a}")
        if abs(rate_a) > FUNDING_RATE_ABS_BOUND:
            raise FailClosed(
                f"{symbol}: funding rate {rate_a} at {ms_a} exceeds the "
                f"documented extreme cap {FUNDING_RATE_ABS_BOUND}"
            )
    if rows:
        if not math.isfinite(rows[-1][1]):
            raise FailClosed(f"{symbol}: non-finite funding rate at {rows[-1][0]}")
        if abs(rows[-1][1]) > FUNDING_RATE_ABS_BOUND:
            raise FailClosed(
                f"{symbol}: funding rate {rows[-1][1]} at {rows[-1][0]} exceeds "
                f"the documented extreme cap {FUNDING_RATE_ABS_BOUND}"
            )
    return tuple(rows)


def load_snapshot(
    data_root: Path | str, *, min_date: Optional[date] = None
) -> Dict[str, dict]:
    """Whole-universe staged snapshot for the family runner.

    ``min_date`` (the earliest metrics day any frozen decision window can
    read: first scored day - max window lookback) bounds the cell census.
    """
    root = Path(data_root)
    symbols: Sequence[str] = UNIVERSE
    return {
        "metrics": {
            sym: load_metric_cells(root, sym, min_date=min_date) for sym in symbols
        },
        "klines": {sym: load_klines(root, sym) for sym in symbols},
        "funding": {sym: load_funding(root, sym) for sym in symbols},
    }


__all__ = [
    "FailClosed",
    "KlineBars",
    "MetricCell",
    "STAGED_ROOT_JSON",
    "load_funding",
    "load_klines",
    "load_metric_cells",
    "load_snapshot",
    "staged_data_root",
]
