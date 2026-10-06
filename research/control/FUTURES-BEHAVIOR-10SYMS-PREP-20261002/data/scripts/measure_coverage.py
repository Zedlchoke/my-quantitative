#!/usr/bin/env python
"""measure_coverage.py — DATA-PIT-ACQUISITION-PREP (FUTURES-BEHAVIOR-10SYMS-PREP-20261002)

Measures what we HAVE per symbol x data class from the legal IBKR raw corpus
(~/.my-quantitative-data/futures-10syms-v1/raw/, 1160 files, read-only) produced
by FUTURES-DATA-10SYMS-V1 (2026-10-02).

For every raw JSON file we parse the embedded metadata + bars and aggregate:
  - daily TRADES per contract (barSize="1 day", whatUse=TRADES)
  - daily BID / ASK (barSize="1 day", whatUse=BID/ASK)
  - hourly TRADES (barSize="1 hour")
  - minute TRADES  (barSize="1 min")
Bar-quality metrics per file: n_bars, n_v0 (volume==0), n_close_only
(O==H==L==C and v==0 -> settlement-derived), first/last bar date, first/last
date with v>0 ("real-volume window").

Per symbol we also build a month histogram of real-volume daily bars (any
contract of that symbol) to substantiate the front-month real-volume chain
depth claim (FUTURES-DATA-10SYMS-V1: ~2025-08 -> now).

Classes absent from this corpus (definitions, statistics, OI, explicit
settlement, deep M1/H1) are NOT invented here; they are marked absent.

Output: data/coverage_measured.json  (OBSERVED evidence, script+window recorded).

Usage:
  .venv/bin/python measure_coverage.py \
      --raw-dir ~/.my-quantitative-data/futures-10syms-v1/raw/ \
      --out <task>/data/coverage_measured.json
No network, no writes outside --out. Heavy lock not required (1160 small JSON
files, <40 MB total, seconds of CPU).
"""

import argparse
import collections
import datetime as dt
import json
import os
import sys

RAW_DIR_DEFAULT = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
SYMBOLS = ["NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"]

# data classes keyed by (whatUse, barSize) -> class name
CLASS_OF = {
    ("TRADES", "1 day"): "daily_trades_per_contract",
    ("BID", "1 day"): "daily_bid",
    ("ASK", "1 day"): "daily_ask",
    ("TRADES", "1 hour"): "hourly_trades",
    ("TRADES", "1 min"): "minute_trades",
}


def month_of(t: str) -> str:
    return t[:7]


def summarize_file(path: str) -> dict:
    with open(path) as fh:
        j = json.load(fh)
    bars = j.get("bars") or []
    n = len(bars)
    n_v0 = sum(1 for b in bars if (b.get("v") or 0) == 0)
    n_close_only = sum(
        1 for b in bars
        if (b.get("v") or 0) == 0
        and b.get("o") is not None
        and b.get("o") == b.get("h") == b.get("l") == b.get("c")
    )
    first_t = bars[0]["t"] if bars else None
    last_t = bars[-1]["t"] if bars else None
    first_rv = next((b["t"] for b in bars if (b.get("v") or 0) > 0), None)
    last_rv = next((b["t"] for b in reversed(bars) if (b.get("v") or 0) > 0), None)
    dur = j.get("durationStr") or ""
    role = "front_probe" if "_front_" in os.path.basename(path) else "per_contract"
    return {
        "file": os.path.basename(path),
        "bytes": os.path.getsize(path),
        "role": role,
        "symbol": j.get("symbol"),
        "localSymbol": j.get("localSymbol"),
        "conId": j.get("conId"),
        "exchange": j.get("exchange"),
        "whatUse": j.get("whatUse"),
        "barSize": j.get("barSize"),
        "durationStr": dur,
        "endDateTime": j.get("endDateTime"),
        "expiry_month_raw": j.get("expiry_month"),
        "timeZoneId": j.get("timeZoneId"),
        "ok": j.get("ok"),
        "n_bars": n,
        "n_v0": n_v0,
        "n_close_only": n_close_only,
        "first_bar": first_t,
        "last_bar": last_t,
        "first_real_volume": first_rv,
        "last_real_volume": last_rv,
        "fetched_utc": j.get("fetched_utc"),
    }


def dedupe_per_contract(pc: list) -> list:
    """Same contract can appear in >1 file (bulk 6Y/1Y fetch + short refresh /
    gap-fill fetch). Keep the file with the most bars per localSymbol; count the
    raw file multiplicity so nothing is hidden."""
    best = {}
    for f in pc:
        k = f["localSymbol"]
        if k not in best or f["n_bars"] > best[k]["n_bars"]:
            best[k] = f
    return [best[k] for k in sorted(best)]


