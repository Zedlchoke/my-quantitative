# FREEZE PACKET — NFL-WINPROB-NG-SCORED-V1

- Lane: `F_FREEZE` · Cycle: `NFL-WINPROB-NG-SCORED-V1` · Written: 2026-10-05
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/nfl-winprob-ng-scored-v1/integration`
  · Branch: `orca/nfl-winprob-ng-scored-v1-integration`
- Authority chain: predecessor cycle `NFL-WINPROB-NG-PREP-V1` (FREEZE_PACKET_DRAFT §7 open items +
  OWNER_DECISION_PACKET, both cited in §12 with sha256s) → this cycle's dispatch packet
  `lanes/DISPATCH/DISPATCH_F_FREEZE.md` (declared DISPATCH SHA
  `69798a8389f9992d7f59adc170890013423610e8`; the file's on-disk sha256 is
  `cf21f3f923aabba1e535ea8df1faa0b003d38601bef691fb55034af7c9d7d8df` — different namespaces:
  integration-HEAD sha at dispatch vs file sha256) → this packet.
- Scope: assembly of landed, committed evidence ONLY. No new computation beyond sha256 digest
  arithmetic. No metrics. No ledger writes. No git commands. No GO typed or consumed here.
- Machine-readable twin: `lanes/F_FREEZE/freeze_digests.json` (every sha256 cited below; the
  packet's own digest and the GENESIS pin live there — see §6).
- Language law: calibration/forecasting vocabulary only. No betting vocabulary anywhere.

## 1. Final arm enumeration (binding, ≤9 slots; released slots never reallocated)

| slot | arm | status | basis (cited) |
|---|---|---|---|
| 1 | **B0** — constant `p_home = 0.571399049390` | **FIELDED** (mandatory anchor) | TRAIN 2000–2018 REG non-tie home-win rate = 2765/4839; re-verified by this lane from SELECTION_REPORT.md §3 (arithmetic re-check: 2765/4839 = 0.5713990493903699 → frozen 12-dp 0.571399049390); B0 is selection-exempt (intercept-only refit is its entire spec, PROTOCOL §2.1) |
| 2 | **B1\*** — own-Elo K=40, HCA=0, γ=2/3, μ=1500 | **FIELDED** (mandatory baseline) | Frozen from terminal cycle `NFL-WINPROB-SCORED-V1`, never re-fit (BASELINE LAW, PROTOCOL §0.10); selection-exempt (PROTOCOL §2.1); measured TRAIN pooled inner LL 0.652497, slope 1.6051 (SELECTION_REPORT §3/§5) |
| 3 | C1 SOS-adjusted Elo | **RELEASED (KILL)** | G-ENTRY failure: selected config `C1_B025` (β=25.0) has pooled inner ΔLL vs B1* = +0.000141 (point ≥ 0) and calibration slope 1.6260 outside [0.85, 1.15] (SELECTION_REPORT §7; SELECTION_LEDGER.jsonl arm_verdict row C1). Time-shuffled-SOS twin did not win (ΔLL +0.000029 [−0.000119, +0.000173]) — kill is on the gate, not the control |
| 4 | C2 home/away split rating | **RELEASED (KILL + MACHINERY_SUSPECT)** | G-ENTRY failure (slope 1.2533 of selected `C2_L075_D1O2_H025` outside band) AND its venue_label_permutation control WON (ΔLL −0.006873, CI [−0.009950, −0.003733] entirely < 0 with corrupted venue labels) ⇒ MACHINERY_SUSPECT per MECHANISMS §2-C2 falsifier: the C2 train gain does NOT depend on true venue labels, i.e. comparison-machinery fault. A negative control can never win; a winning control un-scores the candidate. Evidence retained in SELECTION_LEDGER.jsonl + SELECTION_CONTROLS.csv; retention does NOT un-kill — C2 is never fielded this cycle |
| 5 | **C3** — offseason EPA prior, θ=50 (config `C3_T050`) | **FIELDED** (only fielded candidate) | G-ENTRY PASS: pooled inner LL 0.648348; ΔLL vs B1* −0.004149 [−0.009944, +0.001837] (weak-positive: point < 0, CI includes 0 — admits the arm to accrue prospective evidence, never converts a train-internal CI into a claim); slope 1.0788 in band; time-shuffled-EPA-prior twin clean (ΔLL −0.000455 [−0.004890, +0.004169], no win). Lane A PIT verdict: PASS_PIT_SEASON_GRAIN, offseason-prior role ONLY (SUCCESSOR_DATA_AUDIT §3). Its time-shuffled twin is fielded as the DIAGNOSTIC-ONLY arm `C3_TWIN` (never a budget arm, never counted as a win) |
| 6 | C4 short-week×away interaction | **RELEASED (G-INT fail)** | No pre-registered δ>0 config has the away-short-week slice CI excluding 0 in the pre-registered direction with pooled direction consistent: δ=25 slice n=365 ΔLL +0.005637 [+0.002762, +0.008617] (wrong side, CI excludes 0), pooled +0.001614; δ=50 slice +0.012209 [+0.006457, +0.018169], pooled +0.003495 (SELECTION_REPORT §7). G-INT = FAIL ⇒ slot released; recorded as train-internal-only evidence with its selection-ledger rows |
| 7 | RESERVE | **RELEASED — owner named none before freeze** | PROTOCOL §3/§10-OQ-3: reserve must be named in the freeze packet before any prospective row, else released; the Option B registration instruction names no reserve ⇒ slot released, never reallocated |
| 8 | — | **RELEASED at freeze** | PROTOCOL §3 |
| 9 | — | **RELEASED at freeze** | PROTOCOL §3 |

**Fielded arms: 3 — B0, B1\*, C3.** Diagnostic arm: `C3_TWIN` (report-only). Selected config for
C3 is `C3_T050` (params `{"theta": 50.0}`); B1\*'s selection-ledger config id is `B1STAR`
(params `{"HCA": 0, "K": 40, "gamma": "2/3", "mu": 1500}`) — the ledger row alias for arm
`B1_STAR`. Dispositions verbatim: `{'C1': 'KILL', 'C2': 'KILL', 'C3': 'FIELD', 'C4': 'RELEASE'}`
(T_SELECT VERDICT_TABLE.md). Dead-arm law carries: rejected families (MOV-weighted Elo,
K/HCA/rest/form re-grids, additive logistic-over-elo_diff, in-season pbp, 538/odds/current-box)
stay dead — cited, never re-fit (PROTOCOL §0.9, MECHANISMS §3).

### 1.1 Canonical arm-config form and digests

`arm_config_digest` (LEDGER_SCHEMA.md §2 field 11) = sha256 (lowercase hex) over the canonical
JSON of the arm's frozen config: **JSON object, keys sorted lexicographically, separators `,`
and `:`, no whitespace, `ensure_ascii=false`, UTF-8 bytes** (LEDGER_SCHEMA §3 digest rule
applied to documents, sorted-key form). Schema id `nfl_ng_scored_v1_arm_config@1`. Canonical
strings and digests (also in freeze_digests.json):

- **B0** — `bea17ae49a33e460912aa9bdf9c0266da22d81c5168e4490e35194e49a2154aa`
  `{"arm_id":"B0","arm_schema":"nfl_ng_scored_v1_arm_config@1","cycle_id":"NFL-WINPROB-NG-SCORED-V1","p_home":"0.571399049390","p_home_derivation":"2765_home_wins_of_4839_non_tie_REG_rows_TRAIN_2000_2018","selection_status":"exempt_intercept_only","slot":1,"spec_type":"constant"}`
- **B1_STAR** — `5c97475c5df745056429e3eb075386e9b4f85729dbb9722eaf409f4b7fcbf32a`
  `{"arm_id":"B1_STAR","arm_schema":"nfl_ng_scored_v1_arm_config@1","cycle_id":"NFL-WINPROB-NG-SCORED-V1","frozen_from":"NFL-WINPROB-SCORED-V1","gamma":"2/3","hca":0,"k":40,"mu":1500,"selection_status":"exempt_baseline_law","slot":2,"spec_type":"own_elo","tie_update":"S_0.5"}`
- **C3** — `f7cde49880ee1f413f740c97a45ae4b863c017bf148326e116a7058126ecc74e`
  `{"arm_id":"C3","arm_schema":"nfl_ng_scored_v1_arm_config@1","config_id":"C3_T050","cycle_id":"NFL-WINPROB-NG-SCORED-V1","gamma":"2/3","hca":0,"k":40,"mu":1500,"pit_class":"PASS_PIT_SEASON_GRAIN","prior_entries":574,"prior_formula":"0.5*(off_EPA_per_play+def_EPA_per_play_allowed)","prior_pbp_seasons":"2000_2017","prior_role":"offseason_only_train_only","prior_source":"nflverse_pbp_frozen_snapshot","season_start_rule":"R_i=1500+gamma*(R_i-1500)+theta*z_i","selection_status":"selected_C3_T050","slot":5,"spec_type":"own_elo_plus_offseason_epa_prior","theta":50.0,"z_boundaries":"2001_2018","z_standardization":"(E-mean)/sd_across_32_lineages"}`
  (`prior_entries` 574 = measured (season,lineage) z-table entries, SELECTION_REPORT §2;
  z-boundaries 2001–2018; 2000 and expansion lineages carry no prior term — MECHANISMS §2-C3.)
- **C3_TWIN** (diagnostic-only) —
  `c86b3710ba1621adc879ad83222457969a395b810554241234cdf4c237036361`
  `{"arm_id":"C3_TWIN","arm_schema":"nfl_ng_scored_v1_arm_config@1","budget_arm":false,"control_name":"time_shuffled_epa_prior_twin","cycle_id":"NFL-WINPROB-NG-SCORED-V1","parent_arm":"C3","parent_config_id":"C3_T050","role":"diagnostic_negative_control","seed":20261005,"shuffle_rule":"shuffle_z_across_lineages_at_each_season_boundary_preserving_marginals","slot":"diagnostic","theta":50.0}`

Released slots carry no config and no digest. Changing any frozen input above invalidates the
digest and is a new registered trial, not an amendment (PROTOCOL §2.2).

## 2. Selection ledger (frozen)

- Paths (byte-identical copies, same sha256):
  `lanes/T_SELECT/SELECTION_LEDGER.jsonl` and
  `~/.my-quantitative-data/nfl-ng-scored-v1/selection/SELECTION_LEDGER.jsonl` — sha256
  `ff698d5d85e6144022bca7475daa3c2054ea92adc7a167549488e290fcedfd5a` (verified on disk by this
  lane; equals lane T's handoff claim).
- Row count: **38 rows = 28 config rows (B0 + B1* + C1×5 + C2×12 incl. designed null + C3×5 +
  C4×3) + 6 control rows + 4 arm_verdict rows (dispositions KILL/KILL/FIELD/RELEASE)** — counted
  by this lane from the file; matches SELECTION_REPORT §5 and DISPATCH item 2.
- Companion artifacts (sha256s in freeze_digests.json): SELECTION_REPORT.md
  (`4cb25090…`), SELECTION_CONFIGS.csv (`0bb91de1…`), SELECTION_CONTROLS.csv (`50e577c0…`),
  VERDICT_TABLE.md (`66bf4e48…`), in both locations.
- **Tie-break rule (applied, PROTOCOL §2.1):** selection criterion = pooled mean log loss over
  inner folds 2014–2018 (1,275 inner-eval rows); ties broken by fewer active parameters, then
  lexicographically smaller config id. No tie occurred among gate-eligible winners; C3_T050 is
  the unique band-compliant LL optimum among C3 grid points (θ=50 LL 0.648348 < θ=25 0.649196 <
  θ=75 0.649960; θ=75 is also in band but loses on LL; θ=0/100 FAIL).
- Designed-null equivalence held before any other number: C1_B000 / C2_NULL / C3_T000 / C4_D000
  reproduce B1*'s p_home stream bit-for-bit (max |Δp| = 0.0 on inner-eval stream and all 5,057
  rows; SELECTION_REPORT §4). Trial accounting complete: every evaluated config is a ledger row.
- Gate vocabulary (PROTOCOL §6.1): G-SELECT / G-ENTRY / G-PIT / G-INT as applied per arm in §1.

## 3. Data freeze

- **Schedules snapshot (registration-time freeze).**
  `~/.my-quantitative-data/nfl-ng-scored-v1/raw_schedules_fresh/games.csv` — sha256
  **`486d72273c0d9650756176fc016a0852c65ad6f030f443805c20cb35e387a9fc`** (re-hashed from disk by
  this lane; equals DOWNLOAD_MANIFEST.md/​.json claim and is byte-identical to the predecessor r1
  snapshot), 2,182,513 bytes, nflverse `schedules` release compile **2026-10-05T05:46:22Z**
  (`timestamp.json` in the same directory, sha256 `e771060881d4def7acd8c0e7b634a3c33d393c771f4d2464971421458e0adacf`,
  content `{"last_updated":"2026-10-05 01:46:22 EDT"}` — verified). Kickoff-UTC derivation:
  `gameday`+`gametime` in `America/New_York` (zoneinfo) → UTC (SUCCESSOR_DATA_AUDIT preamble).
  If a fresher pull ever replaces this file, its sha256 changes and the freeze moves with the new
  sha — never silently.
- **pbp 2000–2017 (C3 prior input).** 18 files, 315,021,834 bytes total, all HTTP 200, PAR1
  verified, downloaded 2026-10-05T09:02:02–09:02:41Z. Per-file sha256s are pinned in
  `lanes/A_DATA/DOWNLOAD_MANIFEST.json` — sha256 `bd53215d30bbd2322843eb10ea1271f3109d3a6f17f1919cf39ed696277b94af`
  (verified on disk; the `.md` twin is `4e9648699785428c6badb19145829309f560d1253c1cfab801beb6629e5f6603`).
  This packet **cites the manifest and its sha256 instead of re-hashing the 315 MB**; the
  manifest is the binding pin (spot re-download of season 2011 was byte-identical,
  `c54753b8…8795b1`). Files held at `~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2000_2017/`.
  Coverage: 17/18 seasons join games.csv exactly (0 orphans); 2000 is 99.2% complete with the 2
  missing games named (`2000_03_SD_KC`, `2000_06_BUF_MIA`); epa populated on 99.37–100.0% of
  team-attributable rows (PBP_COVERAGE_AUDIT §1/§3).
- **Rights.** CC BY 4.0, license sha256 `2a82ac9bbc3e3ee066908381e8d373896db5a6025d083fbd59692fe9ccfb9111`
  (re-fetched live 2026-10-05T09:01:18Z by lane A; equals the pinned predecessor sha; copy held
  at `~/.my-quantitative-data/nfl-ng-scored-v1/rights/nflverse-data_LICENSE.md`, sha verified on
  disk by this lane). Underlying league/ESPN publication-commercial rights remain UNVERIFIED —
  internal-research-only, fail-closed (§10).
- **TRAIN = complete seasons 2000–2018** (the §2 selection territory). Re-measured from the
  frozen snapshot: 2000=259, 2001=259, 2002–2018=267 each, 5,057 rows, 0 rows missing final
  scores; 2022 carries 271 REG rows (canceled BUF@CIN omitted upstream — consumers use row
  counts, never nominal 256/272); 9 tie rows 2000–2018 excluded from LL/training rows with
  per-season counts disclosed (SUCCESSOR_DATA_AUDIT §1; SELECTION_REPORT §2).
- **1999 excluded** (re-measured, not inherited prose): 259/259 rows have empty `gametime` and
  unparseable kickoff → not kickoff-capable (SUCCESSOR_DATA_AUDIT §1).
- **Kickoff fallback X = NOT ACTIVATED**: `gametime` 100% present in every season 2000–2026 on
  this snapshot; the trigger condition does not hold (SUCCESSOR_DATA_AUDIT §1).
- **Neutral-site law**: flag = games.csv `location` column (values {`Home`,`Neutral`} only);
  window 2000–2018 = 5,006 Home / **51 Neutral**; **HCA=0 on every `Neutral` row** (B1* carries
  HCA=0 so unaffected; any candidate HCA-like term zeroes it — PROTOCOL §0.6). Ties scored as
  excluded rows, `S=0.5` rating-update convention (TIE LAW, PROTOCOL §0.5).
- **32-lineage map (compact restatement).** One lineage = one rating stream (franchise
  continuity, PROTOCOL §0.4). The 32 current lineage codes are the identity space; games.csv
  carries 35 historical abbreviations whose only in-lineage mappings are
  **SD→LAC (2017), STL→LA (2016), OAK→LV (2020)** (measured season ranges, predecessor
  DATA_AUDIT_NFL_NG.md §5); CLE/BAL are separate lines; HOU enters 2002. nflverse pbp is already
  lineage-normalized to the 32 current codes (SD/STL/OAK absent in all pbp seasons; role-aligned
  2000 check: 257/257 games, 0 mismatches under the map) — the games.csv side must apply the map
  when pulling pre-2017 game-level labels (PBP_COVERAGE_AUDIT §2). C3 aggregates key directly on
  the 32-lineage convention.

## 4. Window and capture law

- **SPENT 2019–2025 — cite-only.** May be cited as prior evidence (with source paths and
  values); may never serve as hypothesis-testing window, selection window, re-scoring target,
  re-grid surface, or pooling partner (PROTOCOL §1.1).
- **PROSPECTIVE 2026+ — ledger-only.** Admissible evaluation rows are exclusively
  prediction-ledger rows recorded strictly before kickoff; there is no retrospective arm
  (PROTOCOL §1.3).
- **63 played games = NOT_RUN prospective, forever (count frozen).** All 63 have final scores,
  0 started-without-score; the prospective epoch is `2026-10-05T03:13:51Z` (controller bootstrap,
  predecessor state.json); the 09:06:07Z audit recount is a measurement instant, not a new
  epoch. Never backfilled, never presented as pre-game forecasts, never pooled into prospective
  aggregates (SUCCESSOR_DATA_AUDIT §2; PROTOCOL §1.3 played-before-record law).
- **209 future games at registration** (audit recount instant 2026-10-05T09:06:07Z on the frozen
  snapshot above; 272 REG scheduled total; 0 future rows carrying scores — law holds).
- **Earliest future kickoff: `2026_04_ATL_NO` 2026-10-06T00:15:00Z** (ATL@NO). Under the
  registered **Option B** (OWNER_DECISION_PACKET: week-5 slate from 2026-10-09 becomes the first
  prospective window), the **first prospective TARGET = week-5 opener `2026_05_TB_DAL`
  2026-10-09T00:15:00Z** (measured week-5 slate opener; 15 week-5 games). `2026_04_ATL_NO` and
  any other pre-week-5 game becomes capturable ONLY if the capture rule below is satisfied for
  it before its own kickoff — otherwise it is NOT_RUN prospective forever, like the 63.
- **Capture rule (mechanical, no discretion):** a week is capturable if and only if, AFTER owner
  GO at this cycle's gate, a recorder batch lands ≥ 6h before that week's first scheduled kickoff
  UTC and appends its rows to the ledger. No backfill; no retrospective rows, ever; games without
  rows are simply NOT_RUN (missing evidence is never inferred PASS).

## 5. Ledger law (nfl_ng_ledger@1)

- **Tool**: `nfl_ng_ledger@1` — append-only JSONL, flock+fsync, sha256 hash chain from a GENESIS
  anchor, closed 17-field rows (LEDGER_SCHEMA.md §2), no outcome columns, R1–R10 validator,
  no rewrite/delete API. 42/42 SYNTHETIC tests pass (handoff_E.json).
- **Provenance (predecessor source, read-only)**: implementation file
  `.worktrees/nfl-winprob-ng-prep-v1/integration/research/control/NFL-WINPROB-NG-PREP-V1/ledger/nfl_ng_ledger.py`
  — on-disk sha256 **`6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c`**
  (hashed by this lane; no git commands were run). Predecessor cycle id:
  `NFL-WINPROB-NG-PREP-V1`; its E-lane handoff (`lanes/E_LEDGER/handoff_E.json`, sha256
  `51190cfa8e9cd19e29f6c66970bad41fb951af060fdd9d2bb8dc2de53d88d1d4`) records the artifact
  commit `177fa4ef7a0b7066dd0c806fc31d6258b0b97d44` and the 42/42 test run. The dispatch-supplied
  predecessor branch head value (`14f28d62…`) was NOT verified here (git prohibited in this
  lane); the wave-4 port of the tool into this cycle's control tree carries the full provenance
  and will reconcile it. The port must reproduce the file at the sha256 above or disclose the
  delta.
- **Recorder = THIS cycle's controller** (or the single recorder role it appoints) — the ONLY
  writer of the ledger file; lane workers never write it; every row carries `recorded_by`
  (PROTOCOL §8).
- **Cadence**: one batch per NFL week (all rows for all games of the upcoming week, REG and
  POST, appended in a single session); playoff rounds follow the same per-round cadence before
  each round's first kickoff (PROTOCOL §8).
- **Margin**: each batch completes **≥ 6 hours before the week's first scheduled kickoff UTC**
  (or earlier whenever the schedule demands) — the frozen margin (PROTOCOL §8 placeholder
  adopted).
- **Scoring-time row classes (O-2, verbatim vocabulary)**: `VALID_PROSPECTIVE` ·
  `INVALID_PROSPECTIVE` · `NOT_SCORED_CANCELLED` · `NOT_RUN` (LEDGER_SCHEMA.md R10), plus the
  lane-E disclosed fifth class `NOT_SCORED_NO_ACTUAL_DATA` for rows whose game has no entry in
  the actual-kickoff input (handoff_E.json known_limitations). Only `VALID_PROSPECTIVE` rows
  enter aggregates; nothing is ever inferred PASS from absence.
- **Postponement / flex / cancellation laws — PROTOCOL §4, verbatim:**
  > - Postponed or flexed to a LATER time: the row remains `VALID_PROSPECTIVE` if
  >   `recorded_at_utc < actual kickoff` (the prediction was made before the game was played);
  >   moved-game count disclosed.
  > - Moved EARLIER past `recorded_at_utc`: `INVALID_PROSPECTIVE`.
  > - Cancelled (no result): `NOT_SCORED_CANCELLED`, disclosed, no outcome join.
  Notice rows `POSTPONEMENT_NOTICE` / `CANCELLATION_NOTICE` are chained inside the same
  append-only file (handoff_E.json); nothing is edited in place.
- **Timestamp law** (LEDGER_SCHEMA R2): `recorded_at_utc < kickoff_utc` strictly at append AND
  re-validated at scoring against ACTUAL kickoffs (`actual_kickoff_utc > recorded_at_utc` AND
  `actual_kickoff_utc ≥ successor cycle freeze timestamp`). Violations ⇒ `INVALID_PROSPECTIVE`,
  disclosed, never deleted, never patched. `p_home` is a string with exactly 6 fractional digits
  in strict (0,1) (R6); duplicates of (game_id, arm_id) rejected (R5); arm registry enforcement
  (R4) binds to §1 of this packet.

## 6. GENESIS

The ledger's first row anchors the chain: `prev_row_hash = "GENESIS:" + sha256_hex(freeze
packet file bytes)` (LEDGER_SCHEMA.md §1). This packet defines the canonical GENESIS payload and
pins its digest; the **real GENESIS row is written ONLY after owner GO** — never in this round.

- **Canonical payload fields** (schema `nfl_ng_scored_v1_genesis@1`):
  - `schema`: `"nfl_ng_scored_v1_genesis@1"`
  - `cycle_id`: `"NFL-WINPROB-NG-SCORED-V1"`
  - `freeze_digest`: sha256 over the **exact file bytes of `lanes/F_FREEZE/FREEZE_PACKET.md`**
    as written by this lane (canonical content = file bytes, UTF-8). Computed post-write;
    pinned in freeze_digests.json (a file cannot contain its own digest — the non-circular
    arrangement is: packet → freeze_digests.json → controller addendum).
  - `arm_set_ids`: `["B0","B1_STAR","C3"]` (§1); `diagnostic_arm_ids`: `["C3_TWIN"]`
  - `code_freeze_sha`: placeholder literal **`PENDING_CONTROLLER_ADDENDUM`** until the
    controller's addendum substitutes the measured integration HEAD sha (§9 two-step procedure)
  - `created_at`: placeholder literal **`POST_GO_TIMESTAMP`**; law — the real GENESIS is written
    **only after owner GO** with the real UTC timestamp (never before, never by an agent).
- **Serialization**: sorted keys, separators `,`/`:`, no whitespace, `ensure_ascii=false`, UTF-8
  (same canonical rule as §1.1).
- **Pinned digest**: sha256 of the canonical payload string **with `created_at` as the literal
  placeholder `POST_GO_TIMESTAMP`** (and `code_freeze_sha` as `PENDING_CONTROLLER_ADDENDUM`) is
  pinned in `lanes/F_FREEZE/freeze_digests.json` under `genesis.payload_sha256_pinned` (computed
  and written by this lane immediately after this packet).
- **Invalidation law**: changing ANY frozen input — this packet's bytes (⇒ freeze_digest), the
  arm set, the placeholder substitution rules, or either placeholder literal's meaning —
  invalidates the pinned digest. At GO the controller substitutes ONLY the two declared
  placeholders (`created_at`, `code_freeze_sha`); any other byte-level difference between the
  pinned payload and the written GENESIS payload is a registration failure and stops the
  program (PROTOCOL §6.3 ledger-integrity stop).

## 7. Metrics and gates (verbatim from PROTOCOL_NFL_NG.md §5)

**§5.1 Metrics** — "PRIMARY: mean log loss `LL = −mean[y·ln p + (1−y)·ln(1−p)]` on
`VALID_PROSPECTIVE` regular-season rows, ties excluded per TIE LAW (count disclosed)."
Secondary: "Brier score `mean[(p−y)²]`; 10 equal-width reliability bins on p with (n, mean p,
observed rate) per bin; **calibration slope** = binomial-GLM (logit link) coefficient of
`logit(p)` in `outcome ~ 1 + logit(p)`. … **Band: [0.85, 1.15]** (inherited)." B0's slope is
reported `N/A (degenerate)` in all successor tables. "**Playoffs separate.** Playoff rows are
scored with the same frozen config, reported separately per season and pooled-separately; NEVER
pooled into regular-season headline aggregates, never silently dropped."

**§5.2 Paired uncertainty** — "Per-game paired `ΔLL = LL(arm) − LL(reference)` on identical game
sets. 95% CI by block bootstrap resampling **kickoff calendar dates** with replacement
(clusters = kickoff dates…). 10,000 resamples, percentile CI." **Seed: INHERIT 20261005**
("the seed is not a tuning knob, no outcome was ever selected with it…"). "Sign convention:
Δ < 0 favors the arm."

**§5.3 Gates** (C = program candidate per the registered ranking rule below; "CI" =
kickoff-date-clustered bootstrap 95% CI). Program PASS for C requires ALL of:
- **T1 (discriminative gain over B1\*)**: pooled ΔLL(C, B1*) has CI entirely < 0 AND per-season
  ΔLL(C, B1*) < 0 on ≥ half of completed prospective seasons.
- **T2 (calibration)**: pooled calibration slope of C ∈ [0.85, 1.15].
- **T3 (floor safety)**: no completed prospective season where Brier(C) > Brier(B0), AND pooled
  ΔLL(C, B0) has CI entirely < 0.

REJECT (negative terminal) if ANY of:
- **R1**: CI of pooled ΔLL(B1*, B0) includes 0 or lies entirely > 0 → own-Elo dynamic strength
  adds nothing over the constant baseline at this grain → program premise fails.
- **R2**: pooled ΔLL(C, B0) CI entirely > 0 → candidate is worse than the constant baseline.
- **R3**: pooled ΔLL(C, B1*) CI entirely > 0 AND T2 violated → both degradation vs the dynamic
  baseline and miscalibration.

INCONCLUSIVE: "all decision CIs include 0 while T2 holds → no PASS; no re-tuning, no threshold
relaxation, no metric substitution, no baseline substitution; continuation requires a new
registered cycle with a NEW mechanism claim." "Single-season results are never PASS/REJECT
terminals regardless of gates."

**≥2-season rule (§7, verbatim core):** "**Strong conclusions require ≥2 completed prospective
seasons** (≈ ≥540 regular-season games, ties excluded with disclosure), each evaluated under the
identical frozen protocol, with per-season columns always shown alongside any pooled aggregate.
Only then may T1–T3 PASS or R1–R3 REJECT be asserted at program level." Single-season outputs
are labelled **descriptive** and carry the ≥2-season caveat verbatim.

**No outcome-based early stopping (§6.3, verbatim core):** "Once the prospective window is open,
metric readings do NOT stop arms: mid-window stopping on the primary metric is optional stopping
and is prohibited. Interim per-week metrics may be computed for monitoring and are
non-binding; decision reads happen once per completed prospective season."

**Candidate-ranking rule (REGISTERED, PROTOCOL §10-OQ-6):** C = **lowest pooled prospective LL
among fielded candidate slots**. The only fielded candidate is **C3** (slot 5) ⇒ C = C3 by
uniqueness; no ranking arithmetic is ever needed this cycle.

## 8. Power disclosure (verbatim, predecessor FREEZE_PACKET_DRAFT.md §6)

> One NFL regular season ≈ 272 games. Measured paired CI calibration (lane B POWER_NOTES):
> MDD(80%) ≈ 0.026–0.056 at 1 season; 0.019–0.039 at 2 seasons (~540); ~0.006–0.013
> train-internal (~4,839 games). Plausible single-mechanism effects (ΔLL 0.002–0.010) are
> STARVED at 1 season; 2 seasons adjudicates only ≥~0.02. Therefore: train-internal adjudication
> FIRST; prospective accrual is an evidence accumulator, not a 1-season verdict; STRONG
> conclusions require ≥2 completed prospective seasons; no outcome-based early stopping (decision
> reads once per completed season; prospective aborts are operational only).

## 9. Code freeze

On-disk sha256 as of this packet's writing (lanes/T_SELECT/, verified by this lane; identical to
lane T's handoff claims):

| file | sha256 |
|---|---|
| `arms.py` | `19dddd3ff2bec808e549981473e0523b4178cfd8c7c0db7c08b7e41a86d7d3e8` |
| `select.py` | `8f733d456e895959924df84f295b92b0292c4713eac2499b3f10b21bf66f4628` |
| `boot.py` | `0674b95fd7a4aa736e2a50821b1acd29606b8f30583cab6f46553433c1b0887a` |

**CODE_FREEZE_SHA** (the integration HEAD sha containing this packet) is measured and appended
by the **controller in the immediately-following control commit** — the two-step procedure
(commit the packet, measure HEAD, backfill the addendum in a tiny second commit),
precedent-authorized (PROTOCOL §11.5; handoff_E.json known_limitations documents the same
precedent). The GENESIS payload's `code_freeze_sha` placeholder (`PENDING_CONTROLLER_ADDENDUM`)
is substituted only by that controller addendum (§6). Any post-freeze change to the frozen
pipeline is a new registered trial (PROTOCOL §8: no arm config, feature, or threshold changes
after the first prospective row; `model_version`/`arm_config_digest` in every ledger row must
match this packet throughout the pre-registered horizon).

## 10. Boundaries

- **GO phrase (verbatim): `GO NFL WINPROB NG SCORED V1 PROSPECTIVE`** — owner-only, typed only
  at THIS cycle's own gate, AFTER the independent A7 prelaunch verdict. Agents never type it,
  never consume it, never treat any state as GO (P-8 two-key launch law). Nothing in this packet
  is a GO.
- **Rights posture: internal-research-only, fail-closed** on publication/commercial (CC BY 4.0
  covers the data; league/ESPN publication-commercial rights UNVERIFIED). Forbidden regardless
  of any decision: retrospective predictions for any played game; S1; paper/live; betting;
  data purchases; push/merge to main; scoring without typed GO (OWNER_DECISION_PACKET).
- Quarantine register carries forward (PROTOCOL §9): odds/probability columns quarantined at
  load (9 columns named in SELECTION_REPORT §2); in-season pbp features NOT_RUN_PIT (C3's
  offseason-prior role is the only surviving pbp use); injuries/availability NOT_RUN_PIT;
  weather NOT_RUN_PIT; tie 3-outcome model NOT_RUN_SCOPE; external forecasts BANNED.
- This packet does not consume trial budget and does not open the prospective window; the window
  opens only via the capture rule (§4) after GO.

## 11. Digest map

Every sha256 cited in this packet (files, arm configs, GENESIS pin) is recorded in
`lanes/F_FREEZE/freeze_digests.json` — written by this lane immediately after this packet. The
packet's own file sha256 (the GENESIS `freeze_digest` input) is pinned there as
`freeze_packet.sha256`; it cannot appear inside this file. Any mismatch between a cited digest
and the file on disk at consumption time is a STOP event (BLOCKED_TOOLING evidence), per the
dispatch stop conditions. This lane's verification pass found ZERO mismatches: all cited
predecessor/lane/data digests recomputed from disk equal their artifacts' claims (including
games.csv `486d7227…`, LICENSE `2a82ac9b…`, and all 13 lane-T handoff sha256 claims).

## 12. Evidence index (paths of record)

This cycle: `lanes/DISPATCH/DISPATCH_F_FREEZE.md`; `lanes/A_DATA/{SUCCESSOR_DATA_AUDIT.md,
DOWNLOAD_MANIFEST.md, DOWNLOAD_MANIFEST.json, PBP_COVERAGE_AUDIT.md, VERDICT_TABLE.md}`;
`lanes/T_SELECT/{SELECTION_REPORT.md, SELECTION_LEDGER.jsonl, SELECTION_CONFIGS.csv,
SELECTION_CONTROLS.csv, VERDICT_TABLE.md, arms.py, select.py, boot.py}`;
`lanes/DISPATCH/{handoff_A_DATA.json, handoff_T_SELECT.json}`;
`~/.my-quantitative-data/nfl-ng-scored-v1/{raw_schedules_fresh/, raw_pbp_2000_2017/, rights/,
selection/, provenance/}`. Predecessor (read-only): `research/control/NFL-WINPROB-NG-PREP-V1/
{FREEZE_PACKET_DRAFT.md, OWNER_DECISION_PACKET.md, state.json, event_log.jsonl, ledger/}`;
`lanes/C_PROTOCOL/{PROTOCOL_NFL_NG.md, LEDGER_SCHEMA.md}`;
`lanes/B_MECHANISMS/{MECHANISMS_NFL_NG.md, POWER_NOTES.md}`; `lanes/E_LEDGER/handoff_E.json`.
All sha256 values in freeze_digests.json.
