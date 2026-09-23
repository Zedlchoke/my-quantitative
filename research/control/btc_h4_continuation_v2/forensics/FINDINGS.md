# FINDINGS — FORENSICS_P1, cycle BTC-H4-CONTINUATION-V2

Arm: `PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION` (BTCUSDT-PERP H4, Binance
Vision panel, manifest `3f1a6687…`). Rebuild executed by
`forensics_driver.py` calling the FROZEN PSV1 engine verbatim
(`cells.load_btc_h4` → `books.l2_run_book` → `books.l2_fills_from_book` →
`accounting.run_accounting`), PSV1 trees read-only.

**Reconciliation gate §1.1: PASS** — measured == committed PSV1 targets with
`max_rel_err = 0.0` at ALL THREE tiers (13 checks per tier: entries/exits/
trades, exit reasons, 4 fold nets, net/gross/fees/funding; tier files
cross-checked against the ledger). The ledger below is therefore the
predecessor's own record, not an approximation.

Lock disclosure: run completed in `LIGHT_EXEMPTION_DISCLOSED` mode after the
machine-wide heavy lock stayed HELD_PROVEN (foreign worker
`CRYPTO-HISTORICAL-REPLICATION-3F-V1/data-staging`, pid 77456) through the
original bounded window and 2 renewed attempts 90 s apart. Measured
`resource.getrusage`: wall 0.424 s, CPU 0.370 s, peak RSS 121,962,496 bytes —
far inside the plan §8 ceilings (<5 min CPU / <2 GB). See
`data_receipt.json`.

Everything below is POST-HOC S0 DISCOVERY (plan header): descriptive, never
OOS, never validation. No parameter is recommended anywhere; no threshold was
scanned; the k=6 constant and the immediate-stop counterfactual are
DESCRIPTIVE-ONLY (plan §1.2/§1.3/§2).

---

## (a) MEASURED FACTS

### A.1 Rebuild @1.0x (identical at 1.5x/2.0x up to costs — reconciliation.json)

| quantity | measured (== PSV1 target) |
|---|---|
| net @1.0x | +177,691.82015965082 USD |
| F1 / F2 / F3 / F4 net | +140,843.2837184764 / −46,959.98560513256 / +133,820.82597620029 / −50,012.3039298933 |
| gross / fees / funding @1.0x | +204,721.76063992942 / +23,317.1602728789 / −3,712.7802073988382 |
| trades | 86 entries / 86 exits; 79 DONCHIAN_STOP + 7 GATE_INACTIVE (0 FOLD_END, 0 MAX_HOLD, 0 SERIES_END) |
| net @1.5x / @2.0x | +161,531.82703744556 / +146,308.4144221541 (both reconciled) |

Fold map: F1 2020-01-26→2021-04-30 · F2 2021-05-01→2022-12-31 · F3
2023-01-01→2024-12-31 · F4 2025-01-01→2026-09-22 (post-warmup truncation:
14,589 of 14,742 H4 bars scored; first kept bucket 2020-01-26T12:00Z).

### A.2 Identical fold metric set (fold_comparison.json, @1.0x)

| metric | F1 | F2 | F3 | F4 |
|---|---|---|---|---|
| n_trades | 19 | 17 | 34 | 16 |
| hit_rate | 0.526 | 0.353 | 0.471 | 0.313 |
| avg_win | +18,492.96 | +8,469.50 | +15,442.04 | +4,246.77 |
| avg_loss | −4,898.48 | −8,888.82 | −6,291.76 | −6,476.92 |
| win/loss payoff | 3.78 | 0.95 | 2.45 | 0.66 |
| gross | +144,859.94 | −41,884.62 | +145,250.34 | −43,503.90 |
| fees | 3,262.05 | 4,480.64 | 9,845.19 | 5,729.27 |
| funding | −754.60 | −594.73 | −1,584.32 | −779.13 |
| funding_drag_share (\|funding\|/\|gross\|) | 0.0052 | 0.0142 | 0.0109 | 0.0179 |
| median / mean hold (bars) | 26 / 38.2 | 16 / 22.4 | 25 / 27.2 | 22 / 23.7 |
| DONCHIAN_STOP fraction | 0.947 | 0.882 | 0.882 | 1.000 |
| failed-breakout count (stop ≤ 6 bars) | 0 | 0 | 0 | 0 |
| MFE median [p25, p75] (return) | 8.13% [2.94, 18.24] | 3.79% [1.34, 6.80] | 3.68% [1.64, 7.57] | 3.12% [1.23, 4.89] |
| MAE median [p25, p75] (return) | −2.70% [−4.16, −1.78] | −2.35% [−5.00, −1.18] | −2.60% [−3.50, −0.80] | −2.33% [−3.36, −1.27] |
| PIT medians at entry: realized_vol_20 | 1.22% | 1.10% | 0.79% | 0.85% |
| PIT medians: trend_slope_20 | +4.52% | +5.12% | +2.85% | +4.14% |
| PIT medians: dd_from_high_200 | 0.00 | −0.005 | 0.00 | 0.00 |
| PIT medians: donchian_rank | 1.00 | 1.00 | 1.00 | 1.00 |
| exit reasons | 18 stop / 1 gate | 15 stop / 2 gate | 30 stop / 4 gate | 16 stop / 0 gate |

