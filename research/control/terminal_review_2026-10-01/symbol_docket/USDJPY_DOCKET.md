# USDJPY SYMBOL-DOCKET — PC12A terminal review (group A)

**STATUS HEADER — READ FIRST.** Every PnL/trade number below is reconstructed
from the COMMITTED Stage-C TEST journals
(`research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/diagnostics/stagec/ARMS/{POLICY,B1_ALWAYS_ON}/journal.jsonl`,
scored TEST folds 2022-01-07→2025-12-26). These are the SAME folds the arms
were scored on. **All contrasts, rule tests and "effects" here are
HYPOTHESIS-GENERATING ONLY — they are retrospective reads of already-scored
TEST data and are NOT fresh validation. Nothing here may be cited as an
out-of-sample result.** No engine run, no S1, no network; reconstruction by
offline scripts over the committed journals.

**The headline, restated precisely.** "USDJPY carried ALL the harm
(−87,201.39)" = the per-fold sum of the USDJPY **POLICY − B1 differential**
(600,082.92 − 687,284.31 = −87,201.39, `per_symbol_fold_records` in both
metrics.json). USDJPY is **net positive in both arms** (journal reconciliation
below); the harm is the POLICY overlay *underperforming* the always-on control
on this symbol, concentrated in folds 1 (−83,216.71) and 2 (−209,367.77),
partly recovered in folds 4 (+111,160.89) and 5 (+174,621.74). Fold-0 nets are
arm-identical (+540,319.38) — the gates bit nothing there.

**Units caveat (measured).** USDJPY `cash_delta_usd` on fills is carried at
par from the JPY notional (10,000 units × 115.63 → 1,156,299.65; no ÷rate),
while SWAP rows ARE rate-converted (29,384 units × 1 pip / ≈132.9 = 2.21).
This is the frozen quote-currency book convention of FILL_ACCOUNTING_SPEC §4,
applied identically in both arms and all folds, so every *relative* statement
(POLICY vs B1, winners vs losers, rule deltas) is unaffected; **absolute
USD magnitudes would scale by ≈1/USDJPY-rate under an explicit FX
conversion**. Successor engine must fix explicit conversion.

---

## 0. Reconstruction method and reconciliation (accounting identity)

