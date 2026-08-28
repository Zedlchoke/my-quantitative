"""Synchronized point-in-time daily-close panel builder (Sprint V4, owner A2).

Implements the PLAN.md section 19 PIT data contract:

* Catalog bar ``ts_event`` is the exchange CLOSE stamp of each 15m bar
  (mirrors ``research.data_audit`` semantics).
* ``build_daily_closes`` resamples completed 15m bars to one close per UTC
  day boundary: for each midnight ``C`` in the window the emitted point is
  ``(ts_event, close)`` of the LAST bar whose ``ts_event <= C``. A boundary
  with no bar at-or-before it emits nothing ("days only when a bar exists by
  cutoff" -- warmup semantics). This is the PIT guarantee: a bar arriving
  later can never change an earlier day's close, because selection only looks
  backwards.
* ``DataUnavailable`` is raised instead of silently publishing a close whose
  sourcing bar is stale: a boundary (every boundary, not only the terminal
  one) whose newest bar at-or-before it is older than ``C - BAR_INTERVAL_NS``
  has missed the 15m bar that closes the interval, so the "daily close" would
  actually be an older bar re-labelled as the day's close. Companion fix to
  Sprint V10R Option A for V10P prelaunch gate ``G05_COVERAGE_SHORTFALL_HIGH``
  (staged ETHUSDT bars ended 2026-08-20T02:29:59.999Z against a
  2026-08-21T00:00:00Z window end: 86 bars / 21.5h short, and
  ``build_daily_closes`` still emitted a terminal close from that bar).
  Fail-closed, defined HERE -- ``research.hyp_a8_m01`` imports this module and
  ``research.adapter_v10`` transitively imports M01, so this file must not
  import from ``research.adapter_v10`` (circular-import hazard).
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
#: Catalog bar cadence: 15-minute bars whose ``ts_event`` is the exchange
#: CLOSE stamp. A boundary ``C`` is fully covered iff its newest bar
#: at-or-before it closes inside ``(C - BAR_INTERVAL_NS, C]``.
BAR_INTERVAL_NS = 900_000_000_000
_PRICE_SCALE = 10 ** 16  # nautilus parquet fixed-scalar encoding (verified)
_BAR_COLUMNS = ("ts_event", "open", "high", "low", "close", "volume")


class DataUnavailable(RuntimeError):
    """Bar data cannot support a point-in-time close: fail closed, never guess.

    Raised by :func:`build_daily_closes` (and therefore
    :func:`build_btc_benchmark`) when a day boundary's newest bar is more than
    one 15-minute interval old, and by :func:`coverage_report` when a
    symbol's terminal close is older than ``window_end - BAR_INTERVAL_NS``.
    Both conditions mean the requested close would be sourced from a bar that
    is not the last bar of its interval -- a silent coverage shortfall
    (V10P ``G05_COVERAGE_SHORTFALL_HIGH``). Callers must treat this as a hard
    data failure for that window, not a partial result.
    """


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


def iso_utc(ns: int) -> str:
    """Render epoch nanoseconds as a millisecond ISO-8601 UTC stamp.

    Millisecond precision mirrors the catalog's ``...T02:29:59.999Z`` bar
    close stamps; exact integer arithmetic (no float round-trip).
    """
    seconds, rem = divmod(int(ns), 1_000_000_000)
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + f".{rem // 1_000_000:03d}Z"


def staleness_bars(bar_ts_ns: int, reference_ns: int) -> int:
    """Whole 15m intervals missing between a sourcing bar and ``reference_ns``.

    ``0`` when the bar closes inside ``(reference_ns - BAR_INTERVAL_NS,
    reference_ns]`` -- i.e. it IS the last bar of the interval it feeds.
    ``1`` means exactly one bar is missing, ``86`` means the V10P terminal
    shortfall. Exact integer arithmetic on the half-open interval so a bar
    stamped exactly ``reference_ns - BAR_INTERVAL_NS`` counts as stale.
    """
    return max(0, (int(reference_ns) - int(bar_ts_ns)) // BAR_INTERVAL_NS)


def _stale_source_error(
    symbol: str, reference: str, bar_ts_ns: int, stale: int
) -> DataUnavailable:
    """Build the fail-closed error for a stale sourcing bar."""
    return DataUnavailable(
        f"{symbol}: close for {reference} cannot be sourced fresh -- newest "
        f"bar at-or-before it is {iso_utc(bar_ts_ns)}, "
        f"{stale} bar(s) ({stale * 0.25:.2f}h) stale against a "
        f"{BAR_INTERVAL_NS // 1_000_000_000 // 60}-minute bar cadence "
        f"(tolerance: 1 bar interval); refusing to emit a stale PIT close"
    )


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
    """Resample completed 15m bars to daily closes (PIT-safe, fail-closed).

    For each UTC midnight boundary ``C`` in the window, emit the
    ``(ts_event, close)`` of the last bar with ``ts_event <= C``; boundaries
    with no earlier bar emit nothing (warmup). Because ``ts_event`` is the
    bar CLOSE stamp, that bar is only the day's close if it falls inside
    ``(C - BAR_INTERVAL_NS, C]``; if the newest bar at-or-before ``C`` is
    older than that, the 15m bar that closes the day is missing and
    :class:`DataUnavailable` is raised -- naming the symbol, the boundary
    ISO, the stale bar ISO and the staleness in bars and hours -- rather
    than re-labelling an older bar as the day's close. The rule applies to
    EVERY boundary, not only the terminal one (a mid-window hole is the same
    defect as a short tail). Deterministic and backward-looking otherwise:
    selection still looks strictly backwards, so a later bar can never
    change an earlier day's close, and the raise fires on the first stale
    boundary in ascending order.
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
            if idx is None:
                # No bar at-or-before this boundary: warmup, emit nothing.
                # NOT a staleness failure -- there is nothing to be stale.
                continue
            bar_ts = stamps[idx]
            stale = staleness_bars(bar_ts, cutoff)
            if stale:
                raise _stale_source_error(
                    sym, iso_utc(cutoff), bar_ts, stale
                )
            series.append((bar_ts, bars[idx][4]))
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
          "freshness":          {sym: {"last_close_bar_ts": iso_or_None,
                                       "staleness_bars": int_or_None,
                                       "fresh": bool}},
        }

    ``freshness`` is measured evidence (V10R Option A companion fix): each
    panel close carries the ``ts_event`` of the bar it was sourced from, so
    the report can state how far that bar trails ``window_end``. A symbol
    with no closes reports ``None``/``None``/``False`` rather than
    disappearing. ``fresh`` is False whenever the last sourcing bar is not
    the last bar of the terminal interval.

    Fail-closed: :class:`DataUnavailable` is raised when any symbol WITH a
    non-empty series has its last close's sourcing bar older than
    ``window_end - BAR_INTERVAL_NS`` (the terminal bar of the window is
    stale, i.e. the tail coverage shortfall that V10P gate
    ``G05_COVERAGE_SHORTFALL_HIGH`` caught). Symbols with an empty series
    are exempt: they already report zero days and must keep doing so
    (warmup/partial-universe semantics) rather than aborting the report.

    The split lets XG0 emit distinct reason codes:
    ``benchmark_coverage_incomplete`` (benchmark block short/zero) vs
    ``funding_coverage_insufficient`` (funding settlements missing/partial)
    vs ``coverage_below_declared`` (bar intersection narrower than declared).
    Benchmark coverage is CONTEXT ONLY and must not be reported as a funding
    failure. ``metadata_symbols`` lists symbols with usable instrument
    metadata; anything absent reports False.
    """
    start_ns, end_ns = _window_bounds_ns(window_start_iso, window_end_iso)
    syms = sorted(panel)
    bar_coverage: dict[str, int] = {}
    freshness_limit_ns = end_ns - BAR_INTERVAL_NS
    for sym in syms:
        series = panel[sym] or []
        bar_coverage[sym] = len(series)
        if series:
            last_ts = int(series[-1][0])
            stale = staleness_bars(last_ts, end_ns)
            if last_ts <= freshness_limit_ns:
                raise _stale_source_error(
                    sym, f"window_end {window_end_iso}", last_ts, stale
                )

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

    freshness: dict[str, dict] = {}
    for sym in syms:
        series = panel[sym] or []
        if not series:
            freshness[sym] = {
                "last_close_bar_ts": None,
                "staleness_bars": None,
                "fresh": False,
            }
            continue
        last_ts = int(series[-1][0])
        stale = staleness_bars(last_ts, end_ns)
        freshness[sym] = {
            "last_close_bar_ts": iso_utc(last_ts),
            "staleness_bars": stale,
            "fresh": stale == 0,
        }

    return {
        "bar_coverage": bar_coverage,
        "benchmark_coverage": benchmark_coverage,
        "funding_coverage": funding_coverage,
        "metadata_coverage": metadata_coverage,
        "freshness": freshness,
    }
