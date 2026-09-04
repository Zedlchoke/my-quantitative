# Wayfinder map: evidence-led profitability research for my-quantitative

## Sprint state (synced by A2, 2026-08-25, branch orca/v7-a2-closure)

- **STOCKS-FREE-V5 TERMINAL** (synced by A1, 2026-09-04, branch
  `orca/stocks-free-v5-integration`) — verdict
  `STOCKS_FREE_V5_REJECT_ALL` (terminal A7
  `STOCKS_FREE_V5_REJECT_ALL_CONFIRMED`, audit head `bc5827e`): Data Fusion
  V1 core adopted pre-freeze (c6a0576 byte-identical; pit_conditioning.py
  canonical bridge per owner adjudication after a two-controller concurrency
  incident). Six outcome-blind proposals (4 PIT-conditioned): A7-N eligible
  1/6; A9-F killed all four SEC-conditioned proposals pre-selection (F1
  single-vintage coverage collapse — future-plan candidate, unremediated);
  the Section 1.1 vol-level confirmatory was measured-ineligible (shape gate
  0.319 > 0.20). Selected family SFV5-A6-H2-CROSS-SECTOR-COUPLING × 3 arms
  scored at `STOCKS_FREE_V5_W1=0ecca232` (driver be0e4fa4): anchor fails
  10/15 Stage-A gates and the nominal-price placebo outperforms the anchor
  on the identifying metric (alpha 0.0252 vs 0.0077) — preregistered
  falsification fires. Budget 3/6 (3 slots unused forever), V5
  observed=published=3, reproduction 3/3 EXACT_MATCH, denominator 21.
  Detail: `research/control/stocks_free_v5_run/terminal_report.json`,
  `research/audits/stocks_free_v5/r_a7_terminal_audit.json`.

- **STOCKS-FREE-V3 TERMINAL** (synced by A1, 2026-09-03, branch
  `orca/stocks-free-v3-integration`) — verdict
  `STOCKS_FREE_V3_REJECT_ALL` (terminal A7
  `STOCKS_FREE_V3_REJECT_ALL_CONFIRMED`, commit `ad897c8`): two blind-
  selected families × 3 frozen arms scored on reused S0 at
  `STOCKS_FREE_V3_W1=586f9fe`; budget 6/6, V3 observed=published=6,
  reproduction 6/6 EXACT_MATCH. `SFV3-A5-IDIO-SHOCK-REVERSAL` REJECT
  (anchor −20.6% pnl, PF 0.43, alpha −0.25 — neither idio-crash nor
  idio-overshoot reverts net of costs). `SFV3-A6-TOM-SETTLE` REJECT
  (anchor +38.5% raw pnl / PF 1.62 BUT incremental alpha −0.13 vs
  risk-matched SPY and the mid-month placebo control fails falsification:
  the raw PnL is scaled sector beta, not a calendar premium; PLAN §16 bars
  raw PnL from overriding failed beta gates). Zero survivors; nothing
  locked for S1; S1 sealed; statistical denominator now 12. Terminal A7
  incident A7T-B1 (ledger wrapper digests) remediated append-only and
  re-verified. Detail:
  `research/control/stocks_free_v3_run/terminal_report.json`.

- **STOCKS-FREE-V2 TERMINAL — V2R RECONCILED** (synced by A1, 2026-09-03,
  branch `orca/stocks-free-v2-integration`, reconciliation branch
  `orca/stocks-free-v2r-integration`) — effective verdict
  `STOCKS_FREE_V1_REJECT_ALL` (terminal A7 confirmed): Twelve Data Basic
  USD 0 authorized by owner; 11-ETF SPDR cohort; six scored S0 cells
  (budget 6/6, observed=published=6), reproduction 6/6 EXACT_MATCH.
  Canonical `STOCKS_FREE_W1=106378230abecbaefff4248eeb373794f1b73038`
  (stale `5046a87…` state reference superseded; FD2 re-audit-pending suffix
  superseded). A4 momentum-family REJECT (control reproduced the mechanism:
  bottom-3 expectancy 96.5% of top-3 — sector beta dominates; MDD 30.4%
  fail). A5 trend/defensive REJECT (MDD 23.2%, drop-one-ETF negative,
  fold-share fail; concentration passes at 25%). Zero survivors; S1 sealed;
  workers zero. Detail:
  `research/control/stocks_free_v2_run/terminal_effective_verdict.json`
  and `research/control/stocks_free_v2_run/terminal_report.json`.

