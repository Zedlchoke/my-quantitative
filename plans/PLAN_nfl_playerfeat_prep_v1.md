# PLAN — NFL-PLAYERFEAT-PREP-V1 (NFL player-feature table PREP, $0)

- cycle_id: NFL-PLAYERFEAT-PREP-V1 · asset: shared · ACTIVE_LIGHT, budget 0 scored, NO GO
  phrase. PREP/data ONLY.
- owner authority 2026-10-05 (this chat): the crosswalk blocker is cleared at the data level;
  build the frozen NFL player-feature table in its OWN cycle. **Absolutely no player feature
  enters the frozen arm set of NFL-WINPROB-NG-SCORED-V1** (separate cycle IDs, worktrees,
  artifacts; nothing in this cycle touches that cycle's freeze, arms, ledger or worktree).
- Hard boundaries: no scored computation, no win-prob metrics on outcomes, no S1/paper/live/
  betting/purchases/push/merge, no backfill, no edits to frozen artifacts; calibration
  vocabulary only; internal-research-only rights posture (nflverse-data CC BY 4.0 pinned;
  underlying league rights unverified, fail-closed).

## Inheritance (re-measured 2026-10-05)

- Verified data (WINPROB-PLAYERFEAT-PREP-V1 lanes C + D): weekly player stats 2024–2026 +
  snap_counts 2025–2026 sha-pinned at `~/.my-quantitative-data/playerdata-prep-v1/nfl/`;
  crosswalk players.parquet at `~/.my-quantitative-data/playerfeat-prep-v1/nfl/raw_players/`
  (sha 485b1980…; GSIS join 100% all seasons; PFR 99.73/99.82%; round-trip 97.55% 2026;
  32/32 teams). Residual blockers carried: snap_counts ≤1-week in-season lag; release-cadence
  (not row-level) availability — frozen sha256s are the evidence anchor; 1 NaN-player
  placeholder row per week excluded; **target-game injury/active/DNP/starter status remains
  NOT_RUN_PIT** (law).
- Baseline yardstick for any future successor: NFL B1* = B1-c own-Elo K=40 HCA=0 (frozen,
  NFL-WINPROB-SCORED-V1). 2026 split law: 63 played = NOT_RUN prospective forever; 209 future;
  earliest future kickoff 2026-10-06T00:15Z (re-measure at build time).
- Feature groups inherited from predecessor lane-C proposals (design): QB form/availability
  (prior-games passing production), skill-player usage mass (targets/carries share), absence
  proxy (missing snap-share of top players from prior games). All strictly prior-game
  aggregates via kickoff-time as-of joins (leak guards proven in the predecessor PIT audit).

## Tasks

1. Lane B — BUILD: freeze FEATURE_SPEC.md (exact scalars per team-game; 1 all-zero NaN-player
   placeholder row per week excluded; bye-week handling; in-game-injury risk documented — a
   player injured mid-game still logs prior-game production, the aggregate is lagged evidence
   by design); build the frozen table (one row per (game_id, team side), games 2024–2026 with
   stats data available — window disclosure: stats release history limits prior-game
   aggregates; measure the first season where prior-game windows are fully computable and
   disclose) into `~/.my-quantitative-data/nfl-playerfeat-prep-v1/features/` with
   FEATURE_TABLE_MANIFEST.md (+json: input/output sha256, row counts, per-season coverage,
   join rates via crosswalk, missing-data rule outcomes); as-of columns embedded
   (kickoff_utc, n_prior_games_used, asof_rule_version); NO outcome columns; deterministic;
   --selftest leak guards (kickoff strict inequality; target-game absence; crosswalk join
   canaries incl. a pfr-null player case).
2. Lane D — INDEPENDENT VERIFIER: re-hash inputs+output; re-join rates with own code;
   independently recompute ≥6 sampled rows incl. one bye-week case and one pfr-null case;
   missing-data rule behavior; 0-scored grep; boundary compliance (no touch of
   NFL-WINPROB-NG-SCORED-V1 worktree/artifacts — verify by git status of that worktree
   unchanged). VERIFICATION_REPORT.md + verdict.
3. Controller: 2026 recount at integration (played/future/earliest future kickoff) recorded
   in the control state for the readiness report.

## Boundaries

Lanes write only in their lane dirs + `~/.my-quantitative-data/nfl-playerfeat-prep-v1/`;
all predecessor data read-only (EXTEND-ONLY); no git by lanes; registry via researchctl
from root. Lane artifacts land uncommitted; controller commits per lane.

## Artifacts

`lanes/B_BUILD/ · lanes/D_VERIFY/ · lanes/DISPATCH/` under the integration worktree; control
state under `research/control/NFL-PLAYERFEAT-PREP-V1/`.

## Terminal outcomes (negative-first)

PREP_COMPLETE_PENDING_OWNER_DECISIONS | BLOCKED_DATA_RIGHTS | BLOCKED_TOOLING | TECHABORT_*.
A scored NFL player-feature successor (which would ALSO require re-registration and its own
freeze/A7/GO, and must never modify the prospective cycle's frozen arms) may be proposed only
on this cycle's PREP_COMPLETE verdict + owner instruction + fresh registration.
