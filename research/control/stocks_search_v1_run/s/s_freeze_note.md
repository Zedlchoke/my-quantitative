# S FREEZE NOTE — STOCKS-SEARCH-V1 selection freeze

task_id: ssearch-s
cycle: STOCKS-SEARCH-V1 (orchestration label ZCODE-ORCHESTRATION-V3)
base: 9419b97a515c10b28bcc224300906c9c138e9194, branch orca/stocks-search-v1-integration
plan: plans/PLAN_stocks_search_v1.md §5 as amended by §3b (D2 SKIPPED, R0 NOT_RUN)
builder: `s_select.py` (deterministic; `--selfcheck` recomputes the entire walk
byte-identically under the machine-wide heavy lock)

## What was frozen

`selection_freeze.json` — the exact S selection for the §5 grid under the
frozen §3b tier order, with P-20 books-distinct adjudicated DURING the walk.

- Tier (i) family order (P0 F3 fired census, DESC): GAP 304,405,122 >
  52W-HIGH 140,371,770 > VOL-REGIME 135,394,900 > CLV-RANGE 19,455,398 >
  DVOL-SHOCK 11,695,946 > EVENT-UNWIND 745,575.
- Tier (ii) per-config order within family (F3 fired DESC, config-id ASC) —
  re-derived mechanically from `p0/p0_census.json` and verified equal to the
  manifest's frozen order (check tier1_*/tier2_*).
- Round-robin: one configuration per family per round, <= 2 scored cells per
  family, until 3 cells are filled.
- P-20 books-distinct: pairwise pooled |rho| of the daily POSITION-count
  series vs every already-selected higher-ranked candidate; strictly
  > 0.98 => SELF_SUBSUMED, next in the frozen order taken; an unmeasurable
  rho is NOT_ADJUDICABLE fail-closed (never an inferred PASS).

## Position-series conventions (pinned, disclosed in the freeze)

The dispatch packet pins the S adjudication statistic: daily per-name position
series from the manifest construction on the P0 cohort, positions {0,1}
long-only, pooled as a daily count series, pairwise Pearson |rho| at
threshold 0.98. Conventions c1..c8 (freeze `p20_conventions`):

- positions taken on fired AND bookable decisions (F4 floors are part of the
  frozen construction), index >= warmup_need;
- clock legs (t, t+1, t+1+H) all served (missing exit leg = DEATH_CENSORED,
  excluded, counted);
- held on sessions t+1 .. t+H (flat from the t+1+H open);
- {0,1} long-only, overlapping decisions collapse;
- sessions mapped onto the SPY-pinned S0 calendar (2,943 sessions,
  2015-01-02..2026-09-16; SPY.json.gz sha256 pinned);
- no fold force-flat (execution contract of phase E, not a books-distinct
  property);
- NO return, PnL, PF, Sharpe or drawdown anywhere (banned-key scan on the
  freeze body).

## Engine identity

p0_lib.py aaa9355f... and p0_run.py fa7e7ee2... sha256-verified before use;
`parse_name` + `run_config_census` reused read-only. One heavy pass over the
111,322-name cohort rebuilt per-state fired/bookable totals and cross-checked
them EXACT against the frozen P0 census sums (47/47 configs, check
`state_totals_equal_p0_census_all_47`).

## Selection result

<!-- RESULT_BLOCK -->

## Verification battery

26 pre-pass checks + state cross-check + banned-key scan recorded in the
freeze `verifications` block (see `checks:` line in run_log_s.txt). INPUT
identity: D1 manifest file sha256 1ccbf668..., self_sha256 e0b69b41...
(empty-field convention), all P0 artifact digests pinned AND cross-checked
against f9_artifact_digests.json.

## Outcome-blindness and labels

R0 NOT_RUN (D2 SKIPPED by owner amendment §3b — never an inferred PASS).
PBO NOT_RUN fail-closed (<=3 cells, d0992d17 class). §10 disclosure carried
verbatim in the freeze. This selection consumes NO scored cell: scoring
happens only at phase E after fresh-context A7 and the exact owner GO
("GO STOCKS SEARCH V1 SCORED EXECUTION"; early/paraphrased GO dies
unconsumed, P-8).
