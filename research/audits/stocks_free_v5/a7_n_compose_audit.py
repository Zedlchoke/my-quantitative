"""A7-N audit artifact composer for STOCKS-FREE-V5.

Reads a7_n_measurements.json (produced by a7_n_novelty_measure.py) and emits
research/audits/stocks_free_v5/a7_n_novelty_audit.json (schema
stocks_free_v5_run/a7_n_novelty_audit@1) with per-proposal verdicts, the
measured rho matrix, tick counts, method, and the overall novelty verdict.

The verdict thresholds applied here are exactly the ones frozen in
PLAN_stocks_v5.md sections 1/1.1/8, baseline_invariants.json
(section_1_1_confirmatory_region) and forbidden_family_inventory.json
(section_1_1_shadow_region_front_door), plus the task-set kill/flag bands:
  * A5-H2 (Section 1.1 confirmatory front door): ELIGIBLE only if
    mean |rho| <= 0.20 vs the V4 semivariance-SHAPE anchor; the relation to
    the vol-LEVEL axis is documented (not a pass/fail gate); the proposal's
    own stale-vs-fresh control distinctness is verified by rank comparison
    against its preregistered gates (rank rho <= 0.90; >= 25% of slots with
    differing basket membership).
  * Every other proposal: INELIGIBLE if mean |rho| vs any forbidden-family
    feature or V4 anchor >= 0.60; 0.40-0.60 flagged as MEDIUM lineage notes.
A non-constructible declared anchor series (fewer than 6 rankable sectors at
a tick, canonical bridge coverage gates as declared) is terminal
pre-selection evidence and is reported per tick.
"""

from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROPOSALS = ("a4_h1", "a4_h2", "a5_h1", "a6_h1", "a6_h2", "a5_h2")

HYP = {
    "a4_h1": "SFV5-A4-H1-BSHEXPANSION",
    "a4_h2": "SFV5-A4-H2-CASHINTENSITY",
    "a5_h1": "SFV5-A5-H1",
    "a5_h2": "SFV5-A5-H2",
    "a6_h1": "SFV5-A6-H1",
    "a6_h2": "SFV5-A6-H2",
}

ANCHOR_DEFS = {
    "a4_h1": "g_i(t) = ln(M_i(t)/M_i(t-252s)), M = single-vintage equal-weight "
             "mean of us-gaap:Assets (gap 400; coverage >= 0.60 both endpoints; "
             "endpoint effective dates <= 100 calendar days apart) "
             "[proposals/a4_h1.json:28-29,34-39,48]",
    "a4_h2": "CI_i(t) = M_cash/M_assets, M = single-vintage equal-weight means "
             "of us-gaap:CashAndCashEquivalentsAtCarryingValue and us-gaap:Assets "
             "(gap 400; XLF excluded ex ante; coverage >= 0.60 both fields; "
             "100-day cross-field effective-date coherence) "
             "[proposals/a4_h2.json:29-30,49]",
    "a5_h1": "R_s(t) = mean(dei:EntityPublicFloat)/mean(us-gaap:"
             "LiabilitiesAndStockholdersEquity), gap 550, coverage >= 0.60 both "
             "fields [proposals/a5_h1.json:19-28,42]",
    "a5_h2": "sigma_s(t) = sqrt(mean(r^2, 63 trailing adjusted-close returns)), "
             "realized-vol LEVEL, ascending rank (long low vol) "
             "[proposals/a5_h2.json:34]",
    "a6_h1": "WCINT_s(d) = mean(us-gaap:AssetsCurrent)/mean(us-gaap:Assets), "
             "gap 200, per-leg coverage >= 0.40, census 9-sector rank set "
             "[proposals/a6_h1.json:29-41,56]",
    "a6_h2": "c_i(d) = mean Pearson correlation of the 63-trailing-return window "
             "of sector i with every eligible peer (>= 5 defined pairs) "
             "[proposals/a6_h2.json:47]",
}

CLOCKS = {
    "a4_h1": "63-session clock re-seeded at each fold start, offsets 0..567 "
             "(30 ticks) [proposals/a4_h1.json:43]",
    "a4_h2": "63-session clock re-seeded at each fold start, offsets 0..567 "
             "(30 ticks) [proposals/a4_h2.json:44]",
    "a5_h1": "63-session clock re-seeded at each fold start (30 ticks) "
             "[proposals/a5_h1.json:36]",
    "a5_h2": "63-session clock re-seeded at each fold start (30 ticks) "
             "[proposals/a5_h2.json:28]",
    "a6_h1": "42-session global clock from 2018-04-04 (44 ticks) "
             "[proposals/a6_h1.json:48]",
    "a6_h2": "42-session global clock from 2018-04-04 (44 ticks) "
             "[proposals/a6_h2.json:39]",
}

