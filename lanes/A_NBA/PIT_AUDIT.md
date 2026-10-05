# PIT AUDIT — NBA player box features (Lane A, WINPROB-PLAYERDATA-PREP-V1)

Law (doctrine §13 as applied by the plan): features forecasting game g may use
only rows from games whose tip time (UTC) is **strictly before** the forecast
time; same-game stats are banned; target-game roster/active/starter/DNP status
is **NOT_RUN_PIT** unless a pre-game publish timestamp is evidenced; prior-game
aggregates are PIT-safe only via a proven as-of join on tip time UTC. Anything
unprovable is NOT_RUN_PIT, never inferred PASS.

## 1. Verdict summary per candidate field

| candidate feature field | PIT verdict | basis |
|---|---|---|
| player minutes / points / usage aggregates from prior games (as-of join on tip_utc) | **PIT_SAFE_CONSTRUCTIBLE** (proven join; not a scored PASS) | §2, §3 |
| team minutes-mass prior-k games | **PIT_SAFE_CONSTRUCTIBLE** | §3 worked example |
| top-player recent form prior-k games | **PIT_SAFE_CONSTRUCTIBLE** | same join |
| key-player absence indicator (prior-game DNP sequence) | **PIT_SAFE_CONSTRUCTIBLE** (as prior-game evidence) | same join |
| target-game `starter` | **NOT_RUN_PIT** | no pre-game publish timestamp; the flag is a post-game field |
| target-game `did_not_play` / `reason` / `active` | **NOT_RUN_PIT** | same |
| target-game injury status (injuries release of same store) | **NOT_RUN_PIT** | not downloaded; no publish-time schema evidenced |
| same-game player stats (any column of game g's box) | **BANNED** | law |
| box rows as-of availability timestamps (per-row retrieved/available time) | **NOT_RUN_PIT** | store has no per-row publish timestamps; only tip-time ordering is usable |

No field above is a scored result. "PIT_SAFE_CONSTRUCTIBLE" means: the as-of
join needed to compute the feature pre-tip is proven constructible from on-disk
schedule times + downloaded box rows. Actual feature values and any skill
assessment remain out of scope (no scored computation this cycle).

## 2. Timing inputs verified (sample join keys)

Schedule corpus carries both fields; verified on **every** row of the three
sampled season files (parse + UTC-normalize via `pd.to_datetime(..., utc=True,
format='mixed')`):

- `game_date_time` — local time with offset (e.g. `2021-07-20T21:00:00.000000-0400`)
- `start_date` — UTC (e.g. `2021-07-21T01:00Z`)

Equality after UTC normalization: 1317/1317 (2016), 1204/1204 (2021),
1330/1330 (2026). Parse failures: 0. The player-box rows carry a copy of
`game_date_time`/`game_date`, but the **authoritative tip time for the as-of
join is the schedule row** (both corpora key on the same ESPN `game_id`;
join rate and key equality proven in COVERAGE_SCHEMA.md §4).

## 3. Worked as-of join example (one team, one game, prior 5 by tip time)

Executed 2026-10-05 on the downloaded 2021 sample (commands + output in
`provenance/anomaly_and_pit_example.txt`):

- Target: game_id `401307387`, MIL@WSH, tip_utc **2021-03-15 23:00:00+00:00**
  (from schedule `game_date_time`).
- MIL team_id taken from player-box rows; all MIL games with tip_utc strictly
  `< target tip` sorted; prior 5 = {401267680 (02-28), 401267700 (03-03),
  401267715 (03-05), 401307356 (03-12), 401307372 (03-14)}.
- Invariant checked: `max(prior tip) < target tip` → **True**.
- Aggregation at forecast time (i.e. using only those 5 games): MIL
  minutes-mass per prior game = 240.0, 240.0, 240.0, 238.0, 239.0 → mean
  **239.4**. This is exactly the constructible pre-tip feature.

## 4. Honest limits of the construction (recorded, not silently assumed)

1. **No per-row availability timestamps exist** in the box store. The
   PIT-safety of prior-game aggregates rests on the tip-time ordering law plus
   the operational fact that a team's prior game completes before its next tip.
   Conservative margin option for the future build: require
   `prior_game.tip_utc + 3h < target_game.tip_utc`, or freeze forecasts at a
   fixed pre-tip time (e.g. 12:00 UTC game day) — design decision for the
   successor step, not assumed here.
2. **Target-game availability (starter/DNP/injury report) is NOT_RUN_PIT.**
   The box store publishes `starter`/`did_not_play`/`reason` only as post-game
   facts; the store's `espn_nba_injuries` release was NOT downloaded and shows
   no publish-time schema in the evidence collected → cannot be used as a
   feature basis without its own PIT verification.
3. Trades/mid-season team changes: rows carry the `team_id` the player played
   FOR in that game, so prior-aggregates keyed by (game team) are internally
   consistent; but "absence from team X" after a trade to Y must not be read
   as injury/rest — the absence indicator must key on player-team continuity
   (roster-crosswalk check), which is NOT built this cycle → the indicator's
   trade-handling remains a design risk, see FEATURE_PROPOSALS.md.
4. Store rebuilds (last 2026-09-09) mean late corrections to historical boxes
   are possible; PIT correctness of the join does not depend on it, but exact
   reproducibility requires pinned sha256 (done in DOWNLOAD_MANIFEST.md).
