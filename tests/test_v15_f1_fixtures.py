"""Shared HAND-COMPUTED synthetic fixtures for the A5-V15-F1 tests.

ALL DATA SYNTHETIC: nothing here reads the machine-local staged root (the
real staged bytes never enter any test), nothing is scored, no ledger is
touched.  The fixtures reproduce the STAGED SCHEMA (the same parquet columns
the frozen loader reads) so the loader/runner exercise the real code paths
on synthetic bytes.

The hand world (``build_constant_panel_root``):

* 20 frozen universe symbols; metrics day grid 288 rows (00:00..23:55,
  5-minute) per (symbol, day); span 2025-08-10..2026-08-21 (the earliest
  day any frozen decision window can read: neighbour D-12 for the first
  scored day 2025-08-22);
* ``count_toptrader_long_short_ratio`` = 1.0 for every symbol/day;
  ``sum_toptrader_long_short_ratio`` = 1 + 0.1*i for the symbol at frozen
  universe index i, so the frozen feature ``s_i = ln(1 + 0.1*i)`` is
  CONSTANT in time and strictly increasing in the frozen symbol order:
  long side (bottom-7) = universe[0:7], short side (top-7) =
  universe[13:20], middle universe[7:13] flat, per-name weight 0.5/7
  (side gross 0.5 per side; gross exactly 1.0);
* 15m klines at a constant price ``PRICE = 100.0`` (96 aligned bars/day);
* funding = 0.0 (8h stamps) -- the book realizes price PnL 0 and funding 0,
  so the ONLY PnL is the hand-exact fill cost:
  rate = 5e-4 (fee) + 2 * 0.01 / 100 (2 ticks) = 7e-4 per unit notional;
  every full transition trades Sigma|dw| = 14 * (0.5/7) = 1.0, and the
  frozen force-flat folds give exactly 6 transitions (entry + flat per
  fold) => cost_total = 6 * 7e-4 = 0.0042 (hand);
* the four global defect dates in the frozen loader apply to this panel as
  in production: 2025-08-29 and 2026-08-12 fall inside the fixture span and
  are dropped by the loader, so anchor/control decisions whose windows
  contain them (2025-09-01..05 and 2026-08-15..19) refuse for every
  symbol: exactly 2 * 5 * 20 = 200 anchor refusals; the neighbour's 10-day
  window tolerates 1/10 = 10% (not > 10%) and refuses none.

Targeted variants (``build_root`` kwargs + mutation helpers) inject holes,
malformed inputs, value shifts and panel mutations at exact (symbol, date)
coordinates.  Malformed "empty_fields" days are written as non-finite
floats -- the loader's cell-integrity check treats them exactly like empty
numeric fields (unusable 00:00 observation -> missing cell).
"""

from __future__ import annotations

import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Set, Tuple

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from research.v15.families.elite_size_asym.frozen_identity import UNIVERSE

METRICS_DAY_ROWS = 288
KLINE_DAY_ROWS = 96

METRICS_SCHEMA = pa.schema(
    [
        ("create_time", pa.string()),
        ("symbol", pa.string()),
        ("sum_open_interest", pa.float64()),
        ("sum_open_interest_value", pa.float64()),
        ("count_toptrader_long_short_ratio", pa.float64()),
        ("sum_toptrader_long_short_ratio", pa.float64()),
        ("count_long_short_ratio", pa.float64()),
        ("sum_taker_long_short_vol_ratio", pa.float64()),
        ("ts", pa.timestamp("us")),
    ]
)
KLINES_SCHEMA = pa.schema(
    [
        ("open_time_ms", pa.int64()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("volume", pa.float64()),
        ("close_time_ms", pa.int64()),
    ]
)
FUNDING_SCHEMA = pa.schema(
    [("funding_time_ms", pa.int64()), ("funding_rate", pa.float64())]
)

PRICE = 100.0
TICK = 0.01
FEE_BPS = 5.0
FEE_RATE = 5.0e-4
SLIP_RATE = 2 * TICK / PRICE  # 2e-4
BASE_RATE = FEE_RATE + SLIP_RATE  # 7e-4 per unit notional

FIXTURE_METRICS_START = date(2025, 8, 10)
FIXTURE_END = date(2026, 8, 21)

_TIMES288: List[str] = [
    (datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=5 * i)).strftime(
        "%H:%M:%S"
    )
    for i in range(METRICS_DAY_ROWS)
]


