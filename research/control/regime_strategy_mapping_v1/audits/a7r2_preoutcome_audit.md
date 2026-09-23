# A7 ROUND-2 PRE-OUTCOME AUDIT — REGIME-STRATEGY-MAPPING-V1

**Auditor:** A7-R2, fresh context (no involvement in the round-1 audit or its
remediation). **Date:** 2026-09-23. **Base:** 5e72f368
(`orca/rsmv1-a7r2-preoutcome`, tree clean at start; verified with
`git rev-parse HEAD` before any work).
**Scope:** verify the A1 remediation of round-1 findings F1/F2/F3 is CORRECT
and COMPLETE, re-run the full 18-item pre-outcome checklist, and actively
attempt refutation — especially of anything the remediation may have broken.
Machine re-runs executed by the auditor: full test suite, engine equivalence,
sanitized dry-run, timeline rebuild, GO-quarantine refusal + `--check`,
all freeze/manifest/proposal digest recomputation, an independent census
recomputation from the timeline bytes (auditor's own segmentation/fold/floor
code), and four in-process refutation scripts (all in /tmp, none in the
repo). Nothing was repaired; the one artifact my dry-run re-run refreshed was
restored to HEAD (`git checkout --`) and is reported as finding N4.

# VERDICT: `REMEDIATION_REQUIRED`

The three round-1 findings are closed or closed-in-substance EXCEPT F3, whose
remediation test exists but is vacuous (N2, MEDIUM), and F1b, which was not
folded in (N3, LOW, zero material effect). The remediation itself introduced
no lookahead, no data-identity defect, and did not thin-gate the controls.
However, this round's independent re-derivation of the selection law found a
NEW HIGH defect (N1): the frozen fold-1 empty-inner rule is implemented with
an off-by-one that force-FLATs outer fold k=2 for every regime — including
three BTC_H1 slots where the inner evidence exists, passes the frozen floors,
and the law requires selection to proceed. Zero unresolved HIGH is required
for STOP-1; N1 blocks.

---

## Round-1 remediation verification

### F1 (HIGH) — OUTER census floor gate: FIXED, verified load-bearing — CLOSED

- `rsmv1/scored.py::arm_c_selection` now calls
  `measure_cell_census(CYCLE_DIR, ctx.cell)` (the REAL census: a fresh
  self-verifying timeline rebuild per call, not a cached artifact read)
  BEFORE any inner-law logic; a regime with verdict
  `NOT_RUN_THIN_REGIME` is mapped FLAT in EVERY fold with audit reason
  `OUTER_FLOOR_THIN`, carrying `outer_episodes_total` and
  `outer_margin_to_floor_min`. Missing-regime lookups default to
  `NOT_RUN_THIN_REGIME` (fail-closed). This implements frozen rule
  `OUTER_THIN` (order 2) of `rsmv1_selection_freeze.proposal.json`.
