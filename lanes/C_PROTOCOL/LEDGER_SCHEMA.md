# LEDGER_SCHEMA — prospective NFL prediction ledger (`nfl_ng_ledger@1`)

- Cycle: `NFL-WINPROB-NG-PREP-V1` · Lane: `C_PROTOCOL` · Task: `nflng-c-proto` · Date: 2026-10-05
- Status: DESIGN ONLY. The schema below is the preregistration the successor scored cycle's
  freeze packet must adopt (unchanged, or amended by a registered amendment) before the first
  prospective row is recorded. No ledger file exists yet by construction.
- Companion document: `PROTOCOL_NFL_NG.md` (§4 ledger law, §8 operational plan).
- All examples in this document are **SYNTHETIC** (fabricated teams `TEAM_X`/`TEAM_Y`,
  fabricated ids, fabricated digests). They contain no real-game predictions.

## 1. File form

- One JSON object per line (**JSONL**), UTF-8, no blank lines, no comments.
- File is **append-only** (opened in append mode; never rewritten). Row order = append order.
- The first row anchors the chain: its `prev_row_hash` is
  `"GENESIS:" + sha256_hex(freeze_packet_file_bytes)`.
- One ledger file per (cycle_id, season). Filename:
  `predictions_<cycle_id>_<season>.jsonl`.

## 2. Row schema (exact field order — canonical order is binding)

| # | Field | Type | Rule |
|---|---|---|---|
| 1 | `schema_version` | string | exactly `"nfl_ng_ledger@1"` |
| 2 | `cycle_id` | string | the scored successor cycle id, e.g. `"NFL-WINPROB-NG-SCORED-V1"` |
| 3 | `game_id` | string | unique game identifier from the Lane-A-audited schedule (source-native id) |
| 4 | `season` | integer | NFL season year, ≥ 2026 for prospective rows |
| 5 | `game_type` | string | `"REG"` or `"POST"` only; `PRE` is forbidden (dropped upstream, count disclosed) |
| 6 | `home_team` | string | home team id from the audited crosswalk |
| 7 | `away_team` | string | away team id from the audited crosswalk |
| 8 | `kickoff_utc` | string | **scheduled** kickoff at record time, ISO 8601 UTC with `Z` suffix, e.g. `"2026-09-10T00:15:00Z"` |
| 9 | `recorded_at_utc` | string | append timestamp, ISO 8601 UTC with `Z` suffix; must be strictly < `kickoff_utc` (R2) |
| 10 | `arm_id` | string | one of the frozen arm registry ids (R4), e.g. `"B0"`, `"B1_STAR"`, `"C1"`, `"C2"`, `"C3"`, `"C_INT"`, `"RESERVE"` |
| 11 | `arm_config_digest` | string | `sha256_hex` of the canonical JSON of the arm's full frozen config from the freeze packet (R3) |
| 12 | `model_version` | string | pipeline identity at record time: `<git_commit_sha>+<pipeline_config_digest>` |
| 13 | `inputs_digest` | string | `sha256_hex` over the sorted list of `"<source_id>=<snapshot_sha256>"` entries of the versioned input-snapshot manifest used to compute this row (R3) |
| 14 | `p_home` | string | model output for P(home team wins), serialized as a **string with exactly 6 decimal places**, e.g. `"0.542317"`; strict (0,1) (R6). String form avoids cross-language float-serialization drift so `row_hash` recomputation is deterministic |
| 15 | `recorded_by` | string | recorder session id (controller-designated recorder role, PROTOCOL §8) |
| 16 | `prev_row_hash` | string | `row_hash` of the previous line; `"GENESIS:<64-hex>"` for line 1 (R1) |
| 17 | `row_hash` | string | `sha256_hex` of the canonical serialization defined in §3 |

- **No outcome fields.** The row contains no scores, results, winners, or any post-game
  quantity. Outcomes are joined at scoring time from the audited final data (R8).
- Field additions require a registered schema-version bump; the 17 fields above are closed
  under `nfl_ng_ledger@1`.

