# PIT AUDIT — NBA player-feature table (Lane A_NBA_FEAT, WINPROB-PLAYERFEAT-PREP-V1)

Law carried from the predecessor (doctrine §13): features for game G may use
only rows of games with tip STRICTLY before G's tip; same-game stats BANNED;
target-game roster/active/starter/DNP/injury status NOT_RUN_PIT (no pre-game
publish timestamps exist in this store). Feature construction only — no scored
metric anywhere in this lane.

## 1. Verdict summary for the frozen table

| element | PIT verdict | basis |
|---|---|---|
| prior-game aggregates via as-of join on schedule tip_utc (strict `<`) | **PIT_SAFE_CONSTRUCTIBLE** (proven; not a scored PASS) | §2, §3 |
| Group A/B/C scalars as frozen (FEATURE_SPEC §3–§5) | **PIT_SAFE_CONSTRUCTIBLE** | §3, §4; independent recompute 8/8 rows |
| target-game `starter`/`did_not_play`/`reason`/`active` | **NOT_RUN_PIT** — NOT used anywhere in the build | no pre-game publish timestamp; emission happens before the target's own rows are committed (code ordering), and play-in targets are never committed |
| target-game injury status | **NOT_RUN_PIT** (not downloaded, no publish schema) | predecessor §4 |
| box rows with per-row availability timestamps | **NOT_RUN_PIT** (none exist; only tip ordering usable) | predecessor §4 |
| exhibition games (19) | present as targets, flagged `is_exhibition` (pre-game-derivable from event team ids); never in franchise priors | COVERAGE_AUDIT §6 |

## 2. Timing inputs verified on all 11 seasons (bytes)

`game_date_time` (arena-local + offset) parses with 0 failures and equals
`start_date` (UTC) after UTC normalization on **14,254/14,254 schedule rows
(100%)**. The authoritative tip is the schedule row keyed by the same ESPN
`game_id` as the box (join 100%/99.92% of played games, 0 orphans —
COVERAGE_AUDIT §1). Worked predecessor anchor: game `401307387` (Bucks @
Wizards) `game_date_time=2021-03-15T19:00:00.000000-0400` → `tip_utc
2021-03-15 23:00:00+00:00` — reproduced in `--selftest`
(`mil_tip_utc_2021_03_15_23Z` PASS).

## 3. Worked as-of examples (numbers reproduced from the built table)

### 3a. Predecessor anchor — MIL, game 401307387, tip 2021-03-15T23:00Z

- Prior-5 MIL games by strict tip `<`: 401267680 (02-28), 401267700 (03-02),
  401267715 (03-04), 401307356 (03-11), 401307372 (03-13) — **exactly the 5
  game_ids documented by the predecessor** (`mil_prior5_ids` PASS).
- Raw minutes-mass per prior game from this build: 240.0, 240.0, 240.0, 238.0,
  239.0 → mean **239.4** (`mil_prior5_mean_mass_239p4` PASS, tolerance 1e-9) —
  independently reproduces predecessor PIT_AUDIT §3.
- Emitted table row (team_id 27 = MIL, away): team_games_so_far=37,
  n_prior_games_used=37, feature_neutral=0, `a_top5_share_k5=0.640980`,
  `a_load_top5_k5=0.002198`, `b_form_top3=0.011803` (n=3), `c_abs_out=1`,
  `c_abs_streak=1`. All inputs have tip strictly < 23:00Z; game 401307387
  absent from every input set (asserted).

### 3b. 2016 Finals Game 7 — game 400878160, CLE @ GSW, tip 2016-06-20T00:00Z

- Team 9 (GSW, home): priors=105 (full season + playoffs, strictly earlier),
  `a_top5_share_k5=0.712854`, `a_load_top5_k5=0.046717`, `b_form_top3=-0.067536`,
  `c_abs_out=1`, `c_abs_streak=0`. Team 5 (CLE): priors=102,
  `a_top5_share_k5=0.745296`, `a_load_top5_k5=0.067852`, `b_form_top3=-0.052923`,
  `c_abs_out=0`, `c_abs_streak=0`. Independent recomputation matches both rows
  exactly (`recompute_match[2016:400878160:*]` PASS).
- Early-window behavior: 2016 opener 400827888 both sides priors=0 →
  feature_neutral=1, all scalars 0.0; 2026 opener 401809243 identical pattern.

### 3c. Leak-guard checks inside `build_features.py --selftest` (42/42 PASS)

- For 8 sample team-rows (openers + late-season games of 2016/2021/2026):
  (i) every prior game's tip strictly `<` target tip; (ii) the target game_id
  absent from the prior set; (iii) all six scalars equal an independent
  pandas recomputation (separate code path) to <1e-12.
- Neutral rule asserted both directions; scalars zero exactly when neutral.
- 0 duplicate (game_id, team_id); row count = 2 × 14,187.

## 4. Trade guard (Group C) — real-data case + logic tests

- **Real case (measured):** Patty Mills (athlete_id 4004), 2025: 17 usable
  games for UTAH (26) through 2025-01-28 (last: 401705227, tip
  2025-01-29T03:00Z), then 13 usable games for LAC (12) from 2025-02-04
  (401705281). The store carries ONE stale UTAH roster-scaffold row after his
  departure: game 401705243 (2025-01-30), `did_not_play=True`, reason
  "COACH'S DECISION". Measured outcome: his season-to-date UTAH minutes at the
  affected targets were 260 vs ≥1,112 for the actual top-3, so he was never in
  the top-3 absence set; UTAH rows around the departure show `c_abs_out=0`,
  `c_abs_streak=0`. The trailing-10-appearance guard (frozen FEATURE_SPEC §5)
  additionally bounds any counted absence to ≤10 team-games after a player's
  last appearance for that team — the successor-noted "traded-away player read
  as injured" exposure is closed both by membership (top-3 requires recent
  minutes mass) and by the guard.
- **Logic tests (synthetic, in `--selftest`, all PASS):** a player who
  appeared within the trailing 10 team-games has his DNP counted; a player
  whose last appearance is >10 team-games before the missed game has
  `_guard=False` and is never counted; `abs_streak` walks consecutive guarded
  DNP games (1, 2, 3 reproduced on constructed timelines) and stops at the
  first game with a usable row or no row at all.

## 5. Honest limits (recorded, not assumed)

1. No per-row availability timestamps: PIT-safety rests on tip ordering plus
   the operational fact that a team's prior game completes before its next tip
   (same predecessor caveat). A future conservative variant (tip + 3h margin)
   remains a successor design decision; this build freezes the strict-tip law.
2. Target-game availability is never used; DNP/`reason` enter ONLY as
   prior-game facts (post-game facts of earlier games).
3. Store rebuilds (last 2026-09-09) can change bytes; reproducibility is pinned
   by input sha256 in FEATURE_TABLE_MANIFEST.json.
4. Exhibition games (19) are emitted as targets per the dispatch's
   "every played game" law and flagged; a successor should filter
   `is_exhibition=0` for franchise-game forecasting (disclosed, not silently
   dropped).
