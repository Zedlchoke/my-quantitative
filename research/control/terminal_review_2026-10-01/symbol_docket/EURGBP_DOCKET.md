# EURGBP_DOCKET — Symbol docket, group B: EURUSD + GBPUSD (PC12A terminal review 2026-10-01)

Scope: the two M1-panel non-JPY majors in the PC12A scored TEST arms —
EURUSD (legs S013, S046, S009 + VC2-LVNFAIL-EUR) and GBPUSD (legs S002,
S017). ANALYSIS OF EXISTING BACKTESTS ONLY: no new scored run, no engine
execution, no S1, no network.

**HYPOTHESIS-GENERATING ONLY.** The journals analyzed are the *scored TEST
folds* (`stagec/ARMS/{POLICY,B1_ALWAYS_ON}/journal.jsonl`, label
`SCORED-TEST`, window 2022-01-07 → 2025-12-26, 8 folds). Nothing here is
fresh validation; every "rule works" statement below is an in-sample
observation on already-scored folds and must be re-registered before any
GO use. TRAIN diagnostics (`DIAG_MAIN_EUR_EURUSD.json`,
`DIAG_MAIN_GBPA_GBPUSD.json`, `DIAG_MAIN_GBPB_GBPUSD.json`,
`DIAG_MAIN_GBPVC_GBPUSD.json`, label `DISCOVERY-TRAIN-ONLY`) are cited as
priors only, never as edge evidence.

Cycle root (abbreviated `C/`) =
`research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/`.

## Method and reconciliation (how every number below was produced)

