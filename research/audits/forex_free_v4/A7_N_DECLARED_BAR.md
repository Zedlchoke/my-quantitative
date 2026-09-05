# A7-N DECLARED ADMISSION BAR — cycle FOREX-FREE-V4

Auditor: A7-N (independent novelty / anti-rescue auditor)
Written: 2026-09-05, BEFORE any rho computation of this audit.
Status: FROZEN for this audit. It will not be moved after measurement.

## What is being measured

Decision-level Spearman rho between a V4 proposal's anchor decision series
(signed direction state per (pair, daily 16:00 America/New_York decision
clock), values in {-1, 0, +1}; non-evaluable cells excluded) and the V3
family2 (FXFV3-A6-P1) anchor decision series, reconstructed per the frozen
family2 construction in two variants:

- variant (a) "as-scored": asserted-bound availability vintages
  (data_raw/forex_free_v3_macro, V3 tree);
- variant (b) "corrected": evidenced-availability vintages
  (data_raw/forex_free_v3r_macro_evidenced, V3R tree).

## The gating statistic

GATING RHO = Spearman rho over the ACTIVE shared cells: those (pair, clock)
cells of the shared daily decision grid where BOTH books hold a non-flat
direction (both values non-zero). This is the ancestry question stated
operationally: when both books are in the market, do they point the same
way? A re-grade of the ancestor must agree in direction where both trade.

Supporting diagnostics (reported, not gating): rho_full over ALL shared
cells (flats included; attenuated by flat-state overlap), direction
agreement rate on active cells, n_shared (total and active), and
event-level overlap commentary. Where the two diagnostics disagree, the
GATING RHO decides and the disagreement is reported.

## Thresholds (declared before measurement; |rho| because a sign-inverted
clone is equally a rescue under the blanket clauses)

- |rho_gating| < 0.5  AND n_shared_active >= 30  -> admits novelty
  (NOVELTY_PASS on the series measurement).
- 0.5 <= |rho_gating| <= 0.7                      -> CONDITIONAL:
  reported to the owner with full analysis; the owner decides at D2.
- |rho_gating| > 0.7                              -> re-grade of the
  ancestor: NOVELTY_FAIL, REJECT.
- n_shared_active < 30                            -> INDETERMINATE:
  measurement cannot support a novelty claim; verdict CONDITIONAL
  (escalated to the owner with the raw numbers; NOVELTY_PASS is not
  available on this measurement alone).

## Front-door application (PLAN_forex_v4.md section 1.1; forbidden inventory
front_door conditions)

For FXFV4-A4-P1 and FXFV4-A4-P2 the front-door admission decision is:

- ADMITTED  iff |rho_gating| < 0.5 vs variant (a) AND vs variant (b),
  with n_shared_active >= 30 on both.
- REJECTED  iff |rho_gating| > 0.7 vs EITHER variant.
- CONDITIONAL otherwise (any cell in [0.5, 0.7] or any INDETERMINATE),
  reported to the owner with analysis.

This decision and the raw numbers go to the owner either way. The numbers
are an audit decision, never a prose argument.

## Non-applicability branch

For proposal-vs-forbidden-row pairs where a decision series cannot be
measured (V1/V2 intraday session families; V3 family1 code not re-run by
this audit), the verdict is by systematic feature comparison on four
recorded features per row: information source, decision clock, causal
control, signal functional form. NOVELTY_PASS requires all four features
distinct from the forbidden row; any shared load-bearing feature is
CONDITIONAL or NOVELTY_FAIL as recorded per row.

Signed: A7-N, 2026-09-05 (frozen before measurement).
