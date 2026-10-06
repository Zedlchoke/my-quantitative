# WINDOW_RESOLUTION — WNBA-PLAYERFEAT-SCORED-V1 · lane EXEC · 2026-10-06

Status: **BINDING — raw-bytes re-verification CONFIRMS the controller's pre-measurement.
NO freeze contradiction. 2026 COMPLETE at freeze ⇒ OOS = [2020, 2021, 2022, 2023, 2024,
2025, 2026] exactly as frozen.**

Measured by lane EXEC from bytes only, schedule/tip facts only. **No outcome value was
read anywhere in this determination** (the only columns consumed are `tip_utc` /
`date` / `game_date` / game counts / status labels / id sets).

## 1. The law (quotes)

- Plan `plans/PLAN_wnba_playerfeat_scored_v1.md` (Inheritance): "WALK-FORWARD OOS = final
  7 complete seasons at freeze — pin 2019–2025 is NOT chosen here: freeze pins
  OOS = [2020..2026] (2026 in-progress games excluded from any historical evaluation;
  only completed seasons counted post-GO; **placeholder TBD rows never games**)."
- Predecessor packet `SUCCESSOR_PACKET_SCORED.md` §1 (window law): "WALK-FORWARD OOS:
  final 7 complete seasons at the successor's data freeze — placeholder 2019–2025 if 2026
  incomplete at freeze, else 2020–2026 ... 2026 if-necessary TBD rows are placeholders,
  never games."
- Dispatch `DISPATCH_EXEC.md` Task 1: completeness is measured from SCHEDULE facts
  (tip_utc) against the freeze instant; zero future-tipped 2026 universe games at freeze
  ⇒ 2026 COMPLETE ⇒ the pin stands.

## 2. Freeze anchors (all candidates measured; conclusion is anchor-invariant)

| anchor | instant (UTC) | provenance |
|---|---|---|
| feature-table last write (earliest candidate — used) | **2026-10-05T09:26:30Z** | mtime of `wnba_player_features_2002_2026.parquet` (deterministic table; no wall-clock inside it — the mtime is the build/write instant) |
| registry heartbeat of this cycle at freeze | 2026-10-05T11:47:45Z | `CYCLE_REGISTRY.json` row `heartbeat_utc` |
| state heartbeat cited by the controller | 2026-10-05T12:10:00Z | DISPATCH_EXEC Task 1 |

The latest 2026 universe tip (2026-10-03T01:00:00Z, below) precedes the EARLIEST anchor by
~2.35 days, so "zero future tips at freeze" holds under every candidate anchor.

## 3. Feature-table re-measurement (frozen table, sha re-verified)

`wnba_player_features_2002_2026.parquet` sha256
`ceaf10ba33e705b9569a11cec2aa33e1875e372c35d643ed5d80d5e757ffc7bf` — matches the freeze
manifest and the T_SELECT-era pin. Schedule facts per season (1 game = 2 rows):

| season | rows | games | min tip (UTC) | max tip (UTC) | rows with tip > 2026-10-05T12:10Z |
|---|---|---|---|---|---|
| 2019 | 440 | 220 | 2019-05-24T23:30Z | 2019-10-11T00:00Z | 0 |
| 2020 | 294 | 147 | 2020-07-25T16:00Z | 2020-10-06T23:00Z | 0 |
| 2021 | 420 | 210 | 2021-05-14T23:00Z | 2021-10-17T19:11Z | 0 |
| 2022 | 480 | 240 | 2022-05-06T23:00Z | 2022-09-18T20:00Z | 0 |
| 2023 | 522 | 261 | 2023-05-19T23:00Z | 2023-10-19T00:00Z | 0 |
| **2024** | 526 | 263 | 2024-05-14T23:00Z | **2024-10-21T00:00Z** | 0 |
| **2025** | 622 | 311 | 2025-05-16T23:30Z | **2025-10-11T00:00Z** | 0 |
| **2026** | 682 | **341** | **2026-05-08T23:30Z** | **2026-10-03T01:00Z** | **0** |

**Match vs the controller's pre-measurement: EXACT** (2026 = 682 rows / 341 games, tip
range 2026-05-08T23:30Z → 2026-10-03T01:00Z, zero future tips).

## 4. RAW corpus cross-check (the decisive re-verification)

Lineage: the feature table's `tip_utc` is `pd.to_datetime(ESPN schedule date, utc=True)`
built from `~/.my-quantitative-data/wnba-v1/raw/espn_schedules/` (FEATURE_SPEC.md of the
predecessor lane B_WNBA_FEAT); the roster_audit corpus
(`~/.my-quantitative-data/wnba-prep-v1/roster_audit/`, 50 CSVs + 3 meta) is the other raw
side. Universe filter law (COVERAGE_AUDIT.md §2): keep `status_type_state == 'post'`;
drop Forfeit/Postponed; drop All-Star aliases; **TBD placeholders are `pre` and already
excluded**; never filter on score presence (0–0 prefill rows stay).

