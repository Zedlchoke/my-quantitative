# ATTRIB_failres_REPORT — Phase A attribution decomposition (failres-attrib)

**Labels (every table/number below): `FAILURE_ROOT_CAUSE_RESEARCH` ·
`DIAGNOSTIC_OUTCOME_EXPOSED` · `SINGLE_SOURCE_PANEL` ·
`FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` · `PAPER_TIER`.**
**R-ORIG numbers additionally carry `R-ORIG-SEMANTICS`** (byte-faithful
leaky ancestor law — placement reference only; citation law of
INCIDENT_RANGEFADE_PIT_SEAM_2026-09-25).

Owner instruction (2026-09-26, verbatim intent): explain why the EURUSD
R-DAEMON shadow law loses in F1/F2/F5, especially F2 2021-11..2022-08.
Phase A = facts/decomposition only, **no winner-picking, no strategy
proposal, no parameter touched** (one pass, frozen laws). Nothing here is
promotable evidence regardless of sign; correlation is not causation; the
events overlay belongs to a separate lane and was NOT performed here.

Lane: `failres-attrib` · branch `orca/erp1-ta1-failres-attrib` @ base
`05168bfebc0dc53f8cc2e6b2a7f0cb79bc80b0a9` · heavy lock `FREE_PROVEN`
before and after compute.

---

## 0. Reconciliation guard — PASS (exact)

The 5 diag books (R-DAEMON, R-ORIG, R-ANCHOR, SHORT_ALWAYS, LONG_ALWAYS)
were rebuilt on byte-copied ANC planes (`bars1h_ANC_{pair}.parquet`,
EURUSD H1 sha256 `2e175b06…4f9d` = expected) with the committed
`engine.run_strategy` / `tracka_lib` laws, `warmup_end_idx=0`, k=1.0.
Folds = imported `falsifier_run.FOLD_TABLE` (never redefined); per-fold
nets count trades ENTERED in the fold.

| Target (DIAG_DAEMON_REPORT) | Diag value | This lane | Δ |
|---|---:|---:|---:|
| EURUSD R-DAEMON F1..F6 | −188.8 / −884.4 / +1,049.8 / +348.3 / −191.5 / +257.0 | identical | 0.0 |
| EURUSD totals: R-DAEMON, R-ORIG, R-ANCHOR, SHORT, LONG | +812.2 (1,062 RT) / +7,322.7 / +1,052.7 / +704.6 / −1,665.5 | identical | 0.0 |
| GBPUSD R-DAEMON total; F3 | −1,708.9; −1,272.7 | identical | 0.0 |

Tolerance was 0.05 pips; every reproduced number is bit-identical at the
2-dp reporting precision (full table in
`failres_attrib_PROVENANCE.json` → `reconciliation`). The instrumentation
used for bar-level mode labels (`labeled_daemon`) asserted identical to
the authoritative `T.f_rangeexp_daemon` (target array + first-mode +
change dicts) on both pairs.

## 1. Method / conventions (all frozen, one pass)

- **Cost decomposition, not a variant**: the SAME book is re-run at k=0.0
  (zero-cost fills; the engine state machine is price-independent, so the
  schedule is identical — asserted per trade). Per trade:
  `gross = pips(k=0)`, `cost = pips(k=1.0) − pips(k=0.0)`.
- **exit_type**: FORCE_FLAT if the exit bar is the day-close (19:00 bar,
  20:00 UTC); else REVERSAL if the next trade enters at this trade's exit
  bar; else TARGET_EXIT. (REVERSAL occurs 0 times in 2,125 daemon RTs —
  the daemon target never flips sign without passing through 0.)
- **mode_at_entry**: instrumented daemon mode (flat/fade/follow) at the
  entry's SIGNAL bar (entry bar − 1).
- **ex_ante_vol_pct**: `pct[d−1]` (prior traded day's full-range
  percentile — the R-ANCHOR mode input, PIT-known at day start).
- **Terciles**: cuts computed on the FULL panel, applied per fold
  (descriptive, one pass). EURUSD cuts: ex-ante {0.2333, 0.5667}, entry
  spread {0.2, 0.4} pips. GBPUSD: {0.25, 0.5833}, {0.7, 0.9} pips.
- **Hour buckets**: Asia 00–06, London 07–12, NY 13–18 UTC.

