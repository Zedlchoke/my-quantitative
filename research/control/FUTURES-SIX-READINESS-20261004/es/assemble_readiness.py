#!/usr/bin/env python
"""
ES-READINESS lane, FUTURES-SIX-READINESS-20261004 — Task 6:
assemble the 8-dimension data-readiness verdict from this lane's own
re-verification artifacts (no new evidence invented; NOT_RUN stays NOT_RUN).
Writes es_readiness.json next to this script.
"""
import json
import os
import sys

OUT = os.path.dirname(os.path.abspath(__file__))

def load(name):
    return json.load(open(os.path.join(OUT, name)))

expiry = load("es_expiry_recheck.json")
o1m = load("es_o1m_roll_recheck.json")
session = load("es_session_holiday.json")
fee = load("es_fee_status.json")
census = load("es_trial_census.json")
q5 = load("q5_independent_verify/verify_report.json")

dims = [
    {
        "dim": 1, "name": "identity/tick",
        "status": "PASS",
        "claim": ("ES = E-mini S&P 500, CME Globex; multiplier 50 USD/index-pt; "
                  "minimum tick 0.25 index pts = $12.50/tick; quote in plain "
                  "index points; 71 outright quarterly contracts keyed by vendor "
                  "instrument_id; dash (calendar-spread) symbols filtered by law; "
                  "deferred 2027 stray tails excluded by >=100k volume floor"),
        "evidence": [
            "FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/es_nq/ES_DEEPFOUR_V3_ADDENDUM.md §1 [FACT rows: mult/tick corroborated DATACONTRACT §1.1 + SPEC_PB1_ES §1]",
            "research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md §1 (binding: mult 50, tick 0.25 = $12.50)",
            "FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_contracts.json + es_1m_outright.parquet (7,825,657 bars re-measured this lane — exact match to dossier)",
        ],
        "residuals": ["TACO/BTIC/TMAC 0.05 sub-tick instruments exist in specs but are excluded from the outright chain by construction"],
    },
    {
        "dim": 2, "name": "O1M coverage + holes",
        "status": "PASS",
        "claim": ("16.4y panel 2010-06-06..2026-10-01, 4,204 sessions, 7,825,657 "
                  "1m bars (re-measured exactly); 0 OHLC violations, 0 duplicate "
                  "(instrument,minute) rows, 0 Saturday sessions; era coverage "
                  "~97% (E1) -> 100% (E6-E7) of era-correct session length"),
        "evidence": [
            "es_o1m_roll_recheck.json o1m_panel (this lane: rows/span re-measured from ES_cache/es_1m_outright.parquet)",
            "FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_quality_ledger.json eras (n_sessions 665+732+385+711+483+452+776 = 4,204; coverage_vs_1380 per era)",
            "FUTURES-OVERNIGHT-PREP-20261003/synth/BLOCKER_MATRIX.md ES row: 'PASS in-hand: 4,204 sessions 2010-2026, 0 integrity violations'",
        ],
        "residuals": [
            "remaining per-era minute-gap share 0.03%-0.90%",
            "residual 16:00-16:59 maintenance-window single-mark prints: 24,653 bars across 1,267 sessions (pre-2016 tail in BRK bucket, excluded from RTH/ON aggregates — disclosed)",
            "vendor-vs-IBKR close = settlement-mark convention gap (median 15 ticks RTH-close), IBKR closes never fill prices",
        ],
    },
    {
        "dim": 3, "name": "roll/expiry",
        "status": "PASS",
        "claim": ("Expiry calendar CLOSED 68/68 quarters 2010-2026 — re-derived "
                  "this lane by unioning the three baseline sources (37 D3 "
                  "product rows + 26 DEEPFOUR family rows + 5 OVERNIGHT gap "
                  "quarters), zero conflicts, zero missing; all 68 dates parse, "
                  "67 are 3rd Fridays + ESM6 2026-06-18 Juneteenth shift; "
                  "quarterly spacing 84-98 days, 0 violations; data-side: 66/66 "
                  "ES_cache roll expiries match authority dates"),
        "evidence": [
            "es_expiry_recheck.json (this lane machine re-derivation + byte-grep of G1a/G1b/NQ captures; G1a+G1b sha256 match baseline claims)",
            "FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/es_expiry_coverage.json (26 family quarters, cross-checks)",
            "FUTURES-OVERNIGHT-PREP-20261003/cme_cal_gap/equity/EQ_GAPFILL_EVIDENCE.md (gap-1 CLOSED, 68/68 arithmetic)",
            "FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md (37-row product master table; prose verdict '36' = counting slip, rows count 37)",
        ],
        "residuals": [
            "capture bytes for D3 C10/C11 and DEEPFOUR R4 not present in this worktree — mid-era/2024-25/2026 spot-checks ran on the authority-claim vs data-side leg (all match); capture-byte legs recorded NOT_RUN_IN_THIS_WORKTREE with pointers",
            "2026-12 and 2010-03 expiries outside data window (authority rows only)",
        ],
    },
    {
        "dim": 4, "name": "session/holiday",
        "status": "PASS",
        "claim": ("Holiday windows 17/17 years 2010-2026 authority-backed; "
                  "era-correct weekly template OBSERVED in bars "
                  "(16:30 -> 16:15 -> 16:00 CT close marks); 2026 ES product "
                  "Globex weekly template + all 11 holiday-deviation windows "
                  "OBTAINED_PERMITTED and INDEPENDENTLY VERIFIED this lane from "
                  "Q5 raw capture bytes (15 present captures, all sha256 match, "
                  "23/23 claimed cells reproduced); day-offset legality: 161 "
                  "date checks + 36 event-row checks + DST consistency, all "
                  "legal; unproven ES-specific days 2011-2025 are deterministically "
                  "EXCLUDEd fail-closed by frozen SPEC §2-E1 law"),
        "evidence": [
            "es_session_holiday.json (this lane assembly + legality validation)",
            "q5_independent_verify/verify_report.json verdict VERIFIED_WITH_RESIDUALS (own sha256 + own re-extraction from raw bytes; 8 claimed captures absent from disk AND fetch_log — residual, none needed to reproduce claimed cells)",
            "FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md (17/17 years; 2010 full product-level PDF detail)",
            "FUTURES-ES-V1-PACKET/audit/a7_spec/a7_spec_checks.json R5 PASS (E1 EXCLUDE fail-closed law; measured early-close sessions 3-10/yr)",
        ],
        "residuals": [
            "ES product-level Globex early-close TIMES 2011-2025 NOT_TRANSCRIBED (live in per-holiday official files) — SPEC §2-E1 EXCLUDE fail-closed applies to any day not proven ES-specific",
            "P3#2 ClearPort 2026 row PENDING_ADJUDICATION (row sits in preserved Q5 capture; P3-lane captures ineligible; not extracted here)",
            "2025 June-capture ClearPort table NOT_TRANSCRIBED beyond advisory rows",
            "8 of 23 Q5-listed deviation captures missing from disk and absent from Q5's own fetch_log (coverage-JSON over-claim; sha unverifiable; zero claimed cells lost)",
        ],
    },
    {
        "dim": 5, "name": "event PIT (BLS/FOMC)",
        "status": "PASS",
        "claim": ("CLOSED-PREP: BLS calendars PASS_EVIDENCED — CPI 204 + EMPSIT "
                  "204 scheduled dates 2010-2026 all 08:30 ET, per-year wayback "
                  "verifiers; 2025 vintage law measured (11 CPI / 10 EMPSIT "
                  "actual prints, 2 canceled-day falsifiers; recurs 2026); FOMC "
                  "132 statement days day-level law (base-EXCLUDE), 92 timed "
                  "minute-level 2016+; decision-date-keyed schedule vintage"),
        "evidence": [
            "FUTURES-OVERNIGHT-PREP-20261003/bls_vintage/bls_vintage_evidence.json + BLS_VINTAGE_INVESTIGATION.md",
            "hypo/es_nq/esnq_hypotheses.json standing_context.bls_pit (supersedes stale v3 'CPI/NFP NOT_RUN' calendar claim)",
            "FUTURES-ES-V1-PACKET/audit/a7_spec/a7_spec_checks.json R5 + SPEC_PB1_ES §3 [ERRATUM A7-SPEC-M3]",
        ],
        "residuals": [
            "PIT consensus/surprise archive NOT_RUN (never acquired — H3 blocker)",
            "publish-latency measurement NOT_RUN",
            "FOMC statements 2011-2015 lack release-time text (minute anatomy NOT_RUN there; day-level law safe)",
        ],
    },
    {
        "dim": 6, "name": "fee/spread/slippage/BBO",
        "status": "BLOCKED",
        "claim": ("Corrected tier-1 all-in 2.24 USD/side UPHELD as MODELED COST "
                  "(P0 erratum UPHELD in full; byte-level glue adjudication), but "
                  "VERIFIED_VS_ACCOUNT=NOT_RUN (owner decision D2 OPEN), SPEC §5 "
                  "published 21.006/33.506/46.006 is UNDER-REVIEW-ERRATUM until a "
                  "new A7 fee re-audit runs (packet READY, NOT RUN), the "
                  "USD 0.01/side regulatory-basis divergence (NFA timeline vs "
                  "IBKR capture basis) is OPEN, and BBO/depth is NOT_RUN "
                  "program-wide"),
        "evidence": [
            "es_fee_status.json (this lane restatement + sha256 pins of all cited fee artifacts)",
            "FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/verify/P0_ERRATUM_VERDICT.md §7 (UPHELD in full)",
            "FUTURES-OVERNIGHT-PREP-20261003/fees_erratum/impact/GATE_REVIEW_NOTE.md §1 (SPEC §5 + cost gates UNDER REVIEW)",
            "P3 round synth/FINAL_SAFE_BLOCKER_MATRIX.md ('A7 packet READY (not run)'; ES row 'D3 $0.01 reg-basis open')",
        ],
        "residuals": [
            "overnight-position fee tables NOT_RUN (JS-driven, never render)",
            "spread half-turn is a 1-tick close proxy (high-biased), never BBO",
            "slippage tiers are declared assumption D1",
        ],
        "blocks_scored_use": True,
    },
    {
        "dim": 7, "name": "trial budget",
        "status": "BLOCKED",
        "claim": ("ES minimal identity demand recounted 36 (F1 11 + F2 11 + "
                  "F3 7 + F4 7) vs frozen cap 24 (SPEC_PB1_ES r3 A-r4 explicit "
                  "list: P-A 8 + P-B 8 + FOMCIN 4 + C1-C4 4); headroom 0; every "
                  "new ES family BLOCKED_TRIAL_BUDGET — standing, unchanged"),
        "evidence": [
            "es_trial_census.json (this lane recount; all 24 frozen IDs enumerated from SPEC §6 patterns)",
            "FUTURES-OVERNIGHT-PREP-20261003/hypo/es_nq/RANKING_INPUT.md §3 census table",
            "FUTURES-OVERNIGHT-PREP-20261003/synth/CENSUS_FINAL.md §3 (the ES cap conflict)",
            "FUTURES-ES-V1-PACKET/audit/a7_spec/a7_spec_checks.json R1 PASS (identity grid 24 recomputed)",
        ],
        "residuals": [
            "executable at 0 identities: ES-F3 stage-1 vol leg + F1/F2/F4 anatomy pre-gates + X-1..X-5 diagnostics (0-cost classes only)",
            "any ES expansion requires owner amendment + ceiling re-check",
        ],
        "blocks_scored_use": True,
    },
    {
        "dim": 8, "name": "reproduction/A7",
        "status": "PASS",
        "claim": ("Baseline reproduction re-verified this lane at machine level: "
                  "7,825,657 panel rows exact; 4,204 sessions exact; 66/66 roll "
                  "crossovers recomputed from es_contract_daily.parquet match "
                  "es_roll_table.json; |T-5 - crossover| <= 3 sessions 66/66; "
                  "sign-match 61/66 reproduced; 68/68 expiry union reproduced; "
                  "23/23 Q5 2026 cells re-extracted from raw bytes; A7-SPEC "
                  "verdict on file FREEZE_READY_WITH_ERRATA (0 BLOCKER/0 MAJOR, "
                  "5 MINOR applied at r3); NO_GO_REGISTER/SCORE/ORDER stands"),
        "evidence": [
            "es_o1m_roll_recheck.json + es_expiry_recheck.json + q5_independent_verify/verify_report.json (all written by this lane's own scripts in this worktree)",
            "FUTURES-ES-V1-PACKET/audit/a7_spec/a7_spec_checks.json (probes r1-r5 all PASS)",
            "FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md r3 header (FREEZE-READY r3, awaiting owner GO + registration)",
        ],
        "residuals": [
            "A7 FEE re-audit READY-NOT-RUN (required before any cost gate clears)",
            "S1 SEALED_UNTOUCHED (prospective post-freeze)",
            "D3 contract-qual reproduction not re-run in this lane (out of scope; status inherited CLOSED_WITH_ERRATA r6)",
        ],
    },
]

