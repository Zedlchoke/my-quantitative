# AMENDMENT 1 — NFL-WINPROB-SCORED-V1 (pre-outcome, §24 remediation round 4)

Trigger: co-owner audit follow-up 2026-10-04. Two defects confirmed by
controller re-measurement (0 outcomes ever computed; ledger 9 PREREGISTERED /
0 COMPUTED — pre-scoring remediation per handbook §24):

- L1' (was A7 LOW-1, escalated by co-owner as a trial-accounting consistency
  violation): nfl_winprob/run_evaluation.py append_trial_rows wrote COMPUTED
  rows with schema "nba_winprob_trial_ledger@1" while the 9 seeded
  PREREGISTERED rows use "nfl_winprob_trial_ledger@1". FIXED: appends now use
  the NFL schema; a synthetic test asserts EVERY row (PRIMARY append + REPRO
  append) carries the NFL schema and that no NBA-schema string exists in the
  runner source.
- L2' (was A7 LOW-2): the explicit immutable-code drift prefix in the launch
  gate was the NBA remnant "nba_winprob/" (dead in this worktree; only the
  allowlist fallback covered nfl_winprob/). FIXED: prefix is "nfl_winprob/"
  and the check is refactored into the pure helper _code_drift_reasons with
  positive/negative drift unit tests (code change flagged; allowlisted
  control file not flagged; NBA-prefixed path no longer special).

No hypotheses/arms/folds/thresholds change. Freeze of code 8cd0e1bc is
SUPERSEDED_BLOCKED; freeze v2 pins the remediation commit. Raw data and the
9 PREREGISTERED ledger rows are untouched; no metric on real outcomes.
