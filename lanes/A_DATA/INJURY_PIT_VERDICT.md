# INJURY_PIT_VERDICT — Lane A · DATA (nflng-a-data), cycle NFL-WINPROB-NG-PREP-V1

Question: is any free injury/availability source BOTH (a) $0-rights-verified
verbatim AND (b) per-record publish timestamps provably ≤ kickoff − report
cadence on a SPOT-CHECKED SAMPLE? If either fails → NOT_RUN_PIT. No retro-fill
of injury data may ever be treated as PIT.

**VERDICT: NOT_RUN_PIT for every candidate. No availability feature may enter
any prospective program from these sources as of this audit.**

## Candidate 1 — nflverse-data `injuries` release (primary; downloaded and inspected)

- Files held: `~/.my-quantitative-data/nfl-ng-prep-v1/raw_injuries_20261005/`
  (`injuries_2026.csv` 120,160 B sha256 `5af78248…3466b`, asset updated_at
  2026-10-04T13:08:58Z; `injuries_2025.csv` 696,006 B sha256 `873ca160…eb735`,
  asset updated_at 2026-09-07T12:23:41Z; release timestamp.json
  "2026-10-04 09:08:56 EDT" = 2026-10-04T13:08:56Z).
- (a) Rights: **PASS** — same nflverse-data release family, CC BY 4.0
  re-verified verbatim 2026-10-05 (DATA_AUDIT_NFL_NG.md §1).
- (b) Per-record publish timestamps: **FAIL — categorical.** The current schema
  (identical in both held seasons) is exactly:
  `season, season_type, game_type, team, week, gsis_id, position, full_name,
  first_name, last_name, report_primary_injury, report_secondary_injury,
  report_status, practice_primary_injury, practice_secondary_injury,
  practice_status` — there is **no timestamp column of any kind** (no
  date_modified, no date_time; a column-name search over the header for
  date/time/modif returns zero). There is nothing to spot-check: each row is a
  (team, week) report snapshot as of the release compile, which for the
  audited compile (13:08:56Z Sat) post-dates that week's kickoff window.
  Whether any given "Out/Questionable" status was public before kickoff is
  **unprovable from the released bytes**.
- History note: the predecessor cycle rejected this asset because its then
  `date_modified` column did not prove announcement-before-kickoff. That column
  has since been REMOVED from the release entirely — the failure mode is now
  stronger (no per-record time at all).
- Verdict: **NOT_RUN_PIT** (rights PASS, PIT unprovable).

## Candidate 2 — nflverse-data `depth_charts` release (availability adjacent)

Same release family → rights would be PASS, but no download was performed and
the nflreadr-era schema carries no announced per-record publication timestamp
that would survive the (b) spot-check; unverified. Verdict: **NOT_RUN_PIT
(candidate, unverified)**. If a successor wants it, the burden is a held-file
spot-check proving each (team, week) depth-chart snapshot was published ≤ the
week's first kickoff minus the report cadence.

## Candidate 3 — nflverse-data `weekly_rosters` release (availability adjacent: game_status / inactives)

Same release family → rights would be PASS; no download performed. Weekly
roster `game_status` (e.g., inactives) is compiled per week; per-record publish
time ≤ kickoff is again unprovable from release metadata alone. Verdict:
**NOT_RUN_PIT (candidate, unverified)**. Note additionally that full inactives
are typically announced ~90 minutes before kickoff — even a timestamped weekly
snapshot would prove less than a true PIT pre-kickoff signal unless its publish
time is strictly before kickoff.

## Other free candidates (not exercised, $0 constraint noted)

- Media-scraped historical injury archives (e.g., Kaggle 2010–2020
  media-sourced sets): rights unverifiable at $0 (platform terms +
  unknown upstream). Verdict: **NOT_RUN_PIT (rights FAIL/BLOCKED_DATA_RIGHTS-candidate)**.
- NFL.com / team official injury reports: scraping rights not granted; prior
  cycle verdict FAIL stands. **NOT_RUN_PIT**.

## Consequence (carried into handoff authority_claims)

Availability/injury mechanisms (predecessor H-C3 shape) remain NOT_RUN_PIT for
any 2026-forward prospective program. A candidate can only be cleared by a
source whose released bytes carry per-record publish timestamps that a held-file
spot-check proves are ≤ kickoff − report cadence — none found this cycle at $0.
No retro-fill: historical injuries files must never be back-converted into
"pre-game known/unknown" features.