- **STOCKS-FREE-V1 TERMINAL** (synced by A1, 2026-09-03, branch
  `orca/stocks-free-v1-integration`) — verdict
  `STOCKS_FREE_V1_BLOCKED_FREE_DATA_AUTHORITY` (A7 CONFIRM_BLOCKED): zero-cost
  no-account ETF daily-OHLCV stack impossible — stooq anti-bot wall, SSGA
  embedded license adverse, issuers publish close/NAV only; budget 0/6,
  counters 0/0, old paid-data families untouched. Detail:
  `research/control/stocks_free_v1_run/terminal_report.json`.

- **STOCKS SPRINT TERMINAL AT S3** (synced by A1, 2026-09-02, branch
  `stocks@4521cf6`) — verdict `STOCKS_BLOCKED_DATA_AUTHORITY`: M0 multi-asset
  core frozen (`MULTIASSET_CORE_SHA=8310366`, M0_PASS 78/78), S1 correctness
  lanes integrated (SD0–SD6 PASS, full stock suite 209 passed), six
  outcome-blind proposals audited by A7 (6/6 ELIGIBLE, zero HIGH/CRITICAL),
  selection frozen to `EQ_S2_A3_F1_PIT_RECON_FLOW` +
  `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM` (budget 0/6, counters 0/0). Scored
  cells computed: 0. S1: sealed and untouched. Owned workers: 0. Next
  authorized action: owner acquires/approves PIT data authority, then
  S4 -> S5 -> S6. Detail:
  `research/control/stocks_run/terminal_report.json`.

- **V10P BLOCKED_PRELAUNCH** (synced by A1, 2026-08-27, branch
  `orca/v10-integration@86b7274`) — generic strategy→research adapter built and
  accepted (BG1–BG6, G15, F2 adopted-with-proof, G17 one measured authority,
  H08 12–20), family `A8-V10-M01-AGGRESSOR-ABSORPTION-PANEL` frozen with 0/3
  scored cells consumed, W2=`d61a483` with detached R1b/R2b and 47/47 verified
  staged data. A7 prelaunch `NO_GO_BLOCKED_PRELAUNCH`: HIGH
  `G05_COVERAGE_SHORTFALL` (staged bars end 21.5 h before the preregistered
  window end; final daily close silently synthesized) + launch-window and
  measured-cap (final_cap=0) blockers. Entry conditions for the next thread:
  [CONTINUE.md](../../CONTINUE.md). Detail:
  `research/control/v10p_run/terminal_closeout_v10p.json`,
  `research/audits/v10p/a7_prelaunch_v10p.json`.
- **V9 REJECTED** — `V9_REJECT_ALL_MULTI_FAMILY` (5/5 frozen trials, all
  reproduced, terminal at `425843d`); V9H hardening
  `V9H_PASS_V10_AUTHORIZED` (14/14, `3241bd0`). Denominator 117.
- **V6P PASS** — engine/data/PIT/accounting validation sprint: 20/20 gates,
  A7 independent audit PASS (0 unresolved HIGH/CRITICAL), verdict
  `V6P_PASS_V6_AUTHORIZED`.
- **V6 REJECTED (family)** — `V6P_PASS_V6_CANDIDATE_FAIL`, 4/4 scored trials
  consumed, 0 candidates locked. Per-trial: CARRY-1D −5,679.96 PF 0.978
  mechanism_failure; CARRY-3D +2,076.03 PF 1.0116 edge_too_weak; CARRY-7D
  +20,580.87 PF 1.157 rejected on top-positive-fold concentration 51.66%>50%
  (MDD actually 8.84% PASS); REVERSE-3D −20,102.83 failed as designed
  (negative control). Terminal HEAD at closure `fbd2e9d` (clean tree).
  Authoritative detail + checksums:
  [v6-closure-addendum-20260825.md](evidence/v6-closure-addendum-20260825.md).
