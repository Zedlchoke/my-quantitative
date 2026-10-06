#!/usr/bin/env python
"""Assemble fx_eb_readiness.json — 8-dim data-readiness per code (6E, 6B)."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep")
RC = WT / "research/control"
LANE = RC / "FUTURES-SIX-READINESS-20261004/fx_eb"
DR = RC / "FUTURES-DEEPRESEARCH-V2-20261003"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


expiry = json.loads((LANE / "calendar/fx_eb_expiry_2023_2026.json").read_text())
hol = json.loads((LANE / "holiday/holiday_deviation_6e_6b.json").read_text())
cre = json.loads((LANE / "cost_roll_events/cost_roll_events_fxeb.json").read_text())
ver = json.loads((LANE / "q5_independent_verify/q5_6e_verify_result.json").read_text())

PINS = {
    "FEES_CORRECTED.md": "FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/source/FEES_CORRECTED.md",
    "fx_hypotheses.json": "FUTURES-OVERNIGHT-PREP-20261003/hypo/6e_6b/fx_hypotheses.json",
    "PB2_ANCESTRY_COURT_DRAFT.md": "FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/6e_6b/PB2_ANCESTRY_COURT_DRAFT.md",
    "6E_DEEP_v2.md": "FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6E_DEEP_v2.md",
    "6B_DEEP_v2.md": "FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/6B_DEEP_v2.md",
    "6E_a4_events.json": "FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_a4_events.json",
    "6B_a4_events.json": "FUTURES-DEEPRESEARCH-V2-20261003/analysis/6B_a4_events.json",
}
pins = {k: {"path": v, "sha256": sha(RC / v)} for k, v in PINS.items()}

COMMON = {
    "schema": "fx_eb_readiness@1",
    "task_id": "FUTURES-SIX-READINESS-20261004",
    "lane": "FX-EB-CALENDAR",
    "generated_utc": NOW,
    "standing_rulings": ["NO_GO_REGISTER / NO_GO_SCORE / NO_GO_ORDER",
                         "all fees MODELED COST / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW until owner-authorized A7 (D2 open)",
                         "PB2 HOLD; PB3 PARK (6A); 6F NOT_RUN_DATA_ABSENT",
                         "BLS PIT vintage law in force; current-calendar inference FORBIDDEN",
                         "IMM-rule expiry derivation FORBIDDEN"],
    "q5_independent_verify": {
        "pcal_58_6e": ver["captures"][0]["verdict"],
        "svc_captures": ver["svc_captures"] and ver["summary"]["svc_pass"],
        "artifact": "fx_eb/q5_independent_verify/q5_6e_verify_result.json",
    },
    "artifact_pins": pins,
    "lane_artifacts": {},
}
for rel in ["calendar/fx_eb_expiry_2023_2026.json", "holiday/holiday_deviation_6e_6b.json",
            "cost_roll_events/cost_roll_events_fxeb.json", "q5_independent_verify/q5_6e_verify_result.json",
            "pb2/PB2_HOLD_RESTATE.md", "pb2/pb2_restate.json", "census/fx_census_recount.json",
            "fetch_log.jsonl"]:
    COMMON["lane_artifacts"][rel] = sha(LANE / rel)


def dims(sym, mult, unit, tick, tick_val, bars, bars_note, notional):
    e = expiry[sym]
    n_exp = sum(1 for c in e["quarters"].values() if c["status"] == "OBTAINED")
    fy = {y: h for y, h in (("2023", hol["6E"]["by_year"]["2023"]),
                            ("2024", hol["6E"]["by_year"]["2024"]),
                            ("2025", hol["6E"]["by_year"]["2025"]),
                            ("2026", hol["6E"]["by_year"]["2026"]))}
    if sym == "6E":
        roll = cre["roll_remeasure"]["6E"]
        events = {
            "fomc": {k: cre["fomc_2023_2026"][k] for k in
                     ("n_dated_decisions_2023_2026_through_20260930", "by_year",
                      "n_rate_decision_statements_2023_2026", "by_year_rate_decisions",
                      "note_framework_statement", "vintage_law")},
            "ecb": {"baseline": cre["ecb_6e"]["baseline"], "n_meetings_2020_2026": 55,
                    "path": cre["ecb_6e"]["path"], "sha256": cre["ecb_6e"]["sha256"]},
        }
        hol_cell = ("OBTAINED (archived, this round): 34/42 windows deviation-documented; 8 aged-out inconclusive; "
                    "by year " + json.dumps(fy) + "; artifact fx_eb/holiday/holiday_deviation_6e_6b.json")
        event_dim = "PASS_EVIDENCED (FOMC 30 decision statements 2023-2026.9 from archived federalreserve.gov HTML with in-file release-time proof; ECB 55/55 baseline) — keyed to vintage as-of decision date; current-calendar inference FORBIDDEN"
    else:
        roll = cre["roll_remeasure"]["6B"]
        events = {"boe_mpc": {k: cre["boe_mpc_2023_2026"][k] for k in
                              ("n_mpc_dates_2023_2026_listed", "n_in_panel_through_20260930",
                               "by_year_in_panel", "rate_change_dates_in_panel", "note", "vintage_law")},
                  "fomc": {k: cre["fomc_2023_2026"][k] for k in
                           ("n_rate_decision_statements_2023_2026", "by_year_rate_decisions")}}
        hol_cell = ("NOT_OBTAINED 0/42: product id 42 (6B) in NO archived trading-hours-by-product "
                    "capture (CDX zero-row probe + sibling id enumeration); live BLOCKED_TRANSPORT; "
                    "FX deviation model for 6B remains calendar-uncertain")
        event_dim = "PASS_EVIDENCED (BoE MPC 30/32 listed dates in panel through 2026-09-30, 11 rate changes matching official Bank Rate history; FOMC 30 decision statements) — vintage law applies"
    return {
        "1_identity_tick": {
            "status": "PASS_BASELINE_RESTATE",
            "contract": f"{sym}: CME FX futures, {mult} {unit}, USD quote",
            "tick": tick, "tick_value_usd": tick_val,
            "baseline_agreement": "baseline dossiers v2 + DATACONTRACT agree; no flag",
            "source": "dossiers_v2 (artifact_pins)",
        },
        "2_o1m_coverage": {
            "status": "PASS_WITH_DISCLOSED_GAPS" if sym == "6E" else "PASS_WITH_DISCLOSED_GAPS",
            "panel": bars,
            "holes_note": bars_note,
            "held_chain": f"1,746 held sessions {roll['first_session']}..{roll['last_session']} (held_calendar.parquet sha256 {roll['held_calendar_sha256'][:16]}…)",
        },
        "3_roll_expiry": {
            "status": "IMPROVED_THIS_ROUND",
            "expiry_2023_2026": f"{n_exp}/16 cells OBTAINED (dispatch baseline already credited sibling Q5 6E+12; this round adds ECH26/ECM26 for 6E / BPU24..BPZ26 for 6B)",
            "cumulative_note": "dispatch baseline 236/272 already credits sibling Q5 6E+12; this round +2 (6E) / +10 (6B) -> cumulative 248/272; per-code 6E 66/68, 6B 62/68",
            "expiry_cells": e["quarters"],
            "rule_law": "dated official values only; IMM-rule derivation FORBIDDEN — never used",
            "roll_remeasure": {
                "n_roll_switches": roll["n_roll_switches"],
                "n_contracts_held": roll["n_contracts_held"],
                "observed_rule": "chain rolls before expiry; measured lead vs official last-trade where cell obtained (see switches[].days_lastheld_before_official_expiry)",
                "matrix_baseline": "roll_rule NOT_RUN at dispatch -> now MEASURED from held_calendar.parquet (no new chain built)",
            },
        },
        "4_session_holiday": {
            "status": "PASS_EVIDENCED" if sym == "6E" else "PARTIAL_HOLIDAB_HOLE",
            "weekly_session": "Globex ~23h template (17:00 CT reopen), OBSERVED in dossier v2 session anatomy; no verbatim weekly-hours spec capture for FX codes (spec service archived captures exist for ES/NQ only)",
            "holiday_deviations": hol_cell,
            "aged_out_law": hol.get("aged_out_law"),
        },
        "5_event_pit": {
            "status": event_dim,
            "events": events,
            "bls_restate": cre["bls_vintage_restate"]["law"],
        },
        "6_fee_spread_slippage_bbo": {
            "status": "MODELED_UNDER_REVIEW",
            "fee_tier1_usd_side": 2.46,
            "fee_class": "MODELED COST / VERIFIED_VS_ACCOUNT=NOT_RUN / UNDER REVIEW until new A7",
            "fx_alias_mapping": "PARTIAL (generic CME 'Forex Futures' group row; 6E/6B not printed verbatim next to 1.60)",
            "modeled_round_trip_bp": {"6E": [3.6, 6.3], "6B": [6.3, 11.2]}[sym],
            "spread": "high-biased close-proxy; BBO NOT_RUN (D5 ruling: not purchased)",
            "pins": {"FEES_CORRECTED.md": pins["FEES_CORRECTED.md"]["sha256"],
                     "fx_hypotheses.json": pins["fx_hypotheses.json"]["sha256"],
                     "a7_fee_packet": {"status": "READY-not-run", "sha256": "60b095fefe36c94d6dd02fa4d911088519a6055899c0478225ef04cac74f9dfc"}},
            "notional_range_usd": notional,
        },
        "7_trial_budget": {
            "status": "RECOUNTED_NO_NEW_TRIALS",
            "fx_family_census": "288 base + 360 strata contingency = 648 program-hypothetical, NO ceiling defined by standing ruling",
            "subset": "all 648 on 6E/6B; 6J/6A separate census",
            "pb2_contingency": "FX-F1 census contingency only (PB2 HOLD)",
            "artifact": "fx_eb/census/fx_census_recount.json",
        },
        "8_reproduction_a7": {
            "status": "BASELINE_A7_PASS_WITH_ERRATA; FEE_A7_READY_NOT_RUN",
            "baseline": "A7-DEEP-6E / A7-DEEP-6B verdicts + errata ledgers in dossier v2 section 11 / audit dirs (deepresearch V2, tracked at base sha)",
            "q5_verify_this_round": "pcal_58 PASS 13/13 claimed values reproduced from bytes; 30/30 svc captures hash+parse PASS (own parser)",
            "fee_a7": "packet READY-not-run; until it runs, fee layer stays UNDER REVIEW",
        },
    }


doc = dict(COMMON)
doc["6E"] = {"dims": dims("6E", 125000, "EUR", "0.00005", 6.25,
                          "3,054,311 outright 1m bars 2020-01..2026-09 (3 eras: AV1B backfill2 886,127 / AV1R backfill 1,823,090 / AV1T 345,094)",
                          "era butts verified no-overlap (BACKFILL_LEDGER job GLBX-20261002-94UVSCXK6G, $3.47); holes register in 6E_a6_dq.json; O1M present for all 16 expiry quarters 2023-2026 inside panel span through 2026-09-30",
                          [119400, 155363])}
doc["6B"] = {"dims": dims("6B", 62500, "GBP", "0.0001", 6.25,
                          "~2.55M outright 1m bars 2020-01..2026-09 (5 parquet files, shas pinned in 6B_DEEP_v2 section 0)",
                          "vendor file butts at quarter boundaries; serials/calendar-spreads excluded by design and counted in dossier section 7; two-rule roll agreement 1458/1746 sessions (83.5%) documented in dossier; O1M present for all obtained expiry quarters inside panel span",
                          [64950, 88878])}
doc["closing_law"] = "data-ready != scored-authorized"
doc["blockers_for_scored_use"] = {
    "6E": ["NO_GO_SCORE standing ruling", "fee layer UNDER REVIEW (account verification NOT_RUN until A7)", "BBO/execution realism NOT_RUN (D5)", "ECU26/ECZ26 expiry cells NOT_OBTAINED (calendar incomplete for late-2026 rolls)", "7 aged-out 2023 holiday windows inconclusive"],
    "6B": ["NO_GO_SCORE standing ruling", "fee layer UNDER REVIEW (A7)", "BBO NOT_RUN (D5)", "holiday/deviation grid entirely NOT_OBTAINED (id-42 absent from archive)", "6 expiry cells 2023Q1-2024Q2 NOT_OBTAINED (no archived 6B calendar covers them)", "6B leg of F4 gated on gap-std anatomy (baseline not_run register)"],
}
out = LANE / "fx_eb_readiness.json"
out.write_text(json.dumps(doc, indent=1))
print("wrote", out)
print("expiry counts:", expiry["6E"]["obtained_2023_2026"], expiry["6B"]["obtained_2023_2026"])
