# JOURNAL_CENSUS_AND_RECONCILIATION — successor_design_2026-10-02

Scope: EVERY journal already on disk that the successor program inherits —
the 38 PC12A Stage-C arms and the 85 DAILY-EXPLORATORY-V1 journals. All
counts below are `[M]` from the committed files (machine census:
`analysis/census_and_complementarity.py` → `analysis/census.json`), except
where marked `[derived]`/`[NR]`. Nothing was re-scored.

Sources:
- `research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/*/` (38 arms × {journal.jsonl, metrics.json})
- `.worktrees/pc12a-daily-exploratory-prep/research/control/DAILY-EXPLORATORY-V1/battery/` (85 journals, 1,225 rows)

## 1. The dedup law (read before any count)

The 38 Stage-C arms contain at most **two portfolio-realized scored books**
(POLICY and B1_ALWAYS_ON at tier ×1.0) plus artifacts derived from the same
market decision streams:

| arm class | arms | what they are | counts as new trades? |
|---|---|---|---|
| primary scored | POLICY, B1_ALWAYS_ON | the two portfolio books, 12 legs, ×1.0 | YES (the only portfolio trades) |
| tier re-pricing | POLICY/B1 × {P90, X15, X20} | same corpus re-priced under cost multipliers: B1 family decision streams byte-identical (3,467); POLICY family varies slightly (3,124/3,126/3,114/3,110) because the L6 cost guard defers cost-dependently — measured difference, disclosed; no tier arm adds a NEW market decision stream | NO |
| portfolio controls | B2_EQUAL_WEIGHT, B3_BEST_SINGLE, B5_CLOCK_GATE, B6_INVERTED, B7_LAGGED, B8_ORACLE | control re-runs of the same market under different gating/sizing laws | NO (control evidence) |
| solo paper books | 24 × `*_MO_<leg>` | single-leg books, header `legs=[<leg>]` exactly — SOLO, not minus-one (correction #1 in session header) | NO (paper books; no netting) |

**Rule enforced everywhere below: nothing is summed across arms or tiers.**
Summing POLICY+B1+controls would double-count one market; the census counts
the market ONCE and then counts the arm-specific overlays separately.

## 2. Decision, fill and round-trip census (primary arms)

### 2.1 Row census `[M]`

| arm | DECISION rows | of which nonzero-vote | NET_ORDER fills | SWAP | BLOCK | DEFER | NETTED_TO_ZERO |
|---|---:|---:|---:|---:|---:|---:|---:|
| POLICY | 3,124 | 1,567 | 2,436 | 963 | 343 | 331 | 35 |
| B1_ALWAYS_ON | 3,467 | 1,757 | 2,363 | 1,096 | 0 | 296 | 101 |

- **Decision streams: POLICY ⊂ B1** (3,124 of 3,467 decision points shared;
  union = 3,467 corpus-unique leg-level decision points on the window)
  `[M]`. The policy's eligibility layers suppress decision-row emission
  itself for blocked legs — POLICY "missing" decisions are recoverable from
  B1's stream.
- Nonzero-vote decisions by leg (B1): S026 946 · S002(GBP) 245 · S014 144 ·
  S013 119 · S009 63 · S046 47 · S003(JPY) 47 · S002(JPY) 41 · S017 39 ·
  VC2-EUR 37 · VC2-JPY 21 · S023 8. The vote-carrying core is 4 legs
  (S026, GBP-S002, S014, S013 = 1,454 of 1,757 = 83%).

### 2.2 Fill matching (unique market trades) `[M]`

Matching key = (symbol, `ts_fill_utc`). A shared timestamp is ONE market
trade, possibly sized differently by the two books:

| quantity | value |
|---|---:|
| POLICY unique fill timestamps | 2,436 |
| B1 unique fill timestamps | 2,363 |
| **shared timestamps (= same market trade in both books)** | **2,001** |
| — of which identical size | 1,517 |
| — of which sized differently | 484 |
| POLICY-only fills (extra path trades) | 435 |
| B1-only fills (trades POLICY skipped/re-sized away) | 362 |
| **union: corpus-unique market fills in the window** | **2,798** |

The 2,001 shared trades are the same fills booked twice (once per arm); the
honest portfolio-trade denominators are **2,798 unique market fills** or,
per arm, that arm's own fill count — never a cross-arm sum.

### 2.3 Round trips (flat-to-flat / FIFO reconstructions) `[M, prior dockets]`

Round-trip reconstruction was done by the 2026-10-01 dockets with exact
reconciliation to journal nets and cost bills (cited):
- USDJPY: 703 excursions (POLICY 393 + B1 310); Σnet reconciles to journal
  symbol nets to the cent; friction equals metrics cost bill exactly
  (docket A §0).
- EURUSD: 182 (POLICY) + 250 (B1); GBPUSD: 273 + 284; per-fold sums match
  engine `per_symbol_fold_records` to ≤$1 on all 32 cells (docket B §Method).
- **Total reconstructed round trips across both primary books: 1,692.**

### 2.4 Outcome grouping law (breakeven defined BEFORE grouping)

The dockets' frozen convention (kept for the successor): per-pair median
round-trip cost `c` (USDJPY c=$239.54 journal units; EURUSD $3.35; GBPUSD
$2.12); WINNER net > +c, LOSER net < −c, BREAKEVEN otherwise. Breakeven =
fee-dominated band, not a free parameter; per-pair `c` re-measured on any
new calendar before grouping (never re-thresholded after seeing a
distribution).

## 3. Blocked / deferred / netted inventory (opportunities NOT taken)

### 3.1 POLICY journal rows `[M]`

| outcome | rows | detail |
|---|---:|---|
| BLOCKED_FLOOR (E1) | 343 | per-leg (journal recount, `analysis/census.json` `per_leg_inventory.POLICY`): S009 123 · VC2-EUR 44 · S002(JPY) 79 · S003 37 · S023 16 · VC2-JPY 22 · S017 22 |
| DEFERRED_COST_GUARD (L6) | 331 | S026 299 · S014 27 · VC2-JPY 4 · S003 1 |
| NETTED_TO_ZERO (L4 tie) | 35 | ties net to zero in both arms — $0 divergence (GATING_VS_SIZING §3) |

### 3.2 SUPERMAJORITY_BLOCK: metrics-only, per leg `[M]`

No journal rows in either arm (GATING_VS_SIZING §3). Per-leg counts from
`metrics.json → per_symbol.<sym>.legs.<leg>.fills_by_outcome` (B1):
S026 706 · S014 186 · S002(JPY) 55 · S003 20 · VC2-JPY 22 · S009/S013/…
(portfolio totals: POLICY 659 vs B1 1,021 histogram). This is the LARGEST
blocked channel and its PnL attribution is `[NR]` (closest proxy:
`pathdown_policy_sizing_netting` −$31,686 `[derived]`).

### 3.3 DAILY-EXPLORATORY-V1 journals `[M: battery §9]`

85 journals, 1,225 rows: **1,128 FILLED · 73 BLOCKED_STALE** (source-holiday
/panel-gap freshness) **· 24 BLOCKED_FLOOR** — all 24 floor rows are DS-05
folds 4&7; DS-03 folds 6&8 are typed NOT_RUN_THIN via ZERO fires in those
folds (no journal rows — absence typed by the floor law). Aggregate 61
decisions < 100 floor → `NOT_RUN_THIN_AGGREGATE`. Every arm net-negative at
every tier (SLATE −$1,088.08 ×1.0 → −$1,713.01 ×2.0); B0 FLAT dominates
(family failure DEV1-DAILY-EXPLORATORY-DS03-DS05, CLOSED).

## 4. Reconciliation checks performed (this session + inherited)

| check | result | source |
|---|---|---|
| Fold cash identity: Σ(fills−swaps) = cash_end−cash_start, 48 segments | worst $0.000001 | GATING_VS_SIZING V1 `[derived]` |
| Weekly nets vs metrics net_pnl | worst $0.000002 | GATING_VS_SIZING V2 |
| Known totals: USDJPY −87,201.39 / EURUSD +1,714.26 / GBPUSD +223.70 / pooled −85,263.43 | exact to cent | GATING_VS_SIZING V3 |
| Weekly component identity ΔW ≡ GATE+SIZE+PONLY+CARRY | max residual $0.0000 | GATING_VS_SIZING V4 |
| USDJPY excursion Σnet = journal symbol net; friction = cost bill; force-flats 4/5 tagged | exact | docket A §0 |
| EUR/GBP per-fold reconstruction vs engine records, 32 cells | ≤ $1 | docket B §Method |
| DAILY: 85 journals hash-chain verified; quote-CCY identity to 1e-9; 1,128+73+24 = 1,225 rows | PASS | battery §9, A7 terminal |
| Tier arms: metrics n_decisions_total 3,411 identical across all 12-leg arms; B1 family journal decisions identical (3,467); POLICY family 3,124/3,126/3,114/3,110 (cost-guard defer variation, disclosed) | verified this session + skeptic recount | census.json |

## 5. What this census establishes (and does not)

- The successor's honest sample base on the M1 pairs, **per portfolio book**:
  POLICY 393+182+273 = 848 reconstructed round trips; B1 310+250+284 = 844;
  these two books share 2,001 of their fills, so the CORPUS-UNIQUE
  denominators are 2,798 unique market fills and 3,467 leg-level decision
  points over 4 years (never a cross-arm sum — the per-arm reconstruction
  counts above are for scale only). USDJPY carries ~99.6% of turnover and
  spread cost `[M: docket A §8]`. EUR/GBP books are small (13–50 trades per
  leg-arm cell) — every EUR/GBP rule is under-powered by the dockets' own
  floors.
- No portfolio-minus-one-leg artifact exists (solo ≠ minus-one); per-leg
  portfolio counterfactuals stay `[NR]` and cannot be produced by
  arithmetic on these journals (netting path-dependence; GATING_VS_SIZING
  §8.4's no-counterfactual ban).
- The three attribution laws (entry-trigger / paper_fold_net_by_leg /
  solo-arm) disagree in SIGN for S014 and by 178× in magnitude for S026
  `[M]`. Any successor rule keyed to "a leg's PnL" must name its attribution
  law, and the successor battery must include true leave-one-leg arms to
  resolve this (COMPOSITE_POLICY_DESIGN §6).

— end census —
