# CYCLE VERDICT — ERP1-TRACKA-COHORT-1 (REJECT_ALL)

- Terminal date (UTC): 2026-09-26. Integration branch orca/erp1-tracka-cohort-1-integration (see sha chain below).
- Parent: ECONOMIC-ROBUSTNESS-PROGRAM-V1 (Track A). Plan: plans/PLAN_erp1_tracka_cohort_1.md.
- A7 terminal: TERMINAL_AUDIT_PASS_WITH_CONDITIONS (audits/A7_terminal_REPORT.md); certified label below.
- Labels (binding on every citation): PAPER_TIER | SINGLE_SOURCE_PANEL | FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK.

## VERDICT: `REJECT_ALL` (umbrella §9)

No mechanism survived its falsifier battery. Per-record labels:

| mechanism | verdict | decisive evidence |
|---|---|---|
| M1 RANGEFADE-PIT (replication slot) | KILL_PIT_SEAM on BOTH pairs (+KILL_INVERSION: AUDUSD F5, USDCAD F1+F6) | R-ANCHOR fails G2/G3/G4 at dev (PF 1.0334/1.0509; 3/6 folds; net<0 @k1.5) while its one-day-lookahead twin R-ORIG passes all 8 gates (+3207.4/+5029.6 pips) — all three seam limbs fire with 100–180× margin (S=2884.1/4348.6 vs 20.0/24.0). The apparent range-expansion edge was the PIT seam, not economics. |
| M2 XCONF-ABSORB | NOT_SCORED_FALSIFIED (D2 veto V-4 blend, pre-PnL) | skeptic D2 adjudication as written; slot closed, no repair |
| M3 QSTATE-ABSORB | NOT_SCORED_FALSIFIED (F-5 arithmetic, pre-PnL) | measured stress RT 4.8 pips >= 2.0 kill line (USDCAD census) |

- Holdout 2026-01-01..2026-06-30 (both new pairs): consumed by NOBODY; preserved unread under the one-look law (C-3).
- Budget: 12 of 24 scored cells used; 0 holdout looks; 0 survivors. Observed == published for all ledger rows.
- Reproduction: detached twin ALL_MATCH (0 substantive differences; repro/REPRO_REPORT.md). P-4 applies: determinism proven, not truth.

## Errata bundle (A7 close condition C-1 — carried verbatim into every citation)

- F1: freeze code pin for scripts/tracka_lib.py cites 27f21671 (3931aed8 bytes); the sanctioned rebuild 43cb8b1f appended the placebo rebuild (+87 lines, append-only, NOT on the scored path) without refreshing the pin; scored-time bytes were 1e09b368. Numeric invariance doubly proven (not on execution path; twin re-ran committed bytes byte-exact).
- F2: scored rows cite scored_lib.py eabe8e84 (uncommitted run-time state); committed post-run bytes 1a5a9e00 without re-run; twin row diff is exactly that one field; numeric equality byte-confirmed.
- F3: GO-2 record received_utc (exactly midnight) post-dates authorized artifacts; registry write token 23:30:37Z carries the true GO-2->dryrun->scored order. Timestamp imprecision only.
- F5: SCORED_REPORT prose "USDCAD R-ORIG 5/6 folds" vs machine truth 6/6 — erratum recorded in SCORED_REPORT.md; prose not silently repaired.

## Sha chain

460d2acd (register) -> 43a84688/2682422a (data gate) -> 3931aed8/5b89e1ee (falsifier+freeze) -> 43cb8b1f/215ce855 (sanctioned placebo rebuild) -> 44a58af9 (dry-run) -> df9dda49 (scored) -> 9e21ce6f (handoff) -> 4aae6226 (repro harvest + erratum) -> <this close commit>. A7 terminal audited at 4aae6226.

## Denominators (P-9)

27 pre-PnL rows + 14 scored-phase rows + 1 terminal stamp = 42 ledger rows; 12 scored cells (0 holdout looks); DSR 0.0008/0.0016 (deflated to zero); PBO NOT_RUN fail-closed.

## Next owner-authorized paths (nothing auto-opens)

1. D-F: evidence classification of FX-RANGEFADE-2M-SHADOW-V1 (PROPOSAL_SHADOW_CLASSIFICATION..., DIAGNOSTIC_PENDING_PIT_REBASE) — unaffected by this verdict, still awaiting owner.
2. Owner-directed diagnostic (2026-09-26): daemon-law scored on EURUSD/GBPUSD runs on branch orca/erp1-tracka-cohort-1-diag (DIAGNOSTIC_OUTCOME_EXPOSED; can never promote); harvest pending — separate from this verdict.
3. Track A cohort 2 (if ever): only with fresh falsification room per umbrella §10.8; the failure memory now carries the PIT-seam class.

## Incidents (complete register)

c28577ef commit-message overclaim + erratum E1; scored lane pre-scored machinery fixes (bar-index/exit_kind cost book; np.float64 repr leak — numbers unchanged); repro prose slip (F5); F1/F2 sha-provenance imprecisions above. Nothing silently repaired.
