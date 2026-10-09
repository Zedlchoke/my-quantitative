# MONITORING_REPORT_20261009 — NFL-WINPROB-NG-SCORED-V1

**Label: DESCRIPTIVE_MONITORING.** Owner-directed descriptive monitoring round,
2026-10-09 (~10:58Z retrieval; report written ~11:05Z). Scope: recorded
pre-match forecasts of cycle `NFL-WINPROB-NG-SCORED-V1` are scored
descriptively ONLY for games whose FINAL results validly exist in the fresh
nflverse schedules snapshot. No backfill, no parameter/grid work, no new GO.

**Disclosure (explicit):**
- This monitoring consumes **NO scored-cell budget** of any cycle and modifies
  **NO ledger** and no other cycle's paths. The ledger was opened READ-ONLY.
- Calibration vocabulary only: accuracy / log loss / Brier below are
  **descriptors** of recorded forecasts on the FINAL subset. **NO edge,
  betting, or profitability claims** are made or implied. n is tiny (1 game);
  nothing here is evidence of skill or of edge.

---

## 1. Provenance

### Ledger (READ-ONLY)
- Path: `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-scored-v1/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl`
- sha256 verified at monitor time:
  `7d9af2867b480f08c7b195398e15f927fd45172e25899130125a7e8f1a922c90`
  (matches the `7d9af286…` prefix registered for the cycle)
- Lines: 129. Schema `nfl_ng_ledger@1`, all rows `cycle_id=NFL-WINPROB-NG-SCORED-V1`,
  `recorded_by=EXEC-POST-GO-EXECUTOR`, season 2026, `game_type=REG`.
- Integrity (extra read-only check): genesis link OK
  (`prev_row_hash=GENESIS:9978a950cf…` equals genesis file `genesis_digest`);
  all 129 `prev_row_hash → row_hash` chain links OK; all 129 `row_hash`
  recomputations match (JSON, sort_keys=False, separators `(',',':')`).

### nflverse schedules snapshot (the ONLY network fetch; free, keyless)
- URLs:
  - `https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv`
  - `https://github.com/nflverse/nflverse-data/releases/download/schedules/timestamp.json`
- Retrieval UTC: **2026-10-09T10:58:11Z**
- sha256:
  - games.csv: `9c925388e875b6e90c4ba21e7029e0a0ff44648d4528dcab080d1c11dbe560e1`
  - timestamp.json: `0081235036d5199df02b4c11ef12515875f63d6e23fe090cd6038236abee47a2`
- timestamp.json content: `{"last_updated":"2026-10-09 06:46:37 EDT"}`
  (= 2026-10-09 10:46:37Z, ~12 min before retrieval — fresh)
- Same free URLs the NG runbook uses (release tag `schedules`). No other
  network use; no keys.

### Heavy lock
- `researchctl.py locks inspect` verdict: **FREE_PROVEN** (no registry row,
  lock file not flocked). Lock NOT taken by this monitor; no worker touched.
  Last worker released 2026-10-09T10:11:08Z (WSL cycle, unrelated).

---

## 2. Ledger structure + 129-row census

Per-game recorded fields: `game_id, season, game_type, home_team, away_team,
kickoff_utc, recorded_at_utc, arm_id, arm_config_digest, model_version,
inputs_digest, p_home, recorded_by, prev_row_hash, row_hash`.

- 129 rows = **43 unique games × 3 arms (B0, B1_STAR, C3)** — complete design,
  every game has all three arms.
- Kickoff range: 2026-10-09T00:15:00Z → 2026-10-27T00:15:00Z.
- p_home ranges per arm (descriptive of the recorded forecasts):
  - **B0**: constant 0.571399 for all 43 games (constant-probability baseline arm).
  - **B1_STAR**: 43 distinct values, 0.319781 … 0.669418.
  - **C3**: 43 distinct values, 0.216504 … 0.751936.

Rows per arm per week (weeks from `game_id` field `2026_WW_…`):

| Arm | W05 | W06 | W07 | Total |
|---|---|---|---|---|
| B0 | 15 | 14 | 14 | 43 |
| B1_STAR | 15 | 14 | 14 | 43 |
| C3 | 15 | 14 | 14 | 43 |
| **Games** | **15** | **14** | **14** | **43** |

---

## 3. Status classification — STRICT rule