def agg_class(files: list) -> dict:
    """Aggregate one (symbol, data class) bucket from per-file summaries."""
    pc_raw = [f for f in files if f["role"] == "per_contract"]
    fp = [f for f in files if f["role"] == "front_probe"]
    pc = dedupe_per_contract(pc_raw)
    contracts = sorted({f["localSymbol"] for f in pc})
    conids = sorted({f["conId"] for f in pc})
    dated = [f for f in pc if f["n_bars"] > 0]
    span = None
    if dated:
        first = min(f["first_bar"] for f in dated)
        last = max(f["last_bar"] for f in dated)
        span = [first[:10], last[:10]]
    out = {
        "per_contract_files": len(pc_raw),
        "per_contract_files_after_dedupe": len(pc),
        "front_probe_files": len(fp),
        "contracts": len(contracts),
        "contract_list": contracts,
        "distinct_conIds": len(conids),
        "bars_total": sum(f["n_bars"] for f in pc),
        "bars_v0": sum(f["n_v0"] for f in pc),
        "bars_close_only": sum(f["n_close_only"] for f in pc),
        "files_with_zero_bars": sum(1 for f in pc if f["n_bars"] == 0),
        "bytes_total": sum(f["bytes"] for f in pc),
        "bar_date_span": span,
        "per_contract": [
            {
                "localSymbol": f["localSymbol"],
                "conId": f["conId"],
                "expiry_month_raw": f["expiry_month_raw"],
                "durationStr": f["durationStr"],
                "endDateTime": f["endDateTime"],
                "n_bars": f["n_bars"],
                "n_v0": f["n_v0"],
                "n_close_only": f["n_close_only"],
                "first_bar": f["first_bar"],
                "last_bar": f["last_bar"],
                "first_real_volume": f["first_real_volume"],
                "last_real_volume": f["last_real_volume"],
            }
            for f in sorted(pc, key=lambda x: (x["localSymbol"] or ""))
        ],
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default=RAW_DIR_DEFAULT)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    files = []
    for name in sorted(os.listdir(args.raw_dir)):
        if not name.endswith(".json"):
            continue
        try:
            files.append(summarize_file(os.path.join(args.raw_dir, name)))
        except Exception as e:  # noqa: BLE001 - record, never crash the scan
            files.append({"file": name, "error": repr(e)})

    errors = [f for f in files if "error" in f]
    ok_files = [f for f in files if "error" not in f]

    measured = {
        "schema": "futures_behavior_10syms_coverage_measured@1",
        "measured_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "raw_dir": args.raw_dir,
        "script": "data/scripts/measure_coverage.py",
        "source_corpus": "FUTURES-DATA-10SYMS-V1 (2026-10-02), IBKR TWS readonly, 1160 files claimed; re-measured here",
        "files_scanned": len(files),
        "files_parse_errors": len(errors),
        "parse_error_files": [e["file"] for e in errors],
        "symbols": {},
        "_caveats": [
            "expiry_month_raw is the raw IBKR field (lastTradeDate); for NYMEX CL/NG the delivery month is the letter-code month ITSELF (X=Nov -> Nov delivery; lastTradeDate falls in the prior month) (FUTURES-DATA-10SYMS-V1 S9 finding C3; corrected 2026-10-02 per audit M4 - an earlier revision of this caveat said 'month AFTER', which was wrong).",
            "close_only bars (O=H=L=C, v=0) are settlement-derived; usable as reference/signal price, NOT as fill price (FUTURES-DATA-10SYMS-V1 finding #3).",
            "timeZoneId empty on expired-contract files (S9 C4); daily timestamps verified US/Central in S9 for 1-min files; treat tz as declared by source session, not re-verified here.",
            "front_probe files (_front_ in name) are short probe windows (3 D / 1800 S) recorded separately; they do not add coverage depth.",
        ],
    }

    for sym in SYMBOLS:
        sym_files = [f for f in ok_files if f.get("symbol") == sym]
        classes = {}
        for (whatUse, barSize), cls in CLASS_OF.items():
            bucket = [f for f in sym_files if f["whatUse"] == whatUse and f["barSize"] == barSize]
            if bucket:
                classes[cls] = agg_class(bucket)
        # real-volume month histogram from per-contract daily TRADES
        month_hist = collections.Counter()
        real_volume_dates = 0
        # per-contract {date: v} map for front-chain computation
        by_contract = {}  # localSymbol -> dict(expiry=YYYYMMDD, vol={date: v})
        for f in sorted(
            [f for f in sym_files
             if f["role"] == "per_contract" and f["whatUse"] == "TRADES" and f["barSize"] == "1 day"],
            key=lambda x: -(x["n_bars"]),
        ):
            with open(os.path.join(args.raw_dir, f["file"])) as fh:
                bars = json.load(fh).get("bars") or []
            ls = f["localSymbol"]
            if ls not in by_contract:  # keep richest file per contract
                by_contract[ls] = {"expiry_raw": f["expiry_month_raw"], "vol": {}}
            for b in bars:
                v = b.get("v") or 0
                if v > 0:
                    month_hist[month_of(b["t"])] += 1
                    real_volume_dates += 1
                by_contract[ls]["vol"][b["t"][:10]] = max(by_contract[ls]["vol"].get(b["t"][:10], 0), v)

        # ---- front-month real-volume chain under the FUTURES-DATA-10SYMS-V1
        # declared roll rule: hold the contract whose expiry month (month of
        # lastTradeDate, raw field) is the nearest month STRICTLY AFTER the
        # current calendar month; i.e. roll on the last session before day-1
        # of that contract's expiry month.
        # GENUINE-FRONT GATE: a month only counts if the nearest-expiry
        # fetched contract expires within 4 months (monthly cycles give gap
        # 1-2, quarterly cycles up to 4). A larger gap means the true front
        # contract of that month was NOT fetched (expired-secdef wall) and the
        # nearest fetched contract was then a DEFERRED contract - sporadic
        # deferred volume must not be counted as front-month tradability.
        front_month_hist = collections.Counter()
        front_dates = 0
        deferred_only_months = []
        all_dates = sorted({d for c in by_contract.values() for d in c["vol"]})
        expiries = []
        for ls, c in by_contract.items():
            e = str(c["expiry_raw"] or "")
            if len(e) == 8:
                expiries.append(((int(e[:4]), int(e[4:6])), ls))
        expiries.sort()
        month_gate = {}
        for d in all_dates:
            ym = (int(d[:4]), int(d[5:7]))
            cand = next(((eym, ls) for eym, ls in expiries if eym > ym), None)
            if cand is None:
                continue
            eym, ls = cand
            gap = (eym[0] * 12 + eym[1]) - (ym[0] * 12 + ym[1])
            if gap > 4:
                month_gate.setdefault(d[:7], gap)
                continue
            v = by_contract[ls]["vol"].get(d, 0)
            if v > 0:
                front_month_hist[month_of(d)] += 1
                front_dates += 1
        deferred_only_months = sorted(month_gate)
        # longest continuous recent run of months with >=10 real-volume trading days
        def longest_recent_run(hist):
            months = sorted(m for m, c in hist.items() if c >= 10)
            run_start = None
            if months:
                run_start = months[-1]
                for prev_idx in range(len(months) - 2, -1, -1):
                    y, m = map(int, months[prev_idx].split("-"))
                    nxt = (y + (m // 12), (m % 12) + 1)
                    if f"{nxt[0]:04d}-{nxt[1]:02d}" == run_start:
                        run_start = months[prev_idx]
                    else:
                        break
                n_months = (
                    None if run_start is None
                    else (int(months[-1][:4]) * 12 + int(months[-1][5:7]))
                    - (int(run_start[:4]) * 12 + int(run_start[5:7]))
                    + 1
                )
            return {"from": run_start, "to": months[-1] if months else None, "n_months": n_months}

        measured["symbols"][sym] = {
            "exchange": next((f["exchange"] for f in sym_files if f.get("exchange")), None),
            "classes": classes,
            "daily_real_volume": {
                "distinct_dates_with_v_gt0_any_contract": real_volume_dates,
                "month_histogram_any_contract": dict(sorted(month_hist.items())),
                "continuous_recent_run_any_contract": longest_recent_run(month_hist),
                "front_chain": {
                    "method": "declared roll rule approximation: held = contract with nearest expiry-month (month of raw lastTradeDate) strictly after current month; GENUINE-FRONT GATE: nearest fetched expiry must be within 4 months, else the true front was not fetched (deferred volume not counted); month counts >=10 days where held contract has v>0",
                    "distinct_dates_front_v_gt0": front_dates,
                    "month_histogram_front": dict(sorted(front_month_hist.items())),
                    "continuous_recent_run_front": longest_recent_run(front_month_hist),
                    "months_where_nearest_fetched_expiry_gt_4m_deferred_only_sampled": deferred_only_months[:60],
                },
            },
        }

    with open(args.out, "w") as fh:
        json.dump(measured, fh, indent=1, sort_keys=False)
    print(f"wrote {args.out}: {len(files)} files scanned, {len(errors)} parse errors")
    return 0


if __name__ == "__main__":
    sys.exit(main())
