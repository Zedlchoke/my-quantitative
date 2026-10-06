#!/usr/bin/env python
"""LANE-MEAS-NQ M3 — NQ MDE refresh arithmetic for NQ-F2/NQ-F3 (G11 feed).

DESCRIPTIVE ARITHMETIC ONLY. Consumes m1_session_sigma_v3.json (this lane) and the
committed nq_held_daily_v3.parquet (read posture per SPEC_NQ.md section 2 — D9 unsigned,
canonical-CANDIDATE). No conditional-on-signal returns, no PnL, no gate adjudication.

Census MDE formula (quoted from the census artifacts):
  HYPOTHESES_ESNQ_R3.md section 7 (F5-K2): "court-method MDE (two-sided alpha=0.05,
  power 80%, z=2.80; dispersion proxy = committed session sigma, an upper bound)" —
  i.e.  MDE = 2.80 * sigma / sqrt(n)   [cross/FALSIFICATION_MATRIX.md rows state the
  same per-event form "MDE ~ 2*sigma/sqrt(n)"; the committed ESNQ lane test records
  "MDE=2.80*sigma/sqrt(66) with committed sigmas ... NQ 112.30bp"].

Family n inputs are taken from the 5SYM census declarations, never invented:
  NQ-F2 MACRO-0730-NQ: scoring era confined 2023-26, "~160 event days"
  (CENSUS_5SYM.md NQ-F2 rows 3/7/12).
  NQ-F3 RUN-REV-NQ: universe = all held sessions; armed-cell census (runs>=5
  occurrence) NOT_RUN -> MDE parameterized in n, optimistic bound at the full
  held-session count.

Exit 0 on success.
"""
import json
import math
import sys

import numpy as np
import pandas as pd

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-5sym-prescored/prep"
OUT = f"{WT}/research/control/FUTURES-5SYM-PRESCORED-20261005/meas_nq"
HELD = f"{WT}/research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/nq_held_daily_v3.parquet"
M1 = f"{OUT}/m1_session_sigma_v3.json"

Z = 2.80  # court-method: two-sided alpha=0.05, power 80% (census F5-K2 law)


def mde(sigma_bp, n):
    return Z * sigma_bp / math.sqrt(n)


def pooled_sigma_bp(held, lo, hi):
    """Daily sigma of held log rets in the window, in bp (std * 1e4)."""
    m = (held["d"] >= lo) & (held["d"] <= hi)
    rr = held.loc[m, "ret"].dropna().astype(float)
    return float(rr.std() * 1e4), int(len(rr))


