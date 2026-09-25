"""Shared data wiring for the BASISLV window-fold replication (cycle
CRYPTO-HISTORICAL-REPLICATION-3F-V1, namespace basislv_replication).

Mirrors the PROVEN basislv_equivalence wiring (equiv_runner.py, verdict
EQUIVALENT bit-exact) on the B-window replication authorities:

* basis  : ``basislv_replication/basis_parquet/<SYM>/<SYM>_basis_15m.parquet``
           (basis_convert.py output, frozen restage schema).  Loader value
           path = frozen ``audits.load_premium_series`` semantics via
           ``basis_series_from_rows``: duplicates / availability-before-close
           / non-finite premiums fail closed; the |p_b - basisRate| <= 1e-4
           absolute identity check fails closed; grid gaps are REPORTED and
           remain NaN slots (disclosed deviation from the A9F restage's
           zero-gap refusal -- one systematic missing bucket
           2023-11-10T04:05Z in 15/19 names; the engine's per-slot
           eligibility then refuses straddling formation windows).
* bars   : ``catalog_live_crypto_b20`` (2020-01..2024-08, 20 symbols) via the
           EXACT equivalence loader semantics: catalog ``ts_event`` is the
           kline OPEN stamp -> remap to the close boundary it terminates
           (``snap(ts) + 15m``, availability = close boundary), i128/1e16
           decode, duplicate-boundary refusal, boundary-window filter,
           frozen ``bars_from_rows``.  THE REMAP IS LOAD-BEARING (the
           pre-fix DIVERGENT equivalence run measured the +1-bar lag).
* funding: ``funding_data_scan/scan_2026`` (B window) with the frozen
           ``snap_funding_times_to_hour`` row mapping; NO frozen-count trim
           exists for this window -- rows are consumed AS-IS (disclosed).
* ticks  : the per-symbol tick table recorded in the b20 build report
           (fapi exchangeInfo metadata at catalog build time -- current
           metadata, disclosed convention; no uniform stubs).

Universe: the FROZEN ``TRADEABLE_UNIVERSE`` (19 ranked names) -- the engine's
own per-stamp eligibility decides; nothing is pre-narrowed.  Feed for bars =
universe + BTCUSDT (pinned benchmark, context-only).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
CD = HERE.parent
V14_ROOT = CD / "recovered/v14_root"

BASIS_PARQUET_ROOT = HERE / "basis_parquet"
CATALOG = CD / "catalog_live_crypto_b20"
CATALOG_TICKS_REPORT = CD / "catalog_live_crypto_b20_build_report.json"
FUNDING_SCAN = CD / "funding_data_scan/scan_2026"  # B window

import sys

sys.path.insert(0, str(V14_ROOT))

from research.panel import _bar_type_dir  # noqa: E402
from research.v12.data_contract import snap_funding_times_to_hour  # noqa: E402
from research.v14.families.basislv_premfade.audits import (  # noqa: E402
    TRADEABLE_UNIVERSE,
    _snap_close_to_boundary_vectorized,
    decode_i128,
)
from research.v14.families.basislv_premfade.strategy import (  # noqa: E402
    BASIS_IDENTITY_TOL_ABS,
    BENCHMARK_SYMBOL,
    BUCKET_NS,
    bars_from_rows,
    basis_series_from_rows,
)

#: Frozen 19 ranked names (staged REQUIRED_SYMBOLS minus the benchmark leg).
UNIVERSE: tuple[str, ...] = tuple(TRADEABLE_UNIVERSE)
#: Feed = universe + the pinned context-only benchmark leg.
FEED_SYMBOLS: tuple[str, ...] = tuple(sorted(set(UNIVERSE) | {BENCHMARK_SYMBOL}))

#: Preregistered replication folds (plan section 3).  Each fold window is one
#: plugin binding; the window-fold subclass maps its weekly Monday stamps to
#: chronological thirds of the bound window with force-flat boundaries
#: (chr3f_illiq_plugin.py pattern).
FOLDS: tuple[tuple[str, str, str], ...] = (
    ("Y2021", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z"),
    ("Y2022", "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    ("Y2023", "2023-01-01T00:00:00Z", "2024-01-01T00:00:00Z"),
    ("Y2024P", "2024-01-01T00:00:00Z", "2024-08-19T00:00:00Z"),
)

ARMS: tuple[tuple[str, str], ...] = (
    ("ANCHOR", "BASISLV-PREMFADE-28D"),
    ("INV", "BASISLV-PREMFADE-28D-INV"),
)

#: First archive month per symbol -- the measured P0 census carried by
#: chr3f_illiq_plugin.py (the SAME frozen 20-symbol universe).  Used ONLY for
#: the context-marks narrowing (benchmark_context_symbols, context-only
#: buy-and-hold, ``enters_denominator`` False): the runner requires an
#: entry/exit mark for every context symbol at the first/last instant, and a
#: not-yet-listed name has no bars.  No scored surface consumes it.
FIRST_ARCHIVE_MONTH: dict[str, tuple[int, int]] = {
    "1000PEPEUSDT": (2023, 5), "AAVEUSDT": (2020, 10), "ACEUSDT": (2023, 12),
    "ADAUSDT": (2020, 1), "AVAXUSDT": (2020, 9), "BCHUSDT": (2020, 1),
    "BNBUSDT": (2020, 2), "BOMEUSDT": (2024, 3), "BTCUSDT": (2020, 1),
    "DOGEUSDT": (2020, 7), "ENAUSDT": (2024, 4), "ETHUSDT": (2020, 1),
    "LINKUSDT": (2020, 1), "NEARUSDT": (2020, 10), "ONGUSDT": (2023, 11),
    "SOLUSDT": (2020, 9), "SUIUSDT": (2023, 5), "WLDUSDT": (2023, 7),
    "XRPUSDT": (2020, 1), "ZECUSDT": (2020, 2),
}


def listed_at(window_start_iso: str) -> tuple[str, ...]:
    """Symbols whose first archive month precedes a window start (YYYY-MM)."""
    w0 = window_start_iso[:7]
    y, m = int(w0[:4]), int(w0[5:7])
    return tuple(
        sorted(s for s in FEED_SYMBOLS if FIRST_ARCHIVE_MONTH.get(s, (9999, 1)) <= (y, m))
    )


# --------------------------------------------------------------------------- #
# Basis loader (frozen value path; grid gaps REPORTED not fatal)
# --------------------------------------------------------------------------- #
def load_basis_world(
    symbols: Sequence[str] = UNIVERSE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Frozen loader semantics on the basislv_replication parquet root."""
    import pyarrow.parquet as pq

    world: dict[str, Any] = {}
    report: dict[str, Any] = {}
    for sym in symbols:
        path = BASIS_PARQUET_ROOT / sym / f"{sym}_basis_15m.parquet"
        if not path.is_file():
            raise FileNotFoundError(
                f"basis parquet missing: {path} (run basis_convert.py first)"
            )
        table = pq.read_table(path)
        opens_ms = np.asarray(
            table.column("open_time_ms").to_pylist(), dtype=np.int64
        )
        fut = np.asarray(table.column("futures_price").to_pylist(), dtype=np.float64)
        idx = np.asarray(table.column("index_price").to_pylist(), dtype=np.float64)
        rate = np.asarray(table.column("basis_rate").to_pylist(), dtype=np.float64)
        if not (fut.shape[0] == idx.shape[0] == rate.shape[0] == opens_ms.shape[0]):
            raise ValueError(f"{sym}: basis route columns must share one length")
        with np.errstate(divide="ignore", invalid="ignore"):
            computed = (fut - idx) / idx
        admissible = (
            np.isfinite(computed) & np.isfinite(idx) & (idx > 0.0) & (fut > 0.0)
        )
        deviation = np.abs(computed[admissible] - rate[admissible])
        max_deviation = float(deviation.max()) if deviation.size else 0.0
        if max_deviation > BASIS_IDENTITY_TOL_ABS:
            raise ValueError(
                f"{sym}: basis-route identity check violated: max |p_b - "
                f"basisRate| = {max_deviation} > {BASIS_IDENTITY_TOL_ABS} "
                "(fail-closed)"
            )
        premium = np.where(admissible, computed, np.nan)
        opens_ns = (opens_ms.astype(np.int64) * 1_000_000).astype(np.int64)
        closes_ns = opens_ns + BUCKET_NS
        if opens_ns.size and int(opens_ns[0]) % BUCKET_NS != 0:
            raise ValueError(f"{sym}: basis bucket open off the 15m grid")
        rows = [
            (int(closes_ns[i]), int(closes_ns[i]), float(premium[i]))
            for i in range(opens_ns.shape[0])
        ]
        series = basis_series_from_rows(rows)  # duplicates/non-finite fail closed
        expected = (
            (int(opens_ns[-1]) - int(opens_ns[0])) // BUCKET_NS + 1
            if opens_ns.size
            else 0
        )
        n_slots = int(series.premium.shape[0])
        n_nan = int(n_slots - np.isfinite(series.premium).sum())
        world[sym] = series
        report[sym] = {
            "path": str(path),
            "rows": int(opens_ms.shape[0]),
            "slots": n_slots,
            "expected_slots_in_span": int(expected),
            "nan_slots": n_nan,
            "grid_gap_policy": "REPORTED_NAN (engine per-slot refusal decides)",
            "grid_gap_clean": bool(n_nan == 0),
            "max_abs_identity_deviation": max_deviation,
            "identity_tol_abs": BASIS_IDENTITY_TOL_ABS,
            "origin_iso": iso_utc(int(series.origin_ns)),
        }
    return world, report


