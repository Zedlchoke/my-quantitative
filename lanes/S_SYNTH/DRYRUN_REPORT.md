# DRYRUN_REPORT — S_SYNTH lane, cycle NFL-WINPROB-NG-SCORED-V1

Synthetic-only sandbox rehearsal of the full prospective record pipeline. Every game,
lineage, digest input, and timestamp in the dry run is FABRICATED (`SYNTH_` game ids,
`SYN_T01…SYN_T30` lineages, kickoffs 2028–2030). No real game data was read as a dry-run
input, no metric was computed on any outcome, no betting vocabulary is used. Interpreter
for every command: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`. No git commands.

## 1. Port (task 1) — full detail in PORT_NOTES.md

```
$ cmp <predecessor>/nfl_ng_ledger.py research/control/NFL-WINPROB-NG-SCORED-V1/ledger/nfl_ng_ledger.py   # silent
$ cmp <predecessor>/test_ledger_synthetic.py research/control/NFL-WINPROB-NG-SCORED-V1/ledger/test_ledger_synthetic.py  # silent
$ cmp <predecessor>/README.md research/control/NFL-WINPROB-NG-SCORED-V1/ledger/README.md  # silent
→ BYTE-IDENTICAL port; sha256s (pre == post, and == freeze_digests.json pins):
  nfl_ng_ledger.py        6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c
  test_ledger_synthetic.py 93d3e248ae7190710bc334a638ff41e7a8394a9ea0ce140789157663a105bc1d
  README.md               d44e945f1d0c0ddd8271e08333fc4dbeb1d95314f6356b385c4f46dec5575256
