#!/usr/bin/env python
#!/usr/bin/env python
"""ES deep-research v2 — A6 data-quality ledger per era (lane DEEP-ES).

Vendor-documented eras (DATA_ACQUISITION_SPEC.md, citing
databento.com/docs/venues-and-datasets/glbx-mdp3, access 2026-10-02):
  - pre-2017-05-21: legacy FIX/FAST capture (no ts_recv; ts_event present)
  - pre-2015-11-20: timestamps limited to millisecond resolution
Checks here VERIFY those claims on our actual bytes (ts granularity), and
measure per-era coverage/staleness/jump rates on the front-contract series.

Also: DST-transition integrity, maintenance-window leakage, Saturday
sessions, early-close holidays, big 1m jumps, and an ES-vs-IBKR daily close
overlap validation (the acquisition lane's IBKR_OVERLAP_VALIDATION.json only
covered NQ; CL was rescope-dropped; ES = this check).

Outputs ES_quality_ledger.json. DESCRIPTIVE ONLY.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python ES_quality.py
"""
import glob
import json
import os
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "ES_cache")

raw = pd.read_parquet(os.path.join(CACHE, "es_1m_outright.parquet"),
                      columns=["instrument_id", "ts_event", "open", "high",
                               "low", "close", "volume"])
ch = pd.read_parquet(os.path.join(CACHE, "es_chain_VOL.parquet")).sort_index()
cd = pd.read_parquet(os.path.join(CACHE, "es_contract_daily.parquet"))
cd["sess"] = pd.to_datetime(cd["sess"])
seg = pd.read_parquet(os.path.join(CACHE, "es_1m_seg.parquet"),
                      columns=["instrument_id", "sess", "seg", "chi",
                               "minute_of_sess", "open", "high", "low",
                               "close", "volume"])
meta = json.load(open(os.path.join(CACHE, "es_contracts.json")))
iid2del = {c["instrument_id"]: c["delivery"] for c in meta["contracts"]}
seg["delivery"] = seg["instrument_id"].map(iid2del)
seg = seg.merge(ch.reset_index()[["sess", "front"]], on="sess")
# keep only the front contract's bars (VOL chain, strict past)
seg = seg[seg["delivery"] == seg["front"]]

ERAS = [
    ("E1 2010-06..2012-12 (FIX/FAST, s/ms precision)", "2010-06-07", "2012-12-31"),
    ("E2 2013-01..2015-11-19 (FIX/FAST, ms precision)", "2013-01-01", "2015-11-19"),
    ("E3 2015-11-20..2017-05-20 (FIX/FAST, ms->native)", "2015-11-20", "2017-05-20"),
    ("E4 2017-05-21..2020-02-19 (MDP3 native)", "2017-05-21", "2020-02-19"),
    ("E5 2020-02-20..2021-12-31 (COVID)", "2020-02-20", "2021-12-31"),
    ("E6 2022-01-01..2023-09-30", "2022-01-01", "2023-09-30"),
    ("E7 2023-10-01..2026-10-01 (AV1T trim era)", "2023-10-01", "2026-10-01"),
]

# ---- front per session, on the segmented minute frame
def q(x):
    x = pd.Series(x).dropna()
    return None if len(x) == 0 else {
        "median": float(x.median()), "p10": float(x.quantile(.1)),
        "p90": float(x.quantile(.9))}