- **Trade = flat-to-flat excursion** of the per-symbol netted position: from
  the NET_ORDER that leaves `units_after ≠ 0` to the first that returns it to
  exactly 0 (the netting voter architecture — one net position per symbol;
  legs' internal exposures blend inside it). Sequential OPEN→CLOSE pairing
  alone is not well-defined here because an `OPEN` can flatten (opposite-leg
  netting) and a `CLOSE` can re-open inventory (19k–29k unit flip-flops vs the
  ±10,000 vote quantum).
- Per trade: entry/exit ts (UTC hour → session), direction, `max_units`,
  fills, `gross = Σcash + Σcommission + Σcross_cost` (net-of-nothing vs mid),
  `net = Σcash + Σswap`, friction = commission + cross_cost (+gap_excess=0
  everywhere) + |swap|. Swap rows (22:00 UTC nightly) allocated to the open
  excursion. Entry/exit **trigger** = the DECISION row chained via
  `prev_row_sha256`; CLOSEs chained to a NET_ORDER (no DECISION) = fold-edge
  **force-flat**, tagged. Cost identity `gross − comm − cross − gapx + swap =
  net` holds to 0.00 for every trade.
- **Reconciliation [MEASURED]:** POLICY 393 trades, Σnet = +602,943.11 =
  journal symbol net (fills 601,513.02 + swap 1,430.10); friction Σ128,073.06
  = metrics `cost_bill_totals_usd` for USDJPY **exactly**; 4 force-flat trades
  = `n_force_flat` 4, on folds 3/4/5/7 where `force_flat_cost_usd > 0`.
  B1: 310 trades, +689,713.59; friction 106,651.05; 5 force-flats ✓.
  Residual: per-symbol-fold-record nets (600,082.92) differ from journal cash
  sums by 2,860.19 (0.48%) — fold-edge mark convention in the rollup; does not
  affect any conclusion. One POLICY trade closes at the 2025-12-28T22:04Z
  post-window force-flat (tagged).

**Outcome grouping.** WINNER net > +c, LOSER net < −c, BREAKEVEN otherwise,
**c = 239.54** = pooled median round-trip friction over all 703 USDJPY
excursions (both arms). Justification: |net| below the median cost of one
round trip is indistinguishable from cost realization, not edge; c is measured
on this pair's own cost scale (spread+slip+commission+|swap|), not a free
parameter.

---

## 1. Eligibility line (USDJPY)

- **Data:** M1 bid/ask panel staged (`panels.py`, one of only 3 M1 pairs);
  data_digest `d1b0c257…42c0c0` identical across both arms, DIAG and journals.
- **Legs admitted (6):** USDJPY-S002 (A-TREND ma_regime_gate, MULTIMONTH),
  S003 (A-TREND tsmom_12_1skip, MULTIMONTH), S014 (B-MEANREV rsi2_fade,
  DAILY/H4), S023 (C-BREAKOUT vol_regime_breakout, DAILY), S026 (C-BREAKOUT
  pdhl_stop_sweep, INTRADAY/H1), VC2-LVNFAIL-USDJPY (VOLPROF M1 class
  candidate — registered via TRIAL_LEDGER/CLASS_SPEC, not in the 1200-corpus
  TSV). All five corpus legs: census `VARIANT_OR_DUPLICATE`,
  `FAMILY_HISTORY_NEGATIVE` prior, mechanizable YES, PRICE_ONLY.
- **PIT/cost axis:** price_axis `M1_BIDASK_PANEL`; pit_class PRICE_ONLY (all
  6 legs — no macro PIT inputs); cost_axis
  `PROVISIONAL_PENDING_COST_AUTHORITY` (no owner cost statement landed).
- **M1 measured spreads (DECLARED bands, FILL_ACCOUNTING_SPEC §3,
  DATA_AUDIT §D):** C1 general 0.5/0.9 pips p50/p90 (n=286/286); C2 Mon–Thu
  (21:00,22:00] roll **2.1/7.4** (n=64,892 corrected cell); C2 Fri roll
  0.8/1.8; C3 Sunday reopen **11.0/22.0**. Slip U3 0.2 pip non-event / 1.0
  event; commission U2 0.35 bps/side; swap U4/U5 1 pip/night, Wed ×3.
- **TRAIN-side solo priors (DIAG_MAIN_JPY_USDJPY.json, label
  DISCOVERY-TRAIN-ONLY, expanding folds 2021-01-08→2025-06-20):** all 6 legs
  carried positive or mixed cumulative TRAIN nets except early-fold losses
  (S002 f0 −10,382; S014 f0 −10,079; S023 f0 −9,558; S026 f0 −26,022);
  VC2 f0 +2,366. These priors justified triage admission, not TEST
  expectations.

---

## 2. OUTCOME TABLE

Counts + medians per arm and pooled (session = entry session; UTC hour).

### Pooled (n=703)

| group | n | Σnet | med net | med gross | med cost | med hold (h) | med entry hour | top entry sessions (n) |
|---|---|---|---|---|---|---|---|---|
| WINNER | 292 | +6,417,355.58 | +9,027.60 | +9,404.24 | 309.79 | 24.0 | 12 | London 119, LondonNY 83, NY 73 |
| LOSER | 387 | −5,124,559.15 | −7,289.74 | −7,036.39 | 214.35 | 7.0 | 12 | London 168, LondonNY 120, NY 86 |
| BREAKEVEN | 24 | −139.73 | −45.59 | +113.13 | 171.08 | 1.0 | 13 | LondonNY 12, NY 6, London 4 |

### Per arm

| arm | W / L / B (n) | Σnet | med net W / L / B | med hold W / L / B |
|---|---|---|---|---|
| POLICY | 157 / 224 / 12 | +602,943.11 | +7,965.47 / −7,409.65 / −45.59 | 22 / 7 / 1 h |
| B1_ALWAYS_ON | 135 / 163 / 12 | +689,713.59 | +9,185.20 / −6,915.51 / −45.59 | 24 / 8 / 1 h |

Per-fold pooled W/L (provenance): f0 42/56/6 · f1 38/46/2 · f2 33/48/1 ·
f3 37/51/3 · f4 24/33/4 · f5 42/57/0 · f6 37/58/3 · f7 39/38/5 — losers
outnumber winners in **every** fold; the book lives on winner magnitude
(med W/L gross ratio ≈ 1.34), not hit rate.

### Decomposition by leg (6 legs)

Direct attribution requires single-leg fills at vote scale (|Δu| ≤ 10,000);
nearly everything else is blended by the netting voter — marked
**[derived]**.

- **Direct single-leg trades:** only S026 qualifies in volume: POLICY n=16
  (Σnet +18.41; 3W/12L/1B, med net −950.27) · B1 n=40 (Σnet −35,496.60;
  7W/28L/5B). The S026 stop-cascade's *isolated* round trips are a coin-flip
  churn; its PnL arrives blended with the persistent inventory (below).
- **Entry-trigger attribution [derived]** (excursion booked to the leg whose
  DECISION triggered its entry): POLICY — S026 n=369 → +825,243.84; S014
  n=24 → −222,300.73; (no other leg triggers an entry; blocked at gate).
  B1 — S026 n=268 → +822,232.99; S014 n=29 → −319,603.73; S002 n=7 →
  +68,820.39; S023 n=1 → +107,139.61; VC2 n=3 → +16,589.20; S003 n=2 →
  −5,464.87.
- **Campaign's own paper book [derived, B1 only]** (`paper_fold_net_by_leg`,
  TEST folds): S026 +1,637,143.15 · S023 +230,099.40 · S003 +225,631.11 ·
  S014 +34,984.20 · S002 −24,268.70 · VC2 −2,804.70 (paper sum +2,100,784.46
  ≫ realized 689,713.59 — solo-leg paper ignores netting interactions; treat
  as mechanism evidence, not realizable PnL).
