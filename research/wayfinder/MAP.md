# Wayfinder map: evidence-led profitability research for my-quantitative

## Sprint state (synced by the Lead, 2026-09-08 morning)

- **CRYPTO V16 CLOSED → `V16_REJECT_ALL`** (closed 2026-09-08 07:45 VN,
  branch `orca/v16-integration`, terminal `46db31d` + canonical close
  `9d62d5c`) — the first aggTrades tick cycle and the first
  governance-native cycle (gate + lock + registry adopted and exercised
  end-to-end; per-period series persisted; two-key arc incl. a
  form-refused GO attempt correctly rejected). CLOSE-DISPLACE-FADE dies
  G2 PF razor (−0.0364) — plain negative; RUNPERSIST dies G1 with the
  control out-earning (corroborating shadow). D2 measured vetoes: 3
  proposals rho-blocked (0.2225/0.3385/0.3885); run_imb razor 0.1927.
  Budget 6/6; reproduction ALL_MATCH 60/60/1854; DSR NOT_RUN fail-closed
  for historical trials (prior Sharpes never persisted — prospective
  P-11 contract now in force). **aggTrades frontier measured-exhausted
  at the DAILY clock on BTC/ETH; sub-daily is the untested axis.**
  Crypto 155/158. Detail:
  `.worktrees/crypto/v16/integration/research/control/v16_run/terminal_report_v16.json`.

- **Program totals after all three closes (ledger authority, P-9):
  233 published / 236 observed, 0 survivors, S1 SEALED everywhere**
  (crypto 155/158, stocks 39/39, forex 39/39). Failure registry 55
  entries --verify PASS. No cycle is currently running; V17 (crypto),
  V12 (stocks) and V8 (forex) plans await owner dispatch.

- **FOREX V7 CLOSED → `FOREX_FREE_V7_REJECT_ALL`** (closed 2026-09-07
  20:32 VN, branch `orca/forex-free-v7-integration`, terminal `f59ea0c` +
  closeout `efb9601`) — the cross-economy spillover cycle. Both families
  mechanically negative AND control-killed: FXFV7-A4-P1 anchor −4.026/trade
  (PF 0.9088) with **falsification-by-control #12 — the +7d sham reproduces
  the anchor once the reaction window is closed before entry (F-A7-PL-1
  remediation): cross-economy conditioning carries no incremental
  information; together with V6 (own-economy, sham-NEGATIVE) the whole
  reaction-direction class is closed**. FXFV7-A6-P2 lead-lag −8.410/trade
  with the own-lag control out-earning the anchor (negative information).
  Budget 6/6; reproduction whole-file byte-identical (twin @ea905c8, ledger
  sha 1a82118b…); **first forex DSR from persisted per-period series
  (N=39, all ~0; P-11 gate delivering)**; A7 prelaunch arc R1 REFUSED
  (CRITICAL lookahead) → R3 AUTHORIZED → owner fresh GO; heavy lock waited
  out the V16 extraction (90 attempts). Forex 39/39. Detail:
  `.worktrees/forex-free-v7/integration/research/control/forex_free_v7_run/terminal_verdict_v7.json`.

- **STOCKS V11 CLOSED → `STOCKS_FREE_V11_REJECT_ALL`** (closed 2026-09-07
  22:49 VN, branch `orca/stocks-free-v11-integration@9d3a061`) — the
  filing-event/amendment-process cycle. The MANDATORY filing-event lane
  died measured at D2 (novelty 0.219/0.2192 vs momentum_63s); the single
  scored family SFV11-A5-H1 (amendment cadence-latency book)
  FALSIFIED_BY_CONTROL — anchor fails 7 gates and the shuffled-chain
  control reproduces its alpha 1.2042x same sign (**cluster #13**:
  cadence-latency spread is an exposure-shape artifact, not process
  information). A7 terminal CONFIRM 10/10 from bytes (0 HIGH/CRITICAL);
  reproduction ALL_MATCH byte-equal both files (twin @aac07d9); budget 3/6,
  3 slots dead forever; two-key arc incl. an A7 v1 REFUSED on an undisclosed
  push (INC-V11-4, resolved disclosed-owner-directed). Stocks 39/39. Detail:
  `.worktrees/stocks-free-v11/integration/research/control/stocks_free_v11_run/terminal_report.json`.