- Trades were reconstructed offline from the journals by walking each
  symbol's `NET_ORDER` rows in `seq` order and FIFO-matching open lots
  against closing deltas (the books are netted: multiple legs vote on one
  position; every fill carries at most one non-zero `contribution_units`
  leg, taken as the lot's owner). Per trade: holding time, entry
  hour/session, `gross_mid` (entry/exit `mid_at_fill`), costs decomposed
  as `spread_once + slip_beyond_halfspread + commission` allocated
  pro-rata by matched units, and swap allocated from `SWAP` rows by
  position share between entry and exit (swap is a cost, per
  `C/triple_barrier/INVENTORY_AND_DESIGN.md` §6 "never income");
  `net = gross_mid − spread − slip − commission − swap`.
- **Reconciliation: per-fold sums of reconstructed trade nets match the
  engine's own `metrics.json` `per_symbol_fold_records` cash deltas to
  ≤ $1 on all 32 arm × symbol × fold cells** (EURUSD POLICY +2,315.2,
  B1 +600.1; GBPUSD POLICY +942.4, B1 +718.7). The two force-flats
  (EURUSD POLICY n=2, cost $12.53) and 2–7 fold-edge-carrying exits
  (exit fill dated after the entry fold's window end; tagged in the
  analysis) are inside these numbers.
- **Attribution honesty:** EURUSD is a *netted* multi-leg book — when one
  leg's flatten vote is offset by another leg's keep vote no fill fires
  and the FIFO lot survives, so long-hold "VC2" trades and
  `UNATTRIBUTED` trades (lots created by CLOSE fills with no leg
  contribution — netting rebalances) are book artifacts, not leg
  behavior: POLICY 26 (+$122.6), B1 79 (−$986.4) of EURUSD trades are
  `UNATTRIBUTED`. GBPUSD attribution is direct (S002 trades 08:30 London
  open, S017 15:30–18:30; sessions disjoint; 1–2 unattributed trades).
- Context check (dispatch framing): policy-vs-B1 on these pairs —
  EURUSD POLICY−B1 = **+1,714.2**, GBPUSD = **+223.7**; pooled two-pair
  book POLICY net +3,257.7 / trade-path maxDD $813.8 vs B1 +1,318.8 /
  $2,143.6. Small books: 182–284 trades per arm-symbol, median trade
  nets sit inside the fee band (below). Treat all splits with the
  per-cell n shown.

---

## 1. Eligibility lines for both pairs

Source `C/eligibility/PORTFOLIO_ELIGIBILITY_1200.tsv` (all six legs:
`price_axis=M1_BIDASK_PANEL`, `cost_axis=PROVISIONAL_PENDING_COST_AUTHORITY`,
`mechanizable=YES`, `known_negative_prior=YES`, exploratory_status
`EXPLORATORY_CANDIDATE`, block_reason "rules+data+cost testable on
evidenced panels; ancestry carried as label only"):

| gid | family | title_short / mech_key | horizon | census_verdict | f0_verdict | pit_class | outcome_exposed_label |
|---|---|---|---|---|---|---|---|
| EURUSD-S009 | A-TREND | MACD-histogram exhaustion exit / `macd_divergence_exit` | MULTIWEEK | DISTINCT_TESTABLE | REJECT_NOT_STANDALONE | PRICE_ONLY | F0_INDIVIDUAL_REJECT |
| EURUSD-S013 | B-MEANREV | Bollinger z-score reversion in low-ADX / `bb_zscore_fade` | DAILY | VARIANT_OR_DUPLICATE | n/a | PRICE_ONLY | FAMILY_HISTORY_NEGATIVE |
| EURUSD-S046 | E-SESSION | Turn-of-month flow effect / `monthend_fix_flow` | DAILY | VARIANT_OR_DUPLICATE | n/a | PRICE_PLUS_CALENDAR | FAMILY_HISTORY_NEGATIVE |
| VC2-LVNFAIL-EURUSD | VOLPROF-M1-LVNFAIL | `vc2_lvnfail` | M1 intraday | (class candidate) | n/a | PRICE_ONLY | CLASS_CANDIDATE_ANCESTRY_RHO_LABELLED |
| GBPUSD-S002 | A-TREND | London-Open Direction Persistence / `session_open_cont` | INTRADAY | VARIANT_OR_DUPLICATE | n/a | PRICE_ONLY | FAMILY_HISTORY_NEGATIVE |
| GBPUSD-S017 | B-MEANREV | NY VWAP 2-Sigma Reversion / `vwap_reversion_fade` | INTRADAY | VARIANT_OR_DUPLICATE | n/a | PRICE_ONLY | FAMILY_HISTORY_NEGATIVE |

Exit-law classes (source `C/triple_barrier/INVENTORY_AND_DESIGN.md`
§1 tables): S009 **SIG only** (MACD-H dual divergence, C-D1, O/N+W/E);
S013 **TP (SMA20) + SL (2.8σ)**, C-M1 on an H4 clock; S046 **TIME only**
(window end + max-hold, no SL/TP); VC2 **TP (POC, M1 mid-close crossing)
+ SL (1×ATR60, T-QUOTE touch on the quoted side) + TIME (tmax 240 min +
19:55)**, INTRADAY-FLAT; S002 **SL (range ±2 pip) + TIME (16:00 London)**,
INTRADAY-FLAT; S017 **TP (VWAP) + SL (+1σ)**, exit evaluated only inside
the 15:30–18:30 window.

TRAIN priors (8-fold sums, `DIAG_MAIN_*.json`, HYPOTHESIS-GENERATING
ONLY): EURUSD-S009 +7,207.5 net / 164 entries; S013 +15,824.8 / 623;
S046 +3,150.7 / 240; VC2-EURUSD +758.0 / 141; VC2-GBPUSD **−783.6 / 126
(not selected)**; GBPUSD-S002 +4,681.3 / 1,309; S017 +193.7 / 48. Note the
S009 prior/TEST contradiction (+7.2k TRAIN vs −588 always-on TEST below) —
the E1 activity floor, not the signal, is what kept POLICY out of it.

---

## 2. Outcome tables (per pair, per arm)

`c` = per-pair median round-trip cost of the reconstructed trades.
WINNER: net > +c; LOSER: net < −c; BREAKEVEN: |net| ≤ c (fee-dominated
band). Fold ids 0–7 = test windows
f0 2022-01-07→07-01, f1 2022-07-08→12-30, f2 2023-01-06→06-30, f3
2023-07-07→12-29, f4 2024-01-05→06-28, f5 2024-07-05→12-27, f6
2025-01-03→06-27, f7 2025-07-04→12-26.

### 2.1 EURUSD

| arm | n | net $ | c $ | W/L/B | med hold | LONG net | SHORT net | per-fold net $ (f0..f7) |
|---|---|---|---|---|---|---|---|---|
| POLICY | 182 | +2,315.2 | 3.35 | 92/85/5 | 44 h | +395.7 (59) | +1,919.6 (123) | +999, +1,216, +110, +96, +301, −346, −134, +74 |
| B1_ALWAYS_ON | 250 | +600.1 | 3.37 | 121/119/10 | 40 h | −336.6 (120) | +936.7 (130) | +999, +1,402, −431, +85, −67, +186, −1,696, +123 |

Per-leg (attribution: S009/S013/S046/VC2 via OPEN-fill contribution;
UNATTR = netting rebalances, see Method):

| leg | POLICY n / net $ / med net $ / W-L-B / med hold | B1 n / net $ / med net $ / W-L-B / med hold |
|---|---|---|
| EURUSD-S009 | 1 / −83.8 / −83.8 / 0-1-0 / 24 h | 50 / −587.8 / +1.3 / 25-23-2 / 24 h |
| EURUSD-S013 | 103 / +1,148.3 / −4.3 / 47-53-3 / 36 h | 68 / +731.7 / −5.7 / 31-36-1 / 59 h |
| EURUSD-S046 | 39 / +702.3 / +29.7 / 25-14-0 / 48 h | 27 / +789.6 / +34.4 / 18-9-0 / 72 h |
| VC2-LVNFAIL-EUR | 13 / +425.7 / −2.4 / 6-6-1 / ≤4 h | 26 / +653.0 / −3.0 / 10-13-3 / minutes–hours* |
| UNATTRIBUTED | 26 / +122.6 | 79 / −986.4 |

\* 11/13 POLICY VC2 trades hold ≤ 4 h (median 1 min; 240-min tmax and
~2-h 19:55 flats observed exactly as designed); the few multi-day "VC2"
holds in B1 are netting-carry artifacts, not VC2 behavior.

Reading: the POLICY−B1 gap (+1,714) decomposes into (i) S009 admission
under always-on (−587.8 B1 book; the E1 floor suppressed 123/126 S009
decisions in POLICY), (ii) the fold-6 netting book (B1 f6 −1,696 vs
POLICY −134: ten SHORT lots, mostly UNATTRIBUTED, held 16–531 h through
the 2025 EUR rally), (iii) offset by B1's larger S046 book. S013 is the
workhorse by count but its median trade is −$4.3 (fee band): all its net
is tail — the top-5 EURUSD winners (+$1,389 of +2,315 book net) are three
2022 S013 trades (+389/+260/+225), one netting-rebalance trade (+279) and
one VC2-attributed netting carry (+236, held 337 h — an artifact, §4).

### 2.2 GBPUSD

| arm | n | net $ | c $ | W/L/B | med hold | LONG net | SHORT net | per-fold net $ (f0..f7) |
|---|---|---|---|---|---|---|---|---|
| POLICY | 273 | +942.4 | 2.12 | 125/136/12 | 6.5 h | −440.3 (126) | +1,382.7 (147) | +166, +176, +196, −48, +143, −249, +343, +216 |
| B1_ALWAYS_ON | 284 | +718.7 | 2.12 | 128/138/18 | 6.5 h | −603.3 (134) | +1,322.1 (150) | +166, +176, +196, −48, +143, −351, +199, +238 |

| leg | POLICY n / net $ / med net $ / W-L-B / med hold | B1 n / net $ / med net $ / W-L-B / med hold |
|---|---|---|---|---|---|
| GBPUSD-S002 | 244 / +992.6 / −0.9 / 116-118-10 / 6.5 h | 243 / +932.0 / −1.0 / 115-118-10 / 6.5 h |
| GBPUSD-S017 | 28 / −47.6 / −2.9 / 9-17-2 / minutes* | 39 / −212.9 / −1.7 / 12-19-8 / minutes* |
| UNATTRIBUTED | 1 / −2.5 | 2 / −0.3 |

\* S017 hold distribution (POLICY): 15/28 trades close within 1 minute of
entry; 4 carry overnight (22–64 h). Fold-level S017 (B1): f0 −105.5, f1
−44.7, f2 −5.5, f3 +64.5, f4 +45.2, f5 −103.6, f6 −85.9, f7 +22.5 —
POLICY's E1 floor cut exactly the f5–f7 tail (see §6 R-G1).

Reading: GBPUSD ≈ a one-leg book (S002 = 89% of trades) with a small
bleeding satellite (S017). The policy-vs-B1 difference (+223.7) is
entirely S017 admission differences in f5–f7 plus a $144 f6 S002 netting
interaction. Both arms' books are SHORT-heavy profitable (2022 USD trend;
see §8 for the regime caveat).

---

## 3. Entry-time feature contrast (DECISION-row fields only)

Available at decision time in these journals: `onoff_features.decision_count_trailing`
(dct), `portfolio_state.n_eligible`, family/leg, fold, direction vote.
**Everything else — vol, spread regime, calendar state beyond S046's own
window, cross-pair state — is [NR] (not recorded) in the DECISION rows.**
Medians, WINNER vs LOSER population per arm (n = trades with the field
resolvable through the prev-row chain):

| feature | EUR POLICY | EUR B1 | GBP POLICY | GBP B1 |
|---|---|---|---|---|
| decision_count_trailing | 67.5 (n78) vs 81.0 (n74) | 57 (83) vs 56 (81) | 220 (125) vs 210 (135) | 214 (127) vs 206 (137) |
| portfolio n_eligible | 4 vs 4 | 4 vs 4 | 2 vs 2 | 2 vs 2 |
| entry_hour | 4 vs 15 | 4 vs 12 | 8 vs 9 | 8 vs 9 |
| hold_h (post-hoc) | 52 vs 26 | 36 vs 44 | 6.5 vs 5.0 | 6.5 vs 5.1 |
| LONG W/L — SHORT W/L | 26/32 — 66/53 | 53/61 — 68/58 | 58/62 — 67/74 | 61/64 — 67/74 |
| session W/L (TOKYO/LONDON/OVERLAP/NY) | 49/27 — 7/5 — 0/0 — 27/42 | 68/49 — 11/7 — 0/0 — 25/43 | 0/0 — 116/118 — 0/0 — 8/15 | 0/0 — 115/118 — 0/0 — 11/17 |

Contrasts worth carrying forward (all hypothesis-grade):
- **EURUSD entry hour**: winners enter at hour 4 (S013's 04:00 H4 vote /
  S046's 00:00–04:00 window) vs losers at hour 15/16 (NY); hour 16 is the
  single worst entry hour on both arms (POLICY −$264.2 n44, of which 40
  are S013's 16:00 H4 vote; B1 −$210.4 n39) and hour 12 is worst on B1
  (−$826.7 n20 — but 13/20 are UNATTRIBUTED netting trades, so the B1
  hour-12 cell is book-artifact-heavy; the POLICY hour-12 cell is −$231.7
  n13, 10 of them S013). Tokyo-session entries W/L 49/27 (POLICY) — the
  only session with a clear winner majority.
- **EURUSD holding asymmetry flips between arms** (POLICY winners run
  2× longer; B1 reversed) — a netting artifact of B1's long UNATTRIBUTED
  book, not a stable feature.
- **GBPUSD**: nothing at decision time separates winners from losers
  (dct 220 vs 210, n_eligible identical); only entry hour 8 vs 9 within
  S002 (hour 8: n147 +$839.1 W/L 71/67; hour 9: n97 +$153.5 W/L 45/51)
  and direction (regime-linked, §8) move the needle.

---

## 4. Exit-mechanics effects per exit class

Exit class from the reason code on the decision row chained to the
closing fill (`prev_row_sha256`). Net $ per class, POLICY arm (B1 in
parentheses where materially different):

**EURUSD-S013 (TP SMA20 / SL 2.8σ, H4 clock)**
- SL `M1_STOP_HIT`: 49 trades, −$1,528.8, med gross −$25.9, med hold 12 h
  (B1: 24, −$1,087.0).
- TP `Z_TARGET_SMA20` + `M1_TARGET_HIT`: 35, +$1,866.8, med gross +$48.7,
  med hold 68 h.
- TIME `MONTH_TURN_*` (S046-driven closes of S013 lots): 15, +$618.6.
- Shape: stops fire 3× more often per unit time and cost 2× the median TP
  win; the leg survives on tail TPs + benign time exits.

**EURUSD-S046 (TIME-only window exits)**
- `MONTH_TURN_END`/`CONTINUATION`: 27, +$38.9 combined net via 19/8
  trades (+138.4 / −99.6); entries verified on day-of-month 29–03
  (design-consistent).
- The leg's real PnL arrives through *other* legs' closes of its lots
  (`H4_Z_FADE` SIG exits: 12 trades +$962.4; `TP_POC` +$153.6) — i.e.
  turn-of-month entries held beyond the window by netting captured the
  2022 trends. TIME-only + no stop = the window exit itself is PnL-neutral.

**VC2-LVNFAIL-EURUSD (VOLPROF; TP POC on mid-close crossing, SL T-QUOTE
quoted-side touch, TIME tmax/19:55)**
- POLICY: `TP_POC` 7 trades −$32.1 (median hold 1 min — the POC target is
  hit immediately on entry-minute retests and pays ~0 after costs);
  `TIME_STOP_TMAX` 2 → +$107.6 (240-min tmax observed exactly);
  `TIME_STOP_FLAT_1955` 2 → +$75.4; `M1_TARGET_HIT` (S013-close of VC2
  lots) 2 → +$274.7.
- B1 adds the true touch-stop class: `ATR_STOP` (T-QUOTE) 2 trades,
  −$44.2, hold ≤ 36 min — quoted-side-touch stops are rare and small;
  `TP_POC` 9 → +$269.6 (but median hold 39.9 h = netting artifacts
  inside).
- Net: VC2's own barrier machinery (TP fast/flat, SL touch, tmax) is
  cost-light (med trade cost $1.53) and its TEST book is positive in both
  arms (POLICY +425.7 / 13; B1 +653.0 / 26) with the wins coming from
  *non*-POC exits (tmax/flat/other-leg closes), not from the POC target
  itself.

**GBPUSD-S002 (SL range ±2 pip + TIME 16:00 London)**
- TIME `LONDON_1600_EXIT`: 177/244 = 72.5% of trades, +$3,852.9, avg
  +$21.8, med +$16.0, med hold 6.5 h.
- SL `M1_STOP_HIT`: 66/244 = **27.0% stop rate**, −$2,864.6, med net
  −$42.9 (med gross −$40.6 vs med cost $2.11), med hold 4.0 h.
- The whole GBPUSD edge is "survive to 16:00": one stopped trade erases
  ~2.7 median time-exit wins; the ±2-pip range stop is the dominant
  loss mechanism of the pair.

**GBPUSD-S017 (TP VWAP + SL +1σ, window-locked)**
- SL `M1_STOP_HIT`: 20 → −$220.6 (B1 26 → −$323.4); TP
  `M1_TARGET_HIT`: 6 → +$243.9 (B1 10 → +$285.9); the remaining exits are
  1-minute round trips inside the band (15/28 POLICY trades close within
  60 s, nets −$6..−$1) and 4 overnight carries (up to 64 h; includes the
  −$164.9 worst loss). Stop:target frequency 20:6 with near-symmetric
  magnitude = structurally negative.

**EURUSD-S009 (SIG-only)**: the single POLICY trade (−$83.8) and B1's 35
`MACDH_DUAL_DIVERGENCE_EXIT` closes (−$560.8) show the signal exit
realizing losses on B1's admitted book — evidence the E1 floor, not the
exit, carried POLICY.

---

## 5. Cost anatomy

Per arm-symbol totals over all reconstructed trades (reconciles with
`metrics.json` `per_symbol.cost_bill_totals_usd`):

| book | gross_mid $ | spread_once $ | slip $ | commission $ | swap $ | total cost $ | net $ | c (med) $ | c p90 $ | turnover |
|---|---|---|---|---|---|---|---|---|---|---|
| EUR POLICY | 3,141.4 | 77.7 | 72.8 | 137.7 | 538.0 | 826.2 | 2,315.2 | 3.35 | 9.54 | 3.9 M |
| EUR B1 | 1,991.3 | 125.4 | 100.6 | 190.2 | 975.0 | 1,391.1 | 600.1 | 3.37 | 12.51 | 5.4 M |
| GBP POLICY | 1,533.4 | 235.0 | 109.2 | 241.8 | 5.0 | 591.0 | 942.4 | 2.12 | 2.49 | 6.9 M |
| GBP B1 | 1,333.8 | 242.6 | 113.6 | 251.9 | 7.0 | 615.0 | 718.7 | 2.12 | 2.49 | 7.2 M |

- **EURUSD's dominant cost is swap** (65% of POLICY cost bill): charged
  on 133/182 trades, $2–3/night per 10k lot; B1's longer netting carries
  nearly double it ($975). GBPUSD is structurally intraday-flat: $5–7
  total swap — the O/N exposure difference between the pairs *is* the
  cost-structure difference.
- **GBPUSD's dominant costs are spread + commission** (81% of bill) —
  273–284 round trips of a ~$0.60–0.70 crossing.
- **Session spread structure** (median `spread_once_usd` per fill by
  fill-time session, POLICY): EURUSD LONDON $0.20 / TOKYO $0.15 /
  OVERLAP $0.15 / NY $0.15 / LATE(21–24h) **$4.40 (n=3)**; GBPUSD LONDON
  $0.45 / OVERLAP $0.35 / NY $0.40. With the fixed U3 non-event slip
  ($0.20/fill), the *trade-level* London-vs-NY gap visible in
  `spread_pips_charged` terms is small (≤ $0.25/round trip); the real
  hazard is the rollover-window fills (3 EURUSD late fills at ~29× the
  normal spread) — an n=3 tail, not a systematic session penalty.
- All 910 EUR/GBP fills are tier `C1` and `U3_NON_EVENT` — no
  event-window (rollover/Sunday) slippage was sampled by these books, so
  the declared C2/C3 bands are untested by this data (§9).
- Cost-relative outcome scale: c = 3.35 (EUR) / 2.12 (GBP) vs median
  |net| of BREAKEVEN trades $2.77 / $0.93 — the fee band is narrow;
  "BREAKEVEN" here means genuinely fee-dominated, not cost-blind noise.

---

## 6. Rule-sensitivity tests (journal-computable off/on rules)

Method: suppress the trades a candidate rule would have denied (entry-side
recomputation; exits unchanged — this measures *admission* effects only,
not exit-law changes). Report: suppressed net (its sign = whether the rule
helps on this book), winners cut (missed-profit) vs losers cut
(avoided-loss), trade-path maxDD of the pair book before/after, and fold
provenance of the suppressed net. All numbers TEST-fold in-sample;
per-fold cells are 1–15 trades deep — read the fold column as consistency
check, not as independent power.

**R-E1 — EURUSD S009 admission (what E1 floor buys).** B1 S009-only book:
50 trades, −$587.8 (f0 −84, f1 +65, f2 −496, f4 +65, f5 −55, f6 −70, f7
−12). POLICY blocked 123/126 S009 decisions (E1 "trailing 26w < 3"); the
missed set (B1 S009 entries where POLICY had no fill: 49 trades) nets
**−$504.0 → the floor avoided ~$500 of loss**, concentrated in f2, with
25 c-winners cut (+$683.8 missed-profit) against 22 c-losers avoided
(−$1,183.7).

**R-E2 — EURUSD entry-hour gate: no new entries at 12:00 / 16:00 UTC.**

| book | suppressed n / net $ | winners cut / missed $ | losers cut / avoided $ | maxDD all → rule | suppressed net by fold $ |
|---|---|---|---|---|---|
| POLICY | 57 / −495.9 | 17 / −901.4 | 40 / +1,397.3 | 878 → 387 | +5, +208, +91, −179, −151, −97, −368, −4 |
| B1 | 59 / −1,037.1 | 21 / −1,440.7 | 38 / +2,477.7 | 2,277 → 977 | +5, +163, −128, −19, −398, +274, −1,083, +150 |

Positive on both arms (6/8 folds negative-suppression each), halves the
pair-book DD; the two folds it hurts (f0–f1, and B1 f5/f7) are the
honest cost. Mechanism: hour 12 = S013's H4 vote inside the London/NY
liquidity handover; hour 16 = NY-open spread widening + S013's 16:00
vote — both cost-visible in §5.

**R-E3 — EURUSD VC2 admission (opportunity cost of the E1 floor).**
POLICY blocked 44 VC2 decisions; the B1 VC2 book is +$653.0 over 26
trades (f0 +194, f1 +231, f2 −23, f3 +3, f4 +63, f5 +337, f7 −153) and
the strictly-missed subset (13 trades where POLICY blocked) nets
**+$227.4 of missed-profit**. Same floor, opposite sign vs R-E1 — the E1
activity floor is not free on this pair.

**R-G1 — GBPUSD S017 off entirely.** POLICY: suppress 28 trades / net
−$47.6 (winners cut $266.8 / losers avoided $314.4), maxDD 676 → 502;
fold split −105, −45, −5, +65, +45, −2. B1: 39 trades / −$212.9 (310.1 /
523.0), folds −105, −45, −5, +65, +45, −104, −86, +23. Positive on both
arms, 6–7/8 folds — but each fold cell is 1–8 trades.

**R-G2 — GBPUSD S002 first-hour-only (entries at hour 8 only).**
Suppresses hour-9 book: n97 / **+$153.5 net cut** (winners missed $1,811.5
vs losers avoided $1,658.1), folds +157, +182, +30, −184, +7, −271,
+214, +19 — fails (removes profit on 5/8 folds). Not a rule; the hour-8
concentration noted in §3 does not survive as an admission filter.

**R-G3 — GBPUSD short-only.** Suppress LONG: −$440.3 removed, maxDD 676 →
221; but fold split of suppressed net (−170, −364, **+193**, −131, +73,
−136, +58, +37) shows LONG was positive in 4/8 folds — the rule is a
2022-regime artifact, rejected as in-sample regime fitting (kept here
because it is the largest single DD lever visible in the pair).

**R-E4 — EURUSD short-only.** POLICY: suppresses +$395.7 of LONG profit —
fails outright. (B1: saves $336.6 — again the B1-only netting book, not a
stable effect.)

---

## 7. Falsifiable hypotheses (ranked by mechanistic plausibility)

All require fresh registration + TRAIN-first re-measurement before any
scored use; all are entry-side or governance-side except H-G2 which names
the TB-EXIT-OVERLAY lane.

**H-E1 (EURUSD, governance) — keep and codify the E1 activity floor for
signal-exit-only legs.**
Trigger/measurement: S009 always-on TEST book −$587.8 over 50 trades, ≤0
in 5/7 traded folds (worst f2 −$496); R-E1 avoided-loss ≈ +$504 (missed
set −$504.0 over 49 trades).
Rationale: a MULTIWEEK SIG-only exit leg with <3 decisions/26w has no
adaptive information to size against; the TRAIN prior (+7,207) does not
transfer (family F0_INDIVIDUAL_REJECT, known_negative_prior YES).
Predicted benefit: ~+$125/yr-equivalent on this pair and removal of the
worst B1 fold-6 carry channel.
Failure condition: any future fold where the admitted S009 book exceeds
+$200 while the floor is blocking, or a registered TRAIN re-run where the
floor's suppressed book is net-positive ≥ +$500.
Sample floor: ≥30 admitted trades per evaluation window (current
admitted n=50 is minimal; per-fold cells are NOT sufficient).

**H-E2 (EURUSD, admission) — deny new EURUSD entries at 12:00 and 16:00
UTC.**
Trigger/measurement: R-E2 — suppressed net negative on both arms (−496
POLICY / −1,037 B1), 6/8 folds each, pair-book maxDD 878→387 / 2,277→977.
Rationale: mechanism named (H4-clock meanrev voting inside the
London/NY handover and the NY-open spread widening; cost-visible in §5's
session spread medians and in S013's stop-heavy 12–16h entries).
Predicted benefit: +$500–1,000 per 4y on this pair, ~50% pair-DD
reduction.
Failure condition: the two positive-suppression folds (f0, f1) widening —
if the rule's suppressed book turns net-positive in ≥3/8 folds on a fresh
TRAIN-fold replication, or the DD reduction fails to reproduce outside
2022- folds, kill it.
Sample floor: ≥40 suppressed trades per arm replication (current 57–59).

**H-E3 (EURUSD, admission) — admit VC2-LVNFAIL-EURUSD (remove the E1
floor for POOL_B_VOLPROF legs).**
Trigger/measurement: R-E3 — missed-profit +$227.4 (strictly blocked
subset); full B1 book +$653.0 / 26 trades, positive 6/8 folds, med trade
cost $1.53, exits design-faithful (§4).
Rationale: VOLPROF legs are high-frequency vs the 26w activity window —
the E1 floor is calibrated for daily/weekly clocks and mis-fires here;
mechanism is cost-light intraday barriers, no O/N swap.
Predicted benefit: +$150–650/4y on this pair at negligible DD cost (not
measurable per-fold at current n).
Failure condition: the f7 sign (−$153) repeating — if a fresh replication
shows ≥3/8 negative folds or the POC-touch exit quality degrades below
breakeven ex-costs, reject. Ancestry label
(`CLASS_CANDIDATE_ANCESTRY_RHO_LABELLED`) must stay a label, never an
input (directive #2).
Sample floor: ≥50 trades per replication (current 26 — under-powered;
this hypothesis is ranked below H-E1/H-E2 for that reason).

**H-G1 (GBPUSD, retirement) — retire GBPUSD-S017 (or floor it to
≥3 decisions/26w, which the E1 floor already approximates).**
Trigger/measurement: R-G1 — −$47.6 (POLICY 28 trades) / −$212.9 (B1 39),
negative both arms, 6–7/8 folds; exit structure 20 SL : 6 TP with
15/28 trades closing within 1 minute (§4) — the +1σ stop is inside the
entry bar's noise for an M1 VWAP fade.
Rationale: mechanistic (stop geometry vs instrument noise at the decision
clock), not just PnL sign.
Predicted benefit: +$50–210/4y and pair maxDD 676→502.
Failure condition: a TRAIN-fold replication showing the window-locked
TP:SL ratio reverting to ≥40% TP share, or the overnight-carry subset
(the +$71/+$129 winners) being the majority of gross.
Sample floor: ≥50 trades per arm book (current 28–39).

**H-G2 (GBPUSD, exit law — needs the registered TB-EXIT-OVERLAY lane,
not journal-recomputable) — S002's ±2-pip range stop destroys ~half the
gross edge; test a wider initial stop (e.g. ±3 pip) as a TB-EXIT-OVERLAY
node per `C/triple_barrier/INVENTORY_AND_DESIGN.md` §3 (B-MEANREV family
node values, no per-leg tuning).**
Trigger/measurement: 27.0% of S002 trades stop out at med −$42.9 gross
while the 72.5% surviving-to-16:00 book earns med +$17.9 gross (§4); the
leg is the whole GBPUSD book, so stop geometry ≈ pair geometry.
Predicted benefit: stop rate below ~20% at unchanged time-exit PnL ⇒
+$400–800/4y on the pair.
Failure condition (dual-side law): widened-stop trades that still exit at
16:00 must not systematically carry larger 16:00 losses than the avoided
stops (profits-cut-early/losses-avoided accounting per §2b of the design
doc); if post-stop M1 paths (TB-LABELS) show stopped trades would have
recovered to ≥0 by 16:00 in <50% of cases, the stop is doing its job —
reject.
Sample floor: ≥150 trades per node (S002 supplies 244/book; feasible).

Explicitly NOT proposed: direction gates (R-G3/R-E4 — regime artifacts,
LONG positive in 3–4/8 folds on both pairs) and S002 hour-8-only
(R-G2 — removes profit).

---

## 8. Measured-vs-story table

| story (going in) | measured (this docket) | verdict |
|---|---|---|
| "These pairs were net-neutral in policy-vs-B1 (EURUSD +1,714, GBPUSD +224 harm)" | Confirmed small: EUR +1,714.2, GBP +223.7; but EURUSD's gap is *concentrated*: E1-S009 save (~+500), B1 fold-6 long-carry −1,696 vs POLICY −134, offset by B1's better f1; GBPUSD's gap is S017 admission in f5–f7 (~+$102–224) | Refined, not overturned |
| "S013 is the EURUSD edge" (TRAIN +15.8k) | S013 carries the trade count (103/182) but median net −$4.3; book net lives in 5 tail trades (+$1,389 of +2,315) and in S046/VC2 survivors; SL:TP asymmetry −1,529 (49) vs +1,867 (35) | Half-true: tail-dependent workhorse |
| "S009 rejected at F0 but implemented anyway" | 1 POLICY trade in 4 years (E1 floor); always-on TEST book −$587.8 despite +$7.2k TRAIN prior | Floor carried the pair; prior did not transfer |
| "S002 London-open persistence is the GBPUSD edge" | The *persistence direction* is not what pays: LONG −$440 vs SHORT +$1,383 (regime), and within-direction W/L ≈ even (116/118). What pays is surviving to the 16:00 time exit (+$3,853) vs the ±2-pip stop (−$2,865) | Mechanism mislabeled: it is an exit-geometry book |
| "S017 adds a meanrev satellite" | −$47.6 / −$212.9 both arms; 1-minute stop-outs 15/28; TRAIN prior was only +$193.7/48 entries | Satellite bleeds; retire candidate |
| "VC2 class candidates are ancestry-tainted, keep floored" | VC2-EURUSD TEST +$426–653, positive 6/8 folds, cost-light, design-faithful exits; VC2-GBPUSD TRAIN −$784 (not selected — correctly) | Pair-specific: floor helps GBP, costs EUR |
| "EURUSD costs are spread-dominated like GBPUSD" | EURUSD cost bill is 65% swap ($538–975); spread+slip are trivial ($150–226) | Overturned for EUR; true for GBP |
| "Fold-edge force-flats distort these books" | 2 force-flats (POLICY EUR, $12.53), 0 GBP; 2–7 trades exit after fold-window end; per-fold reconstruction matches engine books ≤$1 | Non-issue here |

---

## 9. What these pairs' data cannot answer + unlocks

1. **Intrabar exit ordering (did the stop touch before the target?)** —
   journals record fills, not paths. S013's 2.8σ stops, S017's 1-minute
   stop-outs and H-G2's stop-widening all hinge on it. Unlock:
   TB-LABELS offline labeling (design already frozen,
   `C/triple_barrier/INVENTORY_AND_DESIGN.md` §2a; M1 bid/ask panels
   exist for exactly these pairs).
2. **True per-leg books on EURUSD** — the netted FIFO book mis-assigns
   netting transfers (26–79 UNATTRIBUTED trades; B1 "VC2" lots held
   days). Unlock: the per-leg minus-one/plus-one arms already on disk
   (`C/diagnostics/stagec/ARMS/{POLICY,B1}_MO_EURUSD-S{009,013,046}` and
   `*_MO_VC2-LVNFAIL-EURUSD`, each with journal+metrics) were not
   analyzed in this docket and are the direct attribution evidence.
3. **Whether the S009 TRAIN→TEST sign flip is regime or overfit** —
   TRAIN episodes (`episodes_serialized`) carry direction/timestamps but
   no per-episode PnL, so the TRAIN book cannot be decomposed the way
   TEST was here. Unlock: extend the diag serializer with per-episode
   net (TRAIN-only, no engine change to scored paths).
4. **Event-window cost behavior** — all 910 fills are C1/U3_NON_EVENT;
   the 3 late-night EURUSD fills ($4.40 spread) are n=3. The declared
   C2/C3 bands are untested by these books. Unlock: none without new
   fills; a stress re-price (×1.5/×2.0 tiers per FILL_ACCOUNTING_SPEC
   §5) is registerable but was not run here.
5. **Pooled-portfolio DD attribution** — my DD numbers are per-pair
   trade-path DD; the pooled 12-asset book's DD interleaving and heat
   interactions are only visible in `metrics.json.weekly_equity` /
   `heat_events_by_symbol`, which do not decompose by pair contribution.
   Unlock: pooled weekly equity re-aggregation from the same journals
   (analysis-only).
6. **Sample size for every hypothesis in §7** — 4 years × 8 folds gives
   13–50 trades per leg-arm book and 1–15 per fold cell; nothing here
   reaches an acceptance-grade n. Unlock: only time or the registered
   replication lanes (TRAIN-fold replicas, MO arms, TB overlays) — never
   re-scoring the same TEST folds.

— end of docket —
