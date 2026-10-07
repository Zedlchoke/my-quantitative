# PLAN — SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1 (men's intl soccer prospective PREP, $0)

- cycle_id: `SOCCER-INTL-WINPROB-PROSPECTIVE-PREP-V1` · asset: shared · budget
  0/0 (ZERO scored cells) · registered 2026-10-07.
- Owner authority 2026-10-07 (this chat, AMENDMENT): each league's paper rows
  need a valid prospective forecast path + odds + rights/PIT + its own GO; soccer
  historically had NO fixture feed (`NOT_RUN_SOURCE` in the TERMINAL scored
  cycle). Explicitly **NOT a typed GO**.
- GO phrase (REGISTERED_NOT_CONSUMED, typed ONLY by the owner, verbatim, fresh,
  at this cycle's own gate):
  **`GO SOCCER INTL WINPROB PROSPECTIVE V1 PREDICTIONS`**

## Scope

Prepare prospective pre-kickoff 3-way (HOME/DRAW/AWAY) forecasting for men's
international football on the frozen arm **B1 Elo/Davidson K=48, ν=0.6, HCA=65**
(verbatim from `SOCCER-INTL-WINPROB-SCORED-V1` FREEZE_SCORED.md, selection of
record; **V1 HCA=80 is shadow/control only — never selectable from paper
results**). Binding PIT law inherited: day-D features use only results with date
STRICTLY < D (PIT_LAW_PROVEN_SAMEDAY_EXCLUSION); kickoff times never fabricated;
shootout winners never modify targets; the one contradictory duplicate stays
excluded; held-out 2023+ is PARTIALLY REVEALED (erratum) — never a clean holdout,
never tuned on.

Lanes: (1) FIXTURES SOURCE — find, rights-check, and PIN a future-fixtures
source with true kickoff UTC (candidate: The Odds API `/v4/sports` 0-credit
census + events listing under OWNER_DECISION_CAPTURE_2 standing key law; quota
caps 4/day + 120/month shared across the key; NO assumed coverage — measure
which international competitions actually carry 1X2); no qualified source ⇒
NOT_RUN_SOURCE stays. (2) CORPUS REFRESH — extend-only martj42 results.csv
re-download (CC0-1.0), byte-diff vs df35268f snapshot, QC battery re-run, new sha
pins. (3) FORECAST LAW FREEZE — B1 pins re-hashed; warmup 1872–1950; rating
replay through the refresh cutoff; per-match forecast cutoff
**kickoff_utc − 6h** (strict `recorded_at_utc < kickoff_utc` at append AND
scoring; batch granularity: one batch per UTC date at min-kickoff − 6h10m unless
the census proves a different binding law); (4) LEDGER — port
`wnba_prospective_ledger@1` as `soccer_prospective_ledger@1` (3-outcome rows);
(5) SYNTH + DRY-RUN sandbox; (6) A7 PRELAUNCH fresh context.

## Boundaries

$0; no purchases/accounts; no S1; no push/merge/rebase; registry via researchctl
CAS; heavy lock machine-wide; data under
`~/.my-quantitative-data/soccer-intl-winprob-prospective-prep-v1/`; other
cycles untouched; TERMINAL PREP/SCORED trees read-only. Worktree/branch:
`orca/soccer-intl-winprob-prospective-prep-v1-integration` (created at lane
start). Terminal outcomes: PRELAUNCH_READY_PENDING_OWNER_GO |
NOT_RUN_SOURCE | NOT_RUN_PIT_ASOF | PRELAUNCH_BLOCKED_<gate> | TECHABORT_*.
An early/paraphrased GO dies unconsumed.