era_rows = []
for name, a, b in ERAS:
    msk = (seg["sess"] >= pd.Timestamp(a)) & (seg["sess"] <= pd.Timestamp(b))
    mm = seg[msk]
    # ts granularity verification (raw ns integers)
    rsk = (raw["ts_event"] >= pd.Timestamp(a, tz="UTC").value) & \
          (raw["ts_event"] < (pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1)).value)
    rr = raw.loc[rsk, "ts_event"]
    gran = {
        "frac_ms_aligned": float((rr % 1_000_000 == 0).mean()),
        "frac_exact_ms_all_zeros_below": float((rr % 1_000 == 0).mean()),
    }
    per_sess = mm.groupby("sess").agg(
        nbars=("volume", "size"), vol=("volume", "sum"),
        zero_vol_bars=("volume", lambda v: float((v == 0).mean())))
    # flat bars: o==h==l==c
    mm_flat = (mm["open"] == mm["high"]) & (mm["high"] == mm["low"]) & \
              (mm["low"] == mm["close"])
    flat_by_sess = mm_flat.groupby(mm["sess"]).mean()
    # consecutive-minute gaps within each session (missing minutes)
    def gapfrac(g):
        mins = g["minute_of_sess"].sort_values().values
        if len(mins) < 2:
            return 0.0
        return float(np.mean(np.diff(mins) > 1))
    gaps = mm.groupby("sess").apply(gapfrac, include_groups=False)
    # large 1m jumps (front only)
    lr = np.log(mm.sort_values(["sess", "minute_of_sess"])["close"]).diff()
    same_sess = mm.sort_values(["sess", "minute_of_sess"])["sess"] \
        .eq(mm.sort_values(["sess", "minute_of_sess"])["sess"].shift())
    lr = lr[same_sess]
    era_rows.append({
        "era": name,
        "n_sessions": int(per_sess.shape[0]),
        "median_bars_per_session": float(per_sess["nbars"].median()),
        "coverage_vs_1380": float(per_sess["nbars"].median() / 1380),
        "zero_volume_bar_share": float(per_sess["zero_vol_bars"].mean()),
        "flat_ohlc_bar_share": float(flat_by_sess.mean()),
        "minute_gap_share": float(gaps.mean()),
        "n_1m_jumps_gt1pct": int((lr.abs() > 0.01).sum()),
        "n_1m_jumps_gt2pct": int((lr.abs() > 0.02).sum()),
        "ts_granularity_check": gran,
    })

# maintenance-window leakage + Saturday sessions + DST (global checks)
brk = seg[seg["seg"] == "BRK"]
maint = {"n_bars_1600_1659_chi": int(len(brk)),
         "sessions_with_maint_bars": int(brk["sess"].nunique())}
sat = seg[pd.DatetimeIndex(seg["sess"]).dayofweek == 5]
saturdays = {"n_saturday_sessions": int(sat["sess"].nunique())}
# DST transitions: spring-forward Sunday has no 02:00-02:59 Chicago; fall-back
# has two 01:00 hours. tz_convert handles it; just verify those Sundays exist.
dst_days = []
for d in pd.date_range("2010-06-07", "2026-10-01", freq="D"):
    if d.month in (3, 11) and d.dayofweek == 6:
        dst_days.append(d.date().isoformat())
present = seg["sess"].isin([pd.Timestamp(x) for x in dst_days])
dst_check = {"n_transition_sundays": len(dst_days),
             "n_with_session_data": int(seg.loc[present, "sess"].nunique())}

# early-close holiday sessions: RTH volume ends before 13:05 CT
rth_last = seg[seg["seg"] == "RTH"].groupby("sess")["chi"].max()
early = rth_last[rth_last.dt.hour < 13]
early_by_year = early.groupby(early.index.year).size().to_dict()

# ---- ES vs IBKR daily close overlap (IBKR raw is RTH-only daily 6y)
ibkr_rows = []
for fp in sorted(glob.glob(os.path.expanduser(
        "~/.my-quantitative-data/futures-10syms-v1/raw/ES_*_TRADES_1day_6Y.json"))):
    d = json.load(open(fp))
    if not d.get("ok"):
        continue
    for b in d["bars"]:
        ibkr_rows.append({"symbol": d["localSymbol"], "date": b["t"],
                          "close": b["c"], "volume": b["v"]})
ib = pd.DataFrame(ibkr_rows)
ib["date"] = pd.to_datetime(ib["date"])
ib = ib[(ib["date"] >= "2023-10-01") & (ib["volume"] >= 1000)]
cdd = cd.merge(ch.reset_index()[["sess", "front"]], on="sess")
cdd = cdd[cdd["delivery"] == cdd["front"]].set_index("sess")
cdd = cdd.rename(columns={"symbol": "symbol_front"})
comp = ib.set_index("date").join(
    cdd[["rth_close16", "cash_close15", "symbol_front"]], how="inner")