- **Program totals after the 2026-09-07 evening closes (superseded same
  night by V16): 227 published / 230 observed** — see the current totals
  above.

- **FOREX V6 CLOSED → `FOREX_FREE_V6_REJECT_ALL`** (closed 2026-09-07,
  branch `orca/forex-free-v6-integration@4d81dcd`) — the direction-conditioned
  calendar cycle. FXFV6-A4-P1 own-economy CPI reaction-direction drift is
  **the forex season's near-miss**: anchor fin-adj +824.37 @tier2.0
  (+0.963/trade, 208 trades) dying on FOUR robustness gates — PF margin
  −0.0021 (razor per P-2), GBPUSD concentration 0.4257, break-even 3.475bps,
  LOPO 3/4; k=10 neighbour out-earned (+1922.02, PF 1.1142) failing its own
  gates. **Sham control NEGATIVE (−910.40) while the anchor EARNS — release-
  DIRECTION conditioning carries genuine calendar information; V5's
  sham-shadow is counter-evidenced** (no falsification kill). FXFV6-A6-P2
  USD PC1-gated reversal mechanically dead (−3.299/trade; neighbour + placebo
  worse). Budget 6/6; reproduction whole-file byte-identical (twin @8a0fd01,
  ledger sha 8517ca36…); two-key P-8 legal. **A7 terminal NOT_RUN at close (disclosed in the ledger row) — ADDENDUM
  same day: it has since RUN → `CONFIRM_FOREX_FREE_V6_REJECT_ALL`
  (`0dead47`, 0 blocking, A7's own worktree re-run byte-identical; kernel debt
  F-A7-T-1 carried as owner item).** Forex 33/33; program 218/221 (ledger authority, P-9). S1
  sealed. Detail:
  `.worktrees/forex-free-v6/integration/research/control/forex_free_v6_run/terminal_verdict.json`.

- **CRYPTO V15 CLOSED → `V15_REJECT_ALL`** (closed 2026-09-07, branch
  `orca/v15-integration`, closeout `ad61fca` + terminal-line merge; code
  freeze `824190c`) — the archived-positioning-metrics cycle on
  data.binance.vision bulk daily metrics (keyless, sha256-pinned; staging
  PASS_UNDER_AMENDMENT_1: 4 global defect dates, ONG/ACE hole-heavy). 6/6
  cells published, 0 TECHABORT, reproduction ALL_MATCH 61,633 leaves. Both
  anchors fail rule order #1: ELITE-SIZE-ASYM −0.00173/day PF 0.897 with
  **falsification-by-control instance #11** (CTL-ELITELEVEL +0.00196
  PF 1.131 — asymmetry carries negative information vs plain elite level);
  TAKER-SAT −0.00380/day PF 0.842, control does not reproduce. A4's OI-axis
  pair novelty-blocked pre-score (rho 0.431 vs CTL-OISHARE, 0.253 vs
  OICYC-STOCH28 — the closed shadow measured). DSR/PBO NOT_RUN fail-closed
  (no per-period series persisted — driver-contract lesson for future
  cycles). Two-key P-8 proven again: fresh-context A7 REFUSED prelaunch on
  Q-LEAK_1 (fold-sign leak in q v1) → sanitized v2 + incident, exposure
  carried → AUTHORIZED → owner exact GO. The bulk-metrics frontier is
  measured-exhausted on this universe/window/cost regime pending an owner
  data decision. Crypto 149/152; program 212/215 (ledger authority, P-9).
  S1 sealed. Detail:
  `.worktrees/crypto/v15/integration/research/control/v15_run/terminal_report_v15.json`.

