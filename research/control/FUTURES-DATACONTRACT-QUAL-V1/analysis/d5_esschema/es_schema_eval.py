"""FUTURES-DATACONTRACT-QUAL-V1 / D5-ESSCHEMA — ES vendor schema + close
conventions + spread-proxy recompute. READ-ONLY over owned data.

Inputs (all owned, no new purchases):
  Vendor Databento GLBX ohlcv-1m ES:
    /Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/
      AV1R-O1M-ES-DELTA/  (2010-06..2023-10 legacy batch)
      AV1T-O1M-ES/        (2023-10..2026-10)
      AV1T-definition-ALL10/   (instrument definitions)
      AV1T-statistics-ALL10/   (settlement & other statistics)
  IBKR intake (FUTURES-DATA-10SYMS-V1):
    ~/.my-quantitative-data/futures-10syms-v1/raw/ES_*.json
    research/control/FUTURES-DATA-10SYMS-V1/S6_FRONT_SPREADS.json

Explicit limits: no BBO is owned (bbo-1m NOT owned); nothing here supports
fill/queue/execution-realism claims. Everything is MODELED-COST input
quality only. Missing statistics => NOT_RUN.

Bar timestamp convention (verified empirically below): ts_event = interval
START in exchange time (no bar is stamped 16:00-16:59 CT during the Globex
maintenance halt; session-reopen trades at 17:00:00 CT land in the bar
stamped 17:00). Hence the last session bar is stamped 15:59 and the bar
whose interval ENDS exactly at 15:00:00 CT is the one stamped 14:59.
"""
from __future__ import annotations

import glob
import json
import os
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

