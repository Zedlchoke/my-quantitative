# m1 — FX-F5 CIP-vintage sensitivity (WORK_QUEUE A-#8 / HYPO G3)

- Lane **MEAS-FX**, round **FUTURES-5SYM-PRESCORED-20261005** wave-3.
- Outcome-blind: correlation/regime statistics on committed vintages only.
  No PnL, no conditional-on-signal return, no network. Machine mirror:
  `m1_fx_f5_cip_vintage.json`. Generator: `meas_fx_m1_m3_cip_vintage.py`.
- Locks inspected at start: **FREE_PROVEN**.

## What ran

The year-end ALFRED as-of recomputation of the 6E differential regime on
the 27 rolls is **already committed** as per-roll values:
`FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_6e/a7_6e_recompute.json:
rolls_cip.rows` (A7 audit; vintage basis = ALFRED year-end SOFR vintages
2019-12-31..2024-12-31 + 2026-09-30, no 2025-12-31 vintage exists; €STR is
latest-only everywhere — no vintage set exists). This lane recomputes the
sensitivity statistics from those committed rows. The vintage CSVs
themselves are NOT in this tree (see NOT_RUN below); consuming the
committed per-roll recomputation is the lawful route.

## Results (6E, n=27 rolls, 2020-03-02 .. 2026-09-01)

| statistic | latest-vintage | year-end-ALFRED as-of |
|---|---|---|
| Pearson r(gap%, CIP gap%) | **+0.9097** | **−0.1068** |
| Spearman rho | +0.8999 | +0.0153 |
| sign agreement (gap vs CIP) | 27/27 | 26/27 |
| 0.20 rho bar | **PASS** (0.91 ≥ 0.20) | **FAIL** (−0.11 < 0.20) |

- Reproduction check: recomputed r reproduces the committed lane number
  (6E_a3_term.json corr_gap_vs_cip 0.9097) and the committed A7 numbers
  (0.9097 / −0.1068) to within 1e-6 — same committed rows.
- **Regime-label flips**: 1/27 (roll 2022-12-01 flips the sign of the
  CIP-predicted gap between bases). The deeper damage is the correlation
  itself: r crosses zero (+0.91 → −0.11) with the vintage basis.
- **0.20 rho bar** (ANCESTRY_CHECK.md FX-F5 row; bar value precedent
  FAMILY_FAILURES.jsonl row 67 "bar 0.20"): bar passage is
  **vintage-dependent** — passes only on the latest-vintage basis. The
  direct rho of the F5 differential regime against the V8/V9 nominal/PPP
  shadow series is NOT_RUN (shadow series not in tree); context from the
  dead rows: FXFV9-A5-P1 pooled |rho| 0.3034 / P2 0.3119 vs the
  FXFV8-anchor (both over the bar — ANCESTRY_RHO_BLOCK deaths), FXFV8
  itself died CONTROL_OUTEARNED_ANCHOR (DGS10-level control out-earned
  4.01×, cluster #14).

## Verdict

**Bar passage flips with the vintage basis on the only vintage data
available — the measured proof of FX-F5's standing NEEDS_EVIDENCE.** The
owner real-time SOFR decision (court §d row 7) remains a SIGNATURE
regardless of this quantification; nothing here re-tunes, registers, or
schedules anything; PB2 untouched.

## NOT_RUN register

| what | grounds |
|---|---|
| Fresh year-end-ALFRED as-of recomputation from the vintage CSVs (6E and 6B) | **NOT_RUN_DATA_NOT_IN_TREE** — `git ls-files` finds no committed DFF/SOFR/DFEDTARU vintage capture in the worktree (only the collector `FUTURES-BEHAVIOR-10SYMS-PREP-20261002/nonprice_acquisition/collect/fred_alfred.py` and BLS release-schedule captures). The vintages live outside the repo at `/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms/fred_alfred/` (subdirs `latest/`, `pit/`, `vintage_attempts/`) — uncommitted, therefore not consumed. Note: even on that external disk only SOFR year-end vintages exist; no DFF/DFEDTARU vintage set was ever captured. |
| 6B vintage-as-of recomputation | **NOT_RUN_DATA_NOT_IN_TREE** — no committed 6B vintage-as-of recomputation exists (6B_a3_term.json gap_vs_policy_diff is latest-vintage only: Pearson +0.8423 / Spearman +0.7445, n=19 diff>0 vs n=1 diff<0); BoE Bank Rate is revision-free so the vintage risk is the US (DFEDTARU) side only, and the US vintage files are not in this tree. |
| Direct 0.20-rho measurement vs the V8/V9 nominal/PPP shadow series | **NOT_RUN_DATA_NOT_IN_TREE** (shadow signal series not committed); by law the bar is re-measured at any D2-equivalent stage. |

— End m1.