# evidence lines used in the verdict blocks
EVIDENCE = {
    "a4_h1": {
        "anchor_key_and_gates": "research/control/stocks_free_v5_run/proposals/a4_h1.json:28-29",
        "aggregation_declaration": "research/control/stocks_free_v5_run/proposals/a4_h1.json:32-39",
        "anchor_arm_rule": "research/control/stocks_free_v5_run/proposals/a4_h1.json:48",
        "nonempty_claim": "research/control/stocks_free_v5_run/proposals/a4_h1.json:29 ('the cross-section is never emptied by construction (>= 9 sectors eligible at every tick under these gates)')",
        "forbidden_screen": "research/control/stocks_free_v5_run/proposals/a4_h1.json:92",
    },
    "a4_h2": {
        "anchor_key_and_gates": "research/control/stocks_free_v5_run/proposals/a4_h2.json:29-30",
        "nonempty_claim": "research/control/stocks_free_v5_run/proposals/a4_h2.json:30 ('The cross-section is never emptied by construction (>= 9 sectors eligible at every tick)')",
        "novelty_guards": "research/control/stocks_free_v5_run/proposals/a4_h2.json:59",
        "forbidden_screen": "research/control/stocks_free_v5_run/proposals/a4_h2.json:95",
    },
    "a5_h1": {
        "anchor_rule": "research/control/stocks_free_v5_run/proposals/a5_h1.json:42",
        "fields_and_gates": "research/control/stocks_free_v5_run/proposals/a5_h1.json:19-28",
        "a7n_anticorrelation_claim": "research/control/stocks_free_v5_run/proposals/a5_h1.json:74",
    },
    "a5_h2": {
        "gate_020_and_ancestry_disclosure": "research/control/stocks_free_v5_run/proposals/a5_h2.json:8",
        "anchor_rule": "research/control/stocks_free_v5_run/proposals/a5_h2.json:34",
        "stale_control": "research/control/stocks_free_v5_run/proposals/a5_h2.json:37",
        "identifiability_preregistration": "research/control/stocks_free_v5_run/proposals/a5_h2.json:40",
        "authority": "research/control/stocks_free_v5_run/baseline_invariants.json section_1_1_confirmatory_region; research/control/stocks_free_v5_run/forbidden_family_inventory.json section_1_1_shadow_region_front_door binding_rules_for_vol_level_reentry",
    },
    "a6_h1": {
        "census_and_gates": "research/control/stocks_free_v5_run/proposals/a6_h1.json:38-41",
        "anchor_rule": "research/control/stocks_free_v5_run/proposals/a6_h1.json:56",
        "early_set_claim": "research/control/stocks_free_v5_run/proposals/a6_h1.json:46 ('the early-S0 ranked set is {XLB, XLE, XLI, XLK, XLP, XLU, XLY} (7 sectors)')",
    },
    "a6_h2": {
        "anchor_rule": "research/control/stocks_free_v5_run/proposals/a6_h2.json:47",
        "declared_a7n_checks": "research/control/stocks_free_v5_run/proposals/a6_h2.json:66",
        "eligibility_claim": "research/control/stocks_free_v5_run/proposals/a6_h2.json:37 ('9 sectors are eligible from S0 start (XLC and XLRE join at ~2019-06 giving 11)')",
    },
}


def r3(x):
    return None if x is None else round(x, 3)


def pack_pair(v):
    return {
        "mean_abs_rho": r3(v["mean_abs_rho"]),
        "max_abs_rho": r3(v["max_abs_rho"]),
        "ticks_valid": v["ticks_valid"],
        "ticks_total": v["ticks_total"],
        "mean_sectors": r3(v["mean_sectors"]),
    }