Raw ESPN schedule 2026 (`wnba_schedule_2026.csv`, 360 rows):

- **343 rows `post`** — max date **2026-10-03T01:00Z**, **0 rows dated after any anchor**.
- **17 rows `pre`** (TBD placeholders) — 15 of them dated after the controller heartbeat,
  through **2026-11-01** (if-necessary playoff slots). These are the only future-tipped
  raw rows, and they are **excluded by the frozen law** ("placeholder TBD rows are `pre`
  and already excluded"; plan: "placeholder TBD rows never games"). They are not games;
  their existence is not a future-tipped 2026 GAME.
- Set identity (raw `post` ids vs frozen-table 2026 ids): 343 post − **2 exclusions** =
  **341 = feature table exactly** (intersection 341, feature-table-only 0). The 2 raw-post
  exclusions, both identified from raw bytes:
  - `401857072` — 2026-07-17 DAL@NYL, `status_type_state='post'` (ESPN quirk) but
    `status_type_description='Postponed'`, 0–0 prefill, note "Travel Issues - Makeup date
    July 20" → dropped by the frozen drop-Postponed law (its July 20 makeup IS in the
    universe; the 0–0 score is NOT the exclusion reason — the Postponed label is).
  - `401857320` — 2026-07-26 "AT&T WNBA All-Star Game" (TEAM COOP vs TEAM SPOON) →
    dropped by the frozen All-Star alias law.
- roster_audit cross-check: `game_rosters_2026.csv` carries **342 unique game_ids** =
  341 universe + exactly the All-Star extra `401857320` (consistent with COVERAGE_AUDIT
  §3 "file-side extras are All-Star games"); `player_box_2026.csv` game_date max =
  2026-10-02 (ET date; the −0400 box suffix is cosmetic per the frozen corpus laws).

## 5. Per-season maxima and future-tip counts (asked by the dispatch)

| season | max universe tip (feature table = raw post, identical) | future-tipped universe games at any anchor |
|---|---|---|
| 2024 | 2024-10-21T00:00:00Z | 0 |
| 2025 | 2025-10-11T00:00:00Z | 0 |
| 2026 | 2026-10-03T01:00:00Z | 0 |

(2026 season structure visible in raw bytes: regular season + postseason all completed by
2026-10-03T01:00Z; the raw file additionally holds 17 `pre` TBD placeholder slots through
2026-11-01 which the universe law excludes.)

## 6. Conclusion

1. The raw bytes **CONFIRM** the controller's pre-measurement on every measured quantity.
   The only future-dated raw 2026 rows are `pre` TBD placeholders that the frozen universe
   law has always excluded — **this is not a freeze contradiction** (the contradiction
   condition was "any future-tipped 2026 GAME"; there are zero).
2. **2026 is COMPLETE at freeze** (last universe tip 2026-10-03T01:00Z < earliest anchor
   2026-10-05T09:26:30Z; 341/341 universe games present; census identical to the frozen
   COVERAGE_AUDIT list "…, 311, 341 — identical to the predecessor's measured list, row by
   row").
3. **OOS = [2020, 2021, 2022, 2023, 2024, 2025, 2026] — exactly as frozen.** Final 7
   complete seasons at freeze; the pin stands; nothing re-pinned, nothing resolved.
4. Runner re-assertion (binding, G4 run-time law in `run_oos.py`): at post-GO run time the
   runner asserts every OOS game has `tip_utc < run time` — a game still in the future at
   run time would mean the corpus was stale (or contaminated post-freeze) and the runner
   REFUSES (exit 5, `FUTURE-TIPPED-GAME-AT-RUN-TIME`); proven by fixture (i).

## 7. Provenance

- Measurement scripts/output (this lane's sandbox):
  `~/.my-quantitative-data/wnba-playerfeat-scored-v1/exec_sandbox/window_measure.py`,
  `window_measurements.json`. Interpreter: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`.
- Real inputs read (read-only): the frozen feature table (tip/season/id columns only),
  raw ESPN schedules 2024/2025/2026 (id/date/status/alias columns only),
  `roster_audit/game_rosters_2026.csv` + `player_box_2026.csv` (id/date columns only),
  COVERAGE_AUDIT.md / FEATURE_SPEC.md / FEATURE_TABLE_MANIFEST.json (lineage law).
- No OOS metric was computed; no outcome value (score/winner) of any 2019+ game entered
  this determination.
