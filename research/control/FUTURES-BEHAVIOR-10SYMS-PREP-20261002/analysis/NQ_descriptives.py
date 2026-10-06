#!/usr/bin/env python
"""NQ_descriptives.py — lane SYMBOL-DOSSIER-NQ, task FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Descriptive statistics ONLY for CME E-mini Nasdaq-100 futures (NQ), computed
from the legal read-only raw snapshot of FUTURES-DATA-10SYMS-V1 at
~/.my-quantitative-data/futures-10syms-v1/raw/ (files NQ_*).

Hard constraints honored:
  - No PnL, no equity curves, no Sharpe/performance metrics, no parameter
    selection, no event studies. Descriptive distribution/window stats only.
  - Any activation/threshold definition uses STRICT PAST/ROLLING windows
    (trailing 20 sessions; never ex-post labels).
  - Conventions fixed a priori and disclosed (not tuned):
      roll rule  = data lane's declared rule (hold until last session BEFORE
                   day-1 of the held contract's delivery month, roll to the
                   next listed contract at that session close);
      returns    = within-contract daily log returns; on a roll date the
                   return belongs to the OLD contract (old_t vs old_{t-1});
                   the new contract's segment starts the NEXT session, so no
                   synthetic stitching jump ever enters the return series.
                   Roll-day adjacent-contract close gaps are reported
                   separately as raw calendar gaps (description, not a cost
                   model).
      multipliers: multiplier=20, minTick=0.25 -> tick value USD 5.00
                   (S1_IDENTITY.json NQ; CME page body text 2026-10-02).

Dataset structure discovered and disclosed (affects every section):
  - Expired NQ contracts' daily files were downloaded with the window ENDING
    at the first day of the delivery month, i.e. data ends exactly at the
    declared roll boundary (e.g. NQU5 last bar 2025-08-29). Consequence:
    the true market volume handoff (which for equity index futures normally
    happens INSIDE the delivery month, in the week before the 3rd-Friday
    expiry) is NOT observable in this snapshot for any completed pair.
  - The earliest downloaded contract NQU5 (delivery 2025-09) is only the TRUE
    front under the declared rule from 2025-05-30 (last session before
    2025-06-01, when NQM5 would have been rolled away); before that the true
    fronts (NQM4..NQM5) are not in the dataset (expired ~1y resolution wall).
    Therefore two windows are reported:
      W1 = full chain window 2024-03-18..2026-10-01: held contract =
           earliest-available dataset contract (a DEFERRED quarterly
           reference before 2025-05-30, settlement-derived bars)
      W2 = true-front window 2025-05-30..2026-10-01 (~16 months)

Output: analysis/NQ_descriptives.json (same directory as this script).
Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python NQ_descriptives.py
"""

import json
import math
import os
from datetime import date, datetime, timezone
from statistics import median

RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NQ_descriptives.json")

MULT = 20.0
MIN_TICK = 0.25
TICK_USD = MULT * MIN_TICK  # 5.00
TODAY = date(2026, 10, 2)  # fetch date of the snapshot (FUTURES-DATA-10SYMS-V1)

# Contract universe from S1_IDENTITY.json (NQ): localSymbol -> (conId, lastTradeDate yyyymmdd, delivery yyyymm)
CONTRACTS = {
    "NQU5": (691171690, "20250919", "202509"),
    "NQZ5": (563947738, "20251219", "202512"),
    "NQH6": (730283097, "20260320", "202603"),
    "NQM6": (750150196, "20260618", "202606"),
    "NQU6": (770561204, "20260918", "202609"),
    "NQZ6": (563947726, "20261218", "202612"),
    "NQH7": (815824270, "20270319", "202703"),
    "NQM7": (840227400, "20270617", "202706"),
    "NQU7": (866514788, "20270917", "202709"),
    "NQZ7": (586139864, "20271217", "202712"),
}
CHAIN = sorted(CONTRACTS, key=lambda s: CONTRACTS[s][2])  # by delivery month
FIRST = CHAIN[0]  # NQU5


def load_daily(sym):
    conid = CONTRACTS[sym][0]
    path = os.path.join(RAW, f"NQ_{sym}_{conid}_TRADES_1day_6Y.json")
    with open(path) as f:
        d = json.load(f)
    assert d["ok"] and d["localSymbol"] == sym
    return {b["t"]: b for b in d["bars"]}, d.get("useRTH")


