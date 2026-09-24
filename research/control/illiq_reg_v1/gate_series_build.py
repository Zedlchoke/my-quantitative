"""ILLIQ-REG-V1 gate-series build (gate-sequence step 3; HEAVY: run under the
global heavy lock via researchctl, see handbook SS8).

Modes:
  --check-coverage-only   bootstrap-safe: verifies per-fold funding scan
                          coverage (small JSONs) and catalog presence; writes
                          coverage_status.json. No parquet scan, no lock.
  default (full build)    reads the READ-ONLY CHR3F catalogs (parquet), builds
                          the daily PIT DV-share / BTC closes, computes the
                          frozen gate walk + 200 random-gate controls, writes
                          gate_series.json + digests. NOT RUN at bootstrap.

Reads ONLY wiring.FOLD_WIRING absolute paths; never writes outside the
research/control/illiq_reg_v1/ namespace; never modifies CHR3F files.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gate_module as gm  # noqa: E402
import wiring  # noqa: E402

ALL_SYMS = wiring.SYMS
GATE_FOLDS = ("Y2021", "Y2024P", "S0R", "FWD")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_coverage() -> dict:
    """Bootstrap-safe wiring proof: scans exist, catalogs exist, per-fold
    funding coverage > 0 for all 20 symbols. Fail-closed on any violation."""
    status = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "folds": {}}
    for fold in GATE_FOLDS:
        w = wiring.FOLD_WIRING[fold]
        w0, w1 = wiring.FOLD_WINDOWS[fold]
        entry = {"funding_scan": w["funding_scan"].name,
                 "window": [w0, w1],
                 "catalog": str(w["catalog"]) if w["catalog"] else None}
        if w["catalog"] is not None and not Path(w["catalog"]).exists():
            raise wiring.WiringError(f"{fold}: catalog missing: {w['catalog']}")
        # Coverage law (wiring.py): S0R/FWD require the FULL 20-symbol list;
        # pre-window folds require only the in-window PIT-listed subset
        # (not-yet-listed names legitimately have zero rows).
        if fold in ("S0R", "FWD"):
            required = ALL_SYMS
        else:
            required = sorted(wiring.listed_symbols_proxy(
                w["funding_scan"], w1))
        counts = wiring.verify_funding_scan_coverage(
            w["funding_scan"], required, w0, w1)
        entry["required_symbols"] = len(required)
        entry["funding_rows"] = counts
        entry["funding_rows_total"] = sum(counts.values())
        status["folds"][fold] = entry
    return status


# --- full build (NOT_RUN at bootstrap; heavy lock required) --------------------

def daily_dv_from_catalog(catalog: Path, sym: str, day_lo: dt.date,
                          day_hi: dt.date) -> dict:
    """DV per completed daily block from the staged 15m parquet bars."""
    import pyarrow.parquet as pq
    directory = catalog / "data" / "binance_bar" / \
        f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(glob.glob(str(directory / "*.parquet")))
    if not files:
        raise wiring.WiringError(f"no parquet bars for {sym} in {catalog}")
    per: dict[dt.date, float] = {}
    for fp in files:
        t = pq.read_table(fp, columns=["ts_event", "quote_volume"])
        ts = t.column("ts_event").to_pylist()
        qv = t.column("quote_volume").to_pylist()
        for i in range(len(ts)):
            day = dt.datetime.fromtimestamp(int(ts[i]) / 1e9,
                                            dt.timezone.utc).date()
            if day_lo <= day < day_hi:
                per[day] = per.get(day, 0.0) + float(qv[i])
    return per


def daily_closes_from_catalog(catalog: Path, sym: str, day_lo: dt.date,
                              day_hi: dt.date) -> dict:
    import pyarrow.parquet as pq
    directory = catalog / "data" / "binance_bar" / \
        f"{sym}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(glob.glob(str(directory / "*.parquet")))
    per: dict[dt.date, float] = {}
    for fp in files:
        t = pq.read_table(fp, columns=["ts_event", "close"])
        ts = t.column("ts_event").to_pylist()
        cl = t.column("close").to_pylist()
        for i in range(len(ts)):
            day = dt.datetime.fromtimestamp(int(ts[i]) / 1e9,
                                            dt.timezone.utc).date()
            if not (day_lo <= day < day_hi):
                continue
            raw = cl[i]
            val = (int.from_bytes(raw, "little", signed=True) / 10 ** 16
                   if isinstance(raw, (bytes, bytearray)) else float(raw))
            per[day] = val  # last completed 15m bar of the day wins
    return per


def full_build(out_path: Path) -> dict:
    """Full gate series over GATE_FOLDS from the frozen catalogs.

    Requires the global heavy lock (researchctl); refuses without it.
    """
    lock = Path("/Users/hoangminhlong/.my-quantitative-governance/heavy_runtime/"
                "heavy_worker.lock")
    if lock.exists():
        raise wiring.WiringError(
            "heavy lock present: run the full build under researchctl "
            "lock discipline, not ad hoc (handbook SS8)")
    raise NotImplementedError(
        "full build is gate-sequence step 3, after M0+dry-run gates; "
        "implementation continues there with fold-stitched DV/closes and "
        "artifact digests. Bootstrap delivers wiring + M0 only.")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-coverage-only", action="store_true")
    ap.add_argument("--full-build", action="store_true")
    args = ap.parse_args()
    out = HERE / "coverage_status.json"
    if args.full_build:
        payload = full_build(out)
    else:
        payload = check_coverage()
        out.write_text(json.dumps(payload, indent=1, sort_keys=True))
    print(json.dumps({"written": str(out),
                      "digest": sha256_file(out),
                      "mode": "full" if args.full_build else "coverage"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
