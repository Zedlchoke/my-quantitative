# COMPLEMENTARITY_AND_FAILURE_MAP — successor_design_2026-10-02

Question put to the journals (owner dispatch §4): which legs participate,
lose and draw down TOGETHER; what is shared (USD exposure, direction,
cluster, turnover); what each leg contributes after costs; and whether one
leg is carrying the whole portfolio. Machine evidence:
`analysis/complementarity.json`; prior evidence: GATING_VS_SIZING.md,
dockets A/B, DECISION_PACKET §2.

All statements on the 8 exposed TEST folds; USDJPY figures at-par journal
units; weekly nets are CASH-BASIS (fills − swaps per ISO week) — they
approximate, and do not replace, MTM drawdown decompositions (docket
friday-equity work covers MTM).

## 1. Co-participation, co-loss, co-drawdown

- **Exposure (POLICY heat events `[M]`):** USDJPY in position 57.8% of the
  window, EURUSD 36.9%, GBPUSD 4.5% (the `heat_events_by_symbol` key is
  ABSENT from B1 metrics — `[NR]`, disclosed). Joint in-position time:
  EURUSD×USDJPY 22.92% of the window (= 62.8% of EURUSD's in-position
  time); EURUSD×GBPUSD 1.82%; GBPUSD×USDJPY 2.91% (GBPUSD is an
  intraday-flat satellite). USDJPY and EURUSD overlap substantially but NOT
  "a majority of the window" — 22.9% joint is the honest number.
- **Co-loss weeks (cash-basis, both-symbols-lose > $1,000, B1 path)
  `[derived]`:** 27 of 208 weeks (13.0%); every sampled co-loss pair is
  **EURUSD × USDJPY** (GBPUSD essentially never co-loses — it is flat
  overnight and its losses are small). The co-loss clusters sit in
  2022-04→2022-12 and 2023-02→2023-05 — the USD-rally regime in which both
  books' losing sides were effectively the same USD exposure.
- **Fold co-movement `[M: metrics per_fold]`:** the portfolio's losing folds
  (f1 −150k, f2 +22k POLICY; f6 −231k) are USDJPY-gate-dominated
  (GATING_VS_SIZING §4: harm folds 1/2/6 all GATE-led; helper folds 4/5 are
  PONLY/CARRY-led). There is no fold where EUR/GBP gains offset a USDJPY
  drawdown materially — their books (≤ ±2k per fold) are an order of
  magnitude too small.
- **Weekly cash-net correlation (B1) `[derived]`:** EUR|GBP −0.12 (n=142),
  EUR|JPY +0.16 (n=151), GBP|JPY −0.03 (n=137) — near zero. **Do not read
  this as diversification**: cash nets bucket trades by fill week while
  positions span weeks; near-zero correlation of lumpy cash series mostly
  measures asynchronous fill timing, not risk independence. MTM drawdown
  overlap (the co-loss list above) is the honest risk lens.

## 2. Shared exposure structure

- **USD:** EURUSD longs and GBPUSD longs are USD-shorts; USDJPY longs are
  USD-longs. The realized books: USDJPY long-dominant (260 W-long vs 32
  W-short pooled) AND GBPUSD short-heavy profitable (+1,383 SHORT vs −440
  LONG) — in the 2022 USD rally both were effectively **long USD together**
  (the co-loss weeks above are the flip side). The portfolio has a hidden
  common USD factor; it paid in 2022 and is unhedged in reverse regimes.
- **Direction/cluster:** 3 of 12 legs are A-TREND family, 3 B-MEANREV, 2
  C-BREAKOUT, 2 VOLPROF, 1 E-SESSION, 1 J-REGIME_OPT; but vote-carrying
  mass is 83% in 4 legs (S026 breakout-intraday, GBP-S002 session trend,
  S014 meanrev, S013 meanrev) — family diversity on paper, concentration in
  practice.
