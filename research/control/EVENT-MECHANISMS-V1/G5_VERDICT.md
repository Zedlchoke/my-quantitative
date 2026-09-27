# G5 VERDICT — EVENT-MECHANISMS-V1 (r3-canonical rebuild + re-comparison, 2026-09-27)

Task: `delta-r3` (A1-directed remediation + re-run lane). Binding authority:
`G3_FREEZE_ADDENDUM_r3.md`. Both implementations (lane I `engine/`, lane X
`lane_x/engine_x/`) rebuilt all books to the r3 canonical reading and were
re-compared record-only (R2-6 respected: zero PnL/aggregate computed
anywhere, at any depth).

## G5 final verdict

**G5_PASS_RESIDUALS_CLASSIFIED**

- Zero DEFECTs remain (the two r3 defects D-1/D-2 are fixed in lane I; one
  residual defect found in lane X during re-comparison — exhaustion-exit
  semantics vs r3 AMB-7 "exhaustion = last bar + DELISTING_EXIT flag" —
  was fixed in-lane; fix iteration 1 of max 2).
- Zero unattributed diffs. All 789 residual records classify to spec
  ambiguities that r3 did NOT rule (fold force-flat at book stage; A2
  issuer-day basis; A2 row-level vs transaction-level unpriced-drop
  semantics) — none traceable to the 16 r3-ruled AMBs, i.e. every r3
  ruling converged to byte-identity.
- A1 identity is fully adjudicable at G4; A2 is NOT_RUN_THIN per
  F-ADJ-1 regardless (F1 = 0 substrate fact).

## What each lane changed (r3 delta)

Lane I (`engine/`):
- **D-1**: A2 entry = first session whose 09:30 ET open is STRICTLY after
  the acceptance instant (`resolve_entry_open_anchored`); A2 records carry
  `direction_session = null` (no A1-style direction session in the A2 law).
- **D-2**: div/split tables resolve via case-insensitive normalized stems;
  collision-counted, deterministic; CA loader census recorded
  (4,336 files, 0 casefold collisions).
- **AMB-1**: weekend acceptances are anchor members — stratum label `WKND`
  (S1∪S3∪S4∪WKND). Production weekend candidates: 0 (both lanes, measured).
- **AMB-7**: unfillable EXIT rolls forward (was: exclude); exhaustion =
  last permissible bar + `delisting_exit` + note. `X_EXIT_FILL` reason
  retired from the pipeline.
- **AMB-9**: fold assignment by ET-LOCAL acceptance date (was UTC date).
- **AMB-13/15**: CA exclusion checked on the FINAL window after the roll,
  as a CALENDAR-interval compare (ex-dates need not be session dates).
- AMB-10/11 (strict close; tie 0 excluded+counted), AMB-14 (15% cap stays
  execution-stage), AMB-16 (symmetric B1) already canonical — pinned by
  new regression tests.
- Accepted r3 rulings already lane-I-canonical: AMB-2/3/4/5/6/8/12.

Lane X (`lane_x/engine_x/`):
- **AMB-1**: weekend acceptances moved from a separate excluded bucket INTO
  the anchor as stratum `WKND` (N2 still S2-only).
- **AMB-6**: unpriced A2 rows DROP + count (`A2_ROW_UNPRICED`); the
  panel-close price fallback (imputation) is removed.
- **AMB-11**: direction ties EXCLUDED + counted (`ZERO_DIRECTION_
  SESSION_MOVE`); no direction-0 records.
- DVmed60 eligibility floor applied at book stage (frozen cost contract
  X1/X2; r3 AMB-14 leaves only the 15% cap at execution) with the frozen
  band inputs now carried on records (`dv_band_class`, `dvmed60_decision`,
  per-side bps) — closes the 13,100-record pre-r3 DV-floor divergence.
- Panel ingestion guards aligned to lane I (duplicate-date first-wins
  marked-before-validity; non-finite/non-positive open/close skipped) —
  closes the panel-guard DATA_VARIANT class.
- **Fix iteration 1 (found at re-comparison)**: roll EXHAUSTION now moves
  the exit to the LAST bar + `delisting_exit` (r3 AMB-7 verbatim); the
  pre-fix reading kept the exit at the failing bar.
- Direction recorded as `LONG`/`SHORT` (representation parity with lane I).

## Re-comparison results (records only)

Key = (cik, acceptance_utc). Fields compared byte-identically
(json-canonical): direction_session, direction, entry_session, entry_price,
exit_session, exit_price, delisting_exit, fold, stratum, hold_sessions,
exclusions_applied, dv_band_class, dvmed60_decision, cost_entry_bps_x1,
cost_exit_bps_x1, ticker_reuse_risk.

| arm | lane I | lane X | intersection | only I | only X | key-set identical | field-identical |
|---|---|---|---|---|---|---|---|
| A1 anchor | 14,096 | 14,098 | 14,095 | 1 | 3 | no (4 diffs, all force-flat class) | 14,092/14,095 = 99.979% |
| A1 N2 | 14,565 | 14,565 | 14,565 | 0 | 0 | **YES** | 14,561/14,565 = 99.973% |
| A2 anchor | 2,903 | 2,837 | 2,271 | 632 | 132 | no (structural day-basis) | 2,257/2,271 = 99.383% |