- **STOCKS V10 CLOSED → `STOCKS_FREE_V10_REJECT_ALL`** (closed 2026-09-06,
  branch `orca/stocks-free-v10-integration@bec559c`) — the filing-timing/
  revision cycle on the death-inclusive panel. Both families mechanical-REJECT:
  SFV10-A4-H1 own_z timing carries real directional content (raw-lag control
  opposite-sign; cohort_z neighbour same-sign) but dies PF margin −0.019 /
  ETF-share 0.8333 / SPY-excess 0/3 — sector-book drowning of a sub-cost
  signal (P-2 knife-edge class); SFV10-A5-H1 revision direction dead (−0.2047)
  with the severity neighbour equally dead → the revision axis is mined out.
  A7 terminal CONFIRM 8/8 (0 HIGH/CRITICAL); reproduction ALL_MATCH (twin
  @5b40d48, single by-design provenance leaf, INC-V10-1 adjudicated
  outcome-neutral); two-key P-8 proven end-to-end (A7 v1 REFUSED →
  remediation afad4b1 → v2 AUTHORIZED → owner exact GO). Budget 6/6; stocks
  36/36; program 206/209 (ledger authority, P-9). S1 sealed. Detail:
  `.worktrees/stocks-free-v10/integration/research/control/stocks_free_v10_run/terminal_report.json`.

