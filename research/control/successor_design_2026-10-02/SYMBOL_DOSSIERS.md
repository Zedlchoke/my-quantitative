# SYMBOL_DOSSIERS — successor_design_2026-10-02

Per-symbol dossier consolidating: the 2026-10-01 dockets (A=USDJPY, B=EURUSD+GBPUSD,
C=USDCAD/AUDUSD + 7 blocked), this session's solo-arm census, and the
DAILY-EXPLORATORY-V1 result. All TEST-fold numbers are **exposure-labeled,
hypothesis-generating**. Breakeven law: per-pair median round-trip cost c
(W > +c, L < −c, B otherwise). USDJPY magnitudes are at-par journal units.

Legend for attribution tags: `trig` = portfolio entry-trigger attribution
(dockets); `pfold` = in-portfolio leg attribution (`paper_fold_net_by_leg`);
`solo` = single-leg arm. **The three are not interchangeable** (census §5).

---

## 1. USDJPY — the whole portfolio in one symbol

**Book:** 6 legs (S002, S003, S014, S023, S026, VC2-JPY); 99.6% of portfolio
turnover (3.31B/3.32B) and spread cost; 57.8% of time in position (POLICY
heat events) `[M]`.

**Round trips / outcomes (docket A, n=703 pooled):** W 292 / L 387 / B 24 —
losers outnumber winners in EVERY fold; the book lives on winner magnitude
(med W gross +9,404 vs L −7,036; ratio 1.34). Winners hold 24h vs losers 7h
(median); 650/703 excursions end on a netting SIG-ENTRY, not their own
TP/SL; real SL-flattened losers are small/fast (−942.50 med, 5.5h).