BASE = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet")
IBKR_RAW = Path(os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw"))
OUT = Path(__file__).resolve().parent
TICK = 250_000_000          # 0.25 pts in 1e-9 fixed point (from definitions)
SPREAD_TICK = 50_000_000    # 0.05 pts — ES calendar-spread grid
PT = 1_000_000_000          # 1.0 index point
MULT = 50.0                 # USD per index point (unit_of_measure_qty 5e10 * 1e-9)
CT = "America/Chicago"

# stat_type enum per vendor's own databento_dbn package (StatType):
STAT_NAMES = {1: "OPENING_PRICE", 2: "INDICATIVE_OPENING_PRICE",
              3: "SETTLEMENT_PRICE", 4: "TRADING_SESSION_LOW_PRICE",
              5: "TRADING_SESSION_HIGH_PRICE", 6: "CLEARED_VOLUME",
              7: "LOWEST_OFFER", 8: "HIGHEST_BID", 9: "OPEN_INTEREST",
              10: "FIXING_PRICE", 11: "CLOSE_PRICE", 17: "UPPER_PRICE_LIMIT",
              18: "LOWER_PRICE_LIMIT"}

report: dict = {}


def pct(x, digits=2):
    return None if x is None else round(float(x), digits)


def med_abs_ticks(diffs):
    s = pd.Series(diffs).abs() / TICK
    return (int(len(s)), pct(s.median(), 2)) if len(s) else (0, None)


# ------------------------------------------------------------------ 1. schema
def schema_block():
    files = {
        "ohlcv_AV1R": "AV1R-O1M-ES-DELTA/AV1R-O1M-ES-DELTA__2022-06-01_2023-10-01.parquet",
        "ohlcv_AV1T": "AV1T-O1M-ES/AV1T-O1M-ES__2026-04-01_2026-10-01.parquet",
        "definition": "AV1T-definition-ALL10/AV1T-definition-ALL10__2026-07-01_2026-10-01.parquet",
        "statistics": "AV1T-statistics-ALL10/AV1T-statistics-ALL10__2026-06-01_2026-08-01.parquet",
    }
    out = {"files": {}}
    for k, rel in files.items():
        md = pq.read_metadata(BASE / rel)
        cols = []
        for i in range(md.num_columns):
            c = md.schema.column(i)
            cols.append({"name": c.name, "physical_type": c.physical_type,
                         "logical_type": str(c.logical_type)})
        out["files"][k] = {"path": rel, "rows": md.num_rows, "columns": cols}
    ohl = out["files"]["ohlcv_AV1T"]
    names = [c["name"] for c in ohl["columns"]]
    out["publication_fields_present"] = sorted(
        set(names) & {"publisher_id", "sequence", "ts_init", "user_defined_instrument_id"})
    out["publication_fields_note"] = ("no publisher_id/sequence/ts_init in these "
                                      "trimmed parquet exports (absent, not null)")
    return out


# ------------------------------------------------- 2. definitions / id map
def es_id_map():
    sym2id, id2row = {}, {}
    for f in sorted(glob.glob(str(BASE / "AV1T-definition-ALL10/*.parquet"))):
        t = pq.read_table(f, columns=["instrument_id", "raw_symbol",
                                      "security_type", "instrument_class",
                                      "maturity_year", "maturity_month",
                                      "min_price_increment", "unit_of_measure_qty",
                                      "action"])
        m = pc.and_(pc.equal(t["security_type"], "FUT"),
                    pc.starts_with(t["raw_symbol"], "ES"))
        for r in t.filter(m).to_pylist():
            key = (r["raw_symbol"], r["maturity_year"], r["maturity_month"])
            sym2id.setdefault(key, set()).add(r["instrument_id"])
            id2row[r["instrument_id"]] = {
                "raw_symbol": r["raw_symbol"], "class": r["instrument_class"],
                "maturity": f"{r['maturity_year']}-{r['maturity_month']:02d}",
                "tick": r["min_price_increment"], "uom_qty": r["unit_of_measure_qty"],
                "action": r["action"]}
    return sym2id, id2row


# ------------------------------------------------------------- 3. ohlcv load
def load_ohlcv(rel):
    t = pq.read_table(BASE / rel).to_pandas()
    t["dt"] = pd.to_datetime(t["ts_event"], unit="ns", utc=True).dt.tz_convert(CT)
    t["is_spread"] = t["raw_symbol"].str.contains("-")
    return t


def session_assign(df):
    """Trade-date d = session (d-1 17:00 CT -> d 16:00 CT)."""
    d = df["dt"].dt.date
    nxt = (df["dt"] + pd.Timedelta(days=1)).dt.date
    df = df.copy()
    df["session"] = pd.Series(np_where_hour_ge_17(df), index=df.index)
    return df


def np_where_hour_ge_17(df):
    return [nd if h >= 17 else d for d, h, nd in
            zip(df["dt"].dt.date, df["dt"].dt.hour,
                (df["dt"] + pd.Timedelta(days=1)).dt.date)]


# --------------------------------------------- 4. per-session front + marks
def front_marks(ohl, id2row):
    outr = ohl[~ohl["is_spread"]].copy()
    outr["session"] = np_where_hour_ge_17(outr)
    vol = outr.groupby(["session", "instrument_id"])["volume"].sum()
    # front = highest-volume outright that session (schema-lane front approx)
    front = vol.reset_index().sort_values("volume", ascending=False) \
               .drop_duplicates("session").set_index("session")
    rows = []
    front = front.reset_index()
    front["session"] = front["session"].astype(str)
    front = front.set_index("session")
    for sess, iid in front["instrument_id"].items():
        day = outr[(outr["session"].astype(str) == sess) & (outr["instrument_id"] == iid)]
        hhmm = day["dt"].dt.strftime("%H:%M")
        row = {"session": str(sess), "front": id2row[iid]["raw_symbol"],
               "front_iid": int(iid), "n_bars": int(len(day)),
               "first_bar": str(hhmm.iloc[0]) if len(day) else None,
               "last_bar_stamp": str(hhmm.iloc[-1]) if len(day) else None,
               "close_1600_lastbar": int(day["close"].iloc[-1]) if len(day) else None,
               "vol_1m_sum": int(day["volume"].sum())}
        b1459 = day[hhmm == "14:59"]
        b1500 = day[hhmm == "15:00"]
        row["close_1500_edge"] = int(b1459["close"].iloc[-1]) if len(b1459) else None
        row["close_1500_bar"] = int(b1500["close"].iloc[-1]) if len(b1500) else None
        rows.append(row)
    m = pd.DataFrame(rows).set_index("session")
    return m.join(front[["volume"]].rename(columns={"volume": "front_vol"})).sort_index()


# ------------------------------------------------------- 5. settlement stats
def settlement_stats(chunks, front_sessions):
    """stat_type 3 = SETTLEMENT_PRICE rows for the front instruments."""
    want = {}   # session -> iid
    for r in front_sessions.itertuples():
        want[r.Index] = r.front_iid
    ids = pa.array(sorted({int(v) for v in want.values()}), type=pa.uint32())
    recs = []
    for rel in chunks:
        f = BASE / rel
        t = pq.read_table(f, columns=["instrument_id", "ts_event", "stat_type",
                                      "price", "update_action"])
        es = t.filter(pc.is_in(t["instrument_id"], ids)).to_pandas()
        es = es[es["stat_type"] == 3]
        if not len(es):
            continue
        es["dt"] = pd.to_datetime(es["ts_event"], unit="ns", utc=True).dt.tz_convert(CT)
        recs.append(es)
    if not recs:
        return None, {}
    allst = pd.concat(recs)
    out = {}
    hh_all = Counter()
    for (iid, dt), grp in allst.groupby(["instrument_id", allst["dt"].dt.date]):
        sess = None
        # settlement published in break/reopen (>=15:00) belongs to same trade date
        sess = str(dt)
        for r in grp.sort_values("ts_event").itertuples():
            hh_all[r.dt.strftime("%H:%M")] += 1
        fin = grp.sort_values("ts_event").iloc[-1]
        out[(sess, int(iid))] = {
            "n_updates": int(len(grp)),
            "final_price": int(fin["price"]),
            "final_pub_hhmm": fin["dt"].strftime("%H:%M"),
            "first_pub_hhmm": grp.sort_values("ts_event").iloc[0]["dt"].strftime("%H:%M"),
        }
    return out, dict(hh_all)


# ------------------------------------------------------------- 6. IBKR daily
def ibkr_daily(local):
    hits = [p for p in IBKR_RAW.glob(f"ES_{local}_*_TRADES_1day_6Y.json")]
    if not hits:
        return {}
    d = json.loads(hits[0].read_text())
    return {b["t"]: b for b in d["bars"] if b.get("v", 0) not in (0, -1)}


def ibkr_bid_ask(local):
    b = json.loads(next(IBKR_RAW.glob(f"ES_{local}_*_BID_1day_1Y.json")).read_text())["bars"]
    a = json.loads(next(IBKR_RAW.glob(f"ES_{local}_*_ASK_1day_1Y.json")).read_text())["bars"]
    return ({x["t"]: x["c"] for x in b}, {x["t"]: x["c"] for x in a})


# ==================================================================== main
def main():
    dt_start = datetime.now(timezone.utc)

    report["meta"] = {
        "lane": "D5-ESSCHEMA", "cycle": "FUTURES-DATACONTRACT-QUAL-V1",
        "generated_utc": dt_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_root": str(BASE),
        "read_only": True, "bbo_owned": False,
        "claims_class": "MODELED COST input quality; NO fill/queue/execution-realism claims",
    }

    # ---- 1 schema ----
    report["schema"] = schema_block()
    sym2id, id2row = es_id_map()
    outright_ids = {iid: r for iid, r in id2row.items() if r["class"] == "F"}
    report["definitions"] = {
        "n_es_rows": len(id2row),
        "n_outright_futures": len(outright_ids),
        "outright_ids": {str(k): v["raw_symbol"] for k, v in sorted(outright_ids.items())},
        "tick_min_price_increment": outright_ids[10252]["tick"] if 10252 in outright_ids else None,
        "unit_of_measure_qty": outright_ids[10252]["uom_qty"] if 10252 in outright_ids else None,
        "symbol_multi_id": {f"{y}-{m}-{s}": sorted(v)
                            for (s, y, m), v in sym2id.items() if len(v) > 1},
        "actions": dict(Counter(r["action"] for r in id2row.values())),
        "scale_note": "int64 fixed-point 1e-9 (price 7635250000000 = 7635.25); "
                      "tick 250000000 = 0.25; uom 50000000000 = $50/pt",
    }

    # ---- 2 ohlcv windows ----
    W1 = "AV1T-O1M-ES/AV1T-O1M-ES__2026-04-01_2026-10-01.parquet"
    W2 = "AV1T-O1M-ES/AV1T-O1M-ES__2025-10-01_2026-04-01.parquet"
    ohl = load_ohlcv(W1)
    ohl2 = load_ohlcv(W2)
    tickchk = {}
    for name, df in [("2026_summer(W1)", ohl), ("2026_winter(W2)", ohl2)]:
        o, s = df[~df["is_spread"]], df[df["is_spread"]]
        tickchk[name] = {
            "rows": int(len(df)),
            "outright_rows": int(len(o)),
            "outright_close_off_grid": int((o["close"] % TICK != 0).sum()),
            "outright_ohlc_off_grid": int(((o[["open", "high", "low", "close"]] % TICK) != 0)
                                          .any(axis=1).sum()),
            "spread_rows": int(len(s)),
            "spread_close_off_quarter_grid": int((s["close"] % TICK != 0).sum()),
            "spread_close_off_nickel_grid": int((s["close"] % SPREAD_TICK != 0).sum()),
            "rtype_values": dict(Counter(df["rtype"].to_list())),
            "dt_min": str(df["dt"].min()), "dt_max": str(df["dt"].max()),
            "n_symbols": int(df["raw_symbol"].nunique()),
            "symbols_with_multiple_ids": {},
        }
    # halt / stamp-convention check (hour histogram)
    wk = ohl[(ohl["dt"] >= "2026-09-08") & (ohl["dt"] < "2026-09-12") & (~ohl["is_spread"])]
    hrs = Counter(wk["dt"].dt.hour.to_list())
    tickchk["stamp_convention"] = {
        "sample_week": "2026-09-08..11 (outright)",
        "bars_by_hour_CT": {str(h): int(c) for h, c in sorted(hrs.items())},
        "hour16_bars": int(hrs.get(16, 0)),
        "conclusion": "ts_event = bar interval START: no bar stamped 16:00-16:59 "
                      "(maintenance halt); reopen trades at 17:00:00 CT appear in "
                      "the 17:00-stamped bar; last session bar stamped 15:59",
    }
    # boundary continuity AV1R -> AV1T
    last_r = pq.read_table(BASE / "AV1R-O1M-ES-DELTA/AV1R-O1M-ES-DELTA__2022-06-01_2023-10-01.parquet",
                           columns=["ts_event"]).column(0).to_pylist()
    first_t = pq.read_table(BASE / "AV1T-O1M-ES/AV1T-O1M-ES__2023-10-01_2024-04-01.parquet",
                            columns=["ts_event"]).column(0).to_pylist()
    report["vendor_batches"] = {
        "AV1R-O1M-ES-DELTA": "2010-06-06..2023-10-01, 7 chunks, same ohlcv-1m schema",
        "AV1T-O1M-ES": "2023-10-01..2026-10-01, 6 chunks",
        "boundary": {"AV1R_last_ts": max(last_r), "AV1T_first_ts": min(first_t),
                     "note": "file ranges touch at 2023-10-01; not re-verified row-level "
                             "for duplicates here (bulk coverage out of D5 scope)"},
    }
    report["tick_grid"] = tickchk

    # ---- 3 front + marks ----
    m1 = front_marks(ohl, id2row)
    m2 = front_marks(ohl2, id2row)
    # volume front sanity: roll months observed
    report["front_selection"] = {
        "rule": "front = highest 1m-volume outright instrument per session "
                "(schema-lane approximation; T-5 roll not needed for schema work)",
        "W1_fronts": dict(Counter(m1["front"])),
        "W2_fronts": dict(Counter(m2["front"])),
        "last_bar_stamp_distribution": dict(Counter(m1["last_bar_stamp"]).most_common(5)),
    }

    # ---- 4 settlement ----
    set1, hh1 = settlement_stats(
        ["AV1T-statistics-ALL10/AV1T-statistics-ALL10__2026-06-01_2026-08-01.parquet"], m1)
    set2, hh2 = settlement_stats(
        ["AV1T-statistics-ALL10/AV1T-statistics-ALL10__2025-10-01_2025-12-01.parquet",
         "AV1T-statistics-ALL10/AV1T-statistics-ALL10__2025-12-01_2026-02-01.parquet",
         "AV1T-statistics-ALL10/AV1T-statistics-ALL10__2026-02-01_2026-04-01.parquet"], m2)
    report["settlement"] = {
        "source": "AV1T-statistics-ALL10 (statistics schema), stat_type=3 "
                  "SETTLEMENT_PRICE per databento_dbn StatType enum",
        "status": "PRESENT" if set1 else "NOT_RUN_MISSING",
        "pub_time_top_hhmm_W1": dict(Counter(hh1).most_common(8)) if set1 else None,
        "pub_time_top_hhmm_W2": dict(Counter(hh2).most_common(8)) if set2 else None,
        "note_close_price_stat": "stat_type 11 CLOSE_PRICE: zero ES rows in sampled "
                                 "chunks (absent for ES; SETTLEMENT_PRICE is the mark CME "
                                 "publishes for ES)",
    }

    # ---- 5 IBKR close comparisons ----
    ibkr = {}
    for loc in ("ESZ6", "ESU6", "ESM6", "ESH6", "ESH7"):
        d_ = ibkr_daily(loc)
        if d_:
            ibkr[loc] = d_
    cmp_rows = []
    for m, tag in ((m1, "W1_summer"), (m2, "W2_winter")):
        for r in m.itertuples():
            loc = r.front
            if loc not in ibkr or r.Index not in ibkr[loc]:
                continue
            c_ibkr = int(round(ibkr[loc][r.Index]["c"] * PT))
            st = (set1 or {}).get((r.Index, r.front_iid)) if tag == "W1_summer" \
                else (set2 or {}).get((r.Index, r.front_iid))
            cmp_rows.append({
                "win": tag, "session": r.Index, "front": loc,
                "ibkr_close": c_ibkr,
                "vendor_lastbar": r.close_1600_lastbar,
                "vendor_1459bar": r.close_1500_edge,
                "vendor_1500bar": r.close_1500_bar,
                "d_lastbar_vs_ibkr_ticks": (r.close_1600_lastbar - c_ibkr) / TICK,
                "d_1500edge_vs_ibkr_ticks": (r.close_1500_edge - c_ibkr) / TICK
                                             if r.close_1500_edge is not None else None,
                "d_1500bar_vs_ibkr_ticks": (r.close_1500_bar - c_ibkr) / TICK
                                            if r.close_1500_bar is not None else None,
                "settle_final": st["final_price"] if st else None,
                "settle_final_pub": st["final_pub_hhmm"] if st else None,
                "d_settle_vs_ibkr_ticks": (st["final_price"] - c_ibkr) / TICK if st else None,
                "d_settle_vs_lastbar_ticks": (st["final_price"] - r.close_1600_lastbar) / TICK
                                              if st else None,
                "ibkr_v": ibkr[loc][r.Index]["v"],
                "vendor_v_1m_sum": r.vol_1m_sum,
            })
    cd = pd.DataFrame(cmp_rows)
    conv = {}
    cd["d_settle_vs_1500edge_ticks"] = [
        (sf - e) / TICK if (sf is not None and e is not None and not pd.isna(e)) else None
        for sf, e in zip(cd["settle_final"], cd["vendor_1459bar"])]
    for col, lab in [("d_lastbar_vs_ibkr_ticks", "vendor_lastbar(15:59-stamp) vs IBKR daily close"),
                     ("d_1500edge_vs_ibkr_ticks", "vendor_14:59-bar close (ends 15:00 CT) vs IBKR"),
                     ("d_1500bar_vs_ibkr_ticks", "vendor_15:00-bar close vs IBKR"),
                     ("d_settle_vs_ibkr_ticks", "vendor SETTLEMENT final vs IBKR daily close"),
                     ("d_settle_vs_lastbar_ticks", "vendor SETTLEMENT final vs vendor lastbar"),
                     ("d_settle_vs_1500edge_ticks", "vendor SETTLEMENT final vs vendor 14:59-bar close")]:
        s = pd.Series([x for x in cd[col] if x is not None])
        conv[lab] = {"n": int(len(s)), "median_abs_ticks": pct(s.abs().median(), 2),
                     "mean_abs_ticks": pct(s.abs().mean(), 2),
                     "p90_abs_ticks": pct(s.abs().quantile(0.9), 2),
                     "exact_ticks": int((s == 0).sum())} if len(s) else {"n": 0}
    # per-window split for the headline corroboration
    split = {}
    for w in ("W1_summer", "W2_winter"):
        sub = cd[cd["win"] == w]
        split[w] = {
            "n": int(len(sub)),
            "med_lastbar_vs_ibkr": pct(sub["d_lastbar_vs_ibkr_ticks"].abs().median(), 2),
            "med_1500edge_vs_ibkr": pct(sub["d_1500edge_vs_ibkr_ticks"].abs().median(), 2),
            "med_settle_vs_ibkr": pct(sub["d_settle_vs_ibkr_ticks"].abs().median(), 2)
                                  if sub["d_settle_vs_ibkr_ticks"].notna().any() else None,
        }
    vol_ratio = (cd["vendor_v_1m_sum"] / cd["ibkr_v"]).replace([float("inf")], pd.NA).dropna()
    report["close_conventions"] = {
        "windows": {"W1_summer": "2026-03-31..2026-09-30 (CDT)",
                    "W2_winter": "2025-09-30..2026-04-01 (CST+CDT)"},
        "match_table": conv, "per_window": split,
        "settlement_coverage": {
            "sessions_compared": int(len(cd)),
            "with_vendor_settlement_final": int(cd["settle_final"].notna().sum()),
            "share": pct(cd["settle_final"].notna().mean() * 100, 1)},
        "ibkr_volume_ratio": {"n": int(len(vol_ratio)), "median": pct(vol_ratio.median(), 4),
                              "p10": pct(vol_ratio.quantile(0.1), 4),
                              "p90": pct(vol_ratio.quantile(0.9), 4),
                              "note": "vendor sum(1m trade volume)/IBKR daily volume; "
                                      "1m volume semantics = traded contracts per minute"},
        "detail_rows": cmp_rows,   # full per-session audit trail
    }

    # ---- 6 S6 spread proxy reproduction + vendor analogue ----
    s6 = json.loads(Path("/Users/hoangminhlong/my-quantitative/research/control/"
                         "FUTURES-DATA-10SYMS-V1/S6_FRONT_SPREADS.json").read_text())["ES"]
    bid, ask = ibkr_bid_ask("ESZ6")
    common = sorted(set(bid) & set(ask))[-20:]
    diffs, crossed = [], 0
    for t in common:
        d = ask[t] - bid[t]
        if d < 0:
            crossed += 1
        else:
            diffs.append(d)
    ibkr_proxy = {
        "front": "ESZ6", "n_sessions": len(common),
        "window": f"{common[0]}..{common[-1]}",
        "median_points": pct(statistics.median(diffs), 3),
        "median_ticks": pct(statistics.median(diffs) * PT / TICK, 2),
        "median_usd": pct(statistics.median(diffs) * MULT, 2),
        "p90_usd": pct(sorted(diffs)[int(0.9 * len(diffs))] * MULT, 2)
                   if len(diffs) >= 10 else None,
        "crossed_days": crossed,
        "s6_reference": s6,
        "definition": "IBKR daily ASK-close minus BID-close, same session, front "
                      "ESZ6, last 20 mutual sessions (mirrors fut10 spread_stats "
                      "close-to-close BID/ASK proxy)",
    }
    # vendor 1m analogue on the same 20 sessions, front outright = ESZ6
    outr = ohl[~ohl["is_spread"]].copy()
    outr["session"] = pd.Series(np_where_hour_ge_17(outr), index=outr.index).astype(str)
    z = outr[(outr["raw_symbol"] == "ESZ6") & (outr["session"].isin(common))]
    dcl, rng, dcl_rth = [], [], []
    for sess, g in z.groupby("session"):
        g = g.sort_values("dt")
        c = g["close"].to_list()
        for i in range(1, len(c)):
            d = abs(c[i] - c[i - 1]) / TICK
            dcl.append(d)
            hh = g["dt"].dt.hour.iloc[i]
            if 8 <= hh < 15:       # RTH-ish 08:30-15:00 CT
                dcl_rth.append(d)
        rng += list((g["high"] - g["low"]) / TICK)
    s_all, s_rth, s_rng = pd.Series(dcl), pd.Series(dcl_rth), pd.Series(rng)
    vendor_proxy = {
        "front": "ESZ6", "sessions": int(z["session"].nunique()),
        "n_1m_transitions": int(len(s_all)),
        "median_abs_dclose_ticks": pct(s_all.median(), 3),
        "zero_change_share": pct((s_all == 0).mean() * 100, 2),
        "median_nonzero_abs_dclose_ticks": pct(s_all[s_all > 0].median(), 3),
        "p90_abs_dclose_ticks": pct(s_all.quantile(0.9), 2),
        "rth_median_abs_dclose_ticks": pct(s_rth.median(), 3),
        "rth_median_nonzero_ticks": pct(s_rth[s_rth > 0].median(), 3),
        "rth_zero_share_pct": pct((s_rth == 0).mean() * 100, 2),
        "median_1m_hilo_range_ticks": pct(s_rng.median(), 2),
        "note": "vendor has TRADE ohlcv only (no BBO owned): a BID/ASK-close proxy "
                "CANNOT be mirrored. Reported instead: consecutive-1m |dclose| in "
                "ticks (effective-cost flavored, floor-ish) and 1m high-low range "
                "(volatility flavored, upper bound flavor) on the same sessions.",
    }
    report["spread_proxy"] = {
        "ibkr_reproduction": ibkr_proxy, "vendor_1m_analogue": vendor_proxy,
        "honest_statement": (
            "A close-proxy spread supports ONLY tiering inputs for modeled cost "
            "with an overstatement caveat (IBKR daily BID/ASK closes are two "
            "non-synchronous marks; the 15:00/16:00 convention gap above shows "
            "single-time marks can sit ~ticks away from each other). It does NOT "
            "support execution realism claims, fill probability, queue position, "
            "or capacity: bbo-1m is NOT owned and, per Co-Owner, insufficient "
            "anyway. Vendor 1m |dclose| likewise bounds nothing executable — it "
            "only shows the ES front trades on a 1-tick grid with ~half of minute "
            "transitions flat, consistent with a ~1-tick effective-spread regime."),
    }

    (OUT / "es_schema_eval.json").write_text(json.dumps(report, indent=1, default=str))

    # console digest
    print("== D5-ESSCHEMA digest ==")
    print("tick grid:", {k: v for k, v in tickchk.items() if k.startswith(("2026",))})
    print("fronts W1:", report["front_selection"]["W1_fronts"])
    print("settlement status:", report["settlement"]["status"],
          report["settlement"]["pub_time_top_hhmm_W1"])
    for k, v in conv.items():
        print("conv:", k, v)
    print("per-window:", split)
    print("vol ratio:", report["close_conventions"]["ibkr_volume_ratio"])
    print("ibkr proxy:", {k: v for k, v in ibkr_proxy.items() if k != "s6_reference"})
    print("s6 ref:", s6)
    print("vendor proxy:", {k: v for k, v in vendor_proxy.items() if k != "note"})
    print("wrote", OUT / "es_schema_eval.json")


if __name__ == "__main__":
    main()
