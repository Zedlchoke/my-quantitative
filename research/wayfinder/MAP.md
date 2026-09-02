# Wayfinder map: evidence-led profitability research for my-quantitative

## Sprint state (synced by A2, 2026-08-25, branch orca/v7-a2-closure)

- **STOCKS SPRINT TERMINAL** (synced by A1, 2026-09-02, branch
  `stocks@4521cf6`) — verdict `STOCKS_BLOCKED_DATA_AUTHORITY`: M0 multi-asset
  core frozen (`MULTIASSET_CORE_SHA=8310366`, M0_PASS 78/78), S1 correctness
  lanes integrated (SD0–SD6 PASS, full stock suite 209 passed), six
  outcome-blind proposals audited by A7 (6/6 ELIGIBLE, zero HIGH/CRITICAL),
  selection frozen to `EQ_S2_A3_F1_PIT_RECON_FLOW` +
  `A5-S2-F1-LENDING-CONSTRAINT-PREMIUM` (budget 0/6, counters 0/0). Scored
  research blocked: no PIT provider entitlement. Detail:
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
