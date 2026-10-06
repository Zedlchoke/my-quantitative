#!/usr/bin/env python
"""
ES-READINESS lane, FUTURES-SIX-READINESS-20261004 — Tasks 3 + 4:
fee erratum status cell + trial census recount.

Task 3 restates the baseline fees_erratum verdicts (NO re-derivation of web
captures — every value is a restatement of the pinned baseline artifacts).
Task 4 recounts the ES minimal-identity census (36) vs the frozen cap (24).
Writes es_fee_status.json and es_trial_census.json next to this script.
"""
import hashlib
import json
import os
import sys

OUT = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(OUT, "../../../.."))
P3 = ("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/"
      "research/control/FUTURES-P3-QUARANTINE-20261004")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


PINS = {}
for label, p in {
    "FEES_CORRECTED_md": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/FEES_CORRECTED.md",
    "fees_corrected_json": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/fees_corrected.json",
    "P0_ERRATUM_VERDICT_md": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/verify/P0_ERRATUM_VERDICT.md",
    "p0_verdict_json": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/verify/p0_verdict.json",
    "FEE_ERRATUM_DRAFT_md": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/impact/FEE_ERRATUM_DRAFT.md",
    "GATE_REVIEW_NOTE_md": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/impact/GATE_REVIEW_NOTE.md",
    "A7_SPEC_md": WT + "/research/control/FUTURES-ES-V1-PACKET/audit/a7_spec/A7_SPEC.md",
    "a7_spec_checks_json": WT + "/research/control/FUTURES-ES-V1-PACKET/audit/a7_spec/a7_spec_checks.json",
    "SPEC_PB1_ES_md": WT + "/research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md",
    "FEES_BY_CODE_md_DEEPFOUR": WT + "/research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/fees/FEES_BY_CODE.md",
    "FINAL_SAFE_BLOCKER_MATRIX_md_P3": P3 + "/synth/FINAL_SAFE_BLOCKER_MATRIX.md",
    "esnq_hypotheses_json": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/esnq_hypotheses.json",
    "RANKING_INPUT_md": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/RANKING_INPUT.md",
    "CENSUS_FINAL_md": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/synth/CENSUS_FINAL.md",
    "BLOCKER_MATRIX_md": WT + "/research/control/FUTURES-OVERNIGHT-PREP-20261003/synth/BLOCKER_MATRIX.md",
}.items():
    PINS[label] = {"path": p, "sha256": sha(p)}

