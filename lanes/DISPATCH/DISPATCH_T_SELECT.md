# DISPATCH — Lane T_SELECT (NFL-WINPROB-NG-SCORED-V1, wave 2) — TRAIN-INTERNAL SELECTION

ROLE: implementation/selection lane (train-internal only). Pre-registered grids BELOW are the
preregistration — the lane may not add, remove or move grid points; every evaluated config
enters the selection ledger.
ABSOLUTE WORKTREE: /Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration
BRANCH: orca/nfl-winprob-ng-scored-v1-integration · DISPATCH SHA: 8b196ef5c61890865e1b2e4af41de7a67221da25
ALLOWED PATHS (write): lanes/T_SELECT/** + lanes/DISPATCH/handoff_T_SELECT.json + selection
outputs under ~/.my-quantitative-data/nfl-ng-scored-v1/selection/ (ledgers/reports only).
READ-ONLY: everything else.
FORBIDDEN: git; ANY access to season > 2018 outcome rows (hard filter at load + assertion +
grep-auditable constant); scored evaluation on any window; the real prediction ledger (must
not exist / not be written); S1; purchases; keys; betting vocabulary.

## Data (inputs, read-only)
- games.csv: ~/.my-quantitative-data/nfl-nflverse-v1/raw/games.csv (archive; 1999–2026;
  filter season 2000..2018 REG+POST at load; assertion enforces).
- pbp 2000–2017: ~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2000_2017/ (C3 priors;
  season ≤ 2017 asserted).
- Frozen semantics to implement verbatim: predecessor lanes/C_PROTOCOL/PROTOCOL_NFL_NG.md
  §0 laws (as-of kickoff grain; simultaneous-kickoff exclusion; tie law S=0.5 update +
  excluded from scoring/training rows with counts; neutral-site HCA=0 reported separately;
  franchise lineage 32-lineage map: SD→LAC 2017, STL→LA 2016, OAK→LV 2020, CLE/BAL separate,
  HOU from 2002; PRE rows dropped with counts) — read the file, do not rely on this summary.
- Mechanism specs verbatim: predecessor lanes/B_MECHANISMS/MECHANISMS_NFL_NG.md §2 (C1/C2/C3/C4
  exact operationalizations).

## Pre-registered grids (pinned by controller before any run)
- C1: β ∈ {0, 25, 50, 75, 100} (5 configs).
- C2: λ ∈ {0.25, 0.5, 0.75} × γ_d ∈ {1/3, 1/2} × h ∈ {0, 25} (12 configs).
- C3: θ ∈ {0, 25, 50, 75, 100} (5 configs).
- C4: δ ∈ {0, 25, 50} (3 configs; gate-only).
- Designed-null equivalence (must reproduce B1* bit-for-bit on the eval stream before any
  other number is believed): C1 β=0; C2 λ=0 ∧ h=0; C3 θ=0; C4 δ=0.
- Inner folds (rolling origin, pinned): inner test seasons 2014, 2015, 2016, 2017, 2018;
  fold s warms the replay from season 2000 through s−1 then evaluates season s REG non-tie
  rows. Selection criterion: pooled mean LL over the 5 inner test seasons. Tie-break: fewer
  active parameters, then lexicographically smaller config id.
- Uncertainty: paired ΔLL vs B1* on identical rows; 95% CI by kickoff-calendar-date-cluster
  bootstrap, 10,000 resamples, seed 20261005 (inherited), percentile method.
- Negative controls (train-internal): time-shuffled twin per candidate (shuffle the
  candidate's adjustment across lineages within each scoring week, preserving marginals);
  venue-label permutation for C2 (swap home/away on a random half of train games for
  deviation updates only, seed 20261005). A control that "wins" ⇒ machinery suspect flag.

## Arms to implement (specs in MECHANISMS_NFL_NG.md — exact)
- B0: constant p = TRAIN 2000–2018 REG non-tie home-win rate (emit the frozen constant).
- B1*: own-Elo K=40, HCA=0, γ=2/3 (update law binary S; offseason reversion to 1500 by
  one-third; μ=1500 start; new/expansion lineages start 1500).
- C1: R̃ = R − β·(SOS_i(t) − S̄(t)) prediction-only adjustment, current-season completed
  games, zero at season openers; update law unchanged.
- C2: role deviations d^H,d^A (init 0; in-role updates with λ; γ_d offseason decay; league
  scalar h in prediction).
- C3: season-start prior R ← 1500 + (2/3)(R−1500) + θ·z_i(s); z from prior-season REG EPA
  per lineage: E = 0.5·(off_EPA/play + def_EPA_allowed/play signed) standardized across
  lineages each boundary; no term when prior season missing.
- C4: one-cell δ penalty on p_home argument for away rest_days ≤ 6 (protocol f2 definition:
  days between strictly-prior kickoffs).

## Verdicts to emit (per protocol §6)
- G-SELECT / G-ENTRY per candidate (ADMIT requires pooled inner ΔLL point < 0 AND calibration
  slope ∈ [0.85, 1.15] AND shuffled control not winning; confident-worse ⇒ kill); G-INT for
  C4 (slice CI excludes 0 in direction AND pooled direction consistent, else release slot).
- Slot dispositions for the freeze: which of C1/C2/C3/C4 field with which frozen params;
  released slots named. C3 runs only under lane A's PASS_PIT_SEASON_GRAIN (granted).

## Deliverables (lanes/T_SELECT/)
- select.py / arms.py / boot.py (deterministic, seeded; --selftest mode with hand-computed
  fixtures: one-game Elo update, tie update, same-kickoff exclusion, neutral-site handling,
  season-boundary reversion, C3 z-standardization).
- SELECTION_LEDGER.jsonl (one row per evaluated config: arm, params, pooled inner LL, per-fold
  LL, ΔLL vs B1*, CI, verdict).
- SELECTION_REPORT.md (frozen params + dispositions + B0 constant + fit counts + bootstrap
  details + negative-control results + designed-null equivalence evidence).
- VERDICT_TABLE.md (PASS/FAIL/NOT_RUN per check).
- Lock discipline: before the selection run execute
  `.venv/bin/python research/researchctl.py locks inspect` (cwd = root checkout
  /Users/hoangminhlong/my-quantitative) — if verdict ≠ FREE_PROVEN ⇒ NOT_RUN_RESOURCE_
  CONFLICT, re-check up to 3× with 60 s backoff, else stop and record; record both the
  before/after observations with timestamps in SELECTION_REPORT.md. Job is minutes-scale
  single-process; do not write the lock registry.
HANDOFF: zcode_orch_v3_handoff@1 at lanes/DISPATCH/handoff_T_SELECT.json (task_id
nfl-winprob-ng-scored-v1-T-SELECT, dispatch_sha=actual_start_sha=8b196ef5…, commit_sha=null).
STOP CONDITIONS: designed-null equivalence fails (stop — machinery bug; record TECHABORT_
EQUIVALENCE); any need to touch 2019+ data (stop); repeated lock conflict.
