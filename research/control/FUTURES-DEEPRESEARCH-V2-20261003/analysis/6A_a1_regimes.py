#!/usr/bin/env python
"""A1 — strict-past regime map 2020-2026 for 6A — lane DEEP-6A.

Descriptive ONLY. No PnL, no signals, no conditional mean-return tables.
Held chain = declared calendar rule with quarterly adaptation (next HMUZ),
built from per-contract session bars (no vendor stitching).

Statistics (all OBSERVED, script + window in every block):
  * full-session daily returns, two variants:
      within  — v1 convention (roll-date return belongs to the OLD contract;
                no stitched jump)
      rolled  — tradable chain (roll gap included on roll dates)
  * annualized vol by year and half-year; rolling-63 vol;
  * vol-regime tags from STRICT-PAST quantiles (prior 2y window);
  * trend persistence = share of sessions whose return sign matches the
    prior-50-session mean sign (strict past);
  * drawdowns on the rolled chain close (mark-to-market of a held long),
    top-10 table + COVID week anatomy (2020-03-09..03-27);
  * large-move days: |r| above q95 of prior-126 |r| (strict past);
  * biggest 63-session cumulative moves (descriptive, incl 2021-22 cycle).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_a1_regimes.py
Writes: 6A_a1_regimes.json
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

OUT = os.path.join(_HERE, "6A_a1_regimes.json")


def qstats(x: pd.Series) -> dict:
    x = x.dropna()
    if len(x) < 5:
        return {"n": int(len(x))}
    return {
        "n": int(len(x)), "mean": float(x.mean()), "median": float(x.median()),
        "std": float(x.std()), "q05": float(x.quantile(0.05)),
        "q95": float(x.quantile(0.95)), "min": float(x.min()), "max": float(x.max()),
    }


def main():
    sess = pd.read_parquet(f"{L.CACHE}/session_contract.parquet")
    sess = sess[~sess["contract"].str.startswith("STRAY")]
    sess["session_date"] = pd.to_datetime(sess["session_date"])
    sess = sess.sort_values("session_date")

    chain = L.calendar_chain(sess, quarterly_only=True)
    chain["session_date"] = pd.to_datetime(chain["session_date"])
    m = chain.merge(sess, left_on=["session_date", "held"],
                    right_on=["session_date", "contract"], how="left")
    if m["close_px"].isna().any():
        raise ValueError("chain sessions missing held-contract bars")
    m = m.sort_values("session_date").reset_index(drop=True)
    m["roll_flag"] = m["held"] != m["held"].shift(1)
    # full-session close and RTH close series
    m["px"] = m["close_px"] / L.PRICE_SCALE
    m["rth_px"] = m["rth_close"] / L.PRICE_SCALE
    m["open_px_f"] = m["open_px"] / L.PRICE_SCALE
    m["rth_open_f"] = m["rth_open"] / L.PRICE_SCALE

    # returns
    within = (m["px"] / m["px"].shift(1) - 1).where(~m["roll_flag"])
    rolled = m["px"] / m["px"].shift(1) - 1
    # RTH-only session return (v1-comparable: RTH open -> RTH close? v1 daily
    # bars were RTH close-to-close within contract; use RTH close-to-close)
    rth_ret = m["rth_px"] / m["rth_px"].shift(1) - 1
    overnight_gap = m["open_px_f"] / m["rth_px"].shift(1) - 1  # session open vs prior RTH close

    m["ret_within"], m["ret_rolled"], m["ret_rth"], m["gap_overnight"] = \
        within, rolled, rth_ret, overnight_gap

    out = {
        "meta": {
            "lane": "DEEP-6A", "analysis": "A1 regime map",
            "window": [str(m["session_date"].min().date()),
                       str(m["session_date"].max().date())],
            "sessions": int(len(m)),
            "n_rolls": int(m["roll_flag"].sum() - 1),
            "chain_rule": "declared calendar, quarterly adaptation (next HMUZ), roll at close of last session before delivery month",
            "price_convention": "full-session (17:00 CT prior day -> 16:00 CT) last-bar close, unadjusted",
            "laws": "descriptive only; strict-past thresholds; no PnL",
        },
    }

    # ---- vol by year --------------------------------------------------------
    yr = m.set_index("session_date")
    by_year = {}
    for y, g in yr.groupby(yr.index.year):
        by_year[int(y)] = {
            "n": int(len(g)),
            "vol_ann_within_pct": float(g["ret_within"].std(ddof=1) * np.sqrt(252) * 100),
            "vol_ann_rolled_pct": float(g["ret_rolled"].std(ddof=1) * np.sqrt(252) * 100),
            "vol_ann_rth_pct": float(g["ret_rth"].std(ddof=1) * np.sqrt(252) * 100),
            "mean_abs_ret_bp": float(g["ret_rolled"].abs().mean() * 1e4),
            "worst_day_pct": float(g["ret_rolled"].min() * 100),
            "best_day_pct": float(g["ret_rolled"].max() * 100),
            "median_daily_volume": float(g["volume"].median()),
        }
    out["vol_by_year"] = by_year

    # half-year granularity for regime narrative
    half = {}
    for h, g in m.groupby(m["session_date"].dt.year.astype(str) + "H"
                          + np.where(m["session_date"].dt.month <= 6, "1", "2")):
        half[h] = {
            "n": int(len(g)),
            "vol_ann_pct": float(g["ret_rolled"].std(ddof=1) * np.sqrt(252) * 100),
            "cum_ret_pct": float((np.prod(1 + g["ret_rolled"].fillna(0)) - 1) * 100),
            "mean_abs_ret_bp": float(g["ret_rolled"].abs().mean() * 1e4),
        }
    out["vol_by_halfyear"] = half

    # ---- rolling-63 vol -----------------------------------------------------
    rv63 = m["ret_rolled"].rolling(63).std() * np.sqrt(252)
    out["rolling63_vol"] = {
        "window_sessions": 63,
        "min_pct": float(rv63.min() * 100), "max_pct": float(rv63.max() * 100),
        "median_pct": float(rv63.median() * 100),
        "p05_pct": float(rv63.quantile(0.05) * 100),
        "p95_pct": float(rv63.quantile(0.95) * 100),
        "max_date": str(m.loc[rv63.idxmax(), "session_date"].date()),
        "min_date": str(m.loc[rv63.idxmin(), "session_date"].date()),
        "start_end_by_year": {
            int(y): [float(rv63[g.index].dropna().iloc[0] * 100),
                     float(rv63[g.index].dropna().iloc[-1] * 100)]
            for y, g in m.groupby(m["session_date"].dt.year) if rv63[g.index].notna().any()},
    }

    # ---- strict-past vol-regime tags ----------------------------------------
    tags = []
    for i in range(len(m)):
        if i < 252:
            tags.append(None)
            continue
        past = rv63.iloc[max(0, i - 504):i]      # prior 2y of rolling vol, strict past
        if pd.isna(past).all() or len(past.dropna()) < 126:
            tags.append(None)
            continue
        v = rv63.iloc[i]
        if pd.isna(v):
            tags.append(None)
            continue
        cuts = [past.quantile(q) for q in (0.2, 0.4, 0.6, 0.8)]
        tags.append(int(np.searchsorted(cuts, v)))
    m["vol_regime_tag"] = tags   # 0..4 quintiles of strict-past distribution

    regime_tbl = {}
    for t in range(5):
        g = m[m["vol_regime_tag"] == t]
        if len(g) < 10:
            continue
        regime_tbl[f"q{t}"] = {
            "n_sessions": int(len(g)),
            "realized_vol_ann_next_session_pct": None,
            "note": "tag = current rolling-63 vol quintile within its prior-2y distribution (strict past); descriptive split only",
            "mean_abs_ret_bp": float(g["ret_rolled"].abs().mean() * 1e4),
            "date_span": [str(g["session_date"].min().date()),
                          str(g["session_date"].max().date())],
        }
    out["vol_regime_strict_past_quintiles"] = regime_tbl

    # ---- trend persistence (strict past) ------------------------------------
    prior50 = m["ret_rolled"].rolling(50).mean()
    sign_match = (np.sign(m["ret_rolled"]) == np.sign(prior50.shift(1))) & \
                 (m["ret_rolled"] != 0) & (prior50.shift(1) != 0)
    valid = prior50.shift(1).notna() & m["ret_rolled"].notna()
    persist = {}
    persist["overall"] = {
        "n": int(valid.sum()),
        "share_sign_matches_prior50_mean_sign": float(
            (sign_match & valid).sum() / max(valid.sum(), 1)),
        "definition": "share of sessions whose return sign matches the SIGN of the mean of the prior 50 session returns (strict past)",
    }
    for y, g in m.groupby(m["session_date"].dt.year):
        vm = valid.loc[g.index]
        persist[int(y)] = float((sign_match & vm).sum() / max(vm.sum(), 1))
    out["trend_persistence_by_year"] = persist

    # persistence conditional on strict-past vol regime (descriptive)
    pr = {}
    for t in range(5):
        g = m[(m["vol_regime_tag"] == t)]
        vm = valid.loc[g.index]
        if vm.sum() >= 10:
            pr[f"q{t}"] = float((sign_match & vm).sum() / vm.sum())
    out["trend_persistence_by_vol_regime"] = pr

    # ---- drawdowns (rolled chain, held-long mark-to-market) ------------------
    px = m["px"].reset_index(drop=True)
    dd = px / px.cummax() - 1
    m["dd"] = dd
    # top drawdown episodes
    episodes = []
    peak_i = 0
    in_dd = False
    for i in range(1, len(px)):
        if px[i] >= px[peak_i]:
            if in_dd:
                episodes.append((peak_i, trough_i, i))
                in_dd = False
            peak_i = i
        else:
            if not in_dd:
                in_dd = True
                trough_i = i
            elif px[i] < px[trough_i]:
                trough_i = i
    if in_dd:
        episodes.append((peak_i, trough_i, None))
    ep = []
    for pk, tr, rec in episodes:
        ep.append({
            "peak_date": str(m.loc[pk, "session_date"].date()),
            "trough_date": str(m.loc[tr, "session_date"].date()),
            "recovery_date": str(m.loc[rec, "session_date"].date()) if rec is not None else None,
            "depth_pct": float(dd[tr] * 100),
            "sessions_peak_to_trough": int(tr - pk),
            "ongoing": rec is None,
        })
    ep = sorted(ep, key=lambda e: e["depth_pct"])[:10]
    out["drawdowns_top10_rolled_chain"] = ep
    out["drawdown_summary"] = {
        "worst_depth_pct": float(dd.min() * 100),
        "worst_date": str(m.loc[dd.idxmin(), "session_date"].date()),
        "definition": "rolled held-chain close (unadjusted, roll gap included) vs running max; mark-to-market of a long, NOT PnL of a strategy",
    }

    # COVID week anatomy 2020-03-02..2020-03-27
    cov = m[(m["session_date"] >= "2020-03-02") & (m["session_date"] <= "2020-03-27")]
    out["covid_week_anatomy"] = {
        "window": ["2020-03-02", "2020-03-27"],
        "note": ("volume column = HELD contract (the chain rolled onto 6AM0 on "
                 "2020-03-02; early-March low volumes are the new contract's "
                 "pre-migration book, not market collapse — see "
                 "market_volume_by_month for the all-contract context)"),
        "rows": [{
            "date": str(r.session_date.date()), "held": r.held,
            "ret_rolled_pct": float(r.ret_rolled * 100) if pd.notna(r.ret_rolled) else None,
            "range_ticks": float((r.high_px - r.low_px) / L.TICK),
            "volume": int(r.volume),
        } for r in cov.itertuples()],
        "week_of_mar9_cum_pct": float((np.prod(1 + cov[(cov["session_date"] >= "2020-03-09") &
                                                        (cov["session_date"] <= "2020-03-13")]
                                              ["ret_rolled"].fillna(0)) - 1) * 100),
    }

    # total 6A market volume context (ALL outright contracts, by month)
    allvol = sess.groupby(sess["session_date"].dt.to_period("M"))["volume"].sum()
    out["market_volume_by_month"] = {
        str(k): int(v) for k, v in allvol.items()}

    # 2021-22 cycle: biggest 63-session cumulative moves
    cum63 = (1 + m["ret_rolled"].fillna(0)).rolling(63).apply(np.prod, raw=True) - 1
    top_up = cum63.nlargest(5)
    top_dn = cum63.nsmallest(5)
    out["biggest_63session_moves"] = {
        "definition": "largest cumulative 63-session (rolling) moves on the rolled chain; descriptive cycle anatomy",
        "top_up": [{"end_date": str(m.loc[i, "session_date"].date()),
                    "cum_pct": float(v * 100)} for i, v in top_up.items()],
        "top_down": [{"end_date": str(m.loc[i, "session_date"].date()),
                      "cum_pct": float(v * 100)} for i, v in top_dn.items()],
    }

    # ---- large-move days (strict-past threshold) -----------------------------
    absr = m["ret_rolled"].abs()
    thr = absr.shift(1).rolling(126).quantile(0.95)
    big = m[absr > thr]
    out["large_move_days"] = {
        "definition": "|r| above q95 of prior-126-session |r| (strict past)",
        "n": int(len(big)),
        "by_quarter": {str(k): int(v) for k, v in
                       big.groupby(big["session_date"].dt.to_period("Q")).size().items()},
        "top10_by_abs": [{"date": str(r.session_date.date()),
                          "ret_pct": float(r.ret_rolled * 100),
                          "volume": int(r.volume)} for r in
                         big.assign(absr=big["ret_rolled"].abs())
                         .nlargest(10, "absr").itertuples()],
    }

    # ---- daily return distribution (era-level) -------------------------------
    dist = {}
    for era, g in m.groupby(pd.cut(m["session_date"], pd.to_datetime(
            ["2020-01-01", "2022-01-01", "2024-01-01", "2026-10-01"]),
            labels=["2020-21", "2022-23", "2024-26"])):
        dist[str(era)] = {
            "n": int(len(g)),
            "ret_rolled": qstats(g["ret_rolled"] * 100),
            "gap_overnight_pct": qstats(g["gap_overnight"] * 100),
            "skew_rolled": float(g["ret_rolled"].skew()),
            "lag1_absret_autocorr": float(g["ret_rolled"].abs().autocorr(1)),
        }
    out["return_distribution_by_era"] = dist

    # v1 reconciliation (2026 window, front-scale era comparable)
    v1w = m[(m["session_date"] >= "2025-09-10") & (m["session_date"] <= "2026-10-01")]
    out["v1_reconciliation_2025-09-10_2026-10-01"] = {
        "n": int(len(v1w)),
        "vol_ann_rolled_fullsession_pct": float(v1w["ret_rolled"].std(ddof=1) * np.sqrt(252) * 100),
        "vol_ann_rth_pct": float(v1w["ret_rth"].std(ddof=1) * np.sqrt(252) * 100),
        "v1_reported_rth_vol_ann_pct": 7.45,
        "note": "v1 IBKR useRTH daily bars gave 7.45% ann.; vendor full-session 2026 comparison shows the RTH-vs-full-session gap",
    }

    # session-by-session series cache for later analyses
    keep = m[["session_date", "held", "px", "rth_px", "ret_rolled", "ret_within",
              "ret_rth", "gap_overnight", "volume", "rth_volume", "roll_flag",
              "open_px_f", "rth_open_f", "high_px", "low_px"]]
    keep.to_parquet(f"{L.CACHE}/chain_daily.parquet", index=False)
    L.jdump(out, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
