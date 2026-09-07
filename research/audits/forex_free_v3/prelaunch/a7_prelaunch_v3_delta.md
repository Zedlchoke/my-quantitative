# FOREX-FREE-V3 — A7 Prelaunch DELTA Re-Audit (second pass, V3-Q)

- Audited: 2026-09-04T20:03:10Z (machine_date_u)
- Auditor: A7 independent delta re-audit (audit artifacts only; zero repairs)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/q-a7-prelaunch2`
- Branch: `orca/forex-free-v3-q-a7-prelaunch2` — HEAD `067d4b4`, porcelain empty at start
- Audited freeze: `FOREX_FREE_V3_W3B` = `2d4c88339790c0406bedc35a6c0b8258a58806b2` (ancestor of HEAD; verified)
- Fix commit under review: `df3da17` ("I-GATES-FIX": H1/H2/H3/M1)
- Pass-1 audit: `research/audits/forex_free_v3/prelaunch/a7_prelaunch_v3.json` (75fba7d, S0_LAUNCH_BLOCKED)

## Method

Frozen sources read line-by-line against `baseline_invariants.json`, `PLAN_forex_v3.md` section 12 and **both binding proposals**. All hashes recomputed from bytes in **both twin trees**. The 6-arm dummy dry-run **re-executed independently** in this auditor tree against the e-exec-1 twin data (`freeze_token=None`), then recursively scanned for leaks. `df3da17` diff reviewed hunk-by-hunk. Test suite re-run by the auditor.

## Per-check results

| Check | Verdict |
|---|---|
| C1 pin/twin integrity (HEAD/branch/porcelain; twins detached at W3B, clean) | PASS |
| C2 data+code chain (price 156/156 + macro 9/9 + code_hashes 7/7 vs `w3_freeze.json`, in BOTH twins) | PASS |
| C3 independent 6-arm dry-run (determinism vs freeze + recursive zero-leak scan) | PASS |
| C4 delta gate review (H1/H2/H3 mechanics, M1 ruling, regression sweep) | PASS WITH FINDINGS |
| C5 ledger/budget hygiene (budget 0/6, no V3 scored ledger anywhere) | PASS |
| C6 tests (`pytest tests/assets/forex_free_v3 -q`) | PASS — 89 passed, 2 skipped in 42.9s |

### Delta fix verification

- **H1 mechanics — verified.** `compute_cell` refuses `benchmark_treatment` as a scored cell (`BENCHMARK_TREATMENT_IS_NOT_A_SCORED_CELL`); the scored anchor books the benchmark through the **same** `book_trades -> accounting.book_dual(cost_tier=1.0)` kernel, under the same fail-closed decision validation and session gate; `incremental_alpha` is always a finite number on a scored anchor record and `INCREMENTAL_ALPHA_NOT_POSITIVE` fires on `<= 0`; `BENCHMARK_BOOK_EMPTY` fails closed; a family without the arm fails the scored anchor via its own unknown-arm refusal. **Benchmark arms are rule-verbatim vs the frozen proposals**: family1 = unconditional 21-bar momentum, zero macro reads in the state (test pins the reader is never consulted); family2 = anchor law with the `+270d` as-of lag (`BENCHMARK_LAG_DAYS = 270`), financing accruing at true day-start differentials.
  - **Residual finding D1 (HIGH)** on the alpha *formula* for family1 — below.
- **H2 — verified.** The frozen D1 equal-weight USD index is built inside the runner from the authorized 7-pair H1 snapshot only (16:00-NY daily steps; XXX/USD `-r`, USD/XXX `+r`; equal-weight mean keyed by the later bar's UTC date). Family meta series is never consulted. It feeds the **unchanged** `|corr| <= 0.30` gate over `>= 60` days with trades. Fail-closed: scored run with booked trades and no price source raises `USD_INDEX_SOURCE_MISSING`; a present-but-broken source raises `BLOCKED_DATA`; dry-run never builds the index (no leak). Hand-computed 2-pair golden test pins the signed legs, weekend single-step and source-key priority.
- **H3 — verified.** `dry_run_sanitized` zeroes/placeholders every booked monetary metric on every dummy record, including the stress tiers and `break_even_cost_bps` that constituted the measured pass-1 leak. **Independent rerun (auditor tree, twin data): all 6 record_ids pairwise unique and exactly equal to `w3_freeze.json six_arm_dummy_dry_run`; n_decisions 6/6 equal (312/302/154/138/344/145); recursive scan found ZERO nonzero floats other than `cost_tier=1.0` and integer counts; `scored=real_pnl=published=False`, `dry_run=True` everywhere.** Determinism across trees confirmed.
- **M1 — implemented, deviation ruled.** Suite = 7 drop-one-PAIR + 1 drop-one-BEST-fold = 8 scenarios; survival = reduced-book financing-adjusted expectancy `> 0`; unevaluable fold scenario fails closed; gate counts survivals against the unchanged floor 5. Ruling below.

### Regression sweep (df3da17)

No frozen gate constant changed. Anchor/neighbour/control decision semantics untouched — the only behavioral deltas are the four declared fixes. No nondeterminism introduced (fixed iteration orders, sorted keys, `fsum`/`round` at defined points, deterministic `max()` tie-break, no wall clock or randomness).

## M1 ruling (5-of-8 vs frozen 5-of-7)

**Ruled WEAKER — HIGH, resolved conditionally per A1's recorded precommitment.** The new gate's pass set is a strict superset of the frozen 5-of-7 gate: any book with >= 5 pair-drop survivals still passes (the fold scenario only adds survivals), and books with exactly 4 pair survivals that survive the best-fold drop now pass where the frozen gate failed them. Tolerated scenario failures rise from 2 to 3; survival ratio falls from 71.4% to 62.5%. The added scenario is genuinely harder on fold-concentrated books, but that does not restore the frozen failure tolerance.

**Required tightening:** 6-of-8 minimum must **bind before any scored run** (restores `<= 2` tolerated failures). Since D1 already forces a re-freeze delta, `DROPOUT_SURVIVAL_MIN 5 -> 6` should ride that same delta (preferred, verifiable); alternatively an owner-recorded, verifiable control-plane override checked by the next audit.

## New finding D1 (HIGH — the launch blocker)

**The family1 incremental-alpha Stage-A gate is evaluated on a formula the binding A5 proposal explicitly froze OUT of the gate.**

- `a5_lane/proposal_1.json` `incremental_test.operationalization` freezes: *overall incremental alpha := (full-sample sum of the anchor's after-cost financing-adjusted per-pair-day PnL) − (same for the benchmark), both normalized per pair-day of the identical post-warmup schedule window … Gate: > 0. **The per-trade expectancy difference (anchor − benchmark) is reported alongside as a diagnostic, not the gate.***
- `scored_runner.py` computes exactly the per-trade expectancy difference and `stage_a_gates` fires `INCREMENTAL_ALPHA_NOT_POSITIVE` on it. No code path evaluates the A5 per-pair-day formula.
- family2 is unaffected: the A6 proposal freezes the expectancy difference as its gate — the implementation matches A6 verbatim.
- `i_gates_fix.json` documents the formula but records no deviation against the A5 operationalization; the freeze delta_notes are silent.

**Impact:** the cycle's central incremental test for family1 is evaluated on a non-frozen quantity. Per-trade and per-pair-day normalizations can differ in sign (the anchor trades a subset of the benchmark's active days; A5 froze per-pair-day normalization for exposure fairness), so a family1 verdict under the implemented gate can contradict its own frozen gate in either direction — a false Stage-A survivor or a false reject. Pre-scoring, so fixable at zero outcome cost.

**Remediation (either, before any scored run):** (a) implement the A5 operationalization for `family1:anchor` inside `compute_cell` (pair-day normalized difference over the identical post-warmup schedule window; keep the per-trade difference as the proposal's diagnostic) → code delta, all seven code_hashes re-frozen, delta re-audit; or (b) owner-recorded deviation waiver formally superseding the A5 operationalization text.

## Other findings

- **I1 (INFO):** fold-drop coverage is one scenario (best fold), not the proposals' all-3-fold recomputes; with unequal fold trade counts the best-expectancy fold is not always the most damaging removal. Settle in the D1 remediation (extend to all 3, or record).
- **I2 (INFO):** `stage_a_gates` legacy fallback gates pair-only scenarios for records lacking `dropout_scenarios`; unreachable in the published pipeline. Accepted.
- **L1 (LOW, carried):** per-arm timeout cannot kill a hung worker thread — unchanged accepted wart, not a delta regression.

## Verdict

**FOREX_FREE_V3_S0_LAUNCH_BLOCKED** — blockers: **[D1]** (M1-DEV resolved conditionally via the recorded precommitment; not a blocker once 6/8 binds).

What is solid: twin pins at W3B, byte-identity of 156 price + 9 macro digests and 7/7 W3B code hashes in both twins, commit chain, budget 0/6, empty V3 ledger authority, the H2 in-runner USD index, the H3 sanitizer with a clean independent cross-tree dry-run, and the test suite. The remaining blocker is confined to one gate formula in `compute_cell`.

Conditions bound on any future AUTHORIZED: (1) D1 resolved via code fix (+ re-freeze + delta re-audit) or recorded owner waiver; (2) 6-of-8 dropout floor binding before the first scored cell; (3) I1 settled. Phase E must not start until a subsequent A7 delta audit returns AUTHORIZED and the owner types the release phrase.