def default_count(symbol: str, day: date) -> float:
    return 1.0


def default_sum(symbol: str, day: date) -> float:
    index = UNIVERSE.index(symbol)
    return 1.0 + 0.1 * index


def daterange(start: date, end: date) -> List[date]:
    cursor = start
    days: List[date] = []
    while cursor <= end:
        days.append(cursor)
        cursor += timedelta(days=1)
    return days


def _epoch_ms(day: date, hour: int = 0, minute: int = 0) -> int:
    stamp = datetime(
        day.year, day.month, day.day, hour, minute, tzinfo=timezone.utc
    )
    return int(stamp.timestamp()) * 1000


def _epoch_us(day: date) -> int:
    return int(
        datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp()
    ) * 1_000_000


def _metrics_table(
    symbol: str,
    days: Sequence[date],
    count_fn: Callable[[str, date], float],
    sum_fn: Callable[[str, date], float],
    skip_days: Set[date],
    malformed_days: Optional[Mapping[date, str]] = None,
) -> pa.Table:
    kept = [day for day in days if day not in skip_days]
    malformed = malformed_days or {}
    n = METRICS_DAY_ROWS * len(kept)
    base_us = np.repeat(
        np.array([_epoch_us(day) for day in kept], dtype=np.int64),
        METRICS_DAY_ROWS,
    )
    slot_us = np.tile(
        np.arange(METRICS_DAY_ROWS, dtype=np.int64) * 300_000_000, len(kept)
    )
    ts = base_us + slot_us
    counts = np.array([float(count_fn(symbol, day)) for day in kept], dtype=np.float64)
    sums = np.array([float(sum_fn(symbol, day)) for day in kept], dtype=np.float64)
    count_col = np.repeat(counts, METRICS_DAY_ROWS)
    sum_col = np.repeat(sums, METRICS_DAY_ROWS)
    for day, mode in malformed.items():
        if day in skip_days:
            continue
        offset = kept.index(day) * METRICS_DAY_ROWS
        if mode == "empty_fields":
            count_col[offset : offset + METRICS_DAY_ROWS] = np.nan
            sum_col[offset : offset + METRICS_DAY_ROWS] = np.nan
        elif mode == "nonfinite_midnight":
            count_col[offset] = np.nan
            sum_col[offset] = np.nan
        else:
            raise ValueError(f"unknown malformed mode {mode!r}")
    oi = np.tile(
        np.arange(METRICS_DAY_ROWS, dtype=np.float64), len(kept)
    ) + 1000.0
    oi_value = oi * 1.0e4
    crowd = np.full(n, 1.0)
    taker = np.full(n, 0.5)
    prefixes = [day.isoformat() for day in kept]
    labels = [prefix + " " + stamp for prefix in prefixes for stamp in _TIMES288]
    table = pa.table(
        {
            "create_time": pa.array(labels, pa.string()),
            "symbol": pa.array([symbol] * n, pa.string()),
            "sum_open_interest": pa.array(oi, pa.float64()),
            "sum_open_interest_value": pa.array(oi_value, pa.float64()),
            "count_toptrader_long_short_ratio": pa.array(count_col, pa.float64()),
            "sum_toptrader_long_short_ratio": pa.array(sum_col, pa.float64()),
            "count_long_short_ratio": pa.array(crowd, pa.float64()),
            "sum_taker_long_short_vol_ratio": pa.array(taker, pa.float64()),
            "ts": pa.array(ts, pa.timestamp("us")),
        },
        schema=METRICS_SCHEMA,
    )
    duplicate_days = [day for day, mode in malformed.items() if mode == "duplicate_midnight" and day not in skip_days]
    for day in duplicate_days:
        # one extra row repeating the 00:00 label: breaks the 288-unique check
        stamp = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
        extra = pa.table(
            {
                "create_time": pa.array([stamp.strftime("%Y-%m-%d %H:%M:%S")], pa.string()),
                "symbol": pa.array([symbol], pa.string()),
                "sum_open_interest": pa.array([1.0], pa.float64()),
                "sum_open_interest_value": pa.array([1.0e7], pa.float64()),
                "count_toptrader_long_short_ratio": pa.array(
                    [float(count_fn(symbol, day))], pa.float64()
                ),
                "sum_toptrader_long_short_ratio": pa.array(
                    [float(sum_fn(symbol, day))], pa.float64()
                ),
                "count_long_short_ratio": pa.array([1.0], pa.float64()),
                "sum_taker_long_short_vol_ratio": pa.array([0.5], pa.float64()),
                "ts": pa.array([_epoch_us(day)], pa.timestamp("us")),
            },
            schema=METRICS_SCHEMA,
        )
        table = pa.concat_tables([table, extra])
    return table