# --------------------------------------------------------------------------- #
# Execution bars (verbatim equivalence loader semantics; catalog root param)
# --------------------------------------------------------------------------- #
def load_execution_bars_catalog(
    symbols: Sequence[str],
    *,
    catalog: str | Path = CATALOG,
    start_ns: Optional[int] = None,
    end_ns: Optional[int] = None,
) -> dict[str, Any]:
    """Frozen audits.load_execution_bars semantics on a CHR3F catalog root.

    Catalog stamping law (root-caused in the equivalence gate): the catalog
    stamps each BinanceBar with ts_event = the kline OPEN time; the loader
    remaps each row to the close boundary it terminates
    (``snap(ts_event) + 15m``, availability = that close boundary).  Without
    the remap every fill/mark reads one bar LATE (+1-bar execution lag).
    """
    import pyarrow.parquet as pq

    out: dict[str, Any] = {}
    for sym in symbols:
        sym_dir = Path(_bar_type_dir(str(catalog), str(sym)))
        paths = sorted(sym_dir.rglob("*.parquet"))
        if not paths:
            raise FileNotFoundError(f"no bar parquets for {sym} under {sym_dir}")
        rows: list[tuple[int, int, float]] = []
        seen: set[int] = set()
        for path in paths:
            table = pq.read_table(path, columns=["ts_event", "close"])
            ts = np.asarray(table.column("ts_event").to_pylist(), dtype=np.int64)
            boundary = _snap_close_to_boundary_vectorized(ts) + BUCKET_NS
            mask = np.ones(boundary.shape[0], dtype=bool)
            if start_ns is not None:
                mask &= boundary >= int(start_ns)
            if end_ns is not None:
                mask &= boundary <= int(end_ns)
            close_col = table.column("close").to_pylist()
            for i in np.nonzero(mask)[0]:
                b = int(boundary[i])
                if b in seen:
                    raise ValueError(f"{sym}: two bar closes snap to boundary {b}")
                seen.add(b)
                close, _raw = decode_i128(close_col[i])
                rows.append((b, b, close))
        rows.sort(key=lambda r: r[0])
        out[sym] = bars_from_rows(rows)
    return out