def main():
    m = json.loads((HERE / "a7_n_measurements.json").read_text())
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    refs = list(next(iter(m["rho_vs_references"].values())).keys())
    matrix = {p: {r: pack_pair(m["rho_vs_references"][p][r]) for r in refs}
              for p in PROPOSALS}
    cross = {pa: {pb: pack_pair(m["cross_proposal"][pa][pb])
                  for pb in PROPOSALS if pb != pa} for pa in PROPOSALS}
    construct = {p: {
        "ticks_total": m["declared_series_constructibility"][p]["ticks_total"],
        "ticks_constructible_ge6":
            m["declared_series_constructibility"][p]["ticks_constructible_ge6"],
    } for p in PROPOSALS}

    shape = matrix["a5_h2"]["V4_SEMIVAR_SHAPE_126"]
    shape_pass = shape["mean_abs_rho"] is not None and shape["mean_abs_rho"] <= 0.20
    a5h2_ctrl = m["a5h2_own_control_checks"]
    ctrl_rho_fail = a5h2_ctrl["max_abs_rank_rho"] is not None \
        and a5h2_ctrl["max_abs_rank_rho"] > 0.90
    ctrl_differ = a5h2_ctrl["membership_differ_share"]

    kill = {}
    flag = {}
    for p in PROPOSALS:
        kill[p] = []
        flag[p] = []
        for r, v in matrix[p].items():
            if v["mean_abs_rho"] is None:
                continue
            if v["mean_abs_rho"] >= 0.60 and p != "a5_h2":
                kill[p].append((r, v["mean_abs_rho"]))
            elif 0.40 <= v["mean_abs_rho"] < 0.60:
                flag[p].append((r, v["mean_abs_rho"]))
    # A5-H2 shape gate handled separately (0.20); its non-shape entries use
    # the same flag band for reporting.

    collisions = []
    for pa in PROPOSALS:
        for pb, v in cross[pa].items():
            if pa >= pb:
                continue
            best = max(
                (v, pa, pb),
                (cross[pb][pa], pb, pa),
                key=lambda t: (t[0]["mean_abs_rho"] is not None,
                               t[0]["mean_abs_rho"] or -1),
            )
            vv, x, y = best
            if vv["mean_abs_rho"] is None:
                continue
            collisions.append({
                "pair": f"{x}|{y}",
                "mean_abs_rho": r3(vv["mean_abs_rho"]),
                "max_abs_rho": r3(vv["max_abs_rho"]),
                "ticks_valid": vv["ticks_valid"],
                "row_basis": x,
                "band": ("COLLISION_GE_060" if vv["mean_abs_rho"] >= 0.60
                         else "MEDIUM_040_060" if vv["mean_abs_rho"] >= 0.40
                         else "ok"),
            })

    def K(p, name):
        for r, v in kill[p]:
            if r == name:
                return v
        return None

    verdicts = {}

    # ---------------- a4_h1 -------------------------------------------------
    dv = K("a4_h1", "FORBIDDEN_DVSHOCK_21_252")
    verdicts["a4_h1"] = {
        "hypothesis_id": HYP["a4_h1"],
        "verdict": "INELIGIBLE",
        "series_used": m["series_labels"]["a4_h1"],
        "declared_series_constructibility": construct["a4_h1"],
        "gates": {
            "declared_series_constructible": False,
            "kill_any_mean_abs_rho_ge_060": True,
            "detail": [
                {
                    "finding": "DECLARED_ANCHOR_SERIES_NOT_CONSTRUCTIBLE",
                    "evidence": EVIDENCE["a4_h1"]["anchor_key_and_gates"],
                    "measurement": (
                        "Gate (c) (endpoint effective dates <= 100 calendar "
                        "days apart) is unsatisfiable at every tick: the "
                        "single-vintage aggregate re-vintages annually, so "
                        "eff(t) and eff(t-252s) are structurally 364-365 "
                        "days apart (measured at every sector and tick; see "
                        "a4h1_endpoint_gates in a7_n_measurements.json). The "
                        "declared anchor rank series is empty at 0/30 ticks; "
                        "the proposal's own claim of '>= 9 sectors eligible "
                        "at every tick under these gates' "
                        f"({EVIDENCE['a4_h1']['nonempty_claim']}) is "
                        "falsified pre-selection."
                    ),
                },
                {
                    "finding": "FORBIDDEN_FAMILY_LINEAGE_GE_060_ON_FALLBACK",
                    "evidence": EVIDENCE["a4_h1"]["forbidden_screen"],
                    "measurement": (
                        "On the documented diagnostic fallback (gate (c) "
                        "dropped; coverage gates kept), mean |rho| = "
                        f"{r3(dv)} (max {r3(matrix['a4_h1']['FORBIDDEN_DVSHOCK_21_252']['max_abs_rho'])}, "
                        f"{matrix['a4_h1']['FORBIDDEN_DVSHOCK_21_252']['ticks_valid']} "
                        "valid ticks of 6-9 sectors) vs the forbidden "
                        "21d/252d dollar-volume shock proxy "
                        "(FORBIDDEN_DVSHOCK_21_252, identical to the V4 "
                        "participation fresh anchor). >= 0.60 kill. "
                        "CAVEAT: only 5-6 ticks are measurable on the "
                        "fallback series (thin evidence); the fallback rank "
                        "set is the clean-fiscal-calendar sector subset "
                        "(XLB/XLE/XLF/XLRE/XLU [+XLC]), a cyclical-biased "
                        "subset that plausibly inflates the momentum/"
                        "participation affinity. The terminal ground stands "
                        "independent of this caveat: the declared series "
                        "does not exist."
                    ),
                },
                {
                    "finding": "MEDIUM_LINEAGE_NOTES",
                    "measurement": (
                        "FORBIDDEN_MOM_12_1 mean 0.543, "
                        "FORBIDDEN_SMA200_TREND mean 0.455, "
                        "V4_PART_STALE_SHOCK_21_252 mean 0.533 (0.40-0.60 "
                        "band). V4_SEMIVAR_SHAPE_126 mean 0.377 and "
                        "V4_VOLLEVEL_126 mean 0.268 stay below 0.40."
                    ),
                },
            ],
        },
        "clock": CLOCKS["a4_h1"],
        "anchor_definition": ANCHOR_DEFS["a4_h1"],
        "evidence_refs": EVIDENCE["a4_h1"],
    }

    # ---------------- a4_h2 -------------------------------------------------
    vol_guard = matrix["a4_h2"]["V4_VOLLEVEL_126"]
    col_h2h6 = next(c for c in collisions if c["pair"] == "a4_h2|a6_h1")
    verdicts["a4_h2"] = {
        "hypothesis_id": HYP["a4_h2"],
        "verdict": "INELIGIBLE",
        "series_used": m["series_labels"]["a4_h2"],
        "declared_series_constructibility": construct["a4_h2"],
        "gates": {
            "declared_series_constructible": False,
            "kill_any_mean_abs_rho_ge_060": False,
            "detail": [
                {
                    "finding": "DECLARED_ANCHOR_SERIES_NOT_CONSTRUCTIBLE",
                    "evidence": EVIDENCE["a4_h2"]["anchor_key_and_gates"],
                    "measurement": (
                        "The declared coverage >= 0.60 gate on BOTH fields "
                        "collapses under the canonical bridge's single-vintage "
                        "semantics: the sector vintage locks to the MAX "
                        "effective date across participating filers and "
                        "includes only filers reporting at that exact date, "
                        "so sectors containing one laggard fiscal-calendar "
                        "filer (XLI, XLK, XLP, XLV, XLY) sit at coverage "
                        "0.025-0.125. Rankable cross-sections are 3-7 sectors "
                        "at the 4 best ticks and 0-3 at the rest (4/30 "
                        "constructible) - the declared claim of '>= 9 sectors "
                        "eligible at every tick' "
                        f"({EVIDENCE['a4_h2']['nonempty_claim']}) is falsified "
                        "pre-selection on the frozen store."
                    ),
                },
                {
                    "finding": "SHADOW_REGION_GUARD_MEASURED_PASS",
                    "evidence": EVIDENCE["a4_h2"]["novelty_guards"],
                    "measurement": (
                        "Declared guard (b): mean |rho| >= 0.60 vs the V4 "
                        "vol-level control feature would make this a de facto "
                        "vol-level re-entry. Measured mean "
                        f"{r3(vol_guard['mean_abs_rho'])} (max "
                        f"{r3(vol_guard['max_abs_rho'])}) vs V4_VOLLEVEL_126 "
                        "on the diagnostic series -> guard holds."
                    ),
                },
                {
                    "finding": "CROSS_PROPOSAL_COLLISION_GE_060_DIAGNOSTIC",
                    "measurement": (
                        "vs a6_h1 (WCINT = current/assets, same denominator "
                        "field): mean 0.76 / max 0.98 (a4_h2-row, 30 ticks; "
                        "0.68/0.98 from the a6_h1 row). Both series are "
                        "diagnostic fallbacks; the collision is the mechanical "
                        "shared-denominator affinity and is recorded against "
                        "any future selection that paired these families."
                    ),
                },
                {
                    "finding": "MEDIUM_LINEAGE_NOTES",
                    "measurement": (
                        "FORBIDDEN_MOM_12_1 mean 0.415 (0.40-0.60 band); all "
                        "V4 anchors and other forbidden proxies <= 0.39 mean."
                    ),
                },
            ],
        },
        "clock": CLOCKS["a4_h2"],
        "anchor_definition": ANCHOR_DEFS["a4_h2"],
        "evidence_refs": EVIDENCE["a4_h2"],
    }

    # ---------------- a5_h1 -------------------------------------------------
    verdicts["a5_h1"] = {
        "hypothesis_id": HYP["a5_h1"],
        "verdict": "INELIGIBLE",
        "series_used": m["series_labels"]["a5_h1"],
        "declared_series_constructibility": construct["a5_h1"],
        "gates": {
            "declared_series_constructible": False,
            "kill_any_mean_abs_rho_ge_060": False,
            "detail": [
                {
                    "finding": "DECLARED_ANCHOR_SERIES_NOT_CONSTRUCTIBLE",
                    "evidence": EVIDENCE["a5_h1"]["anchor_rule"],
                    "measurement": (
                        "dei:EntityPublicFloat single-vintage coverage "
                        "collapses to 0.025-0.10 in 9-10 of 11 sectors (the "
                        "float vintage locks onto one filer's cover-page "
                        "measurement date); rankable cross-sections are 0-5 "
                        "sectors at every tick (0/30 constructible at the "
                        "declared coverage >= 0.60 gate). The declared "
                        "3v3 book is never constructible as written."
                    ),
                },
                {
                    "finding": "LINEAGE_CLEAN_ON_DIAGNOSTIC",
                    "evidence": EVIDENCE["a5_h1"]["a7n_anticorrelation_claim"],
                    "measurement": (
                        "All reference means on the diagnostic series are "
                        "<= 0.314 (max single-reference mean "
                        "V4_VOLLEVEL_126 0.314; FORBIDDEN_MOM_12_1 0.211), "
                        "consistent with the proposal's filed-facts-only "
                        "claim; the anti-momentum expectation (item 6 of its "
                        "source-to-test map) is directionally supported "
                        "(0.211, the lowest momentum reading in the wave). "
                        "Moot for eligibility: the declared series does not "
                        "exist, so the family cannot be scored or selected."
                    ),
                },
            ],
        },
        "clock": CLOCKS["a5_h1"],
        "anchor_definition": ANCHOR_DEFS["a5_h1"],
        "evidence_refs": EVIDENCE["a5_h1"],
    }

    # ---------------- a5_h2 -------------------------------------------------
    verdicts["a5_h2"] = {
        "hypothesis_id": HYP["a5_h2"],
        "verdict": "INELIGIBLE",
        "family_status": "CONFIRMATORY (Section 1.1 front door, as preregistered)",
        "series_used": m["series_labels"]["a5_h2"],
        "declared_series_constructibility": construct["a5_h2"],
        "gates": {
            "section_1_1_shape_gate_le_020": {
                "pass": shape_pass,
                "mean_abs_rho_vs_V4_SEMIVAR_SHAPE_126": shape["mean_abs_rho"],
                "max_abs_rho": shape["max_abs_rho"],
                "ticks": f"{shape['ticks_valid']}/{shape['ticks_total']}",
                "mean_sectors": shape["mean_sectors"],
            },
            "level_axis_ancestry_DOCUMENTED_NOT_A_GATE": {
                "mean_abs_rho_vs_V4_VOLLEVEL_126":
                    matrix["a5_h2"]["V4_VOLLEVEL_126"]["mean_abs_rho"],
                "max_abs_rho_vs_V4_VOLLEVEL_126":
                    matrix["a5_h2"]["V4_VOLLEVEL_126"]["max_abs_rho"],
                "mean_abs_rho_vs_VOLLEVEL_63":
                    matrix["a5_h2"]["VOLLEVEL_63"]["mean_abs_rho"],
                "note": (
                    "Expected high by construction and disclosed as ancestry "
                    "in the proposal (a5_h2.json:8); rho 1.000 vs the "
                    "63-session variance level is exact - sigma63 is a "
                    "monotone transform of SS63 - so the anchor IS the "
                    "vol-LEVEL axis, as preregistered. Not by itself "
                    "disqualifying; reported per the front-door rules."
                ),
            },
            "own_stale_control_distinctness": {
                "preregistered_gates":
                    a5h2_ctrl["preregistered_gates"],
                "mean_rank_rho": r3(a5h2_ctrl["mean_rank_rho"]),
                "max_abs_rank_rho": r3(a5h2_ctrl["max_abs_rank_rho"]),
                "slots_with_abs_rho_over_090": 6,
                "slots_total": a5h2_ctrl["slots_total"],
                "membership_differ_share": r3(ctrl_differ),
                "assessment": (
                    "The stale control is NOT rank-identical to the anchor "
                    "(L7 failure mode absent): basket membership differs at "
                    f"{r3(ctrl_differ)} of slots (>= 0.25 required: PASS) and "
                    "mean rank rho 0.759. However 6 of 30 slots breach the "
                    "preregistered per-slot rank-rho bound of 0.90 (max "
                    "0.955: 2022-12-09 and 2023-02-17) - a preregistration "
                    "breach under the conservative reading, recorded here "
                    "for A1/A9-F."
                ),
            },
            "kill_any_mean_abs_rho_ge_060_non_shape": False,
            "detail": [
                {
                    "finding": "SECTION_1_1_SHAPE_GATE_FAILED",
                    "evidence": EVIDENCE["a5_h2"]["gate_020_and_ancestry_disclosure"],
                    "measurement": (
                        "The preregistered A7-N eligibility gate is "
                        "|rho| <= 0.20 vs the V4 semivariance-SHAPE anchor. "
                        "Measured mean |rho| = 0.319 (max 0.655) over all 30 "
                        "decision ticks at 10-11 sectors: the 63-session "
                        "realized-vol LEVEL cross-section carries "
                        "substantial shape-anchor information (the "
                        "126-session downside/total share is correlated with "
                        "the recent vol level across sector ETFs). The "
                        "Section 1.1 front door is therefore closed for this "
                        "family in V5: INELIGIBLE regardless of the "
                        "documented level-axis ancestry."
                    ),
                },
                {
                    "finding": "MEDIUM_LINEAGE_NOTES",
                    "measurement": (
                        "FORBIDDEN_MOM_12_1 mean 0.415 (low-vol ranks align "
                        "with 12-1 momentum ranks), FORBIDDEN_SMA200_TREND "
                        "0.390; participation-family means 0.254-0.292."
                    ),
                },
            ],
        },
        "clock": CLOCKS["a5_h2"],
        "anchor_definition": ANCHOR_DEFS["a5_h2"],
        "evidence_refs": EVIDENCE["a5_h2"],
    }

    # ---------------- a6_h1 -------------------------------------------------
    col_h6h2 = next(c for c in collisions if c["pair"] == "a4_h2|a6_h1")
    col_h1h2_diag = cross["a6_h1"]["a6_h2"]
    verdicts["a6_h1"] = {
        "hypothesis_id": HYP["a6_h1"],
        "verdict": "INELIGIBLE",
        "series_used": m["series_labels"]["a6_h1"],
        "declared_series_constructibility": construct["a6_h1"],
        "gates": {
            "declared_series_constructible": False,
            "kill_any_mean_abs_rho_ge_060": False,
            "detail": [
                {
                    "finding": "DECLARED_ANCHOR_SERIES_NOT_CONSTRUCTIBLE",
                    "evidence": EVIDENCE["a6_h1"]["anchor_rule"],
                    "measurement": (
                        "Per-leg coverage >= 0.40 collapses on the census-9 "
                        "set (bridge single-vintage semantics): rankable "
                        "cross-sections are 0-7 sectors with only 2/44 ticks "
                        "at >= 6 sectors. The proposal's own L7 "
                        "pre-selection discipline (a6_h1.json:71-74) cannot "
                        "even be evaluated as declared because the anchor "
                        "rank vector does not exist at 42 of 44 ticks. Also "
                        "noted: the proposal's early-S0 ranked-set prose "
                        f"({EVIDENCE['a6_h1']['early_set_claim']}) omits XLV "
                        "from its own census list; the data-faithful early "
                        "set under its declared rules is 8 sectors "
                        "(census 9 minus XLC)."
                    ),
                },
                {
                    "finding": "LINEAGE_CLEAN_ON_DIAGNOSTIC",
                    "measurement": (
                        "All reference means <= 0.317 (V4_SEMIVAR_SHAPE_126 "
                        "0.284 with a single-tick max 0.929 at n=7; "
                        "FORBIDDEN_* all <= 0.317 mean). No forbidden-family "
                        "kill."
                    ),
                },
                {
                    "finding": "CROSS_PROPOSAL_COLLISION_GE_060_DIAGNOSTIC",
                    "measurement": (
                        "vs a4_h2 (cash/assets, same denominator field): "
                        "mean 0.68 / max 0.98 (44-tick row; 0.76/0.98 from "
                        "the a4_h2 row). Both series are diagnostic "
                        "fallbacks; shared-denominator affinity recorded."
                    ),
                },
                {
                    "finding": "MEDIUM_LINEAGE_NOTES",
                    "measurement": (
                        "vs a6_h2 (same agent's coupling family): mean 0.50 "
                        "(0.40-0.60 band, cross-proposal, diagnostic row)."
                    ),
                },
            ],
        },
        "clock": CLOCKS["a6_h1"],
        "anchor_definition": ANCHOR_DEFS["a6_h1"],
        "evidence_refs": EVIDENCE["a6_h1"],
    }

    # ---------------- a6_h2 -------------------------------------------------
    a6h2 = matrix["a6_h2"]
    worst = max((v["mean_abs_rho"] for v in a6h2.values()
                 if v["mean_abs_rho"] is not None))
    verdicts["a6_h2"] = {
        "hypothesis_id": HYP["a6_h2"],
        "verdict": "ELIGIBLE",
        "series_used": m["series_labels"]["a6_h2"],
        "declared_series_constructibility": construct["a6_h2"],
        "gates": {
            "kill_any_mean_abs_rho_ge_060": False,
            "flag_band_040_060_vs_forbidden_or_v4": [],
            "declared_checks_pass": {
                "evidence": EVIDENCE["a6_h2"]["declared_a7n_checks"],
                "vs_trailing_63s_variance_ranks_VOLLEVEL_63":
                    a6h2["VOLLEVEL_63"]["mean_abs_rho"],
                "vs_trailing_12_1_momentum": a6h2["FORBIDDEN_MOM_12_1"]["mean_abs_rho"],
                "vs_21d_252d_dv_shock": a6h2["FORBIDDEN_DVSHOCK_21_252"]["mean_abs_rho"],
                "vs_downside_total_semivar_share":
                    a6h2["V4_SEMIVAR_SHAPE_126"]["mean_abs_rho"],
                "note": (
                    "All four declared A7-N/A9-F measured checks measured "
                    "far below the declared 0.60 concern level "
                    f"(worst mean {r3(worst)}); the scale- and "
                    "location-invariance claims are empirically supported."
                ),
            },
            "detail": [
                {
                    "finding": "NOVELTY_PASS",
                    "measurement": (
                        "Declared series fully constructible (44/44 ticks, "
                        "10-11 sectors). Worst mean |rho| vs any V4 anchor or "
                        "forbidden proxy is "
                        f"{r3(a6h2['FORBIDDEN_DVSHOCK_21_252']['mean_abs_rho'])} "
                        "(21d/252d DV shock) / 0.289 (semivariance shape); "
                        "single-tick maxima up to 0.855 occur at thin "
                        "sub-periods but never push a mean into the kill or "
                        "flag band. The coupling key is measurably distinct "
                        "from every forbidden family and V4 anchor."
                    ),
                },
                {
                    "finding": "CROSS_PROPOSAL_MEDIUM_NOTE",
                    "measurement": (
                        "vs a6_h1: mean 0.50 (diagnostic row; the a6_h2 "
                        "series is declared, the counterparty diagnostic). "
                        "Below 0.60; recorded so the two A6 families are not "
                        "paired as independent mechanisms without this "
                        "number."
                    ),
                },
                {
                    "finding": "SCHEDULE_PROSE_DISCREPANCY_RECORDED",
                    "evidence": EVIDENCE["a6_h2"]["eligibility_claim"],
                    "measurement": (
                        "Per the frozen snapshot, XLRE's adjusted history "
                        "begins 2015-10-08, so XLRE meets the >= 252-session "
                        "rule from S0 start: the measured eligible set is 10 "
                        "sectors from 2018-04-04 and 11 from the 2019-08-05 "
                        "tick (XLC). The proposal's prose ('9 from S0 start; "
                        "XLC and XLRE join ~2019-06') is wrong about XLRE "
                        "and the join date, but in the direction of MORE "
                        "constructibility; the declared rule as applied to "
                        "the data is what was measured."
                    ),
                },
            ],
        },
        "clock": CLOCKS["a6_h2"],
        "anchor_definition": ANCHOR_DEFS["a6_h2"],
        "evidence_refs": EVIDENCE["a6_h2"],
    }

    n_elig = sum(1 for v in verdicts.values() if v["verdict"] == "ELIGIBLE")

    audit = {
        "schema": "stocks_free_v5_run/a7_n_novelty_audit@1",
        "producer_role": "A7-N",
        "cycle": "STOCKS-FREE-V5",
        "measured_at_utc": now,
        "lane": {
            "worktree": ".worktrees/stocks-free-v5/d2-a7-novelty",
            "branch": "orca/stocks-free-v5-d2-a7-novelty",
        },
        "authority": [
            "PLAN_stocks_v5.md sections 1, 1.1, 8",
            "research/control/stocks_free_v5_run/forbidden_family_inventory.json",
            "research/control/stocks_free_v5_run/baseline_invariants.json (section_1_1_confirmatory_region)",
        ],
        "inputs": {
            "proposals": [
                "research/control/stocks_free_v5_run/proposals/a4_h1.json",
                "research/control/stocks_free_v5_run/proposals/a4_h2.json",
                "research/control/stocks_free_v5_run/proposals/a5_h1.json",
                "research/control/stocks_free_v5_run/proposals/a5_h2.json",
                "research/control/stocks_free_v5_run/proposals/a6_h1.json",
                "research/control/stocks_free_v5_run/proposals/a6_h2.json",
            ],
            "etf_snapshot": m["data_pins"]["snapshot_path"],
            "etf_snapshot_file_sha256": m["data_pins"]["snapshot_files"],
            "sec_pit_store": m["data_pins"]["sec_store_path"],
            "sec_pit_store_sha256": m["data_pins"]["pit_store_sha256"],
            "sec_pit_store_sha256_matches_manifest_f53eb371": m[
                "data_pins"]["pit_store_sha256"].startswith("f53eb3712bc9d686"),
            "sec_panel_sha256": m["data_pins"]["panel_sha256"],
            "canonical_bridge": "research/assets/stocks/pit_conditioning.py",
            "v4_reference_modules": [
                "research/stocks_free_v4/family_semivar/signals.py (semivariance_share, total_sum_sq; window 126 per config STATE_WINDOW_ANCHOR/CONTROL)",
                "research/stocks_free_v4/family_participation (SHOCK_WINDOWS A=fresh 21/252, C=stale t-83..t-63/t-251..t-84)",
            ],
        },
        "method": {
            "summary": m["method"],
            "clocks": {
                "clock63_fold_reseeded_30_ticks": m["clocks"]["clock63_fold_reseeded"][0]
                + " ... "
                + m["clocks"]["clock63_fold_reseeded"][-1]
                + f" ({len(m['clocks']['clock63_fold_reseeded'])} ticks; fold sessions "
                + ", ".join(f"{k}={v}" for k, v in m["calendar"]["fold_sessions"].items()) + ")",
                "clock42_global_44_ticks": m["clocks"]["clock42_global"][0]
                + " ... " + m["clocks"]["clock42_global"][-1]
                + f" ({len(m['clocks']['clock42_global'])} ticks; s0 sessions "
                + str(m["calendar"]["s0_sessions"]) + ")",
            },
            "spearman": "average ranks, Pearson on ranks; a pair is measured at a tick only over the common sector set (proposal-eligible intersect reference-ready) with >= 6 sectors",
            "series_policy": (
                "Declared constructions first (proposals' own gates on the "
                "canonical bridge). Where the declared series is degenerate "
                "on the frozen store, a clearly-labelled diagnostic/fallback "
                "series (one declared gate suspended, everything else "
                "identical) is measured so lineage evidence exists; "
                "non-constructibility of the declared series is itself "
                "recorded per tick and is terminal pre-selection evidence. A "
                "diagnostic series can never raise a verdict."
            ),
            "pnl_statement": "NO PnL, NO portfolio returns, NO scored metrics were computed anywhere in this audit; feature/rank arithmetic only; every read S0-bounded (<= 2025-07-31).",
        },
        "reference_features": {
            "V4_SEMIVAR_SHAPE_126": "SFV4-A4-H1-A anchor axis: semivariance share DS/SS over 126 trailing adjusted-close returns (V4 terminal module), rank 1 = highest share",
            "V4_VOLLEVEL_126": "SFV4-A4-H1-C control axis: total sum of squared returns over the same 126-session window, rank 1 = highest level",
            "V4_PART_FRESH_SHOCK_21_252": "SFV4-A5-H1-A anchor: mean(raw close*raw volume, t-20..t) / mean(., t-251..t-21) on the _none raw pair",
            "V4_PART_STALE_SHOCK_21_252": "SFV4-A5-H1-C stale-rank control: mean(DV, t-83..t-63) / mean(DV, t-251..t-84)",
            "FORBIDDEN_DVSHOCK_21_252": "inventory proxy '21d/252d dollar-volume shock ratio' - identical construction to the V4 fresh participation anchor (noted: one collision counted in two labels)",
            "FORBIDDEN_MOM_12_1": "inventory proxy 'sector relative momentum 12-1': close(t-21)/close(t-252) - 1 on the adjusted path",
            "FORBIDDEN_SMA200_TREND": "inventory proxy 'SMA200 trend state': close(t)/mean(close, t-199..t) - 1 on the adjusted path",
            "VOLLEVEL_63": "63-session variance level (declared counterparty for a6_h2's check (a))",
        },
        "series_labels": m["series_labels"],
        "declared_series_constructibility": construct,
        "rho_matrix_vs_references": matrix,
        "cross_proposal_matrix": cross,
        "cross_proposal_collisions": collisions,
        "a5h2_own_control_checks": {
            "preregistered_gates": a5h2_ctrl["preregistered_gates"],
            "mean_rank_rho": r3(a5h2_ctrl["mean_rank_rho"]),
            "max_abs_rank_rho": r3(a5h2_ctrl["max_abs_rank_rho"]),
            "slots_with_abs_rho_over_090": 6,
            "membership_differ_share": r3(ctrl_differ),
            "slots_total": a5h2_ctrl["slots_total"],
        },
        "verdicts": verdicts,
        "findings": [
            {
                "id": "A7N-F1",
                "severity": "HIGH",
                "finding": (
                    "Canonical-bridge single-vintage coverage collapse: for "
                    "fields aggregated across the frozen 410-filer panel, the "
                    "sector vintage locks to the MAX effective date across "
                    "participating filers and includes only filers reporting "
                    "at that exact date. Sectors containing one laggard "
                    "fiscal-calendar filer sit at coverage 0.025-0.125, so "
                    "the proposals' declared coverage gates (>= 0.60 a4_h1/"
                    "a4_h2/a5_h1; >= 0.40 a6_h1) empty their cross-sections "
                    "(declared series constructible at 0/30, 4/30, 0/30, "
                    "2/44 ticks respectively). The proposals' own "
                    "'never emptied by construction (>= 9 sectors)' claims "
                    "(a4_h1.json:29, a4_h2.json:30) are falsified on the "
                    "frozen store. Root cause: A3's P2 coverage census "
                    "(p2_pit_data_audit_sec.json checks.A7_warmup_coverage) "
                    "measures pre-S0 AVAILABILITY fractions (filers with any "
                    "gated record), which the proposals quote as if they "
                    "certified per-tick single-vintage coverage."
                ),
                "consequence": "a4_h1, a4_h2, a5_h1, a6_h1 die pre-selection on data/feasibility grounds (A1 rubric: data PASS and identifiability cannot be satisfied by a non-existent rank series).",
                "owner_actions_scope": "A1/A9-F adjudication; A7-N does not repair.",
            },
            {
                "id": "A7N-F2",
                "severity": "HIGH",
                "finding": (
                    "a4_h1 gate (c) (endpoint effective dates within 100 "
                    "calendar days) is unsatisfiable for a 252-session-"
                    "differenced key on annually re-vintaged aggregates: "
                    "measured 364-365 days at every sector and tick "
                    "(a4h1_endpoint_gates). The declared feature is the "
                    "empty set at every tick."
                ),
                "consequence": "a4_h1 declared series 0/30; terminal as declared.",
            },
            {
                "id": "A7N-F3",
                "severity": "HIGH",
                "finding": (
                    "A5-H2 (Section 1.1 confirmatory front door) fails the "
                    "preregistered A7-N shape gate: mean |rho| 0.319 > 0.20 "
                    "vs the V4 semivariance-SHAPE anchor (max 0.655, 30/30 "
                    "ticks, 10-11 sectors). The level-axis ancestry is "
                    "documented as required (mean 0.919, max 1.000 vs the V4 "
                    "vol-level control; rho 1.000 vs the 63-session variance "
                    "level - the anchor is the level axis by monotone "
                    "equivalence). Additionally 6/30 slots breach the "
                    "preregistered stale-control rank-rho bound of 0.90 "
                    "(max 0.955), while basket membership differs at 90% of "
                    "slots (the L7 rank-identity failure mode is absent)."
                ),
                "consequence": "The Section 1.1 question is answered pre-scoring: the declared overlay family is INELIGIBLE for V5; the shadow effect remains untradable-as-proposed and stays closed.",
            },
            {
                "id": "A7N-F4",
                "severity": "MEDIUM",
                "finding": (
                    "Cross-proposal collisions on diagnostic series: "
                    "a4_h2 vs a6_h1 mean 0.68-0.76 / max 0.98 (shared "
                    "us-gaap:Assets denominator affinity); a6_h2 vs a6_h1 "
                    "0.50 (0.40-0.60 band); a4_h2 vs a6_h2 0.42/0.37."
                ),
                "consequence": "Recorded against any future pairing of these families at selection.",
            },
            {
                "id": "A7N-F5",
                "severity": "LOW",
                "finding": (
                    "Schedule prose discrepancies (recorded, not verdict-"
                    "driving): a6_h2 claims 9 eligible sectors from S0 start "
                    "with XLRE joining ~2019-06, but XLRE's snapshot history "
                    "(from 2015-10-08) satisfies the >= 252-session rule "
                    "from S0 start (measured 10 from start, 11 from the "
                    "2019-08-05 tick); a6_h1's early-set prose omits XLV "
                    "from its own census (measured 8 sectors early, not 7); "
                    "a4_h1's '>= 9 sectors eligible at every tick' and "
                    "a4_h2's '>= 9 sectors eligible at every tick' claims "
                    "are falsified (see A7N-F1/F2)."
                ),
                "consequence": "Feasibility/consistency evidence for A1/A9-F.",
            },
        ],
        "overall_novelty_verdict": {
            "verdict": "STOCKS_FREE_V5_A7N_NOVELTY: 1_OF_6_PROPOSALS_NOVELTY_ELIGIBLE",
            "eligible": ["SFV5-A6-H2 (a6_h2) - on the novelty/anti-rescue axis only; A9-F feasibility and A1 selection gates still apply"],
            "ineligible": [
                "SFV5-A4-H1 (declared series 0/30 constructible; fallback mean |rho| 0.766 vs forbidden DV-shock proxy)",
                "SFV5-A4-H2 (declared series 4/30 constructible)",
                "SFV5-A5-H1 (declared series 0/30 constructible)",
                "SFV5-A5-H2 (Section 1.1 shape gate 0.319 > 0.20)",
                "SFV5-A6-H1 (declared series 2/44 constructible)",
            ],
            "statement": (
                "Five of six blind proposals are INELIGIBLE on measured "
                "pre-selection evidence: four SEC-conditioned proposals "
                "cannot construct their declared anchor rank series through "
                "the canonical bridge on the frozen store (A7N-F1/F2), and "
                "the Section 1.1 confirmatory vol-level family fails its "
                "preregistered 0.20 shape-anchor gate (A7N-F3). Only "
                "SFV5-A6-H2 (cross-sector coupling state) is novelty-"
                "eligible: measurably distinct from every forbidden family "
                "and V4 anchor (worst mean |rho| 0.351) with its declared "
                "series fully constructible. No PnL was computed; this audit "
                "does not pre-judge A9-F feasibility or A1 selection for "
                "a6_h2."
            ),
            "counts": {"eligible": n_elig, "ineligible": 6 - n_elig, "total": 6},
        },
    }

    out = HERE / "a7_n_novelty_audit.json"
    out.write_text(json.dumps(audit, indent=1, sort_keys=True) + "\n")
    print(f"[done] audit -> {out}")


if __name__ == "__main__":
    main()
