# COOWNER_REVIEW_RESPONSE — FUTURES-BEHAVIOR-10SYMS-PREP-20261002 (A1 Lead, 2026-10-02)

Response to the co-owner review of sess_60f37a37. Pre-fix commit eae8c3d2 →
fix commit 60bbb48b (+ this response round). Independent audit round:
audit/A7_AUDIT_R2.md (fresh-context, commits work). Verdict at 60bbb48b:
**PASS — 0 BLOCKER / 0 MAJOR / 3 MINOR (all three fixed by Lead after the
audit, validator 22/22 PASS) / 5 NOTE.**

## The six findings — reproduce → fix → independent verification

| # | Reproduced at eae8c3d2 (A7-R2 own fixtures) | Fixed at 60bbb48b (verified numbers) | Tests |
|---|---|---|---|
| R1 commission | ES qty3 $4.48 rt; CL known fee zeroed to $0.00; slippage-missing kept cost_incomplete=False | qty3 $6.72/side, $13.44 rt; missing fee = NULL/NOT_RUN disclosed while known $0.85 charged; all-component incomplete-cost law; allow_incomplete_costs=False → PolicyError refusal | test_exec_costs.py (35 exec tests total) |
| R2 roll gross | journal 425/416.04 vs ledger 700/691.04 (missing 275) | journal=ledger 700/691.04; gross_segments [roll 275, exit 425]; independent per-bar journal↔cash↔events↔inventory↔MTM reconciliation (129 sessions) | test_exec_roll_accounting.py |
| R3 barrier/roll order | exit 184.75 on new contract, outside [198,205] | barrier evaluated on OLD position/contract before end-of-session roll: exit 94.75 in [90,115], 0 rolls; per-contract MAE/MFE segments; no full-day extrema before new fill | test_exec_barrier_ordering.py |
| R4 gap-stop | fill 94.75 outside bar range [70,90] | stop-market fills open-adverse (79.75); TP limit semantics distinct; entry-beyond-barrier; same-bar TP+SL stays AMBIGUOUS_ORDER with gap-aware bounds | test_exec_barrier_fills.py |
| R5 WF windows | fold1 37-38 cells through Jun-30 (29 excess), 31 label-immature, overlapping folds | fold1 exactly 7 cells; 1 PURGE + 2 LABEL_CENSORED + 29 POST_TEST_WINDOW audited; pairwise-disjoint enforced in plan(); producer-prefix PIT tests (bars+rolltable+metadata+selection) with counter-lookahead teeth | test_wf_window_integrity.py, test_wf_pit_prefix.py |
| R6 handoffs | 14/14 handoffs missing 15 of 17 canonical keys | originals archived byte-identical (dispatch/archive_attempt1/, A7-R2 cmp 14/14); 14 canonical replacements + script validator; MCP validator NOT_RUN disclosed; count 13→14 fixed everywhere | dispatch/validate_handoffs.py |

Suite: 417/417 OK at 60bbb48b = 147 base + 35 EXEC-FIX + 29 WF-PIT-FIX +
62 MULTIASSET-WIRING + 144 DBN-ADAPTER (A7-R2 re-ran it independently).

## Steering round (WAITING_DATABENTO_DATA deliverables) — status

1. Engine scope: DAILY synthetic end-to-end TESTED incl. portfolio layer;
   intraday beyond AMBIGUOUS_ORDER bounds + intrabar portfolio = NOT_IMPLEMENTED
   (typed, code/README.md). Journal covers win/loss/breakeven/blocked +
   roll/cost lifecycle + reconciliation (R2 fix). Multiasset netting/risk/
   MTM/DD WIRED + 62 tests (veto-never-clips, leave-one-leg full-path with
   proven non-additivity, frozen-marks no-lookahead); EXEC-FIX defect found
   by that lane (censored-with-roll broke reconciliation) fixed with pinning
   test. No scaffold is called ready.
2. DBN ingestion: code/futbt/dbn/ — DBN v3 framing/layouts verified vs
   official databento/dbn reference; contract identity from definitions;
   NO-CONTFUT-fill; DST/holiday sessions; BBO book-time taxonomy; negative
   CL exact; PIT publication gating; QA fail-closed; 144 tests, all
   synthetic. Live/billable/DBN-v1/v2/zst = NOT_IMPLEMENTED typed.
3. Strategy layer: configs/symbols ×10 (50 hypotheses, dossier-hash-bound,
   PARAM-GAP registers, validator exit 0) + pilot_nq_cl (79 seeded cells,
   full controls, TB labels train-only) + wf_manifest + coverage report
   (16 RUNNABLE_NOW / 30 WAIT_DATA / 4 BLOCKED_NONDATA).
4. DATABENTO_REQUEST_PACKET.md + data/request/request_manifest.json (15
   lines: 6 PILOT + 9 EXPANSION, hypothesis-bound) + metadata-only probe
   scripts (dry-run exit 0, zero network, no-key refusal exit 2).
5. DATA_ACCEPTANCE_CHECKLIST.md (data presence ≠ scored authority; stops at
   freeze+budget+gate+A7) + SYMBOL_READINESS.md (per-symbol gating chain to
   the TRUE blocker incl. non-vendor items: declared slippage ×10, exchange
   fees 9/10, holiday calendar, consensus/weather/macro vintages, HG not in
   corpus, serial re-fetch urgency).

## A7-R2 adversarial regressions (their own, 5/5 pass)

Margin veto + concurrent roll (exact shortfall math 48,117.40); zero-range
H==L bars never invent fills; missing fee disclosed NULL not 0; unknown DBN
rtype → typed error; WF horizon-5/3-fold/60-session disjoint.

## Post-audit Lead fixes (3 MINOR)

m1 configs/symbols/6A.yaml dossier hash re-pinned (post-erratum drift) —
validator PASS exit 0. m2 round-2 handoff canonicity (workers int,
commit_sha-null disclosures, log_digest backfill, digest layer restored to
commit-binding after a mistaken worktree overwrite by the Lead — disclosed
in each handoff's known_limitations; validator 22/22 PASS). m3 REQUEST-PACKET
two no-key-refusal test entries canonicalized as expect-exit-2 wrappers
(inner refusal unchanged). 

## Readiness matrix (summary; full chain in SYMBOL_READINESS.md)

| Area | Status |
|---|---|
| Execution/accounting/journal (daily, synthetic) | IMPLEMENTED + TESTED |
| Portfolio netting/risk/MTM/DD (synthetic) | IMPLEMENTED + TESTED |
| WF selection/purge/embargo/PIT-prefix (synthetic) | IMPLEMENTED + TESTED |
| DBN offline ingestion + QA (synthetic) | IMPLEMENTED + TESTED |
| Strategy configs + pilot + WF manifests | IMPLEMENTED (VALIDATED) |
| Intraday/intrabar beyond AMBIGUOUS_ORDER | NOT_IMPLEMENTED (typed) |
| Real-data anything scored | NOT_RUN — gated on data + registration + owner GO |
| Databento metadata probes (cost/coverage) | RUN by METADATA-PROBE lane (separate report) |
| Declared slippage / exchange fees 9/10 / holiday calendar source | OWNER_BLOCKER (non-vendor) |

## Standing gates

Registration/budget/freeze → owner GO per workspace law; data acceptance per
DATA_ACCEPTANCE_CHECKLIST; serial IBKR re-fetch time-critical (measured
age-out: 6JV5/6JX5 likely already lost; GCX5 at edge; F6-class ~Dec-2026);
Databento retrieval gated on owner budget approval of the pilot package
(even a $0 quote stops at the download gate).