def _klines_table(
    symbol: str, days: Sequence[date], price: float, drop_days: Set[date]
) -> pa.Table:
    kept = [day for day in days if day not in drop_days]
    base = np.repeat(
        np.array([_epoch_ms(day) for day in kept], dtype=np.int64), KLINE_DAY_ROWS
    )
    slots = np.tile(
        np.arange(KLINE_DAY_ROWS, dtype=np.int64) * 900_000, len(kept)
    )
    open_ms = base + slots
    close_ms = open_ms + 899_999
    n = len(open_ms)
    price_col = np.full(n, float(price))
    high = price_col * 1.001
    low = price_col * 0.999
    return pa.table(
        {
            "open_time_ms": pa.array(open_ms, pa.int64()),
            "open": pa.array(price_col, pa.float64()),
            "high": pa.array(high, pa.float64()),
            "low": pa.array(low, pa.float64()),
            "close": pa.array(price_col, pa.float64()),
            "volume": pa.array(np.ones(n), pa.float64()),
            "close_time_ms": pa.array(close_ms, pa.int64()),
        },
        schema=KLINES_SCHEMA,
    )


def _funding_table(
    symbol: str, days: Sequence[date], rate_fn: Callable[[str, date], float]
) -> pa.Table:
    stamps: List[int] = []
    rates: List[float] = []
    for day in days:
        for hour in (0, 8, 16):
            stamps.append(_epoch_ms(day, hour))
            rates.append(float(rate_fn(symbol, day)))
    return pa.table(
        {
            "funding_time_ms": pa.array(stamps, pa.int64()),
            "funding_rate": pa.array(rates, pa.float64()),
        },
        schema=FUNDING_SCHEMA,
    )


def build_root(
    root: Path,
    *,
    symbols: Sequence[str] = UNIVERSE,
    metrics_start: date = FIXTURE_METRICS_START,
    metrics_end: date = FIXTURE_END,
    klines_start: date = FIXTURE_METRICS_START,
    klines_end: date = FIXTURE_END,
    funding_end: date = FIXTURE_END,
    count_fn: Callable[[str, date], float] = default_count,
    sum_fn: Callable[[str, date], float] = default_sum,
    funding_rate_fn: Callable[[str, date], float] = lambda symbol, day: 0.0,
    price: float = PRICE,
    skip_metrics_days: Optional[Mapping[str, Set[date]]] = None,
    malformed_metrics_days: Optional[Mapping[str, Mapping[date, str]]] = None,
    drop_kline_days: Optional[Mapping[str, Set[date]]] = None,
    metrics_start_by_symbol: Optional[Mapping[str, date]] = None,
    omit_symbols: Optional[Set[str]] = None,
    drop_metrics_columns: Sequence[str] = (),
    corrupt_create_time_symbol: Optional[str] = None,
) -> Path:
    """Write one synthetic staged root (parquet layout) and return it."""
    skip = skip_metrics_days or {}
    malformed = malformed_metrics_days or {}
    kline_drops = drop_kline_days or {}
    starts = metrics_start_by_symbol or {}
    root = Path(root)
    for subtree in ("metrics", "klines", "funding"):
        (root / subtree).mkdir(parents=True, exist_ok=True)
    all_metric_days = daterange(metrics_start, metrics_end)
    all_kline_days = daterange(klines_start, klines_end)
    funding_days = daterange(klines_start, funding_end)
    for symbol in symbols:
        if omit_symbols and symbol in omit_symbols:
            continue
        symbol_start = starts.get(symbol, metrics_start)
        symbol_days = [day for day in all_metric_days if day >= symbol_start]
        table = _metrics_table(
            symbol,
            symbol_days,
            count_fn,
            sum_fn,
            skip.get(symbol, set()),
            malformed.get(symbol, {}),
        )
        if drop_metrics_columns:
            table = table.drop_columns(list(drop_metrics_columns))
        if corrupt_create_time_symbol == symbol:
            labels = table.column("create_time").to_pylist()
            labels[0] = "not-a-timestamp"
            table = table.set_column(
                table.schema.get_field_index("create_time"),
                "create_time",
                pa.array(labels, pa.string()),
            )
        pq.write_table(table, root / "metrics" / f"{symbol}.parquet")
        pq.write_table(
            _klines_table(
                symbol, all_kline_days, price, kline_drops.get(symbol, set())
            ),
            root / "klines" / f"{symbol}.parquet",
        )
        pq.write_table(
            _funding_table(symbol, funding_days, funding_rate_fn),
            root / "funding" / f"{symbol}.parquet",
        )
    return root