**Session/direction anatomy:** NY-session entries are the ONLY
sign-consistent negative bucket in BOTH arms (POLICY −281,460 n=91; B1
−83,684 n=74; pooled long×NY −384,747), sign-stable across all 8 folds;
London longs +972,340. dct (decision-density) does NOT separate W/L
(Cliff's δ=0.028 — honest null).

**Per-leg, three attributions side by side `[M]` (TEST folds):**

| leg | trig POLICY / B1 | pfold (B1) | solo B1 | solo POLICY | reading |
|---|---:|---:|---:|---:|---|
| S026 pdhl_stop_sweep | +825,244 / +822,233 | +1,637,143 | **+9,203** (DD 299,849) | +9,203 | the cascade only pays blended with the trend inventory it re-enters around; solo it is a coin-flip churn with huge DD |
| S014 rsi2_fade | −222,301 / −319,604 | +34,984 | **+109,448** (DD 58,494) | +109,448 | OPPOSITE SIGN across attribution laws: solo-positive, portfolio-attributed-negative. Retire hypothesis must be tested as portfolio-minus-S014, never from any one attribution |
| S003 tsmom monthly | no POLICY entries / B1 n=2 → −5,465 | +225,631 | +216,221 (DD 478,226) | +216,221 | the trend core (solo economics are its real signature); E1 floor blocked it in POLICY (37 blocks) — trig n is too small to read |
| S023 vol_regime_breakout | B1 n=1 → +107,140 | +230,099 | +57,454 (DD 125,153) | −50,550 (2 fills) | E1 floor blocked it in POLICY (16 blocks); realized entries in B1 +187,084 |
| S002 ma_regime_gate | no POLICY entries / B1 n=7 → +68,820 | −24,269 | **−248,990** (DD 487,954) | +137,883 (34 fills) | solo-negative always-on; POLICY's E1 floor kept only 34 fills which made +137,883 — the floor was load-bearing here |
| VC2-LVNFAIL-JPY | B1 +16,589 | −2,805 | −385 | +280 | noise-level |

**Blocked (POLICY):** BLOCKED_FLOOR 154 USDJPY rows (S002 79, S003 37, S023
16, VC2-JPY 22); DEFERRED_COST_GUARD 331 (S026 299); SUPERMAJORITY 706 (S026) +
186 (S014) + 55 (S002) + 22 (VC2) + 20 (S003) `[M]`.

**Costs:** spread+slip = 96.4% of friction; swap/commission rounding errors;
breakevens are fee-dominated (friction/|gross| 1.42 median, 13/24
sub-friction gross). C2 roll cell 2.1/7.4 pips (Mon–Thu), C3 Sunday
11.0/22.0 `[M: DECLARED bands]`.

**Cannot answer:** MAE/MFE, entry-bar quoted spread, intrabar TP/SL order
(no M1 sub-path in journals — TB-LABELS producer not yet run); any
portfolio-minus-leg counterfactual `[NR]`.

## 2. EURUSD — small book where the floor was the win

**Book:** 4 legs (S013 workhorse 103/182 POLICY trades, S046, S009,
VC2-EUR). POLICY +2,315.24 / B1 +600.97 (policy HELPED +1,714.26).

**Outcomes:** POLICY 92W/85L/5B; B1 121W/119L/10B; median trade sits inside
the fee band (c=$3.35). Long −396/+937 short mix flips by arm (netting
artifacts). S013's net is 5 tail trades (+1,389 of +2,315 book).

**Mechanism notes:** hour 16 worst entry hour both arms (POLICY −264 n44);
hour 12 worst on B1 (−827 n20, 13/20 netting artifacts); Tokyo entries only
session with winner majority (49/27 POLICY). Swap = 65% of cost bill (133/182
trades charged, $2–3/night/10k). E1 floor suppressed S009 (123/126
decisions) → avoided ≈ $504; the same floor cost VC2-EUR admission (+$227
missed) — pair-specific. S009 solo (always-on) −2,127.77 confirms the floor
read; S013 solo +1,731.42; S046 solo +79.62; VC2-EUR solo +75.30 `[M]`.

**Cannot answer:** intrabar stop/target ordering (S013 2.8σ SL); S009
TRAIN→TEST sign flip (regime vs overfit); event-window costs (all fills
C1/U3 non-event).

## 3. GBPUSD — exit-geometry book with a bleeding satellite

**Book:** S002 89% of trades + S017. POLICY +942.44 / B1 +718.75 (policy
helped +223.70). W/L ≈ even within direction (116/118) — edge is exit
geometry, not direction calling.

**Mechanism notes:** S002's entire edge = "survive to 16:00 London exit":
TIME exits 177/244 trades +$3,853 vs ±2-pip stop 66/244 −$2,865 (27% stop
rate; one stop erases 2.7 median time-exit wins). S017: 20 SL : 6 TP,
15/28 close within 1 minute — stop inside entry-bar noise; both arms
negative (−47.6/−212.9); solo confirms (−318.71 / −95.02) `[M]`.
SHORT-heavy profitable in 2022 (regime-linked; direction gates rejected as
regime artifacts). Costs spread+commission 81% (intraday-flat; $5–7 total
swap).

**Cannot answer:** whether ±3-pip stop improves S002 (needs TB-LABELS
intrabar paths + registered TB-EXIT-OVERLAY identity); per-fold cells are
1–8 trades deep — nothing here reaches acceptance-grade n.

## 4. USDCAD + AUDUSD — TRAIN-only, cost-killed before scoring

9 diagnosed legs, ALL typed COST_DOMINATED at ×2.0 (zero floor kills); at
×1.0 only USDCAD-S011 (+111.72) and S091 (+313.61) survived and both died at
×2.0 `[M: docket C]`. Structural: C2 cell nearly empty (21:00 bar 1.4% of
weekday rows USDCAD); 20:00-bar absence defers Friday fills to C3 Sunday
reopen (USDCAD 39/286 = 13.6%, AUDUSD 87/286 = 30.4% at 2.2× the rate,
4.8× the C1 p90 spread); swap events outnumber fills up to 353:1 on
hold-heavy legs (S002 AUD 1,058:3) under the never-income DECLARED
calendar. No scored journals exist → **no trade-level inference**;
hypotheses H-C1/H-C2/H-C3 parked on named data unlocks. A successor
re-attempt needs a changed mechanism axis (TERMINAL Q-10) — same-axis
retries are banned.

## 5. The 7 data-blocked assets — slots, not conclusions

NZDUSD, USDCHF (D1 panels frozen 2020-10→2026-09, PIT NOT_RUN, costs
NOT_RUN); XAUUSD (basis vs TD archive measured p50 3.25bps but thresholds
UNFROZEN, lag ASSUMED); XAGUSD (widest spreads p50 10.35bps; **zero
consumer legs**); BRENT/WTI/NATGAS (no certified roll chain — FLAT by
authority until owner names a chain source). All unlocks are OWNER-ONLY
(statement export / PIT declaration / threshold freeze / chain naming).
**These are waiting slots in the architecture — carrying any spot-FX
conclusion onto them is prohibited.** NQ/ES/CL/NG/GC/SI/6E/6J/6B/6A
(futures index/commodity/CD legs named by the owner) belong to the same
class: no admissible panel on file ⇒ FLAT-by-authority slots.

## 6. DAILY cohort (DS-03/DS-05) — negative, closed

61 decisions / 4y (< 100 floor): DS-03 fires 34, DS-05 27; every arm
net-negative at every tier; both legs REDUCE slate net (P-MW deltas −355.40
/ −732.67); floors NOT_RUN_THIN in 4 of 16 leg-fold pairs. Lesson P-35:
daily clock too sparse for these corpus rules — floor geometry is a DESIGN
CONSTRAINT (need faster clock or richer signals), not a tuning invitation.

## 7. Cross-symbol summary for the designer

| symbol | journal n (round trips, both arms) | net POLICY/B1 | where its risk lives | inference quality |
|---|---:|---:|---|---|
| USDJPY | 703 | +600,083 / +687,284 (par) | NY longs, guard defers, netting size-path | good (but attribution-law conflicts) |
| EURUSD | 432 | +2,315 / +601 | swap carry, S013 tail dependence | small-n |
| GBPUSD | 557 | +942 / +719 | S002 stop geometry, S017 bleed | small-n |
| USDCAD/AUDUSD | 0 scored | TRAIN-only | cost structure (C2/C3/swap) | none (TRAIN-only) |
| 7 blocked + futures slots | 0 | FLAT-by-authority | — | none |

— end dossiers —
