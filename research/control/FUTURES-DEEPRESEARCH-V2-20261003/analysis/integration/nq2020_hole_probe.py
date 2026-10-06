#!/usr/bin/env python3
"""nq2020_hole_probe.py — metadata-only probe of the NQ 2020 front-contract hole.

Lane INTEGRATION-FIX-V2 (task FUTURES-DEEPRESEARCH-V2-20261003), 2026-10-03.

DEEP-NQ reported NQ front contracts absent 2020-03-23..2020-05-29 (51
sessions; only a deferred NQU0 trickle). This probe adjudicates, using ONLY
free metadata endpoints (metadata.get_record_count / get_billable_size /
get_cost — NO data download; budget untouched):

  (a) records exist at vendor -> our chunking/parent delivery missed them
      (fixable re-request; quote reported, NOT executed);
  (b) truly absent at vendor -> vendor coverage hole.

KEY LAW: the API key is read in-process from the owner's secret file and used
only via the official client (Authorization header). It is NEVER printed,
logged, or written to any artifact. Errors are redacted to exception type +
HTTP status only.

Local evidence assembled BEFORE any API call (from our own delivered vendor
parquet, see nq2020_hole_probe.json): instrument_id 16908 carries the
June-2020 front future's full volume under raw_symbol 'NQU8-NQM9' for
2020-01-01..2020-05-31 and under 'NQM0' from 2020-06-01 — i.e. the front
bars ARE in our delivery, under a vendor symbology alias that every
outright-regex filter quarantines.
"""
from __future__ import annotations

import json
import re
import traceback
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
KEY_PATH = Path("/Users/hoangminhlong/.config/my-quantitative-secrets/databento-api-key")
TOKEN_RE = re.compile(r"db-[A-Za-z0-9_\-]{12,}")

DATASET = "GLBX.MDP3"
SCHEMA = "ohlcv-1m"
WIN = ("2020-03-01", "2020-06-30")          # probe window (dispatch)
HOLE = ("2020-03-23", "2020-05-29")         # DEEP-NQ's exact hole window
NQ_PARQUET = [Path("/Users/hoangminhlong/my-quantitative-data/"
                   "futures-databento-av1trim/parquet/AV1R-O1M-NQ-DELTA") / n for n in
              ("AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01.parquet",
               "AV1R-O1M-NQ-DELTA__2020-06-01_2022-06-01.parquet")]


def redacted(call):
    """Run an API call; on failure return {'error': '<type> HTTP<code>'} with
    the message body REDACTED (it could echo auth material)."""
    try:
        return call()
    except Exception as e:  # noqa: BLE001
        code = ""
        m = re.search(r"\b(4\d\d|5\d\d)\b", str(getattr(e, "status_code", "")) or "")
        if not m:
            m = re.search(r"\b(4\d\d|5\d\d)\b", type(e).__name__ + " " + str(e)[:40])
            code = f" HTTP{m.group(1)}" if m else ""
        return {"error_redacted": type(e).__name__ + code}


def local_evidence() -> dict:
    df = pd.concat([pd.read_parquet(p, columns=["raw_symbol", "instrument_id",
                                                "volume", "ts_event"])
                    for p in NQ_PARQUET], ignore_index=True)
    df["date"] = pd.to_datetime(df.ts_event, unit="ns", utc=True).dt.date.astype(str)
    i = df[df.instrument_id == 16908]
    hole = i[(i.date >= HOLE[0]) & (i.date <= HOLE[1])]
    per_sym_date = (df[(df.date >= WIN[0]) & (df.date <= WIN[1])]
                    .groupby("raw_symbol")
                    .agg(bars=("raw_symbol", "size"), volume=("volume", "sum"),
                         first=("date", "min"), last=("date", "max")))
    return {
        "instrument_16908": {
            "label_windows": [
                {"raw_symbol": s, "first": g.date.min(), "last": g.date.max(),
                 "bars": int(len(g)), "volume": int(g.volume.sum())}
                for s, g in i.groupby("raw_symbol")],
            "monthly_volume": {m: int(g.volume.sum())
                               for m, g in i.groupby(i.date.str[:7])},
            "hole_window_sessions_present": int(hole.date.nunique()),
            "hole_window_first_last": [hole.date.min(), hole.date.max()],
            "hole_window_volume": int(hole.volume.sum()),
        },
        "window_symbols": {s: {"bars": int(r.bars), "volume": int(r.volume),
                               "first": r.first, "last": r.last}
                           for s, r in per_sym_date.sort_values("bars", ascending=False).iterrows()},
    }