- **V7 PENDING** — 0/4 preregistered trials (`XSECT-FUND-PRICE-DIV-1D/3D/7D`
  normal + `REV-3D` reverse control) run or authorized. Status is strictly
  NOT_RUN / NOT_AUTHORIZED. Launch requires the V7P decision-surface repair
  and 18/18 prelaunch gates including A7 attestation (PLAN.md §7). Sprint V7P
  runs from bootstrap `dd026c0` across worktrees A2–A7.
- **S1 UNTOUCHED** — holdout never opened, observed, backfilled or analyzed;
  no paper/live trading; live money UNCHANGED_DISABLED.

## Destination

Produce a frozen, reproducible multi-asset research specification that is
credible enough for controlled signal-only/very-small testnet forward testing:
strategy rules, data contract, cost model, portfolio limits, and explicit
promotion/rejection evidence. Profitability is a hypothesis to test, not a
promise.

## Notes

- Domain: Binance USD-M perpetuals, ETH/BTC, liquid altcoins, and Binance TradFi
  perpetuals.
- Existing stack: NautilusTrader 1.230.0, 15-minute bars, funding/OI/mark-price
  data, shared risk manager, post-trade funding audit.
- Standing rules: no parameter tuning after seeing a fold; no forced transfer;
  no live-money execution; fail closed on incomplete data; preserve rejected
  symbols and negative results.
- Canonical repo notes: `NOTES.md` sections 13–16.
- Tracker: local Markdown because no issue tracker/connector is configured.

## Decisions so far

- [Current evidence baseline](tickets/current-evidence-baseline.md): ETH is the
  only candidate with a weak but repeatable signal; the three new baselines fail
  the shared-capital altcoin gate.
- [Funding is an accounting cost first](tickets/funding-accounting.md): funding
  is audited post-trade today; native intrarun settlement is required before
  margin-sensitive promotion.
- [Profitability gate and benchmark contract](tickets/define-profitability-gate.md):
  two-stage frozen screen/promotion gate; flat is the hard benchmark, while
  buy-and-hold and BTC-beta-neutral alpha are mandatory context checks. Every
  gate uses canonical after-cost PnL plus shared-capital replay.
- [Verify the next data snapshot and split contract](tickets/verify-data-snapshot.md):
  S0 is a clean one-year common crypto screen, but not untouched OOS; promotion
  requires a post-lock S1. The seven-symbol derivative overlay is now complete
  for S0 with a manifest and deterministic bar join.
- [Capture the missing ETH derivatives snapshot](tickets/capture-eth-derivatives-snapshot.md):
  ETH now has 90 funding, 2,880 OI and 2,880 mark rows in the same requested
  30-day interval as the altcoins; one trailing overlay row is excluded.

## Not yet specified

- Which asset-class buckets deserve separate frozen rules after the next data
  snapshot.
- The exact TradFi session/holiday/earnings data contract and whether its history
  is long enough for a credible out-of-sample test.

## Out of scope

- Live-money trading, automatic multi-strategy switching, leverage increases,
  and parameter grids in this map.
- Claiming a backtest is profitable without fees, slippage, funding and a
  portfolio-level test.
- Replacing the existing global default strategy before a separate promotion
  decision is closed.

## Frontier tickets

- [Capture the untouched future holdout](tickets/capture-untouched-holdout.md)
- [Decide the crowding and native-funding feature contract](tickets/crowding-funding-contract.md)

## Blocked tickets

- [Choose the ETH forward-test candidate](tickets/choose-eth-candidate.md) — blocked by the future holdout and crowding/funding contract.
- [Choose altcoin asset-class candidates](tickets/choose-altcoin-candidates.md) — blocked by the future holdout and crowding/funding contract.
- [Define the TradFi perpetual research contract](tickets/tradfi-research-contract.md) — blocked by the future holdout.
- [Set shared-capital and portfolio promotion rules](tickets/portfolio-promotion-gate.md) — blocked by candidate decisions.
- [Approve the controlled forward-test handoff](tickets/forward-test-handoff.md) — blocked by portfolio and execution decisions.
