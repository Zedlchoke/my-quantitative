# nfl_ng_ledger — append-only prospective NFL prediction ledger (PREP lane E)

Implementation of Lane C's `LEDGER_SCHEMA.md` (schema **`nfl_ng_ledger@1`**), cycle
`NFL-WINPROB-NG-PREP-V1`. PREP-only: this directory contains **no real games, no real
predictions, no metrics on outcomes, and no ledger file** — the tool and its SYNTHETIC
test suite only. The successor scored cycle adopts both unchanged (or amends them via a
registered amendment) before its first prospective row.

Files:

- `nfl_ng_ledger.py` — stdlib-only module (Python ≥ 3.10; `fcntl`-based locking).
- `test_ledger_synthetic.py` — SYNTHETIC pytest suite (teams `TEAM_X/Y/Z`, fabricated ids
  and digests; no NFL team names anywhere).

Test evidence (run from this lane's worktree root):

```
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
  research/control/NFL-WINPROB-NG-PREP-V1/ledger/test_ledger_synthetic.py -v
# 42 passed, exit code 0
```

## THE LAW (read before any use)

> **Retro-impossibility law.** A prediction row exists to prove it was written strictly
> before its game was played. At scoring time every row is re-checked against the
> **actual** kickoff from the audited final data: a row whose game's actual kickoff is
> **not strictly after** the row's `recorded_at_utc` (`actual <= recorded_at`) is
> `INVALID_PROSPECTIVE` (the dispatch shorthand is "NOT_RUN prospective"), and a game
> whose actual kickoff precedes the cycle freeze timestamp is `NOT_RUN`
> (played-before-record write-off). Both classes are **permanent** — they are excluded
> from all aggregates, counts are disclosed, rows are never deleted or patched, and they
> **can never be repaired retroactively**. A game actually played with **no** row at all
> is `NOT_RUN` game-level: missing evidence is `NOT_RUN`, never inferred `PASS`.

## Ledger form (LEDGER_SCHEMA.md §1–§3)

- JSONL, UTF-8, one JSON object per line, no blank lines; **append-only by construction**
  (the only write path is a locked end-append; there is no rewrite/edit/delete API).
- One file per (cycle, season), named `predictions_<cycle_id>_<season>.jsonl` (enforced).
- Rows are the closed 17-field schema, written in the §2 binding field order.
- `row_hash = sha256_hex(canonical_json(row_without_row_hash))` — canonical form rebuilds
  the row in the §2 field order with separators ``,`/``:`, `ensure_ascii=false`, UTF-8.
  Line 1 carries `prev_row_hash = "GENESIS:" + sha256_hex(freeze_packet_file_bytes)`.

## Usage for the successor scored cycle

```python
import importlib.util                      # stdlib-only module; import by path:
_spec = importlib.util.spec_from_file_location(
    "nfl_ng_ledger",
    "research/control/NFL-WINPROB-NG-PREP-V1/ledger/nfl_ng_ledger.py")
ledger = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(ledger)

# 1) FREEZE — inside the freeze packet, before any prospective row:
#      genesis_digest = sha256_hex(freeze_packet_file_bytes)      # 64 lowercase hex
#      freeze_utc     = "<cycle freeze timestamp, ISO-8601 Z>"
#      arm_registry   = [...]                                     # frozen §3 enumeration
ledger.create_ledger(
    "predictions/NFL-WINPROB-NG-SCORED-V1/predictions_<CYCLE>_2026.jsonl",
    genesis_digest="…64-hex…",
    cycle_id="<SCORED-CYCLE>", season=2026,
    arm_registry=["B0", "B1_STAR", "…"],   # optional; enforced on every append (R4)
    freeze_utc="2026-…T…Z",                # optional; scoring NOT_RUN gate default
)

# 2) RECORD — one weekly batch (REG and POST), single recorder session,
#    completed before the week's FIRST kickoff UTC (PROTOCOL §8, margin ≥ 6 h):
ledger.append(path, {
    "schema_version": "nfl_ng_ledger@1",
    "cycle_id": "<SCORED-CYCLE>",
    "game_id": "<Lane-A-audited schedule id>",
    "season": 2026,
    "game_type": "REG",                     # "REG" | "POST"; PRE forbidden
    "home_team": "<crosswalk id>", "away_team": "<crosswalk id>",
    "kickoff_utc": "2026-09-10T00:15:00Z",  # scheduled, from the frozen schedule snapshot
    "recorded_at_utc": "2026-09-09T18:00:00Z",  # STRICTLY < kickoff_utc (R2, enforced)
    "arm_id": "B1_STAR",                    # ∈ frozen registry (R4)
    "arm_config_digest": "<sha256 of the arm's frozen config>",   # structural 64-hex here
    "model_version": "<commit_sha>+<pipeline_config_digest>",
    "inputs_digest": "<sha256 over sorted 'source=snapshot_sha' manifest entries>",
    "p_home": "0.542317",                   # STRING, exactly 6 decimals, strict (0, 1) (R6)
    "recorded_by": "<recorder session id>",
    "prev_row_hash": "GENESIS:<digest>",    # line 1; later rows: the previous line's row_hash
})
# append() computes row_hash, enforces R1/R2/R4/R5/R6/R7/R8 structurally, flocks, fsyncs,
# and refuses anything doubtful (fail-closed).

# 3) VERIFY — cheap read any time; full re-hash walk + re-validation of every law:
broken = ledger.verify_chain(path)              # [] means intact (R1/R9)
broken = ledger.verify_chain(path, expected_genesis_digest=genesis_digest)

# 4) DISCLOSE schedule changes (append-only notices, see below):
ledger.postpone(path, game_id, "2026-09-13T19:00:00Z", "reason",
                noticed_at_utc="…Z", recorded_by="<session>")
ledger.cancel(path, game_id, "reason", noticed_at_utc="…Z", recorded_by="<session>")

# 5) SCORE — the real anti-retrospective gate (run per completed season):
report = ledger.validate_for_scoring(
    path,
    actual_kickoffs={game_id: "<actual kickoff ISO-Z from audited final data>", ...},
    cancelled_games={"<game_id>", ...},          # optional; in-file notices also count
    freeze_utc=freeze_utc,                        # defaults to the genesis-bound value
)
assert report["freeze_check"] == "APPLIED"
# report["rows"]  → per-row verdicts; only VALID_PROSPECTIVE rows are aggregate-eligible.
# report["not_run_games"] → played games with no rows (missing evidence, disclosed).
# Any chain break raises LedgerIntegrityError: program-level stop (PROTOCOL §6.3).
```

## Postponement / cancellation

The schema fixes the **classification** (PROTOCOL §4) but is silent on a disclosure
mechanism. This tool emits hash-chained notice rows inside the same append-only file, so
disclosure is tamper-evident and nothing is ever edited in place:

- `postpone(...)` appends a `POSTPONEMENT_NOTICE` (prior/new kickoff, reason,
  `noticed_at_utc`, `affected_row_indices`). A move **later** leaves existing rows valid
  (re-confirmed at scoring against the actual kickoff); a move **earlier past a row's
  `recorded_at_utc`** makes those rows `INVALID_PROSPECTIVE` at scoring time.
- `cancel(...)` appends a `CANCELLATION_NOTICE`; the game's rows classify
  `NOT_SCORED_CANCELLED` (excluded, no outcome join), whether the status comes from the
  notice or from the scoring-time `cancelled_games` input.

## Scoring-time classification (R10)

| Verdict | Condition (checked in order) |
|---|---|
| `NOT_SCORED_CANCELLED` | game cancelled (input or in-file notice) |
| `NOT_SCORED_NO_ACTUAL_DATA`* | game absent from `actual_kickoffs` (unresolved; excluded) |
| `INVALID_PROSPECTIVE` | `actual_kickoff <= recorded_at_utc` (retro-injection / earlier move) |
| `NOT_RUN` | `actual_kickoff < freeze_utc` (played-before-record write-off) |
| `VALID_PROSPECTIVE` | otherwise — the only aggregate-eligible class |

\* documented schema-silent extension (see limitations).

## Schema-silent decisions made by this tool (for the successor freeze packet)

1. **Genesis record sidecar.** `create_ledger` writes an adjacent self-hashed
   `<ledger>.genesis.json` binding the file to its GENESIS digest, cycle id, season,
   optional arm registry (R4 enforcement) and optional freeze timestamp. The schema only
   fixes line 1's `GENESIS:` anchor; the sidecar is the tool's durable binding and must
   never be rewritten after creation.
2. **Notice row types** (`POSTPONEMENT_NOTICE`, `CANCELLATION_NOTICE`) with their own
   fixed field order, chained into the same hash chain. Any successor adoption should
   restate this in the freeze packet; otherwise the adjacent-file alternative must be
   registered instead.
3. **`NOT_SCORED_NO_ACTUAL_DATA`** fifth class for rows whose game has no entry in the
   scoring input (season incomplete). Excluded from aggregates, disclosed — never
   silently dropped and never inferred PASS.
4. **Structural digest checks only at append** (64-hex form for `arm_config_digest` /
   `inputs_digest`). Semantic R3 (digests match the freeze registry, commit resolves,
   manifest recomputes) is a scoring-time law against the freeze packet — out of scope
   for this module.
5. **Canonical field order** (§2 binding order, not alphabetically sorted keys) is used
   for both `row_hash` and the written line, per LEDGER_SCHEMA.md §2/§3 ("canonical
   order is binding"); the dispatch packet's "sorted keys" shorthand was superseded by
   the schema.
6. **Locking discipline**: appends take an exclusive `fcntl.flock`; all writers must use
   this module (non-cooperating filesystem writers are outside any tool's reach and are
   caught by `verify_chain`).

## Known limitations

- `validate_for_scoring` with `freeze_utc=None` (and no genesis-bound freeze) skips the
  NOT_RUN freeze gate and reports `freeze_check: "SKIPPED"` — the successor must bind a
  freeze timestamp for the full R2 gate.
- A full-file rewrite that recomputes every hash and re-anchors line 1 to the correct
  GENESIS digest is undetectable by chain mechanics alone; detection relies on the freeze
  packet pinning the GENESIS digest (R1) and on publishing/committing the ledger tail
  hash per batch (operational discipline, PROTOCOL §8).
- Single-file scope: one ledger per (cycle, season); cross-season pooling is a
  freeze-packet decision (PROTOCOL §7.3), not a tool feature.