# ---------------------------------------------------------------------------
# Task 3 — fee erratum cell (restatement; no re-derivation of web captures)
# ---------------------------------------------------------------------------
fee = {
    "lane": "ES-READINESS",
    "round": "FUTURES-SIX-READINESS-20261004",
    "task": "fee/spread/slippage/BBO readiness cell — restatement + pinning only",
    "restatement": {
        "corrected_tier1_all_in_per_side": "2.24 USD (ES; = 0.85 commission Fixed + 1.38 exchange + 0.00 clearing + 0.01 regulatory; IBKR's own worked example, byte-verified in RAW archive)",
        "cost_class": "MODELED COST — SOURCE=PUBLIC_REFERENCE; words 'measured cost'/'complete cost' forbidden (0 positive uses per BLOCKER_MATRIX law scan)",
        "verified_vs_account": "NOT_RUN (owner account verification never performed; plan/tier of actual account unknown) — owner decision D2 OPEN",
        "p0_erratum_verdict": "UPHELD in full (P0-VERIFY, independent): glued-superscript extraction defect CONFIRMED at byte level for CME cells (1.386 -> 1.38; 0.011 -> 0.01); parent NYMEX reg 0.02 contradicted; two genuine temporal changes documented (GC/SI 1.60->1.65; regs 0.02->0.01); 17/17 output digests recomputed-matched",
        "tiered": "T2/T3/T4 = 2.04/1.84/1.64 USD/side (ES)",
        "spread_half_turn": "6.25 USD (close-proxy, median full-spread 1.0 tick; high-biased proxy, NOT BBO)",
        "slippage_tiers": "S1/S2/S3 = 12.50/25.00/37.50 USD (1/2/3 ticks x $12.50; research assumption D1, not a measurement)",
        "bbo": "NOT_RUN program-wide — BBO/depth never acquired; D5 law: even bbo-1m cannot prove intrabar fill/queue",
    },
    "spec_section5_status": {
        "published_values": "S1 21.006 / S2 33.506 / S3 46.006 USD per side (default NFA 0.02; -0.01 window 2014-10-01..2017-12-31), i.e. ~21.00/33.50/46.00",
        "status": "UNDER-REVIEW-ERRATUM: exchange cell 1.386 is the retired glued-superscript value (corrected 1.38 -> all-in 21.00/33.50/46.00 under Scenario B); every cost gate derived from SPEC §5 is UNDER REVIEW until a new A7 re-audits cost arithmetic against corrected capture-backed sources (A7's R2 'recomputed exact' was arithmetic vs the transcribed D2 table, not a source re-read)",
        "affected": "SPEC §5 exchange row + all-in row; commission 0.85 row, NFA timeline row, spread proxy, slippage tiers, the 24 trial identities: NOT affected",
        "d2_r6_public_reference_table": "stale under correction (2.247 -> 2.24; components 1.38/0.01); labels SOURCE=PUBLIC_REFERENCE / VERIFIED_VS_ACCOUNT=NOT_RUN / MODELED_COST stay true either way",
    },
    "open_divergence_D3_reg_basis": {
        "statement": "USD 0.01/side regulatory-basis divergence OPEN: SPEC §5 binds regulatory to the official NFA timeline (0.02 default, single-source rule; 0.01 only 2014-10-01..2017-12-31) while the corrected IBKR capture basis is 0.01 for the current epoch (and an unverified mirror claims 0.01 from 2026-07-01 — NOT adopted; 0.02 is the conservative choice per A7-SPEC NOTE N-1)",
        "consequence": "SPEC §5 published all-ins carry <=0.01/side divergence vs the corrected capture basis; adjudication belongs to the pending fee A7 re-audit; no cost arithmetic performed in this lane",
    },
    "a7_fee_packet_status": {
        "spec_a7": "A7-SPEC (specification audit) ran: verdict FREEZE_READY_WITH_ERRATA, 0 BLOCKER / 0 MAJOR / 5 MINOR (applied at r3 as [ERRATUM A7-SPEC-M*]) / 7 NOTE",
        "fee_a7_reaudit": "READY_NOT_RUN — the new A7 fee re-audit required by the erratum law is packeted but has not been run (per P3-round FINAL_SAFE_BLOCKER_MATRIX: 'A7 packet READY (not run)'); gates stay UNDER REVIEW until it runs",
    },
    "no_rederivation_note": "Per lane brief: web fee captures were NOT re-derived or re-fetched (no network in this lane); every value above is a restatement of the pinned baseline artifacts below.",
    "sha256_pins": PINS,
    "verdict": "RESTATED_PER_BASELINE_2_24_T1_UPHELD_MODELED_COST_D2_NOT_RUN_UNDER_REVIEW",
}
json.dump(fee, open(os.path.join(OUT, "es_fee_status.json"), "w"), indent=1)

# ---------------------------------------------------------------------------
# Task 4 — trial census recount
# ---------------------------------------------------------------------------
arms = ["CONT", "REV"]
tails = ["UP", "DN"]
identities = []
for a in arms:
    for t in tails:
        for d in ["D0", "D30"]:
            identities.append(f"FBES1-PB1-{a}-{t}-{d}-S2")            # P-A 8
for a in arms:
    for t in tails:
        for s in ["S1", "S3"]:
            identities.append(f"FBES1-PB1-{a}-{t}-D0-{s}")            # P-B 8
for a in arms:
    for t in tails:
        identities.append(f"FBES1-PB1-{a}-{t}-D0-S2-FOMCIN")          # FOMC 4