```

## 2. Command ledger (all commands run from the worktree root)

| # | command | exit code | result |
|---|---|---|---|
| 1 | `.venv/bin/python -m pytest research/control/NFL-WINPROB-NG-SCORED-V1/ledger/test_ledger_synthetic.py -v` | 0 | **42 passed** (predecessor suite on the ported copy) |
| 2 | `.venv/bin/python -m pytest lanes/S_SYNTH/test_successor_synthetic.py -v` | 0 | **16 passed** (successor suite) |
| 3 | `.venv/bin/python lanes/S_SYNTH/sandbox_dryrun.py` | 0 | SANDBOX DRY-RUN OK (run 1) |
| 4 | `.venv/bin/python lanes/S_SYNTH/sandbox_dryrun.py --reset` | 0 | SANDBOX DRY-RUN OK (run 2) |
| 5 | `shasum -a 256 <sandbox ledger>` after run 1 vs run 2 | 0 | **identical**: `77029ae6713921ab204555b42eea36b368e905ec81fac7912b3ba2afa85b343c` — byte-level determinism |

Successor-suite coverage (16 tests, all PASS): frozen-code/port digest identity;
designed-null equivalence C1 β=0 / C2 λ=0∧h=0 / C3 θ=0 / C4 δ=0 vs B1\* — **max |Δp| == 0.0,
bit-identical (`.tobytes()` equal) on 4 synthetic streams**; null-is-not-vacuous power check
(nonzero grid values DO move p_home); C3 θ=50 determinism (byte-identical serialize + tobytes);
as-of canaries (same-kickoff, later-kickoff, input-assembly) — a result with kickoff ≥
prediction time is absent from prediction inputs; tool R2 (recorded_at == and > kickoff
rejected; 1s before accepted); tool margin-config absence (NOT_RUN_MARGIN_CONFIG — the only
"margin" in the ported source is the R8 OUTCOME_BLOCKLIST token) + caller-side ≥6h capture
margin enforced (exact 6h accepted, 5h59m and post-kickoff rejected); single-byte-flip hash-chain
tamper on a sandbox ledger copy (last row and first row) — `verify_chain` flags exactly the
tampered row, `append` and `validate_for_scoring` fail closed.

## 3. Sandbox dry-run contents (task 3)

- Ledger created **through the PORTED tool** at
  `~/.my-quantitative-data/nfl-ng-scored-v1/sandbox/predictions_NFL-WINPROB-NG-SCORED-V1-SANDBOX_2030.jsonl`
  (`cycle_id = NFL-WINPROB-NG-SCORED-V1-SANDBOX`, `season = 2030`; the tool's §1 filename law
  `predictions_<cycle_id>_<season>.jsonl` is enforced by the byte-identical tool — see
  PORT_NOTES.md §3.2 for the dispatch-name deviation).
- **Sandbox GENESIS digest** `e59ec10c61fa318969aa962589b8588f67b1f6aa6e36fd504b11e8e0b2d265b0`
  (sha256 of the sandbox genesis descriptor) — asserted `!=` the freeze GENESIS
  `ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7`, which is **absent from
  every sandbox byte** (ledger + sidecar) by assertion. Line 1 anchors `GENESIS:e59ec10c…`.
- Synthetic week: **15 games** `SYNTH_2030_W1_G01…G15`, kickoffs 2030-09-12…2030-09-16 UTC,
  `recorded_at_utc = 2030-09-05T12:00:00Z` (capture margin **173.0 h ≥ 6 h**, enforced
  caller-side per row and for the batch).
- Arms exactly per freeze (FREEZE_PACKET.md §1): **B0** constant `0.571399049390` → ledger
  `0.571399` (R6 6-dp); **B1\*** own-Elo K=40/HCA=0/γ=2/3 replayed over a 360-game synthetic
  prior stream (seasons 2028–2029) with the as-frozen `lanes/T_SELECT/arms.py` (sha256
  asserted = freeze §9 `19dddd3f…`); **C3** θ=50 (`C3_T050`) with synthetic prior-season EPA
  z values standardized by the frozen `arms.z_standardize`. Rows carry the frozen
  `arm_config_digest`s (`bea17ae4…`, `5c97475c…`, `f7cde498…`).

## 4. Counts and validations (from `dryrun_evidence.json` in the sandbox)

| check | result |
|---|---|
| rows appended | **45 = 15 games × 3 arms** |
| `(game_id, arm_id)` pairs distinct | **45 / 45** |
| chain `verify_chain(path)` | `[]` (intact) |
| chain vs expected sandbox genesis | `[]` (intact) |
| non-`SYNTH_` game ids | **0** |
| freeze GENESIS digest in sandbox bytes | absent |
| re-`create_ledger` refusal (append-only discipline) | raised as required |
| scoring-gate rehearsal (`validate_for_scoring`, kickoffs only) | `{"VALID_PROSPECTIVE": 45}`, `freeze_check: APPLIED`, `not_run_games: []` |
| target-week label-independence of predictions | asserted (two opposite fabricated label fills → identical p_home bits) |
| as-of input assembly at `recorded_at` | 0 target-week games in inputs; inputs == synthetic prior stream |

## 5. REAL prediction-ledger path absence (task 3 final requirement)

The ported tool has **no default path constant** (every ledger path is an explicit argument;
PORT_NOTES.md §3.1), so absence was asserted over every location the tool's §1 filename law or
the README usage example could resolve to:

```
$ ls -la research/control/NFL-WINPROB-NG-SCORED-V1/ledger/
__pycache__  nfl_ng_ledger.py  README.md  test_ledger_synthetic.py     # NO *.jsonl
$ find <worktree> \( -name "prediction_ledger*.jsonl" -o -name "predictions_*.jsonl" \)
(none)                                                                  # zero hits worktree-wide
$ ls -la ~/.my-quantitative-data/nfl-ng-scored-v1/
provenance  raw_pbp_2000_2017  raw_schedules_fresh  rights  sandbox  selection   # NO ledger at root
$ ls -la ~/.my-quantitative-data/nfl-ng-scored-v1/sandbox/
dryrun_evidence.json
predictions_NFL-WINPROB-NG-SCORED-V1-SANDBOX_2030.jsonl                 # SANDBOX ledger (synthetic only)
predictions_NFL-WINPROB-NG-SCORED-V1-SANDBOX_2030.jsonl.genesis.json
```

Paths explicitly checked and confirmed ABSENT by the dry-run (it exits with an INCIDENT error
and deletes nothing if any exists):
- `<worktree>/research/control/NFL-WINPROB-NG-SCORED-V1/ledger/prediction_ledger.jsonl`
- `<worktree>/research/control/NFL-WINPROB-NG-SCORED-V1/ledger/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl`
- `<worktree>/predictions` (README example root)
- `~/.my-quantitative-data/nfl-ng-scored-v1/predictions` and `…/prediction_ledger.jsonl`
- `~/.my-quantitative-data/nfl-ng-scored-v1/predictions_NFL-WINPROB-NG-SCORED-V1_2026.jsonl`

**The real prediction ledger does not exist.** The REAL GENESIS remains unwritten (owner-GO
law, FREEZE_PACKET.md §6); this lane wrote nothing outside
`lanes/S_SYNTH/**`, `research/control/NFL-WINPROB-NG-SCORED-V1/ledger/**` (the port),
`~/.my-quantitative-data/nfl-ng-scored-v1/sandbox/**`, and the handoff JSON.

## 6. Runtime note

`__pycache__` inside the ported ledger directory is a Python bytecode cache regenerated by
test runs; it was removed after the final verification pass and reappears harmlessly on any
re-run. Final ported-file sha256s re-verified unchanged after all runs (§1 values).
