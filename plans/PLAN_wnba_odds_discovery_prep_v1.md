# PLAN — WNBA-ODDS-DISCOVERY-PREP-V1 (historical WNBA moneyline odds: data discovery + qualification, $0 spend)

- cycle_id: `WNBA-ODDS-DISCOVERY-PREP-V1` · asset: shared · **budget 0 scored by
  law** · GO phrase REGISTERED, NOT typed:
  `GO WNBA ODDS DISCOVERY PREP V1 SCORED RUN`
- Owner instruction 2026-10-09 (this chat): a separate PREP cycle about
  **historical WNBA odds**. Goal: enumerate as many WNBA moneyline odds sources
  2020–2026 as possible (vendor data, licensed archives, public CSVs, any other
  findable source), verify **pre-decision-time (PIT) price evidence**, and
  qualify which sources could feed a later money backtest. **DATA DISCOVERY +
  QUALIFICATION ONLY**: no PnL, no scored OOS, no GO, no paper/real orders, no
  purchases, no paid credits consumed, no account creation.
- Relationship: `WNBA-MONEY-BACKTEST-PREP-V1` (ACTIVE_LIGHT, untouched by this
  cycle) already surveyed the $0 space and recorded `NOT_RUN_ODDS` with a
  prospective-capture scaffold (The Odds API free tier, Pinnacle h2h,
  tip-relative T0−6h10m). This cycle BROADENS the search (paid + archives +
  datasets + B2B feeds) and deepens qualification; it must not modify that
  cycle's rows, ledgers, keys, quota, or any win-probability/paper cycle.

## 1. Frozen inputs (measured at bootstrap, sha-pinned in outputs)

- Decision anchor (DEFAULT, inherited frozen): **T0 − 6h10m** where T0 = first
  tip of that ET game-day; anchor timestamps are ET game-day-local. Census
  `CAPTURE_CENSUS_TIP_TIMES_V1.csv` (money worktree, 1,781 rows): **685 distinct
  ET game-days**, earliest ET tip 11:00, latest 23:00 ET, **0 anchors crossing
  ET midnight**.
- Forecast universe: `predictions_b1_wnba.csv`
  sha256 `99268f7314c3626842a1100961c36ff63f2c19232b5a209dc974179de72b0aae`
  (B1-WNBA frozen K=32/HCA=50/gamma=0.65, n=1,773) — the 1v1 join target.
  Census (1,781) vs B1 (1,773): the 8-row delta must be reconciled and
  journaled, never silently dropped.
- B1 2020–2026 is `RECONSTRUCTED_RETROSPECTIVE`: even Class-A odds never make
  that backtest a prospective edge.

## 2. Qualification law (per source, then per row)

- **Class A** (only class proposable for the current policy backtest): documented
  rights for internal research use + row-level PIT evidence
  (`snapshot_time <= anchor` AND `line_update <= snapshot_time < tip`) + both
  sides from the same bookmaker/snapshot + certain 1v1 join.
- **Class B**: genuine pre-tip prices but anchor (or same-book/two-sided)
  requirements unmet — reported separately, never merged into the current
  policy's backtest.
- **Class C**: missing timestamps, missing/ambiguous rights, or uncertain join.
- Target snapshot: `snapshot_time <= anchor` and `line_update <= snapshot_time
  < tip`. Prices that are only "pre-tip but post-anchor" are Class B evidence,
  reported with counts.

## 3. Survey scope

Free AND paid candidates: odds aggregators/APIs (historical endpoints), betting
exchange archives, B2B data vendors, commercial archives, public CSV/dataset
releases, sports-media archives. Per source record: seasons covered,
bookmakers, home/away two-sidedness, odds format, snapshot timestamp semantics,
line last_update, tip times, API/CSV schema, usage rights (primary-source
quote), cost, rate limits, machine-downloadability. **The Odds API deep-dive
required**: WNBA history start date, snapshot semantics, games per query,
credit accounting per region × market, and a cost estimate built from the
actual 685-day batch census (days × credits), never games × credits guesswork.
No paid endpoint calls, no signups, no use of the standing paper key against
any historical endpoint or quota not separately authorized.

## 4. Controlled sample audit (before any outcome viewing; outcomes are moot
here — the audited fields are identity/claims)

- Fixed rule declared first: from census sorted by `tip_utc`, systematic sample
  every 36th row (seed 20261009, start offset 18) → 49 games stratified across
  all 7 seasons including first/last game of seasons; sample list published in
  the audit artifact before verification runs.
- Two independent fresh-context checkers verify team names, tip UTC/ET,
  bookmaker identity where a source was readable, and source-doc claims
  directly against primary evidence; URLs + retrieval time + sha256 recorded
  where rights allow; no prohibited copying.
- Machine-side full-universe coverage: measured only for sources legally
  fetchable; otherwise coverage per season is `NOT_RUN_<reason>`, never assumed.
- Report match/discrepancy rates and causes. The sample is never re-picked
  because it "looks bad".

## 5. Outputs + stopping rule

- Deliverables in `research/control/WNBA-ODDS-DISCOVERY-PREP-V1/`: source
  matrix with per-source rights/PIT verdict and A/B/C class; per-season
  coverage table 2020–2026; sample-audit report; cost estimates for paid
  options; owner decision packet; successor backtest protocol DRAFT if any
  source reaches Class A.
- State explicitly whether the **≥300 valid game-quote gate** is met. If not:
  verdict `NOT_RUN_ODDS` or `NOT_RUN_INSUFFICIENT_COVERAGE` with the specific
  reason.
- HARD STOP before: purchasing data, PnL/scored runs, typed GO, account
  creation, paid-credit spend. No outcome-driven selection of source, anchor,
  bookmaker, or policy.
- Independent fresh-context verifier re-measures load-bearing claims from
  bytes and primary docs; report PASS/FAIL/NOT_RUN, findings, HEAD, registry,
  locks, actual spend ($0 target), and owner decisions required.
- Never: push, merge to main, S1 access, writes to ZCode internal DBs,
  credentials in chat/log/git, `git add -A`.