nflverse `games.csv` has no dedicated status column. Semantics inspected on
this exact snapshot: completed rows carry non-empty integer `away_score` and
`home_score` plus derived `result` / `total` / `overtime`; unplayed rows have
empty strings in ALL of these fields.

**FINAL rule applied:** a game is FINAL only if the snapshot row carries
non-empty integer scores for BOTH teams AND derived `result`/`total` are
populated. Any partial/mixed state would be `NOT_RUN_STATUS_AMBIGUOUS`
(none occurred). Ties would be `NOT_RUN_STATUS_AMBIGUOUS` for the binary
home-outcome descriptor (none occurred).

Result over the 43 recorded games:

| Status | Count |
|---|---|
| **FINAL** | **1** |
| PENDING_NOT_FINAL | 42 |
| NOT_RUN_JOIN_FAILURE (snapshot row missing) | 0 |
| NOT_RUN_STATUS_AMBIGUOUS | 0 |

Anomalies: **none.** All 43 recorded game_ids present in the snapshot;
ledger home/away identity matches snapshot for the FINAL game (checked);
kickoff consistency holds (ledger 2026-10-09T00:15:00Z = snapshot gameday
2026-10-08 20:15 local ET).

As expected at this hour: only the week-5 Thursday opener is FINAL; all
Sunday/Monday week-5 games and all week-6/7 games are pending. NO backfill of
anything not FINAL.

---

## 4. FINAL game table (n=1)

| game_id | kickoff_utc (ledger) | matchup (home vs away) | away_score | home_score | outcome_home_win | p_home B0 | p_home B1_STAR | p_home C3 |
|---|---|---|---|---|---|---|---|---|
| 2026_05_TB_DAL | 2026-10-09T00:15:00Z | DAL vs TB | 24 | 16 | 0 (away win) | 0.571399 | 0.544343 | 0.529183 |

---

## 5. Per-arm descriptive metrics on the FINAL set (n=1)

Definitions (descriptors): log loss = −[y·ln p + (1−y)·ln(1−p)] averaged over
FINAL games; Brier = (p − y)² averaged; argmax accuracy = fraction where
( p_home > 0.5 ) equals (home win).

| Arm | n | log loss (mean / sum) | Brier (mean / sum) | argmax accuracy |
|---|---|---|---|---|
| B0 | 1 | 0.847229 / 0.847229 | 0.326497 / 0.326497 | 0.0 |
| B1_STAR | 1 | 0.786015 / 0.786015 | 0.296309 / 0.296309 | 0.0 |
| C3 | 1 | 0.753286 / 0.753286 | 0.280035 / 0.280035 | 0.0 |

Reading, in calibration vocabulary ONLY: on the single FINAL game the away
team won while all three arms assigned p_home > 0.5, so all three miss the
argmax call on this game; arms assigning lower p_home on DAL incur smaller
log loss / Brier on this single observation. **n = 1: these numbers are
single-game descriptors with zero inferential weight. They support no
comparison conclusion, no ranking, and no edge claim of any kind.**

## 6. Pending inventory

42 recorded games remain PENDING_NOT_FINAL (15th+14th week-5 games Sat/Sun/Mon
+ all week-6 and week-7 games). They are listed with status in the joined CSV;
they receive NO scores in this round. A future owner-directed monitoring round
may score them once their results validly exist as FINAL.

---

## 7. Artifacts

Staging (untracked in root checkout; controller reviews/commits — this agent
made NO git commit):
- `/Users/hoangminhlong/my-quantitative/research/control/NFL-NG-MONITOR-20261009/MONITORING_REPORT_20261009.md` (this file)
- `/Users/hoangminhlong/my-quantitative/research/control/NFL-NG-MONITOR-20261009/joined_monitor_20261009.csv`
- `/Users/hoangminhlong/my-quantitative/research/control/NFL-NG-MONITOR-20261009/monitor_analysis.py` (reproduction script; run with `.venv/bin/python`)

Monitor data dir (agent-owned):
- `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/games.csv` (snapshot copy, sha256 above)
- `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/timestamp.json`
- `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/joined_monitor_20261009.csv` (joined extract)
- `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/provenance_monitor_20261009.json`
- `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/monitor_results_20261009.json`
- `/Users/hoangminhlong/.my-quantitative-data/nfl-ng-monitor-20261009/monitor_analysis.py`

Gates: monitoring join/metrics executed and reproduced via
`monitor_analysis.py` → PASS (evidence: JSON outputs above). No cycle gate,
no scoring, no GO is touched or claimed by this round.
