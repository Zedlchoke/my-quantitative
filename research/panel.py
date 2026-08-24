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
* ``coverage_report`` emits DISTINCT coverage blocks per symbol (bar days,
  benchmark context days, funding settlements first/last/count, metadata
  flag) so XG0 can raise distinct reason codes (Sprint V5 finding F06).

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


# --------------------------------------------------------------------------- #
# Catalog reading (pyarrow-direct, mirrors research.data_audit conventions)
# --------------------------------------------------------------------------- #
def _bar_type_candidates(instrument_id: str) -> list[str]:
    """Bar-type directory names to try, most specific first.

    Catalog layout uses full Binance instrument ids
    (e.g. ``BTCUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL``); a bare symbol is
    resolved by appending the standard PERP suffix.
    """
    base = f"{instrument_id}-15-MINUTE-LAST-EXTERNAL"
    if "-BINANCE" in instrument_id or "-PERP" in instrument_id:
        return [base]
    return [f"{instrument_id}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL", base]


def _bar_type_dir(catalog_path: str | Path, instrument_id: str) -> Path:
    root = Path(catalog_path) / "data" / "binance_bar"
    for candidate in _bar_type_candidates(instrument_id):
        d = root / candidate
        if d.exists():
            return d
    return root / _bar_type_candidates(instrument_id)[-1]


def _decode_fixed16(raw: bytes) -> float:
    """Decode nautilus parquet fixed_size_binary(16) scalar to float."""
    return int.from_bytes(raw, "little", signed=True) / _PRICE_SCALE


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
    *,
    benchmark_symbol: str | None = BENCHMARK_SYMBOL,
    funding_bundles_dir: str | Path | None = None,
    metadata_symbols: list[str] | tuple[str, ...] | set[str] | None = None,
) -> dict[str, dict]:
    """XG0 evidence with DISTINCT coverage blocks (Sprint V5, finding F06).

    Returns::

        {
          "bar_coverage":       {sym: days_present},
          "benchmark_coverage": {benchmark_symbol: days_present_or_0},
          "funding_coverage":   {sym: {"settlements": n,
                                       "first": iso_date_or_None,
                                       "last":  iso_date_or_None}},
          "metadata_coverage":  {sym: bool},
        }

    The split lets XG0 emit distinct reason codes:
    ``benchmark_coverage_incomplete`` (benchmark block short/zero) vs
    ``funding_coverage_insufficient`` (funding settlements missing/partial)
    vs ``coverage_below_declared`` (bar intersection narrower than declared).
    Benchmark coverage is CONTEXT ONLY and must not be reported as a funding
    failure. ``metadata_symbols`` lists symbols with usable instrument
    metadata; anything absent reports False.
    """
    _window_bounds_ns(window_start_iso, window_end_iso)  # validate arguments
    syms = sorted(panel)
    bar_coverage: dict[str, int] = {}
    for sym in syms:
        bar_coverage[sym] = len(panel[sym] or [])

    benchmark_coverage: dict[str, int] = {}
    if benchmark_symbol:
        benchmark_coverage[benchmark_symbol] = bar_coverage.get(benchmark_symbol, 0)

    funding_coverage: dict[str, dict] = {}
    if funding_bundles_dir is not None:
        from research.funding_pit import load_funding_bundle

        root = Path(funding_bundles_dir)
        for sym in syms:
            path = root / sym / "funding.json"
            if not path.exists():
                funding_coverage[sym] = {
                    "settlements": 0, "first": None, "last": None,
                }
                continue
            payload = load_funding_bundle(root, sym)
            times_ms = sorted(int(row["fundingTime"]) for row in payload["rows"])
            funding_coverage[sym] = {
                "settlements": len(times_ms),
                "first": (
                    datetime.fromtimestamp(times_ms[0] / 1000, tz=timezone.utc)
                    .strftime("%Y-%m-%d")
                    if times_ms else None
                ),
                "last": (
                    datetime.fromtimestamp(times_ms[-1] / 1000, tz=timezone.utc)
                    .strftime("%Y-%m-%d")
                    if times_ms else None
                ),
            }

    known_meta = set(metadata_symbols or ())
    metadata_coverage: dict[str, bool] = {sym: sym in known_meta for sym in syms}

    return {
        "bar_coverage": bar_coverage,
        "benchmark_coverage": benchmark_coverage,
        "funding_coverage": funding_coverage,
        "metadata_coverage": metadata_coverage,
    }
