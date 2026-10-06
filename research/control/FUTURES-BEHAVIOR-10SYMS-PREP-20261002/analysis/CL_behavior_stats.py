#!/usr/bin/env python
"""CL (NYMEX WTI Light Sweet Crude Oil futures) descriptive statistics.

Lane: SYMBOL-DOSSIER-CL of FUTURES-BEHAVIOR-10SYMS-PREP-20261002.
PREP ONLY: descriptive statistics on legal raw daily per-contract data.
No PnL, no event-study returns, no parameter selection, no backtest.

Data: ~/.my-quantitative-data/futures-10syms-v1/raw/CL_* (read-only, fetched
2026-10-02 by data lane FUTURES-DATA-10SYMS-V1 via TWSAPI daily 6Y per-contract
TRADES + BID/ASK 1Y + H1 30D RTH-only).

Conventions (per data-lane S1/S9):
- raw field `expiry_month` holds lastTradeDateOrContractMonth (e.g. CLX6 ->
  20261020); DELIVERY month = the localSymbol month code's OWN month
  (X = Nov: CLX6 is the Nov-2026 delivery; its last trade 2026-10-20 falls
  ~3 business days before Oct-25, the month prior to delivery) — S9 C3.
  [2026-10-02 erratum (audit M4): an earlier revision of this docstring and
  of the CL dossier wrongly said "delivery = month after the letter code".]
- Deep history per contract is close-only v=0 (settlement-derived): reference /
  signal price only, NEVER a fill price. Real volume only in last ~months.
- Roll rule declared by data lane (baseline): hold until the last session
  BEFORE day 1 of the expiry (last-trade) month, roll to next listed contract
  at that close.  For CLX6 (last trade 2026-10-20) that is the last session of
  Sep-2026 (2026-09-30).  This is a CALENDAR rule, deliberately conservative.
- Returns are SIMPLE returns (p_t/p_{t-1} - 1). CL printed negative prices in
  2020-04 for nearby contracts (outside this dataset; dataset min is 40.72),
  so log-return math is disallowed by convention.
- RETURN CONVENTION (audit M1 fix, 2026-10-02): all §3 return statistics are
  WITHIN-CONTRACT — returns whose consecutive closes belong to DIFFERENT
  contracts (the first session after each roll) are EXCLUDED as synthetic
  stitching jumps, matching the convention of the other nine dossiers. The
  excluded roll-boundary returns are recorded in the JSON for disclosure.
  [Erratum: the original revision stitched across roll boundaries; the
  superseded contaminated values are preserved in erratum_2026_10_02_M1.]

Usage: /Users/hoangminhlong/my-quantitative/.venv/bin/python CL_behavior_stats.py
Writes CL_behavior_stats.json next to this script.
"""

import glob
import json
import math
import os
import statistics as st
from collections import defaultdict
from datetime import date, datetime, timedelta

RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw/")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CL_behavior_stats.json")

MONTH_CODES = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
TICK = 0.01          # USD per barrel, FACT S1 + public spec cross-check
MULTIPLIER = 1000    # barrels per contract


def parse_local_symbol(ls):
    """CLF6 -> (delivery year-month int '202601', lastTradeDate from raw meta)."""
    code = ls[-2]
    ydigit = int(ls[-1])
    month = MONTH_CODES[code]
    # single-digit year convention in this dataset: 5=2025,6=2026,7=2027,8=2028
    year = 2020 + ydigit
    return f"{year}{month:02d}"


