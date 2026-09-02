# S3 A7 — Independent audit of the six S2 proposals: scope and method

- auditor: A7 (independent novelty / prelaunch / terminal audit lane)
- branch: `orca/stocks-s3-a7-audit`, bootstrap SHA `9e7eada44e3ff716621ce9a08f84d71df54fca4b`
- audited at: 2026-09-02
- identity check: `pwd` = `.worktrees/stocks/s3-a7-audit`, HEAD `9e7eada44e3ff716621ce9a08f84d71df54fca4b` == BOOTSTRAP_SHA, branch `orca/stocks-s3-a7-audit`, `git status --porcelain=v1` empty at start. PASS.
- write scope: this directory only. No proposal, PLAN, control-plane or production file was edited.

## Audit inputs (read-only)

1. Six proposals: `research/proposals/stocks/{a3,a4,a5}_family{1,2}.{json,md}`.
2. `PLAN_stocks.md` §9 (proposal contract, priority spaces, ineligibility) and §1 (scope).
3. `research/control/stocks_run/selection_rubric.json` (frozen 2026-09-02T15:18:47Z; `budget_after_freeze: 0/6`).
4. `research/control/stocks_run/state.json` — phase S1_COMPLETE, `published: 0, observed: 0, budget_used: 0`. Confirmed: **no scored result exists**; this audit is outcome-blind by construction.
5. Factory as-built: `research/assets/stocks/{provider,universe,loader,data_audit,calendar,corporate_actions,accounting,execution,portfolio}.py`, `research/assets/common/*.py` — every proposal API claim was checked against source.
6. Rejected crypto-family inventory: `research/wayfinder/MAP.md` (V6 CARRY-1D/3D/7D funding-carry rejects; REVERSE-3D weekly-reversal control failed as designed; V9 REJECT_ALL_MULTI_FAMILY), root `PLAN.md` §1 (`M01_FAMILY_REJECT`: anchor PF 2.42e-08, placebo ≈ mechanism; "no M01-adjacent aggressor-flow proposal unless the novelty audit proves a different observable, counterparty, holding clock and causal control").

## Method

Per proposal, seven dimensions (PLAN §9): novelty; source quality; correlation; data
readiness vs the as-built factory; cost/borrow feasibility vs declared cost models;
hidden crypto-family rescue; plus rubric scoring E1–E7 exactly as defined in
`selection_rubric.json`. E7 = A7's own count of unresolved HIGH/CRITICAL
objections == 0. Objection severity: CRITICAL/HIGH = disqualifying if unresolved;
MEDIUM/LOW = advisory, does not block.

## Factory verification record (facts relied on by all six audits)

Verified present and behaving as the proposals claim:

- `universe.py`: `SecurityMaster` (`ticker_as_of`, `members_as_of`, effective-dated
  ticker history anchored at `listed_date`), `MembershipTable` with mandatory
  `effective_from` and sole read API `members_as_of` (structural no-backfill ban,
  `MembershipBackfillError`), `EligibilityInput.history_days`,
  `build_rebalance_snapshot` (ACCEPTED/REJECTED rows with reasons + digest),
  `evaluate_delisting_retention`, `evaluate_s0_floors` (8.0y history floor,
  30-name decision floor, 12-month S0 buffer), `SealedWindows`.
- `loader.py`: `BarLoader` — checksum-verified, fail-closed missing partitions,
  tz-aware `ts_exchange`/`ts_ingest` with `ts_ingest >= ts_exchange` enforced,
  `allow_duplicate_timestamps` flag for event streams, declared
  `gap_tolerance_days`, `enforce_gaps` flag. **Caveat found:** `REQUIRED_BAR_COLUMNS`
  mandates numeric `open/high/low/close/volume` on every row — see A3 F1 audit.
- `calendar.py`: `US_EQUITY_REGULAR_V1`, frozen table `2010-01-01..2030-12-31`
  (2010–2026 consistent with published NYSE calendars; 2027–2030 rule-derived,
  flagged), `session_bounds`, `next_session`, `early_close_cutoff_utc`,
  `classify_gap` (inter-session gaps `GAP_OK_WITH_REASON`; in-session uncovered
  gaps `GAP_UNEXPLAINED`, never a synthetic fill), `HaltInterval`,
  `assert_baseline_scoring_phases`.
- `corporate_actions.py`: `CorporateActionEngine` (`apply_to_position`,
  `price_path`, `reconcile_raw_vs_total_return`, `ReconciliationRecord`),
  `classify_earnings_timestamp` → BTO/AMC, UNKNOWN fail-closed with reason.
