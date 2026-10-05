# PIPELINE_REPORT — Lane PIPE, cycle NFL-WINPROB-NG-SCORED-V1

Real prediction-record pipeline + freeze erratum R2. Wave B per
`lanes/DISPATCH/DISPATCH_PIPE.md` (dispatch sha = actual start sha =
`ecf8371abf7839ca49e9245c99f8aa7386d48fdd`). Interpreter for every command:
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`. No git commands; nothing
committed (uncommitted-by-design). ABSOLUTE law held: **no p_home was computed or
emitted for any REAL game** — the only probabilities in any artifact of this lane are
for `SYNTH_`-prefixed synthetic fixtures (2027+ kickoffs); the real-data mode
(`warmup-check`) emits aggregate counts only and never calls the predict stage
(enforced in code by `_assert_synth_only`, which hard-stops any non-`SYNTH_` game id
reaching the prediction path). No real ledger was created; no evaluation of any
2019+ outcome; no betting vocabulary.

## 1. What was built

### 1.1 Task 1 — pbp 2018–2020 state-carry inputs (DONE, 3/3)

- `play_by_play_{2018,2019,2020}.parquet` downloaded from the public nflverse `pbp`
  release into `~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2018_2020/`; HTTP 200
  ×3; PAR1 magic verified ×3; provenance manifest (`DOWNLOAD_MANIFEST.{md,json}`,
  schema `nfl_ng_scored_v1_pbp_2018_2020_manifest@1`) extends the A_DATA format
  (url/http/downloaded_utc/bytes/sha256 + API-metadata cross-checks).
- 2019/2020 sha256s **byte-match the cached GitHub API asset digests** from A_DATA's
  provenance copy; 2018 matches the API size exactly (asset untouched since 2025-04-30).
  **GitHub API calls used: 0 of 1** (metadata read from the cached copy).
- License re-fetched **once** (11:57Z), HTTP 200, 18,651 bytes, sha256
  `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111` = pin ⇒
  **no BLOCKED_DATA_RIGHTS** (stop condition not triggered). Copy under
  `provenance/nflverse-data_LICENSE_refetch_PIPE_20261005.md`; the pinned rights file
  itself was not overwritten.
- Disclosed drift: the release's `timestamp.json` moved after lane A's fetch (in-season
  2026 re-cut; content now `2026-10-05 05:03:27 EDT`). Provenance metadata only — the
  three completed-season assets 2018–2020 were not touched.
- pbp 2021–2025 (predecessor archive, read-only, untouched): sha256s measured and pinned
  in `lanes/FREEZE_ERRATUM_R2/freeze_digests_r2.json`. pbp 2000–2017 re-verified
  **18/18 MATCH** against the A_DATA binding manifest.

### 1.2 Task 2 — recorder (`research/control/NFL-WINPROB-NG-SCORED-V1/recorder/`)

| module | role |
|---|---|
| `frozen_refs.py` | read-only references: sha-pinned imports of the FROZEN `lanes/T_SELECT/arms.py` (replay machinery, kickoff canonicalization, lineage map, `z_standardize`, `GameSet`, `batches`, `replay_elo`) and the ported `nfl_ng_ledger@1` tool (both sha256-asserted at every load); freeze constants; canonical arm-config strings §1.1 + `verify_arm_config_digests()` (arm-param equality law) |
| `schedule.py` | (a) schedule load: versioned games.csv snapshot, sha256 pinned BEFORE parsing (mismatch = `SchedulePinError`); quarantine drop (frozen `arms.quarantine_report`); 1999 dropped (not kickoff-capable); PRE dropped; kickoff-UTC via frozen `arms.kickoff_utc`; completed-games law split (warmup = both scores present AND kickoff strictly < batch ts); `future_score_violations()` (future-with-score detector); `fetch_latest_schedule_snapshot()` — fresh-pull implemented, **never executed** by any mode (refuses non-empty destinations; public URL only) |
| `priors.py` | C3 boundary priors: per-season E aggregation **mirroring `arms.build_z_table` lines 383–403** (documented copy of the formula; direct reuse impractical because the frozen function hard-caps at `SEASON_MAX_PBP=2017` and a single directory) with standardization delegated to the **frozen `arms.z_standardize`** (imported, not copied); real path reads pbp 2000–2025 (5 columns) with per-file pin verification (2018–2025 vs PIPE pins; 2000–2017 vs A_DATA manifest); synthetic prior-E-table path for e2e fixtures; asserts each file's `season` values == filename year |
| `pipeline.py` | (b) `warmup_aggregates()` — state-carry replay (B1* no-prior; C3 θ=50 with z) returning COUNTS ONLY (games/season, lineages initialized, prior applications per boundary via first-prediction analysis, reversions without prior, first-season initializations); (c) `predict_target_week()` — one combined replay per arm over warmup+target rows (warmup kickoffs < batch ts ≤ target kickoffs ⇒ target records are a function of the warmed state only); identical-kickoff exclusion is the frozen `arms.batches` law; p-format guard (6-dp strict (0,1), boundary rounding = design bug ⇒ STOP); (d) `check_margin()` — `batch_write_time + 6h <= first kickoff`, exact boundary passes, failure = `MarginRefusal` BEFORE any write; (e) `append_batch_to_ledger()` — through the PORTED tool to the TARGET PATH argument, deterministic row order (arms B0/B1_STAR/C3 × games by kickoff,game_id), re-asserts margin defensively |
| `record_batch.py` | CLI: `--mode {selftest, warmup-check, e2e-synth}` (+ `--schedule`, `--schedule-sha`); sandbox identity (`NFL-WINPROB-NG-SCORED-V1-PIPETEST` / season 2030, distinct from the real cycle AND from S_SYNTH's sandbox genesis); real-ledger-path absence assertions; freeze-GENESIS-absence-from-sandbox-bytes assertion |

Laws encoded (grep-auditable): future-game-with-score ⇒ `FutureScoreAbort` (hard, before
any compute); no LL/metric anywhere in the warmup (no logarithm is ever computed on game
data; warmup outputs are counts); arm params are read-only constants re-verified against
the freeze digests at every run; recorder = single writer via the ported tool only;
real ledger path only after owner GO (not this lane).

### 1.3 Task 3 — FREEZE_ERRATUM_R2 (drafted; controller integrates)

`lanes/FREEZE_ERRATUM_R2/{ERRATUM_R2.md, freeze_digests_r2.json}`:
1. **ATL@NO per Option B** — capturable weeks = week 5 from the 2026-10-09T00:15Z opener
   ONLY; `2026_04_ATL_NO` and all pre-week-5 games `NOT_RUN` prospective forever
   (forfeit-by-design); ≥6h margin applies within the window; registered window NOT
   changed — the erratum enforces it and supersedes the defective §4 sentence.
2. **STATE-CARRY LAW** — selection caps 2018/2017 permanent for selection (selection
   closed; SPENT 2019–2025 cite-only); recorder consumes completed-game outcomes through
   the batch timestamp for rating/prior updates ONLY (as-of admissible information set,
   NOT evaluation); no metric on any SPENT-window game; arm params immutable; pbp
   2018–2020 = pinned state-carry inputs (plus 2021–2025 archive pins).
3. **RECORDER FREEZE** — five module sha256s; `RECORDER_FREEZE_SHA` =
   `PENDING_CONTROLLER_ADDENDUM` (controller two-step addendum, same precedent as
   CODE_FREEZE_ADDENDUM); pbp 2018–2020 provenance.
4. **GENESIS_PAYLOAD_DIGEST_R2 = `bd94eb77d35077ac7bc1761a2c61031a1cdf2f53c6d8be181de5ddfcefd51483`**
   over the canonical payload V2 (§6 fields + `recorder_freeze_sha`;
   `code_freeze_sha=7ec4c539394e68538f74df327d85fa2a477c6eb7` real;
   `created_at=POST_GO_TIMESTAMP` and `recorder_freeze_sha=PENDING_CONTROLLER_ADDENDUM`
   placeholders with the unchanged substitution law). `ae99a803…` is superseded with
   reason (R1 pinned the addendum placeholder; both substitutions are byte-level payload
   changes). R1 recomputed = `ae99a803…` exactly before R2 was pinned (canonicalization
   verified). Freeze packet bytes unchanged (`9978a950…`).

### 1.4 Task 4 — suites re-run on the current tree (after all additions)

| suite | result |
|---|---|
| `research/control/.../ledger/test_ledger_synthetic.py` (predecessor, byte-identical port) | **42/42 PASS** (0.42s) |
| `lanes/S_SYNTH/test_successor_synthetic.py` (successor) | **16/16 PASS** (1.06s) |
| `lanes/PIPE/test_recorder_synthetic.py` (NEW — this lane's additions) | **3/3 PASS** (selftest, e2e-synth, frozen-bytes) |

Existing suites untouched and unweakened; the additions only stack on top.

## 2. Test matrix (all green)

| # | check | vehicle | result |
|---|---|---|---|
| 1 | arm-config digest equality (recomputed §1.1 == freeze pins) | selftest | PASS |
| 2 | margin arithmetic: exactly 6h accepted; 5h59m59s / 0h / post-kickoff refused, nothing written | selftest (hand) | PASS |
| 3 | kickoff-UTC canonicalization: EDT London 13:30→17:30Z; TB_DAL 20:15→00:15Z(+1d); fall-back day 13:00→18:00Z (EST); winter 13:00→18:00Z; summer 12:00→16:00Z | selftest (hand, frozen `kickoff_utc`) | PASS |
| 4 | state-carry hand Elo: 1500→+20/−20 (win/loss, e=0.5, K=40); tie S=0.5 → no movement; g3 pre-game ratings 1520/1500, e=sig(0.05); target prediction == hand formula incl. γ=2/3 season reversion (B1*) and independent hand-computed C3 θ·z term; C3 ≠ B1* (prior moves p) | selftest (hand) | PASS |
| 5 | warmup aggregate counts on hand stream: 3 games/1 season, 4 lineages, prior counting {"2029": 4} on the extended stream, reversions-without-prior = 0 | selftest | PASS |
| 6 | identical-kickoff exclusion: label-flip canary, absence canary, solo-vs-batch equality (C3 stream) | selftest | PASS |
| 7 | future-score abort: doctored future row detected (`SYNTH_ST_BAD`); e2e scenario 3 aborts with nothing written | selftest + e2e | PASS |
| 8 | fresh-pull guard: refuses non-empty dest; public URL constant; never executed in any mode | selftest | PASS |
| 9 | p-format guard: 6-dp strict (0,1); 0.0/1.0/negative/>1 rejected; 0.9999994 formats fine | selftest | PASS |
| 10 | combined-vs-warmup replay equivalence: C3 prefix records bit-identical | selftest | PASS |
| 11 | frozen bytes: arms.py / ledger tool sha256 pins | selftest + pytest | PASS |
| 12 | e2e nominal week: 192 warmup games (2 completed synthetic seasons), 8 target games, C3 priors exercise (32 z per target season), 24 rows = 8×3 arms, chain intact vs sandbox genesis, scoring rehearsal 24×VALID_PROSPECTIVE, quarantine bait columns dropped (4 named), SYNTH_-only ids, freeze GENESIS absent from all sandbox bytes, real-ledger paths absent | e2e-synth | PASS |
| 13 | margin-violation refusal: batch 5.98h before first kickoff ⇒ `MarginRefusal`, zero files written | e2e-synth scenario 2 | PASS |
| 14 | future-score abort: doctored snapshot row ⇒ `FutureScoreAbort`, zero files written | e2e-synth scenario 3 | PASS |
| 15 | determinism: full pipeline twice ⇒ ledger + genesis sidecar **byte-identical** (ledger sha256 `cf92d600e7bf337f00bd593a7c45d9f6cfa09161244e6ff8f9848713a45a308a`) | e2e-synth double run | PASS |
| 16 | REAL warmup legality + counts on the frozen snapshot (§3 below) | warmup-check | PASS |

## 3. Warmup-check on REAL bytes (aggregate counts ONLY — zero probabilities)

Run 2026-10-05T12:21:39Z, batch_time = run time, snapshot =
`~/.my-quantitative-data/nfl-ng-scored-v1/raw_schedules_fresh/games.csv` sha
`486d7227…` (pin verified before parse). Evidence:
`lanes/PIPE/warmup_check_evidence.json`.

| aggregate | value |
|---|---|
| snapshot rows / dropped pre-2000 / dropped PRE | 7,548 / 259 (1999) / 0 |
| quarantined columns at load | 9 (the audited set: away/home_moneyline, away/home_spread_odds, over/under_odds, spread_line, total, total_line) |
| future games carrying scores (legality) | **0** (law holds) |
| completed games absorbed (warmup) | **7,080** — per season 2000–2018: 259/259/267×17 (== lane A); 2019: 267; 2020: 269; 2021–2025: 285 each (REG+POST); **2026: 63 — exactly the registration audit's count** |
| in-progress excluded (kickoff < batch, no score) | 0 |
| future unplayed | **209** (== audit) |
| ratings-initialized lineages | **32** (SD/STL/OAK folded to LAC/LA/LV; codes enumerated in evidence) |
| C3 z-table | **830 entries**, targets 2001–2026 (31/31 for 2001/2002 — pre-HOU-expansion prior seasons; 32 thereafter) |
| C3 prior applications per boundary | **1:1 with the z-table** — every (season, lineage) with a z got exactly one prior application at its first prediction of that season; reversions-without-prior = 0 |
| state-carry pins verified | 26/26 pbp files (2000–2017 vs A_DATA manifest; 2018–2025 vs PIPE pins) |
| probabilities emitted | **0** (predict stage never called; evidence contains counts/strings only) |

Lock discipline: heavy-stage lock registry inspected (read-only) — `FREE_PROVEN`, no
foreign worker observed or touched at any point; at real record time the controller takes
the global lock before the warmup batch.

## 4. E2E synthetic results

Evidence: `lanes/PIPE/e2e_synth_evidence.json`; sandbox under
`~/.my-quantitative-data/nfl-ng-scored-v1/recorder_sandbox/e2e/` (lane-owned).
Fixtures: real games.csv-format schedule (`SYNTH_2028_R*_G*`, `SYNTH_2029_*`,
`SYNTH_2030_W3_G01..08`), 32 synthetic lineages `SYT01..SYT32`, seasons 2028/2029
completed (96+96 games, same-kickoff pairs, ties/neutral mixed), target week 2030 W3
(8 games in 4 same-kickoff batches), kickoffs derived by the frozen `kickoff_utc`
(DST-crossing slots); synthetic prior-E table → frozen `z_standardize` (32 z per target
season 2029/2030 — C3 priors exercise). Quarantine-bait odds columns in the fixture are
dropped at load (4 named). Sandbox ledger:
`predictions_NFL-WINPROB-NG-SCORED-V1-PIPETEST_2030.jsonl`, 24 rows, chain intact,
scoring-gate rehearsal 24×`VALID_PROSPECTIVE`, margin 173.0h; first-game p_home per arm
(synthetic games only): B0 `0.571399` (frozen constant), B1_STAR `0.495895`, C3
`0.353916` (prior term moves the prediction). Determinism: double-run ledger and genesis
sidecar byte-identical. Scenarios 2 (margin 5.98h ⇒ refusal) and 3 (future score ⇒
abort) left zero files.

## 5. Known limitations / disclosures

- `fetch_latest_schedule_snapshot()` is implemented but **never executed** (dispatch
  law); at real record time its sha256 + pull time enter `inputs_digest`.
- The E-aggregation loop in `priors.py` mirrors frozen `arms.build_z_table` lines
  383–403 (documented in-module): unavoidable because the frozen function is hard-capped
  at the selection pbp ceiling; standardization itself is the imported frozen function.
- Cross-process determinism relies on p_home 6-dp formatting (e_home depends only on
  kickoff-ordered rating arithmetic, not on `set`-iteration-ordered SOS bookkeeping);
  verified byte-identical over two separate process runs.
- The 2026 season counts in the snapshot will evolve (new kickoffs/scores); warmup-check
  is a smoke check at its run instant, not a registration re-audit (the epoch and the
  63-game NOT_RUN count remain frozen by the packet/audit).
- Erratum file sha256 is pinned inside `freeze_digests_r2.json`; the r2 json's own sha256
  is left for the controller to pin at integration (a file cannot contain its own digest).

## 6. Deliverables index

- `lanes/PIPE/PIPELINE_REPORT.md` (this file), `VERDICT_TABLE.md`,
  `test_recorder_synthetic.py`, `warmup_check_evidence.json`, `e2e_synth_evidence.json`
- `research/control/NFL-WINPROB-NG-SCORED-V1/recorder/{frozen_refs,schedule,priors,pipeline,record_batch}.py`
- `lanes/FREEZE_ERRATUM_R2/{ERRATUM_R2.md, freeze_digests_r2.json}`
- `~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2018_2020/**` (3 parquets +
  timestamp.json + ATTRIBUTION.md + DOWNLOAD_MANIFEST.{md,json})
- `~/.my-quantitative-data/nfl-ng-scored-v1/provenance/nflverse-data_LICENSE_refetch_PIPE_20261005.md`
- `~/.my-quantitative-data/nfl-ng-scored-v1/recorder_sandbox/**` (synthetic e2e only)
- `lanes/DISPATCH/handoff_PIPE.json`