identities += ["FBES1-PLA-D0-S2",                                     # C1 placebo (seed 20261002)
               "FBES1-ALW-D0-S2",                                     # C2 baseline
               "FBES1-FLAT",                                          # C3 anchor
               "FBES1-DOSE-D0-S2"]                                    # C4 dose-response
assert len(identities) == 24, len(identities)
assert len(set(identities)) == 24

esnq_census = [
    {"family": "ES-F1 FOMC-RES", "full_grid": 24, "minimal_core": 8, "scored_controls": 3,
     "minimal_total": 11},
    {"family": "ES-F2 MACRO-0730", "full_grid": 48, "minimal_core": 8, "scored_controls": 3,
     "minimal_total": 11},
    {"family": "ES-F3 COT-CROWD", "full_grid": 4, "minimal_core": 4, "scored_controls": 3,
     "minimal_total": 7},
    {"family": "ES-F4 RUN-REV", "full_grid": 8, "minimal_core": 4, "scored_controls": 3,
     "minimal_total": 7},
]
minimal_sum = sum(f["minimal_total"] for f in esnq_census)
frozen_cap = 24
headroom = 0  # frozen 24 fill the cap exactly (SPEC A-r4); any new identity needs owner amendment

census = {
    "lane": "ES-READINESS",
    "round": "FUTURES-SIX-READINESS-20261004",
    "task": "trial census recount — ES minimal identity demand vs frozen cap",
    "frozen": {
        "cap": frozen_cap,
        "source": "SPEC_PB1_ES r3 §6 (A-r4 explicit list; Co-Owner r5; A7-SPEC R1 PASS recomputed 8+8+4+4=24)",
        "headroom": 0,
        "listing": {
            "P_A_delay_pair_S2": [i for i in identities
                                  if (i.endswith("-D0-S2") or i.endswith("-D30-S2"))
                                  and "PLA" not in i and "ALW" not in i and "DOSE" not in i
                                  and "FOMCIN" not in i],
            "P_B_tiers_D0": [i for i in identities if ("-S1" in i or "-S3" in i)],
            "FOMC_sensitivity": [i for i in identities if i.endswith("FOMCIN")],
            "controls": ["FBES1-PLA-D0-S2 (C1 placebo, seed 20261002, single-seed publication limit)",
                          "FBES1-ALW-D0-S2 (C2 baseline)", "FBES1-FLAT (C3 anchor)",
                          "FBES1-DOSE-D0-S2 (C4 dose-response)"],
        },
        "all_24_explicit": identities,
    },
    "new_demand_recount": {
        "rows": esnq_census,
        "minimal_aggregate": minimal_sum,
        "expectation_check": minimal_sum == 36,
        "source": "hypo/es_nq/RANKING_INPUT.md §3 census + synth/CENSUS_FINAL.md §1/§3 (SYNTH-VERIFY filled from lanes' own census sections)",
    },
    "cap_arithmetic": {
        "frozen_cap": frozen_cap,
        "minimal_demand": minimal_sum,
        "headroom": headroom,
        "headroom_expected": 0,
        "verdict": "36 > 24 with headroom 0 => EVERY new ES family BLOCKED_TRIAL_BUDGET (standing; unchanged this round)",
        "executable_at_0_identities": ["ES-F3 stage-1 vol leg (0 IDs)",
                                       "ES-F1/F2/F4 anatomy pre-gates (F1-K6/F2-K6/F4-K6, descriptive)",
                                       "X-1..X-5 cross diagnostics (0 IDs by class)"],
        "no_new_trials_this_lane": True,
    },
    "sha256_pins": PINS,
    "verdict": "CENSUS_RECOUNTED_36_VS_24_HEADROOM_0_ALL_BLOCKED_TRIAL_BUDGET",
}
json.dump(census, open(os.path.join(OUT, "es_trial_census.json"), "w"), indent=1)

print(json.dumps({"fee": fee["verdict"], "census": census["verdict"],
                  "minimal_sum": minimal_sum, "n_frozen_listed": len(identities)}, indent=1))
sys.exit(0)