- `accounting.py`: canonical identity terms incl. `cash_dividends`,
  `short_dividend_liability`, `short_borrow_fees`, `terminal_pnl`;
  `DividendEvent` (fields: `symbol`, `dividend_per_share`, `ex_date_utc` **only**),
  `BorrowLocate` (unavailable locate ⇒ reject; available locate requires PIT
  `annual_rate`), `compute_borrow_fee` (360-day basis), `accrue_borrow_fee`
  (fail-closed on open short), `IdentityLedger.apply_dividend` (flat position
  books nothing), `finalize_terminal` (last executable event only),
  `submit_short_sale` (MISSING_LOCATE/NO_LOCATE reject, never free fill).
- `execution.py`: `EquityExecutionModel.attempt_fill` fail-closed order
  HALTED → SESSION_CLOSED → MISSING_QUOTE → MISSING_ADV → PARTICIPATION_CAP;
  `SpreadPolicy` (quotes-or-declared-proxy), `ImpactModel` (sqrt, hard
  participation cap), `next_executable_event_index`, `deferred_entry_timestamp`.
- `portfolio.py`: `SharedCapitalReplay.submit_intent` — locate gate BEFORE fill on
  shorts; `apply_dividend`, `accrue_borrow_fee`, `record_rejection` per arm.
- `provider.py`: every adapter defaults to `NO_ENTITLEMENT_FAIL_CLOSED`;
  `SOURCE_FREE_CONVENIENCE` can never satisfy authority (`DIAGNOSTIC_ONLY`);
  `REQUIRED_LICENSE_SCOPE` = (PIT_SECURITY_MASTER, DELISTINGS, CORPORATE_ACTIONS,
  HISTORY_WITH_ADJUSTMENTS).

## Correlation dimension — global statement

PLAN_stocks sets **no numeric rho threshold**. The frozen rubric records:
"quantitative prewindow rho marked NOT_IMPLEMENTABLE_NO_REAL_DATA". This audit
therefore evaluates **structural orthogonality only** (observable / clock /
counterparty / control) and states explicitly: **numeric prewindow correlation
among the six families is NOT_IMPLEMENTABLE_NO_REAL_DATA** — no real price
history exists in this sprint (all real data NO_ENTITLEMENT; synthetic fixtures
only), so no correlation number computed here would be evidence of anything.

## Summary verdict table

| # | family_id | E1 | E2 | E3 | E4 | E5 | E6 | E7 | sum | quality | highest unresolved | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `EQ_S2_A3_F1_PIT_RECON_FLOW` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 7/7 | 8.5 | MEDIUM | ELIGIBLE |
| 2 | `EQ_S2_A3_F2_LISTING_AGE` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 7/7 | 8.0 | MEDIUM | ELIGIBLE |
| 3 | `A4_F1_PEAD_TS_V1` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 7/7 | 7.5 | MEDIUM | ELIGIBLE |
| 4 | `A4_F2_OVI_DECOMP_V1` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 7/7 | 7.5 | MEDIUM | ELIGIBLE |
| 5 | `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 7/7 | 8.0 | MEDIUM | ELIGIBLE |
| 6 | `A5-S2-F2-EXDATE-TAX-CLIENTELE-CAPTURE` | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 7/7 | 7.0 | MEDIUM | ELIGIBLE |

Frozen selection rule: "eligible = rubric sum 7/7; rank by (A7
novelty_source_quality score desc, hypothesis_id lex asc); take exactly top 2".
All six are 7/7; expected ranking below. Ties at 8.0: `A5-S2-F1-...` sorts lex
before `EQ_S2_A3_F2_...`, so A5 F1 takes the tie-break.

1. **`EQ_S2_A3_F1_PIT_RECON_FLOW` (8.5)** — expected rank 1.
2. **`A5-S2-F1-LENDING-CONSTRAINT-PREMIUM` (8.0, lex tie-break)** — expected rank 2.
3. `EQ_S2_A3_F2_LISTING_AGE` (8.0) — rank 3 on lex.
4. `A4_F1_PEAD_TS_V1` (7.5) — lex before A4 F2.
5. `A4_F2_OVI_DECOMP_V1` (7.5).
6. `A5-S2-F2-EXDATE-TAX-CLIENTELE-CAPTURE` (7.0).

A1 makes the binding selection; this audit publishes scores and objections only.

## Blockers and assumptions of this audit

- All six proposals are real-data BLOCKED pending owner-authorized entitlement
  (`NO_ENTITLEMENT_FAIL_CLOSED` verified as the provider default). None asserts
  an entitlement. Per PLAN §0 and §9, scored real research cannot run this sprint
  regardless of selection; S4 proceeds on synthetic fixtures only.
- Literature in all six proposals is `MODEL_INTERNAL_UNVERIFIED` (no network in
  this sprint). A7 checked citations against internal knowledge only; no citation
  was identified as fabricated, and none is asserted as verified.
- E7 reflects objections as of this document; a proposal with an unresolved
  HIGH/CRITICAL raised later (e.g. at S5 prelaunch) loses E7 retroactively per
  the rubric's definition.
