# DATA_REFRESH_20261009_CONTROLLER — WNBA-WINPROB-2026-REMAINDER-V1

Controller prep action (no GO typed, no forecast computed, zero scored cells,
zero real ledger rows). Append-only new lineage dir
`~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261009/`.
Purpose: absorb completed 2026 playoff G2 results as HISTORY for the next
batch anchor; re-prove store lineage before the ET-day 2026-10-09 anchor
17:20:00Z. Heavy lock `FREE_PROVEN` pre-pull (2026-10-09T01:1xZ).

- Pull instant: 2026-10-09T01:12–01:14Z · puller `curl`, public release
  assets, no auth, $0. Store lineage identical to lane W26 precedent.

| file | tag | retrieved_at (UTC) | bytes | sha256 |
|---|---|---|---|---|
| wnba_schedule_2026.csv | espn_wnba_schedules | 2026-10-09T01:12Z | 2,569,486 | `e32d3995abbd9de006c6ff294395874503e4de5a4a0d3e73fc01e44bc82b08e3` |
| team_box_2026.csv | espn_wnba_team_boxscores | 2026-10-09T01:12Z | 302,488 | `0218105afd2374a0187317f4b23025764d8b63501ac7b1f32479e44d67a9aba2` |
| timestamp.txt | espn_wnba_schedules | 2026-10-09T01:12Z | 24 | `df23889dd0032529056b9457535cbe06fe4ffc5b24114a744073897091098a2a` |
| timestamp.json | espn_wnba_schedules | 2026-10-09T01:12Z | 43 | `6585e2c6dad2fbc215d1c0ea6c0dc1a14d0c01d7ffc6b910f02a5f1a8ed4323c` |
| package_function.txt | espn_wnba_schedules | 2026-10-09T01:12Z | 29 | `3653be1c98884f9b4f044b0dca24ff20612adc906c5930264cced16ee9975030` |
| release_store_README.md | (main) | 2026-10-09T01:12Z | 292,938 | `ab5be8c4c7a303883f6e8eea134b7737ff06eab884b8b6303e18d618ca4d9df9` |
| espn_wnba_schedules_tag_meta.json | (tag metadata capture) | 2026-10-09T01:13Z | text | n/a |
| espn_wnba_team_boxscores_tag_meta.json | (tag metadata capture) | 2026-10-09T01:13Z | text | n/a |

## Measured findings

1. **Store lag disclosed**: asset `wnba_schedule_2026.csv` updated upstream
   **2026-10-07T10:41:15Z** — i.e. AFTER the lane pin (06:44Z) but BEFORE G2
   was played (tips 2026-10-07T23:30Z / 2026-10-08T01:30Z). Both G2 rows
   (`401918297`, `401918298`) are still `pre` / `STATUS_SCHEDULED` 0–0 in this
   pull; census unchanged 360 rows = 345 `post` + 15 `pre`. Under the
   completed-only stream law the G2 results are therefore NOT YET stream
   material from this lineage. A re-pull immediately before the batch append
   (still strictly before the anchor) is REQUIRED at GO execution; whatever
   the store carries at that instant is the best-available completed-only
   state. No result is ever inferred from a non-store source (fail-closed).
2. **Extension-only holds at cell level**: 0 shared game_ids missing;
   0 tip-time changes; 0 cell changes across all 77 original columns for all
   360 rows. The schema grew by exactly two upstream-added columns
   (`home_logo_dark`, `away_logo_dark`; +41,314 bytes, ESPN logo fields).
   `predict.py` consumes rows by column NAME (mapping law), so the added
   columns are inert. `team_box_2026.csv` byte-identical to the pin.
3. **Remaining-slate census (pre, 15 rows)** — anchors recomputed as
   `T0(ET-day) − 6h10m`:
   - `401918297` 2026-10-07T23:30Z + `401918298` 2026-10-08T01:30Z (ET-day
     10-07): **anchors 17:20Z/19:20Z 2026-10-07 — both PASSED with no GO →
     NOT_RUN forever (never backfilled).**
   - `401918299` 2026-10-09T23:30Z + `401918300` 2026-10-10T01:30Z (ET-day
     10-09): **batch anchor 2026-10-09T17:20:00Z (exclusive)** — the only
     capturable batch today.
   - `401918302` 04:00Z + `401918301` 18:00Z (ET-day 10-11): anchor
     2026-10-10T21:50Z.
   - `401918303` + `401918304` 04:00Z (ET-day 10-14): anchor 2026-10-13T21:50Z.
   - Finals `401918305`–`401918311` (ET-days 10-17…10-31): day anchors
     2026-10-17T13:20Z (305), 2026-10-19T17:50Z (306), 2026-10-22T17:50Z (307),
     2026-10-24T13:20Z (308), 2026-10-26T17:50Z (309), 2026-10-29T17:50Z (310),
     2026-10-31T17:50Z (311) — == FREEZE_PACKET §6 pins (a controller-note
     anchor-date drift for 306/307/309/310 was found by the fresh-context A7
     re-audit and corrected in place; the binding pins live in
     FREEZE_PACKET.md, which the ledger computes from schedule bytes) — teams
     TBD at snapshot (deterministic `tbd:<abbr>` fallback law, disclosed in
     predict.py).
4. Test battery re-run at branch head `46200b30` (controller, worktree cwd):
   **79 passed** (67 at A7 + 12 realpath-lane tests). Green.
5. Paper cross-check (no double-record): the shared paper ledger
   (`sports-papertrade-exec-v1`, GO-consumed cycle) already holds
   FORECAST/DECISION rows for `401918297/298` (settled) and `401918299/300`
   (BET_PAPER open), sourced `wnba26_predict@state=d3cc0218…`. This cycle's
   ledger `wnba_2026_remainder_ledger@1` remains a SEPARATE artifact with
   zero real rows; this cycle's GO does not touch the paper ledger, and the
   paper consumption of this cycle's rows requires both gates' GOs
   (plan L53-55). No double-record, no ledger repair.

GO `GO WNBA WINPROB 2026 REMAINDER V1 PREDICTIONS` remains
REGISTERED_NOT_CONSUMED. Typed GO is the owner's alone.
