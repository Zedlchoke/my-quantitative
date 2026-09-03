"""A9-F scratch: PIT field availability + warmup feasibility inventory.

Loader-selected values only. Reads bars/funding/OI/metadata from the
gitignored workspace roots; emits a JSON inventory to the scratch dir.
Schedule/data verification only -- no returns, no PnL.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pyarrow.parquet as pq

sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/d2-a9f-feasibility")

from research.v12.data_contract import (  # noqa: E402
    BAR_INTERVAL_NS,
    REQUIRED_SYMBOLS,
    S0_SNAPSHOT_WINDOW_START_ISO,
    S0_SNAPSHOT_WINDOW_END_ISO,
    bar_parquet_paths,
    inventory_oi_symbol,
    inventory_funding,
    load_bar_close_ns,
    ns_to_iso_utc,
    parse_iso_utc_ns,
    read_instrument_metadata,
    snap_bar_closes_to_slots,
    warmup_report,
    FUNDING_BUNDLES,
    OI_CONSOLIDATED_ROOT,
    PERP_ROOT,
    BARS_ROOT,
)

OUT = "/Users/hoangminhlong/my-quantitative/.worktrees/crypto/v12/d2-a9f-feasibility/research/audits/v12d/a9f_scratch/a9f_inventory.json"

W0 = parse_iso_utc_ns(S0_SNAPSHOT_WINDOW_START_ISO)
W1 = parse_iso_utc_ns(S0_SNAPSHOT_WINDOW_END_ISO)


def decode_close(raw: bytes, precision: int) -> float:
    return int.from_bytes(raw, "little") / (10 ** precision)


def main() -> None:
    inv: dict = {"schema": "a9f_inventory_v1", "symbols": {}}

    for sym in REQUIRED_SYMBOLS:
        rec: dict = {"symbol": sym}

        # ---------- bars ----------
        paths = bar_parquet_paths(BARS_ROOT, sym)
        rec["bars_files"] = len(paths)
        if paths:
            close_ns = load_bar_close_ns(paths)
            snapped, snap_info = snap_bar_closes_to_slots(close_ns, BAR_INTERVAL_NS)
            closes = sorted(set(snapped))
            arr = np.array(closes, dtype=np.int64)
            rec["bars_first_close_iso"] = ns_to_iso_utc(int(arr[0]))
            rec["bars_last_close_iso"] = ns_to_iso_utc(int(arr[-1]))
            rec["bars_rows"] = int(len(closes))
            rec["snap"] = snap_info
            # S0 window slot coverage
            expected = np.arange(W0 + BAR_INTERVAL_NS, W1 + 1, BAR_INTERVAL_NS, dtype=np.int64)
            present_mask = np.isin(expected, arr)
            rec["s0_expected_slots"] = int(len(expected))
            rec["s0_missing_slots"] = int((~present_mask).sum())
            # pre-window 90d warmup block coverage [W0-90d, W0]
            pre_start = W0 - 90 * 86_400 * 10**9
            pre_expected = np.arange(pre_start + BAR_INTERVAL_NS, W0 + 1, BAR_INTERVAL_NS, dtype=np.int64)
            pre_present = np.isin(pre_expected, arr)
            rec["pre90d_expected_slots"] = int(len(pre_expected))
            rec["pre90d_missing_slots"] = int((~pre_present).sum())
            # contract warmup_report (28/56/90)
            rec["warmup"] = warmup_report(closes, (28, 56, 90), window_start_ns=W0)
            # columns present in first file (loader-selected sample)
            t = pq.read_table(paths[0])
            rec["bar_columns"] = sorted(t.schema.names)
            rec["has_quote_volume"] = "quote_volume" in t.schema.names
            rec["has_trade_count"] = "count" in t.schema.names
            meta = {k.decode(): v.decode() for k, v in (t.schema.metadata or {}).items()}
            rec["price_precision"] = int(meta.get("price_precision", "-1"))
        else:
            rec["present"] = False

        # ---------- funding (scan_2026 primary) ----------
        rec["funding"] = inventory_funding(FUNDING_BUNDLES, sym, window_start_ns=W0, window_end_ns=W1)
        # field-level check on the primary bundle file
        fpath = os.path.join(FUNDING_BUNDLES[0][1], sym, "funding.json")
        if os.path.exists(fpath):
            payload = json.load(open(fpath))
            rows = payload.get("rows", [])
            keys = sorted({k for r in rows[:5] for k in r})
            rates = [float(r["fundingRate"]) for r in rows[:50] if r.get("fundingRate") not in (None, "")]
            rec["funding_fields"] = keys
            rec["funding_has_rate_field"] = "fundingRate" in keys
            rec["funding_rate_sample_nonzero_frac"] = (
                round(sum(1 for x in rates if x != 0.0) / len(rates), 4) if rates else None
            )

        # ---------- OI ----------
        oi_path = os.path.join(OI_CONSOLIDATED_ROOT, f"{sym}_oi.parquet")
        rec["oi_file_exists"] = os.path.exists(oi_path)
        if rec["oi_file_exists"]:
            tbl = pq.read_table(oi_path)
            rec["oi_columns"] = sorted(tbl.schema.names)[:12]

        # ---------- instrument metadata ----------
        rec["instrument"] = read_instrument_metadata(PERP_ROOT, sym)

        inv["symbols"][sym] = rec
        print(f"done {sym}", flush=True)

    with open(OUT, "w") as fh:
        json.dump(inv, fh, indent=1, sort_keys=True, default=str)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
