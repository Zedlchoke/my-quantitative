#!/usr/bin/env python
"""A3 — term structure + rolls + calendar-spread anatomy — lane DEEP-6A.

Descriptive ONLY; no PnL, no tradable-cost claims.

Blocks (all OBSERVED with script+window):
  1. quarterly-chain rolls 2020-2026 (~27 rolls, declared calendar rule,
     quarterly adaptation): per-roll table with roll-session close gap
     (new - old, ticks/USD/annualized), both-side volumes around the roll,
     volume crossover session, old-side decay AFTER roll (now observable on
     vendor data — v1's old-side truncation is gone), new-side ramp to
     front-scale (>=10k lots/day);
  2. roll gap vs RBA cash rate - US effective Fed funds differential at each
     roll date (CIP check). Rate series: RBA cash rate target table (rba.gov.au
     gate HTML, nonprice corpus, as-published decisions); US side FRED DFF
     'latest' CSV (ALFRED vintages are year-end-only in this corpus -> latest
     vintage used, CIP vintage caveat DISCLOSED). Sign-match + magnitude table;
  3. curve snapshots (quarterly ladder closes) on fixed sample dates incl
     COVID week, 2021 peak, 2022 USD-shock, 2024-01, 2026-10-01;
  4. calendar-spread instrument anatomy (SEPARATE — negative prices live
     here): negative-bar counts by era (dispatch said 5,067 — re-measured),
     which spreads print negative closes and when, near-minus-far sign in
     curve terms, spread mark vs outright-implied consistency;
  5. serial vs quarterly liquidity on vendor data (v1 H3 re-measure):
     median daily volume by contract class and roll-window position.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_a3_term.py
Writes: 6A_a3_term.json
"""
from __future__ import annotations

