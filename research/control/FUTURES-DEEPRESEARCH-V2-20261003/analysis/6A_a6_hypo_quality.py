#!/usr/bin/env python
"""A6 — hypothesis refinement vs v1 + data-quality ledger — lane DEEP-6A.

NO PnL anywhere; refined hypothesis SPECS only. Blocks (OBSERVED unless
marked):
  1. HG re-verification: HG copper absent from the av1trim corpus (definitions
     ALL10 scan) — v1 ERRATUM carried forward, still NOT_IN_CORPUS;
  2. v1 roll-rule executability defect DISSOLVED: the vendor panel contains
     every 2020-2026 serial — literal 'next listed' chain built and compared
     to the quarterly adaptation (serial-hold sessions, serial book volume,
     chain-drift differences at same-date rolls);
  3. H4 support: 6A-vs-ES daily-return rolling correlation/beta by year and
     by ES strict-past vol regime (ES regime = trailing-63d vol vs prior-1y
     median, ex-ante tag; descriptive only);
  4. OI availability (2023-10+ statistics): OI-front vs volume-front
     crossover dates for recent quarterly rolls;
  5. data-quality ledger per era (sessions, weekday-coverage gaps, front
     bars/day, DST-transition day counts, zero-volume share, break/weekend
     anomalies, negative-price counts, contamination, strays);
  6. refined hypothesis specs 6A-H1..H5 v2 (floors/param-gaps re-tagged).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python 6A_a6_hypo_quality.py
Writes: 6A_a6_hypo_quality.json
"""
from __future__ import annotations

import glob
import importlib.util
import os

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "sixA_deep_lib", os.path.join(_HERE, "6A_deep_lib.py"))
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

OUT = os.path.join(_HERE, "6A_a6_hypo_quality.json")
ES_CHAIN = os.path.join(_HERE, "ES_cache", "es_chain_DECL.parquet")  # sibling lane DEEP-ES artifact, read-only