**Structural disclosure (gap-fills)**: 15 EURUSD / 14 GBPUSD daemon
trades (net −4.5 / +23.1 pips) enter at 00:00–06:00 on days whose
previous day's 19:00–23:00 bars are absent from the corpus: the engine's
`want = target[i−1]` crosses the gap and fills at 00:00 (hour 0 is
`fill_ok`). This is a property of the committed machinery and data, is
inside the reconciled diag numbers, and is disclosed — not fixed.

## 2. Headline decomposition (full panel, k=1.0)

| Pair | net | gross | cost | cost/RT | mean entry spread |
|---|---:|---:|---:|---:|---:|
| EURUSD R-DAEMON | +812.2 | +1,502.2 | −690.0 | −0.65 | 0.325 pip |
| GBPUSD R-DAEMON | −1,708.9 | +33.5 | −1,742.4 | −1.635 | 0.813 pip |

**Exit-type split is the most consistent axis on both pairs**
(R-DAEMON, k=1.0):

| Fold | EURUSD FF (RT) | EURUSD TE (RT) | GBPUSD FF (RT) | GBPUSD TE (RT) |
|---|---:|---:|---:|---:|
| F1 | −909.6 (121) | +720.8 (43) | −1,205.7 (121) | +1,084.2 (35) |
| **F2** | **−2,116.5 (128)** | **+1,232.1 (38)** | −1,489.9 (131) | +1,601.1 (41) |
| F3 | −608.5 (120) | +1,658.3 (44) | −2,463.2 (134) | +1,190.5 (26) |
| F4 | −668.7 (129) | +1,017.0 (37) | −643.8 (119) | +1,433.6 (40) |
| F5 | −854.9 (135) | +663.4 (24) | −1,464.2 (129) | +1,057.1 (36) |
| F6 | −460.3 (133) | +717.3 (24) | −1,664.1 (131) | +935.3 (30) |
| full | −5,466.2 (839) | +6,278.4 (223) | −9,429.7 (842) | +7,720.8 (224) |

FORCE_FLAT = trades still open at the day-close bar (79% of RTs);
TARGET_EXIT = the fade law's mid-quarter exit fired before the close.
TARGET_EXIT is positive in **every one of the 12 pair-folds**; FORCE_FLAT
is negative in every pair-fold. The law earns when its mid-exit fires and
gives everything back when it rides into the close.

## 3. F2 (2021-11..2022-08, EURUSD) — the owner's emphasis

Gross/cost: **gross −769.1, cost −115.3 → net −884.4**. The F2 loss is a
gross-side loss; costs are 13% of it.

- **Direction**: long entries −696.0 (95 RT, mean −7.33) vs short
  −188.4 (71 RT, mean −2.65). Both negative — but SHORT_ALWAYS made
  **+838.8** in the same fold, so the daemon's fade-shorts lost where
  unconditional shorts won.
- **mode_at_entry**: fade entries −476.5 (138 RT, −3.45/trade);
  **follow entries −407.9 (28 RT, −14.57/trade)** — the breakout-follow
  state was the per-trade worst.
- **Mode-flip days**: 132 flip days → 102 RT **−1,455.5 (mean −14.27)**;
  86 non-flip days → 64 RT **+571.1 (mean +8.92)**. Non-flip-day pools
  are positive in all 12 pair-folds; flip-day pools negative in 10/12.
- **Exit type**: FORCE_FLAT −2,116.5 (128) vs TARGET_EXIT +1,232.1 (38).
- **Hours**: London-bucket entries −689.7 (95 RT), NY −202.9 (70 RT),
  Asia ≈ 0 (structural + 1 gap-fill) — proportionate to RT counts.
- **Ex-ante terciles**: t1_low −359.3 (42), t2_mid −491.4 (53),
  t3_high −33.7 (71): losses sit in the LOW/MID prior-day-range
  percentiles, not the "wide" ones.
- **Beta pull**: daemon − SHORT_ALWAYS = **−1,723.2** (daemon far below
  beta); daily rho(daemon, SHORT) = **−0.189** (anti-correlated);
  signed in-session exposure +0.030 (slightly net-long — wrong side of a
  downtrend); daemon − LONG = +112.3.