def build_constant_panel_root(root: Path) -> Path:
    """The hand-world constant panel (see module docstring)."""
    return build_root(root)


TICK_SIZES: Dict[str, float] = {symbol: TICK for symbol in UNIVERSE}


def copy_root_with_mutated_metrics(
    source: Path,
    destination: Path,
    symbol: str,
    *,
    count_fn: Callable[[str, date], float] = default_count,
    sum_fn: Callable[[str, date], float] = default_sum,
) -> Path:
    """Copy a root; rewrite ONE symbol's metrics with new value functions."""
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    table = pq.read_table(source / "metrics" / f"{symbol}.parquet")
    labels = table.column("create_time").to_pylist()
    days = sorted({date.fromisoformat(label[:10]) for label in labels})
    pq.write_table(
        _metrics_table(symbol, days, count_fn, sum_fn, set(), {}),
        destination / "metrics" / f"{symbol}.parquet",
    )
    return destination


def shift_symbol_metrics_forward(
    source: Path, destination: Path, symbol: str, shift_days: int = 1
) -> Path:
    """Copy a root; shift ONE symbol's metrics rows forward by N days.

    Every row keeps its values under a label N days later (the earliest
    days fall off the start; nothing is synthesized).  The panel ends N
    days later than the original.
    """
    destination = Path(destination)
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    table = pq.read_table(source / "metrics" / f"{symbol}.parquet")
    labels = table.column("create_time").to_pylist()
    counts = table.column("count_toptrader_long_short_ratio").to_pylist()
    sums = table.column("sum_toptrader_long_short_ratio").to_pylist()
    per_day_counts: Dict[date, float] = {}
    per_day_sums: Dict[date, float] = {}
    for label, count, total in zip(labels, counts, sums):
        day = date.fromisoformat(label[:10])
        per_day_counts[day] = float(count)
        per_day_sums[day] = float(total)
    if len(per_day_counts) != len(labels) / METRICS_DAY_ROWS:
        raise ValueError("shift helper expects a clean constant-per-day panel")
    new_days = [day + timedelta(days=shift_days) for day in sorted(per_day_counts)]

    def shifted_count(_symbol: str, day: date) -> float:
        return per_day_counts[day - timedelta(days=shift_days)]

    def shifted_sum(_symbol: str, day: date) -> float:
        return per_day_sums[day - timedelta(days=shift_days)]

    pq.write_table(
        _metrics_table(symbol, new_days, shifted_count, shifted_sum, set(), {}),
        destination / "metrics" / f"{symbol}.parquet",
    )
    return destination


def day(const: str) -> date:
    return date.fromisoformat(const)


try:  # pytest is a test-time dependency only; the builder stays importable
    import pytest
except ImportError:  # pragma: no cover
    pytest = None

if pytest is not None:

    @pytest.fixture(scope="session")
    def constant_root(tmp_path_factory):
        """The hand-world constant panel, built ONCE per test session."""
        base = tmp_path_factory.mktemp("v15f1_constant")
        return build_constant_panel_root(base / "staged")