## 3. Canonical serialization and `row_hash`

- Canonical form of a row: JSON object with keys in the exact field order of §2,
  separators `,` and `:`, no whitespace, `ensure_ascii=false`, UTF-8.
- `row_hash = sha256_hex( canonical_json(row_with_row_hash_removed) )` — i.e., over the row
  including `prev_row_hash`, excluding `row_hash` itself.
- `sha256_hex` = lowercase 64-character hexadecimal digest.
- Digests (`arm_config_digest`, `inputs_digest`) are computed over canonical JSON of their
  respective documents with the same separators/no-whitespace rule.

## 4. Validation rules

The validator runs (a) at **append time** (recorder's pipeline refuses to write an invalid
row) and (b) at **scoring time** over the complete file (defense in depth). A scoring-time
failure of R1/R3/R5 invalidates every row from the first violating row forward (ledger
integrity failure → program-level stop per PROTOCOL §6.3).

- **R1 Ordering / chain integrity**: for each line i>1, `prev_row_hash(i) == row_hash(i−1)`;
  line 1 has `prev_row_hash == "GENESIS:" + sha256_hex(freeze_packet_bytes)`; every
  `row_hash` recomputes per §3.
- **R2 Timestamp law**: `recorded_at_utc < kickoff_utc` strictly (string compare valid for
  same-format ISO 8601 UTC; validator parses both). At scoring time, re-validated against
  the **actual** kickoff from final data: `actual_kickoff_utc > recorded_at_utc` AND
  `actual_kickoff_utc ≥ successor cycle freeze timestamp`. Violations ⇒
  `INVALID_PROSPECTIVE` (excluded from all aggregates, count disclosed, row never deleted).
- **R3 Digest law**: `arm_config_digest` matches an entry in the freeze packet's arm
  registry; `model_version`'s commit sha resolves to a commit on the cycle branch;
  `inputs_digest` recomputes from the archived snapshot manifest. Any mismatch ⇒ row
  `INVALID_PROSPECTIVE` (disclosed).
- **R4 Arm registry**: `arm_id` ∈ frozen enumeration of PROTOCOL §3; no arm outside the
  registry may ever append a row.
- **R5 No duplicates**: `game_id` unique per `arm_id` (at most one row per (game, arm) per
  season file).
- **R6 Probability domain**: `p_home` parses as a finite decimal with exactly 6 fractional
  digits and satisfies `0 < p_home < 1` strictly. Scoring-time clamping to
  [1e-15, 1−1e-15] happens downstream at metric computation, never in the ledger.
- **R7 Game-type enum**: `game_type ∈ {"REG","POST"}`; `season ≥ 2026`.
- **R8 No-outcome check**: no key in any row matches the outcome-vocabulary list
  (`score`, `home_score`, `away_score`, `result`, `winner`, `outcome`, `total`, `spread`);
  the validator fails the file if any appears (retro-injection guard).
- **R9 Immutability**: the file is never rewritten; any byte-level change before the final
  append offset breaks R1 from that point (detected by full-file rehash at scoring time
  against the chain).
- **R10 Scoring-time classifications** (mutually exclusive, counts disclosed):
  `VALID_PROSPECTIVE` · `INVALID_PROSPECTIVE` · `NOT_SCORED_CANCELLED` (no result exists)
  · `NOT_RUN` (no row exists for a game actually played inside the prospective window).
  Only `VALID_PROSPECTIVE` rows enter aggregates; nothing is ever inferred PASS from
  absence.

## 5. SYNTHETIC example rows

**All rows below are SYNTHETIC**: fabricated teams (`TEAM_X`, `TEAM_Y`, `TEAM_Z`),
fabricated game ids (`SYN-2026-0001`…), fabricated digests (`SYNTH…`), fabricated session
ids. They illustrate the schema; they are not predictions of any real game and no real
team ids, kickoffs, or probabilities appear.

