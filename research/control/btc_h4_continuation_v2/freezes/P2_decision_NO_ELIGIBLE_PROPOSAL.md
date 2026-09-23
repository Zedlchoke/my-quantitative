# P2 DECISION — NO_ELIGIBLE_PROPOSAL (record of the ≤1-change selection)

cycle: BTC-H4-CONTINUATION-V2 · decided_by: A1/Lead · date: 2026-09-23 ·
status: PRE-CANDIDATE (no candidate PnL ever computed; no scored run;
budget remains 0/2)

## Input evidence

FORENSICS_P1 (this worktree, `forensics/`): reconciliation PASS 0.0 rel-err
at 1.0x/1.5x/2.0x vs the committed PSV1 ledger; FINDINGS.md layers (a)
measured facts, (b) mechanism hypotheses, (c) undetermined. All post-hoc S0.

## The owner's menu, decided one branch at a time (plan §2 law: mechanism +
PIT observability only, no fold-PnL scanning)

### Branch 1 — sửa rủi ro min-hold/stop → INELIGIBLE (measured counterproductive)

- Min-hold law measured from frozen code (`pipeline/events.py:99-100`,
  `MIN_HOLD_BARS=12`): 22 suppressed DONCHIAN_STOP triggers across 11/86
  trades (delays 2–29 bars, median 9).
- Descriptive immediate-stop counterfactual: net WORSE by −3,785.07 total
  (F1 +2,264, F2 +5,201, F3 +1,817, F4 −13,066). The owner's explicit
  caution ("cần đo tác động, không được mặc định đây là nguyên nhân") is
  answered: measured, and it cuts AGAINST the fix.
- Faster exits generally: same-direction evidence — suppressed GATE_INACTIVE
  triggers behave alike; and the PSV1 G6 control already established the
  gate/exit timing series carries no information (block-shuffled placebo
  +190,392 > +177,692). Any exit re-timing is a member of the killed class.

### Branch 2 — cải thiện xác nhận breakout → INELIGIBLE (no separating PIT observable)

Measured PIT medians at the entry decision bar (forensics
`fold_comparison.json`):

| covariate | F1 (win) | F2 (loss) | F3 (win) | F4 (loss) |
|---|---|---|---|---|
| realized_vol_20 | 1.22% | 1.10% | 0.79% | 0.85% |
| trend_slope_20 | +4.52% | +5.12% | +2.85% | +4.14% |
| dd_from_high_200 | 0.000 | −0.005 | 0.000 | 0.000 |
| donchian_rank | 1.00 | 1.00 | 1.00 | 1.00 |

- No covariate separates the winning folds from the losing folds.
  trend_slope_20 is ANTI-sorted (worst fold F2 has the highest median).
  realized_vol_20 clusters {F1,F2} vs {F3,F4} — the wrong split. Entries
  are mechanically identical (rank 1.0 = at-channel-top, dd200 ≈ 0) in all
  four folds; MAE medians are flat (−2.3…−2.7%) while MFE collapses
  (8.1% F1 vs 3.1–3.8% elsewhere) — the failure is entirely in post-entry
  follow-through, which no at-entry observable in the measured set predicts.
- A confirmation gate therefore has nothing to condition on: any threshold
  placed on these covariates would be a curve-fit to four fold medians on
  n=86 trades (16–34/fold) — exactly the fold-PnL scanning plan §2 forbids.
- Arithmetic no-op proof for the strongest folklore gate (close > SMA200):
  every entry has dd200 ≈ 0, i.e. close ≈ rolling-200-bar max, and
  SMA200(≤ rolling max) ≤ close holds at every such bar — a SMA200
  entry-gate on THIS entry series is a mathematical no-op, not a candidate.
- New observables outside the H4 OHLCV panel are OUT OF SCOPE (plan §0: no
  new data sources this cycle). Inventing further OHLCV-derived gates after
  the measured set failed = fishing until something "works" (plan §2; owner:
  "đừng cố tạo một backtest đẹp").

### Economic reading of the measured record (for the terminal ledger row)

The Donchian-continuation premium on BTC H4 exists only when breakouts
FOLLOW THROUGH (structural bulls F1/F3: BTC +582%/+466%; F2/F4: −71.6%/−8.2%).
In contraction/chop the same mechanically-identical entries pay the breakout
premium and collect nothing: gross −41,885 (F2) / −43,504 (F4) — losses are
gross, not cost artifacts (fees+funding 12–13% of |net|). Neither the UPTREND
phase label (PSV1 G6 kill) nor any measured at-entry state identifies the
follow-through regime ex ante. One change with a causal mechanism and a valid
PIT observable does not exist in the authorized evidence space.

## Consequences (per plan §6/§6.1)

- Verdict: `BTC_H4_CONTINUATION_V2_NO_ELIGIBLE_PROPOSAL` (first-class;
  NO scored run, NO budget cell, NO candidate PnL computed at any point).
- STOP-1 owner gate is moot (nothing to freeze/score); the registered GO
  phrase dies UNCONSUMED at close per P-8/RULES §7.
- Denominators: 0 observed / 0 published scored outcomes this cycle;
  program totals unchanged (283/286 per P-9). The forensic rebuild computed
  no new scored result — it reproduced the predecessor's own record with
  0.0 rel-err and is evidence, not a trial.
- No FAMILY_FAILURES row: no family was scored or rejected; the ancestor
  PSV1-BTC_H4-UPTREND-DONCHIAN_CONTINUATION already carries its kill row
  (CONTROL_OUTEARNED_ANCHOR) from PHASE-STRATEGY-V1.

---

## A7-terminal correction (F-A7-2, recorded before close)

The arithmetic no-op proof above overclaims its premise: "every entry has
dd200 ≈ 0" is median-level, not universal (17/86 entries sit >1% below the
200-bar high; min −23.3%). The CONCLUSION holds independently and was
re-verified by A7 from the panel: `close > SMA200` binds **0/86** entry
decision bars — the SMA200 entry-gate is vacuous on this entry series
regardless. See audits/a7_terminal_audit.{json,md} C6.