- **Silencing**: 82 first-mode-flat days; R-ORIG-SEMANTICS net on those
  days +139.2 (61 RT) vs +1,736.5 (107 RT) on daemon-active days — the
  ancestor's F2 money sits on days the daemon ALSO traded, so early
  silencing is NOT the F2 driver.
- **k-decay**: F2 −884.4 → −942.1 (k=1.5) → −999.7 (k=2.0). Monotone
  decay in every fold on both pairs; no cost tier rescues F2 (loss is
  gross-side).
- **Monthly nets (daemon)**: negative in 7/10 months; worst 2021-11
  −291.2, 2022-03 −269.4, 2022-04 −200.4; best 2022-02 +178.4. Broad,
  not single-month.
- **Worst 15 daemon days** (all single-trade days, 13/15 with a mid-day
  mode flip, 13/15 first-mode fade; worst-5 sum −527.7 = 60% of F2 net):

| date | daemon net | dir | flips | first mode | ex-ante pct | R-ORIG same day |
|---|---:|---:|---:|---|---:|---:|
| 2022-03-10 | −113.7 | L | 1 | fade | 0.983 | −113.7 |
| 2022-07-05 | −109.0 | L | 1 | fade | 0.017 | +108.1 |
| 2022-03-09 | −107.4 | S | 1 | fade | 0.883 | +107.1 |
| 2022-03-04 | −99.1 | L | 1 | fade | 0.700 | +98.7 |
| 2022-08-26 | −98.5 | L | 2 | flat | 0.300 | −98.5 |
| 2022-04-21 | −88.8 | L | 0 | follow | 0.517 | −88.8 |
| 2022-05-12 | −86.8 | L | 1 | fade | 0.300 | +86.1 |
| 2022-05-23 | −86.5 | S | 1 | fade | 0.217 | +85.6 |
| 2021-11-10 | −85.5 | L | 1 | fade | 0.250 | +84.9 |
| 2022-05-17 | −82.6 | S | 1 | fade | 0.083 | +81.8 |
| 2021-11-26 | −82.2 | S | 1 | fade | 0.017 | +80.2 |
| 2022-06-10 | −78.8 | L | 1 | fade | 0.950 | +78.3 |
| 2022-07-08 | −70.6 | S | 0 | follow | 0.333 | −70.6 |
| 2022-03-11 | −69.4 | L | 1 | fade | 0.917 | +68.4 |
| 2022-04-27 | −65.8 | L | 1 | fade | 0.700 | +65.4 |