Combined halves (same artifact): F1+F3 (n=53) hit 0.491, avg_win +16,615.47,
avg_loss −5,827.34, gross +290,110.28, fees 13,107.25, funding −2,338.93;
F2+F4 (n=33) hit 0.333, avg_win +6,550.08, avg_loss −7,682.87, gross
−85,388.52, fees 10,209.91, funding −1,373.85.

Descriptive market context (fold_comparison.json `descriptive_context`,
POST-HOC-DESCRIPTIVE ONLY): BTC close-to-close over each fold: F1 +581.79%,
F2 −71.59%, F3 +465.96%, F4 −8.16%.

### A.3 Min-hold law audit (min_hold_audit.json)

- Code citation: `lane_btc_h4/pipeline/events.py` lines 99–100 — inside
  `run_book`, ANY of DONCHIAN_STOP / GATE_INACTIVE / MAX_HOLD is set to
  `None` while `bars_held < spec.min_hold` (`MIN_HOLD_BARS = 12`,
  `config.py` line 127). FOLD_END force-flat is evaluated after and is NOT
  suppressed.
- Instrumented copy asserted trade-identical to `books.l2_run_book` output
  ("PASSED") before any count was used.
- Suppressed exit triggers: 22 DONCHIAN_STOP + 13 GATE_INACTIVE.
- 11 of 86 trades had at least one suppressed stop; per-trade delay from the
  first suppressed stop to the actual exit (bars): 2, 2, 3, 6, 8, 9, 12, 14,
  21, 24, 29 (median 9).
- Trigger-time bars_held distribution of the 22 suppressed stops:
  1×1, 2×1, 3×1, 4×2, 5×1, 6×3, 7×3, 8×3, 9×7, 10×6, 11×7 → 9 of 22 fired at
  ≤ 6 bars held.
- Immediate-stop counterfactual (POST-HOC-DESCRIPTIVE-ONLY; stop allowed to
  fire immediately, gate/max-hold min-hold kept, full path re-accounted
  @1.0x): 88 trades, net 173,906.7507467543 → **delta −3,785.069412896526 vs
  measured** (counterfactual is WORSE). Per fold: F1 +2,263.59,
  F2 +5,200.74, F3 +1,816.54, **F4 −13,065.94**.

### A.4 Observed failed-breakout rate (k = 6, a-priori constant)

0 / 86 in every fold. This is STRUCTURAL: the 12-bar min-hold forbids any
DONCHIAN_STOP fill before bars_held ≥ 12 > k = 6. The un-suppressed raw
signal is in A.3: 9 stop triggers at ≤ 6 bars (10.3% of the 86-trade book
experienced a ≤6-bar stop trigger that the law silenced; their eventual
outcomes are inside the 11 delayed trades).

---

## (b) MECHANISM HYPOTHESES (each tied to the facts that support it)

**H1 — The fold split is a trend-persistence split, not a cost split.
(Facts A.2 gross row; A.2 fees/funding rows; descriptive context.)**
Gross alone is +144,860 / −41,885 / +145,250 / −43,504: F2 and F4 lose money
BEFORE any cost. Fees+funding are 4,075 (F2) and 6,508 (F4) — 12.1% / 13.0%
of the respective |net|, and funding drag is 1.4–1.8% of |gross| (1.6%
combined F2+F4 vs 0.8% F1+F3). Zeroing all costs would leave F2 at
−41,885 and F4 at −43,504. Costs deepen the losing folds but are not their
origin.

**H2 — In losing folds the breakout premise fails at the entry: upside
follow-through collapses while hit rate halves. (Facts A.2 hit_rate,
avg_win/avg_loss, MFE rows.)**
Entries are mechanically identical across folds (donchian_rank median 1.00
everywhere — fresh 30-bar closes highs; dd_from_high_200 ≈ 0; all labeled
UPTREND at decision). What differs is what happens next: MFE median falls
from 8.13% (F1) to 3.1–3.8% (F2/F3/F4) and the F1 right tail is unique
(p75 = 18.24% vs ≤ 7.57% elsewhere). With the stop trailing a 15-bar
closing low, a trade needs a run before the channel catches it; in F2/F4
runs of that size are rare (avg_win shrinks to 8.5k/4.2k) while failures
book avg losses of −8.9k/−6.5k. Hit rate 52.6%→31–35% plus payoff flipping
from 3.78:1 to 0.66–0.95:1 is arithmetically sufficient for the sign flip.

