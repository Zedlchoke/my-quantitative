# A7 DELTA-2 AUDIT — CRYPTO-V13 (V13R2)

**Verdict: `V13R2_LAUNCH_AUTHORIZED`** — 7/7 items PASS, 0 unresolved HIGH/CRITICAL.
Auditor A7, independent DELTA-2 audit (V12R2 precedent), 2026-09-04 ~17:45Z.
Scope: worktree `r-a7-delta2` @ `ecfaff5`, auditing `bcb2853..d072664` (W1R → W1R2).
Machine-recomputed throughout; audit artifacts only, no repair, no push, no merge.

## Context

W1R `bcb2853`: the first scored LIQEPIS invocation crashed **before any scored metric
existed** (`ContractViolation`: cross-fold holding for BOMEUSDT, established F0
2025-12-15, closed F1 2025-12-22) — TECHABORT, zero budget
(`research/control/v13_run/TECHABORT_liqepis_chain_attempt1.json`).
Remediation delta: `research/v13/families/liqepis/plugin.py` (+ new
`tests/test_v13r_liqepis_delta.py`) implementing **fold-terminal force-flat** — at the
fold-terminal decision stamp the plugin returns the FLAT book (the flat transition IS
the boundary action), with schedule-time fail-closed checks. Lane commit `f2aef59`,
integrated as W1R2 `d0726645`.

## Item results

**1. DELTA SCOPE — PASS.** `git diff bcb2853..d072664` = 8 files: science surface is
ONLY `families/liqepis/plugin.py`; plus the new delta test file and control-plane
records (prior A7 delta audit artifacts, TECHABORT forensic, event_log, state.json,
w13r_freeze.json). Hunk review: no identity/parameter/schedule/cost/fold-constant
change; the fold-terminal stamp set is derived purely from the frozen calendar +
frozen attribution (`fold_terminal_force_flat_stamps()` pins to exactly F0's
2025-12-15); every other effective stamp answers `compute_targets_at` unchanged;
fail-closed paths added, none removed. `w13_freeze.json` untouched.

**2. DIGESTS — PASS.** All 6 arm digests recomputed via
`arm_config_digest(frozen_identity(arm))` == module-recorded == `w13_freeze.json`
(OITD `9f121f3e`/`620ef97b`/`e3b02064`; LIQEPIS `d7af1b24`/`60280408`/`49ca153a`),
pairwise unique 6/6. Independently cross-checked by the driver preflight at the exec
tree (n_match 6/6).

**3. OITD CELLS VALIDITY — PASS.** `research/v13/families/oitd/**` and
`research/adapter_v10/**` are byte-identical between `bcb2853` and `d072664` (empty
diffs), so the 3 published OITD rows remain valid under W1R2 (BAB-under-W12R
precedent). Exec-tree shard ledger `results/v13_phase_e/ledger_oitd.jsonl` sha256 =
`4fa9f3516b36d640265eb98e73168b9b48f2cb919ccb5fc5c7f56ded83fef2b6`, exactly 3 rows
(OITD-28D / OITD-56D / CTL-FLOW-ONLY, producer head `bcb2853`, published 16:47:10Z),
cell summaries consistent.

**4. TESTS — PASS (ran myself, audit worktree at W1R2).** Delta 10; LIQEPIS 39;
OITD 77 (9+16+17+11+15+9; world file fixture-only); driver 35; fusion 227;
accounting 7. Observed: 52 + 116 + 227 all passed, zero failures.

**5. FIX MERIT — PASS.**
- *OITD precedent*: OITD's trailing purge strips exactly the fold-terminal stamps so
  no OITD book can OPEN at one (proven structurally by
  `test_oitd_boundary_handling_is_provably_in_fold`). LIQEPIS retains 2025-12-15 as an
  effective stamp, so the same invariant is restored by answering FLAT there, status
  OK — the frozen runner refuses `FORCE_FLAT` at an OPEN instant (runner.py:373) and
  owns the final-edge force-flat itself.
- *Runner boundary accounting*: a zero-leg flat target is a **liquidating** transition
  — closing fills are demanded for proposal ∪ current holdings, realised positions
  carry fill prices, liquidation cost attaches pro-rata to the closed legs, and the
  positions attribute to the boundary instant's fold (F0). F1 provably opens from an
  empty prior book.
- *Cannot silently drop legs*: the schedule-time check raises `ContractViolation`
  before the flat is offered unless EVERY universe symbol has an executable close fill
  landing strictly inside the owning fold (blanked-bars test proves the refusal). The
  real-snapshot sweep (3 arms × 6 cells through the runner boundary machinery) asserts
  the flat boundaries have **non-empty prior weights** (real held legs liquidated, not
  vanished), applied fills with latest `fill_bar_close_ns < fold_end_ns`, and an empty
  cross-fold tail: 18 cells, 15 fold-terminal flats, 18 final force-flats, all in-fold.
  In `drop_one_fold` F0 is fully carried, so the flat stamp is answered but never
  acted on — calendar-only derivation behaving correctly.

**6. TWINS — PASS.** Both `e-exec-1` and `r-reproduce` detached at `d0726645`,
porcelain 0 (re-checked after preflights). Canonical ledgers `e3b0c442` (empty seed)
in both. Staged manifests `f855ad9c` in both, 90 entries; 4 files spot-verified
against the a3 authority in both trees (8/8 OK); the driver verifier does the full
90/90. Preflight-only run once per family against the exec tree in place: exit 0 both
(`--family liqepis --arm LIQEPIS-28D` and `--family oitd --arm OITD-28D`, expect-head
`d0726645`), staged 90/90, digests 6/6; results listing 76 files before == after —
**no new artifacts**. Disclosure: the preflight rerun refreshes the gitignored
`liqepis/LIQEPIS-28D/preflight.json` evidence file in place (by-design preflight
evidence; no scored metric).

**7. BOUNDARIES — PASS.** Budget 3/9 consumed (3 published OITD cells; 3 LIQEPIS
cells remain planned; ILLIQ unused). Zero LIQEPIS metrics exist (`liqepis/` results
dir holds only preflight.json; `ledger_liqepis.jsonl` absent). S1 `SEALED_UNTOUCHED`.
Owned workers 0. Main untouched (branch `main` @ `50e0207`, owner's next-cycle plan,
pre-scoring; only pre-existing untracked `.v2c/` tool state). Clock: started 16:05Z,
~1h50m elapsed at audit — well within 12h.

## Findings

- **F1 (LOW, non-blocking)** — `state.json` budget/counters (updated 14:40Z) still
  show 0/9 and v13_published 0 despite the 3 published OITD cells. Authoritative
  records (shard ledger, cell summaries, TECHABORT forensic pin) are correct and
  mutually consistent; no overrun risk (plan caps at 6/9). Recommend A1 reconcile at
  the next control-plane update or terminal report.
- **F2 (OBSERVATION)** — the mandated preflight-only rerun refreshes the gitignored
  preflight evidence artifact in place; disclosed above.

## Verdict

All gates green, the delta is minimal, fail-closed, and digest-neutral, and the 3
published OITD cells carry over validly. **`V13R2_LAUNCH_AUTHORIZED`** — the LIQEPIS
chain retry (LIQEPIS-28D, LIQEPIS-56D, LIQEPIS-SIGN-INV; 3 cells, budget to 6/9) may
proceed under W1R2 `d0726645fd97ea6e5ae67e405e8720844d71338c`.