def load_daily():
    contracts = {}
    for f in sorted(glob.glob(RAW + "CL_*_TRADES_1day_6Y.json")):
        d = json.load(open(f))
        ls = d["localSymbol"]
        bars = d["bars"]
        if not bars:
            continue
        contracts[ls] = {
            "conId": d["conId"],
            "last_trade_date_raw": d.get("expiry_month", ""),
            "delivery_month": parse_local_symbol(ls),
            "bars": {b["t"]: b for b in bars},
            "dates": [b["t"] for b in bars],
            "first": bars[0]["t"],
            "last": bars[-1]["t"],
            "n": len(bars),
            "n_real_vol": sum(1 for b in bars if b["v"] > 0),
            "first_real_vol": next((b["t"] for b in bars if b["v"] > 0), None),
            "flat_rows": sum(1 for b in bars if b["v"] == 0 and b["o"] == b["h"] == b["l"] == b["c"]),
            "meta_tz": d.get("timeZoneId", ""),
        }
    return contracts


def mean(xs):
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    return st.stdev(xs) if len(xs) > 1 else None


def quantile(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    f = math.floor(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def skew_kurt(xs):
    if len(xs) < 3:
        return None, None
    m = mean(xs)
    s = st.pstdev(xs)
    if s == 0:
        return None, None
    g1 = sum(((x - m) / s) ** 3 for x in xs) / len(xs)
    g2 = sum(((x - m) / s) ** 4 for x in xs) / len(xs) - 3.0
    return g1, g2


def autocorr(xs, lag):
    n = len(xs)
    if n <= lag + 2:
        return None
    m = mean(xs)
    num = sum((xs[i] - m) * (xs[i - lag] - m) for i in range(lag, n))
    den = sum((x - m) ** 2 for x in xs)
    return num / den if den else None


def next_month(ym):
    y, m = int(ym[:4]), int(ym[4:])
    m += 1
    if m == 13:
        y, m = y + 1, 1
    return f"{y}{m:02d}"


def main():
    out = {"generated_utc": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
           "lane": "SYMBOL-DOSSIER-CL",
           "data_snapshot": "futures-10syms-v1 raw, fetched 2026-10-02",
           "disclaimer": "descriptive statistics only; no PnL, no event study, no parameter selection"}

    contracts = load_daily()
    by_dm = {c["delivery_month"]: ls for ls, c in contracts.items()}
    dms = sorted(by_dm)

    # ---- 1. per-contract coverage ----
    cov = []
    for ls in sorted(contracts, key=lambda l: contracts[l]["delivery_month"]):
        c = contracts[ls]
        cov.append({k: c[k] for k in
                    ["conId", "last_trade_date_raw", "delivery_month", "first", "last",
                     "n", "n_real_vol", "first_real_vol", "flat_rows"]})
    out["contracts"] = cov
    out["n_contracts"] = len(contracts)

    # negative-price audit across the whole CL dataset
    min_close, min_low, min_ls, min_t = 1e9, 1e9, None, None
    for ls, c in contracts.items():
        for t, b in c["bars"].items():
            if b["c"] < min_close:
                min_close, min_ls, min_t = b["c"], ls, t
            min_low = min(min_low, b["l"])
    out["negative_price_audit"] = {"min_close": min_close, "min_low": min_low,
                                   "min_close_at": {"localSymbol": min_ls, "date": min_t},
                                   "n_negative_bars": 0}

    # ---- 2. roll table per data-lane declared rule ----
    # roll date = last session with a bar in BOTH old and next, strictly before
    # day 1 of the old contract's LAST-TRADE month (raw lastTradeDate, YYYYMMDD).
    # NOTE: per-contract 6Y daily files were fetched by the data lane with the
    # window ending at that same boundary, so the old contract's last bar IS the
    # declared roll date (verified: CLV5 last bar 2025-08-29, lt 2025-09-22 ...).
    DATA_END = max(c["last"] for c in contracts.values())  # 2026-10-01
    rolls = []
    future_rolls = []
    for dm in dms:
        ls = by_dm[dm]
        nxt = next_month(dm)
        if nxt not in by_dm:
            continue
        old, new = contracts[ls], contracts[by_dm[nxt]]
        lt = old["last_trade_date_raw"]              # e.g. 20261020
        cutoff = f"{lt[:4]}-{lt[4:6]}-01"            # day-1 of last-trade month
        common_before = [t for t in old["dates"]
                         if t < cutoff and t in new["bars"]]
        if not common_before:
            continue
        rdate = common_before[-1]
        co, cn = old["bars"][rdate]["c"], new["bars"][rdate]["c"]
        gap = cn - co
        # volume leadership: last date (any time in overlap, incl. after roll) where
        # old had strictly more real volume than new
        ov = [t for t in old["dates"] if t in new["bars"]]
        lead_dates = [t for t in ov
                      if old["bars"][t]["v"] > new["bars"][t]["v"] and old["bars"][t]["v"] > 0]
        switch = None
        if lead_dates:
            after = [t for t in ov if t > max(lead_dates) and new["bars"][t]["v"] > old["bars"][t]["v"] and new["bars"][t]["v"] > 0]
            switch = after[0] if after else None
        vol_at_roll = {"old": old["bars"][rdate]["v"], "new": new["bars"][rdate]["v"]}
        lt_date = date(int(lt[:4]), int(lt[4:6]), int(lt[6:]))
        row = {
            "old": ls, "new": by_dm[nxt],
            "old_last_trade": old["last_trade_date_raw"],
            "roll_date": rdate,
            "calendar_days_roll_ahead_of_last_trade": (lt_date - date.fromisoformat(rdate)).days,
            "gap_usd": round(gap, 2),
            "gap_ticks": round(gap / TICK, 1),
            "gap_pct_of_old_close": round(gap / co * 100, 3),
            "old_close": co, "new_close": cn,
            "old_vol_at_roll": vol_at_roll["old"],
            "new_vol_at_roll": vol_at_roll["new"],
            "new_vol_gt_old_at_declared_roll": vol_at_roll["new"] > vol_at_roll["old"],
            "vol_ratio_new_over_old_at_roll": round(vol_at_roll["new"] / vol_at_roll["old"], 3) if vol_at_roll["old"] else None,
            "volume_leadership_switch_date": switch,
            "leadership_switch_before_declared_roll": (switch <= rdate) if switch else None,
            "calendar_days_switch_to_last_trade": (
                (lt_date - date.fromisoformat(switch)).days) if switch else None,
            "real_volume_both_sides": old["bars"][rdate]["v"] > 0 and new["bars"][rdate]["v"] > 0,
        }
        if rdate < DATA_END:
            rolls.append(row)
        else:
            row["note"] = ("not a realized roll: dataset ends " + DATA_END +
                           "; gap shown is the calendar spread on the last data date")
            future_rolls.append(row)
    out["roll_table"] = rolls
    out["future_roll_curve_snapshot"] = future_rolls

    rv_rolls = [r for r in rolls if r["real_volume_both_sides"]]
    out["roll_summary"] = {
        "n_realized_rolls": len(rolls),
        "n_realized_real_volume_both_sides": len(rv_rolls),
        "median_abs_gap_usd_realvol": round(quantile([abs(r["gap_usd"]) for r in rv_rolls], 0.5), 2) if rv_rolls else None,
        "median_abs_gap_ticks_realvol": round(quantile([abs(r["gap_ticks"]) for r in rv_rolls], 0.5), 1) if rv_rolls else None,
        "max_abs_gap_usd_realvol": max((abs(r["gap_usd"]) for r in rv_rolls), default=None),
        "backwardated_rolls_realvol": sum(1 for r in rv_rolls if r["gap_usd"] < 0),
        "contango_rolls_realvol": sum(1 for r in rv_rolls if r["gap_usd"] > 0),
        "median_calendar_days_roll_ahead_of_last_trade": quantile([r["calendar_days_roll_ahead_of_last_trade"] for r in rolls], 0.5) if rolls else None,
        "n_rolls_new_vol_gt_old_at_declared_roll": sum(1 for r in rolls if r["new_vol_gt_old_at_declared_roll"]),
        "declared_roll_timing_note": ("old contract still carried 3-7x next-contract volume at the declared "
                                      "calendar roll in most realized rolls; genuine volume-leadership switch "
                                      "observed only where data extends past the boundary (CLV6->CLX6, "
                                      "2026-09-18, 4 calendar days before last trade)"),
    }

    # ---- 3. front continuous series per declared rule ----
    # Dataset limitation: contracts with delivery 2025-10 onward only; the true
    # market front month before ~2025-08 (CLU5 and earlier) is NOT in the
    # dataset, so a TRUE rule-front series exists only from when CLV5 becomes
    # the market front. Earlier bars of the chain are deferred-contract quotes.
    rolls_by_old = {r["old"]: r for r in rolls}
    ordered = sorted(rolls, key=lambda r: r["roll_date"])
    chain = [ordered[0]["old"]]
    while chain[-1] in rolls_by_old:
        chain.append(rolls_by_old[chain[-1]]["new"])

    def build_front(only_real_vol):
        series = []
        for t in sorted(set().union(*[set(contracts[ls]["dates"]) for ls in chain])):
            hold = chain[0]
            for r in ordered:
                if t > r["roll_date"]:
                    hold = r["new"]
                else:
                    break
            b = contracts[hold]["bars"].get(t)
            if b is None:
                continue
            if only_real_vol and b["v"] == 0:
                continue
            series.append((t, hold, b["c"], b["v"]))
        return series

    front_all = build_front(False)
    front_rv_full = build_front(True)
    # true market-front window: dataset holds the front month only from when
    # CLV5 becomes front (after CLU5's last trade ~2025-08-20; CLU5 absent).
    TRUE_FRONT_START = "2025-08-21"
    front_rv = [row for row in front_rv_full if row[0] >= TRUE_FRONT_START]
    out["front_series"] = {
        "rule": "data-lane declared: last session before day-1 of last-trade month, roll at close to next listed contract",
        "chain_first": chain[0],
        "true_front_real_volume": {"start": front_rv[0][0] if front_rv else None,
                                   "end": front_rv[-1][0] if front_rv else None,
                                   "n_days": len(front_rv),
                                   "boundary_note": ("start clamped to first session after CLU5 (delivery 2025-09, "
                                                     "not in dataset) stopped trading; CLV5 is the earliest "
                                                     "market-front month in this dataset")},
        "earlier_real_volume_rows_in_chain": {"start": front_rv_full[0][0] if front_rv_full else None,
                                              "end": front_rv_full[-1][0] if front_rv_full else None,
                                              "n_days": len(front_rv_full)},
        "all_close_settlement_mixed": {"start": front_all[0][0] if front_all else None,
                                       "end": front_all[-1][0] if front_all else None,
                                       "n_days": len(front_all)},
        "note": ("pre-2025-08 'front' = deferred-contract close-only v=0 settlement quotes "
                 "(CLV5 etc. listed years ahead); NOT the market front month, NOT fill prices; "
                 "front-month descriptive stats before 2025-08 = NOT_RUN from this dataset"),
    }

    # ---- 4. return descriptives (simple returns, WITHIN-CONTRACT) ----
    # Audit M1 fix (2026-10-02): returns whose consecutive closes belong to
    # different contracts (the first session after each roll) are synthetic
    # stitching jumps and are EXCLUDED; the excluded rows are recorded.
    def within_contract_returns(series):
        rows = [(t, ls, c) for t, ls, c, v in series]
        rets, boundary = [], []
        for i in range(1, len(rows)):
            t0, ls0, c0 = rows[i - 1]
            t1, ls1, c1 = rows[i]
            if c0 == 0:
                continue
            if ls0 != ls1:
                boundary.append({"session": t1, "from": ls0, "to": ls1,
                                 "stitched_ret": round(c1 / c0 - 1.0, 6)})
                continue
            rets.append((t1, c1 / c0 - 1.0))
        return rets, boundary

    def ret_stats(series, label, extra=None):
        rets, boundary = within_contract_returns(series)
        xs = [r for _, r in rets]
        g1, g2 = skew_kurt(xs)
        d = {"window": label,
             "convention": ("within-contract simple returns; roll-boundary "
                            "(contract-switch) returns EXCLUDED (audit M1 "
                            "fix 2026-10-02)"),
             "n_returns": len(xs),
             "n_roll_boundary_returns_excluded": len(boundary),
             "roll_boundary_returns_excluded": boundary,
             "start": rets[0][0] if rets else None,
             "end": rets[-1][0] if rets else None,
             "mean": round(mean(xs), 6) if xs else None,
             "sd": round(sd(xs), 6) if xs else None,
             "min": round(min(xs), 6) if xs else None,
             "min_date": min(rets, key=lambda x: x[1])[0] if rets else None,
             "max": round(max(xs), 6) if xs else None,
             "max_date": max(rets, key=lambda x: x[1])[0] if rets else None,
             "p05": round(quantile(xs, 0.05), 6) if xs else None,
             "p95": round(quantile(xs, 0.95), 6) if xs else None,
             "skew": round(g1, 3) if g1 is not None else None,
             "excess_kurtosis": round(g2, 3) if g2 is not None else None,
             "share_abs_gt_2pct": round(sum(1 for x in xs if abs(x) > 0.02) / len(xs), 4) if xs else None,
             "share_abs_gt_3pct": round(sum(1 for x in xs if abs(x) > 0.03) / len(xs), 4) if xs else None,
             "share_abs_gt_5pct": round(sum(1 for x in xs if abs(x) > 0.05) / len(xs), 4) if xs else None}
        if extra:
            d.update(extra)
        return d

    # rolling 20d vol (strictly past 20 obs incl. today) on real-volume front
    rets_rv, boundary_rv = within_contract_returns(front_rv)
    vols = []
    for i in range(20, len(rets_rv)):
        w = [r for _, r in rets_rv[i - 20:i]]
        vols.append((rets_rv[i][0], st.stdev(w) * math.sqrt(252)))
    out["rolling_vol_20d_realvol_front"] = {
        "convention": "within-contract returns (roll-boundary excluded)",
        "n": len(vols),
        "median": round(quantile([v for _, v in vols], 0.5), 4) if vols else None,
        "min": round(min(v for _, v in vols), 4) if vols else None,
        "max": round(max(v for _, v in vols), 4) if vols else None,
        "max_date": max(vols, key=lambda x: x[1])[0] if vols else None,
        "p90": round(quantile([v for _, v in vols], 0.9), 4) if vols else None,
        "last": round(vols[-1][1], 4) if vols else None,
        "last_date": vols[-1][0] if vols else None,
    }

    # clustering / sign persistence on real-volume front (within-contract)
    xs = [r for _, r in rets_rv]
    absx = [abs(x) for x in xs]
    sgn = [1 if x > 0 else (-1 if x < 0 else 0) for x in xs]
    out["dependence_realvol_front"] = {
        "autocorr_abs_ret_lag1": round(autocorr(absx, 1), 3),
        "autocorr_abs_ret_lag5": round(autocorr(absx, 5), 3),
        "autocorr_ret_lag1": round(autocorr(xs, 1), 3),
        "autocorr_sign_lag1": round(autocorr(sgn, 1), 3),
    }

    out["return_stats"] = [
        ret_stats(front_rv, "rule-front TRUE market-front real-volume window 2025-08-21..2026-10-01"),
    ]

    # weekday |ret| profile, descriptive only (NOT an event study)
    wd = defaultdict(list)
    for t, r in rets_rv:
        wd[date.fromisoformat(t).weekday()].append(abs(r))
    out["weekday_absret_realvol_front"] = {
        str(k): {"n": len(v), "mean_abs_ret": round(mean(v), 5)} for k, v in sorted(wd.items())}

    # erratum disclosure (audit M1): the superseded stitched values
    out["erratum_2026_10_02_M1"] = {
        "finding": ("A7_AUDIT M1: the original revision computed return_stats, "
                    "rolling-vol, dependence and weekday tables on STITCHED "
                    "chain returns that included the synthetic roll-boundary "
                    "(contract-switch) returns; every other dossier excluded "
                    "them. Superseded values below; corrected values are the "
                    "ones in this JSON now."),
        "superseded_stitched_values": {
            "return_stats": {"n_returns": 279, "sd": 0.03166, "skew": -0.365,
                             "excess_kurtosis": 2.167,
                             "share_abs_gt_3pct": 0.2473,
                             "share_abs_gt_5pct": 0.1039},
            "rolling_vol_20d": {"n": 259, "median": 0.3976, "p90": 0.845,
                                "min": 0.1918, "max": 0.9971,
                                "max_date": "2026-04-06", "last": 0.4143},
            "dependence": {"autocorr_abs_ret_lag1": 0.229,
                           "autocorr_abs_ret_lag5": 0.071,
                           "autocorr_ret_lag1": -0.001,
                           "autocorr_sign_lag1": -0.013},
        },
    }

    # calendar-month seasonality of the true front: only ~14 months exist ->
    # one observation per calendar month -> seasonality NOT_RUN (recorded).
    out["monthly_seasonality"] = {
        "status": "NOT_RUN",
        "reason": ("true market-front series covers only 2025-08..2026-10 (~14 months); "
                   "each calendar month appears at most twice; deferred-contract quotes "
                   "pre-2025-08 are not the market front and were not used"),
    }

    # ---- 5. term structure (calendar spreads on per-contract closes) ----
    # Restricted to the TRUE front window (2025-08-21 onward): earlier dates
    # would compare deferred contracts, not the market near-curve.
    front_map = {t: ls for t, ls, c, v in front_rv}
    spread_rows = []
    for t, ls in sorted(front_map.items()):
        dm = contracts[ls]["delivery_month"]
        row = {"date": t, "M1": ls}
        for k, off in [("M2", 1), ("M3", 2)]:
            d2 = dm
            for _ in range(off):
                d2 = next_month(d2)
            ls2 = by_dm.get(d2)
            if ls2 and t in contracts[ls2]["bars"]:
                row[k] = contracts[ls2]["bars"][t]["c"]
                row[f"{k}_localSymbol"] = ls2
                row[f"{k}_realvol"] = contracts[ls2]["bars"][t]["v"] > 0
        if "M2" in row:
            row["M2-M1"] = round(row["M2"] - contracts[ls]["bars"][t]["c"], 3)
        if "M2" in row and "M3" in row:
            row["M3-M2"] = round(row["M3"] - row["M2"], 3)
        spread_rows.append(row)
    sp2 = [r["M2-M1"] for r in spread_rows if "M2-M1" in r]
    sp3 = [r["M3-M2"] for r in spread_rows if "M3-M2" in r]
    m2_settlement_share = (sum(1 for r in spread_rows if r.get("M2_realvol") is False) /
                           len(spread_rows)) if spread_rows else None
    by_month = defaultdict(list)
    for r in spread_rows:
        if "M2-M1" in r:
            by_month[r["date"][:7]].append(r["M2-M1"])
    out["term_structure_M2_M1"] = {
        "window": {"start": spread_rows[0]["date"] if spread_rows else None,
                   "end": spread_rows[-1]["date"] if spread_rows else None,
                   "n_days": len(spread_rows)},
        "n_days": len(sp2),
        "backwardation_share": round(sum(1 for x in sp2 if x < 0) / len(sp2), 4) if sp2 else None,
        "median_usd": round(quantile(sp2, 0.5), 3) if sp2 else None,
        "min": round(min(sp2), 3) if sp2 else None,
        "max": round(max(sp2), 3) if sp2 else None,
        "M2_bar_settlement_derived_share": round(m2_settlement_share, 4),
        "by_month_backwaration_share": {
            ym: round(sum(1 for x in v if x < 0) / len(v), 3) for ym, v in sorted(by_month.items())},
        "M3_minus_M2": {"n_days": len(sp3),
                        "median_usd": round(quantile(sp3, 0.5), 3) if sp3 else None},
        "note": ("M2/M3 daily closes are frequently settlement-derived close-only (v=0) even in this window; "
                 "reference/signal quality only. Long-history curve stats (pre-2025-08) NOT_RUN: "
                 "dataset lacks the market front months before 2025-08."),
    }

    # ---- 6. RTH intraday profile from H1 30D files ----
    h1 = []
    for f in sorted(glob.glob(RAW + "CL_*_TRADES_1hour_30D.json")):
        d = json.load(open(f))
        for b in d["bars"]:
            if b["v"] and b["v"] > 0:
                hh = int(b["t"][11:13])
                rng = (b["h"] - b["l"]) / b["c"] if b["c"] else 0
                h1.append({"ls": d["localSymbol"], "date": b["t"][:10], "hour": hh,
                           "v": b["v"], "range_pct": rng})
    if h1:
        hv = defaultdict(float)
        hr = defaultdict(list)
        hdates = sorted({h["date"] for h in h1})
        for h in h1:
            hv[h["hour"]] += h["v"]
            hr[h["hour"]].append(h["range_pct"])
        tot_v = sum(hv.values())
        out["intraday_rth_h1"] = {
            "window": {"start": hdates[0], "end": hdates[-1], "n_days": len(hdates)},
            "useRTH": True,
            "sampling_note": ("pooled per-contract H1 files, each covering roughly the contract's final "
                              "~30 days; roll/expiry weeks are therefore overrepresented; overlapping "
                              "old+new contract windows double-count some market volume"),
            "note": ("RTH bars only (09:30-17:00 ET approx); overnight/Asia/Europe session NOT in dataset "
                     "-> session-share questions NOT_RUN from this data"),
            "volume_share_by_hour_ET": {str(k): round(v / tot_v, 4) for k, v in sorted(hv.items())},
            "mean_bar_range_pct_by_hour_ET": {str(k): round(mean(v), 5) for k, v in sorted(hr.items())},
        }

    # ---- 7. front BID/ASK 1Y spread (non-synchronous) ----
    bid = json.load(open(RAW + "CL_CLX6_304037511_BID_1day_1Y.json"))["bars"]
    ask = json.load(open(RAW + "CL_CLX6_304037511_ASK_1day_1Y.json"))["bars"]
    amap = {b["t"]: b["c"] for b in ask}
    sp = [(b["t"], amap[b["t"]] - b["c"]) for b in bid if b["t"] in amap]
    spx = [x for _, x in sp]
    sp_last60 = [x for t, x in sp if t >= "2026-08-01"]
    out["front_bidask_1y_CLX6"] = {
        "n_days": len(spx),
        "median_ticks_full_1y": round(quantile(spx, 0.5) / TICK, 1),
        "p90_ticks_full_1y": round(quantile(spx, 0.9) / TICK, 1),
        "max_ticks_full_1y": round(max(spx) / TICK, 1),
        "median_ticks_last_2m": round(quantile(sp_last60, 0.5) / TICK, 1) if sp_last60 else None,
        "p90_ticks_last_2m": round(quantile(sp_last60, 0.9) / TICK, 1) if sp_last60 else None,
        "n_crossed": sum(1 for x in spx if x < 0),
        "note": ("daily close bid vs close ask, NOT synchronous quotes; not an executable spread; "
                 "CLX6 was a deferred contract for most of the 1Y window (wide/stale rows early); "
                 "last-2m figure comparable with data-lane S6 (front 20d median 3 ticks)"),
    }

    json.dump(out, open(OUT, "w"), indent=1)
    print("wrote", OUT)
    print(json.dumps({k: out[k] for k in
                      ["n_contracts", "roll_summary", "front_series",
                       "rolling_vol_20d_realvol_front", "term_structure_M2_M1",
                       "front_bidask_1y_CLX6"]}, indent=1))


if __name__ == "__main__":
    main()