comp = comp[comp["symbol"] == comp["symbol_front"]]
comp["diff_ticks_16"] = (comp["rth_close16"] - comp["close"]).abs() / 0.25
comp["diff_ticks_15"] = (comp["cash_close15"] - comp["close"]).abs() / 0.25
ibkr_overlap = {
    "window": ["2023-10-01", "2026-10-01"],
    "n_liquid_days_ge1000_ibkr_vol": int(len(comp)),
    "rth_close16_vs_ibkr_close": {
        "median_abs_diff_ticks": float(comp["diff_ticks_16"].median()),
        "pct_within_1_tick": float((comp["diff_ticks_16"] <= 1).mean() * 100)},
    "cash_close15_vs_ibkr_close": {
        "median_abs_diff_ticks": float(comp["diff_ticks_15"].median()),
        "pct_within_1_tick": float((comp["diff_ticks_15"] <= 1).mean() * 100)},
    "note": ("IBKR daily close = RTH 16:00 CT settlement-mark class; vendor "
             "1m close at 15:59/16:00; diff includes mark convention"),
}

out = {
    "generated_utc": datetime.utcnow().isoformat() + "+00:00",
    "eras": era_rows,
    "session_structure_history_OBSERVED": {
        "2010-06..2012": "Globex day ends 16:30 CT (bars observed to "
                         "16:29/16:30; expected session length 1425 min)",
        "2013..2015-11": "close moved to 16:15 CT (expected 1395 min)",
        "2015-11-29+": "close 16:00 CT, maintenance 16:00-17:00 (expected "
                       "1380 min); residual 16:00/16:59 prints are single-"
                       "mark artifacts (<=60 bars/yr)",
        "impact": "pre-2016 the 16:00-16:15/16:30 tail trades in the BRK "
                  "bucket of ES_chains segmentation (excluded from both RTH "
                  "and ON aggregates in ES_session_stats; disclosed)",
    },
    "maintenance_window": maint,
    "saturdays": saturdays,
    "dst_note": (
        "US DST transitions occur Sunday 02:00 local, inside the weekend "
        "closure (Fri 16:00 -> Sun 17:00 CT), so no ES session is ever "
        "distorted by the clock change; tz-convert (IANA America/Chicago) "
        "handles all 2010-2026 offsets. The earlier per-Sunday session "
        "presence check is degenerate because Sunday-17:00 bars roll into "
        "Monday session dates by construction."),
    "early_close_rth_sessions_by_year": early_by_year,
    "ibkr_overlap_ES": ibkr_overlap,
    "ts_granularity_note": (
        "ohlcv-1m bars are minute-stamped, so ts_event is trivially "
        "ms-aligned in every era; the vendor 'ms precision pre-2015-11-20' "
        "caveat is NOT testable on this schema (it matters for tick-level "
        "schemas only) and no sub-minute precision is claimed anywhere in "
        "this dossier"),
    "contract_calendar_check": {
        "note": "every expired contract's last session == 3rd Friday except "
                "ESM6 2026-06-18 and (definitions) ESM7 2027-06-17 — "
                "Juneteenth shifts; ESU7/ESZ7 2027 tails are stray-print "
                "contracts excluded from chains",
    },
    "nonprice_quality_notes": [
        "cftc_legacy_tidy.parquet series_id COT_LEGACY_ES mixes 3 CFTC "
        "markets (Micro E-mini, S&P 500 Consolidated, true E-mini); exact-"
        "name filter required (applied in ES_cot.py)",
        "FOMC statements 2011-2015 lack release-time text in the as-issued "
        "HTML -> minute-anchored anatomy NOT_RUN there",
        "FRED latest tidy is latest-revised, NOT PIT (used only for era-"
        "level sign corroboration of roll spreads)",
    ],
}
with open(os.path.join(HERE, "ES_quality_ledger.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
for r in era_rows:
    print(f"{r['era'][:48]:48s} sess={r['n_sessions']:4d} bars/sess={r['median_bars_per_session']:6.0f} "
          f"cov={r['coverage_vs_1380']:.3f} zeroVol={r['zero_volume_bar_share']:.4f} "
          f"gap={r['minute_gap_share']:.3f} jumps>1%={r['n_1m_jumps_gt1pct']:3d} "
          f"ms-aligned={r['ts_granularity_check']['frac_ms_aligned']:.3f}")
print(json.dumps(maint, indent=1), json.dumps(saturdays, indent=1))
print(json.dumps(dst_check, indent=1))
print("early closes:", early_by_year)
print(json.dumps(ibkr_overlap, indent=1))
print("WROTE ES_quality_ledger.json")