- **Force-flat trades (tagged):** POLICY 4 — f3-end −18,082.83 (L, 99h),
  f4-end +102,106.64 (W, 434h), f5-end +83,635.02 (W, 289h), f7-end
  −6,737.44 (L, 53h); Σ +160,921.39 — fold-edge flats *locked in* two large
  winners.

---

## 3. ENTRY-TIME FEATURE CONTRAST (journal fields only)

Features available: `onoff_features.decision_count_trailing` (dct),
`eligibility_state` (always ON on filled decisions), `direction_vote`,
`entry_reason_code`, `cluster_id`/`family_id`, `outcome_exposed_label`
(FAMILY_HISTORY_NEGATIVE for all but 42 VC2 CLASS_CANDIDATE rows — no
contrast possible), `portfolio_state.n_eligible` (constant 6 → no
contrast), entry hour/session (derived). Effect sizes with n; **no
significance language** — these are descriptive contrasts on one path.

| feature | WINNER | LOSER | BREAKEVEN | effect (W vs L) |
|---|---|---|---|---|
| dct (median [q25,q75]) | 624.5 [245, 943.5] | 568 [236, 944.5] | 591.5 | Cliff's δ = **+0.028** (nW=292, nL=387) — no separation |
| entry hour (median) | 12.0 | 12 | 13.0 | δ = +0.016 — none |
| session (n, Σnet) | London 119 +912.8k; LondonNY 83 +380.0k; NY 73 −365.1k; Tokyo 14 +129.7k; Late 3 +235.3k | London 168; LondonNY 120; NY 86; Tokyo 8; Late 5 | LondonNY 12; NY 6; London 4; Tokyo 2 | **NY-session entries are the only money-negative bucket (both arms: POLICY −281,460.12 n=91; B1 −83,683.91 n=74)**; sign-consistent across all 8 folds |
| direction (n, Σnet) | long 260 → +1,268,237.07 pooled; short 32 → +24,419.64 | long 352; short 35 | long 19; short 5 | long-dominant book; NY effect is a LONG effect (long×NY −384,746.52 n=143; short×NY +19,602.49 n=22) |
| entry_reason (n, Σnet) | M1_STOP_HIT re-entries 194 (+1,195,638.32 overall n=482); H1_PDH_BREAK_LONG 19 (fam +503,708.41 n=45) | M1_STOP_HIT 267; RSI2_MID_CROSS 20 (**family −470,441.67, n=33**); M1_TARGET_HIT 60 (fam −163,696.70 n=113) | M1_STOP_HIT 21 | stop-cascade re-entries carry the book; RSI2 mid-cross (S014) and target-hit exits are the negative families |
| cluster (Σnet) | breakout_intraday +1,647,476.83 (n=637) | meanrev_daily −541,904.46 (n=53) | trend_multimonth +63,355.52 (n=9); breakout_daily +107,139.61 (n=1); volprof +16,589.20 (n=3) | the two D1-trend clusters only appear (net-positive) when the E-floor lets them trade — i.e., in B1 |

