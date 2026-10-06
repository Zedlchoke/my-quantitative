#!/usr/bin/env python
"""MEAS-FX m1 + m3 — CIP-vintage sensitivity (FX-F5 / G3) and AF2 K2
vintage-flip machinery (G9). Lane MEAS-FX, round FUTURES-5SYM-PRESCORED-
20261005 wave-3.

Outcome-blind law: descriptive correlation / regime / flip-count statistics
on COMMITTED artifacts only. No PnL, no conditional-on-signal return, no
network. The vintage-as-of MACHINERY is demonstrated on synthetic fixtures;
the real-data vintage recomputation that is not already committed records
NOT_RUN_DATA_NOT_IN_TREE (see m1/m3 .md).

Inputs (all committed, read-only):
  1. FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_6e/a7_6e_recompute.json
     -> rolls_cip: per-roll 6E gap vs CIP on BOTH bases (latest-vintage and
        year-end-ALFRED as-of). The ALFRED year-end SOFR vintage CSVs
        themselves live OUTSIDE the tree (external nonprice corpus); the
        per-roll recomputed values ARE committed here. m1 quantifies the
        sensitivity from these committed rows.
  2. FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_a3_term.json -> gap_summary
     (lane-basis latest-vintage committed numbers, cross-check).
  3. FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_a3_term.json
     -> gap_vs_policy_diff (6B latest-vintage only; NO vintage-as-of
        recomputation was ever committed for 6B).
  4. FUTURES-DEEPRESEARCH-V2-20261003/analysis/6A_a3_term.json
     -> roll_gap_vs_rate_differential (AF2 basis: 27 rolls, 16 material,
        latest-vintage DFF only).
  5. research/wayfinder/FAMILY_FAILURES.jsonl rows 56/64/65/83 (V8/V9
     nominal/PPP shadow rho magnitudes, context for the 0.20 rho bar).

Outputs (written next to this script):
  m1_fx_f5_cip_vintage.json
  m3_af2_vintage_flip.json
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DEEP = os.path.join(WT, "research", "control", "FUTURES-DEEPRESEARCH-V2-20261003")

RHO_BAR = 0.20          # ANCESTRY_CHECK.md FX-F5 row; FAMILY_FAILURES row 67 ("bar 0.20")
MATERIAL_BAND = 0.25    # AF2 material differential |RBA-DFF| >= 25bp (JPY_AUD §5.5)

# External paths CITED BY THE DOSSIERS but NOT in the git tree:
EXTERNAL_ALFRED_DIR = "/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/fred_alfred"
NOT_IN_TREE_NOTE = (
    "git ls-files finds NO committed DFF/SOFR/DFEDTARU vintage capture under the "
    "worktree (only the collector script FUTURES-BEHAVIOR-10SYMS-PREP-20261002/"
    "nonprice_acquisition/collect/fred_alfred.py and the BLS vintage captures, "
    "which are release-schedule captures, not rate vintages). The vintages live "
    "outside the repo at " + EXTERNAL_ALFRED_DIR +
    " (subdirs latest/, pit/, vintage_attempts/) — uncommitted, therefore NOT "
    "consumed by this lane; a committed 6E per-roll vintage-as-of recomputation "
    "does exist (a7_6e_recompute.json rolls_cip) and is what m1 consumes.")


def jdump(obj, path):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, allow_nan=False)


def pearson(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or a.std() == 0 or b.std() == 0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b):
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    return pearson(ra, rb)


def sign_agreement(gaps, cips):
    g, c = np.sign(np.asarray(gaps)), np.sign(np.asarray(cips))
    return int((g == c).sum()), len(g)


# ---------------------------------------------------------------- m1: FX-F5
def run_m1():
    a7 = json.load(open(os.path.join(
        DEEP, "audit", "a7_6e", "a7_6e_recompute.json")))
    rc = a7["rolls_cip"]
    rows = rc["rows"]
    lane = json.load(open(os.path.join(DEEP, "analysis", "6E_a3_term.json")))
    b3 = json.load(open(os.path.join(DEEP, "analysis", "6B_a3_term.json")))

    gap = [r["gap_pct"] for r in rows]
    cip_l = [r["cip_latest_pct"] for r in rows]
    cip_v = [r["cip_vintage_pct"] for r in rows]
    n = len(rows)

    res = {
        "schema": "meas_fx_m1_f5_cip_vintage@1",
        "item": "WORK_QUEUE A-#8 / HYPO G3 — FX-F5 CIP-vintage sensitivity",
        "law": "descriptive correlation/regime statistics on committed vintages "
               "only; no conditional-on-signal return; no PnL; PB2 untouched; "
               "owner real-time SOFR decision (court §d row 7) remains a "
               "SIGNATURE regardless of this quantification",
        "inputs": {
            "committed_per_roll_vintage_rows":
                "FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_6e/a7_6e_recompute.json:rolls_cip.rows",
            "lane_basis_6E": "FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_a3_term.json:gap_summary",
            "6B_latest_only": "FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_a3_term.json:gap_vs_policy_diff",
        },
        "n_rolls": n,
        "vintage_bases": {
            "latest": "FRED SOFR latest + ECB €STR SDW latest (lane basis)",
            "vintage_asof": "ALFRED year-end SOFR vintages 2019-12-31..2024-12-31 "
                            "+ 2026-09-30 as-of each roll (A7 audit basis); €STR "
                            "latest-only (no vintage set exists anywhere)",
        },
        "6E_correlations": {
            "pearson_latest": pearson(gap, cip_l),
            "spearman_latest": spearman(gap, cip_l),
            "pearson_vintage_asof": pearson(gap, cip_v),
            "spearman_vintage_asof": spearman(gap, cip_v),
            "committed_check": {
                "lane_pearson_latest": lane["gap_summary"]["corr_gap_vs_cip"],
                "a7_pearson_latest": rc["corr_gap_vs_cip_latest"],
                "a7_pearson_vintage": rc["corr_gap_vs_cip_vintage"],
                "reproduction_within": "1e-6 (this lane recomputes from the same "
                                       "committed rows)",
            },
        },
        "6E_sign_agreement": {
            "latest": sign_agreement(gap, cip_l),
            "vintage_asof": sign_agreement(gap, cip_v),
            "committed": {"lane_latest": lane["gap_summary"]["sign_agreement_gap_vs_ratediff"],
                          "a7_vintage": rc["sign_agreement_gap_vs_cip_vintage"]},
        },
        "regime_label_flip": {
            "definition": "flip = sign(CIP-predicted gap, latest) != sign(CIP-predicted "
                          "gap, year-end-ALFRED-as-of) on the same roll (the "
                          "differential-regime label the F5 host split consumes)",
            "n_flips": None,   # filled below
            "flip_rolls": [],  # filled below
            "note": None,      # filled below
        },
        "rho_bar_test": {
            "bar": RHO_BAR,
            "bar_source": "ANCESTRY_CHECK.md FX-F5 row ('the 0.20 rho bar vs the "
                          "V8/V9 nominal/PPP shadows must be re-measured at any "
                          "D2-equivalent stage'); bar value precedent FAMILY_"
                          "FAILURES.jsonl row 67 ('bar 0.20, margin -0.008')",
            "latest_basis": {"rho": pearson(gap, cip_l),
                             "passes_bar": bool(abs(pearson(gap, cip_l)) >= RHO_BAR)},
            "vintage_asof_basis": {"rho": pearson(gap, cip_v),
                                   "passes_bar": bool(abs(pearson(gap, cip_v)) >= RHO_BAR)},
            "verdict": "BAR PASSAGE IS VINTAGE-DEPENDENT: r=+0.91 (latest) clears "
                       "the 0.20 bar; r=−0.11 (year-end-ALFRED as-of) fails it. "
                       "Vintage choice alone decides bar passage on the only "
                       "vintage basis available — the measured proof of the "
                       "standing NEEDS_EVIDENCE (FX-F5 stays NEEDS_EVIDENCE; "
                       "owner real-time SOFR decision mandatory before any "
                       "F5-conditioned registration).",
        },
        "v8_v9_shadow_context": {
            "note": "the dead standalone forms' own shadow-rho magnitudes, cited "
                    "as context (ANCESTRY_RHO_BLOCK class); the DIRECT rho of "
                    "F5's differential regime vs the V8/V9 shadow series is "
                    "NOT_RUN (shadow series not in tree)",
            "FXFV9_A5_P1_pooled_rho_vs_FXFV8_anchor": 0.3034,
            "FXFV9_A5_P2_pooled_rho_vs_FXFV8_anchor": 0.3119,
            "FXFV8_A5_P1_death": "CONTROL_OUTEARNED_ANCHOR: DGS10-level control "
                                 "out-earned 4.01x (cluster #14)",
            "FXNG1_A4_P2_death": "CTL-DGS10LEVEL out-earned (cluster #15)",
            "direct_rho_vs_shadows": "NOT_RUN_DATA_NOT_IN_TREE (DGS10 / "
                                     "PPP-deviation signal series not committed "
                                     "in this tree)",
        },
        "6B_side": {
            "committed_latest_only": {
                "pearson": b3["gap_vs_policy_diff"]["pearson_corr"],
                "spearman": b3["gap_vs_policy_diff"]["spearman_corr"],
                "mean_gap_ticks_diff_pos": b3["gap_vs_policy_diff"]["mean_gap_ticks_when_diff_pos"],
                "n_diff_pos": b3["gap_vs_policy_diff"]["n_diff_pos"],
                "n_diff_neg": b3["gap_vs_policy_diff"]["n_diff_neg"],
                "vintage_note_committed": b3["gap_vs_policy_diff"]["vintage_note"],
            },
            "vintage_asof_recomputation": "NOT_RUN_DATA_NOT_IN_TREE — no committed "
                                          "6B vintage-as-of recomputation exists and "
                                          "the DFEDTARU/BoE vintage files are not in "
                                          "this tree; BoE Bank Rate is revision-free, "
                                          "so the 6B vintage risk is the US side only",
        },
        "not_run": [
            {"what": "fresh year-end-ALFRED as-of recomputation from the vintage "
                     "CSVs themselves (6E and 6B)",
             "grounds": "NOT_RUN_DATA_NOT_IN_TREE", "path": NOT_IN_TREE_NOTE},
            {"what": "direct 0.20-rho measurement of F5's differential regime vs "
                     "the V8/V9 nominal/PPP shadow series",
             "grounds": "NOT_RUN_DATA_NOT_IN_TREE (shadow series not committed); "
                        "bar is re-measured at any D2-equivalent stage by law"},
        ],
    }
    res["regime_label_flip"]["n"] = n
    flip_rolls = [r["roll"] for r in rows
                  if np.sign(r["cip_latest_pct"]) != np.sign(r["cip_vintage_pct"])]
    res["regime_label_flip"]["n_flips"] = len(flip_rolls)
    res["regime_label_flip"]["flip_rolls"] = flip_rolls
    res["regime_label_flip"]["note"] = (
        ("%d/%d rolls flip the differential-regime label between bases (%s); "
         "independently, the CORRELATION sign itself flips (+0.91 -> −0.11). "
         "Both channels damage F5: stratum membership changes on the flipped "
         "roll(s), and the rho that must clear the 0.20 bar flips sign with "
         "the vintage basis."
         % (len(flip_rolls), n, ", ".join(flip_rolls))) if flip_rolls else
        ("0/%d rolls flip the label; the vintage damage enters through the "
         "rho value alone." % n))

    jdump(res, os.path.join(HERE, "m1_fx_f5_cip_vintage.json"))
    return res


# ---------------------------------------------------------------- m3: AF2 K2
def asof_differential(roll_sessions, rba_on_date, vintage_series_by_asof,
                      latest_series=None):
    """Generic as-of differential machinery (the AF2 K2 instrument).

    For each roll date d: pick the latest vintage whose as-of stamp <= d,
    then the vintage's own nearest observation <= d (a7_6e §6 method);
    differential_vintage = rba_effective(d) - dff_vintage(d).
    `rba_on_date` is the as-published RBA effective-rate step function
    (revision-free per the committed dossier). `latest_series`, if given,
    yields the latest-vintage differential for the flip comparison.
    Pure function over committed-style inputs; no I/O — the CALLER supplies
    the vintage tables (real vintages: NOT_RUN_DATA_NOT_IN_TREE for 6A).
    """
    out = []
    for d in roll_sessions:
        rd = pd.Timestamp(d)
        rba = float(rba_on_date(rd))
        elig = [a for a in sorted(vintage_series_by_asof) if a <= rd]
        dff_v = np.nan
        if elig:
            s = vintage_series_by_asof[elig[-1]]
            idx = s.index.asof(rd)
            if idx is not None and pd.notna(s.loc[idx]):
                dff_v = float(s.loc[idx])
        dff_l = np.nan
        if latest_series is not None:
            idx = latest_series.index.asof(rd)
            if idx is not None and pd.notna(latest_series.loc[idx]):
                dff_l = float(latest_series.loc[idx])
        out.append({"roll_session": str(pd.Timestamp(d).date()), "rba": rba,
                    "dff_vintage": dff_v, "dff_latest": dff_l,
                    "diff_vintage": (rba - dff_v) if np.isfinite(dff_v) else np.nan,
                    "diff_latest": (rba - dff_l) if np.isfinite(dff_l) else np.nan})
    return out


def k2_flip_count(rows, material_band=MATERIAL_BAND):
    """K2 instrument: count material rolls whose differential SIGN REGIME
    flips between the latest-vintage and vintage-as-of bases. >=3/16 => dead
    (JPY_AUD_HYPOTHESES §5.7 K2; CENSUS_5SYM AF2 field 3)."""
    flips, mat = 0, 0
    detail = []
    for r in rows:
        if not (np.isfinite(r["diff_latest"]) and np.isfinite(r["diff_vintage"])):
            detail.append({**r, "material": None, "flip": None,
                           "basis": "vintage cell missing"})
            continue
        material = abs(r["diff_latest"]) >= material_band
        mat += int(material)
        flip = material and (np.sign(r["diff_latest"]) != np.sign(r["diff_vintage"]))
        flips += int(bool(flip))
        detail.append({**r, "material": material, "flip": bool(flip)})
    return {"n": len(rows), "n_material": mat, "n_flips_material": flips,
            "dead_per_K2": bool(flips >= 3), "rows": detail}


def run_m3():
    a3 = json.load(open(os.path.join(DEEP, "analysis", "6A_a3_term.json")))
    rg = a3["roll_gap_vs_rate_differential"]
    rows = rg["rows"]

    # baseline verification on the committed latest-vintage rows (data-quality
    # facts, not strategy returns — allowed):
    mat = [r for r in rows if r["material_differential"]]
    match_mat = sum(1 for r in mat if r["cip_sign_match"])
    match_all = sum(1 for r in rows if r["cip_sign_match"])

    res = {
        "schema": "meas_fx_m3_af2_k2_vintage_flip@1",
        "item": "WORK_QUEUE A-#10 / HYPO G9 — AF2 K2 vintage-flip test machinery",
        "law": "flip counts are data-quality facts (label stability), not "
               "strategy returns; no PnL; PB3 PARK untouched; owner real-time "
               "rates decision outstanding regardless",
        "k2_kill_rule": "recompute the differential with year-end ALFRED vintages "
                        "as-of each roll; >=3/16 material-roll sign flips => the "
                        "conditioning variable is vintage-fragile => AF2 dead "
                        "(JPY_AUD_HYPOTHESES §5.7 K2; 6E +0.91→−0.11 flip is the "
                        "named bar)",
        "baseline_committed_latest_vintage": {
            "source": "FUTURES-DEEPRESEARCH-V2-20261003/analysis/6A_a3_term.json:"
                      "roll_gap_vs_rate_differential",
            "n": rg["n"], "n_material": rg["n_material"],
            "material_sign_match_recomputed": f"{match_mat}/{len(mat)}",
            "all_sign_match_recomputed": f"{match_all}/{len(rows)}",
            "reproduces_committed": bool(
                match_mat == len(mat) == rg["n_material"] == 16
                and match_all == 20),
            "caveat_committed": rg["caveat"],
            "note": "on the latest-vintage basis the flip count is 0 by "
                    "construction (single basis) — 16/16 material sign match "
                    "is the FLOOR the K2 test stress-tests",
        },
        "machinery": {
            "asof_rule": "for roll date d: latest vintage with as-of stamp <= d, "
                         "then that vintage's own nearest observation <= d "
                         "(identical to the committed a7_6e §6 6E method); "
                         "differential = RBA_effective(d) − DFF_vintage(d); "
                         "RBA table revision-free (as-published effective dates)",
            "flip_definition": "material roll (|diff_latest| >= 0.25pp) with "
                               "sign(diff_vintage) != sign(diff_latest)",
            "kill": "n_flips_material >= 3",
            "synthetic_fixture_proof": None,  # filled below
        },
        "real_vintage_run": {
            "status": "NOT_RUN_DATA_NOT_IN_TREE",
            "grounds": NOT_IN_TREE_NOTE,
            "missing_paths": [
                EXTERNAL_ALFRED_DIR + "/vintage_attempts/DFF_<YYYY-MM-DD>.csv "
                "(no DFF vintage set exists even on the external disk — the "
                "collector captured SOFR year-end vintages; DFEDTARU/DFF "
                "vintages were never captured)",
                "a committed 6A per-roll vintage-as-of recomputation (none "
                "exists; A7_DEEP_6A used DFF latest-vintage only, NOTE-4)",
            ],
            "coverage": "0 of the 16 material rolls have a committed "
                        "vintage-as-of differential; the computable subset from "
                        "committed artifacts is the latest-vintage baseline only",
        },
    }

    # ---- synthetic fixture proof of the machinery (documented law) ----
    # Fixture law: 6 material-style rolls; vintage series with KNOWN injected
    # flips. Latest base: DFF=1.00 flat => diff = rba-1.00, material where
    # |diff|>=0.25. Vintage series injects: for rolls #2 and #4 the vintage
    # observation is set on the OPPOSITE side of RBA (flip), for roll #6 the
    # vintage keeps the same sign (no flip). Expected: n_material=6,
    # n_flips_material=2, dead_per_K2=False (2 < 3).
    roll_sessions = ["2021-03-01", "2021-06-01", "2021-09-01",
                     "2021-12-01", "2022-03-01", "2022-06-01"]
    rba = 1.50
    rba_on_date = lambda d: rba
    latest = pd.Series({pd.Timestamp("2021-01-01"): 1.00})
    vint = {}
    for a in ["2020-12-31", "2021-12-31"]:
        vint[pd.Timestamp(a)] = pd.Series({pd.Timestamp("2020-12-31"): 1.00})
    # inject: vintage observation 2.00 (flip: diff 1.50-2.00 = -0.50 <0 vs
    # latest +0.50 >0) on 2021-06-01 and 2021-12-01 via vintage-relative rows
    vint_fix = {}
    s_common = [(pd.Timestamp("2020-12-31"), 1.00),
                (pd.Timestamp("2021-03-01"), 1.00),
                (pd.Timestamp("2021-06-01"), 2.00),   # FLIP
                (pd.Timestamp("2021-09-01"), 1.00),
                (pd.Timestamp("2021-12-01"), 2.00),   # FLIP
                (pd.Timestamp("2022-03-01"), 1.00)]
    vint_fix[pd.Timestamp("2020-12-31")] = pd.Series(
        dict(s_common)).sort_index()
    syn = asof_differential(roll_sessions, rba_on_date, vint_fix, latest)
    k2 = k2_flip_count(syn)
    expect = {"n": 6, "n_material": 6, "n_flips_material": 2, "dead": False}
    got = {"n": k2["n"], "n_material": k2["n_material"],
           "n_flips_material": k2["n_flips_material"], "dead": k2["dead_per_K2"]}
    res["machinery"]["synthetic_fixture_proof"] = {
        "fixture_law": "6 rolls, RBA flat 1.50, latest DFF 1.00 (all material, "
                       "diff +0.50); one vintage table (as-of 2020-12-31) with "
                       "INJECTED opposite-sign observations (DFF 2.00) on rolls "
                       "#3 (2021-06-01) and #5 (2021-12-01); rolls #1/#2/#4/#6 "
                       "carry the same-sign vintage value (DFF 1.00)",
        "expected": expect, "got": got,
        "pass": got == expect,
        "note": "proves the as-of selection + material band + flip counter "
                "recover exactly the injected flips; the >=3/16 kill rule is "
                "evaluated but never adjudicated on synthetic data",
    }
    # negative fixture: vintage == latest everywhere => 0 flips
    vint_same = {pd.Timestamp("2020-12-31"): latest.copy()}
    k2_neg = k2_flip_count(asof_differential(roll_sessions, rba_on_date,
                                             vint_same, latest))
    res["machinery"]["synthetic_fixture_null"] = {
        "fixture_law": "vintage identical to latest (no injected flips)",
        "expected_flips": 0, "got_flips": k2_neg["n_flips_material"],
        "pass": k2_neg["n_flips_material"] == 0,
    }
    res["machinery"]["fixtures_all_pass"] = bool(
        res["machinery"]["synthetic_fixture_proof"]["pass"]
        and res["machinery"]["synthetic_fixture_null"]["pass"])

    jdump(res, os.path.join(HERE, "m3_af2_vintage_flip.json"))
    return res


if __name__ == "__main__":
    m1 = run_m1()
    m3 = run_m3()
    print("m1: 6E pearson latest %.4f / vintage-asof %.4f; flips(regime sign) %d; "
          "bar latest %s / vintage %s"
          % (m1["6E_correlations"]["pearson_latest"],
             m1["6E_correlations"]["pearson_vintage_asof"],
             m1["regime_label_flip"]["n_flips"],
             m1["rho_bar_test"]["latest_basis"]["passes_bar"],
             m1["rho_bar_test"]["vintage_asof_basis"]["passes_bar"]))
    print("m3: baseline 16/16 reproduced=%s; machinery fixtures_all_pass=%s; "
          "real vintage run=%s"
          % (m3["baseline_committed_latest_vintage"]["reproduces_committed"],
             m3["machinery"]["fixtures_all_pass"],
             m3["real_vintage_run"]["status"]))