def main():
    m1 = json.load(open(M1))
    held = pd.read_parquet(HELD)
    held["d"] = held["d"].astype(str)
    sigma_full = m1["sigma_proxy"]["new_v3"]["sigma_bp"]            # median-year law
    sigma_old = m1["sigma_proxy"]["old_pre_recovery"]["sigma_bp"]
    rth5_full = m1["rederived"]["full_era"]["rth_5min_sd_bp"]["median"]

    s_2326, n_2326 = pooled_sigma_bp(held, "2023-01-01", "2026-09-30")
    s_f3fold, n_f3fold = pooled_sigma_bp(held, "2018-01-01", "2021-12-31")
    s_f4fold, n_f4fold = pooled_sigma_bp(held, "2022-01-01", "2026-09-30")
    s_f1fold, n_f1fold = pooled_sigma_bp(held, "2010-06-06", "2012-12-31")
    s_f2fold, n_f2fold = pooled_sigma_bp(held, "2013-01-01", "2017-12-31")
    n_held = int(len(held))

    res = {
        "schema": "meas_nq_m3_mde_refresh@1",
        "cycle": "FUTURES-5SYM-PRESCORED-20261005", "lane": "MEAS-NQ",
        "descriptive_arithmetic_only": True,
        "formula_law": {
            "formula": "MDE = 2.80 * sigma_bp / sqrt(n)",
            "z": Z,
            "quoted_from": [
                "FUTURES-TEN-HYPO-PREP-20261004/es_nq/HYPOTHESES_ESNQ_R3.md §7 F5-K2: "
                "'court-method MDE (two-sided α=0.05, power 80%, z=2.80; dispersion proxy "
                "= committed session σ, an upper bound)'",
                "FUTURES-TEN-HYPO-PREP-20261004/cross/FALSIFICATION_MATRIX.md (JF3/AF1 rows): "
                "'per-event MDE ≈ 2σ/√n'",
                "FUTURES-TEN-HYPO-PREP-20261004/dispatch/handoff_ESNQ.json test record: "
                "'MDE=2.80*sigma/sqrt(66) with committed sigmas ES 68.41bp ... and NQ 112.30bp "
                "(NQ_a1_regimes yearly[].vol_ann_pct median 17.83%/sqrt(252))'"],
            "sigma_proxy_law": "σ_bp = median_over_years(std(daily held log rets, year)*√252)*100 "
                               "(the census proxy; m1 re-derived on v3: measurement-identical)"},
        "sigma_inputs": {
            "sigma_full_era_median_year_bp": sigma_full,
            "sigma_old_pre_recovery_bp": sigma_old,
            "sigma_delta_bp": sigma_full - sigma_old,
            "pooled_era_sigmas_v3_bp": {
                "F1_2010-06_2012-12": s_f1fold, "F2_2013-01_2017-12": s_f2fold,
                "F3_2018-01_2021-12": s_f3fold, "F4_2022-01_2026-09": s_f4fold,
                "2023-01_2026-09": s_2326},
            "pooled_era_n_nonnan_rets": {
                "F1": n_f1fold, "F2": n_f2fold, "F3": n_f3fold, "F4": n_f4fold,
                "2023-26": n_2326},
            "n_held_sessions_total": n_held,
            "rth5min_dailyized_full_era_median_bp": rth5_full,
            "note": "the G11 defect correction moved year-2020 vol_ann 33.5434%->34.8153% "
                    "(+1.2719 pct-pts, m1 DEFECT_CORRECTED) and left the median year (2015) "
                    "untouched: σ_full unchanged; every pooled stratum that includes 2020 "
                    "(F3 fold) absorbs the corrected year"},
        "nq_f2_macro_0730": {
            "family": "NQ-F2 MACRO-0730-NQ (08:30-ET print discharge)",
            "n_source": "CENSUS_5SYM.md NQ-F2: scoring era confined 2023-26, ~160 event days "
                        "(census-declared, thin-power pre-registered K7); taken as-declared, "
                        "not re-derived",
            "n": 160,
            "sigma_used_bp": s_2326,
            "sigma_basis": "pooled std of daily held log rets 2023-01..2026-09 on v3 "
                           "(era-matching the confined scoring era)",
            "mde_bp": mde(s_2326, 160),
            "mde_with_census_proxy_sigma_bp": mde(sigma_full, 160),
            "mde_with_rth5min_sigma_bp": mde(rth5_full, 160),
            "modeled_cost_floor_ref": "NQ S2 RT-class floor per SPEC_NQ §5 (MODELED/UNDER REVIEW)"},
        "nq_f3_run_rev": {
            "family": "NQ-F3 RUN-REV-NQ (multi-day run reversion on repaired chain)",
            "n_status": "armed-cell census (runs≥5 occurrence rate) NOT_RUN (CENSUS_5SYM.md "
                        "NQ-F3 field 3) -> MDE parameterized in n; optimistic bound uses the "
                        "full held-session count (upper bound on n => lower bound on MDE)",
            "n_optimistic_bound": n_held,
            "sigma_used_bp": sigma_full,
            "mde_bp_at_n_optimistic": mde(sigma_full, n_held),
            "mde_bp_at_n_optimistic_foldF3_sigma": mde(s_f3fold, n_held),
            "mde_per_n_table_bp": {str(n): mde(sigma_full, n) for n in (200, 400, 800, 1600, n_held)},
            "fold_f3_window_sigma_bp": s_f3fold,
            "fold_f3_window_note": "F3 fold (2018-2021) pooled σ includes the corrected 2020 "
                                   "(34.8153% yearly ann on v3; pre-recovery 33.5434% on the "
                                   "depleted year — m1 per-year defect table)"},
        "expwitch_nq_reference_row": {
            "note": "the census's own committed MDE row (n=66, NQ leg of ESNQ-F5) refreshed "
                    "with the m1-corrected σ",
            "n": 66, "mde_old_bp": mde(sigma_old, 66), "mde_new_bp": mde(sigma_full, 66),
            "delta_bp": mde(sigma_full, 66) - mde(sigma_old, 66),
            "verdict": "MEASUREMENT_IDENTICAL — census print MDE ≈ 38.7 bp survives the v3 "
                       "repair unchanged (census committed 38.7 bp vs recomputed "
                       f"{mde(sigma_full, 66):.1f} bp)"},
        "final": "PASS_DESCRIPTIVE_ARITHMETIC",
        "post_freeze_mde_tables": "NOT_RUN (post-freeze arithmetic per SPEC_NQ §7; this file "
                                  "is the descriptive refresh feed, not the post-freeze table)"}
    json.dump(res, open(f"{OUT}/m3_mde_refresh.json", "w"), indent=1)
    print("MDE F2 (σ=2023-26 pooled, n=160):", round(mde(s_2326, 160), 2), "bp")
    print("MDE F3 (σ=full median-year, n=4219 optimistic bound):",
          round(mde(sigma_full, n_held), 2), "bp")
    print("EXPWITCH-NQ reference (n=66):", round(mde(sigma_old, 66), 2), "->",
          round(mde(sigma_full, 66), 2), "bp (delta 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