- **Turnover/cost sharing:** USDJPY = 99.6% of portfolio turnover and
  spread cost `[M]`; the cost guard (L6), the worst overlay, was keyed to
  USDJPY's own trailing spend — i.e., the portfolio's cost governance was
  effectively single-symbol governance.
- **Calendar/session sharing:** all legs trade the same M1 calendar;
  USDJPY's bad bucket (NY session) and EURUSD's bad hours (12:00/16:00
  UTC) are the SAME liquidity handover window — the two symbols' worst
  admission windows coincide (London→NY handover).

## 3. Contribution after costs, per leg — three attribution laws

Portfolio nets (TEST, ×1.0): POLICY +603,340.60 / B1 +688,604.03 pooled
(par-convention; quote-CCY restatement is a REQUIRED successor item).
Per-symbol contribution: USDJPY 600,083/687,284 · EURUSD 2,315/601 ·
GBPUSD 942/719 `[M]` — **USDJPY is 99.6% of the book.**

Inside USDJPY the three attribution laws disagree (census §5; solo arms
`[M]`):

| leg | trig (portfolio entry-trigger) | pfold (in-portfolio) | solo (single-leg arm) |
|---|---:|---:|---:|
| S026 | +825k/+822k | +1,637k | **+9.2k** |
| S003 | B1 n=2 → −5k | +226k | +216k |
| S023 | B1 n=1 → +107k | +230k | +57k |
| S014 | −222k/−320k | +35k | **+109k** |
| S002 | B1 n=7 → +69k | −24k | −249k (B1) / +138k (floored POLICY) |

Reading for the designer: **the portfolio's PnL lives in the BLEND** —
S026's re-entry cascade riding a persistent trend inventory (S003/S023/S002
votes) — and no attribution law on file can decompose it. "S026 is the
workhorse" (trig) and "S026 is churn" (solo) are both true under their own
laws. Consequences: (i) leg-level on/off rules cannot be priced from
existing journals (no minus-one arm exists); (ii) the successor battery
MUST include leave-one-leg arms as first-class identities; (iii) any rule
whose justification is a single attribution law inherits that law's bias.

## 4. Is one leg carrying the portfolio?

- At SYMBOL level: yes — USDJPY carries ~99.6% of net and turnover. A
  portfolio-level DD event is a USDJPY event by construction.
- At LEG level inside USDJPY: **undecidable from existing artifacts** — the
  S026/S003/S023 blend is path-dependent (650/703 exits are netting
  SIG-ENTRYs; CARRY+PONLY returned 79% of the gate harm). The PC12A P8
  "7/12 isolation re-runs fail" (corr-3) used SOLO arms, which measure
  standalone economics, not portfolio carriage; the without-leg-i reading
  was never run `[NR]`.

## 5. Netting / caps / sizing vs on-off (what the decomposition says)

GATING_VS_SIZING (exact identity, $0.0000 residual) `[derived]`:
**GATE −385,500 (4.4× the net harm) · SIZE −7,307 (2%) · PONLY +65,678 ·
CARRY +241,865 · net ΔW −85,263.**
- The harm is a PARTICIPATION phenomenon, not a sizing phenomenon. The
  supermajority/netting stack on identical decision hours moved −$7.3k.
- L6 cost guard = 91.4% of USDJPY gate harm (−352,959; folds 1–2 = −351.5k
  of it); the 29 matched defers B1 filled were +274,572 and
  drawdown-REDUCING.
- E1 floor: net-POSITIVE pooled (+17,282; +108,761 in f5) — the floor was
  the policy's one measured win; E-degradation/W-rules never fired (zero
  rows).
- Weekly classes: SIZE-only weeks netted +371,526 FOR the policy; MIXED
  weeks (gate-skips interleaved with sizing) carry the whole harm −460,224.
  Gate-skips matter through the multi-week position paths they create.

## 6. Control-arm readings (same market, different laws) `[M: metrics]`