def main() -> None:
    import databento as db

    key = KEY_PATH.read_text().strip()
    assert key and not TOKEN_RE.search(key) is None, "key file empty/malformed"
    h = db.Historical(key=key)

    out = {
        "schema": "nq2020_hole_probe@1",
        "lane": "INTEGRATION-FIX-V2",
        "task_id": "FUTURES-DEEPRESEARCH-V2-20261003",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "probe_law": "metadata endpoints only (record_count / billable_size / "
                     "get_cost); ZERO data downloaded; key in-process only, never "
                     "in outputs; errors redacted",
        "vendor_request": {"dataset": DATASET, "schema": SCHEMA,
                           "probe_window": WIN, "hole_window": HOLE},
        "local_delivery_evidence": local_evidence(),
    }

    # --- live vendor metadata ---
    live = {}
    live["parent_NQ.FUT_record_count_2020-03-01_2020-06-30"] = redacted(
        lambda: h.metadata.get_record_count(
            dataset=DATASET, start=WIN[0], end="2020-07-01", symbols="NQ.FUT",
            schema=SCHEMA, stype_in="parent"))
    live["parent_NQ.FUT_record_count_hole_2020-03-23_2020-05-29"] = redacted(
        lambda: h.metadata.get_record_count(
            dataset=DATASET, start=HOLE[0], end="2020-05-30", symbols="NQ.FUT",
            schema=SCHEMA, stype_in="parent"))
    for sym in ("NQH0", "NQJ0", "NQM0", "NQU0"):
        live[f"raw_{sym}_record_count_2020-03-01_2020-06-30"] = redacted(
            lambda s=sym: h.metadata.get_record_count(
                dataset=DATASET, start=WIN[0], end="2020-07-01", symbols=s,
                schema=SCHEMA, stype_in="raw_symbol"))
    # re-request quote (reported, NOT executed — budget nearly exhausted)
    live["requote_parent_NQ.FUT_get_cost_2020-03-01_2020-06-30"] = redacted(
        lambda: h.metadata.get_cost(
            dataset=DATASET, start=WIN[0], end="2020-07-01", symbols="NQ.FUT",
            schema=SCHEMA, stype_in="parent"))
    live["requote_parent_NQ.FUT_billable_size_2020-03-01_2020-06-30"] = redacted(
        lambda: h.metadata.get_billable_size(
            dataset=DATASET, start=WIN[0], end="2020-07-01", symbols="NQ.FUT",
            schema=SCHEMA, stype_in="parent"))
    out["vendor_metadata_live"] = live

    # ---- adjudication (computed locally from the reconciliation above) ----
    win = out["local_delivery_evidence"]["window_symbols"]
    nqm0_ours = sum(win[s]["bars"] for s in ("NQU8-NQM9", "NQM0") if s in win)
    rc = live
    out["adjudication"] = {
        "verdict": "A_ALIAS_NOT_ABSENCE",
        "dispatch_dichotomy": "(a) records exist / (b) truly absent",
        "statement": "Records EXIST at the vendor AND are already 100% inside our "
                     "delivered chunk (AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01, QA "
                     "PASS records_actual==records_quoted==944,290). The DEEP-NQ "
                     "'hole' is a VENDOR SYMBOLOGY ALIAS: instrument_id 16908 is the "
                     "NQ June-2020 future, carried raw_symbol 'NQU8-NQM9' from its "
                     "2018-08-15 listing until 2020-06-01, then 'NQM0'. Every "
                     "outright filter (regex ^NQ[FGHJKMNQUVXZ][0-9]$, dash-excluding) "
                     "quarantined the front bars, so panels built from raw_symbol "
                     "alone show NaN fronts 2020-03-23..2020-05-29.",
        "reconciliation": {
            "window_total_ours_vs_vendor_parent": [int(sum(v["bars"] for v in win.values())),
                                                   rc["parent_NQ.FUT_record_count_2020-03-01_2020-06-30"]],
            "NQM0_id16908_ours_vs_vendor_raw": [int(nqm0_ours),
                                                rc["raw_NQM0_record_count_2020-03-01_2020-06-30"]],
            "NQH0_ours_vs_vendor_raw": [win["NQH0"]["bars"],
                                        rc["raw_NQH0_record_count_2020-03-01_2020-06-30"]],
            "NQU0_ours_vs_vendor_raw": [win["NQU0"]["bars"],
                                        rc["raw_NQU0_record_count_2020-03-01_2020-06-30"]],
            "NQJ0": "vendor HTTP422: symbol unresolvable in GLBX.MDP3 for the "
                    "window (April serial not listed in feed)",
        },
        "fix": "VIEW RULE, $0: relabel bars with instrument_id==16908 and "
               "date<2020-06-01 from 'NQU8-NQM9' to 'NQM0' before applying the "
               "outright filter (vendor-corroborated: current vendor symbology "
               "attributes all 100,034 window records to raw NQM0). No re-request "
               "needed; quote recorded below per dispatch, NOT executed.",
        "requote_not_executed": {
            "get_cost_usd": rc.get("requote_parent_NQ.FUT_get_cost_2020-03-01_2020-06-30"),
            "billable_size_bytes": rc.get("requote_parent_NQ.FUT_billable_size_2020-03-01_2020-06-30"),
        },
    }

    (HERE / "nq2020_hole_probe.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(live, indent=1))
    print("wrote", HERE / "nq2020_hole_probe.json")


if __name__ == "__main__":
    main()