**[NR — computable only in successor engine]:** MAE/MFE, realized vol at
entry, trend state/regime flags, spread actually quoted at the entry bar —
none are journal fields (feature_pit_snapshot carries only value digests of
D1/M1 closes, not numeric features).

---

## 4. EXIT-MECHANICS EFFECTS (pooled; exit class from the TB inventory)

Exit class of an excursion = the class of the decision that triggered its
final flattening fill (in a netted book most flattings are *another leg's
entry* — that is itself the finding).

| exit class | n | W/L/B | Σnet | med hold (W/L) | med winner \|gross\| | med loser gross |
|---|---|---|---|---|---|---|
| SIG-ENTRY (opposite/same-leg entry nets the position flat) | 650 | 270/358/22 | +861,458.51 | 23 / 7 h | 9,545.36 | −7,509.65 |
| SL (M1_STOP_HIT / STOP_HIT / ATR_STOP) | 28 | 2/24/2 | +31,680.89 | 24 / 5.5 h | 30,036.88 | **−942.50** |
| TP (M1_TARGET_HIT / TP_POC) | 10 | 10/0/0 | +58,605.91 | 21 h | 6,415.00 | — |
| FORCEFLAT (fold edge) | 9 | 6/3/0 | +265,721.28 | 264 / 80 h | 53,302.08 | −17,130.16 |
| SIG — TSMOM_REBALANCE (S003 monthly) | 2 | 2/0/0 | +67,234.37 | 72.5 h | 33,896.97 | — |
| SIG — MA50_200_ADX (S002) | 4 | 2/2/0 | +7,955.75 | 92 / 20.5 h | 9,366.42 | −4,773.47 |

Reading: (i) **the netting exit law IS the dominant exit** — 650/703
excursions end on a signal entry, not on their own TP/SL; per-leg exit
inventory classes (S026: SL 0.5×ATR(H1)+TP ratchet; S014: SL+SIG+TIME;
S002/S003/S023: SL/SIG/rebalance; VC2: TP/SL/TIME) mostly fire *inside* a
still-open net position and only occasionally flatten it. (ii) When a real SL
does flatten, losers are stopped **small and fast** (med loser gross −942.50,
5.5h) — the stop law works; the damage sits in the SIG-ENTRY class, where
loser excursions are 8× larger (−7,509.65). (iii) Holding-time distributions
by outcome: W p50/p90 = 24/255h; L p50/p90 = 7/73h; B p50/p90 = 1/175h —
winners are held 3.4× longer at the median; the winner tail (>137h, p75) is
trend-inventory carry, and fold-edge flats monetized it (§2).

## 5. COST ANATOMY (pooled, journal units)

| component | WINNERS | LOSERS | BREAKEVEN | total |
|---|---|---|---|---|
| spread_once | 80,059.52 | 63,418.52 | 2,574.38 | 146,052.41 |
| slip_beyond_halfspread | 44,399.55 | 38,194.01 | 1,953.82 | 84,547.37 |
| commission | 776.99 | 668.40 | 34.19 | 1,479.58 |
| \|swap\| | 1,907.05 | 675.89 | 61.79 | 2,644.74 (signed) |

- Spread+slip = **96.4% of all friction**; swap and commission are rounding
  errors at this trade scale (contrary to the "carry bleeds JPY shorts"
  prior).
- Friction share of |gross|: W 3.4%, L 3.2% medians — costs do NOT decide
  W/L outcomes; the edge question is gross direction, not cost.
- **Breakeven ≈ fee-dominated: YES, quantified.** Median friction/|gross| =
  **1.417** for the 24 BE trades; **13/24 have |gross| < friction** outright
  (vs 7/387 losers, 0/292 winners); BE medians: gross +113.13 vs cost 171.08,
  hold 1h — a population of one-fill, one-hour flips whose entire PnL is the
  crossing.