| arm | net | reading |
|---|---:|---|
| B1 always-on | +688,604 | the wall every overlay must beat (seven-deaths prior) |
| B7 lagged eligibility 1w | +591,220 | 1-week information lag costs ~97k — the always-on edge is not lag-robust at portfolio scale |
| B8 oracle eligibility | +388,901 | an ELIGIBILITY oracle with 1,380 fills UNDERPERFORMS always-on by ~300k — eligibility-style gating destroyed value even with foresight, because the money is in staying in the S026/trend blend |
| B5 clock gate | +54,024 | cadence gating alone destroys 92% of B1 net |
| B6 inverted | −256,348 | sign matters (eligibility inversion loses) |
| B2 equal weight | +356,101 | naive re-weighting also loses to always-on |
| B3 best-single (S013, TRAIN-chosen) | +1,731 | the only positive control besides always-on variants; best weekly SR (0.13) but trivially small |
| POLICY | +603,341 | −85k vs B1 pooled (the terminal verdict) |

**Structural lesson for the successor:** every overlay class that removed
participation (gates, clocks, oracles, inversions, lag, re-weighting)
underperformed the always-on blend on these folds. The ONLY layers with
measured positive contribution are E1-floor-on-bleeding-legs (+504 EUR,
+138k on S002-JPY floored book vs solo-negative always-on) and the
NY-long/session admission buckets (retrospective). The successor's design
budget belongs in (a) per-symbol admission hygiene (session/entry-quality),
(b) retiring structurally-broken exit geometry, (c) cost-authority upgrades
— NOT in portfolio-level gating over the blend.

## 7. Failure map (mechanism → evidence → successor implication)

| # | failure mode | evidence | implication |
|---|---|---|---|
| F1 | Overlay gating harms the blend | 7 terminal deaths; GATE −385.5k; B8 oracle also loses | never portfolio-level always-gates over a netted blend; test per-symbol, per-leg |
| F2 | Cost guard keyed to trailing spend skips the cascade's profitable re-entries | −352,959 direct; +274,572 B1-path on 29 matched defers; DD-worsening without them | guard, if kept, must be re-anchored to measured capacity, not realized spend; treat as hypothesis J3 with strict anti-hypothesis |
| F3 | Calendar-sparse legs mis-read as dead by activity floors | E1 blocked S003/S023/S002 (B1 entries +187k realized; paper +428.7k) BUT saved S009 (−504) and S002-JPY (solo −249k vs floored +138k) | floors must be CLOCK-AWARE (per-leg decision-rate expectations), not one global 3/26w |
| F4 | Session/handover admission losses | USDJPY NY-longs negative both arms all folds; EURUSD 12/16z both arms | the only rule family consistent on both arms/quantities |
| F5 | Stop geometry inside entry-bar noise | S017 20SL:6TP, 15/28 ≤1min; S013 SL:TP asymmetry; S002 27% stop rate | exit-law fixes are TB-EXIT-OVERLAY experiments, NOT journal-recomputable |
| F6 | Cost-structure kills at thin margins | 9/9 H1 legs COST_DOMINATED at ×2.0; AUDUSD C3 deferral 2.2×; swap 353:1 events:fills | cost authority (measured statement) is the highest-leverage unlock; DAILY re-affirmed (P-MW fails under DECLARED costs) |
| F7 | Clock/floor mismatch | DAILY 61 decisions < 100; DS legs FLAT in thin folds | match decision clock to rule cadence a priori (P-35) |
| F8 | Attribution ambiguity blocks leg surgery | S014 sign flips by attribution law; S026 178× spread | leave-one-leg arms mandatory in successor battery |
| F9 | Currency-convention blindness | pooled par numbers mislead cross-symbol sums (DP §13) | quote-CCY ledger (DAILY engine has it) is the successor book law |
| F10 | Hidden common USD factor | co-loss weeks 2022 clusters; long-USD both symbols | per-symbol on/off must be evaluated WITH the USD cluster cap, not leg-by-leg alone |

— end map —