A2 secondary match on the shared triggering filing (cik, acceptance_utc):
2,271 of lane I's 2,903 instants matched; 2,257 field-identical; the 14
diffs are all fold force-flat exits (lane I clamp at the 2022-12-30 /
2020-12-31 fold boundaries vs lane X full windows). Entry law (D-1),
entry/exit sessions, direction, DV band and cost fields are byte-identical
on every matched record outside the force-flat class.

### Residual classification (789 records, 0 unattributed, 0 DEFECT)

| class | records |
|---|---|
| r3-SPEC_AMBIGUITY — fold force-flat at book stage (lane I convention, unruled at r3; evaluation-stage fold isolation belongs to G4) | 27 |
| r3-SPEC_AMBIGUITY — A2 issuer-day basis unruled at r3 (lane I: (cik, UTC acceptance date); lane X: (cik, transaction_date)) | 599 |
| r3-SPEC_AMBIGUITY — A2 value aggregation / unpriced-drop semantics unruled at r3 (row-level drop vs transaction-level drop) | 163 |
| DEFECT | 0 |
| DATA_VARIANT (field representation) | 0 (direction/labels aligned in the delta) |

All 27 force-flat residuals verified mechanically (e.g. anchor key
CIK0000063754/2026-06-25: lane I's force-flat window [06-29..06-30] hides
the 2026-07-06 div ex-date that lane X's full window correctly catches
under the same convention-free reading — the two readings differ only
where the convention binds).

## Population census per arm per fold vs immutable floors

Floors (G3_FREEZE, immutable): >=100 bookable events per fold, >=400 total
per anchor.

| arm | F1 | F2 | F3 | F4 | total | >=100/fold | >=400 total | verdict |
|---|---|---|---|---|---|---|---|---|
| A1-ANCHOR (lane I) | 3,679 | 4,013 | 2,553 | 3,851 | 14,096 | PASS | PASS | **PASS** |
| A1-ANCHOR (lane X) | 3,679 | 4,013 | 2,554 | 3,852 | 14,098 | PASS | PASS | **PASS** |
| A1-N1 (lane I) | 3,392 | 3,665 | 2,319 | 3,407 | 12,783 | PASS | PASS | neighbour (not floored) |
| A1-N2 (lane I = lane X) | 4,873 | 4,778 | 2,633 | 2,281 | 14,565 | PASS | PASS | neighbour |
| A2-ANCHOR (lane I) | 0 | 1,606 | 664 | 633 | 2,903 | **FAIL (F1=0)** | PASS | **NOT_RUN_THIN** (F-ADJ-1) |
| A2-ANCHOR (lane X) | 0 | 1,727 | 665 | 445 | 2,837 | **FAIL (F1=0)** | PASS | **NOT_RUN_THIN** (F-ADJ-1) |

A2 F1 = 0 on BOTH implementations: the pinned form4_stream substrate spans
2018-01..2025-05 — no 2015–2017 bytes exist (pre-2018 XML re-fetch is
www.sec.gov 403-blocked = BLOCKED_DATA). Per F-ADJ-1 the A2 identity is
NOT_RUN_THIN this cycle; mechanism UNADJUDICATED on merits; doors (a)
owner GA-1 network unblock -> pre-2018 XML extension -> new freeze, (b)
owner-directed substrate-honest re-freeze. No scored A2 cell will be
presented at the GO gate this cycle.

## Test re-run results (all E6 + proofs)

| check | result |
|---|---|
| lane I pytest (engine/tests/) | **35 passed / 0 failed** (22 pre-delta + 13 new r3-delta tests) |
| lane X pytest (lane_x/tests/) | **42 passed / 0 failed** (37 pre-delta + 5 new/updated r3 tests) |
| lane I truncation replay (seed 7, 300 events + 18 fold-boundary) | **318/318** V1 entry-prefix + **318/318** V2 full-record byte-identical |
| lane I full-chain determinism double-run | **10/10 output files byte-identical** (build, controls, rho, costs, truncation) |
| lane X determinism double-run | **6/6 outputs byte-identical** (evidence/determinism.txt) |
| lane I dry-run proofs | pairwise-distinct record IDs: TRUE; recursive no-PnL scan: CLEAN (16 files) |
| staged digest pins (both lanes) | EXACT (a1_events a6a5bb6e…/54,941; form4_stream 6ac2cd5b…/546,039; n4_map 537cd5af…/2,178; NG6 panel 2,169-file manifest) |

## Boundary compliance

R2-6 held everywhere: decision/fill records, exclusion censuses and
population counts only. No return, expectancy, PF or PnL aggregate was
computed by either engine or by this re-comparison (machine-scanned).
No ledgers, registries, lanes or the root checkout were touched; no push,
no merge; pathspec staging only.

## Artifacts

- `reconciliation/compare_r3.py` + `reconciliation/comparison_results.json`
  (per-arm key/field stats, every residual record classified)
- `engine/evidence/` (rebuilt books + controls + rho + costs +
  truncation_replay.json + determinism_full_run.json + pytest_run.txt)
- `lane_x/output/` (rebuilt books/census/manifest) +
  `lane_x/evidence/` (determinism.txt, pytest_run.txt)
- `engine/REPORT.md` — dated delta section appended