- **Independent census (auditor's own code, /tmp/a7r2_audit/own_census.py):**
  run-length segmentation, START-bar fold assignment and floor arithmetic
  re-implemented from scratch over `runtime/regime_timeline_*.json` +
  `fold_contract.json`. Result matches the census artifact and the expected
  thin set EXACTLY: BTC_H1 ACC/UP/DOWN PASS (23/28/34 episodes) with DIST
  THIN (5); BTC_H4 all four THIN (4/12/1/14); SPY_D1 all four THIN
  (1/17/1/15).
- **Live refutation with the real census call**
  (/tmp/a7r2_audit/refute_arm_c.py): with `eligible_for` monkeypatched to
  return fake specialists for EVERY regime and fake evidence paying +100 on
  every fold, BTC_H1 DISTRIBUTION routes FLAT in all 4 folds, reason
  `OUTER_FLOOR_THIN`. Counterfactual: flipping only DIST's census verdict to
  PASS (simulating an absent gate) makes fold 4 select the fake specialist
  (inner pool 5 episodes / 1621 decisions passes the inner floors) — the
  census verdict IS the load-bearing gate.
- **Controls correctly NOT thin-gated:** `arm_d` and `arm_e` build their own
  mappings and contain no census/thin references (verified by code
  inspection + source grep) — the gate was applied exactly where it belongs
  (candidate arm C only). Arm F's anchor mapping inherits arm C's
  thin-gated mapping (consistent anchor).

### F1b (LOW, fold-in requested) — NOT FOLDED IN → N3 below

`arm_c_selection` still counts inner eligible decisions as
`sum(e["length"] for e in inner_eps if e["length"] >= 6)` while the frozen
`counts_definitions.eligible_decision_for_regime` defines an eligible
decision as an in-episode bar with offset >= buffer_k + 1 = 2. No code
change, no freeze amendment (selection proposal `amendments` = []).

### F2 (MEDIUM) — decision-cache manifest digest: FIXED, fully re-verified — CLOSED

- All 7 `files[]` entries are exactly 64 hex and recompute from
  `data_local/` bytes (auditor recompute, 7/7 match).
- `bulk_response_manifest_SPY_D1.json` recorded digest now
  `4bae…e56c9` (64 hex) — recomputes exactly; file re-verified byte-identical
  to the V2 original.
- The A6 arms proposal carries a DISCLOSED amendment (`amendments[0]`,
  id `A7-R1-F2`, by A1, old_value/new_value, path
  `input_pins/decision_cache_manifest/sha256`, "no semantic contract
  changed").
- Amended `self_sha256` recomputes exactly (canonical-JSON convention:
  sort_keys, compact separators, ensure_ascii, field removed) — 4/4
  proposals.
- The freeze wrappers pin the AMENDED bytes: 4/4
  `parameter_source_of_truth.sha256` match the proposal files on disk;
  5/5 `rsmv1_freeze_manifest.json` entries match the wrapper files; the
  frozen `rsmv1_arms_freeze.json` `input_pins.decision_cache_manifest.sha256`
  equals both the amendment's `new_value` and the on-disk manifest digest.
- 3/3 V2 `JEV_ONLY_ROUTER/tier_1.json` artifact pins match (trades
  978/1060/343).

### F3 (MEDIUM) — mandated leak test: PRESENT but VACUOUS → N2 below

`tests_py/test_thin_routing_and_leak.py::test_selection_invariance_outer_fold_leak`
does mutate outer-fold evidence (fold nets 999/-999 vs -1/1 on folds 2–3)
and asserts identical selections — the letter of the
`no_peeking_law` mandate. It does not, however, contain the leak
(see N2).

---

## NEW FINDINGS (this round)

### N1 — HIGH — Frozen fold-numbering off-by-one: outer fold k=2 is force-FLAT for every regime, with a false audit reason

- **Law:** `rsmv1_selection_freeze.proposal.json`
  `nested_walk_forward_law`: folds numbered **k ∈ {1,2,3,4}**;
  `fold_1_default`: "**k=1** has an empty inner set ⇒ FLAT … reason code
  FOLD1_NO_INNER"; `inner_train_set` = folds 1..k−1. Rule `FOLD1`
  (order 3): predicate `k == 1`. Plan §5: "fold 1 has empty inner ⇒ FLAT";
  folds k=2..4 each select from their (non-empty for k≥2) inner window.
- **Code:** `rsmv1/selection.py::select_for_fold` tests
  `if fold_id == 1: return FLAT, "fold1_empty_inner_default"`, but its
  caller `rsmv1/scored.py::arm_c_selection` iterates
  `for fid in range(4)` — **0-indexed** — and computes inner evidence as
  `0 <= _start_fold(ctx, e) < fid` (fid=0 is the empty-inner fold). The
  unit-test fixtures (`test_turnover_selection.py`) call `select_for_fold`
  with 1-indexed ids (1..4), matching the freeze — so the special case
  fires one fold LATE in the scored path:
  - **k=1 (fid=0):** falls through to the floor check and returns FLAT with
    reason `inner_floor_failure` — outcome coincidentally FLAT (inner
    genuinely empty), but the recorded reason code contradicts the frozen
    procedure (`FOLD1_NO_INNER`).
  - **k=2 (fid=1):** the `fold_id == 1` branch FIRES and returns FLAT
    "fold1_empty_inner_default" — **a false statement** (this fold's inner
    pool is fold 1 and is frequently non-empty) — before floors or
    selection are ever consulted. The stability rule's
    "inner folds ≤ 2 ⇒ higher on every inner fold" branch is accordingly
    dead for k=2 (reachable only at k=3).
- **Live proof** (/tmp/a7r2_audit/refute_arm_c.py, real census, real
  `CellCtx("BTC_H1")`): audit rows at fid=1 read
  `selected=FLAT, reason=fold1_empty_inner_default, floor_ok=True` with
  `inner_episodes/inner_eligible_decisions` = **6/396 (ACCUMULATION),
  9/642 (UPTREND), 10/750 (DOWNTREND)** — all far above the 5/150 inner
  floors. Under the frozen law these three slots MUST proceed to selection
  (ACC: single eligible ⇒ `SINGLE_ELIGIBLE`; UP/DOWN: pair resolution).
  Auditor re-derivation of fold-0 pools from the timeline bytes confirms
  the same conclusion independently of the in-process run.
- **Consequence if scored as built:** arm C's BTC_H1 mapping for the whole
  outer fold k=2 is FLAT for every regime — an unauthorized deviation from
  the frozen selection law; the selection audit records a false reason;
  arm F's matching anchor inherits the deviant mapping. The direction is
  conservative (suppresses candidate risk), which is exactly why it must be
  fixed BEFORE any outcome exists: after PnL is visible, changing the
  mapping law is forbidden (plan §10.3 "no mapping/threshold edits after
  PnL is visible"), so an uncorrected run would either score a law the
  cycle never froze, or force a post-outcome TECHABORT. BTC_H4 and SPY_D1
  are unaffected (every regime is census-THIN there, so the OUTER gate
  already routes FLAT in all folds regardless).
- **Required remediation (owner/A1, pre-GO):** make the empty-inner special
  case fire on the FIRST fold only (0-indexed `fold_id == 0` at this call
  site, or pass 1-indexed k consistently), emit `FOLD1_NO_INNER` for k=1,
  and let k=2 proceed to floors + selection per the frozen law. Re-run
  dry-run + tests; no freeze content changes (this is code catching up to
  the frozen law, same class as round-1 F1).

### N2 — MEDIUM — The F3 remediation leak test cannot detect the leak it mandates

- The shipped `test_selection_invariance_outer_fold_leak` builds its
  selections from a stub ctx with `episodes = []`, so EVERY row of both
  audits is FLAT via `inner_floor_failure` / `fold1_empty_inner_default`.
  Auditor experiment (/tmp/a7r2_audit/refute_leak_test.py): a deliberately
  LEAKY re-implementation of the same selection loop (candidates pooled
  over ALL folds, `f < fid` filter removed) produces **byte-identical
  outputs** on the test's exact fixture — the assertion passes for the
  clean AND the leaking implementation. Additionally, even with floors
  passing, the fixture's single candidate can never flip: the
  `single_eligible_specialist` outcome ignores nets entirely. The leak
  class the `no_peeking_law` targets (outer-fold data flipping a
  two-candidate pooled/stability winner) is not exercised.
- **Detection is demonstrably possible** (/tmp/a7r2_audit/race_fixture.py):
  a floors-passing two-candidate fixture with near-tied inner folds and
  opposing outer-fold nets DIVERGES between clean and leaky variants
  (e.g. fid=3: `inner_net_higher_stable` → B vs `FLAT, unstable`).
- **For/against:** FOR genuineness — the test does mutate outer-fold
  evidence and asserts selection invariance, so a grossly broken filter
  combined with floor-passing evidence would trip it; it documents intent.
  AGAINST — with its actual fixture the assertion is trivially true
  regardless of the filter, so it provides zero regression protection for
  the exact leak class named in the freeze law. **Remediation:** replace
  the fixture with floors-passing two-candidate races (mutate outer folds
  2–3, assert identical selections; optionally assert the mutated pooled
  values DO differ to prove the mutation is live).

### N3 — LOW — F1b not folded in: inner eligible-decision counter deviates from the frozen definition (zero material effect on this data)

- Freeze: eligible decision = in-episode bar with offset ≥ 2. Code: full
  lengths of episodes with length ≥ 6 (permissive: counts up to 2 extra
  bars per episode). Round-1 required folding this into the F1
  remediation; it was not (no code change, no disclosed freeze amendment).
- Auditor recompute of BOTH definitions for every (cell, regime, fold)
  (/tmp/a7r2_audit/own_census.py): **no slot's floor pass/fail flips** —
  e.g. BTC_H1 DIST fold-4 inner pool 1621 vs ~1611 (both ≫ 150); all thin
  cells fail on episode counts, not decisions. Direction permissive, but
  with the OUTER gate now first, every affected regime is THIN anyway.
  Fix alongside N1 (implement the offset≥2 counter) or amend the freeze
  with a disclosed change — either is acceptable pre-outcome.

### N4 — LOW — `evidence/dryrun_sanitized.json` is stale at HEAD (config_digest does not recompute)

- The artifact was last written at 91f82aa6; commit 5e72f368 regenerated
  all four freeze wrappers (new `frozen_at_utc` bytes), so the dry-run's
  `config_digest` (sha256 over all `freezes/*.json`) changed: committed
  `d3ead114…` vs recomputed-at-HEAD `5de75dbd…`. The commit message claims
  "dryrun ALL_PASS", but the committed artifact predates the final wrapper
  regen.
- Auditor re-ran `tools/cmd_dryrun.py` at HEAD: `all_pass: True`, exit 0,
  `pnl_anywhere: false`, `denominator_delta: 0`, 21 pairwise-distinct
  identities; the artifact carries only counts/booleans — no PnL at any
  depth (verified by key inspection). The refresh was restored to HEAD
  (auditors do not repair); **remediation:** re-run the dry-run after the
  N1 fix and commit the refreshed artifact.

---

## Checklist verdicts (all 18 re-verified this round)

| # | Item | Verdict |
|---|---|---|
| 1 | Predecessor verdict + V2 byte-untouched | PASS (0c277a94 clean; 3 tier_1 pins recompute) |
| 2 | Decision identity + timeline rebuild | PASS (7/7 digests 64-hex recompute; 90/31/34 OK, exit 0, deterministic rewrite) |
| 3 | Sample floors (census) | PASS (own-code census reproduces verdicts/counts exactly; floors unadjusted) |
| 4 | Specialist library bounded + verbatim | PASS (6 specs, ≤2/regime; 20/10 Turtle, ATR14, EMA20/50, SMA20, 0.5/3.0 ATR stops, min-hold 6, hh20/ll10 trailing; SPY filters `-S`; UNK FLAT) |
| 5 | A4 outcome-blindness + integration order | PASS |
| 6 | Nested selection law | **FAIL → N1 (HIGH off-by-one k=2)**; OUTER gate itself now correct |
| 7 | NO-LOOKAHEAD | PASS (buffered_labels delay direction; A2 delay_labels same law; inner-only reads `f < fid`; engine targets strictly pre-open via B equivalence) |
| 8 | Turnover law | PASS (k=1; no-op; FIXED_POINT_MAX=5 fail-closed; caps 978/1060/343; NEW hard `unnecessary_close_reopen` counter raises on ≠0) |
| 9 | Cost authority | PASS (BTC 5+1 bps/side + funding 1.377e-5/8h; SPY 10 bps/fill; `CellCtx.cost` multiplies fee+slip only; tiers 1.0/1.5/2.0) |
| 10 | Controls | PASS (F matching+Q-11 inside acceptance, fail-closed `NOT_RUN_CONTROL_MATCHING`; D disclosed OUTCOME_INFORMED_CONTROL; `_assert_b_equivalence` before any C outcome in `run_all`; D/E correctly NOT thin-gated) |
| 11 | Trial accounting | PASS (21 = 3×7; observed += 7/cell even on F failure; `runtime/scored` absent) |
| 12 | Engine equivalence re-run | PASS (MATCH ×3, all_match true, exit 0) |
| 13 | Freeze digests + amendment chain | PASS (5/5 manifest, 4/4 wrapper pins, self_sha256 4/4, amendment verified, V2 pins 3/3) |
| 14 | Full test suite | PASS (**117 passed + 1 xfailed**, exactly as mandated; xfail = A5-F1, ACCEPTED) |
| 15 | Sanitized dry-run | PASS (all_pass, exit 0, no PnL at depth, 21 distinct) with N4 LOW staleness note |
| 16 | S1 sealed + no broker surface | PASS (S1/V1 guards live; only credential-hygiene mention of api_key; no SANDBOX-OVERFIT refs) |
| 17 | GO quarantine | PASS (exit 20 `REFUSED_BACKTEST_QUARANTINE`; `--check` expected sha `47ee5e6f…` = recomputed exact-phrase sha256, no-newline; registry go REGISTERED_NOT_CONSUMED, budget 0/21, S1 SEALED_UNTOUCHED) |
| 18 | Contamination disclosure | PASS (`DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION` ceiling in evaluation freeze + run_all disclosure; promotion ban; successor law) |

## Evidence log (round-2 commands + results)

1. `git -C <a7r2 worktree> rev-parse HEAD` → 5e72f36801aadef71aae152d900ec43c1cc7dcbf; branch `orca/rsmv1-a7r2-preoutcome`; clean; remediation commits 06bf30bd + 5e72f368 (faa1a9f1 = round-1 handoff).
2. `git -C <V2 worktree> rev-parse HEAD` → 0c277a94ba2831636cde423d51fd9251ed487bfd; `status --porcelain` empty; branch `orca/jev-regime-router-v2-integration`.
3. Digest script: 7/7 decision-cache manifest entries 64-hex + recompute; V2 byte-identity of the corrected file; 4/4 wrapper pins; 5/5 manifest entries; arms input pin == amendment new_value == on-disk sha; 4/4 proposal self_sha256 (canonical-JSON-minus-field convention, `tests_py/test_freeze_proposals.py` header law); 3/3 V2 tier_1 artifact pins.
4. Own-code census (no rsmv1.census import): thin set EXACTLY {BTC_H1: DIST; BTC_H4: all; SPY_D1: all}; per-cell totals 23/28/5/34, 4/12/1/14, 1/17/1/15; census artifact cross-checked — identical.
5. /tmp/a7r2_audit/refute_arm_c.py: real-census thin gate holds (DIST FLAT ×4, OUTER_FLOOR_THIN); counterfactual verdict-flip selects fake specialist at DIST fold 4 (inner 5/1621); fid=1 rows expose N1 (6/396, 9/642, 10/750 with floor_ok=True yet FLAT fold1_empty_inner_default); arm_d/arm_e contain no census/thin logic.
6. /tmp/a7r2_audit/refute_leak_test.py + race_fixture.py: shipped leak-test fixture CLEAN ≡ LEAKY (vacuous); constructible floors-passing two-candidate fixture DIVERGES (leak detectable in principle).
7. `python -m pytest tests_py -q` → **117 passed, 1 xfailed in 8.76s**.
8. `python tools/cmd_equivalence.py` → BTC_H1/BTC_H4/SPY_D1 MATCH, all_match True, exit 0.
9. `python tools/cmd_dryrun.py` → all_pass True, exit 0; refreshed artifact diff = config_digest only (N4); restored to HEAD after inspection.
10. `python tools/run_diagnostics.py timeline` → switches 90/31/34 OK, exit 0; tree unchanged apart from N4 item.
11. `python tools/cmd_scored.py` → REFUSED_BACKTEST_QUARANTINE, exit 20; `--check` expected sha 47ee5e6f2bde5957149db8e8b0381ff0f3d6ffa7529fe6d4474c62f2bfb2c70c == recomputed sha256 of the exact GO phrase (no trailing newline).
12. `plans/CYCLE_REGISTRY.json` (read-only): lifecycle PLANNED_NOT_STARTED, budget 0/21, s1 SEALED_UNTOUCHED, go_phrase REGISTERED_NOT_CONSUMED, workers 0.
13. `runtime/scored` does not exist (runtime/ holds only the three frozen timeline JSONs).

## Verdict statement

`REMEDIATION_REQUIRED` — round-1's F1 (gate) and F2 are correctly and
completely remediated; F3's test exists but is vacuous (N2). One NEW HIGH
defect (N1, fold-numbering off-by-one force-flatting outer fold k=2 with a
false audit reason) blocks `AUTHORIZED_FOR_DISCOVERY_STOP`. Required before
STOP-1: (1) fix N1 (fold-1 special case on the first fold; FOLD1_NO_INNER
reason; k=2 proceeds to floors+selection); (2) make the leak test detect
the leak (N2); (3) re-run + commit the refreshed dry-run artifact after the
code fix (N4); (4) resolve F1b/N3 in code or by disclosed amendment. With
those applied, no further barrier to authorization is known to this audit —
every re-measured number in this round reproduced exactly.
