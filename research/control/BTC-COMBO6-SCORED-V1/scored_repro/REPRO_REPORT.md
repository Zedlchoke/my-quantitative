# REPRO REPORT — BTC-COMBO6-SCORED-V1 — R-REPRO (reproduction twin)

- Date (UTC): 2026-09-29
- Lane: R_REPRODUCTION, task_id BTC-COMBO6-R-REPRO
- Code freeze SHA under test: `c0f97a9db2e460707188877348af01d1c5d395d6`
- Twin worktree (detached, NO commits made): `/Users/hoangminhlong/my-quantitative/.worktrees/btc-combo6-scored-v1/repro_twin`
- Reference (integration, read-only): `/Users/hoangminhlong/my-quantitative/.worktrees/btc-combo6-scored-v1/integration` (branch `orca/btc-combo6-scored-v1-integration`)
- Python: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`

## 1. Twin construction

```
git -C /Users/hoangminhlong/my-quantitative worktree add \
  /Users/hoangminhlong/my-quantitative/.worktrees/btc-combo6-scored-v1/repro_twin \
  --detach c0f97a9db2e460707188877348af01d1c5d395d6
```

- `rev-parse HEAD` = `c0f97a9db2e460707188877348af01d1c5d395d6` (verified pre-
  and post-run; HEAD never moved, detached).
- `status --porcelain` clean at creation. After the run the ONLY entries are
  untracked outputs (no tracked file modified, no commits):
  - `research/control/BTC-COMBO6-SCORED-V1/scored/` (3 artifacts)
  - `research/control/BTC-COMBO6-SCORED-V1/TRIAL_LEDGER.jsonl`
  - `research/control/BTC-COMBO6-SCORED-V1/scored_repro/` (this evidence)
- Staging cache (`data_manifest.json`, `m5_panel.parquet`, build stamp) is
  committed at the freeze and was NOT rewritten (absent from status).
- Corpus used: committed kline zips + funding parquet, digest-verified against
  the pinned manifest by the frozen loader; `corpus_digest`
  `e270c9c77801aa19…` matches FREEZE.md.

## 2. Governance lock evidence (machine-wide heavy lock)

Driver: `scored_repro/run_locked_repro.py` (governance import:
`sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/research");
from governance import heavy_lock`). Machine-readable summary:
`scored_repro/lock_run_summary.json`; full log: `scored_repro/locked_run.log`.

| item | value |
|---|---|
| acquire | OK, pid 20268, `acquired_at_utc` 2026-09-29T02:56:27.987Z |
| cycle_id / role | BTC-COMBO6-SCORED-V1 / R_REPRODUCTION |
| worktree | twin path (above) |
| command registered | `[.venv/bin/python, <twin>/research/btcombo6/run_btcombo6.py, --mode, scored]` |
| expected_artifacts | `<twin>/research/control/BTC-COMBO6-SCORED-V1/scored/btcombo6_scored_stress1.0.json` |
| heartbeat | before scored, after scored, after truncation check (steps recorded in registry `extra`) |
| scored run | `subprocess` cwd=twin, rc=0, elapsed 7.3s |
| truncation check | `subprocess` cwd=twin, rc=0, elapsed 9.2s (inside the same lock window) |
| release | `FINISHED` at 2026-09-29T02:56:44.517Z (finally block), note "scored rc=0; truncation check rc=0 (all legs/cuts PASS)" |

No `NOT_RUN_RESOURCE_CONFLICT` / `CONTROL_STATE_DRIFT` occurred (lock proven
free immediately before, via `researchctl.py locks inspect` → FREE_PROVEN).

## 3. Scored artifact comparison (integration vs twin)

Raw file sha256s differ because `generated_utc` differs (runs at different
times); the required canonicalization removes ONLY `generated_utc`
(`json.dumps sort_keys` after key removal). Full details in
`scored_repro/compare_artifacts.json` (includes a recursive first-diff scan —
no differing field exists on any artifact).

| stress | content_sha256 (both sides, equal) | canonical equal (ignoring generated_utc) | matches dispatch pin |
|---|---|---|---|
| 1.0 | `d787697451af997b0c5f314937ac46444d747c35347dba4ed4370e95c615e5e6` | YES | YES (exact) |
| 1.5 | `f5eb9c915b6565f3f5a289fcdd3d713b4096d160a353384dbecbbf12f8ea9276` | YES | YES (exact) |
| 2.0 | `e1a43807dd659175fbda60b3239d1238757505ef52ebe70d0bc438cd24a2776d` | YES | NO — single-char discrepancy, see incident I-1 |

Raw file sha256 (reference / twin) — differ only through `generated_utc`
(`file_bytes_identical=False` expected; both sides' canonical content is
byte-equal):

- stress1.0: `8790e17e29c6d367d2985555995ecf6fce9175de37c2b928d5b56b2871fea184` / `136d59c16fceac0bb69e43f15d7838ae70a351511172a9b3bc2ed2fc7c61fe2e`
- stress1.5: `3a8ea4e65c21e9be7ec706533f1f3dbd1d3d004176f2ac3ace46afa08b028477` / `0ff829cb50c0c4348218b536e93b346b779f4e5184c6b319220c20032a3f6d9a`
- stress2.0: `d2ed67372a364755c3305d9364c3091ba495a3a09cad364be33ddea237aeba3a` / `0189e112370c6f168d940cc25f9c380447c5e770768803c3882bf814d7b22d31`

(Machine copies of these values: `compare_artifacts.json` fields
`integration_file_sha256` / `twin_file_sha256` — the JSON is authority.)

### TRIAL_LEDGER.jsonl

- Row inventory identical: 1 header + 7 scored_outcome rows
  (COMBO, LEG-1..LEG-6), same schemas.
- All 7 scored_outcome rows EQUAL ignoring only
  `generated_utc`/`updated_utc`/`created_utc` — matched on `cell`,
  `cell_kind`, full `stress` block (net_pnl + trade_count per tier),
  `verdict`, `trades_total`, and the full `scored_content_sha256` dict.
- Header equal ignoring the timestamp fields (`observed_scored_denominator`=8
  rows incl. header bookkeeping identical; `freeze_commit` placeholder
  identical on both sides).

### Incident I-1 (disclosed, does not affect the verdict)

The R-REPRO dispatch packet pinned stress=2.0 expected
`content_sha256` = `e1a43807dd659175fbda6033…` (char 22 = `3`). The actual
digest — identical in ALL FIVE independent recordings: integration artifact,
integration TRIAL_LEDGER rows (7/7 carry it), twin artifact, twin ledger, and
the twin's in-process recomputation at the freeze SHA — is
`e1a43807dd659175fbda60b3…` (char 22 = `b`). Two different contents cannot
differ by exactly one hex character in SHA-256; every code-produced and
committed record agrees on `…60b3…`, so the dispatch constant is assessed as
a single-character transcription error in the packet, not a reproduction
failure. Integration-vs-twin equality (the reproduction criterion) holds on
all three artifacts. Flagged for A1/owner acknowledgement.

## 4. Truncation-replay check (A7 F-5 INFO coverage) — ALL 6 legs x 3 cuts

Script: `scored_repro/truncation_check.py` (twin's own `data`/`signals`/
`engine`/`combo` modules on the real digest-verified corpus). Method: m5 panel
truncated at cut (`ts < cut`), funding truncated at cut, decisions REBUILT on
the truncated panel, leg backtest re-run; truncated trade list must equal the
full-run list's exact prefix (field-by-field) AND its length must equal the
count of full-run trades with `exit_ts < cut`. Sanity pre-check: in-process
full-run trades == twin scored stress-1.0 artifact trades for all 6 legs
(PASS 6/6). Engine `_guard_sealed` ran on every full and truncated run.

Cuts: `2022-07-01T00:00:00Z`, `2024-01-01T00:00:00Z`, `2025-06-01T00:00:00Z`.

| leg | full trades | 2022-07-01 | 2024-01-01 | 2025-06-01 |
|---|---|---|---|---|
| LEG-1 | 3795 | PASS (1778/1778) | PASS (2555/2555) | PASS (3549/3549) |
| LEG-2 | 401 | PASS (188/188) | PASS (269/269) | PASS (370/370) |
| LEG-3 | 226 | PASS (89/89) | PASS (144/144) | PASS (206/206) |
| LEG-4 | 581 | PASS (301/301) | PASS (406/406) | PASS (546/546) |
| LEG-5 | 660 | PASS (339/339) | PASS (463/463) | PASS (621/621) |
| LEG-6 | 417 | PASS (205/205) | PASS (278/278) | PASS (391/391) |

(cell = truncated trades / expected prefix length; `prefix_ok` and `count_ok`
both True in all 18 cells; several truncated runs ended with a position OPEN
at the cut — engine leaves it open with no synthetic record, preserving the
prefix law. Machine detail: `scored_repro/truncation_check.json`.)

## 5. Verdict

REPRO_VERDICT: ALL_MATCH

- All three scored artifacts canonical-equal (integration vs twin), ignoring
  ONLY `generated_utc`; `content_sha256` fields equal on every artifact and
  equal to the pinned constants for 1.0/1.5 (2.0: see incident I-1 — both
  sides identical, dispatch pin has a one-char typo).
- TRIAL_LEDGER scored_outcome rows equal (7/7) ignoring the three timestamp
  fields; header equal likewise.
- Truncation-replay prefix law: 18/18 PASS (6 legs x 3 cuts) + 6/6 artifact
  trades sanity match.

Twin left in place (detached at c0f97a9d, outputs untracked); no commits made
anywhere by this lane; integration worktree touched ONLY by the handoff file
`research/control/BTC-COMBO6-SCORED-V1/handoffs/R_REPRO.json` (A1 commits it).