import importlib.util
import os

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "sixA_deep_lib", os.path.join(_HERE, "6A_deep_lib.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

OUT = os.path.join(_HERE, "6A_a3_term.json")


def load_dff() -> pd.DataFrame:
    """US effective fed funds rate, FRED 'latest' CSV in nonprice corpus."""
    f = f"{L.NONPRICE}/fred_alfred/latest/DFF_latest.csv"
    d = pd.read_csv(f)
    col_date = d.columns[0]
    col_val = [c for c in d.columns if c.upper().startswith("DFF")][0]
    d = d[[col_date, col_val]].dropna()
    d["date"] = pd.to_datetime(d[col_date])
    d["dff"] = pd.to_numeric(d[col_val], errors="coerce")
    return d[["date", "dff"]].sort_values("date").reset_index(drop=True)


def main():
    sess = pd.read_parquet(f"{L.CACHE}/session_contract.parquet")
    sess = sess[~sess["contract"].str.startswith("STRAY")]
    sess["session_date"] = pd.to_datetime(sess["session_date"])
    reg = pd.read_parquet(f"{L.CACHE}/registry.parquet")
    chain = L.calendar_chain(sess, quarterly_only=True)
    chain["session_date"] = pd.to_datetime(chain["session_date"])
    ch = chain.merge(sess, left_on=["session_date", "held"],
                     right_on=["session_date", "contract"],
                     suffixes=("", "_c"), how="left")
    ch = ch.sort_values("session_date").reset_index(drop=True)
    ch["roll_flag"] = ch["held"] != ch["held"].shift(1)

    out = {"meta": {
        "lane": "DEEP-6A", "analysis": "A3 term structure/rolls",
        "window": [str(ch["session_date"].min().date()), str(ch["session_date"].max().date())],
        "laws": "descriptive only; gaps are adjacent-contract close differences, NOT tradable costs",
    }}

    # ---- 1. rolls table ------------------------------------------------------
    rolls = []
    idx = ch.index[ch["roll_flag"]][1:]      # skip first session
    wide = sess.pivot_table(index="session_date", columns="contract",
                            values="volume", aggfunc="sum").sort_index()
    closes = sess.pivot_table(index="session_date", columns="contract",
                              values="close_px", aggfunc="last").sort_index()
    for i in idx:
        d_new = ch.loc[i, "session_date"]
        new = ch.loc[i, "held"]
        old = ch.loc[i - 1, "held"]
        if old not in closes.columns or new not in closes.columns:
            continue
        co = closes.loc[d_new, old] if d_new in closes.index and pd.notna(
            closes.loc[d_new].get(old)) else None
        cn = closes.loc[d_new, new] if d_new in closes.index and pd.notna(
            closes.loc[d_new].get(new)) else None
        gap_ticks = (cn - co) / L.TICK if (co is not None and cn is not None) else None
        # days held until next roll for annualization
        nxt = ch.loc[i:, "session_date"]
        span_days = None
        for j in range(i + 1, len(ch)):
            if ch.loc[j, "roll_flag"]:
                span_days = (ch.loc[j, "session_date"] - d_new).days
                break
        if span_days is None:
            span_days = (ch["session_date"].max() - d_new).days
        ann_pct = None
        if gap_ticks is not None and co:
            ann_pct = float(gap_ticks * L.TICK / co * 365.0 / max(span_days, 1) * 100)
        # migration metrics around roll
        post = wide.loc[d_new:]
        crossover = None
        old_decay_last10 = None
        ramp_days = None
        if old in wide.columns and new in wide.columns:
            both = post[[old, new]].dropna(how="all").fillna(0)
            cross = both[both[new] > both[old]]
            if len(cross):
                crossover = str(cross.index[0].date())
            oldpost = post[old].dropna().head(10)
            old_decay_last10 = float(oldpost.median()) if len(oldpost) else None
            newvol = post[new].dropna()
            big = newvol[newvol >= 10000]
            if len(big):
                ramp_days = int((newvol.index[newvol >= 10000][0] - d_new).days)
        rolls.append({
            "roll_session": str(d_new.date()), "old": old, "new": new,
            "old_close_usd": (L.px(co) if co is not None else None),
            "new_close_usd": (L.px(cn) if cn is not None else None),
            "gap_ticks": (float(gap_ticks) if gap_ticks is not None else None),
            "gap_usd_per_contract": (float(gap_ticks * 5.0) if gap_ticks is not None else None),
            "gap_ann_pct": ann_pct,
            "vol_old_on_roll": (float(wide.loc[d_new].get(old, np.nan))
                                if d_new in wide.index else None),
            "vol_new_on_roll": (float(wide.loc[d_new].get(new, np.nan))
                                if d_new in wide.index else None),
            "volume_crossover_session": crossover,
            "old_med_vol_10sess_post_roll": old_decay_last10,
            "new_ramp_days_to_10k": ramp_days,
        })
    out["quarterly_rolls"] = rolls
    gaps = [r["gap_ann_pct"] for r in rolls if r["gap_ann_pct"] is not None]
    out["roll_gap_summary"] = {
        "n_rolls_measured": len(gaps),
        "share_negative_gap_pct": float(np.mean([g < 0 for g in gaps]) * 100),
        "median_ann_pct": float(np.median(gaps)),
        "min_ann_pct": float(np.min(gaps)), "max_ann_pct": float(np.max(gaps)),
        "note": "negative = deferred cheaper (backwardation) at the roll session close; adjacent-contract close difference, not tradable",
    }

    # ---- 2. roll gap vs RBA-Fed differential ---------------------------------
    rba = L.load_rba_decisions()
    dff = load_dff()
    rba_rate = rba[["announcement_date", "cash_rate_pct"]].rename(
        columns={"announcement_date": "date", "cash_rate_pct": "rba"})
    # effective-date alignment: use effective_date for the rate actually in force
    rba_eff = rba[["effective_date", "cash_rate_pct"]].rename(
        columns={"effective_date": "date", "cash_rate_pct": "rba"})
    merged_rates = pd.merge_asof(
        dff.sort_values("date"), rba_eff.sort_values("date"),
        on="date", direction="backward")
    merged_rates["diff"] = merged_rates["rba"] - merged_rates["dff"]
    rows = []
    for r in rolls:
        d = pd.Timestamp(r["roll_session"])
        m = merged_rates[merged_rates["date"] <= d].tail(1)
        if len(m) == 0 or r["gap_ann_pct"] is None:
            continue
        diff = float(m["diff"].iloc[0])
        # CIP for a USD-per-AUD quote: F = S*(1+r_USD)/(1+r_AUD) ->
        # r_AUD > r_USD implies deferred CHEAPER (backwardation, negative gap)
        cip_match = bool(np.sign(r["gap_ann_pct"]) == np.sign(-diff))
        rows.append({
            "roll_session": r["roll_session"],
            "gap_ann_pct": r["gap_ann_pct"],
            "rba_cash_rate_pct": float(m["rba"].iloc[0]),
            "us_dff_pct": float(m["dff"].iloc[0]),
            "rate_diff_rba_minus_dff_pct": diff,
            "cip_sign_match": cip_match,
            "material_differential": bool(abs(diff) >= 0.25),
        })
    mat = [r for r in rows if r["material_differential"]]
    out["roll_gap_vs_rate_differential"] = {
        "definition": ("gap_ann_pct = roll-session adjacent-contract close gap "
                       "annualized (new minus old); CIP direction for USD-per-AUD "
                       "quote: r_AUD > r_USD (diff>0) implies backwardation "
                       "(negative gap); cip_sign_match tests sign(gap) == sign(DFF-RBA)"),
        "caveat": ("RBA table = as-published decisions (gate HTML); DFF = FRED latest "
                   "vintage (ALFRED year-end vintages only in corpus) -> CIP check is "
                   "latest-vintage, not strict-PIT vintages; overnight rates are a "
                   "proxy (no 3m AUD series in corpus; DTB3 exists for US only)"),
        "n": len(rows),
        "cip_sign_match_share_pct": (float(np.mean([r["cip_sign_match"] for r in rows]) * 100)
                                     if rows else None),
        "cip_sign_match_share_material_only_pct": (
            float(np.mean([r["cip_sign_match"] for r in mat]) * 100)
            if mat else None),
        "n_material": len(mat),
        "rows": rows,
    }

    # ---- 3. curve snapshots ---------------------------------------------------
    snap_dates = ["2020-03-13", "2020-06-01", "2021-02-01", "2021-06-01",
                  "2022-04-29", "2023-01-03", "2024-01-02", "2025-01-02",
                  "2026-01-02", "2026-10-01"]
    snaps = {}
    for dstr in snap_dates:
        d = pd.Timestamp(dstr)
        row = closes.loc[:d].tail(1)
        if not len(row):
            continue
        r = row.iloc[0].dropna()
        q = {c: L.px(v) for c, v in r.items() if c.split("_")[0][2] in "HMUZ"}
        if len(q) < 3:
            continue
        ladder = sorted(q.items(), key=lambda kv: reg.set_index("contract")
                        .loc[kv[0], "delivery_month_start"])
        first_c, first_p = ladder[0]
        last_c, last_p = ladder[-1]
        snaps[dstr] = {
            "ladder_quarterly": {c: p for c, p in ladder},
            "front": first_c, "farthest": last_c,
            "front_to_farthest_pct": float((last_p / first_p - 1) * 100),
        }
    out["curve_snapshots"] = snaps

    # ---- 4. calendar-spread instrument anatomy --------------------------------
    spr = pd.read_parquet(f"{L.CACHE}/spreads_1m.parquet")
    mc = L.MONTH_CODE

    def legs(sym):
        a, b = sym.split("-")
        return a, b

    def month_key(s):
        """delivery month index within the 2020s window (2020-01 = 240)."""
        return (2020 + int(s[3])) * 12 + mc[s[2]]

    def near_far(sym):
        a, b = legs(sym)
        return (a, b) if month_key(a) <= month_key(b) else (b, a)

    def contract_key(s):
        return f"{s}_{2020 + int(s[3])}"

    spr["neg"] = spr["is_negative_bar"]
    neg_by_era = spr.groupby("era")["neg"].agg(["sum", "count"])
    sym_stats = []
    for sym, g in spr.groupby("raw_symbol"):
        near, far = near_far(sym)
        adjacent = abs(month_key(near) - month_key(far)) == 1
        negshare = float(g["neg"].mean() * 100)
        cls = g[g["neg"]]
        sym_stats.append({
            "symbol": sym, "near": near, "far": far, "adjacent": adjacent,
            "bars": int(len(g)), "neg_bar_share_pct": negshare,
            "neg_close_median": (L.px(cls["close"].median())
                                 if len(cls) else None),
            "neg_close_min": (L.px(cls["close"].min()) if len(cls) else None),
            "first_neg_date": (str(cls["session_date"].min()) if len(cls) else None),
            "last_neg_date": (str(cls["session_date"].max()) if len(cls) else None),
            "median_volume": float(g["volume"].median()),
        })
    sym_stats = sorted(sym_stats, key=lambda s: -(s["neg_bar_share_pct"] or 0))
    out["calendar_spread_negative_anatomy"] = {
        "note": ("spread instruments kept OUT of all price-behavior stats; this table "
                 "describes them separately as curve information (dispatch law). "
                 "'near_minus_far' sign convention: spread close < 0 means the FAR leg "
                 "is more expensive (contango in the quoted order)"),
        "total_spread_bars": int(len(spr)),
        "total_negative_bars": int(spr["neg"].sum()),
        "dispatch_claim_negative_bars": 5067,
        "negative_by_era": {k: {"neg": int(v["sum"]), "bars": int(v["count"])}
                            for k, v in neg_by_era.iterrows()},
        "n_spread_symbols": int(spr["raw_symbol"].nunique()),
        "top_negative_symbols": sym_stats[:25],
    }

    # spread mark vs outright-implied consistency (sample: last 90 calendar days)
    sample = spr.copy()
    sample["sd"] = pd.to_datetime(sample["session_date"])
    sample = sample[sample["sd"] >= (sample["sd"].max() - pd.Timedelta(days=90))]
    checks = []
    sc = closes.copy()
    sc.index = pd.to_datetime(sc.index)
    for sym, g in sample.groupby("raw_symbol"):
        a, b = legs(sym)                    # spread price = leg1 - leg2 as named
        ca, cb = contract_key(a), contract_key(b)
        if ca not in sc.columns or cb not in sc.columns:
            continue
        gg = g.groupby("sd")["close"].last()
        diffs = []
        for d, v in gg.items():
            if d in sc.index and pd.notna(sc.loc[d].get(ca)) \
                    and pd.notna(sc.loc[d].get(cb)):
                implied = (sc.loc[d, ca] - sc.loc[d, cb]) / L.PRICE_SCALE
                diffs.append((v / L.PRICE_SCALE) - implied)
        if len(diffs) >= 5:
            checks.append({"symbol": sym, "n": len(diffs),
                           "median_abs_diff_usd": float(np.median(np.abs(diffs))),
                           "q95_abs_diff_usd": float(np.quantile(np.abs(diffs), 0.95))})
    checks = sorted(checks, key=lambda c: -c["n"])[:15]
    out["spread_mark_vs_outright_implied"] = {
        "definition": "spread-instrument session close minus (leg1 outright close - leg2 outright close), sampled last 90 calendar days",
        "checks": checks,
    }

    # ---- 5. serial vs quarterly liquidity (v1 H3 re-measure) -------------------
    reg2 = reg[~reg["stray"]].copy()
    sc2 = sess.merge(reg2[["contract", "is_quarterly", "year", "month"]],
                     on="contract")
    liq = sc2.groupby(["is_quarterly", "session_date"])["volume"].sum().reset_index()
    out["serial_vs_quarterly_liquidity"] = {
        "median_daily_volume_quarterly_contracts_all": float(
            sc2[sc2["is_quarterly"]]["volume"].median()),
        "median_daily_volume_serial_contracts_all": float(
            sc2[~sc2["is_quarterly"]]["volume"].median()),
        "serial_contracts_in_corpus": int((~reg2["is_quarterly"]).sum()),
        "quarterly_contracts_in_corpus": int((reg2["is_quarterly"]).sum()),
        "serial_front_candidacy_note": ("v1 measured serial fronts at 8-17 lots/day (IBKR RTH); "
                                        "vendor full-session re-measure below by contract"),
        "serial_by_contract": [
            {"contract": r.contract, "total_volume": float(r.total_volume),
             "median_daily_volume": float(sc2[sc2["contract"] == r.contract]["volume"].median())
             if len(sc2[sc2["contract"] == r.contract]) else None}
            for r in reg2[~reg2["is_quarterly"]].itertuples()],
    }

    L.jdump(out, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