def dstr(y, m, dd=1):
    return f"{y:04d}-{m:02d}-{dd:02d}"


def first_day_of_delivery(yyyymm):
    return dstr(int(yyyymm[:4]), int(yyyymm[4:]))


def quantile(sorted_vals, q):
    if not sorted_vals:
        return None
    idx = q * (len(sorted_vals) - 1)
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (idx - lo)


def stats(vals):
    if not vals:
        return {"n": 0}
    n = len(vals)
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1) if n > 1 else 0.0
    sd = math.sqrt(var)
    s = sorted(vals)
    m3 = sum((v - mean) ** 3 for v in vals) / n
    m4 = sum((v - mean) ** 4 for v in vals) / n
    return {
        "n": n,
        "mean": round(mean, 6),
        "std": round(sd, 6),
        "min": round(min(vals), 6),
        "q05": round(quantile(s, 0.05), 6),
        "q25": round(quantile(s, 0.25), 6),
        "median": round(quantile(s, 0.50), 6),
        "q75": round(quantile(s, 0.75), 6),
        "q95": round(quantile(s, 0.95), 6),
        "max": round(max(vals), 6),
        "skew": round(m3 / sd**3, 4) if sd > 0 and n > 2 else None,
        "excess_kurtosis": round(m4 / sd**4 - 3.0, 4) if sd > 0 and n > 2 else None,
        "frac_positive": round(sum(1 for v in vals if v > 0) / n, 4),
    }


