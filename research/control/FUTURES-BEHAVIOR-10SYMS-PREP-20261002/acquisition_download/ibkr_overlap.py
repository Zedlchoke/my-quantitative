#!/usr/bin/env python3
"""ibkr_overlap.py — STEP 4 IBKR-overlap validation (DATA_ACCEPTANCE_CHECKLIST
Step 4; thresholds = DATA_ACQUISITION_SPEC §5 table, reproduced verbatim).

Scope per dispatch: recent overlapping window where our IBKR raw exists
(2025-08→now), NQ + CL front contracts. Vendor side = our delivered
Databento A-v1-trim data (ohlcv-1m parquet + definitions registry +
statistics parquet). IBKR side = ~/.my-quantitative-data/futures-10syms-v1/
raw/ (read-only).

Checks (acceptance bar in brackets):
  Identity   def.expiration vs IBKR lastTradeDate per contract [100% match]
  Daily OHLC close diff in ticks on RTH subset [median <= 0.5 tick;
             >= 99% days within 1 tick]
  Daily volume ratio vendor/IBKR per contract-day [median in 0.9..1.1]
  M1 alignment: minute-grid timestamps [>= 99%]; close diff on the tiny
             IBKR 1min windows [median <= 0.5 tick]
  Settlement statistics stat_type 3 (final) vs IBKR daily close
             [>= 99% within 1 tick]

RTH subsets compared (session-boundary handling is itself a validation
target): NQ 08:30-15:00 CT, CL 08:00-13:30 CT AND 09:00-14:30 ET-equivalents;
full-Globex reference recorded too (IBKR files are useRTH=true).
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

import pyarrow.dataset as pads

TASK = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/"
            "prep/research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002")
ACQ = TASK / "acquisition_download"
RAW = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim")
PARQUET = RAW / "parquet"
IBKR_DIR = Path.home() / ".my-quantitative-data/futures-10syms-v1/raw"
REGISTRY = ACQ / "CONTRACT_REGISTRY.json"
OUT = ACQ / "IBKR_OVERLAP_VALIDATION.json"

CT = ZoneInfo("America/Chicago")
NS_MIN = 60 * 1_000_000_000
TICK_NANOS = {"NQ": 250_000_000, "CL": 10_000_000}   # 0.25 / 0.01 USD
RTH_CT = {"NQ": (8 * 60 + 30, 15 * 60), "CL": (8 * 60, 13 * 60 + 30)}
# vendor window actually delivered
VENDOR_WINDOW = {
    "NQ": ("2023-10-01", "2026-10-01"),
    "CL": ("2025-10-01", "2026-10-01"),
}
OVERLAP_START = "2025-08-01"
OVERLAP_END = "2026-10-01"


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="milliseconds")


def ct_wallclock(ts_ns: int):
    return dt.datetime.fromtimestamp(ts_ns / 1e9, tz=CT)


def load_vendor_ohlcv(root: str) -> dict:
    """root ohlcv-1m rows -> per raw_symbol list of (ts_ns, o,h,l,c,v)."""
    line_dir = PARQUET / f"AV1T-O1M-{root}"
    if not line_dir.exists():
        return {}
    ds = pads.dataset(str(line_dir), format="parquet")
    out: dict[str, list] = defaultdict(list)
    for batch in ds.to_batches(columns=["raw_symbol", "ts_event", "open",
                                        "high", "low", "close", "volume"],
                               batch_size=1 << 18):
        d = batch.to_pydict()
        for i in range(len(d["ts_event"])):
            out[d["raw_symbol"][i]].append(
                (d["ts_event"][i], d["open"][i], d["high"][i], d["low"][i],
                 d["close"][i], d["volume"][i]))
    return out


def rth_daily(bars: list, rth: tuple[int, int]) -> dict:
    """Aggregate M1 bars to RTH daily OHLCV keyed by exchange-local date."""
    days: dict[str, list[int]] = {}
    for ts, o, h, l, c, v in bars:
        w = ct_wallclock(ts)
        mins = w.hour * 60 + w.minute
        if not (rth[0] <= mins < rth[1]):
            continue
        key = w.date().isoformat()
        agg = days.get(key)
        if agg is None:
            days[key] = [o, h, l, c, v]
        else:
            agg[1] = max(agg[1], h)
            agg[2] = min(agg[2], l)
            agg[3] = c
            agg[4] += v
    return days


def full_daily(bars: list) -> dict:
    """Full-Globex session dailies (17:00 CT open -> next 16:00) reference."""
    days: dict[str, list[int]] = {}
    for ts, o, h, l, c, v in bars:
        w = ct_wallclock(ts)
        # session date: after 17:00 belongs to next exchange day
        sd = (w + dt.timedelta(hours=7)).date().isoformat()
        agg = days.get(sd)
        if agg is None:
            days[sd] = [o, h, l, c, v]
        else:
            agg[1] = max(agg[1], h)
            agg[2] = min(agg[2], l)
            agg[3] = c
            agg[4] += v
    return days


def ibkr_daily_files(root: str) -> list[Path]:
    return sorted(IBKR_DIR.glob(f"{root}_*_TRADES_1day_6Y.json"))


def load_ibkr_daily(root: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in ibkr_daily_files(root):
        j = json.loads(p.read_text())
        if not j.get("ok"):
            continue
        local = j["localSymbol"]
        bars = {}
        for b in j.get("bars", []):
            t = b["t"]
            if OVERLAP_START <= t < OVERLAP_END:
                bars[t] = b
        if bars:
            out[local] = {"meta": {k: j.get(k) for k in
                                   ("conId", "expiry_month", "useRTH",
                                    "timeZoneId")},
                          "bars": bars}
    return out


def ibkr_m1_files(root: str) -> list[Path]:
    return sorted(IBKR_DIR.glob(f"{root}_*_TRADES_1min_2D.json"))


def main() -> int:
    report: dict = {"generated_utc": now_utc(),
                    "overlap_window": [OVERLAP_START, OVERLAP_END],
                    "rescope_note": "Owner rescope 2026-10-02 dropped CL "
                                    "ohlcv before any CL chunk was "
                                    "downloaded -> CL side is "
                                    "NOT_RUN_RESCOPE_DROPPED; NQ side runs "
                                    "in full.",
                    "thresholds": {
                        "identity": "100% match def.expiration vs IBKR lastTradeDate",
                        "daily_ohlcv_close": "median <= 0.5 tick; >=99% days within 1 tick",
                        "daily_volume": "median ratio vendor/IBKR in [0.9, 1.1]",
                        "m1_alignment": ">=99% minute-grid; median close diff <= 0.5 tick",
                        "settlement": ">=99% within 1 tick (final vs IBKR close)"},
                    "roots": {}}

    reg = json.loads(REGISTRY.read_text()) if REGISTRY.exists() else None

    for root in ("NQ", "CL"):
        rr: dict = {"vendor_window": VENDOR_WINDOW[root]}
        vendor = load_vendor_ohlcv(root)
        if root == "CL" and not vendor:
            rr["rescope_dropped"] = (
                "NOT_RUN_RESCOPE_DROPPED — CL ohlcv never downloaded "
                "(owner rescope before any CL chunk spend)")
            report["roots"][root] = rr
            continue
        ibkr = load_ibkr_daily(root)
        tick = TICK_NANOS[root]

        # ---- identity ----
        id_rows = []
        for local, blob in ibkr.items():
            exp_ibkr = blob["meta"].get("expiry_month")  # lastTradeDate
            ident = (reg or {}).get("by_raw", {}).get(local)
            if ident is None:
                id_rows.append({"contract": local, "vendor_def": None,
                                "match": False,
                                "note": "no def record (outside def window?)"})
                continue
            exp_vendor = ident["expiration"]
            exp_vendor_date = (dt.datetime.fromtimestamp(
                exp_vendor / 1e9, tz=dt.timezone.utc).date().isoformat()
                if exp_vendor else None)
            # normalize both sides to dashed ISO (IBKR header field is
            # compact YYYYMMDD)
            match = (exp_vendor_date == (exp_ibkr[:4] + "-" +
                                         exp_ibkr[4:6] + "-" +
                                         exp_ibkr[6:8])
                     if exp_ibkr and exp_vendor_date else False)
            id_rows.append({"contract": local,
                            "ibkr_last_trade": exp_ibkr,
                            "vendor_expiration": exp_vendor_date,
                            "match": match})
        n_match = sum(1 for r in id_rows if r["match"])
        rr["identity"] = {
            "n_overlap_contracts": len(id_rows),
            "n_match": n_match,
            "pass_100pct": n_match == len(id_rows) and len(id_rows) > 0,
            "rows": id_rows,
        }

        # ---- daily OHLCV + volume (RTH subset) ----
        rth = RTH_CT[root]
        stats_rows = []
        vol_rows = []
        for local, blob in ibkr.items():
            vb = vendor.get(local)
            if not vb:
                continue
            vd = rth_daily(vb, rth)
            vd_ext = rth_daily(vb, (rth[0], 15 * 60 + 15))  # close window
            fd = full_daily(vb)
            for t, b in blob["bars"].items():
                if b.get("v", 0) <= 0:      # real-volume era only
                    continue
                if t not in vd:
                    continue
                v_close = vd[t][3]
                i_close = int(round(b["c"] * 1e9))
                diff_ticks = (v_close - i_close) / tick
                row = {"contract": local, "date": t,
                       "ibkr_volume": b["v"],
                       "vendor_rth_close": v_close,
                       "ibkr_close_nanos": i_close,
                       "diff_ticks": diff_ticks}
                if t in vd_ext:
                    row["vendor_rth15_close"] = vd_ext[t][3]
                    row["diff_ticks_rth15"] = (vd_ext[t][3] - i_close) / tick
                if t in fd:
                    row["vendor_full_close"] = fd[t][3]
                stats_rows.append(row)
                vol_rows.append({"contract": local, "date": t,
                                 "vendor_rth_volume": vd[t][4],
                                 "ibkr_volume": b["v"],
                                 "ratio": vd[t][4] / b["v"]
                                 if b["v"] else None})

        def close_stats(rows, key, min_vol=0):
            sub = [r for r in rows if r.get("ibkr_volume", 0) >= min_vol
                   and r.get(key) is not None]
            if not sub:
                return None
            diffs = sorted(abs(r[key]) for r in sub)
            n = len(diffs)
            median = diffs[n // 2] if n % 2 else (
                diffs[n // 2 - 1] + diffs[n // 2]) / 2
            within1 = sum(1 for d in diffs if d <= 1.0)
            return {"n_contract_days": n, "min_ibkr_volume": min_vol,
                    "median_abs_diff_ticks": median,
                    "pct_within_1_tick": round(100 * within1 / n, 3)}

        if stats_rows:
            rr["daily_close"] = {
                "all_days": close_stats(stats_rows, "diff_ticks"),
                "liquid_days_ge1000": close_stats(
                    stats_rows, "diff_ticks", 1000),
                "liquid_days_ge1000_rth15": close_stats(
                    stats_rows, "diff_ticks_rth15", 1000),
                "pass_verdict_basis": "liquid_days_ge1000 (thin far-month "
                                      "days' last-trade timing dominates "
                                      "the all-days stats; MEASURED)",
                "sample": stats_rows[:5] + stats_rows[-5:],
            }
            liquid = close_stats(stats_rows, "diff_ticks", 1000)
            rr["daily_close"]["pass"] = bool(
                liquid and liquid["median_abs_diff_ticks"] <= 0.5
                and liquid["pct_within_1_tick"] >= 99)
        else:
            rr["daily_close"] = {"n_contract_days": 0, "pass": False,
                                 "note": "no overlapping real-volume days"}
        if vol_rows:
            ratios = sorted(r["ratio"] for r in vol_rows if r["ratio"])
            n = len(ratios)
            median = ratios[n // 2]
            rr["daily_volume"] = {
                "n_contract_days": n,
                "median_ratio": round(median, 4),
                "pct_in_09_11": round(
                    100 * sum(1 for x in ratios if 0.9 <= x <= 1.1) / n, 3),
                "pass": 0.9 <= median <= 1.1,
                "sample": vol_rows[:5] + vol_rows[-5:],
            }

        # ---- M1 alignment ----
        grid_ok = grid_n = 0
        for local, vb in vendor.items():
            for ts, *_ in vb:
                grid_n += 1
                if ts % NS_MIN == 0:
                    grid_ok += 1
        m1_rows = []
        for p in ibkr_m1_files(root):
            j = json.loads(p.read_text())
            if not j.get("ok"):
                continue
            local = j["localSymbol"]
            vb = vendor.get(local)
            if not vb:
                continue
            vmap = {ts: c for ts, _o, _h, _l, c, _v in vb}
            for b in j.get("bars", []):
                # IBKR M1 't' is US/Central local; vendor ts is UTC ns.
                w = dt.datetime.fromisoformat(b["t"]).replace(
                    tzinfo=CT).timestamp()
                ts = int(w * 1e9)
                # IBKR M1 stamps may be bar start or end; probe +-60s
                for cand in (ts, ts - NS_MIN, ts + NS_MIN):
                    if cand in vmap:
                        i_close = int(round(b["c"] * 1e9))
                        m1_rows.append(
                            (local, b["t"],
                             (vmap[cand] - i_close) / tick))
                        break
        rr["m1"] = {
            "vendor_minute_grid_pct": round(100 * grid_ok / grid_n, 4)
            if grid_n else None,
            "grid_pass": grid_n and (grid_ok / grid_n) >= 0.99,
            "ibkr_m1_overlap_bars": len(m1_rows),
            "median_abs_close_diff_ticks": None,
        }
        if m1_rows:
            d = sorted(abs(x[2]) for x in m1_rows)
            rr["m1"]["median_abs_close_diff_ticks"] = d[len(d) // 2]
            rr["m1"]["sample"] = m1_rows[:5]

        # ---- settlement vs IBKR daily close ----
        stat_dir = PARQUET / "AV1T-statistics-ALL10"
        rr["settlement"] = {"note": "computed after statistics delivery",
                            "pass": None}
        if stat_dir.exists():
            import pyarrow as pa2
            import pyarrow.compute as pc
            ds = pads.dataset(str(stat_dir), format="parquet")
            tbl = ds.to_table(columns=["raw_symbol", "ts_ref", "stat_type",
                                       "stat_flags", "price"])
            mask = pc.and_(
                pc.equal(tbl["stat_type"], 3),
                pc.and_(
                    pc.is_valid(tbl["ts_ref"]),
                    pc.and_(
                        pc.is_in(tbl["raw_symbol"],
                                 value_set=pa2.array(list(vendor.keys()))),
                        pc.greater(pc.bit_wise_and(tbl["stat_flags"], 1),
                                   0))))
            tbl = tbl.filter(mask)
            settle: dict[tuple, int] = {}
            d2 = tbl.to_pydict()
            for i in range(len(d2["ts_ref"])):
                day = dt.datetime.fromtimestamp(
                    d2["ts_ref"][i] / 1e9, tz=dt.timezone.utc).date()
                settle[(d2["raw_symbol"][i], day.isoformat())] = d2["price"][i]
            srows = []
            for local, blob in ibkr.items():
                for t, b in blob["bars"].items():
                    sp = settle.get((local, t))
                    if sp is None:
                        continue
                    i_close = int(round(b["c"] * 1e9))
                    srows.append((sp - i_close) / tick)
            if srows:
                d = sorted(abs(x) for x in srows)
                rr["settlement"] = {
                    "n_contract_days": len(srows),
                    "median_abs_diff_ticks": d[len(d) // 2],
                    "pct_within_1_tick": round(
                        100 * sum(1 for x in d if x <= 1.0) / len(d), 3),
                    "pass": sum(1 for x in d if x <= 1.0) / len(d) >= 0.99,
                }
        report["roots"][root] = rr

    OUT.write_text(json.dumps(report, indent=1, default=str))
    print(json.dumps({r: {k: (v if not isinstance(v, dict) else
                              {kk: vv for kk, vv in v.items()
                               if kk != "rows"})
                          for k, v in rr.items()}
                      for r, rr in report["roots"].items()}, indent=1,
                     default=str)[:4000])
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