Line 1 (chain anchor, B0):
```json
{"schema_version":"nfl_ng_ledger@1","cycle_id":"SYN-CYCLE","game_id":"SYN-2026-0001","season":2026,"game_type":"REG","home_team":"TEAM_X","away_team":"TEAM_Y","kickoff_utc":"2026-09-10T00:15:00Z","recorded_at_utc":"2026-09-09T18:00:00Z","arm_id":"B0","arm_config_digest":"SYNTH000000000000000000000000000000000000000000000000000000b0","model_version":"SYNTHCOMMIT000+SYNTHPIPE000","inputs_digest":"SYNTH0000000000000000000000000000000000000000000000000000in01","p_home":"0.564932","recorded_by":"SYN-RECORDER-1","prev_row_hash":"GENESIS:SYNTH0000000000000000000000000000000000000000000000000000genesis","row_hash":"SYNTH0000000000000000000000000000000000000000000000000000row001"}
```

Line 2 (same game, B1*):
```json
{"schema_version":"nfl_ng_ledger@1","cycle_id":"SYN-CYCLE","game_id":"SYN-2026-0001","season":2026,"game_type":"REG","home_team":"TEAM_X","away_team":"TEAM_Y","kickoff_utc":"2026-09-10T00:15:00Z","recorded_at_utc":"2026-09-09T18:00:01Z","arm_id":"B1_STAR","arm_config_digest":"SYNTH0000000000000000000000000000000000000000000000000000b1st","model_version":"SYNTHCOMMIT000+SYNTHPIPE000","inputs_digest":"SYNTH0000000000000000000000000000000000000000000000000000in01","p_home":"0.612084","recorded_by":"SYN-RECORDER-1","prev_row_hash":"SYNTH0000000000000000000000000000000000000000000000000000row001","row_hash":"SYNTH0000000000000000000000000000000000000000000000000000row002"}
```

Line 3 (different game, candidate arm C1):
```json
{"schema_version":"nfl_ng_ledger@1","cycle_id":"SYN-CYCLE","game_id":"SYN-2026-0002","season":2026,"game_type":"REG","home_team":"TEAM_Z","away_team":"TEAM_X","kickoff_utc":"2026-09-13T17:00:00Z","recorded_at_utc":"2026-09-09T18:00:02Z","arm_id":"C1","arm_config_digest":"SYNTH0000000000000000000000000000000000000000000000000000c100","model_version":"SYNTHCOMMIT000+SYNTHPIPE000","inputs_digest":"SYNTH0000000000000000000000000000000000000000000000000000in01","p_home":"0.431900","recorded_by":"SYN-RECORDER-1","prev_row_hash":"SYNTH0000000000000000000000000000000000000000000000000000row002","row_hash":"SYNTH0000000000000000000000000000000000000000000000000000row003"}
```

Line 4 (playoff row, same week-batch discipline applies per round):
```json
{"schema_version":"nfl_ng_ledger@1","cycle_id":"SYN-CYCLE","game_id":"SYN-2026-POST-01","season":2026,"game_type":"POST","home_team":"TEAM_Y","away_team":"TEAM_Z","kickoff_utc":"2027-01-09T01:15:00Z","recorded_at_utc":"2027-01-08T19:00:00Z","arm_id":"B1_STAR","arm_config_digest":"SYNTH0000000000000000000000000000000000000000000000000000b1st","model_version":"SYNTHCOMMIT000+SYNTHPIPE000","inputs_digest":"SYNTH0000000000000000000000000000000000000000000000000000in42","p_home":"0.578210","recorded_by":"SYN-RECORDER-1","prev_row_hash":"SYNTH0000000000000000000000000000000000000000000000000000row003","row_hash":"SYNTH0000000000000000000000000000000000000000000000000000row004"}
```

Illustrative validator verdicts (still SYNTHETIC):
- A row identical to Line 2 but with `recorded_at_utc` = `"2026-09-10T01:00:00Z"` would
  fail R2 at append time (after scheduled kickoff) and be `INVALID_PROSPECTIVE` if it ever
  appeared in the file.
- Two Line-2 duplicates would fail R5.
- Any row carrying a `"home_score"` key fails R8 outright.