def main():
    out = {
        "meta": {
            "lane": "SYMBOL-DOSSIER-NQ",
            "task": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
            "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "script": "analysis/NQ_descriptives.py",
            "raw_source": "~/.my-quantitative-data/futures-10syms-v1/raw/ (FUTURES-DATA-10SYMS-V1 snapshot, fetched 2026-10-02, read-only)",
            "conventions": {
                "roll_rule": "declared by data lane: hold until last session BEFORE day-1 of delivery month, roll to next listed contract at that close",
                "returns": "within-contract daily log returns; roll-date return belongs to old contract; no synthetic stitching jump",
                "windows": "W1 = full chain (earliest available contract, deferred reference pre-2025-05-30); W2 = true front under declared rule (from NQU5 promotion 2025-05-30)",
                "activation": "trailing-20-session window (strict past): >=16 of last 20 sessions with v>0",
                "rolling_vol": "trailing 20 log returns, annualized sqrt(252)",
                "multiplier": MULT,
                "min_tick": MIN_TICK,
                "tick_usd": TICK_USD,
            },
            "prohibitions_honored": "no PnL, no performance metrics, no parameter selection, no event studies",
        },
        "caveats": [
            "Daily per-contract bars deeper than each contract's liquid window are close-only volume-0 (settlement-derived): reference/signal price only, NOT a fill price (FUTURES-DATA-10SYMS-V1 finding).",
            "Daily and hourly bars were fetched with useRTH=True (per-file metadata): daily OHLCV and the intraday profile describe the RTH session (08:30-16:00 US/Central); Globex overnight volume share is NOT measurable from this snapshot (NOT_RUN).",
            "Intraday raw files cover only ~30 days (1hour_30D) / 2 days (1min_2D) per contract ending 2026-10-01; no multi-year intraday depth exists on this entitlement (S7_DEPTH_ACTIVE probes n=0 for older end dates).",
            "BID/ASK daily files are end-of-day close snapshots, not synchronous quotes: spread stats are descriptive only and are NOT an executable spread; full-1Y medians are dominated by stale deferred-contract quotes, so last-20-session medians are also reported (S6-comparable).",
            "Expired contracts' files end exactly at the declared roll boundary (day-1 of delivery month minus one session): volume handoff inside the delivery month is unobservable; the 'market roll date' for NQ is NOT_RUN on this data.",
        ],
    }

    # ---------- load daily ----------
    daily, use_rth = {}, {}
    for sym in CHAIN:
        bars, ur = load_daily(sym)
        daily[sym] = bars
        use_rth[sym] = ur

    # ---------- per-contract coverage + activation (strict past window) ----------
    contracts = []
    for sym in CHAIN:
        conid, ltd, deliv = CONTRACTS[sym]
        bars = daily[sym]
        dates = sorted(bars)
        vpos = [t for t in dates if bars[t]["v"] > 0]
        flat = sum(1 for t in dates if bars[t]["v"] == 0 and bars[t]["o"] == bars[t]["h"] == bars[t]["l"] == bars[t]["c"])
        act = None
        for i, t in enumerate(dates):
            if i + 1 < 20:
                continue
            window = dates[i - 19 : i + 1]
            if sum(1 for w in window if bars[w]["v"] > 0) >= 16:
                act = t
                break
        first_100k = next((t for t in dates if bars[t]["v"] >= 100_000), None)
        contracts.append(
            {
                "localSymbol": sym,
                "conId": conid,
                "last_trade_date": ltd,
                "delivery_month": deliv,
                "n_bars": len(dates),
                "first_bar": dates[0],
                "last_bar": dates[-1],
                "n_v_pos": len(vpos),
                "flat_zero_vol_frac": round(flat / len(dates), 4) if dates else None,
                "first_v_pos": vpos[0] if vpos else None,
                "last_v_pos": vpos[-1] if vpos else None,
                "sustained_active_from_20d": act,
                "first_session_v_ge_100k": first_100k,
                "months_first_v_pos_before_delivery": (
                    round((int(deliv[:4]) * 12 + int(deliv[4:]) - (int(vpos[0][:4]) * 12 + int(vpos[0][5:7]))) / 12.0, 1) if vpos else None
                ),
                "total_volume": sum(bars[t]["v"] for t in dates),
                "median_daily_volume_all_v_pos_days": median(bars[t]["v"] for t in vpos) if vpos else None,
                "daily_bars_useRTH": use_rth[sym],
            }
        )
    out["contracts"] = contracts

    # ---------- declared roll dates ----------
    data_last = max(sorted(daily[s])[-1] for s in CHAIN)
    rolls = []
    for old, new in zip(CHAIN, CHAIN[1:]):
        first_day = first_day_of_delivery(CONTRACTS[old][2])
        old_dates = sorted(daily[old])
        candidates = [t for t in old_dates if t < first_day]
        roll_date = max(candidates) if candidates else None
        old_expired = CONTRACTS[old][2] < "202610"
        if old_expired and roll_date == old_dates[-1]:
            status = "completed_boundary (old contract's file ends exactly at the declared roll boundary)"
        elif roll_date == data_last:
            status = f"NOT_COMPUTABLE_YET (old contract still active; dataset ends {data_last}; true roll date is later — gap below is just today's calendar spread, not a roll gap)"
        else:
            status = "completed (roll date within old contract's data window)"
        gap_pts = None
        if roll_date and roll_date in daily[new]:
            gap_pts = daily[new][roll_date]["c"] - daily[old][roll_date]["c"]
        ov = daily[old][roll_date]["v"] if roll_date and roll_date in daily[old] else None
        nv = daily[new][roll_date]["v"] if roll_date and roll_date in daily[new] else None
        rolls.append(
            {
                "old": old,
                "new": new,
                "declared_roll_date": roll_date,
                "old_last_trade": CONTRACTS[old][1],
                "status": status,
                "gap_new_minus_old_close_pts": round(gap_pts, 2) if gap_pts is not None else None,
                "gap_ticks": round(gap_pts / MIN_TICK, 1) if gap_pts is not None else None,
                "gap_usd_per_contract": round(gap_pts * MULT, 2) if gap_pts is not None else None,
                "old_volume_on_roll_date": ov,
                "new_volume_on_roll_date": nv,
                "new_volume_share_on_roll_date": round(nv / (ov + nv), 4) if (ov or nv) else None,
            }
        )
    out["declared_rolls"] = rolls

    # ---------- liquidity migration (volume crossover, OBSERVED) ----------
    migration = []
    for old, new in zip(CHAIN, CHAIN[1:]):
        both = [t for t in sorted(daily[old]) if t in daily[new] and daily[old][t]["v"] > 0 and daily[new][t]["v"] > 0]
        cross = None
        old_dom_last = None
        for t in both:
            if cross is None and daily[new][t]["v"] > daily[old][t]["v"]:
                cross = t
            if daily[old][t]["v"] >= daily[new][t]["v"]:
                old_dom_last = t
        migration.append(
            {
                "pair": f"{old}->{new}",
                "n_days_both_real_volume": len(both),
                "first_crossover_new_vol_gt_old": cross,
                "last_day_old_vol_ge_new": old_dom_last,
                "old_last_real_volume_day": next(c["last_v_pos"] for c in contracts if c["localSymbol"] == old),
                "note": "expired-old files end at the declared roll boundary; new contract's volume while old is alive stays negligible (deferred prints), so the true market handoff inside the delivery month is NOT observable",
            }
        )
    out["migration"] = migration

    # ---------- build declared-rule held (front) series ----------
    roll_date_of = {r["old"]: r["declared_roll_date"] for r in rolls}
    all_dates = sorted(set().union(*[set(daily[s]) for s in CHAIN]))
    u5_promotion = max(t for t in daily[FIRST] if t < "2025-06-01")  # true-front promotion of earliest contract under declared rule
    held = []  # (date, sym, close, v)
    current = FIRST
    for t in all_dates:
        while current in roll_date_of and roll_date_of[current] and t > roll_date_of[current]:
            current = CHAIN[CHAIN.index(current) + 1]
        if t in daily[current]:
            b = daily[current][t]
            held.append((t, current, b["c"], b["v"]))

    real_start = None
    for i in range(len(held)):
        if all(h[3] > 0 for h in held[i:]):
            real_start = held[i][0]
            break
    out["front_series"] = {
        "rule": "declared (calendar) roll; unadjusted closes; contract identity retained",
        "n_sessions": len(held),
        "first": held[0][0],
        "last": held[-1][0],
        "held_contracts_in_order": [s for i, s in enumerate([h[1] for h in held]) if i == 0 or [h[1] for h in held][i - 1] != s],
        "W1_definition": f"{held[0][0]}..{held[-1][0]}: earliest-available-contract chain; before {u5_promotion} the held contract is a DEFERRED quarterly reference (true fronts NQM4..NQM5 absent), bars settlement-derived",
        "W2_definition": f"{u5_promotion}..{held[-1][0]}: TRUE front under declared rule (NQU5 promoted at {u5_promotion} close)",
        "true_front_promotion_of_earliest_contract": u5_promotion,
        "real_volume_continuous_from": real_start,
        "n_zero_volume_held_bars": sum(1 for h in held if h[3] == 0),
        "zero_volume_bars_all_before": max([h[0] for h in held if h[3] == 0], default=None),
    }

    # per-contract held-window volume descriptives (liquidity of the HELD contract)
    held_vols = {}
    for t, sym, c, v in held:
        held_vols.setdefault(sym, []).append((t, v))
    out["held_contract_volume"] = {
        sym: {
            "held_from": vs[0][0],
            "held_to": vs[-1][0],
            "n_sessions": len(vs),
            "median_volume": round(median(v for _, v in vs)),
            "p10_volume": round(quantile(sorted(v for _, v in vs), 0.10)),
            "p90_volume": round(quantile(sorted(v for _, v in vs), 0.90)),
            "frac_sessions_v_ge_100k": round(sum(1 for _, v in vs if v >= 100_000) / len(vs), 3),
        }
        for sym, vs in held_vols.items()
    }

    # ---------- returns within segments (no stitching jump) ----------
    segs = []
    for i, (t, sym, c, v) in enumerate(held):
        if i == 0 or held[i - 1][1] != sym:
            segs.append({"date": t, "contract": sym, "r": None})
            continue
        pc = held[i - 1][2]
        segs.append({"date": t, "contract": sym, "r": math.log(c / pc) if pc > 0 else None})

    def window_stats(start=None, end=None):
        rs = [s["r"] for s in segs if s["r"] is not None and (start is None or s["date"] >= start) and (end is None or s["date"] <= end)]
        return stats(rs)

    def extremes(start):
        cand = [(s["r"], s["date"]) for s in segs if s["r"] is not None and s["date"] >= start]
        if not cand:
            return {}
        top = sorted(cand, key=lambda x: -abs(x[0]))[:3]
        return {d: round(r, 5) for r, d in top}

    out["returns"] = {
        "unit": "daily log return of held contract close (within-contract; roll-day return belongs to old contract)",
        "W1_full_chain_incl_deferred_reference": window_stats(),
        "W2_true_front_only": window_stats(start=u5_promotion),
        "annualized_vol_W1_pct": round(window_stats()["std"] * math.sqrt(252) * 100, 2),
        "annualized_vol_W2_pct": round(window_stats(start=u5_promotion)["std"] * math.sqrt(252) * 100, 2),
        "W2_largest_abs_3_daily_returns": extremes(u5_promotion),
    }

    by_year = {}
    for s in segs:
        if s["r"] is not None:
            by_year.setdefault(s["date"][:4], []).append(s["r"])
    out["returns_by_year_W1_basis"] = {y: stats(v) for y, v in sorted(by_year.items())}

    # ---------- rolling 20-session realized vol (strict past window) ----------
    rs_seq = [(s["date"], s["r"]) for s in segs if s["r"] is not None]
    roll_vols = []
    for i in range(19, len(rs_seq)):
        w = [x[1] for x in rs_seq[i - 19 : i + 1]]
        m = sum(w) / 20
        sd = math.sqrt(sum((x - m) ** 2 for x in w) / 19)
        roll_vols.append((rs_seq[i][0], sd * math.sqrt(252) * 100))
    if roll_vols:
        vols = sorted(v for _, v in roll_vols)
        vmax = max(roll_vols, key=lambda x: x[1])
        vmin = min(roll_vols, key=lambda x: x[1])
        out["rolling_vol_20d"] = {
            "window": "trailing 20 sessions, annualized %, descriptive (W1 basis)",
            "n": len(roll_vols),
            "min_pct": round(vmin[1], 2), "min_date": vmin[0],
            "median_pct": round(quantile(vols, 0.5), 2),
            "max_pct": round(vmax[1], 2), "max_date": vmax[0],
            "latest_pct": round(roll_vols[-1][1], 2), "latest_date": roll_vols[-1][0],
        }

    # ---------- day-of-week / monthly seasonality (true-front window, descriptive) ----------
    dow_v, dow_absr, dow_r = {}, {}, {}
    mon_r, mon_absr, mon_n = {}, {}, {}
    for s, (t, sym, c, v) in zip(segs, held):
        if s["r"] is None or t < u5_promotion:
            continue
        d = date.fromisoformat(t)
        dow = d.strftime("%a")
        dow_v.setdefault(dow, []).append(v)
        dow_absr.setdefault(dow, []).append(abs(s["r"]))
        dow_r.setdefault(dow, []).append(s["r"])
        mon = t[:7]
        mon_r.setdefault(mon, []).append(s["r"])
        mon_absr.setdefault(mon, []).append(abs(s["r"]))
        mon_n[mon] = mon_n.get(mon, 0) + 1
    out["seasonality_dow_true_front_window"] = {
        "window": f"{u5_promotion}..{held[-1][0]} (descriptive means; RTH-session volume per useRTH=True daily bars)",
        "median_volume": {k: round(median(v)) for k, v in dow_v.items()},
        "mean_abs_return_bps": {k: round(sum(v) / len(v) * 1e4, 2) for k, v in dow_absr.items()},
        "mean_return_bps": {k: round(sum(v) / len(v) * 1e4, 2) for k, v in dow_r.items()},
    }
    out["seasonality_monthly_true_front_window"] = {
        "note": "<=2 observations per calendar month cell across ~16 months: description only, NO statistical claim",
        "mean_return_bps": {k: round(sum(v) / len(v) * 1e4, 1) for k, v in mon_r.items()},
        "mean_abs_return_bps": {k: round(sum(v) / len(v) * 1e4, 1) for k, v in mon_absr.items()},
        "n_days": mon_n,
    }

    # ---------- term structure: adjacent calendar spreads ----------
    ts = []
    for old, new in zip(CHAIN, CHAIN[1:]):
        common = [t for t in sorted(daily[old]) if t in daily[new]]
        spreads_all = [daily[new][t]["c"] - daily[old][t]["c"] for t in common]
        common_rv = [t for t in common if daily[old][t]["v"] > 0 and daily[new][t]["v"] > 0]
        spreads_rv = [daily[new][t]["c"] - daily[old][t]["c"] for t in common_rv]
        ts.append(
            {
                "pair": f"{old}-{new}",
                "n_common_days": len(common),
                "first_common": common[0] if common else None,
                "last_common": common[-1] if common else None,
                "spread_new_minus_old_pts_all_common": stats([round(s, 2) for s in spreads_all]),
                "n_common_days_both_real_volume": len(common_rv),
                "spread_pts_both_real_volume": stats([round(s, 2) for s in spreads_rv]),
                "caveat": "bars before the deferred contract's liquid window are settlement-derived (v=0); all_common stats are settlement-basis",
            }
        )
    out["calendar_spreads_adjacent"] = ts

    # ---------- RTH hourly volume profile (last 30D per contract, useRTH=True) ----------
    hour_vol, file_cov = {}, []
    for sym in CHAIN:
        conid = CONTRACTS[sym][0]
        path = os.path.join(RAW, f"NQ_{sym}_{conid}_TRADES_1hour_30D.json")
        with open(path) as f:
            d = json.load(f)
        bars = [b for b in d["bars"] if b["v"] > 0]
        days = sorted(set(b["t"][:10] for b in bars))
        file_cov.append({"localSymbol": sym, "n_bars_v_pos": len(bars), "n_days": len(days), "first": days[0] if days else None, "last": days[-1] if days else None, "useRTH": d.get("useRTH")})
        for b in bars:
            hh = b["t"][11:16]  # local wall clock (offset-verified US/Central per S9)
            hour_vol[hh] = hour_vol.get(hh, 0) + b["v"]
    tot = sum(hour_vol.values())
    out["rth_hourly_profile"] = {
        "window": "1hour_30D files per contract, pooled; v>0 bars only; each file covers its own final ~30 sessions (front or pre-roll for expired)",
        "file_coverage": file_cov,
        "volume_share_by_ct_bar_start": {k: round(v / tot, 4) for k, v in sorted(hour_vol.items())},
        "bar_note": "first RTH bar starts 08:30 CT and covers only 08:30-09:00 (30 min); remaining bars are 60 min on the hour; last bar 15:00-16:00",
        "note": "useRTH=True fetch: covers RTH hours only. Globex overnight share NOT_RUN from this snapshot.",
    }

    # ---------- BID/ASK 1Y end-of-day spread descriptives ----------
    ba = []
    for sym in CHAIN:
        conid = CONTRACTS[sym][0]
        with open(os.path.join(RAW, f"NQ_{sym}_{conid}_BID_1day_1Y.json")) as f:
            bid = json.load(f)
        with open(os.path.join(RAW, f"NQ_{sym}_{conid}_ASK_1day_1Y.json")) as f:
            ask = json.load(f)
        bd = {b["t"]: b["c"] for b in bid["bars"]}
        ad = {b["t"]: b["c"] for b in ask["bars"]}
        common = sorted(set(bd) & set(ad))
        ticks = [(ad[t] - bd[t]) / MIN_TICK for t in common]
        crossed = sum(1 for x in ticks if x < 0)
        s = sorted(x for x in ticks if x >= 0)
        last20 = sorted(x for x in ticks[-20:] if x >= 0)
        ba.append(
            {
                "localSymbol": sym,
                "n_days": len(common),
                "first": common[0] if common else None,
                "last": common[-1] if common else None,
                "median_spread_ticks_full_1y_excl_crossed": round(quantile(s, 0.5), 2) if s else None,
                "median_spread_ticks_last20_excl_crossed": round(quantile(last20, 0.5), 2) if last20 else None,
                "median_spread_usd_last20_excl_crossed": round(quantile(last20, 0.5) * TICK_USD, 2) if last20 else None,
                "p90_spread_ticks_full_1y_excl_crossed": round(quantile(s, 0.9), 2) if s else None,
                "n_crossed_ask_lt_bid": crossed,
            }
        )
    out["bid_ask_daily_1y"] = {
        "caveat": "end-of-day close snapshots, non-synchronous, NOT an executable spread; full-1Y median is dominated by stale deferred-contract days; last-20-session median is the S6-comparable number (S6 front NQZ6 20-day median 6.5 ticks = USD 32.5)",
        "per_contract": ba,
    }

    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print("written:", OUT)
    print("u5_promotion(true front from):", u5_promotion, "| real_volume_continuous_from:", real_start)


if __name__ == "__main__":
    main()
