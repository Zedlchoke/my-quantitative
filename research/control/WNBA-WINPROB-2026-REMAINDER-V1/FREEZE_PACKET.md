# FREEZE PACKET — WNBA-WINPROB-2026-REMAINDER-V1 (Lane W26)

PROSPECTIVE PREP ARTIFACT · NO GO TYPED · ZERO REAL FORECASTS COMPUTED
(Typed GO is the owner's alone; nothing here constitutes, predicts, or
consumes a real-game probability.)

- Freeze instant: **2026-10-07** (this lane's work; dispatch anchor
  77b531072715cb8343d261cb410292fe6ea770aa = measured worktree HEAD at lane
  start). Everything below is bound at THIS packet's sha256 (the genesis
  digest input for the ledger, computed at ledger-creation time post-GO; the
  ledger tool consumes the freeze-packet bytes; nothing pre-GO creates it).
- Bound tree: branch `orca/wnba-2026-remainder-v1-integration`, worktree
  `.worktrees/wnba-2026-remainder-v1/integration`.

## 1. Arms (verbatim, never re-tuned — inherited unchanged from the PREP freeze)

| arm | binding | verification at THIS freeze |
|---|---|---|
| **B1-WNBA** (mandatory arm) | own-Elo **K=32 / HCA=50 / γ=0.65**, binary updates, tip-batch snapshot law, neutral ⇒ HCA=0 | engine re-hashed **2026-10-07**: `arms.py` `82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3`, `harness.py` `b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e` (== ERRATUM_R1 pins; read-only source `.worktrees/wnba-playerfeat-scored-v1/integration/lanes/T_SELECT/`) |
| **B0** (reference floor) | constant **p = 0.603755** | asserted literal (closed cycle's train-internal floor; OOS evidence inherited, NEVER re-run) |
| slots 3–9 | **RELEASED pre-look, never reallocated** | PREP FREEZE_PACKET §1/§8; any new mechanism needs a fresh packet + owner instruction and must beat B1-WNBA, never merely B0 |

Diagnostic annex R (PREP cycle) found NO supported mechanism; the frozen
B1-WNBA verbatim remains the only standing arm. Nothing reallocated here.

## 2. Seed (pinned once)

- Evaluation bootstrap seed: **`20261006`** (pinned at the PREP freeze,
  2026-10-06; carried UNCHANGED — never changed after first real row, never
  re-pinned here). Engine determinism seed inside the frozen code: `20261005`
  (arms.py `SEED`, frozen byte-level, untouched).

## 3. Ledger law (adaptation of the 2027-frozen tool)

- Schema: **`wnba_2026_remainder_ledger@1`** — port of the 2027-frozen
  `wnba_prospective_ledger@1` (source: PREP lane L_LEDGER at PREP tree HEAD
  `9ed717c43c2e0724a51095730b28df8c7d5881ae`, module introduced at
  `0d9b3d575106405c5ed5335d02b4c1ec2f132192`); 18 closed fields
  (`tip_utc` + `local_date`); GENESIS sha-chain; append-only flock+fsync;
  tamper-evident notices; full re-hash verify walk; scoring-time
  classification.
- **Window law**: only remaining 2026 playoff games — `season == 2026`
  (exact) AND `game_type == "POST"` structurally enforced at creation,
  append and verify. Completed 2026 playoff games are HISTORY (stream
  warm-up material, never scored rows). The REAL ledger file
  (`predictions_<cycle_id>_2026.jsonl`) is created ONLY after the owner
  typed this cycle's GO; none exists today (test-enforced).
- **Batch law (tip-relative day-anchored T0−6h10m)**: one day-batch per
  Eastern calendar day; `T0` = earliest `tip_utc` of the ET game-day per the
  **pinned schedule snapshot** (`wnba_schedule_2026.csv` sha
  `0ed97faf…`, DATA_REFRESH_MANIFEST.md); every row must satisfy
  `recorded_at_utc < T0 − 6h10m` **STRICTLY** — the anchor is an EXCLUSIVE
  deadline (a row stamped exactly at T0−6h10m is refused; disclosed
  tightening of the frozen 2027 law, which was inclusive at exactly 6h) —
  AND the per-row strict law `recorded_at_utc < tip_utc` at append AND at
  scoring. One batch per ET day: no re-prediction, no backfill, ever.
  Tool note (disclosed): the tool gates on the min tip of the rows actually
  in the batch — a first-and-only partial batch of only later-tipped games
  gates at its own earliest game anchor and permanently consumes the ET day
  (proven in DRYRUN_REPORT D6).
- **Stream state law** (scoring-side; frozen engine semantics): the rating
  state used for a batch includes ONLY games with `tip_utc < batch anchor`
  AND result present (completed only); games sharing an exact tip are all
  predicted from one rating snapshot; updates apply only after a day's tips
  pass (DRYRUN_REPORT D3/D5).
- **Row vocabulary (O-2 classes)**: `VALID_PROSPECTIVE`
  (aggregate-eligible only), `INVALID_PROSPECTIVE` (retro-injection / tip
  moved earlier past record — permanent), `NOT_SCORED_CANCELLED`,
  `NOT_RUN` (incl. played-before-record write-off),
  `NOT_SCORED_NO_ACTUAL_DATA`; game-level `not_run_games` census. Missing
  evidence is NOT_RUN — never inferred PASS.
- **No-parameter-change-after-first-real-row law**: after the first real
  row, NO parameter of any arm changes — any drift is a documented anomaly,
  never a re-fit (interim calibration monitoring allowed: Brier, 10-bin
  reliability, slope band [0.85, 1.15], coverage counts,
  played-before-record census).

## 4. Evaluation law (verbatim inheritance)

- Pooled + per-season-segment ΔLL vs B0; this cycle's window is a single
  segment (2026 remainder); paired **tip-date-cluster bootstrap, 10,000
  resamples, seed `20261006`**. REJECT-vs-B0 iff the pooled 95% CI of ΔLL
  includes 0 OR >= half of segments non-negative (1 segment ⇒ threshold 1).
  **MIN_VALID = 300** VALID_PROSPECTIVE rows; below it the verdict caps at
  INCONCLUSIVE_COVERAGE (with ≤15 remaining games this window can never
  reach MIN_VALID alone — stated, not stretched).

## 5. Census — REMAINING 2026 playoff slate (from the pinned schedule snapshot)

Source: `~/.my-quantitative-data/wnba-2026-remainder-v1/refresh_20261007/
wnba_schedule_2026.csv` (sha `0ed97faf…`; 15 `pre` rows; tip_utc canonicalized
per SPEC §3: `pd.to_datetime(espn.date, utc=True, format="ISO8601")`;
`local_date := tip_utc.tz_convert("America/New_York").date`).
**Per-game anchor = tip_utc − 6h10m** (exclusive deadline). Day-batch gate =
T0(day) − 6h10m where T0(day) = earliest tip of the ET game-day.

| # | game_id | tip_utc | ET local_date | matchup | per-game anchor (tip−6h10m) |
|---|---|---|---|---|---|
| 1 | 401918297 | 2026-10-07T23:30:00Z | 2026-10-07 | NY @ ATL (SF Game 2) | **2026-10-07T17:20:00Z** |
| 2 | 401918298 | 2026-10-08T01:30:00Z | 2026-10-07 | LV @ GS (SF Game 2) | **2026-10-07T19:20:00Z** |
| 3 | 401918299 | 2026-10-09T23:30:00Z | 2026-10-09 | ATL @ NY (SF Game 3) | 2026-10-09T17:20:00Z |
| 4 | 401918300 | 2026-10-10T01:30:00Z | 2026-10-09 | GS @ LV (SF Game 3) | 2026-10-09T19:20:00Z |
| 5 | 401918302 | 2026-10-11T04:00:00Z | 2026-10-11 | GS @ LV (SF Game 4 if nec.) | 2026-10-10T21:50:00Z |
| 6 | 401918301 | 2026-10-11T18:00:00Z | 2026-10-11 | ATL @ NY (SF Game 4 if nec.) | 2026-10-11T11:50:00Z |
| 7 | 401918303 | 2026-10-14T04:00:00Z | 2026-10-14 | NY @ ATL (SF Game 5 if nec.) | 2026-10-13T21:50:00Z |
| 8 | 401918304 | 2026-10-14T04:00:00Z | 2026-10-14 | LV @ GS (SF Game 5 if nec.) | 2026-10-13T21:50:00Z |
| 9 | 401918305 | 2026-10-17T19:30:00Z | 2026-10-17 | TBD @ TBD (Finals Game 1) | 2026-10-17T13:20:00Z |
| 10 | 401918306 | 2026-10-20T00:00:00Z | 2026-10-19 | TBD @ TBD (Finals Game 2) | 2026-10-19T17:50:00Z |
| 11 | 401918307 | 2026-10-23T00:00:00Z | 2026-10-22 | TBD @ TBD (Finals Game 3) | 2026-10-22T17:50:00Z |
| 12 | 401918308 | 2026-10-24T19:30:00Z | 2026-10-24 | TBD @ TBD (Finals Game 4) | 2026-10-24T13:20:00Z |
| 13 | 401918309 | 2026-10-27T00:00:00Z | 2026-10-26 | TBD @ TBD (Finals Game 5 if nec.) | 2026-10-26T17:50:00Z |
| 14 | 401918310 | 2026-10-30T00:00:00Z | 2026-10-29 | TBD @ TBD (Finals Game 6 if nec.) | 2026-10-29T17:50:00Z |
| 15 | 401918311 | 2026-11-01T00:00:00Z | 2026-10-31 | TBD @ TBD (Finals Game 7 if nec.) | 2026-10-31T17:50:00Z |

**15 games, 11 ET game-dates.** The two dispatch-pinned anchors reproduce
exactly: 401918297 → 2026-10-07T17:20:00Z; 401918298 → 2026-10-07T19:20:00Z.
(Reconciliation note: both game 1 and game 2 share ET local_date 2026-10-07,
so a full-slate day batch for that day gates at the day's T0−6h10m =
17:20:00Z; the 19:20:00Z value is game 401918298's own per-game anchor —
operative when it is recorded alone or with only later-tipped games; see
DRYRUN_REPORT D6 + feasibility section.)

ET-day batch gates (full-slate batches, exclusive):
ET 10-07 → 2026-10-07T17:20:00Z · ET 10-09 → 2026-10-09T17:20:00Z ·
ET 10-11 → 2026-10-10T21:50:00Z · ET 10-14 → 2026-10-13T21:50:00Z ·
ET 10-17 → 13:20:00Z · ET 10-19 → 2026-10-19T17:50:00Z · ET 10-22 →
2026-10-22T17:50:00Z · ET 10-24 → 13:20:00Z · ET 10-26 →
2026-10-26T17:50:00Z · ET 10-29 → 2026-10-29T17:50:00Z · ET 10-31 →
2026-10-31T17:50:00Z (all UTC).

## 6. Window / played-before-record laws (carried)

- 2002–2026 are stream/spent windows (citable, never re-scored); this
  cycle's PROSPECTIVE window is exactly the 15 remaining 2026 playoff games
  above; the 2027 season is the PREP cycle's own prospective window (not
  touched here).
- **Played-before-record census law**: any remaining game whose per-game
  anchor passes without a pre-tip row (or with `recorded_at >= tip`) is
  never re-recorded; the count is disclosed at each evaluation, never
  repaired. **Missed anchors are NOT_RUN forever (no backfill).**
- tip-UTC canonicalization (SPEC §3 verbatim, see §5).

## 7. Budget + rights bindings

- Budget stays **0/0**; no purchases, no accounts, no S1. GO typing is the
  owner's alone (`GO WNBA WINPROB 2026 REMAINDER V1 PREDICTIONS` — expected
  verbatim shape; registered-not-consumed by any agent).
- Rights: SportsDataverse (wehoop) release store, data CC BY 4.0 + MIT code;
  ATTRIBUTION re-verified `1068e5c7…` == pin (DATA_REFRESH_MANIFEST.md §
  Rights re-verification); feature table + crosswalk re-hashed == pins.

## 8. Negative-first terminal outcomes (carried)

PRELAUNCH_READY_PENDING_OWNER_GO | GATE_FAIL_<GATE> | BLOCKED_DATA_RIGHTS |
BLOCKED_TOOLING | NOT_RUN_RESOURCE_CONFLICT | TECHABORT_*.
