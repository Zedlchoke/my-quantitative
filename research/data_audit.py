"""Data coverage audit for the sprint matrix (owner: A2).

Audits the frozen research-scan universe (``config/research_scan_top20.yaml``)
against the live crypto catalog (default ``./catalog_live_crypto``, 15m bars)
and the funding bundles (default ``funding_data/scan_2026``), then classifies
every symbol against the frozen ``CellStatus`` contract:

* ``DATA_INCOMPLETE`` with one or more machine-readable reason codes
  (from ``contracts.protocol.REASON_CODES``):
  - ``duplicate_bars``
  - ``unexplained_gap``
  - ``funding_coverage_insufficient``
  - ``missing_instrument_metadata``
  - ``coverage_below_declared``
* otherwise the symbol is eligible for matrix cells.

The audit also reports the actual common intersection boundaries across ALL
universe symbols and across the S0 seven-symbol set, and compares them with the
declared S0 window (contracts/README.md: 1 year, 2025-08-21 -> 2026-08-21).

Usage::

    python -m research.data_audit --matrix-id audit_20260823

Writes ``results/matrix/<matrix_id>/coverage.json`` and prints a summary plus
CPU/disk environment info. Read-only over data directories.

Timestamp semantics: catalog bar ``ts_event`` is the exchange CLOSE stamp of
each 15-minute bar (e.g. ``...:14:59.999000064``); a complete series has
exactly 900s between consecutive stamps. Gaps are flagged beyond a small
tolerance to absorb nanosecond padding artifacts.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import yaml

from contracts.protocol import CellStatus

# --------------------------------------------------------------------------- #
# Frozen inputs
# --------------------------------------------------------------------------- #
DEFAULT_UNIVERSE_CONFIG = "config/research_scan_top20.yaml"
DEFAULT_CATALOG = "./catalog_live_crypto"
DEFAULT_FUNDING_DIR = "funding_data/scan_2026"
DEFAULT_MATRIX_ID = "audit"

# S0 declared window per contracts/README.md ("Known limitations"): one year,
# 2025-08-21 -> 2026-08-21 UTC, ~35,038 15m bars.
DECLARED_S0_START = "2025-08-21T00:00:00+00:00"
DECLARED_S0_END = "2026-08-21T00:00:00+00:00"

# S0 seven-symbol evidence set (PLAN.md / task brief).
S0_SYMBOLS = (
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
    "ETHUSDT",
)

BAR_INTERVAL_MINUTES = 15
INTERVAL_NS = BAR_INTERVAL_MINUTES * 60 * 1_000_000_000
# Consecutive close stamps are exactly INTERVAL_NS apart in a clean series;
# tolerate up to +2s for adapter timestamp padding before calling it a gap.
GAP_TOLERANCE_NS = 2_000_000_000


# --------------------------------------------------------------------------- #
# Catalog / bundle stat readers
# --------------------------------------------------------------------------- #
def _bar_type(instrument_id: str) -> str:
    return f"{instrument_id}-15-MINUTE-LAST-EXTERNAL"


def read_bar_timestamps(catalog_path: str | Path, instrument_id: str) -> list[int]:
    """Read only ``ts_event`` values for one symbol's 15m bars via pyarrow.

    Much faster than materialising Nautilus objects and robust to missing data.
    """
    bt_dir = Path(catalog_path) / "data" / "binance_bar" / _bar_type(instrument_id)
    if not bt_dir.exists():
        return []
    files = sorted(bt_dir.rglob("*.parquet"))
    if not files:
        return []
    table = pq.read_table([str(f) for f in files], columns=["ts_event"])
    return sorted(table.column("ts_event").to_pylist())


def bar_stats(timestamps_ns: list[int]) -> dict[str, object]:
    """Compute count/boundaries/duplicates/gaps from raw ns timestamps."""
    if not timestamps_ns:
        return {
            "bar_count": 0,
            "first_ts_utc": None,
            "last_ts_utc": None,
            "duplicate_timestamps": 0,
            "gaps_over_interval": 0,
        }
    series = pd.Series(timestamps_ns, dtype="int64")
    diffs = series.diff().dropna()
    gap_mask = diffs > INTERVAL_NS + GAP_TOLERANCE_NS
    gap_positions = diffs.index[gap_mask].tolist()
    gap_details = [
        {
            "after_ts_utc": pd.Timestamp(int(series.loc[idx - 1]), unit="ns", tz="UTC").isoformat(),
            "before_ts_utc": pd.Timestamp(int(series.loc[idx]), unit="ns", tz="UTC").isoformat(),
            "gap_minutes": round(float(diffs.loc[idx]) / 60e9, 3),
        }
        for idx in gap_positions
    ]
    first = pd.Timestamp(int(series.iloc[0]), unit="ns", tz="UTC")
    last = pd.Timestamp(int(series.iloc[-1]), unit="ns", tz="UTC")
    return {
        "bar_count": int(len(series)),
        "first_ts_utc": first.isoformat(),
        "last_ts_utc": last.isoformat(),
        "duplicate_timestamps": int(series.duplicated().sum()),
        "gaps_over_interval": int(gap_mask.sum()),
        "gap_details": gap_details,
    }


def instrument_metadata_present(catalog_path: str | Path, instrument_id: str) -> bool:
    inst_dir = Path(catalog_path) / "data" / "crypto_perpetual" / instrument_id
    return inst_dir.is_dir() and any(inst_dir.glob("*.parquet"))


def funding_stats(
    funding_dir: str | Path,
    symbol: str,
    declared_start: pd.Timestamp,
    declared_end: pd.Timestamp,
) -> dict[str, object]:
    """Funding-bundle coverage for one symbol vs its requested range and the
    declared window."""
    path = Path(funding_dir) / symbol / "funding.json"
    if not path.exists():
        return {
            "bundle_present": False,
            "requested_days": None,
            "days_covered": None,
            "coverage_ratio": None,
            "covers_declared_window": False,
        }
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    requested_start_ms = int(payload["requested_start_ms"])
    requested_end_ms = int(payload["requested_end_ms"])
    rows = payload.get("rows", [])
    row_times = [int(row["fundingTime"]) for row in rows]
    requested_days = (requested_end_ms - requested_start_ms) / 86_400_000
    days_covered = (
        (max(row_times) - min(row_times)) / 86_400_000 if row_times else 0.0
    )
    first_row = pd.Timestamp(min(row_times), unit="ms", tz="UTC") if row_times else None
    last_row = pd.Timestamp(max(row_times), unit="ms", tz="UTC") if row_times else None
    covers_window = bool(
        first_row is not None
        and last_row is not None
        and first_row <= declared_start
        and last_row >= declared_end
    )
    return {
        "bundle_present": True,
        "requested_start_utc": pd.Timestamp(requested_start_ms, unit="ms", tz="UTC").isoformat(),
        "requested_end_utc": pd.Timestamp(requested_end_ms, unit="ms", tz="UTC").isoformat(),
        "requested_days": round(requested_days, 2),
        "days_covered": round(days_covered, 2),
        "row_count": len(rows),
        "first_settlement_utc": first_row.isoformat() if first_row is not None else None,
        "last_settlement_utc": last_row.isoformat() if last_row is not None else None,
        "coverage_ratio": round(days_covered / requested_days, 4) if requested_days > 0 else None,
        "covers_declared_window": covers_window,
    }


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #
def classify_symbol(
    stats: dict[str, object],
    instrument_ok: bool,
    funding: dict[str, object],
    declared_start: pd.Timestamp,
    declared_end: pd.Timestamp,
) -> tuple[CellStatus, list[str]]:
    """Map coverage facts onto CellStatus + contract reason codes."""
    reasons: list[str] = []
    if int(stats.get("duplicate_timestamps", 0)) > 0:
        reasons.append("duplicate_bars")
    if int(stats.get("gaps_over_interval", 0)) > 0:
        reasons.append("unexplained_gap")
    if not funding.get("bundle_present", False) or not funding.get(
        "covers_declared_window", False
    ):
        reasons.append("funding_coverage_insufficient")
    if not instrument_ok:
        reasons.append("missing_instrument_metadata")
    first = stats.get("first_ts_utc")
    last = stats.get("last_ts_utc")
    if not first or not last or int(stats.get("bar_count", 0)) == 0:
        reasons.append("coverage_below_declared")
    else:
        if (
            pd.Timestamp(first) > declared_start + pd.Timedelta(minutes=BAR_INTERVAL_MINUTES)
            or pd.Timestamp(last) < declared_end - pd.Timedelta(minutes=BAR_INTERVAL_MINUTES)
        ):
            reasons.append("coverage_below_declared")
    if reasons:
        return CellStatus.DATA_INCOMPLETE, reasons
    return CellStatus.COMPLETED, []


def load_universe_symbols(config_path: str | Path) -> list[str]:
    with Path(config_path).open(encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    symbols = raw.get("market", {}).get("symbols") or []
    if not symbols:
        raise ValueError(f"No market.symbols in {config_path}")
    return [str(symbol) for symbol in symbols]


def build_coverage(
    *,
    universe_config: str | Path,
    catalog_path: str | Path,
    funding_dir: str | Path,
    declared_start: pd.Timestamp,
    declared_end: pd.Timestamp,
    symbols: list[str] | None = None,
) -> dict[str, object]:
    """Assemble the full coverage document (pure function, no I/O side effects
    beyond reading data dirs)."""
    if symbols is None:
        symbols = load_universe_symbols(universe_config)

    per_symbol: dict[str, object] = {}
    starts: list[pd.Timestamp] = []
    ends: list[pd.Timestamp] = []
    eligible: list[str] = []
    incomplete: dict[str, list[str]] = {}

    for symbol in symbols:
        instrument_id = f"{symbol}-PERP.BINANCE"
        stats = bar_stats(read_bar_timestamps(catalog_path, instrument_id))
        instrument_ok = instrument_metadata_present(catalog_path, instrument_id)
        funding = funding_stats(funding_dir, symbol, declared_start, declared_end)
        status, reasons = classify_symbol(
            stats, instrument_ok, funding, declared_start, declared_end
        )
        entry = {
            "instrument_id": instrument_id,
            "bars": stats,
            "instrument_metadata_present": instrument_ok,
            "funding": funding,
            "status": status.value,
            "reason_codes": reasons,
        }
        per_symbol[symbol] = entry
        if stats["bar_count"]:
            starts.append(pd.Timestamp(str(stats["first_ts_utc"])))
            ends.append(pd.Timestamp(str(stats["last_ts_utc"])))
        if reasons:
            incomplete[symbol] = reasons
        else:
            eligible.append(symbol)

    def intersection(names: list[str]) -> dict[str, object]:
        members = {
            name: per_symbol[name]
            for name in names
            if int(per_symbol[name]["bars"]["bar_count"]) > 0  # type: ignore[index]
        }
        if not members:
            return {"symbols": names, "start_utc": None, "end_utc": None}
        common_start = max(pd.Timestamp(str(entry["bars"]["first_ts_utc"])) for entry in members.values())  # type: ignore[index]
        common_end = min(pd.Timestamp(str(entry["bars"]["last_ts_utc"])) for entry in members.values())  # type: ignore[index]
        bars = min(int(entry["bars"]["bar_count"]) for entry in members.values())  # type: ignore[index]
        covers_declared = bool(
            common_start <= declared_start and common_end >= declared_end
        )
        return {
            "symbols": list(members),
            "symbol_count": len(members),
            "start_utc": common_start.isoformat(),
            "end_utc": common_end.isoformat(),
            "min_per_symbol_bars": bars,
            "covers_declared_window": covers_declared,
            "declared_window_respected": (
                max(common_start, declared_start).isoformat(),
                min(common_end, declared_end).isoformat(),
            ),
        }

    s0_names = [name for name in S0_SYMBOLS if name in set(symbols)]
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "universe_config": str(universe_config),
        "catalog_path": str(catalog_path),
        "funding_dir": str(funding_dir),
        "bar_interval_minutes": BAR_INTERVAL_MINUTES,
        "declared_window": {
            "start_utc": declared_start.isoformat(),
            "end_utc": declared_end.isoformat(),
            "source": "contracts/README.md S0 (1 year)",
        },
        "symbols": per_symbol,
        "intersections": {
            "all_universe": intersection(symbols),
            "s0_seven": intersection(s0_names),
        },
        "summary": {
            "declared_symbols": len(symbols),
            "eligible_count": len(eligible),
            "eligible_symbols": eligible,
            "incomplete_symbols": incomplete,
            "all_current": not incomplete,
        },
    }


# --------------------------------------------------------------------------- #
# Environment reporting
# --------------------------------------------------------------------------- #
def cpu_count_via_sysctl() -> str:
    try:
        out = subprocess.run(
            ["sysctl", "-n", "hw.ncpu"], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip()
    except Exception:  # noqa: BLE001 - env info must never fail the audit
        return str(__import__("os").cpu_count())


def disk_free_human() -> str:
    try:
        out = subprocess.run(
            ["df", "-h", "."], capture_output=True, text=True, timeout=10
        )
        return out.stdout.strip().splitlines()[-1]
    except Exception:  # noqa: BLE001
        return "df unavailable"


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Universe/catalog/funding coverage audit -> coverage.json",
    )
    parser.add_argument(
        "--matrix-id",
        default=f"{DEFAULT_MATRIX_ID}_{datetime.now(timezone.utc):%Y%m%d}",
        help="results/matrix/<matrix_id>/ target directory",
    )
    parser.add_argument("--universe-config", default=DEFAULT_UNIVERSE_CONFIG)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--funding-dir", default=DEFAULT_FUNDING_DIR)
    parser.add_argument("--declared-start", default=DECLARED_S0_START)
    parser.add_argument("--declared-end", default=DECLARED_S0_END)
    parser.add_argument(
        "--output-root",
        default="results/matrix",
        help="root directory for matrix artifacts",
    )
    args = parser.parse_args(argv)

    declared_start = pd.Timestamp(args.declared_start)
    declared_end = pd.Timestamp(args.declared_end)
    if declared_start.tzinfo is None:
        declared_start = declared_start.tz_localize("UTC")
    if declared_end.tzinfo is None:
        declared_end = declared_end.tz_localize("UTC")

    coverage = build_coverage(
        universe_config=args.universe_config,
        catalog_path=args.catalog,
        funding_dir=args.funding_dir,
        declared_start=declared_start,
        declared_end=declared_end,
    )

    out_dir = Path(args.output_root) / args.matrix_id
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "coverage.json"
    out_path.write_text(json.dumps(coverage, indent=2), encoding="utf-8")

    summary = coverage["summary"]
    intersections = coverage["intersections"]
    print("=" * 68)
    print(f"DATA COVERAGE AUDIT -> {out_path}")
    print("=" * 68)
    print(
        f"Universe: {summary['declared_symbols']} symbols "
        f"({args.universe_config}) | interval {BAR_INTERVAL_MINUTES}m"
    )
    print(f"Eligible: {summary['eligible_count']}/{summary['declared_symbols']}")
    for symbol, codes in summary["incomplete_symbols"].items():  # type: ignore[union-attr]
        print(f"  DATA_INCOMPLETE {symbol}: {', '.join(codes)}")
    for key in ("all_universe", "s0_seven"):
        bounds = intersections[key]
        print(
            f"{key}: {bounds.get('symbol_count', '?')} symbols "
            f"{bounds.get('start_utc')} .. {bounds.get('end_utc')} "
            f"(covers declared S0: {bounds.get('covers_declared_window')})"
        )
    ncpu = cpu_count_via_sysctl()
    disk = disk_free_human()
    print(f"CPU cores (hw.ncpu): {ncpu}")
    print(f"Disk: {disk}")
    print(f"Environment: python {sys.version.split()[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
