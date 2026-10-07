# PLAN — NBA-WINPROB-PROSPECTIVE-PREP-V1 (NBA prospective win-prob PREP, $0)

- cycle_id: `NBA-WINPROB-PROSPECTIVE-PREP-V1` · asset: shared · budget 0/0
  (ZERO scored cells) · registered 2026-10-07.
- Owner authority 2026-10-07 (this chat, AMENDMENT): "NBA cần successor
  prospective, forecast ghi trước tip và odds thật ghi trước tip; nếu thiếu thì
  NBA = NOT_RUN, không backfill." Explicitly **NOT a typed GO**: no real-game
  probability for any real game anywhere in this cycle before its own typed GO.
- GO phrase (REGISTERED_NOT_CONSUMED, typed ONLY by the owner, verbatim, fresh,
  at this cycle's own gate):
  **`GO NBA WINPROB PROSPECTIVE V1 PREDICTIONS`**

## Scope

Prepare prospective pre-tip NBA win-prob forecasting on the frozen mandatory arm
**B1* own-Elo K=32, HCA=100, γ=0.75** (binary updates; boundary
`R ← 1500 + 0.75·(R−1500)`; HCA=100 prediction-only), inherited verbatim from the
TERMINAL `NBA-WINPROB-NG-SCORED-V1` (head 0f3de175/a76dadb1 chain; successor
packet at `.worktrees/nba-winprob-ng-prep-v1/integration/research/control/
NBA-WINPROB-NG-PREP-V1/SUCCESSOR_PACKET_SCORED.md` is PROPOSAL status). Carried
disclosure (never edited, never re-fit): pooled OOS F1–F5 2022–2026 LL 0.639953,
Brier 0.223545 (n=6,605); **calibration slope 0.8107 below [0.85,1.15] —
overconfidence sign; NO recalibration on viewed OOS.**

Lanes (mirror of the WNBA-WINPROB-PROSPECTIVE-PREP-V1 precedent, adapted): (1)
DATA REFRESH — espn_nba_schedules/team_game_logs release-store lineage refresh,
$0/no-auth, ingest the published 2026-27 season schedule (available now),
provenance URL+tag+timestamp+bytes+sha256 per file, extend-only rating stream;
(2) LEDGER — port `wnba_prospective_ledger@1` (57/57 precedent) as
`nba_prospective_ledger@1` with tip_utc law (ESPN ISO8601 → UTC) + tip-relative
day-anchored batch at **T0 − 6h10m** (ERRATUM_CAPTURE_1 E-2 default unless an NBA
tip census proves a different binding law; strict `recorded_at_utc < tip_utc` at
append AND scoring); (3) FREEZE — B1* pins re-hashed at freeze, B0 floor carried,
window/seed laws, no-parameter-change-after-first-real-row; (4) SYNTH + DRY-RUN —
sandbox only, zero real rows; (5) A7 PRELAUNCH (fresh context, 0 unresolved
HIGH/CRITICAL).

## Boundaries

$0; no purchases; no S1; no push/merge/rebase; registry writes only via
researchctl CAS; heavy runs take the machine-wide lock; root checkout control
plane only; data under `~/.my-quantitative-data/nba-winprob-prospective-prep-v1/`;
other cycles' trees/ledgers read-only; language law: calibration/forecasting
vocabulary only; no paper/betting claims (the paper-trade cycle consumes this
cycle's forecasts only after BOTH gates have owner GOs). Worktree/branch:
`orca/nba-winprob-prospective-prep-v1-integration` (created at lane start).
Terminal outcomes: PRELAUNCH_READY_PENDING_OWNER_GO | PRELAUNCH_BLOCKED_<gate> |
NOT_RUN_* | TECHABORT_*. An early/paraphrased GO dies unconsumed.