- **FOREX V5 CLOSED → `FOREX_FREE_V5_REJECT_ALL`** (closed 2026-09-06, branch
  `orca/forex-free-v5-integration@3e8cacf`, terminal head 61100aa) — the
  inflation/real-rate axis cycle. P0 funded the per-print CPI axis on 4/8
  economies (GB 88 / CA 105 / AU 23 / NZ 30 evidenced in-S0 clocks; US OUT
  via archived BLS anti-bot 403 — owner hand-provision remains open; EMU/CH/
  JP release TIMING unevidenced) and closed the ALFRED vintage axis
  BLOCKED_DATA_AUTHORITY this host (license text unreachable — fail-closed;
  owner unblock options: FRED API key or alternate network path). P0c
  extended the announcement ledger 220→250 (cf1f01a7; CA 20/22, EMU 10/19
  via BoC/ECB PR bytes) and surfaced 9 EMU value-integrity findings —
  suspected MRO/DFR series mixing in the pinned base ledger, rows left
  UNEVIDENCED (owner debt, values never edited). D2 measured kills:
  A6-P2 ancestry rho 0.3257>0.20 (packet-consented); A4-P2 fold-infeasible;
  selection = FXFV5-A6-P1 alone. Scored REJECT: anchor FAIL 8 gates
  (gross-of-cost expectancy +0.712 only), sham-calendar neighbour
  out-earned the anchor (+2.744 vs −2.608) and died at the frozen primary
  stress gate (PF margin +0.0468 — falsification-by-control instance #10).
  Reproduction twin byte-identical whole-file; budget 3/3; two-key P-8
  re-proven. Denominators forex 27/27 (ledger: program 200/203 post-V5).
  S1 sealed. Detail:
  `.worktrees/forex-free-v5/integration/research/control/forex_free_v5_run/terminal_verdict.json`.

- **STOCKS V9 CLOSED → `STOCKS_FREE_V9_REJECT_ALL`** (synced by Lead,
  2026-09-06, branch `orca/stocks-free-v9-integration@3a61638`) — first
  cycle on the death-inclusive universe (evidenced Form-15 census,
  accession-union 3,395; dead-filer fundamentals extension; EODHD dead-name
  pulls — the probe-proven delisted capability finally exercised). Single
  eligible family SFV9-A4-H2 depletion-runway REJECT (PF 0.8095; control
  Cash/Assets opposite-sign weak-positive — informative shadow recorded,
  not rescuable); 5/6 proposals novelty-blocked vs the V8 shadow inventory;
  A1 refused post-hoc pooling re-adjudication. Budget 3/6; stocks 30/30;
  S1 sealed. Detail:
  `.worktrees/stocks-free-v9/integration/research/control/stocks_free_v9_run/terminal_report.json`.
- **CRYPTO V14 CLOSED → `V14_REJECT_ALL`** (2026-09-05, branch
  `orca/v14-integration@183554a`) — A7 terminal APPROVED 0_FAIL; reproduction
  ALL_MATCH at 874,334 leaf comparisons. PREMFADE-28D the near-miss of the
  cycle: +0.700 net, PF 1.360, MDD 11.6%, rejected on fold concentration
  0.5110 > 0.50 (marginal gate's third decisive kill). OICYC §1.1
  confirmatory entry closed with status bound in every cell (no exploratory
  recounting). First program DSR computed (0.00224 / 4.98e-07 over N=146 —
  effectively zero); PBO NOT_RUN fail-closed (<8 configs). Crypto 143/146.
  Detail: `.worktrees/crypto/v14/integration/research/control/v14_run/terminal_report_v14.json`.
- **FOREX V4 CLOSED → `FOREX_FREE_V4_REJECT_ALL`** (2026-09-05, branch
  `orca/forex-free-v4-integration@edba9bf`) — A7 terminal CONFIRM 8/8 from
  bytes; 6/6 cells, zero TECHABORT, twin ledger pinned 65725edc.
  Commodity-bloc risk-off whisper-positive (PF 1.0142, +0.675/trade) failing
  every robustness bar; family2 negative. Carry front door CLOSED at D2 by
  measured rho 0.997–1.000 vs both invalidated-ancestor variants. Two-key
  launch protocol proven in production (frozen phrase gate refused the
  19:48 shorthand; fresh exact-phrase GO 19:53). Inflation-axis classes
  DATA_BLOCKED_VALID → carried into PLAN_forex_v5.md. Forex 24/24.
- **STOCKS V8 CLOSED → `STOCKS_FREE_V8_REJECT_ALL`** (2026-09-05, branch
  `orca/stocks-free-v8-integration@9557f59`) — first cycle on the
  owner-entitled EODHD source (probe 6/6 PASS incl. delisted canaries);
  both families FALSIFIED_BY_CONTROL (cluster instances #8/#9); cohort
  honesty M-I1 honored (no delisted leg claimed). Stocks 27/27.
- Program totals after all four closes (ledger authority, P-9): **197
  published / 200 observed, 0 survivors, S1 SEALED everywhere** (crypto
  143/146, stocks 30/30, forex 24/24).

- **FOREX V3 CLOSED → V3R DATA_AUTHORITY_INVALIDATED** (synced by A1,
  2026-09-05, branch `orca/forex-free-v3r-integration@c356813`) — V3 locked
  FXFV3-A6-P1 (vol-gated policy-rate carry) provisionally pending evidenced
  PIT availability; the V3R remediation recomputed the six frozen cells
  under a pinned official announcement ledger (G4 twin ALL_MATCH; A7 PASS
  9/9, 0 blocking): anchor fails frozen STRESS_TIER_2.0 (PF 1.2825 fin-adj,
  expectancy +20.72 under honest availability), control arm refused by the
  frozen validator (mechanism sanity null). Verdict
  `FOREX_FREE_V3_DATA_AUTHORITY_INVALIDATED`; family2 in the forbidden
  inventory (economic observation recorded; front-door re-entry only via a
  future preregistered plan, standard ancestry rho gates). S1 never opened,
  stays SEALED. Denominators unchanged (forex 18/18; V3R published
  nothing). Detail:
  `.worktrees/forex-free-v3r/integration/research/control/forex_free_v3r_run/terminal_verdict.json`,
  S-1 entry in [SURVIVORS.md](SURVIVORS.md).

- **FOREX TERMINAL `FOREX_BLOCKED_SELECTION_INSUFFICIENT`** (synced by A1,
  2026-09-03, branch `forex@af707e3` + terminal closeout commit) — G10 spot-FX
  sprint closed honestly: F0 consumed the owner-authorized multi-asset core
  `8310366` (F0 PASS, 78 tests), F1 correctness engineering complete
  (FX0–FX6 PASS, 118-test forex suite; provider/instruments/loader/audit,
  sessions/DST/rollover clocks, conversion/rollover/accounting/execution,
  all synthetic-golden), F2 produced six outcome-blind proposals (pool
  `4b9ee91`) and A7 audited them 0 ELIGIBLE / 5 CONDITIONAL_ON_OWNER_DATA /
  1 INELIGIBLE. F3 never opened: no FX data authority exists (bid/ask 0/7
  pairs, rollover/swap, PIT rates all UNAVAILABLE_FAIL_CLOSED; owner did not
  authorize any provider). Scored cells 0, budget 0/6, denominators 0/0,
  S1 SEALED_UNTOUCHED, workers 0. The five conditional proposals are frozen
  future inputs; re-grading only after concrete data authority, outcome-blind.
  Evidence: `research/control/forex_run/terminal_report.json`,
  `research/audits/forex/f2_novelty/a7_f2_novelty_audit.json`.

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
