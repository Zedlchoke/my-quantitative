# A7 ROUND-3 PRE-OUTCOME AUDIT — REGIME-STRATEGY-MAPPING-V1

**Auditor:** A7-R3, fresh context (no involvement in the round-1/round-2 audits
or their remediations). **Date:** 2026-09-23. **Base:** 102ed500
(`orca/rsmv1-a7r3-preoutcome`; `git rev-parse HEAD` verified
`102ed5000fbc1f6ac4f1f2eb1aeeb27e7de31f97` before any work; tree clean).
**Scope:** verify the R2 remediations (N1–N4) rigorously, re-verify the
highest-risk invariants without trusting prior rounds, and hunt for anything
the remediation broke. Machine re-runs executed by this auditor: full test
suite, engine equivalence, timeline rebuild, sanitized dry-run (regenerated,
then compared to HEAD), GO-quarantine refusal + `--check` + independent GO-phrase
sha recompute, all freeze/manifest/wrapper/amendment digest recomputation, V2
artifact-pin recomputation, and two auditor-authored refutation/probe scripts
(`/tmp/a7r3_audit/refute_n1.py`, `/tmp/a7r3_audit/probe_n2.py`; nothing written
into the repo). Nothing was repaired.

# VERDICT: `AUTHORIZED_FOR_DISCOVERY_STOP`

All four R2 findings are remediated: N1 (HIGH, the only finding that ever
blocked) is **FIXED and verified by an auditor-authored refutation against the
real census**; N3/N4 are **FIXED**; N2 is **fixed in letter** (real selections
now occur and are asserted invariant) but **residual detection weakness**
remains — recorded as N5 (MEDIUM, new finding below). Zero unresolved
HIGH/CRITICAL → authorized under the stated verdict rule. The two LOW items
and one INFO are recorded with pre-STOP-1 recommendations that do not gate
authorization.

---

## R2 remediation verification

### N1 (HIGH — fold off-by-one): FIXED, refuted-and-survived — CLOSED

- `rsmv1/selection.py::select_for_fold` now fires the empty-inner gate at
  `fold_id == 0` ONLY (diff in 47da824a is exactly this hunk + comment); the
  scored caller `arm_c_selection` iterates `for fid in range(4)` (0-based),
  inner window `0 <= _start_fold(ctx, e) < fid`, `inner_fold_count=max(0,fid)`
  — fid 0 is the law's fold 1, fid 1 pools fold 0 = law's folds 1..k−1.
