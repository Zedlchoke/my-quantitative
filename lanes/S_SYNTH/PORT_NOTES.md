# PORT_NOTES — S_SYNTH lane, cycle NFL-WINPROB-NG-SCORED-V1

Port of the predecessor prediction-ledger tooling (cycle `NFL-WINPROB-NG-PREP-V1`,
lane E) into this cycle's control tree. Interpreter for every command:
`/Users/hoangminhlong/my-quantitative/.venv/bin/python`. No git commands used.

## 1. Files ported (BYTE-IDENTICAL, zero line changes)

Source (read-only): `.worktrees/nfl-winprob-ng-prep-v1/integration/research/control/NFL-WINPROB-NG-PREP-V1/ledger/`
Destination: `research/control/NFL-WINPROB-NG-SCORED-V1/ledger/` (this worktree)

| file | sha256 source (pre-port) | sha256 ported (post-copy) | verdict |
|---|---|---|---|
| `nfl_ng_ledger.py` | `6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c` | `6fb0a1d41b347c16162742ee2591090d576af7633fd1d86b641d444156a1219c` | BYTE-IDENTICAL |
| `test_ledger_synthetic.py` | `93d3e248ae7190710bc334a638ff41e7a8394a9ea0ce140789157663a105bc1d` | `93d3e248ae7190710bc334a638ff41e7a8394a9ea0ce140789157663a105bc1d` | BYTE-IDENTICAL |
| `README.md` | `d44e945f1d0c0ddd8271e08333fc4dbeb1d95314f6356b385c4f46dec5575256` | `d44e945f1d0c0ddd8271e08333fc4dbeb1d95314f6356b385c4f46dec5575256` | BYTE-IDENTICAL |

Method: plain `cp` (no editor pass), then `cmp` pairwise (silent) and `shasum -a 256`.
The post-port sha256s also equal the values pinned in
`lanes/F_FREEZE/freeze_digests.json → files.predecessor_sources` — the port reproduces
the file at exactly the sha256 the freeze packet demanded (FREEZE_PACKET.md §5: "The port
must reproduce the file at the sha256 above or disclose the delta" — delta: NONE).

Line-by-line adaptations: **NONE.** Zero bytes differ in any of the three files.

## 2. Predecessor suite on the ported copy

```
cd <worktree root>
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
  research/control/NFL-WINPROB-NG-SCORED-V1/ledger/test_ledger_synthetic.py -v
# 42 passed, exit code 0   (matches handoff_E.json "42/42 pass")
```

No STOP/TECHABORT condition triggered (a byte-identical port passed every test).

## 3. Usage-level decisions (NOT code changes — documented per dispatch)

1. **No default path constant exists in the tool.** `nfl_ng_ledger.py` takes every ledger
   path as an explicit function argument (`create_ledger(path, …)`, `append(path, …)`, …);
   there is no module-level default path to adapt. Consequently the "tool's configured
   real path" is: whatever path the caller passes. The only cycle-specific paths anywhere
   are (a) the §1 filename law pattern `predictions_<cycle_id>_<season>.jsonl` enforced by
   `create_ledger`, and (b) the README usage example
   `predictions/NFL-WINPROB-NG-SCORED-V1/predictions_<CYCLE>_2026.jsonl` (example text only,
   not executed by the module). Both resolved locations are enumerated and asserted absent
   in the dry-run (DRYRUN_REPORT.md §5).
2. **Dispatch-named sandbox file vs the tool's §1 filename law.** The dispatch names the
   sandbox artifact `~/.my-quantitative-data/nfl-ng-scored-v1/sandbox/prediction_ledger_sandbox.jsonl`.
   The ported tool (byte-identical, enforced by its own test
   `test_create_refuses_existing_and_filename_law`) refuses to create any ledger whose
   basename is not `predictions_<cycle_id>_<season>.jsonl`. Rather than modify the frozen
   tool (forbidden: prefer byte-identical), the sandbox ledger is created under the SAME
   directory with the tool-enforced name
   `predictions_NFL-WINPROB-NG-SCORED-V1-SANDBOX_2030.jsonl`
   (`cycle_id = "NFL-WINPROB-NG-SCORED-V1-SANDBOX"`, `season = 2030`). The dispatch-named
   path is intentionally NOT created as a second file/symlink so that exactly one
   validated ledger artifact exists in the sandbox. This is the only deviation from the
   dispatch text and it is a naming deviation only; the directory, content, tool and
   checks are exactly as specified.
3. **Sandbox GENESIS digest.** New digest
   `sha256_hex(canonical_json(<sandbox genesis descriptor>))` computed inside
   `sandbox_dryrun.py` from a descriptor that names the sandbox cycle/season/kind; the
   freeze GENESIS digest `ae99a803dfcc280e85d46bdc192a5b1a042320af127f688d66481ba3f1aaa3e7`
   appears in lane code ONLY inside inequality assertions (`sandbox != freeze`) and is
   never written into any sandbox row, sidecar, or ledger byte (asserted over the final
   file bytes).
4. **Synthetic-only inputs.** All dry-run game ids are `SYNTH_`-prefixed; team lineages are
   `SYN_T01…SYN_T30` (no real NFL lineage code); all kickoffs are in 2028–2030 (≥ 2027);
   ledger `season = 2030` (tool law ≥ 2026). No real games.csv / pbp file is read by any
   lane script; the T_SELECT frozen modules are exercised only on synthetic `GameSet`s
   constructed in-memory.
5. **Frozen code used as-frozen.** `lanes/T_SELECT/{arms.py,select.py}` are imported
   unmodified (sha256 asserted at runtime against the freeze-packet §9 values);
   `sandbox_dryrun.py` and `test_successor_synthetic.py` never write to `lanes/T_SELECT/**`.
6. **Determinism.** The sandbox genesis sidecar is written with an explicit synthetic
   `created_at_utc`; rows carry no wall-clock; every computation is deterministic — two
   full dry-run executions produce byte-identical ledger files (evidence in DRYRUN_REPORT.md).

## 4. Verification commands (all exit 0)

```
cmp <src>/nfl_ng_ledger.py        <dst>/nfl_ng_ledger.py        # silent → identical
cmp <src>/test_ledger_synthetic.py <dst>/test_ledger_synthetic.py
cmp <src>/README.md               <dst>/README.md
shasum -a 256 <dst>/{nfl_ng_ledger.py,test_ledger_synthetic.py,README.md}
/Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
  research/control/NFL-WINPROB-NG-SCORED-V1/ledger/test_ledger_synthetic.py -v   # 42 passed
```
