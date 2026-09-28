# PLAN — DAYTRADER-100-V1 (daytrader strategy census + bounded first cohort)

- cycle_id: `DAYTRADER-100-V1`
- asset: `shared` (census spans futures/forex/crypto; scored cohort is crypto-only)
- plan: `plans/PLAN_daytrader_100_v1.md` (this file)
- branch: `orca/daytrader-100-v1-integration` (worktree created at implementation wave)
- registered: 2026-09-28, base `aa954939af9994731be2efaf173f9dde719c47cb` (root main, owner tree preserved)
- budget: **0/3 scored cells** (GO authorizes at most 3: 1 anchor + 2 neighbours of ONE family; controls/baselines/placebos are re-evaluations and consume zero cells)
- GO phrase (registered, NOT consumed; typed only at this cycle's own gate per P-8):
  `GO DAYTRADER 100 V1 SCORED EXECUTION`
- S1: `SEALED_UNTOUCHED` — nothing in this plan opens it.

## 1. Objective

Owner instruction 2026-09-28: take a 100-strategy day-trader brainstorm (futures/forex/crypto)
and, for each strategy, define arms (1 anchor + 2 neighbours + 1 control), implement into the
system, and run scored cells, reporting calendar-dated windows, analysis and reliability.

This plan executes that instruction under program law. The governing measured facts at
registration (evidence: `research/wayfinder/HYPOTHESIS_LEDGER.md`, `FAMILY_FAILURES.jsonl`
139-140 rows, data census 2026-09-28):

1. **Ancestry**: ~400 observed scored cells program-wide, 0 survivors. The mechanism classes
   underlying most of the 100 (trend/momentum, intraday mean-reversion/range-fade,
   session/clock, event/announcement-clock, funding carry/basis, positioning/OI, orderflow,
   lead-lag, regime routers, vol-level sortings, folklore playbooks) each carry dated kills.
   Re-scoring them unchanged is ancestry-rescue — forbidden by the ledger header law and
   §14.3 without a preregistered measured decorrelation (pooled |rho| <= 0.20 vs named dead
   shadows, immovable bar).
2. **Data**: the only multi-year authorized intraday substrates are Binance USD(S)-M keyless
   Vision panels (BTCUSDT/SOLUSDT 1m 2020-09..2026-08; 1h majors; 8h funding; mark/index) and
   Dukascopy M1 bid/ask for EURUSD/GBPUSD/USDJPY 2021-01..2026-09 (owner-authorized,
   TCU-disclosed) — the latter with NO citable cost/financing band (measured BLOCKED twice:
   FOREX-NG6/NG7 F4, 2026-09-16). CME/equity/index/rates intraday, options chains, L2 books,
   on-chain, liquidation and OI history: 0 bytes or transport/license-blocked (dated in the
   census matrix).

Therefore the cycle has two halves:

- **G1 census (this registration's deliverable, lands in root control dir)**: the
  100-strategy arm matrix with a per-strategy verdict — `RUNNABLE_COHORT1`,
  `ANCESTRY_VETOED` (prior kill + date), `BLOCKED_DATA/_TRANSPORT/_COST/_LICENSE`
  (blocker + date). Census is bookkeeping on already-measured evidence; it computes no PnL.
- **Cohort-1 scored execution (gated)**: the single never-tried family the ledger itself
  names with a resolved data gap — **crypto forecast-funding (premiumIndex intraday)**.
  Ledger verbatim: "the PS1 probe (DATA-FOUNDATION-V1) measured premiumIndexKlines available
  keyless, resolving the forecast-funding data gap; no forecast-funding family has ever been
  proposed." Every other candidate is either ancestry-vetoed or substrate-blocked.

## 2. Law conformance (binding)

- Two-key launch: A7 prelaunch AUTHORIZED (0 unresolved HIGH/CRITICAL) THEN owner GO typed
  verbatim at this cycle's own gate. Early GO = intent, dies unconsumed (P-8).
- Ancestry rho bar **0.20 immovable**, measured per-leg AND pooled on the frozen
  representation vs named dead shadows (funding-level windows, CARRY, BASISLV, FUNDJUMP,
  PWS run-regimes). pooled-only = NOT_RUN.
- Q-11: each control must be a valid null that MOVES the signal; distinguish kill vs inert null.
- Q-7: clock-only shadow for any session/calendar conditioning.
- P-18/F-PIT-1: three-laws seam measurement (scored panel vs PIT-clean re-spec vs growing
  panel) before any number is trusted; holdout does not substitute truncation proof.
- Q-8: costs measured from bytes (funding 8h bit-exact; taker ladder), never vendor-stated.
- Controls are re-evaluations: zero scored cells, zero denominator.
- Heavy lock for all scored compute; `NOT_RUN_RESOURCE_CONFLICT` if held.

## 3. Cohort-1 family definition (frozen at G3 before any measurement)

- family_id: `DT100-C1-FORECASTFUND`
- hypothesis: the 1m premium index (premiumIndexKlines, keyless, PIT-verified corpus
  2020-09..2026-08) leads the 8h funding settlement mark; an intraday book conditioned on
  premium-index state — NOT on funding level, NOT on realized funding — carries information
  the closed funding-level classes did not consume. Mechanism: marking-flow pressure ahead
  of settlement, observable pre-settlement only.
- universe: BTCUSDT + SOLUSDT USD(S)-M perps (the two 1m-sha-pinned corpora in-tree).
- clock: 1m bars, decisions on 15m boundaries; flat before settlement lock window.
- ANCHOR: premium-index z-score (rolling 24h) beyond +1.5 / -1.5 sigma entering the 4h
  pre-settlement window, faded toward the index leg, exit at settlement or band re-entry.
- N1 (faster): z window 12h, band 1.75.
- N2 (slower): z window 48h, band 1.25.
- CTRL (re-evaluations, zero cells): (a) settlement-clock shadow — same pre-settlement
  windows, premium signal removed (Q-7; this is the shadow class that killed RATES/COMMODITIES);
  (b) funding-level shadow — the dead CARRY observable run on identical windows (if it
  reproduces the anchor, F-0 variant-same-family fires); (c) sign-flip; (d) stale-z placebo
  (z shifted 24h). 
- falsification rule: anchor net expectancy <= 0 at measured cost, OR rho vs any dead
  funding shadow > 0.20 pooled, OR clock shadow reproduces anchor within noise => identity
  dies. No threshold rescue after scored PnL is visible.

### 3.1 Fold windows (explicit calendar dates; frozen)

Substrate window 2020-09-01 .. 2026-08-31 (Binance Vision, all-ms PIT-verified).

- Warmup (không ra quyết định): 2020-09-01 .. 2021-03-31
- Giai đoạn 1: 2021-04-01 .. 2022-06-30
- Giai đoạn 2: 2022-07-01 .. 2023-09-30
- Giai đoạn 3: 2023-10-01 .. 2024-12-31
- Giai đoạn 4: 2025-01-01 .. 2026-08-31

Force-flat at boundaries; no fold substitution after any PnL seen; majority-of-folds rule.

### 3.2 Floors and bars (borrowed verbatim from house G3)

- net expectancy > 0 at measured cost; PF >= 1.10 at x1.0; stress x1.5 reported, x2.0 always.
- >= 100 fired decisions per fold and >= 400 total, else NOT_RUN_THIN.
- fired-rate band [0.02, 0.10]; top-fold contribution <= 50%; single name <= 20% of book net.
- drop-one-symbol survival; weekday-share clock floor 0.35.
- PBO >= 8 configs else NOT_RUN; sub-power positives are INCONCLUSIVE, never PASS.

## 4. Census matrix (G1 artifact)

`research/control/DAYTRADER-100-V1/CENSUS_MATRIX_100.md` — 100 rows, each with arm sketch
(anchor/N1/N2/CTRL by category grammar), substrate requirement, verdict code, and dated
evidence pointer. Notional FX fold calendar for the blocked-FX rows (documented, NOT
scheduled): warmup 2021-01-01..2021-03-31; P1 2021-04-01..2022-06-30; P2 2022-07-01..
2023-09-30; P3 2023-10-01..2024-12-31; P4 2025-01-01..2026-09-23.

## 5. Gate sequence

```
G0 intake (done at registration: HEAD aa954939, lock FREE_PROVEN, owner tree preserved)
G1 census court     -> CENSUS_MATRIX_100.md (this cycle, root control dir)
G2 data authority   -> cohort-1 substrate re-verify (sha-pins, DST, funding bit-exactness)
G3 identity freeze  -> G3_FREEZE.md (arms, folds above, floors, digests)
G4 pre-PnL falsification -> PIT battery, panel-truncation replay, seam divergence (P-18)
G5 second implementation + byte-agreement twin
G6 cost ceiling     -> taker ladder + funding measured; x1.0/x1.5/x2.0
G7 A7 prelaunch     -> 0 HIGH/CRITICAL (two-key #1)
STOP owner packet   -> OWNER_PACKET.md with qualifying cells
G8 owner GO         -> auth/GO_RECORDED.json (two-key #2; phrase above, verbatim)
G9 scored S0        -> <=3 cells under heavy lock; per-cell identity report
G10 reproduction + terminal A7 + two-half close
```

## 6. Preregistered terminal outcomes (decided before results)

- `DAYTRADER_100_V1_CENSUS_ONLY_ZERO_FEASIBLE` — cohort-1 dies at G2-G4 (rho/seam/coverage);
  census stands as the answer to the owner question. Valid, done.
- `DAYTRADER_100_V1_REJECT_ALL` — cells run, no identity passes.
- `DAYTRADER_100_V1_THIN` — floors fire (NOT_RUN_THIN), no rescue.
- Survivor (if any) = Stage-A candidate only; S1 unseal is a separate owner gate.

## 7. Out of scope

Equity/CME/rates/options intraday and on-chain families (blocked, owner actions listed in
the census matrix); any relaxation of the 0.20 bar; any scoring without both keys.