## 6. RULE-SENSITIVITY TESTS (retrospective on the scored TEST path;
hypothesis-generating; every row carries fold provenance)

Base = POLICY arm, 393 excursions; maxDD(weekly exit-week reconstruction,
USDJPY-only approximation) = −412,208.31. "PnL effect" = −Σ(net of removed
trades). Both sides always reported.

**OFF-RULE (retrospective defer/block of POLICY entries):**

| candidate rule | removed | losers avoided | winners suppressed | net PnL effect | maxDD after | folds touched |
|---|---|---|---|---|---|---|
| block NY-session (16–21z) entries | 91 | 50 (−795,805.74) | 38 (+514,369.07) | **+281,460.12** | −359,621.76 | all 8 (13/5/9/12/9/15/15/13) |
| defer if dct > 100 | 348 | 200 (−2,561,783.78) | 139 (+3,142,528.65) | **−580,418.27** | −244,271.34 | all 8 |
| defer if dct > 200 | 323 | 184 | 130 | −317,364.52 | −293,172.70 | all 8 (f0: 3) |
| defer if dct > 400 | 271 | 153 | 110 | −360,722.72 | −525,120.25 | 2–7 |
| block Tokyo (00–07z) entries | 6 | 2 (−64,224.17) | 3 (+63,172.50) | −1,082.37 (noise, n=6) | −405,073.94 | 0,1,5,7 |
| block SHORT entries | 10 | 4 | 5 | +18,791.21 (n=10, all fold 0) | unchanged | 0 only |
| block LONG entries | 383 | 220 | 152 | −584,151.90 | ≈0 | all — destructive |

Honest null: **decision-density (dct) deferral is a null-to-harmful family on
this path** — high-density trades are net positive (the S026 cascade pays
*because* it re-enters); only the dd profile improves (−412k→−244k at
dct>100, at the price of −580k PnL). NY blocking is the only tested off-rule
that is PnL- and dd-consistent, in **both arms** (B1 NY: −83,683.91 n=74).

**ON-RULE (admit currently-deferred/blocked signals), measured on B1's path:**

- **Admit cost-guard defers:** 331 POLICY `DEFERRED_COST_GUARD` rows (S026
  299, S014 27, S003 1, VC2 4); 29 of them were actually FILLED by B1 at the
  identical (leg, ts) — B1 admits them because its own trailing spend differs.
  Those 29 excursions net **+274,572.47 (16W/13L)**, folds {1:7, 2:10, 3:2,
  5:5, 6:4, 7:1}; top +126,734 (2023-05-12, fold 2) = 46% of the total.
  Removing them from B1 **worsens** B1's USDJPY maxDD from −378,482.09 to
  −501,493.31 — the guard deferred trades that were, on B1's path,
  drawdown-reducing.
- **E-floor OFF counterfactual (POLICY blocked legs traded in B1):** blocked
  legs S002 (79 blocks) / S003 (37) / S023 (16) / VC2 (22). B1 paper-book nets
  for those four legs: **+428,657.11 [derived, paper book]** (S003 +225,631.11
  f-distributed +/−; S023 +230,099.40; S002 −24,268.70; VC2 −2,804.70);
  realized B1 excursions *entered* by those legs: +187,084.33 (n=13). The
  E1-style floor ("<3 decisions in trailing 26w") fires structurally on
  calendar-sparse D1/multimonth legs.
- **BLOCKED/DEFERRED inventory (journal rows):** POLICY — BLOCKED_FLOOR 154,
  DEFERRED_COST_GUARD 331, NETTED_TO_ZERO 8; plus SUPERMAJORITY_BLOCK 659 /
  B1 998 (metrics rollup only — no journal rows; portfolio-level vote gate,
  not symbol-controllable).
