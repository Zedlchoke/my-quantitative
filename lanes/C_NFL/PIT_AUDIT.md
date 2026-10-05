# PIT AUDIT — Lane C (NFL PLAYER DATA) · WINPROB-PLAYERDATA-PREP-V1

Doctrine §13 as inherited: three times (event / effective / available); retrieved_time never
substitutes available_time. Same-game player stats of the target game are BANNED as features.
Verdicts below are per candidate field. Everything measured from bytes; no scored computation.

## 1. Kickoff-time canonicalization (as-of join basis) — PASS (with caveats)

Source: on-disk `games.csv` (nfl-nflverse-v1, 2026-10-04 pull; ng-prep 2026-10-05 copy agrees).

Documented convention (verbatim, Lee Sharpe DATASETS.md / nflreadr dictionary, quoted in the
corpus ATTRIBUTION.md):

> "The kickoff time of the game. This is represented in 24-hour time and the Eastern time
> zone, regardless of what time zone the game was being played in."

Canonicalization used (and needed by any as-of join):

```python
kickoff_et  = pd.to_datetime(gameday) + pd.to_timedelta(gametime + ":00")
kickoff_utc = kickoff_et.dt.tz_localize("America/New_York",
                                        nonexistent="shift_forward", ambiguous="NaT"
                                       ).dt.tz_convert("UTC")
```

Caveats measured:

- `gametime` missing on 259/7,548 rows — **all season 1999** (as-of join impossible there;
  irrelevant for 2016+/2021+ windows actually in scope).
- 1999 is also the only season with `kickoff_utc` NaT risk; 2000+ all localize cleanly.
- Away games in London/Munich are listed in ET by convention — handled by uniform ET→UTC.
- DST transitions: `ambiguous="NaT"` + `nonexistent="shift_forward"` guards the two 1–2 AM ET
  edge cases (spring-forward Sundays); zero NaT produced on 2021–2026 seasons (verified by
  non-null kickoff_utc counts = non-null gametime counts).

## 2. Prior-games aggregate = as-of join constructible — PASS (worked example)

Worked example (target game `2024_11_KC_BUF`, kickoff_utc **2024-11-17T21:25:00Z**):

Prior 3 KC games strictly by `kickoff_utc < target kickoff_utc`:

| game_id | kickoff_utc | week |
|---|---|---|
| 2024_08_KC_LV | 2024-10-27T20:25Z | 8 |
| 2024_09_TB_KC | 2024-11-05T01:15Z | 9 |
| 2024_10_DEN_KC | 2024-11-10T18:00Z | 10 |

P.Mahomes (player_id 00-0033873) prior-3 aggregates from `stats_player_week_2024.parquet`:

| game_id | pass_yds | pass_td | int | att |
|---|---|---|---|---|
| 2024_08_KC_LV | 262 | 2 | 1 | 38 |
| 2024_09_TB_KC | 291 | 3 | 0 | 44 |
| 2024_10_DEN_KC | 266 | 1 | 0 | 42 |
| **prior-3 total** | **819** | **6** | **1** | **124** |

Leak guards asserted in code: (i) every aggregated game has `kickoff_utc` strictly less than
the target kickoff; (ii) the target game is absent from the aggregate set. Both PASS.
Bye-week correctness: the window is kickoff-ordered (`tail(3)` on kickoff_utc), not
week-ordered — byes drop out naturally. Note kickoff ordering also handles Thursday/Saturday
short weeks that week-numbering would misorder.

## 3. Prospective-only window (2026) — re-verified at this session's download moment

- `stats_player_week_2026.parquet` (build 2026-10-05T05:30:28Z) contains **63** games; all 63
  have `kickoff_utc` < download moment 2026-10-05T07:18Z; **zero** rows for games kicking off
  after the download moment; the Monday-night game at 2026-10-06T00:15Z (frozen split law's
  earliest future kickoff) has **no** stats rows.
- Frozen law "63 played / 209 future" consistent. Measured nuance (documented, not a
  contradiction): on-disk schedule snapshots are hours-stale relative to the law — the
  2026-10-04-pulled games.csv shows 49 scored (the Oct-4 London + SNF games finished after
  that pull), the 2026-10-05 ng-prep snapshot shows 62 scored + 210 unscored with earliest
  unscored kickoff 2026-10-05T00:20Z (the Oct-4 SNF, in flight when that snapshot was pulled).
  The stats file itself (today 05:30Z build) is the freshest evidence and matches the law.

## 4. Per candidate field

| # | candidate field | PIT basis | verdict |
|---|---|---|---|
| F1 | QB prior-k-game passing production (yds/TD/INT/att, per-dropback rates) | weekly stats rows carry game_id only; kickoff time joined from games.csv (§1); as-of filter proven (§2); stats availability: release build cadence is hours after game end, days before next kickoff | **PASS** (as-of constructible) |
| F2 | Backup-QB / starter snap-share detection (prior-game QB offense_snaps share) | snap_counts release; prior games only; cadence 2026-10-02 build covers through week 3 — published days before the following week's kickoffs | **PASS** (as-of constructible, 2025/2026 files in hand; id crosswalk vs GSIS needed — see §5) |
| F3 | Skill-player usage mass (targets/carries + target_share/air_yards_share/wopr prior-k) | same as F1 | **PASS** (as-of constructible) |
| F4 | Key-position absence proxy (non-participation / zero snaps in prior game(s)) | absence observed in *prior completed* games only | **PASS** (PIT-safe proxy; noisy — see FEATURE_PROPOSALS risks) |
| F5 | Target-game injury/active/DNP status (injuries CSV, weekly rosters) | injuries files carry NO per-record publish timestamps (prior-cycle law, re-confirmed: static CSV dumps); weekly_rosters release not yet audited for availability timing; no pre-game publish evidence | **NOT_RUN_PIT** (blocker carried — do not fake) |
| F6 | Same-game player stats (any) | banned by doctrine | **BANNED** |
| F7 | pbp per-player participation for prior-game snap counts from ON-DISK pbp 2021–2025 | on-disk pbp parquets measured: 372 cols are play-level with event-attribution player columns (`passer_player_id`, `pass_defense_1_player_id`, …) — **no per-player participation/snap columns on disk** | **NOT_RUN_PIT on-disk** (data exists as separate `pbp_participation` release 2016–2025, listed not downloaded); superseded by F2's snap_counts as the PIT-safe snap source |

## 5. Crosswalk dependency (blocking detail for FEATURE-PREP, not for PIT verdicts)

`snap_counts` keys `pfr_player_id`; weekly stats key GSIS `player_id`. The `players` release
(`players.parquet`) publishes the crosswalk. Not downloaded this session (documented from the
release listing). FEATURE-PREP must fetch it and re-hash before any snap-share feature is
built; until then F2 is PASS-as-constructible only at team/position level (e.g. "starting QB
offense_pct" identifiable within snap_counts alone by position+max-snaps heuristics, no
cross-player id join needed for team-level share).

## 6. Explicit non-claims

- No availability/publish timestamps per stat row exist in the files (release-level
  `timestamp.json` only). PIT safety rests on release build cadence (stats ≤ hours post-game;
  snap_counts ≤ days post-week) + kickoff-time as-of filtering — both far inside any next-week
  kickoff margin measured (minimum observed gap: Thursday-night rematches ≈ 3.5 days).
- Nothing here scores any model; no win-prob metric was computed (language law respected).
