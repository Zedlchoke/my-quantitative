# A7 AUDIT REPORT — SYSTEM-HARDENING-V1 (H6, fresh context)

- Auditor: A7 fresh-context subagent, independent of A1 and of every lane.
- Date: 2026-09-08T13:13:16Z. Verdict: **SYSTEM_HARDENING_V1_PASS** (machine-readable twin:
  `A7_AUDIT_VERDICT.json`, schema `system_hardening_v1/a7_audit@1`).
- Position: audit worktree pristine at `orca/system-hardening-v1-audit` = SHV1_WAVE_SHA
  `eda97ab`, porcelain-clean before and after this audit. Nothing was repaired; two files
  written, both under `research/governance/shv1/audit/` per the frozen A7 ownership.

## 1. What was re-run and matched

Everything below was recomputed from bytes in this session — nothing was accepted from a
prior report.

- **H0 chain on main** (`89fbbdf` -> `cb8954f` -> `eda97ab`, plan commit `16555f2`): each
  commit touches exactly what it claims (projection byte-preserve; 6 pause/verification
  files; 1-line path correction). `.runtime/shv1_h0_gate.log` shows 14/14 PASS, exit 0.
  No commit exists on main after `eda97ab`.
- **H1 freeze** (`979b088`, correction `5250e8b`, disclosed amendment `e34a24a`):
  re-ran `h1_reproduce_inventory.py` from the integration worktree -> `GATE H1:
  0 mismatches -> exit 0`. The script is not vacuous: it recounts worktrees (56) and
  branches (324), re-hashes the 4 frozen files (projection `c3c822fb…`, three H0
  artifacts, ledger `63b2e44d…`), re-reads the three cycle-authority heads, and checks
  lane branch/ancestry/cleanliness — all matched live.
- **Lane ownership**: `git show --stat` on A2 `53d76e9` (8 files), A3 `e514140` (3 files),
  A4 `57033ad` (5 files): every path inside its frozen `allowed_paths`, parent of each =
  wave SHA `eda97ab`, zero touches of `research/control/**`, `plans/PLAN_*.md`,
  `plans/system_hardening_v1/PAUSE_*`, or any scientific artifact. Integration picks
  `a611465` -> `1e71194` -> `8ac27b6` have stats byte-identical to their lanes;
  `ff35283` adds only the H5 report.
- **Pre-existing 6 errors, proven by me**: on THIS pristine audit worktree at `eda97ab`:
  `.venv/bin/python -m pytest tests/test_v9_universe_audit.py -q` -> **14 passed, 6 errors**,
  the same 6 test names with the same `TypeError: 'NoneType' object is not a mapping` at
  `scripts/v9_universe_audit.py:567` as `.runtime/shv1_full_suite_integration.log`
  (1012 passed / 1 skipped / 6 errors, exit 1). The "PRE-EXISTING AT BASE" claim holds;
  no SHV1-caused failure exists in the full suite.
- **Targeted suite re-run** (integration worktree): `tests/test_atomic_io.py
  tests/test_cycle_registry.py tests/test_legacy_adapters.py tests/test_scheduler.py
  tests/test_dashboard_purity.py -q` -> **39 passed, 1 skipped**, exit 0 (the skip is the
  absent host lock-registry, truthful NOT_RUN). `git diff --check` clean.
- **Cycle authorities**: V17 worktree HEAD `41de5c9`, V8 `94e78f6`, V12 `5a9b42d` — all
  match the pause/close records, all `status --porcelain=v1` empty. Every frozen pin
  re-hashed MATCH: V17 5/5 (freeze v5 `1ca4fa3d`, extractor/reconcile self-pins, V16
  panels `5bb5016d` / `c5414767`); V8 5/5 (selection freeze `e5d8f7e4`, p3 invariants,
  proposal, d1/d2 verdicts) plus the 13 gitignored FRED raw files independently
  re-hashed 13/13 against `staged_vintaged_manifest.json`; V12 4/4 (panel_v9 `67591464`,
  cohort `6a95401f`, v10 timing `b1477ea3`, v10 revision `7110cbf0`).
- **Scientific neutrality**: budgets 0 used / 6 max and `s1: SEALED_UNTOUCHED` re-read
  from all three legacy states and the registry; ledger line "Program total: 233
  published / 236 observed logical, 0 survivors" present; zero SHV1 commits touch
  `research/control/**` on the integration branch; worktree/branch counts still exactly
  56 / 324; heavy lock 0-byte (FREE), zero live pytest/research processes; main checkout
  dirty only with the owner's `?? .zcode/` (preserved).
- **Pause-commit scope**: V17 `41de5c9` = event log +1 line, state +1 line
  (`hard_stop_reason`), status retained `ACTIVE_LIGHT` — exactly §4 form. V8 `94e78f6` =
  event log +1, state +3/−2 (`hard_stop_reason` plus a byte-level unicode re-encoding of
  two prior lines — objection OBJ-2 below; decoded content identical).

## 2. Negative tests designed and run by A7

- **(a) Truncated/malformed registry**: sandbox copies of `plans/CYCLE_REGISTRY.json`
  truncated to half / filled with broken JSON -> `cycle_registry.load` raises
  `ControlStateDrift` ("unparseable control state") in both cases; file bytes unchanged
  after the failed loads; the `researchctl._load_registry` path raises identically.
  Fail-closed, no self-repair.