- **MISSED set (week+direction pairing, coarse [derived]):** B1 excursions
  entered in (ISO-week, direction) cells where POLICY deferred/blocked a
  same-direction signal: n=158, Σnet **−101,520.59** (71W/81L/6B, med
  −392.71, 67 weeks). Measured label per protocol: this is what B1 did in
  those weeks — **the "missed" set was NOT net-profitable**, so at this
  coarse pairing the POLICY gates were not foregoing profit on average; the
  real leakage is signal-selective (the 29 matched defers, +274.6k), not
  week-wide. Converse (POLICY trades in weeks B1 blocked same direction):
  n=95, Σnet −8,776.10 ≈ neutral.

## 7. HYPOTHESES (falsifiable, ranked by mechanistic plausibility)

**H1 — Cost-guard cap binds exactly on the cascade's profitable re-entries.**
Trigger: at a nonzero-vote decision, `guard.trailing_spend ≥ 0.95 × cap` (28d
window). Rationale (measured mechanism): the 28d spend guard deferred 331
signals; the 29 it suppressed that B1 filled were +274,572.47 and
drawdown-REDUCING (dd −378k→−501k without them); S026's economics are a
stop-cascade that re-enters within hours (med loser hold 7h, med winner 24h)
— the guard cuts re-entries precisely when activity, and therefore
continuation frequency, peaks. Predicted benefit (direction +, fold
provenance f1–f7, mostly f1/f2): on the order of +100k–275k per 4y window in
journal units; concentration risk — one trade is 46% of the measured effect.
Failure condition: a re-run with cap ×1.5 admits ≥20 deferred signals whose
realized net ≤ 0, or any fold's admitted set nets < −50k. Sample floor: ≥3
admitted-defer trades/fold and ≥20 full window.

**H2 — NY-afternoon longs buy a spent move (liquidity-fade mechanism).**
Trigger: entry hour ≥ 16z with direction +1. Rationale: sign-consistent
money-negative bucket in BOTH arms (POLICY −281,460.12 n=91 across all 8
folds; B1 −83,683.91 n=74; pooled long×NY −384,746.52) while London longs are
+972,340.40 — PDH-break longs entering after London closes pay the widening
C2-cell spread into thin NY afternoons and miss the continuation. Predicted
benefit: +281k on the POLICY path (maxDD −412k→−360k), both arms agree in
sign. Failure: a re-run blocking NY entries flips ≥2 folds net-negative or
full-window gain ≤ +50k. Floor: ≥3 NY trades/fold (holds now: 13/5/9/12/9/15/15/13),
≥20 window.

**H3 — The E1 thin-floor rule structurally removes the calendar-sparse trend
core.** Trigger: `eligibility_rule_id = E1` on cluster trend_multimonth /
breakout_daily legs. Rationale: E1 ("0–2 decisions in trailing 26w") fires on
legs whose clocks are monthly/weekly BY DESIGN (S003 tsmom monthly rebal,
S023 squeeze, S002 MA50/200) — sparsity ≠ dead signal; their B1 paper nets
(+428,657.11 for the four blocked legs; +187,084.33 realized entries) are the
largest single block of the POLICY−B1 gap after H1, and they long the same
2022–25 uptrend that S026's longs ride (fold provenance: B1 S003/S023
positive in f0,f1,f2,f4,f7). Predicted benefit: exempting calendar-sparse
legs from E1 recovers a share of the +428.7k paper / +187.1k realized —
**share** is the operative word, because paper nets ignore that S003/S023
longs net against S026 shorts (realized ≪ paper is the expected failure
mode). Failure: re-run realizes < +50k net for the exempted set, or realized
gain ≈ 0 because netting cancels it. Floor: ≥5 exempted-leg entries/fold, ≥20
window.

**H4 — The H4 meanrev fade fights the dominant trend and its mid-cross exit
realizes the damage.** Trigger: `entry_reason_code ∈ {RSI2_FADE_LONG,
RSI2_FADE_SHORT, RSI2_MID_CROSS}` / cluster meanrev_daily. Rationale: S014-
triggered excursions −222,300.73 (POLICY) / −319,603.73 (B1); RSI2_MID_CROSS
family −470,441.67 (n=33 pooled) — a z/RSI fade repeatedly selling a
macro-trending pair, exiting on the mid-cross at whatever the netting
inventory did. Mechanistically the cleanest negative: family-level OFF.
Predicted benefit: family deferral saves a share of ~−0.5M pooled (folds: S014
net-negative in both arms; biggest single loser −103,440 on 2023-12-11).
Failure: re-run shows the fades were hedging trend inventory (removal worsens
dd by >50k) — the netting book makes this a real possibility and must be
checked, not assumed. Floor: ≥3 meanrev entries/fold, ≥20 window (n=53 pooled
now — thin; treat as family-level test only).