readiness = {
    "schema": "es_readiness@1",
    "lane": "ES-READINESS",
    "round": "FUTURES-SIX-READINESS-20261004",
    "worktree": "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep",
    "branch": "codex/futures-six-readiness-20261004",
    "base_sha_measured": "d7fc62312947b2613523dd401d44c9ec1a8d166b",
    "dims": dims,
    "blocking_dims": [
        {"dim": 6, "name": "fee/spread/slippage/BBO",
         "why": "VERIFIED_VS_ACCOUNT=NOT_RUN (D2 open) + SPEC §5 UNDER-REVIEW-erratum + $0.01/side reg-basis divergence (D3-style, open) + fee A7 READY-not-run"},
        {"dim": 7, "name": "trial budget",
         "why": "36 minimal identities vs frozen 24, headroom 0 — BLOCKED_TRIAL_BUDGET stands"},
    ],
    "closing_line": ("data-ready ≠ scored-authorized — dims 1-5 and 8 are "
                     "evidence-complete at data-readiness level; dims 6 (fee "
                     "account verification D2/D3 + fee A7 re-audit) and 7 "
                     "(trial budget 36>24) still block scored use; "
                     "NO_GO_REGISTER · NO_GO_SCORE · NO_GO_ORDER stand"),
    "standing_rulings_unchanged": ["NO_GO_REGISTER", "NO_GO_SCORE", "NO_GO_ORDER",
                                   "ES 24 identities FROZEN (headroom 0)",
                                   "fees UNDER REVIEW until new A7",
                                   "BLS PIT vintage law in force"],
}
json.dump(readiness, open(os.path.join(OUT, "es_readiness.json"), "w"), indent=1)
print("dims:", [(d["dim"], d["name"], d["status"]) for d in dims])
sys.exit(0)