# --------------------------------------------------------------------------- #
# Settlements (frozen hour-snap row mapping; AS-IS, no frozen-count trim)
# --------------------------------------------------------------------------- #
def load_settlements_scan(
    symbols: Sequence[str] = UNIVERSE,
    *,
    scan_root: str | Path = FUNDING_SCAN,
) -> tuple[dict[str, tuple[dict, ...]], dict[str, Any]]:
    """funding.json rows -> hour-snapped {publish_ts_ns, value} tuples."""
    out: dict[str, tuple[dict, ...]] = {}
    report: dict[str, Any] = {}
    for sym in symbols:
        path = Path(scan_root) / str(sym) / "funding.json"
        if not path.is_file():
            raise FileNotFoundError(f"funding.json missing for {sym}: {path}")
        body = json.loads(path.read_text(encoding="utf-8"))
        rows = body.get("rows", [])
        times = [int(row["fundingTime"]) * 1_000_000 for row in rows]
        snapped, snap_meta = snap_funding_times_to_hour(times)
        settled = [
            {"publish_ts_ns": int(stamp), "value": float(row["fundingRate"])}
            for row, stamp in zip(rows, snapped)
        ]
        out[str(sym)] = tuple(settled)
        report[str(sym)] = {
            "raw_rows": len(rows),
            "snapped_rows": len(settled),
            "trim_status": "AS_IS (no frozen-count authority on the B window)",
            "snap_meta": dict(snap_meta),
        }
    return out, report


# --------------------------------------------------------------------------- #
# Tick sizes (fapi exchangeInfo metadata recorded in the b20 build report)
# --------------------------------------------------------------------------- #
def load_tick_sizes() -> dict[str, float]:
    report = json.loads(Path(CATALOG_TICKS_REPORT).read_text(encoding="utf-8"))
    ticks = {str(s): float(v["tick"]) for s, v in report["symbols"].items()}
    missing = sorted(set(FEED_SYMBOLS) - set(ticks))
    if missing:
        raise ValueError(f"tick sizes missing for {missing} in the b20 report")
    return ticks


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def iso_utc(stamp_ns: int) -> str:
    from research.v11.families.oilever_delev.strategy import iso_utc as _iso

    return str(_iso(int(stamp_ns)))


def parse_iso_utc(text: str) -> int:
    from research.v11.families.oilever_delev.strategy import parse_iso_utc as _p

    return int(_p(text))


def fold_bar_window(window_start_iso: str, window_end_iso: str) -> tuple[str, str]:
    """Frozen-shaped bars load window for one fold: start - 7d .. end + 3d.

    NOTE (disclosed): the dry-run/scored wiring does NOT use this window.
    It loads every feed symbol at its FULL catalog coverage, because 7 of
    the frozen 19 names have no bars at all inside the Y2021/Y2022 windows
    (``bars_from_rows`` refuses an empty series and an uninjected symbol
    would silently shrink the frozen 19-name universe).  The full-coverage
    series is a strict SUPERSET of this window: only on-schedule stamps are
    ever consumed (fills/marks/fold-terminal checks), and a not-yet-listed
    name refuses the signal with INSUFFICIENT_HISTORY exactly as with a
    windowed load.  Kept as the reference for what the frozen wiring shape
    would be on a one-year window.
    """
    from research.v14.families.basislv_premfade.strategy import DAY_NS

    start = parse_iso_utc(window_start_iso) - 7 * DAY_NS
    end = parse_iso_utc(window_end_iso) + 3 * DAY_NS
    return iso_utc(start), iso_utc(end)