**H5 — Micro-flip churn is pure friction (small, last).** Trigger:
max_units ≤ 10,000 AND hold ≤ 2h. Rationale: the 24 BE trades (med hold 1h,
friction/|gross| 1.42, 13/24 |gross|<friction) plus SL-flattened micro losers
(med gross −942.50) are a cost-only subpopulation. Predicted benefit: +2–4k
per window — small by construction; ranked last. Failure: removing quick
re-entries breaks the S026 cascade (its winners come from re-entry chains).
Floor: ≥50 micro trades for a lawful test (currently satisfied).

## 8. MEASURED vs STORY

| claim | tag |
|---|---|
| −87,201.39 = Σ(POLICY−B1) USDJPY per-fold differential; both arms net positive | MEASURED (metrics per_symbol_fold_records) |
| 393/310 excursions reconcile to journal nets, friction, force-flats; identity 0.00 | MEASURED (this docket's reconstruction) |
| USDJPY = 99.6% of portfolio spread cost (79,410/79,723) and turnover (3.31B/3.32B) | MEASURED (metrics cost_bill/turnover) |
| Winners held 24h vs losers 7h; SL-flattened losers small/fast (−942.50, 5.5h); 650/703 exits are netting SIG-ENTRY | MEASURED (reconstruction) |
| NY-entry negativity, both arms, all folds | MEASURED (both journals) |
| dct (decision density) does NOT separate W/L (δ=0.028); density-defer family harmful | MEASURED null |
| Cost guard suppressed +274.6k of (B1-path) PnL; those trades reduced dd | MEASURED [derived attribution — B1 path, n=29, one trade 46%] |
| E-floor removed legs worth +428.7k paper / +187.1k realized-entry | MEASURED [derived — paper book ≠ realizable; netting risk] |
| "Missed" weeks' B1 trades netted −101.5k (week+direction coarse pairing) | MEASURED [derived, coarse pairing] |
| Breakevens fee-dominated (friction/|gross| 1.42; 13/24 sub-friction gross) | MEASURED |
| Fold-edge force-flats locked in +160.9k net (2 big winners) | MEASURED (tagged trades) |
| H1–H5 causal stories (why guard/NY/E1/meanrev mechanisms behave as measured) | STORY — mechanisms consistent with the measurements but NOT independently tested; every one is single-path |
| "S026 is the workhorse" (+825k/+822k trigger attribution; +1.64M paper) | MEASURED [derived attribution] |
| MAE/MFE, realized-vol, trend-state separation of W/L | NOT_RUN — fields absent from journals (successor engine) |
| USDJPY fills carried at par from JPY notional (SWAP converted) — absolute-unit caveat | MEASURED convention, flagged |

## 9. What USDJPY data cannot yet answer

The journals record only decision timestamps, fill prices vs mid, cost
components and nightly swap — **no intraday path**. Without MAE/MFE and the
M1 sub-path between fill and close we cannot say whether the large SIG-ENTRY
losers (med −7,509.65, 7h) died slowly or gave back open profits, whether a
1×ATR barrier would have exited earlier (the TB-LABELS design in
`triple_barrier/INVENTORY_AND_DESIGN.md` §2a exists precisely for this and
has not been produced), or whether NY entries were spread-victims (C-cell
p50/p90 are declared bands, not per-fill measurements). **True swap and
commission are not measured against any broker statement** (cost axis
PROVISIONAL_PENDING_COST_AUTHORITY), and the at-par JPY convention means
absolute USD PnL is only meaningful after explicit FX conversion. What
unlocks it: (i) run the TB-LABELS offline producer over the committed M1
panels for these journals; (ii) per-fill quoted-spread capture from the M1
panel instead of C-cell bands; (iii) successor-engine explicit quote→USD
conversion and per-leg exposure journaling (kills the [derived] netting
attribution problem); (iv) an owner cost-authority statement. All four are
analysis-side or successor-engine work — none requires touching the frozen
scored surface.