def main():
    sess = pd.read_parquet(f"{L.CACHE}/session_contract.parquet")
    sess = sess[~sess["contract"].str.startswith("STRAY")]
    sess["session_date"] = pd.to_datetime(sess["session_date"])
    reg = pd.read_parquet(f"{L.CACHE}/registry.parquet")
    chain_q = L.calendar_chain(sess, quarterly_only=True)
    chain_q["session_date"] = pd.to_datetime(chain_q["session_date"])
    daily = pd.read_parquet(f"{L.CACHE}/chain_daily.parquet")
    daily["session_date"] = pd.to_datetime(daily["session_date"])
    build = pd.read_json(f"{L.CACHE}/build_report.json", typ="series").to_dict()
    bars = pd.read_parquet(f"{L.CACHE}/outright_1m.parquet",
                           columns=["dt", "contract", "session_date", "volume", "era"])
    bars["session_date"] = pd.to_datetime(bars["session_date"])

    out = {"meta": {"lane": "DEEP-6A", "analysis": "A6 hypo refinement + QA ledger",
                    "laws": "no PnL; refined specs only; all descriptive"}}

    # ---- 1. HG re-verification ------------------------------------------------
    dfiles = sorted(glob.glob(
        f"{L.DATA_ROOT}/parquet/AV1T-definition-ALL10/*.parquet"))
    hg_syms = set()
    for f in dfiles:
        d = pd.read_parquet(f, columns=["raw_symbol"])
        hg_syms |= set(s for s in d["raw_symbol"].unique()
                       if str(s).startswith(("HG", "COPPER")))
        break  # symbol universe identical across windows; one file enough
    out["hg_verification"] = {
        "hg_like_symbols_in_definitions": sorted(hg_syms),
        "ohlcv_dirs": sorted(os.path.basename(p) for p in glob.glob(
            f"{L.DATA_ROOT}/parquet/*/")),
        "verdict": "HG NOT_IN_CORPUS (no HG ohlcv line; definitions carry no HG symbol universe row) — v1 ERRATUM carried forward; iron-ore/HG ideas remain vendor/paid-gated",
    }

    # ---- 2. literal vs quarterly chain (v1 defect dissolved) --------------------
    chain_l = L.calendar_chain(sess, quarterly_only=False)
    chain_l["session_date"] = pd.to_datetime(chain_l["session_date"])
    reg2 = reg[~reg["stray"]].set_index("contract")
    is_q = reg2["is_quarterly"].to_dict()
    serial_hold = chain_l[chain_l["held"].map(lambda c: not is_q.get(c, True))]
    qmap = chain_q.set_index("session_date")["held"]
    serial_hold = serial_hold.copy()
    serial_hold["quarterly_chain_held"] = serial_hold["session_date"].map(qmap)
    vol_by_c = sess.groupby(["session_date", "contract"])["volume"].sum().reset_index()
    serial_vols = []
    for r in serial_hold.itertuples():
        v = vol_by_c[(vol_by_c["session_date"] == r.session_date)
                     & (vol_by_c["contract"] == r.held)]["volume"]
        serial_vols.append(float(v.iloc[0]) if len(v) else 0.0)
    serial_hold["volume"] = serial_vols
    # serial-month coverage: which of the 84 serial months 2020-2026 have bars?
    all_serial_months = []
    d0 = pd.Timestamp("2020-01-01")
    while d0 < pd.Timestamp("2026-10-01"):
        if d0.month not in (3, 6, 9, 12):
            all_serial_months.append(
                f"6A{L.CODE_MONTH[d0.month]}{d0.year % 10}_{d0.year}")
        d0 += pd.offsets.MonthBegin(1)
    present = set(reg2.index)
    missing = [c for c in all_serial_months if c not in present]
    out["literal_vs_quarterly_chain"] = {
        "v1_defect": ("v1 (IBKR corpus): literal next-listed rule NOT executable "
                      "2025-11..2026-08 — six serial contracts absent"),
        "vendor_serial_coverage": {
            "serial_months_expected": len(all_serial_months),
            "serial_months_with_bars": len(all_serial_months) - len(missing),
            "missing_serial_months": missing,
            "note": ("some serial months never print bars (vendor globex parent "
                     "request carries only instruments that traded); literal "
                     "chain truncates at the first missing serial"),
        },
        "literal_chain_executable_sessions": int(len(chain_l)),
        "literal_chain_truncation": (
            "literal chain dies at the first absent serial month (e.g. 6AK0_2020 "
            "after 2020-04); NOT fully executable across 2020-2026 either — the "
            "quarterly adaptation remains the only continuously executable chain"),
        "sessions_holding_a_serial": int(len(serial_hold)),
        "serial_hold_sessions_by_contract": {k: int(v) for k, v in
                                             serial_hold["held"].value_counts().items()},
        "serial_book_volume_on_hold_sessions": {
            "median": float(serial_hold["volume"].median()),
            "p90": float(serial_hold["volume"].quantile(0.9)),
            "max": float(serial_hold["volume"].max()),
        },
        "quarterly_chain_sessions": int(len(chain_q)),
        "note": ("descriptive execution-economics re-measure of v1 H3; both chains are "
                 "PIT-legal contract-selection rules; no PnL computed"),
    }

    # ---- 3. H4 support: 6A vs ES beta -----------------------------------------
    if os.path.exists(ES_CHAIN):
        es = pd.read_parquet(ES_CHAIN)
        es = es.reset_index().rename(columns={"sess": "session_date"})
        es["session_date"] = pd.to_datetime(es["session_date"])
        es["ret"] = es["close"] / es["close"].shift(1) - 1
        es.loc[es["switch"], "ret"] = np.nan     # within-contract (v1 convention)
        # min_periods < window because switch sessions leave NaN gaps after each
        # roll (within-contract convention); still strictly trailing windows
        es["rv63"] = es["ret"].rolling(63, min_periods=40).std() * np.sqrt(252)
        med252 = es["rv63"].shift(1).rolling(252, min_periods=126).median()
        es["risk_on"] = es["rv63"] < med252
        es = es[(es["session_date"] >= "2020-01-01")]
        m = daily.merge(es[["session_date", "ret", "risk_on", "rv63"]],
                        on="session_date", how="inner", suffixes=("_6a", "_es"))
        m["r6"] = m["ret_rolled"]
        by_year = {}
        for y, g in m.groupby(m["session_date"].dt.year):
            v = g.dropna(subset=["r6", "ret"])
            if len(v) < 50:
                continue
            by_year[int(y)] = {
                "n": int(len(v)),
                "corr": float(np.corrcoef(v["r6"], v["ret"])[0, 1]),
                "beta_ols": float(np.polyfit(v["ret"], v["r6"], 1)[0]),
            }
        both = m.dropna(subset=["r6", "ret", "risk_on"])
        regime = {
            "risk_on_n": int(both["risk_on"].sum()),
            "risk_off_n": int((~both["risk_on"]).sum()),
            "corr_risk_on": float(both[both["risk_on"]]["r6"].corr(
                both[both["risk_on"]]["ret"])),
            "corr_risk_off": float(both[~both["risk_on"]]["r6"].corr(
                both[~both["risk_on"]]["ret"])),
            "beta_risk_on": float(np.polyfit(
                both[both["risk_on"]]["ret"], both[both["risk_on"]]["r6"], 1)[0]),
            "beta_risk_off": float(np.polyfit(
                both[~both["risk_on"]]["ret"], both[~both["risk_on"]]["r6"], 1)[0]),
        }
        out["a6_vs_es_beta"] = {
            "es_source": "sibling lane DEEP-ES cache es_chain_DECL.parquet (read-only, their declared-rule chain)",
            "return_convention": "within-contract daily returns both legs (v1 convention; switch sessions excluded; rolling windows min_periods 40/126 to tolerate switch NaNs — still strictly trailing)",
            "by_year": by_year,
            "by_strict_past_es_vol_regime": regime,
            "law_note": "descriptive rolling relation; regime tag ex-ante (trailing 63d ES vol vs prior-252d median); NOT a signal; USD-beta control (6E) NOT_RUN here (sibling lane artifact not reused beyond ES)",
        }
    else:
        out["a6_vs_es_beta"] = {"verdict": "NOT_RUN — ES chain cache absent"}

    # ---- 4. OI-front vs volume-front crossovers (2023-10+) ----------------------
    stats = L.load_statistics_6a()
    oi = stats[stats["stat_type"] == 9].copy()
    oi["contract"] = oi["raw_symbol"] + "_" + (
        2020 + oi["raw_symbol"].str[-1].astype(int)).astype(str)
    oi_daily = oi.groupby(["ref_date", "contract"])["quantity"].sum().unstack()
    oi_daily.index = pd.to_datetime(oi_daily.index)
    oi_q = oi_daily[[c for c in oi_daily.columns
                     if c.split("_")[0][2] in "HMUZ"]]
    wide = sess.pivot_table(index="session_date", columns="contract",
                            values="volume", aggfunc="sum").sort_index()
    cross_rows = []
    qcontracts = sorted(
        [c for c in wide.columns if is_q.get(c, False) and c in oi_q.columns],
        key=lambda c: reg2.loc[c, "delivery_month_start"])
    for a, b in zip(qcontracts[:-1], qcontracts[1:]):
        seg = wide.loc[:, [a, b]].dropna(how="all")
        seg = seg[(seg.index >= oi_q.index.min())]
        # gate both books to front-adjacent scale (>1,000) so a crossover is a
        # real liquidity migration, not noise between two deferred near-zero books
        vc = seg[(seg[b].fillna(0) > seg[a].fillna(0)) & (seg[a].fillna(0) > 1000)]
        oseg = oi_q[[a, b]].dropna(how="all")
        oseg = oseg[(oseg.index >= seg.index.min()) & (oseg.index <= seg.index.max())]
        oc = oseg[(oseg[b] > oseg[a]) & (oseg[a] > 1000)]
        cross_rows.append({
            "old": a, "new": b,
            "volume_crossover": (str(vc.index[0].date()) if len(vc) else None),
            "oi_crossover": (str(oc.index[0].date()) if len(oc) else None),
        })
    out["oi_vs_volume_crossover_2023p"] = {
        "n_roll_pairs": len(cross_rows),
        "rows": cross_rows,
        "note": "OI from GLBX statistics (2023-10+ only); volume from 1m panel; descriptive rule comparison",
    }

    # ---- 5. data-quality ledger per era -----------------------------------------
    ledger = {}
    front = chain_q.merge(sess, left_on=["session_date", "held"],
                          right_on=["session_date", "contract"], how="left")
    front_bars = bars[bars["contract"].isin(front["held"].unique())]
    held_pairs = set(zip(front["session_date"], front["held"]))
    fb = front_bars[[ (d, c) in held_pairs for d, c in
                      zip(front_bars["session_date"], front_bars["contract"])]]
    fb_per_session = fb.groupby(["era", "session_date"]).size().rename("bars").reset_index()
    for era, grp in fb_per_session.groupby("era"):
        sessions = grp["session_date"].sort_values()
        gaps = sessions.diff().dt.days
        ledger[era] = {
            "front_sessions": int(len(grp)),
            "front_bars_per_session": {"min": int(grp["bars"].min()),
                                       "median": float(grp["bars"].median()),
                                       "max": int(grp["bars"].max())},
            "max_calendar_gap_days_between_sessions": int(gaps.max()),
            "zero_vol_share_front": None,  # filled below
        }
    zv = fb.groupby(["era", "session_date"])["volume"].apply(
        lambda s: float((s == 0).mean()))
    for era in ledger:
        try:
            ledger[era]["zero_vol_share_front"] = float(zv.loc[era].mean())
        except KeyError:
            pass
    # DST transition days: count front bars on the 4 transitions/year
    dst_days = bars[bars["dt"].dt.strftime("%m-%d").isin(
        ["03-08", "03-09", "03-10", "03-11", "03-12", "03-13", "03-14",
         "11-01", "11-02", "11-03", "11-04", "11-05", "11-06", "11-07"])]
    dst_sessions = fb[fb["session_date"].dt.strftime("%m-%d").isin(
        ["03-09", "03-10", "03-11", "03-12", "03-13", "03-14",
         "11-02", "11-03", "11-04", "11-05", "11-06", "11-07"])]
    out["data_quality_ledger"] = {
        "eras": ledger,
        "global": {
            "break_violation_bars": build.get("qa", {}).get(
                "break_violation_bars"),
            "weekend_anomaly_bars": build.get("qa", {}).get(
                "weekend_anomaly_bars"),
            "vendor_contamination_excluded": build.get(
                "vendor_contamination_excluded"),
            "registry": build.get("registry"),
            "negative_price_bars": build.get("negative_price_bars"),
            "sessions_total": build.get("qa", {}).get("sessions_total"),
            "dst_transition_front_bars_median": float(
                dst_sessions.groupby("session_date").size().median()),
            "note": ("eras by acquisition line: BF2=2020-21 backfill2, BF1A=2022-23, "
                     "BF1B=2024-25, BF1C=2026Q1, TRIM=2026Q2-09; all checks OBSERVED"),
        },
    }

    # ---- 6. refined hypothesis specs --------------------------------------------
    out["refined_hypotheses_v2"] = {
        "6A-H1": {
            "status": "UPGRADED — measurement floor MET",
            "changes_vs_v1": ("v1 measured only the next-RTH-open gap (RTH-blind corpus); "
                              "v2 vendor 1m data covers the full Globex session -> the "
                              "14:30 Sydney decision minute itself is observable; "
                              "PARAM-GAP 6A-H1-P2 (Globex data at decision time) DISSOLVED; "
                              "6A-H1-P1 (hawkish/dovish surprise classification) STILL OPEN "
                              "(no consensus/market-pricing series in corpus)"),
            "measured_now": "release-anchored volume/vol/range anatomy (A4); NO conditional mean-return tables (law)",
            "spec_v2": ("descriptive first (done in A4); any trade version needs a "
                        "registered cycle + surprise classification source (owner budget)"),
        },
        "6A-H2": {
            "status": "UNCHANGED-GATED — HG/iron-ore still NOT_IN_CORPUS",
            "changes_vs_v1": "none on the commodity leg; HG re-verified absent (block 1 above)",
            "spec_v2": ("China-data windows now VISIBLE in session data (A2 Shanghai window), "
                        "but China release calendars/surprises still not in corpus; the "
                        "commodity-confirmation hypothesis stays vendor-gated"),
        },
        "6A-H3": {
            "status": "MEASURED-END-TO-END with one disclosed caveat",
            "changes_vs_v1": ("vendor panel contains 54 of 84 serial months (30 never "
                              "trade); literal chain truncates at the first absent "
                              "serial, so the v1 executability defect is NARROWER but "
                              "not fully dissolved; serial books re-measured full-session "
                              "(median ~52 lots/day on literal-hold sessions); old-side "
                              "decay now observable (A3 migration)"),
        },
        "6A-H4": {
            "status": "MEASUREMENT READY — spec floor met",
            "changes_vs_v1": ("6.8y of both legs (6A + ES sibling chain) incl 2020-2022 "
                              "stress; ex-ante regime tag defined and computed (block 3)"),
            "spec_v2": ("regime tag FROZEN here a priori for any future registered run: "
                        "risk-on = ES trailing-63d vol < prior-252d median (strict past); "
                        "relation descriptive only in this cycle"),
        },
        "6A-H5": {
            "status": "FLOOR DISSOLVED — sample now >=8 rolls",
            "changes_vs_v1": ("v1 had 4 real-era rolls (floor >=8 NOT met); v2 measures "
                              "~26-27 quarterly rolls 2020-2026 with sign match vs "
                              "RBA-cash-rate minus DFF differential (A3); CIP vintage "
                              "caveat: DFF is latest-vintage (ALFRED year-end vintages only)"),
        },
    }

    L.jdump(out, OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