**H3 — F2 (and to a lesser degree F4) supplied a falling market in which a
long-only fresh-high continuation book is structurally whipsawed.
(descriptive context + A.2.)**
BTC fell −71.6% across F2 and −8.2% across F4, vs +581.8%/+466.0% in F1/F3.
The UPTREND gate kept admitting longs at local highs inside episodic
recovery labels; F2 trades die fastest (median hold 16 bars) and its MAE
p25 is the deepest (−5.00%) — bought highs, quick adverse resolution.
This is a description of the measured environment, not a "bad year" rule:
no fold-level information enters any computation (all metrics are computed
per fold post-hoc from the same frozen ledger).

**H4 — The 12-bar min-hold was NOT a material cause of the F2/F4 losses; on
this window it was mildly protective overall, with its benefit concentrated
in F4. (Facts A.3.)**
The immediate-stop counterfactual changes net by −3,785.07 (worse), composed
of +2,263.59 (F1) +5,200.74 (F2) +1,816.54 (F3) −13,065.94 (F4): removing
the delay would have HELPED F2 by ~5.2k but destroyed ~13.1k in F4, netting
negative. 11/86 trades (12.8%) had any delayed stop at all; median delay 9
bars. The min-hold acts on a small minority of the book and its net effect
has the opposite sign of the F2/F4 problem.

**H5 — Winner concentration amplifies the fold asymmetry. (A.2 MFE p75; PSV1
fold_concentration 0.5128 recomputed from A.1.)**
F1 alone is 51.3% of all positive-fold net (140,843.28 / 274,664.11) —
consistent with a fat-tailed book whose result hangs on a few extended runs
(F1 MFE p75 18.24%, mean hold 38.2 bars). A strategy whose profits are a
right-tail phenomenon will show exactly this fold pattern when the tail is
present in some eras and absent in others.

---

## (c) UNDETERMINED (what this data cannot decide)

1. **Gate (label) quality per fold.** All entries were labeled UPTREND at
   decision by construction; this audit did not measure whether the phase
   rule's UPTREND episodes correspond to ex-post persistent advances more
   poorly in F2/F4 than F1/F3 (that would require a separate label-vs-outcome
   audit and risks becoming threshold design — out of P1 scope).
2. **Which single fix, if any, is causal.** Only ONE counterfactual
   (immediate stop) was computed, because plan §1.3 named it. Whether entry
   confirmation, a different stop horizon, or position throttling would flip
   F2/F4 without destroying F1/F3 is NOT determined here — deciding it by
   scanning fold PnL is forbidden (plan §2).
3. **Whether F4's short history is representative.** F4 ends 2026-09-22
   (−8.2% BTC, 16 trades, all stop exits). With n=16 and one market path,
   F4's loss is measured but its mechanism is weakly identified vs F2's.
4. **Intra-trade path dependence.** MFE/MAE use bar high/low over the held
   window vs the entry fill price (definition in the ledger sidecar); they
   bound, but do not reconstruct, the intra-bar sequence the trailing stop
   actually reacted to.
5. **Cost-model realism.** 6 bps/side + funding 1.377e-5/8h is the FROZEN
   convention; the measured 12–13% cost share of |net| in losing folds is a
   statement about this model, not about achievable execution.

---

## Outputs

- `trade_ledger_btc_h4.csv` — 86 rows, 30 columns (per-trade ledger @1.0x,
  incl. PIT covariates at the decision bar and labeled descriptive forward
  returns)
- `trade_ledger_tiers_sidecar.json` — same trades re-accounted at 1.5x/2.0x
- `reconciliation.json` — verdict PASS, max_rel_err 0.0, all tiers
- `fold_comparison.json` — per-fold metric set + combined halves + descriptive
  context
- `min_hold_audit.json` — §1.3 audit (citation, counts, delay distribution,
  descriptive counterfactual)
- `data_receipt.json` — manifest/parquet digests, fold boundaries, ingest
  note (284/284 PASS), lock_mode + resource measurement
- `BLOCKED_lock_report.json` — foreign-holder evidence trail (2 yield
  attempts)
- `forensics_driver.py` — the rebuild itself (deterministic, re-runnable)
