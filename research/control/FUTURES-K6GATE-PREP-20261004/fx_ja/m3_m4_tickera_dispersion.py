#!/usr/bin/env python
"""Lane FXJA-K6, FUTURES-K6GATE-PREP-20261004 — M3 (6A D-2 tick-era audit,
steps i+ii) + M4 (6J/6A session dispersion refresh).

M3(i): era-1 6A RT cost surface at $10.00/tick — MODELED arithmetic from
named inputs (FEES_CORRECTED tiers; DC §1.7 spread proxy doubled per the
D-2 text; slippage {1,2,3} ticks). VERIFIED_VS_ACCOUNT=NOT_RUN everywhere.
M3(ii): unconditional close-to-close proxy-spread step test at 2020-11-23,
6A vs same-date 6J placebo — descriptive only, no significance test.
M4: per-session |1m ret| dispersion + volume + bar-count tables, era-aware
for 6A (era-1 <=2020-11-20 descriptive-only stratum vs era-2 >=2020-11-23).

NO PnL, NO directional returns anywhere.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import pandas as pd

HERE = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep"
        "/research/control/FUTURES-K6GATE-PREP-20261004/fx_ja")
SIXWRK = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness"
          "/prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis")
RDY = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-k6gate/prep"
       "/research/control/FUTURES-SIX-READINESS-20261004")
sys_path = os.path.join(RDY, "fx_ja")
import sys  # noqa: E402
sys.path.insert(0, sys_path)
from fx_ja_lib import DATA_ROOT, add_session, next_quarter  # noqa: E402

INT_NANO = 1e9
BOUNDARY_LAST = pd.Timestamp("2020-11-20").date()
BOUNDARY_FIRST = pd.Timestamp("2020-11-23").date()


def cease_guard_held(wide):
    roll5 = wide.rolling(5, min_periods=1).mean()
    state, held = None, {}
    for d in wide.index:
        r5 = roll5.loc[d].dropna()
        r5 = r5[r5 > 0]
        row = wide.loc[d]
        if state is None:
            state = r5.idxmax()
        else:
            v = row.get(state, np.nan)
            if pd.isna(v):
                state = next_quarter(state)
            else:
                nxt = next_quarter(state)
                if nxt in r5.index and r5[nxt] > r5[state]:
                    state = nxt
        held[d] = state
    return held


def per_session_stats(df):
    """df: held-contract 1m bars of one symbol with session_date/close/volume."""
    d = df.sort_values("dt").copy()
    g = d.groupby("session_date")
    out = pd.DataFrame({
        "n_bars": g.size(),
        "volume_held": g["volume"].sum(),
        "close": g["close"].last(),
        "high": g["high"].max(), "low": g["low"].min(),
    })
    d["prev"] = d.groupby("session_date")["close"].shift(1)
    d["absret_bp"] = (d["close"] / d["prev"] - 1.0).abs() * 1e4
    d["absdc_intnano"] = (d["close"] - d["prev"]).abs()
    d["ret_bp"] = (d["close"] / d["prev"] - 1.0) * 1e4
    g2 = d.groupby("session_date")
    out["median_absret_bp"] = g2["absret_bp"].median()
    out["mean_absret_bp"] = g2["absret_bp"].mean()
    out["p90_absret_bp"] = g2["absret_bp"].quantile(0.9)
    out["sum_absret_bp"] = g2["absret_bp"].sum()
    out["std_ret_bp"] = g2["ret_bp"].std(ddof=1)
    out["median_absdc_intnano"] = g2["absdc_intnano"].median()
    return out, d


def main():
    # ---------------- 6A panel (single-shot raw read) ----------------
    reg = pd.read_parquet(f"{SIXWRK}/6A_cache/registry.parquet")
    iid2c = dict(zip(reg["instrument_id"].astype("int64"), reg["contract"]))
    is_q = dict(zip(reg["contract"].astype(str), reg["is_quarterly"].astype(bool)))
    files = (sorted(glob.glob(f"{DATA_ROOT}/AV1B-O1M-6A-BACKFILL2/*.parquet"))
             + sorted(glob.glob(f"{DATA_ROOT}/AV1R-O1M-6A-BACKFILL/*.parquet"))
             + sorted(glob.glob(f"{DATA_ROOT}/AV1T-O1M-6A/*.parquet")))
    parts = [pd.read_parquet(f, columns=["instrument_id", "raw_symbol", "ts_event",
                                         "open", "high", "low", "close", "volume"])
             for f in files]
    a = pd.concat(parts, ignore_index=True)
    del parts
    a["dt"] = pd.to_datetime(a["ts_event"], unit="ns", utc=True)
    a = add_session(a)
    n_raw_rows = len(a)
    a = a[a["raw_symbol"].str.fullmatch(r"6A[FGHJKMNQUVXZ]\d")].copy()
    a["contract"] = a["instrument_id"].astype("int64").map(iid2c)
    assert a["contract"].isna().sum() == 0
    awide = (a[a["contract"].map(lambda c: is_q.get(c, False))]
             .pivot_table(index="session_date", columns="contract",
                          values="volume", aggfunc="sum").sort_index())
    held_a = cease_guard_held(awide)
    ha = pd.DataFrame({"held": pd.Series(held_a)})
    bars_a = a[a["contract"] == a["session_date"].map(held_a)]
    sess_a, rets_a = per_session_stats(bars_a)
    # panel-wide (all-contract) session volume, secondary field
    sess_a["volume_all"] = a.groupby("session_date")["volume"].sum()

    era1_mask = pd.to_datetime(pd.Index(sess_a.index)) <= pd.Timestamp("2020-11-20")
    sess_a["era"] = np.where(era1_mask, "era1_to_20201120", "era2_from_20201123")
    n_era1 = int((sess_a["era"] == "era1_to_20201120").sum())

    # ---------------- 6J panel (single-shot cache read) ----------------
    j = pd.read_parquet(f"{SIXWRK}/6J_cache/6j_annotated_1m.parquet",
                        columns=["dt", "close", "high", "low", "volume",
                                 "contract", "session_date"])
    heldj = pd.read_parquet(f"{SIXWRK}/6J_cache/held_volume_k5.parquet")
    heldmap_j = dict(zip(heldj["session_date"], heldj["held"]))
    bars_j = j[j["contract"] == j["session_date"].map(heldmap_j)]
    sess_j, rets_j = per_session_stats(bars_j)
    sess_j["volume_all"] = j.groupby("session_date")["volume"].sum()
    sess_j["era"] = "full_2020_2026"
    n_raw_j = len(j)

    # ================= M3 step (i): era-1 MODELED cost surface ==========
    fees = {"T1": 2.46, "T2": 2.26, "T3": 2.06, "T4": 1.86}
    spread = {"era1": 40.00, "era2": 20.00}      # 4 ticks: $10.00 vs $5.00
    slip = {"era1": [10.00, 20.00, 30.00], "era2": [5.00, 10.00, 15.00]}
    era1_close = sess_a[sess_a["era"] == "era1_to_20201120"]["close"] / INT_NANO
    px_med = float(era1_close.median())
    px_last = float(era1_close.iloc[-1])
    px_era2_ref = 0.6696  # reference of record (DATA_READINESS_6A Dim 6)

    def table(era, px):
        rows = []
        for tier, fee in fees.items():
            for k, s in enumerate(slip[era], start=1):
                side = fee + spread[era] + s
                rt = 2 * side
                rows.append({
                    "tier": tier, "fee_usd_per_side": fee,
                    "spread_proxy_usd_per_side": spread[era],
                    "slippage_usd_per_side": s,
                    "slippage_ticks_per_side": k,
                    "side_cost_usd": round(side, 4),
                    "round_trip_usd": round(rt, 4),
                    "round_trip_bp_of_notional": round(rt / (100_000 * px) * 1e4, 4),
                    "notional_usd_at_representative_price": round(100_000 * px, 2),
                })
        return rows

    step1 = {
        "labels": "MODELED COST / UNDER REVIEW / VERIFIED_VS_ACCOUNT=NOT_RUN "
                  "(no 'measured cost'/'complete cost' anywhere; no D3 default "
                  "language; fees per FEES_CORRECTED §2 FX row; COST_FREEZE_"
                  "ERRATUM is the correction of record)",
        "era_law": "6a_tick_adjudication.json: era-1 <=2020-11-20 grid 1e-04 = "
                   "$10.00/tick; era-2 >=2020-11-23 grid 5e-05 = $5.00/tick "
                   "(data-side PROVISIONAL label; D8 unratified; official "
                   "rulebook page BLOCKED_TRANSPORT)",
        "representative_prices": {
            "era1_median_held_session_close_usd_per_aud": round(px_med, 6),
            "era1_final_session_close_usd_per_aud": round(px_last, 6),
            "era1_final_session": str(era1_close.index[-1]),
            "era2_reference_of_record": px_era2_ref,
        },
        "era1_table_median_px": table("era1", px_med),
        "era1_table_final_close_px": table("era1", px_last),
        "era2_reference_table_at_0.6696": table("era2", px_era2_ref),
        "era2_reference_validation": {
            "expected_rt_T1_1tick_usd": 54.92,
            "recomputed_rt_T1_1tick_usd": 2 * (2.46 + 20.00 + 5.00),
            "expected_bp": 8.2,
            "recomputed_bp": round(2 * (2.46 + 20.00 + 5.00)
                                   / (100_000 * px_era2_ref) * 1e4, 4)},
        "delta_era1_minus_era2_T1_1tick": {
            "rt_usd_delta": round(2 * (2.46 + 40 + 10) - 54.92, 4),
            "note": ("tick-denominated components (spread proxy 4 ticks + "
                     "1-tick slippage) double in era-1; fee layer unchanged")},
    }

    # ================= M3 step (ii): spread-proxy step test =============
    def boundary_windows(sess, tick_intnano_last, tick_intnano_pre):
        s = pd.DataFrame({"proxy": sess["median_absdc_intnano"]})
        s = s[s["proxy"].notna()]
        pre = s[s.index <= BOUNDARY_LAST].tail(10)
        post = s[s.index >= BOUNDARY_FIRST].head(10)
        out = {
            "pre10_dates": [str(x) for x in pre.index],
            "post10_dates": [str(x) for x in post.index],
            "pre10_median_proxy_usd": float(pre["proxy"].median() / INT_NANO),
            "post10_median_proxy_usd": float(post["proxy"].median() / INT_NANO),
            "pre10_median_proxy_ticks": float(pre["proxy"].median() / tick_intnano_pre),
            "post10_median_proxy_ticks": float(post["proxy"].median() / tick_intnano_last),
        }
        out["step_ratio_usd"] = out["post10_median_proxy_usd"] / out["pre10_median_proxy_usd"]
        out["step_ratio_ticks"] = out["post10_median_proxy_ticks"] / out["pre10_median_proxy_ticks"]
        return out, s

    w_a, series_a = boundary_windows(sess_a, 50_000, 100_000)
    w_j, series_j = boundary_windows(sess_j, 500, 500)
    same_dates = (w_a["pre10_dates"] == w_j["pre10_dates"]
                  and w_a["post10_dates"] == w_j["post10_dates"])

    trail = {}
    for nm, s, tks in (("6A", series_a, None), ("6J", series_j, None)):
        end = pd.Timestamp("2020-12-31").date()
        sub = s[(s.index >= pd.Timestamp("2020-10-01").date()) & (s.index <= end)]
        trail[nm] = [{"date": str(ix), "proxy_usd": float(r["proxy"] / INT_NANO)}
                     for ix, r in sub.iterrows()]

    step2 = {
        "definition": ("[OPERATIONALIZED per §0.4] proxy_s = median over "
                       "within-session consecutive 1m bar pairs of |Δclose| "
                       "(held chain, USD); step = post10/pre10 median ratio, "
                       "reported in USD and in prevailing-grid ticks"),
        "boundary_law": ("last pure 1e-4 session 2020-11-20, first 5e-5 session "
                         "2020-11-23 (6a_tick_adjudication.json:tick_break_locator; "
                         "PROVISIONAL label, D8 unratified)"),
        "6A": w_a, "6J_placebo": w_j,
        "same_date_sets_identical": bool(same_dates),
        "trailing_series_2020_10_01_to_2020_12_31": trail,
        "boundary": ("descriptive comparison ONLY; no significance test at "
                     "n=10 vs 10 (pre-declared NOT_RUN by construction); no "
                     "directional claims"),
    }

    aud = {
        "schema": "aud_d2_tickera@1",
        "lane": "FXJA-K6", "round": "FUTURES-K6GATE-PREP-20261004",
        "predeclaration": "FXJA_K6_GATES.md §0.4 (written before compute)",
        "owning_definition": "HYPOTHESES_R2.md §5 D-2 steps (i)+(ii); step (iii) "
                             "6E/6B constancy = FXEB lane's, NOT duplicated here",
        "inputs": {
            "6A_raw_roots": ["AV1B-O1M-6A-BACKFILL2", "AV1R-O1M-6A-BACKFILL", "AV1T-O1M-6A"],
            "6A_raw_rows_outright": int(n_raw_rows - 0),
            "6A_chain": "cease-guard variant re-derived from raw; identical to "
                        "6a_roll_measured.json (verified in rmm_mode_ledger.json "
                        "crosscheck:6A_verification_vs_6a_roll_measured)",
            "6J_panel": f"{SIXWRK}/6J_cache/6j_annotated_1m.parquet",
            "6J_chain": f"{SIXWRK}/6J_cache/held_volume_k5.parquet (baseline k=5 of record)",
            "zero_fetch": True,
        },
        "era_counts": {
            "6A_era1_sessions": n_era1,
            "6A_era2_sessions": int(len(sess_a) - n_era1),
            "expected_era1_per_tick_break_locator": 231,
            "era1_count_matches": n_era1 == 231,
        },
        "step_i_era1_cost_surface": step1,
        "step_ii_spread_proxy_step_test": step2,
        "no_pnl_note": "cost arithmetic + dispersion only; no returns conditioning",
    }

    # ================= M4 dispersion tables =============================
    def disp_block(sess, symbol):
        eras = {}
        for era, sub in sess.groupby("era"):
            eras[era] = {
                "n_sessions": int(len(sub)),
                "n_sessions_with_bars": int((sub["n_bars"] > 0).sum()),
                "n_bars_total": int(sub["n_bars"].sum()),
                "volume_held_total": int(sub["volume_held"].sum()),
                "median_of_session_median_absret_bp": float(sub["median_absret_bp"].median()),
                "mean_of_session_mean_absret_bp": float(sub["mean_absret_bp"].mean()),
                "median_of_session_p90_absret_bp": float(sub["p90_absret_bp"].median()),
                "median_of_session_std_ret_bp": float(sub["std_ret_bp"].median()),
                "median_session_volume_held": float(sub["volume_held"].median()),
                "note": ("era-1 = 231-session descriptive-only stratum per the "
                         "K3-thin law (>=5-per-fold floor fails; JF1 f7 "
                         "n-honesty)" if era == "era1_to_20201120" else None),
            }
        rows = []
        for ix, r in sess.iterrows():
            rows.append({
                "session_date": str(ix), "era": r["era"],
                "n_bars": int(r["n_bars"]) if pd.notna(r["n_bars"]) else 0,
                "volume_held": None if pd.isna(r["volume_held"]) else int(r["volume_held"]),
                "volume_all_contracts": None if pd.isna(r["volume_all"]) else int(r["volume_all"]),
                "close_usd": None if pd.isna(r["close"]) else float(r["close"] / INT_NANO),
                "median_absret_bp": None if pd.isna(r["median_absret_bp"]) else float(r["median_absret_bp"]),
                "mean_absret_bp": None if pd.isna(r["mean_absret_bp"]) else float(r["mean_absret_bp"]),
                "p90_absret_bp": None if pd.isna(r["p90_absret_bp"]) else float(r["p90_absret_bp"]),
                "std_ret_bp": None if pd.isna(r["std_ret_bp"]) else float(r["std_ret_bp"]),
                "sum_absret_bp": None if pd.isna(r["sum_absret_bp"]) else float(r["sum_absret_bp"]),
            })
        return {"era_aggregates": eras, "sessions": rows}

    # 6A delta vs prior committed a2 (mean |1m ret| bp by CT hour, 2020-2021 bucket)
    bars_a2 = bars_a.sort_values("dt").copy()
    bars_a2["prev"] = bars_a2.groupby("session_date")["close"].shift(1)
    bars_a2["absret_bp"] = (bars_a2["close"] / bars_a2["prev"] - 1.0).abs() * 1e4
    bars_a2["ct_hour"] = bars_a2["dt"].dt.tz_convert("America/Chicago").dt.hour
    sub = bars_a2[(bars_a2["session_date"] >= pd.Timestamp("2020-01-01").date())
                  & (bars_a2["session_date"] <= pd.Timestamp("2021-12-31").date())]
    mine_hour = sub.groupby("ct_hour")["absret_bp"].mean().round(6).to_dict()
    a2 = json.load(open(f"{SIXWRK}/6A_a2_sessions.json"))
    a2_hour = {int(k): v for k, v in a2["mean_abs_1m_ret_by_ct_hour_bp"]["2020-2021"].items()}
    delta_6a = {h: {"prior_a2": a2_hour.get(h), "this_lane": mine_hour.get(h),
                    "delta_bp": round(mine_hour[h] - a2_hour[h], 6)}
                for h in sorted(a2_hour) if h in mine_hour}
    # 6J delta vs prior committed a2 panel block
    j2 = json.load(open(f"{SIXWRK}/6J_a2_sessions.json"))
    delta_6j = {
        "prior_a2_panel": j2["panel"],
        "this_lane": {"held_chain_sessions": int(len(sess_j)),
                      "held_chain_n_bars": int(sess_j["n_bars"].sum()),
                      "volume_held_total": int(sess_j["volume_held"].sum())},
        "note": ("prior a2 used the v1 1,745-session bar-level chain; this lane "
                 "uses the committed baseline k=5 held map (1,746 sessions; "
                 "2022-09-20 has zero held bars and enters no statistic)"),
    }

    disp = {
        "schema": "session_dispersion_6j6a@1",
        "lane": "FXJA-K6", "round": "FUTURES-K6GATE-PREP-20261004",
        "predeclaration": "FXJA_K6_GATES.md §0.5 (written before compute)",
        "definition": ("per held-chain session, held-contract within-session "
                       "close-to-close 1m pairs; |ret| in bp; std of signed "
                       "1m rets (ddof=1) = D5/power feed; 6A era-aware "
                       "(era-1 <=2020-11-20 descriptive-only stratum); volume "
                       "shares/ratios only (6J 0.455x gap law)"),
        "6J": disp_block(sess_j, "6J"),
        "6A": disp_block(sess_a, "6A"),
        "deltas_vs_prior_committed": {"6A_mean_absret_by_ct_hour_2020_2021": delta_6a,
                                      "6J_panel": delta_6j},
        "nothing_overwritten_note": ("all outputs are new files under "
                                     "FUTURES-K6GATE-PREP-20261004/fx_ja/; no "
                                     "committed artifact modified"),
        "no_pnl_note": "unconditional dispersion/volume/bar-count only",
    }

    with open(os.path.join(HERE, "aud_d2_tickera.json"), "w") as fh:
        json.dump(aud, fh, indent=1, default=str, allow_nan=False)
    print("wrote aud_d2_tickera.json")
    with open(os.path.join(HERE, "session_dispersion_6j6a.json"), "w") as fh:
        json.dump(disp, fh, indent=1, default=str, allow_nan=False)
    print("wrote session_dispersion_6j6a.json")

    print(json.dumps({"era_counts": aud["era_counts"],
                      "repr_px": step1["representative_prices"],
                      "era1_T1_rows": step1["era1_table_median_px"][:3],
                      "validation": step1["era2_reference_validation"],
                      "step_6A": {k: w_a[k] for k in ("pre10_median_proxy_usd",
                                                      "post10_median_proxy_usd",
                                                      "pre10_median_proxy_ticks",
                                                      "post10_median_proxy_ticks",
                                                      "step_ratio_usd",
                                                      "step_ratio_ticks")},
                      "step_6J": {k: w_j[k] for k in ("pre10_median_proxy_usd",
                                                      "post10_median_proxy_usd",
                                                      "pre10_median_proxy_ticks",
                                                      "post10_median_proxy_ticks",
                                                      "step_ratio_usd",
                                                      "step_ratio_ticks")},
                      "same_dates": same_dates}, indent=1, default=str))


if __name__ == "__main__":
    main()