**R-ORIG-SEMANTICS was positive on 12 of these 15 days, with
near-mirror magnitudes** (e.g. 2022-07-05 daemon −109.0 vs orig +108.1).
Same days, opposite outcomes → day selection is not what separates the
daemon from its ancestor on the worst days; the mid-day re-ranked mode
and the resulting placement/exit are.
- **Cumulative long vs short (F2)**: daemon long-entries cum **−696.0**,
  short-entries cum **−188.4**. R-ORIG-SEMANTICS on the identical
  daemon-trading days: long +625.3 / short +1,109.0 (R-ORIG F2 totals:
  +1,875.7 all days, +1,734.3 on the daemon's trading days).

## 4. Per-fold aggregate tables (B.1–B.10)

Full machine-readable tables: `failres_attrib_agg_{EURUSD,GBPUSD}.json`.
Compact per-fold view, EURUSD R-DAEMON (net pips; RT):

| Fold | net (diag-equal) | long / short | fade-entry / follow-entry | flip-day / non-flip-day RTs | daemon−SHORT | ex-ante t1/t2/t3 | k=1.5 / 2.0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| F1 | −188.8 (164) | −231.1 / +42.3 | −177.0 / −11.8 | −314.4 (119) / +125.6 (45) | −609.3 | −179.0 / +43.8 / −20.4 | −235.8 / −282.8 |
| **F2** | **−884.4 (166)** | **−696.0 / −188.4** | **−476.5 / −407.9** | **−1,455.5 (102) / +571.1 (64)** | **−1,723.2** | **−359.3 / −491.4 / −33.7** | −942.1 / −999.7 |
| F3 | +1,049.8 (164) | +946.4 / +103.4 | +830.8 / +219.0 | +930.3 (128) / +119.5 (36) | +1,332.8 | +700.8 / +453.2 / −104.2 | +984.2 / +918.5 |
| F4 | +348.3 (166) | −14.3 / +362.6 | +275.3 / +73.0 | −60.6 (93) / +408.9 (73) | +213.5 | −196.8 / +236.3 / +308.8 | +308.3 / +268.3 |
| **F5** | **−191.5 (159)** | **−183.3 / −8.2** | **−106.7 / −84.8** | **−418.0 (101) / +226.5 (58)** | **−21.4** | **−102.6 / +109.8 / −198.7** | −230.8 / −270.0 |
| F6 | +257.0 (157) | +462.9 / −205.9 | +161.6 / +95.4 | +51.6 (99) / +205.4 (58) | +636.2 | +186.9 / +76.9 / −6.8 | +189.2 / +121.4 |

GBPUSD R-DAEMON (secondary, same machinery): the disaster fold is **F3
−1,272.7** = long −438.7 (79) + short −834.0 (81); fade entries −941.5,
follow −331.2; flip days −2,002.3 (96 RT) vs non-flip +729.6 (64);
London bucket −1,287.1; ex-ante t3_high −1,395.7 (the only fold where the
"wide prior day" tercile dominates the loss); daemon−SHORT = −270.1 with
SHORT_ALWAYS itself −1,002.6 in F3; k-decay −1,272.7 → −1,624.3 (k=2.0).
Full-panel GBPUSD is a COST story: gross +33.5, cost −1,742.4.

Early-silenced days per fold (daemon first-mode flat; R-ORIG-SEMANTICS
net on exactly those days vs daemon-active days):

| Fold | EURUSD n_sil | orig@sil | orig@active | GBPUSD n_sil | orig@sil | orig@active |
|---|---:|---:|---:|---:|---:|---:|
| F1 | 131 | +867.8 | +557.2 | 115 | +769.4 | +707.9 |
| F2 | 82 | +139.2 | +1,736.5 | 99 | +195.4 | +1,346.9 |
| F3 | 144 | +720.1 | +421.5 | 90 | +562.7 | +1,081.3 |
| F4 | 76 | +798.0 | +477.2 | 132 | +1,352.8 | −3.5 |
| F5 | 97 | +49.2 | +506.7 | 112 | +496.0 | +559.9 |
| F6 | 105 | +500.1 | +373.6 | 107 | +569.0 | +887.4 |

The silencing seam is real but fold-dependent (largest in EURUSD F1,
GBPUSD F4); in F2 on both pairs the ancestor's money is on daemon-active
days, so silencing does not explain F2.

## 5. Daily join table (D)

`failres_daily_{EURUSD,GBPUSD}.json` — per traded day (1,427 / 1,426
rows): net_daemon / net_orig / net_anchor / net_short / net_long (k=1.0),
daemon signed in-session exposure, day_first_mode, n_mode_changes,
ex_ante_vol_pct, day_spread_p50_pips, fold. Sum identities per book and
per fold are asserted in the test suite. This is the overlay surface for
the events lane; no event data was used here.

## 6. Reading — which candidate explanations the numbers support

Per the dispatch, observations only (support/refute with numbers); no
causation claim about news/war/Fed is made or testable here.

**(1) Direction/trend loss (long fades bleed against the F2 downtrend) —
SUPPORTED as the largest F2 component, but incomplete.** Long entries
−696.0 vs short −188.4 (79% of the F2 loss from 57% of RTs); signed
exposure +0.030 (net-long) in a fold where SHORT_ALWAYS made +838.8.
Refuting half: the daemon's SHORT fades also lost (−188.4) where
unconditional shorts won — direction alone does not explain why fade
shorts failed; and in GBPUSD F3 BOTH directions lost badly (−438.7 /
−834.0) while SHORT_ALWAYS lost −1,002.6 there, i.e. that fold's loss is
mostly shared with beta.

**(2) Cost dominance — REFUTED for EURUSD F2, SUPPORTED for GBPUSD.**
EURUSD F2: cost −115.3 of −884.4 (13%); gross already −769.1. The EURUSD
full-panel book is gross-positive (+1,502.2) with cost −690.0. GBPUSD:
gross +33.5 vs cost −1,742.4 (cost/RT −1.635 on a 0.813-pip mean entry
spread vs EURUSD 0.325) — GBPUSD's negative book is arithmetic on
spreads, not on trade selection. k-decay is monotone on both pairs (F2
EURUSD −884.4 → −999.7 at k=2.0), so no cost tier changes any sign
conclusion.

**(3) Mode-plane noise (partial-range percentile flips/silences vs
R-ORIG and R-ANCHOR) — SUPPORTED, with the silencing sub-claim limited.**
Flip-day pools: EURUSD F2 −1,455.5 (mean −14.27/trade) vs non-flip
+571.1 (+8.92); non-flip positive in 12/12 pair-folds, flip negative in
10/12. Follow-mode entries are the worst per-trade class where follow
trades exist (F2 EURUSD −14.57/trade on 28 RT). The worst-15-day mirror
(R-ORIG-SEMANTICS positive on 12/15, near-equal magnitude) shows the
daemon loses on days the ancestor trades profitably — same day, different
(mode re-ranked) placement. Silencing specifically: 48–50% of days have
daemon first-mode flat, but the R-ORIG-SEMANTICS money on silenced days
is small in F2 (+139.2 EURUSD / +195.4 GBPUSD) and the seam is
fold-dependent (biggest in EURUSD F1 +867.8, GBPUSD F4 +1,352.8) — so
"silencing explains F2" is NOT supported; "mid-day re-ranking hurts the
trades it does take" IS supported.

**(4) Session/timing concentration — NOT SUPPORTED as a standalone
cause; the FF/TE split is the real timing fact.** Entries only exist
London/NY (Asia entries are structurally impossible except 15 gap-fills,
net −4.5 pips), and F2's London/NY loss split (−689.7 / −202.9) is
roughly proportional to RT counts (95/70); the diag's G8 top-hour shares
were 0.24/0.19. What timing DOES explain is exit side: 800/1,062 EURUSD
exits at the 19:00 day-close carry −5,466.2 full-panel while the 223
mid-quarter exits carry +6,278.4 — consistently in every fold, both
pairs. Positions that survive to the close are the losers; that is a
placement/exit-quality fact (facet of (1)/(3)), not hour-of-day
concentration.

**(5) Ex-ante volatility conditioning — NOT SUPPORTED as a stable
conditioner.** Tercile signs are not monotone and reorder across folds:
F2 losses sit in t1/t2 (−359.3 / −491.4) with t3 least-bad (−33.7); F1's
worst is t1 (−179.0); F3's best is t1 (+700.8); GBPUSD F3's worst is t3
(−1,395.7). Prior-day range percentile does not consistently separate
winning from losing daemon trades on this panel.

**Explicitly not supported by this data**: cost dominance on EURUSD
(including F2); early-silencing as the F2 mechanism; session/hour
concentration as a standalone cause; ex-ante vol tercile as a stable
conditioner; beta explains F2 (daemon−SHORT = −1,723.2, rho −0.189 —
the daemon is not short-beta in F2, it is anti-correlated with it).
Supported: long-fade directional bleed (largest F2 component), mid-day
mode re-ranking (flip days / follow entries / worst-day mirror vs
R-ORIG-SEMANTICS), and — the most consistent fact on both pairs —
FORCE_FLAT-at-day-close trades lose in every fold while TARGET_EXIT
trades win in every fold. On GBPUSD the full-panel negative book is
additionally a pure cost story.

## 7. Tests

`failres/tests/test_failres_attrib.py` — 8 passed (venv python 3.12.14,
pytest 9.1.1, 2.75s): fold reconciliation vs the 6 diag numbers + full
panel totals (5 books) + GBPUSD total/F3; gross+cost==net on 100 sampled
trades per pair; daily-table sums == trade-table sums (full panel and
per fold); committed recon block matches diag targets.

## 8. Limitations and incidents

Limitations: OUTCOME-EXPOSED dev surfaces (never promotable);
FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK (paper-tier spread costs only);
SINGLE_SOURCE_PANEL; mode_at_entry uses an instrumented copy of the
daemon walk (asserted bit-identical to the authoritative function);
tercile cuts are descriptive full-panel statistics, one pass; 15/14
gap-fill trades disclosed in §1; correlation ≠ causation and no event
overlay was performed (separate lane owns events).

Incidents (lane-internal, no foreign impact): (1) the run script's
worktree constant was initially off by one path component and pointed a
READ-ONLY `git rev-parse HEAD` at the sibling cohort checkout — no write
occurred outside this worktree; fixed with a hard assertion
(worktree name + `.git` presence) and the provenance regenerated. (2)
None otherwise.
