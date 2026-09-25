"""basis_convert.py -- staged basis JSON -> the FROZEN restage parquet schema.

Cycle CRYPTO-HISTORICAL-REPLICATION-3F-V1, namespace basislv_replication.

Input : ``staging/basis_win/<SYM>_basis_15m.json`` (rows carry the endpoint's
        own fields: timestamp (open, ms), futuresPrice, indexPrice, basis,
        basisRate -- strings as served by /futures/data/basis; full-depth
        B window 2020-06/07 or listing date .. 2024-08-19, 19/19 symbols).
Output: ``basislv_replication/basis_parquet/<SYM>/<SYM>_basis_15m.parquet``
        with EXACTLY the frozen ``restage_basis.py`` schema (columns
        ``open_time_ms`` int64 + ``futures_price`` / ``index_price`` /
        ``basis`` / ``basis_rate`` float64, written via pandas ``to_parquet``
        ``index=False``), so the frozen loader value path
        (``basislv_replication.replication_data.load_basis_world``) reads it
        unchanged.

Checks (fail-closed unless marked REPORTED):
* every row parses: timestamp int on the 15m grid, four numeric fields
  finite-float  (fail-closed);
* duplicate open stamps refused (fail-closed -- same as the frozen
  ``basis_series_from_rows``);
* the frozen basis-route identity check on ADMISSIBLE rows
  (finite futuresPrice/indexPrice, both > 0):
  ``|(futures - index)/index - basisRate| <= BASIS_IDENTITY_TOL_ABS (1e-4,
  absolute; the endpoint's own basisRate is rounded to 4 decimal places)``
  -- max deviation recorded per symbol, breach fails closed;
* nonpositive/non-finite price-level rows are NOT dropped: they are written
  through and become NaN premium slots at load (the engine's per-slot
  fail-closed availability semantics then refuse any formation window that
  straddles them).  Counts REPORTED per symbol;
* grid gaps (missing 15m opens inside [first, last]) are REPORTED, not
  fatal: unlike the A9-F restage (whose loader refuses any gap), this
  4.6-year re-fetch carries a single systematic missing bucket
  (open 1699587900000 = 2023-11-10T04:05:00Z, 15/19 symbols -- an endpoint
  outage artifact).  The disclosed policy: write what was fetched, record
  every gap, let the engine's own eligibility refuse the affected formation
  windows.  Measured effect (dry-run 2026-09-25): the 4 decision stamps
  2023-11-13..2023-12-04 in Y2023 lose the gapped names.

No PnL, no scored metric.  Writes ONLY inside this namespace.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
CD = HERE.parent
STAGED_ROOT = CD / "staging/basis_win"
OUT_ROOT = HERE / "basis_parquet"

BUCKET_MS = 900_000  # one 15m basis bucket (open-stamped rows)
BASIS_IDENTITY_TOL_ABS = 1e-4  # frozen strategy.py constant (same absolute band)

COLUMNS = ("open_time_ms", "futures_price", "index_price", "basis", "basis_rate")


def _iso_ms(ms: int) -> str:
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def convert_symbol(sym: str) -> dict:
    path = STAGED_ROOT / f"{sym}_basis_15m.json"
    if not path.is_file():
        raise FileNotFoundError(f"staged basis JSON missing: {path}")
    body = json.loads(path.read_text(encoding="utf-8"))
    rows = body.get("rows", [])
    if not rows:
        raise ValueError(f"{sym}: staged basis JSON carries no rows")

    pair = str(body.get("pair", sym))
    records: list[dict] = []
    seen: set[int] = set()
    off_grid: list[int] = []
    inadmissible = 0
    max_identity_dev = 0.0
    identity_rows = 0
    for row in rows:
        try:
            open_ms = int(row["timestamp"])
            fut = float(row["futuresPrice"])
            idx = float(row["indexPrice"])
            bas = float(row["basis"])
            rate = float(row["basisRate"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{sym}: unparseable basis row {row!r}: {exc}") from exc
        if open_ms % BUCKET_MS != 0:
            off_grid.append(open_ms)
        if open_ms in seen:
            raise ValueError(f"{sym}: duplicate basis open {open_ms}")
        seen.add(open_ms)
        admissible = (
            math.isfinite(fut)
            and math.isfinite(idx)
            and fut > 0.0
            and idx > 0.0
        )
        if not (math.isfinite(fut) and math.isfinite(idx) and math.isfinite(bas) and math.isfinite(rate)):
            raise ValueError(
                f"{sym}: non-finite price-level field at open {open_ms} (fail-closed)"
            )
        if admissible:
            computed = (fut - idx) / idx
            dev = abs(computed - rate)
            max_identity_dev = max(max_identity_dev, dev)
            identity_rows += 1
        else:
            inadmissible += 1
        records.append(
            {
                "open_time_ms": open_ms,
                "futures_price": fut,
                "index_price": idx,
                "basis": bas,
                "basis_rate": rate,
            }
        )
    if off_grid:
        raise ValueError(
            f"{sym}: {len(off_grid)} opens off the 15m grid (fail-closed); first "
            f"{off_grid[0]}"
        )
    if max_identity_dev > BASIS_IDENTITY_TOL_ABS:
        raise ValueError(
            f"{sym}: basis-route identity check violated: max |p_b - basisRate| "
            f"= {max_identity_dev} > {BASIS_IDENTITY_TOL_ABS} (fail-closed)"
        )

    records.sort(key=lambda r: r["open_time_ms"])
    first_open = records[0]["open_time_ms"]
    last_open = records[-1]["open_time_ms"]
    expected_span = (last_open - first_open) // BUCKET_MS + 1
    missing = [
        ms
        for ms in range(first_open, last_open + BUCKET_MS, BUCKET_MS)
        if ms not in seen
    ]

    out_dir = OUT_ROOT / sym
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{sym}_basis_15m.parquet"
    import pandas as pd

    pd.DataFrame(records, columns=COLUMNS).to_parquet(out_path, index=False)

    return {
        "symbol": sym,
        "pair_field": pair,
        "requested_window_ms": list(body.get("window", [])),
        "rows": len(records),
        "first_open_ms": first_open,
        "last_open_ms": last_open,
        "first_open_iso": _iso_ms(first_open),
        "last_open_iso": _iso_ms(last_open),
        "expected_slots_in_span": int(expected_span),
        "grid_gaps": len(missing),
        "grid_gap_opens": list(missing),
        "inadmissible_price_rows": inadmissible,
        "identity_rows_checked": identity_rows,
        "max_abs_identity_deviation": max_identity_dev,
        "identity_tol_abs": BASIS_IDENTITY_TOL_ABS,
        "out_path": str(out_path),
    }


def main() -> int:
    syms = sorted(
        p.name[: -len("_basis_15m.json")]
        for p in STAGED_ROOT.glob("*_basis_15m.json")
    )
    if not syms:
        print(f"NO staged basis JSONs under {STAGED_ROOT}", file=sys.stderr)
        return 2
    entries = []
    for sym in syms:
        entry = convert_symbol(sym)
        entries.append(entry)
        print(
            f"[convert] {sym}: rows={entry['rows']} "
            f"{entry['first_open_iso']}..{entry['last_open_iso']} "
            f"gaps={entry['grid_gaps']} inadmissible={entry['inadmissible_price_rows']} "
            f"max_dev={entry['max_abs_identity_deviation']:.2e}",
            flush=True,
        )
    report = {
        "schema": "basislv_replication.basis_convert_report.v1",
        "measured_utc": datetime.now(timezone.utc).isoformat(),
        "staged_root": str(STAGED_ROOT),
        "out_root": str(OUT_ROOT),
        "parquet_schema": list(COLUMNS),
        "schema_authority": (
            "recovered/v14_root research/v14/families/basislv_premfade/"
            "restage_basis.py stage_symbol_basis (pandas to_parquet, index=False)"
        ),
        "grid_gap_policy": (
            "REPORTED not fatal: the 4.6-year re-fetch carries a single "
            "systematic missing bucket (open 1699587900000 = 2023-11-10T04:05Z, "
            "15/19 symbols); the engine's per-slot NaN semantics refuse any "
            "formation window straddling a gap (fail closed at signal level)"
        ),
        "identity_check": (
            "|(futures-index)/index - basisRate| <= 1e-4 ABSOLUTE on admissible "
            "rows, fail-closed (frozen BASIS_IDENTITY_TOL_ABS)"
        ),
        "entries": entries,
        "n_symbols": len(entries),
    }
    (HERE / "basis_convert_report.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"[convert] {len(entries)} symbols -> {OUT_ROOT}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