- **Auditor refutation** (/tmp/a7r3_audit/refute_n1.py; auditor-authored ctx,
  NOT the repo fixtures; REAL census via the real `measure_cell_census`,
  monkeypatched in and restored around the real `arm_c_selection`): with
  floor-passing pools (≥5 episodes / ≥150 decisions),
  - fid 0 → `FLAT, fold1_empty_inner_default` (ACCUMULATION, UPTREND);
  - **fid 1 → `ACC-BASE-RECLAIM-L, single_eligible_specialist` and
    `UPT-DIPBUY-L, inner_net_higher_stable`** — a specialist IS selected at
    the law's fold 2, exactly what N1 said was wrongly suppressed;
  - fid 2/3 follow the frozen stability rule (`need = |S|` for ≤2 inner
    folds, `ceil(2|S|/3)` for 3 — matches the freeze's required_wins table);
  - DISTRIBUTION (REAL census THIN) → `OUTER_FLOOR_THIN` in all 4 folds.
- **No other fold-index confusion exists:** grep of every `fid`/`fold_id`
  use in `scored.py`, `selection.py`, `census.py`, `feasibility.py` — all
  are 0-based array indices into `fold_contract.cells.<cell>.folds`;
  `folds_exec`/`fold_of_exec`/`mapping_by_fold` keys (0..3) are mutually
  consistent; census `per_fold` keys "0".."3" internal-consistent (OUTER
  floors are per-fold and fold-label-agnostic). The ONLY place the frozen
  law's 1-based numbering (k ∈ {1,2,3,4}) touches semantics is the fold-1
  empty-inner rule, now correctly at `fid == 0`. Unit fixtures
  (`test_turnover_selection.py`) were updated to 0-based ids in the same
  commit (fid 0 = law's fold 1; fid 1 must NOT hit the gate).
- Arm F's anchor mapping is rebuilt from `sel_audit` rows (same 0-based
  keys) — consistent.

### N2 (MEDIUM — vacuous leak test): FIXED IN LETTER; residual detection gap → N5

The shipped `test_selection_invariance_nonvacuous` now: uses floor-passing
episodes so REAL selections occur (audit rows are
`single/inner_net_higher_stable`, not wall-to-wall FLAT); mutates outer-fold
evidence and asserts every `(selected, reason)` pair identical; and carries a
deliberately leaky selector with an explicit vacuity tripwire. The invariance
half is genuinely non-vacuous in R2's sense. **However** (see N5): the
fixture's mutation cannot flip the two-candidate race under ANY pooling rule,
and the leaky-sensitivity proof passes via stub-reason artifacts, so the test
still cannot detect the leak class the freeze's `no_peeking_law` names.

### N3 (LOW — real-census thin-routing test): FIXED — CLOSED

`test_real_census_btc_h4_all_thin` calls the REAL
`measure_cell_census(cd, "BTC_H4")` (no stubbed verdicts; self-verifying
timeline rebuild inside), overrides `ctx.cell="BTC_H4"`, and asserts every
regime FLAT in every fold with `OUTER_FLOOR_THIN`. The stub/real interplay is
clean: the census monkeypatch is set inside a `try` and restored in `finally`
(function-local import inside `arm_c_selection` sees the patch); the full
suite passes with no cross-test pollution.

### N4 (LOW — stale dry-run artifact): FIXED — CLOSED

Auditor re-ran `tools/cmd_dryrun.py` at HEAD: `all_pass: True`, exit 0; the
regenerated `evidence/dryrun_sanitized.json` is **byte-identical** to the
committed one (`git status` clean after the run; `config_digest`
`5de75dbd…` = the value R2 said a HEAD re-run would produce). Artifact scan
at all depths: the only PnL-like key is the boolean `pnl_anywhere: false`;
`denominator_delta: 0`; 11 checks all PASS including
`identities_pairwise_distinct n=21`; `selection_executed: false` on every
cell; arm C marked `wired_NOT_EXECUTED`.

---

## NEW FINDINGS (this round)

### N5 — MEDIUM — The mandated leak test still cannot detect the leak class it exists for (residual N2)

- **Probe evidence** (/tmp/a7r3_audit/probe_n2.py, on the test's own fixture):
  1. The mutation (`fold 2 → −1e6`, `fold 3 → +1e6`) is applied to BOTH
     candidates through `_evidence`'s fixed `v − 50` construction, so the
     candidate pairwise gap is +50 in EVERY fold. No pooled statistic — clean
     (`f < fid`) or leaky (`f <= fid`) — can flip the winner on either
     `clean_ev` or `mut_ev`. The invariance assertion therefore holds
     trivially, not because the `f < fid` filter is load-bearing.
  2. A **faithful leaky re-implementation of the real selector** (copy of
     `arm_c_selection` with `f <= fid`) produces **byte-identical
     `(selected, reason)` on ALL rows** for both evidence variants — i.e. if
     `scored.py:387` regressed to `f <= fid`, NO assertion in the file fails
     (checked every test: the OUTER-gated tests are leak-proof by the census
     gate; the fid-0/fid-1 test's evidence also cannot flip).
  3. The shipped "sensitivity proof" (`CLEAN != LEAKY` assertion) passes for
     the wrong reason: the test's `leaky_selection` stubs the 3 non-UPTREND
     regimes with `reason: "stub"` vs the real path's computed reasons
     (`inner_floor_failure`). **0 of the UPTREND race rows differ** between
     clean and leaky. The code comment "a selector that pools the OUTER fold
     … would flip fold 2's choice" is false on its own fixture.
- **For:** the letter of the `no_peeking_law` mandate ("selection invariance
  under outer-fold data mutation … mandatory") is satisfied; real selections
  execute; a grossly broken selector combined with an asymmetric fixture
  would trip.
- **Against:** the exact regression the law targets — outer-fold data entering
  a selection statistic (`f < fid` → `f <= fid`) — survives the whole file.
- **Mitigation already verified independently:** containment is by
  construction and code-read: `scored.py:387` `f < fid` is the ONLY
  fold-window expression; the auditor's N1 refutation additionally exercised
  the fold-window semantics against the law with the real census.
- **Severity rationale:** strictly stronger than R1-F3/R2-N2 (both graded
  MEDIUM); test-quality defect, no correctness or data impact → MEDIUM.
  **Recommendation (non-blocking, ideally pre-scored-run):** rebuild the
  fixture so pooling fold `fid` flips the winner (R2's race_fixture.py proved
  constructible: near-tied inner folds + outer-fold net that reverses the
  sign), mutate exactly that outer fold, and keep the leaky-variant proof
  computed from the SAME regime rows (no stubs).

### N6 — LOW — Emitted selection reason codes deviate from the frozen reason-code vocabulary

- Freeze `rsmv1_selection_freeze.proposal.json` `reason_code_vocabulary`
  (11 codes; pinned on the FREEZE side by
  `test_freeze_proposals.py::test_selection_reason_codes_exhaustive_and_procedure_ordered`):
  `FIXED_FLAT_UNK, OUTER_FLOOR_THIN, FOLD1_NO_INNER, ASSET_INELIGIBLE,
  INNER_FLOOR_FAIL, SINGLE_ELIGIBLE, POOLED_WIN_STABLE, TIE_BREAK_BTC_SHORT,
  TIE_BREAK_FLAT, STABILITY_NO_COMPARATIVE_FOLDS, STABILITY_FAIL`.
- Code emits: `fold1_empty_inner_default, inner_floor_failure,
  single_eligible_specialist, inner_net_higher_stable,
  inner_evidence_unstable, exact_tie_tiebreak,
  no_asset_eligible_specialist, OUTER_FLOOR_THIN`. Only `OUTER_FLOOR_THIN`
  matches; there is no bridge test. R2's required remediation explicitly
  asked for `FOLD1_NO_INNER` at k=1; the outcome (FLAT) and rule ORDER match
  the freeze, but the arm C audit trail will carry codes outside the frozen
  vocabulary, and the tie-break recording law ("recorded with the delta and
  the class of both candidates") is not implemented (`exact_tie_tiebreak`
  records neither), and UNK (rule R_UNKNOWN → `FIXED_FLAT_UNK`) produces no
  audit row at all (applied silently via `base_map`). LOW: attestation-grade
  identity defect, no semantic effect. Fix by renaming the emitted strings to
  the frozen codes (code catching up to the freeze, no freeze change) or a
  disclosed freeze amendment.

### N7 — INFO — Pair-stability comparative-fold set uses fold-net presence, not episode presence

- Freeze: `comparative_folds_S` = inner folds where BOTH candidates have
  ≥1 episode in R. Code: `folds_both = [f for f in a.inner_fold_nets if f in
  b.inner_fold_nets]`, and `arm_c_inner_evidence` populates `fold_nets` for
  ALL folds (0.0 where the specialist has no R-window) — so S = all inner
  folds always. On this census every passing BTC_H1 regime has ≥3 episodes in
  every fold, so the two definitions coincide — **zero effect on this data**.
  In principle the deviation can go both directions (stricter: zero-fold
  inflates `need`; more permissive: an unopposed positive fold counts as a
  win). Record-only for the terminal analyst.

### N8 — INFO — Remediation commit message miscounts tests

- 47da824a message says "122 tests green"; the suite at that commit (identical
  to HEAD for all code/test paths — verified by `git diff 47da824a..HEAD` over
  `tests_py/ tools/ rsmv1/ freezes/ evidence/` = empty) is
  **119 passed + 1 xfailed**, exactly the mandated count. Message miscount
  only; artifact of record is this audit's re-run.

### Carried (unchanged from R2, still open, LOW) — F1b inner eligible-decision counter

- `scored.py:381` still counts `sum(length for episodes with length >= 6)`
  vs the freeze's `eligible_decision = in-episode bar with offset ≥
  buffer_k+1 = 2`. R2 recomputed BOTH definitions for every (cell, regime,
  fold): no floor pass/fail flips; with the OUTER gate first, every affected
  regime is census-THIN anyway. R2 accepted either code-fix or disclosed
  amendment pre-outcome; neither was applied. Still LOW, zero material
  effect, non-blocking; fold into any next code touch.

---

## High-risk invariants re-verified (not trusted from prior rounds)

| # | Item | Verdict | Evidence |
|---|---|---|---|
| 1 | Worktree/branch/HEAD | PASS | 102ed500… on `orca/rsmv1-a7r3-preoutcome`, clean at start |
| 2 | Engine equivalence | PASS | `cmd_equivalence.py`: BTC_H1/BTC_H4/SPY_D1 MATCH, `all_match: True`, exit 0; tree clean after (deterministic rewrite) |
| 3 | Timeline rebuild self-verification | PASS | `run_diagnostics.py timeline`: switches 90/31/34 OK, exit 0 |
| 4 | B-gate ordering | PASS | `scored.py:655` `_assert_b_equivalence(ctx, res_b1)` immediately after arm B (5 totals fields <1e-6 + trade count), BEFORE `arm_c` at :658 and before any arm C/tier sweep; failure raises "abort before any C outcome" |
| 5 | GO quarantine | PASS | no `SCORED_GO.json`; `cmd_scored.py` → `REFUSED_BACKTEST_QUARANTINE`, exit **20**; `--check` expected sha `47ee5e6f2bde5957149db8e8b0381ff0f3d6ffa7529fe6d4474c62f2bfb2c70c` == auditor recompute of sha256("GO REGIME STRATEGY MAPPING V1 DISCOVERY BACKTEST") no-newline |
| 6 | Freeze digests | PASS | decision-cache manifest 7/7 recompute (all 64-hex); `rsmv1_freeze_manifest.json` 5/5; wrapper `parameter_source_of_truth.sha256` 4/4 match proposal bytes; proposal `self_sha256` 4/4 recompute (selection/turnover/evaluation/arms; canonical-JSON-minus-field) |
| 7 | Arms amendment A7-R1-F2 | PASS | `amendments[0]` by A1 disclosed; `new_value` == frozen arms `input_pins.decision_cache_manifest.sha256` == on-disk manifest digest (`0187bdf2…`) |
| 8 | V2 worktree untouched | PASS | `0c277a94ba2831636cde423d51fd9251ed487bfd` on `orca/jev-regime-router-v2-integration`, `status --porcelain` empty |
| 9 | V2 tier_1 pins | PASS | 3/3: trades 978/1060/343 == pins AND artifact sha256 recompute == pins (`11c9ecda…`, `ba172a8b…`, `5e0b754f…`) |
| 10 | runtime/scored absent | PASS | `runtime/` holds only the 3 frozen timeline JSONs |
| 11 | Registry state | PASS | lifecycle PLANNED_NOT_STARTED; budget 0/21; S1 SEALED_UNTOUCHED; go REGISTERED_NOT_CONSUMED; workers 0; active_heavy false |
| 12 | Specialists verbatim | PASS | every parameter of ACC-BASE-RECLAIM-L, UPT-BREAKOUT-L, DNT-RALLY-SOLD-S vs the A4 proposal: entries (low<LL20≤close<SM20; close>HH20; EMA20<EMA50 ∧ high≥EMA20 ∧ close<EMA20), windows (LL/HH 20, exit LL/HH 10, SMA20=BOLL-mid, ATR14 Wilder), stops (structural `min(low,LL20)[signal] − 0.5·ATR14[signal]`; 3.0·ATR14 entry-anchored), max-hold (24 regime bars ACC/DNT-RALLY; fold-force-flat BREAKOUT), min-hold 6, sizing 1.0, BTC-only shorts via `-S` SPY filter |
| 13 | Turnover caps | PASS | `V2_JEV_TRADE_PINS = {BTC_H1:978, BTC_H4:1060, SPY_D1:343}` (scored.py:68) == V2 stored totals == arms freeze pins |
| 14 | Contamination ceiling | PASS | `DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION` + `promotion_ban` + `successor_law` in the frozen evaluation proposal; same ceiling in `run_all` disclosure |
| 15 | Full test suite | PASS | **119 passed + 1 xfailed in 9.57s** (exactly mandated; xfail = A5-F1 BUY_HOLD, ACCEPTED) |
| 16 | Sanitized dry-run | PASS | all_pass, exit 0, no PnL at any depth, 21 identities distinct, selection NOT executed; committed artifact byte-fresh at HEAD (N4) |

## New-breakage sweep (R2 remediation side effects)

- **Census stub vs real interplay:** clean — `arm_c_selection` imports
  `measure_cell_census` inside the function body, tests patch the census
  module attribute and restore in `finally`; suite passes with no pollution.
- **Arm D/E thin-gating:** correctly absent — `arm_d` (fixed base/FLAT map)
  and `arm_e` (deterministic ∧ JEV-veto) contain no census or thin
  references; the gate applies only to candidate arm C.
- **Selection audit rows at scored time:** arm C `_persist` extra carries
  `selection_audit` (incl. `OUTER_FLOOR_THIN` rows for every fold of every
  census-thin regime), `routing_report` (with the hard
  `unnecessary_close_reopen` counter raising on ≠0), and the
  `turnover_rejection_law` block. Base-tier selection feeds all tiers
  (`arm_c_inner_evidence` always at 1.0); the persisted `sel_audit` is the
  tier-independent audit.
- **N1 fix blast radius:** remediation commit 47da824a touches only
  `selection.py` (the one gate hunk), the two test files, and the dry-run
  artifact — no other production path changed since 5e72f368.

## Evidence log (round-3 commands + results)

1. `git rev-parse HEAD` → 102ed5000fbc1f6ac4f1f2eb1aeeb27e7de31f97; branch
   `orca/rsmv1-a7r3-preoutcome`; clean.
2. `/tmp/a7r3_audit/refute_n1.py` → ALL REFUTATION CHECKS PASSED (exit 0):
   real census verdicts {ACC PASS, UP PASS, DIST THIN, DOWN PASS}; fid 0
   gate; fid 1 selects (`single_eligible_specialist` / `inner_net_higher_stable`)
   with floor-passing pools; fid 2/3 stability per freeze table; DIST
   OUTER_FLOOR_THIN ×4.
3. `/tmp/a7r3_audit/probe_n2.py` → invariance assertion holds with real
   selections; faithful leaky selector (f≤fid) is row-identical on both
   evidence variants (leak undetectable); UPTREND rows clean-vs-leaky
   differ on 0 rows (sensitivity proof passes via stubs).
4. `pytest tests_py -q` → 119 passed, 1 xfailed in 9.57s.
5. `cmd_equivalence.py` → MATCH ×3, all_match True, exit 0; `run_diagnostics.py
   timeline` → 90/31/34 OK, exit 0; tree clean after both.
6. `cmd_dryrun.py` → all_pass True, exit 0; regenerated artifact == HEAD
   byte-for-byte; pnl scan: only `pnl_anywhere: false`; 11/11 checks PASS;
   identities n=21 distinct.
7. `cmd_scored.py` → REFUSED_BACKTEST_QUARANTINE exit 20; `--check` sha ==
   auditor recompute `47ee5e6f…`.
8. Digest battery: 7/7 decision-cache; 5/5 freeze-manifest; 4/4 wrapper pins;
   4/4 self_sha256; amendment new_value == arms pin == on-disk manifest.
9. V2 worktree 0c277a94 clean; V2 tier_1 3/3 pins (trades + sha).
10. Registry: PLANNED_NOT_STARTED, 0/21, S1 SEALED_UNTOUCHED, go
    REGISTERED_NOT_CONSUMED, workers 0.
11. `runtime/scored` absent.

## Verdict statement

`AUTHORIZED_FOR_DISCOVERY_STOP` — zero unresolved HIGH/CRITICAL. N1 is fixed
and independently proven against the real census; N3/N4 are fixed; N2's test
is non-vacuous in execution but not yet leak-detective (N5, MEDIUM,
non-blocking under the verdict rule; containment verified by construction and
auditor code-read). N6/N7/N8 and the carried F1b are LOW/INFO record items.
Standard post-audit warning that binds the scored run itself: no mapping,
threshold, or selection-code edits after PnL is visible (plan §10.3) — any
code touch from this point requires a fresh pre-outcome pass.
