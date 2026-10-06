# m2 — FX-F6 fwd-21d-vol → intraday-sign transfer (WORK_QUEUE A-#9 / HYPO G4)

- Lane **MEAS-FX**, round **FUTURES-5SYM-PRESCORED-20261005** wave-3.
- Outcome-blind handling: the transfer statistic conditions a market
  observable on a signal-family input (CoT stratum), so per the dispatch
  law the harness is built + proven on **synthetic fixtures only**; the
  real-data run is the owner-gated part and is recorded
  **NOT_RUN-REAL-DATA**. Machine mirror: `m2_fx_f6_transfer.json`.
  Generator: `meas_fx_m2_transfer_harness.py` (reads no real data).

## What is already committed (descriptive, cited — not recomputed)

| input | value | source |
|---|---|---|
| 6E signal side: fwd-21d vol by CoT stratum | ≥80th-pct 6.5218% (n=54) vs ≤20th-pct 7.6838% (n=36), mid 6.9817%, n=347 joined; strict-past 3y percentiles, release-safe obs+3 | `FUTURES-DEEPRESEARCH-V2-20261003/analysis/6E_a5_cot.json:positioning_vs_fwd_vol_descriptive` |
| 6B cross-symbol falsifier | corr(\|z\|, fwd vol20) = −0.0745 (n=326) | `.../6B_a5_cot.json` |
| PIT structure | 1,082 weekly net-noncomm obs 2006-01..2026-09; Tue-observe / Fri-15:30 release | `6E_a5_cot.json:coverage` |

The **daily-horizon** fact (fwd-21d vol differs across extreme-CoT strata)
is committed. The **intraday transfer** (host F1/F4-6E trigger-conditioned
sign stability / dispersion split by CoT stratum) is NOT committed — the
transfer IS the hypothesis (CENSUS_5SYM FX-F6 field 3(i), declared
NOT_RUN).

## What remains conditional (NOT_RUN-REAL-DATA)

Executing the harness on the 1m panels + trigger census conditions
real-market observables on the family signal input — owner-gated. When the
owner gates it, the run MUST carry (wired into the harness spec, verified
by fixtures):

1. the release-clock control arm (COMMNG1-A4-P2 rows 107–109 precedent —
   bare release-clock control out-earned every positioning book);
2. the mid-pctile (20–80) negative stratum;
3. the 6B near-zero cross-symbol falsifier re-check;
4. block bootstrap (iid forbidden — labels autocorrelated), strict-past
   percentiles, obs+3 release-safe labels;
5. the √2 MDE-inflation disclosure on the host (halved n per stratum).

## The harness

`T = sign_agree_rate(HIGH) − sign_agree_rate(LOW)` on consecutive session
returns within strata, with a seeded circular block bootstrap CI
(block=8, 500 draws, seed 20261005). Label law: strict-past 156-week
percentile (current obs excluded), strata ≥80 / ≤20, release-safe obs+3
shift. Sign-STABILITY statistic — not a return level; outcome-blind by
construction on synthetic data.

## Fixture law + results (all four PASS)

| id | law | result | pass |
|---|---|---|---|
| F1-null | no injection; T must sit inside its own CI | T = −0.0292, CI95 [−0.0667, +0.0142] | PASS |
| F2-inject+0.10 | HIGH strata shifted toward sign agreement by +0.10 (P(agree\|HIGH)→0.60, sequential injection) | T = +0.0642, CI95 [+0.0156, +0.1005] — direction + order recovered | PASS |
| F3-no-lookahead | corrupting the last 100 weeks of the positioning series must leave the first 100 strata labels identical | labels byte-identical (strict-past construction) | PASS |
| F4-release-lag | a HIGH percentile at row 0 must not surface in the label before row 3 | rows 0-2 NaN, row 3 = HIGH (obs+3) | PASS |

Fixture provenance: deterministic seeded generators (no market data);
injection is sequential so the induced agreement rate is exact-ish; F3
proves the no-future-data property of the percentile machinery; F4 proves
the release-safety property.

## Status summary

- Harness + synthetic proof: **DELIVERED** (this artifact).
- Committed descriptive signal-side inputs: cited above (already in tree).
- Real-data transfer execution: **NOT_RUN-REAL-DATA** (conditional-on-
  signal; owner-gated). Nothing here adjudicates FX-F6's refutation
  conditions, registers, or schedules anything; PB2 untouched.

— End m2.