- **(b) Resume must be dry-run**: `researchctl cycle resume CRYPTO-V17` (run twice)
  prints the sec10 DRY_RUN checklist and changes nothing — `git status --porcelain=v1`
  of the integration tree byte-identical before/after. Additional observation: the
  argparse parser defines no `--execute-live` flag at all, so CLI resume can never
  reach the write path (fail-closed by construction). No `--execute-live` was ever used.
- **(c) CAS violation**: `cycle_registry.save(..., expect_prev_sha='deadbeef'…)` ->
  raises `ControlStateDrift` ("CAS mismatch … concurrent writer"), file byte-identical;
  a correct-CAS save in the same sandbox succeeds (positive control). (An intermediate
  "file changed" reading was this auditor's own test bug — it truncated the file with
  `open(...,'wb')` before comparing — rerun correctly shows byte-identical.)
- **(d) Dashboard purity**: ran `dashboard_collect.py` once in the integration worktree:
  exit 0, snapshot lands in the gitignored `dashboard/` directory, `git status
  --porcelain=v1` identical before/after; the collector accepts `write_registry` but
  ignores it (sec7.5 compliance; the tracked projection stays byte-frozen).
- **(e) Taxonomy**: `classify_exception(TypeError("fromisoformat: argument must be str"))`
  -> `CODE_OR_SCHEMA_ERROR`, retryable=False, consumes_attempt=False, terminal=True;
  `LockBusyError("machine-wide heavy lock busy")` -> `RESOURCE_BUSY`,
  consumes_attempt=False. Matches the frozen sec7.4 taxonomy.

## 3. Adversarial findings (objections)

No HIGH or CRITICAL finding. Four LOW findings recorded in the verdict JSON:

1. **OBJ-1 (LOW)** — The canonical registry's FOREX-FREE-V8 record has empty
   `go_phrase` / `go_phrase_state` / `next_authorized_action`, while its linked pause
   packet declares the V8 GO phrase REGISTERED_NOT_CONSUMED and the I-implementation
   next action; V17's record similarly mirrors legacy `NOT_PRESENT` instead of the
   packet's `REGISTERED_NOT_CONSUMED`. Both inconsistencies are in the conservative
   direction (nothing claims consumed or live; sec10/P-8 already force a fresh owner GO
   at prelaunch) and the registry is a pre-adoption candidate until the owner merges —
   but reconcile `go_phrase_state` with the packets before adoption.
2. **OBJ-2 (LOW)** — V8 pause commit `94e78f6` re-encoded two prior `state.json` lines
   from JSON `\uXXXX` escapes to literal UTF-8 (`\u2014` → literal em-dash, `\u00a7` →
   literal section sign; decoded text identical, semantic no-op, verified in the diff)
   beyond the disclosed additive `hard_stop_reason`; the commit message says "additive"
   without disclosing the re-encoding. Event log stayed append-only; no scientific field
   moved.
3. **OBJ-3 (LOW)** — `plans/CYCLE_REGISTRY.events.jsonl` does not exist yet. No
   post-creation transition has occurred via researchctl (resume is dry-run-only), so
   sec7.3 is not violated (the git commit is the birth record), but the append-only
   event journal is unexercised in-tree; the first real write must create it.
4. **OBJ-4 (LOW, note)** — `.runtime/shv1_drafts/` contains `RESUME_*.{json,md}` for all
   three cycles. These are DRAFT pre-decision artifacts, not gate evidence; no gate
   credit was taken from them. Existence recorded per audit instructions.

Specifically hunted and NOT found: two writable sources of truth (single registry writer
via CAS; collector ignores `write_registry`; projection hash byte-frozen since
`89fbbdf`); budget/S1 change (0/6 + SEALED in all three, re-read from bytes);
scientific hash drift (all pins re-hashed MATCH); worktree/branch drift (56/324 =
freeze); SHV1 edits to cycle state beyond §4 form (V17 exact; V8 exact plus OBJ-2);
a wrongly-live GO phrase (V17/V8 unconsumed per packets, V12 DEAD in the registry);
`git add -A` sweep in any SHV1 commit (all stats are narrow pathscope sets; no commits
on main after `eda97ab`).

## 4. Gates

G0 PASS, G1 PASS, G2 PASS, G3 PASS, G4 PASS, G5 PASS, G6 PASS, G7 PASS, G8 PASS —
per-gate evidence lines are in `A7_AUDIT_VERDICT.json#gates`. Nothing was NOT_RUN: every
mandatory check in the audit brief executed in this session.

## 5. Verdict and resume posture

**SYSTEM_HARDENING_V1_PASS** per PLAN §8 H6 / §9 G8: all gates G0–G8 carry evidence
reproduced in this session and zero HIGH/CRITICAL objections remain. Per PLAN §10 the
resume recommendation order is Forex V8 (selection frozen — implementation next, fresh
owner GO required), Stocks V12 (out of SHV1 scope: TERMINAL, reopen belongs to the
stocks authority after the `fromisoformat` bug is fixed there), Crypto V17 (resume-
eligible after owner GO + lock recheck). No GO phrase carries across this pause; no
scored cell, no S1 access, and no budget change occurred anywhere in SHV1.
