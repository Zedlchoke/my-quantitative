# A7 PRE-OUTCOME AUDIT — REGIME-STRATEGY-MAPPING-V1

**Auditor:** A7, fresh context (did not design or implement any of this cycle).
**Date:** 2026-09-23. **Base:** 91f82aa6 (`orca/rsmv1-a7-preoutcome`, tree clean at start).
**Scope:** independent verification + active refutation of every pre-outcome claim,
before the STOP-1 owner gate. Machine re-runs were executed by the auditor
(timeline rebuild, engine equivalence, dry-run, GO-quarantine refusal, full test
suite, digest recomputation, census recomputation from timeline bytes, two
in-process mutation checks). Nothing was repaired; findings are reported only.

# VERDICT: `REMEDIATION_REQUIRED`

One unresolved HIGH finding (frozen selection-law rule OUTER_THIN not
implemented in code) plus one MEDIUM identity-record defect and one MEDIUM
missing mandated test. All are remediable before the scored run; none
alleges lookahead, outcome leakage into the library, V2 mutation, or a
broken gate. Zero findings require re-running the diagnostics: every
re-measured number reproduced exactly.

---

## Checklist verdicts

| # | Item | Verdict |
|---|---|---|
| 1 | Predecessor verdict + V2 byte-untouched | PASS (F6 note; F2 in RSMV1's own manifest) |
| 2 | Cached decision identity + timeline rebuild | PASS (F2) |
| 3 | Sample floors (A3 census) | PASS (floors judged sensible, kept) |
| 4 | Specialist library bounded + verbatim code | PASS (F4, F7 notes) |
| 5 | A4 outcome-blindness + integration order | PASS |
| 6 | No combinatorial search + selection law | **FAIL → F1 (HIGH)** |
| 7 | NO-LOOKAHEAD (4 refutation targets) | PASS (F3 note) |
| 8 | Turnover law | PASS (F5 note) |
| 9 | Transaction-cost authority | PASS |
| 10 | Controls (F / D / B gate ordering) | PASS |
| 11 | Trial accounting (21; denominator 0) | PASS |
| 12 | Engine equivalence re-run | PASS (MATCH ×3, exit 0) |
| 13 | Freeze digests + V2 pins | PASS (all recomputed) |
| 14 | Full test suite | PASS (113 passed + 1 xfailed) |
| 15 | Sanitized dry-run | PASS (all_pass, no PnL, 21 distinct) |
| 16 | S1 sealed + no broker surface | PASS |
| 17 | GO quarantine | PASS (exit 20; strict byte equality proven) |
| 18 | Contamination disclosure | PASS |

---

## FINDINGS

### F1 — HIGH — Frozen selection-law rule `OUTER_THIN` (thin regime ⇒ FLAT) is not implemented in code

- **Law:** plan §4.0 ("below floor ⇒ that regime×cell scores `NOT_RUN_THIN_REGIME`
  and its specialist selection defaults to FLAT") and the frozen selection law
  `freezes/rsmv1_selection_freeze.proposal.json` `decision_procedure.rules`
  rule `OUTER_THIN` (order 2, reason `OUTER_FLOOR_THIN`) with
  `floors.outer_sample_floors` = 20 episodes total / 3 per outer fold / 100
  eligible decisions per regime per outer fold.
- **Code:** `rsmv1/selection.py::select_for_fold` takes only inner
  episodes/decisions (floors 5/150); `rsmv1/scored.py::arm_c_selection`
  computes only inner floors. `grep OUTER_FLOOR_THIN|OUTER_THIN|outer_floor`
  over `rsmv1/` returns nothing. No scored-run path reads
  `evidence/regime_sample_census.json` or re-implements the outer floors.
  Plan §9's mandatory test "thin-regime → FLAT routing" is likewise absent
  (census-verdict tests exist; no routing test does).
- **Concrete consequence (auditor-recomputed from the verified timeline
  bytes, not from census artifacts):** with per-fold eligible episodes
  - BTC_H1 DISTRIBUTION [1,2,2,0] (census THIN, 5 < 20): inner folds for
    outer fold 4 pool 5 episodes / 1621 decisions ⇒ inner floors (5/150)
    PASS ⇒ single eligible specialist `DIS-FAILED-HIGH-S` would be
    **selected and traded in a regime the sample law declared thin**.
  - BTC_H4 UPTREND [4,3,2,3] (THIN, 12): outer fold 3 inner pool 7/169 ⇒
    selectable; DOWNTREND [4,2,4,4] (THIN, 14): outer fold 4 inner pool
    10/820 ⇒ selectable.
  - SPY_D1 UPTREND [5,4,5,3] (THIN, 17): outer fold 4 inner pool 14/1474 ⇒
    selectable.
- **Why it matters:** the P2 sample-floor law is the cycle's protection
  against selection in regimes without evidence; as built, the scored run
  would violate the frozen law for exactly the regimes the census flagged,
  and the evaluation freeze's "thin cells/regs excluded from the candidate
  gate denominator" bookkeeping could not be honored.
- **Required remediation (owner/A1, pre-GO; A7 does not fix):** implement
  rule `OUTER_THIN` first-match in `arm_c_selection`/`select_for_fold`
  (consume census verdicts or recompute outer floors in-process), emit
  reason `OUTER_FLOOR_THIN` in the selection audit, add the thin-routing
  fixture, and re-run dry-run + tests. New freeze digest recording per the
  wrappers' own law (freeze content unchanged; only code must catch up).
- **F1b (LOW, same locus):** the inner-floor "eligible decisions" counter
  deviates from the frozen definition — code sums full lengths of episodes
  with length ≥ 6; the freeze defines an eligible decision as an in-episode
  bar with offset ≥ buffer_k + 1 = 2. Direction: permissive. Fold into the
  F1 remediation.

### F2 — MEDIUM — Malformed sha256 recorded for `data_local/bulk_response_manifest_SPY_D1.json`

- `freezes/decision_cache_manifest.json` line 17 records
  `4bae6476d55c40e3131e06ea28d0dee1c1a5ff78af87b2c60b513283de56c9` — **62 hex
  chars** (the real digest with two characters "96" dropped after "dee").
  Actual file sha256 (recomputed):
  `4bae6476d55c40e3131e06ea28d0dee296c1a5ff78af87b2c60b513283de56c9`.
- **No data consequence:** the local file is BYTE-IDENTICAL to the V2
  original (`.../jev_regime_router_v2/evidence/bulk_response_manifest_SPY_D1.json`)
  — provenance verified by the auditor. The other 6 manifest entries match
  exactly. But an identity freeze whose recorded digest is unreproducible
  fails any recomputing verifier; remediate by correcting the digest string
  (pre-outcome).

### F3 — MEDIUM — Mandatory no-peeking leak test absent

- The selection freeze `no_peeking_law`: "a leak test (selection invariance
  under outer-fold data mutation) is mandatory in tests". No such test
  exists (`grep invariance|mutation tests_py/` → nothing). Containment is
  by construction (`arm_c_selection` filters `f < fid`), so this is a
  missing mandated test, not a proven leak. Remediate with the test.

### F4 — LOW — Fold/stop same-bar precedence inversion (inherited V2 semantics)

- On a fold-end bar where an intrabar stop also triggers, the engine closes
  at the stop price (open) before the fold force-flat step; the A4
  proposal's precedence declares "fold force-flat > price stop". Verified
  by diffing `SpecialistEngine.run` against `Engine.run`: **identical except
  the two dispatch calls** — the ordering is V2's own. Coincidence is rare;
  impact limited to exit price on that single bar. Record only.

### F5 — LOW — No explicit `unnecessary_close_reopen` counter in the scored run

- The invariant is structurally guaranteed (the no-op pass changes the
  emitted target string only on a direction change or FLAT, so the engine
  can never close-and-reopen on a label-only change), pinned in the turnover
  freeze (`zero_unnecessary_close_reopen`) and tested at freeze-text level.
  But no runtime counter of actual occurrences is emitted into arm C
  artifacts; the scored run would report `noop_target_updates` (suppressed
  events) without a positive proof-of-zero record. Add a post-hoc counter
  over the arm C ledger in the terminal analysis, or in-run.

### F6 — INFO — A2 evidence describes V2 as "terminal" without quoting the verdict string

- `evidence/mechanism_attribution.json` / `...REPORT.md` say "the terminal V2
  corpus" and never write `JEV_NO_INCREMENTAL_VALUE`. The verdict string IS
  recorded in plan §0/§1, the registry entry, `a6_controls_design.md`, the
  decision-cache manifest and the arms freeze proposal. No artifact carries
  a contradicting or softer label.

### F7 — INFO — Plan §5 sketch IDs superseded by the frozen library

- Frozen library: ACC-BASE-RECLAIM-L; UPT-DIPBUY-L + UPT-BREAKOUT-L;
  DIS-FAILED-HIGH-S (BTC-only); DNT-CASCADE-S + DNT-RALLY-SOLD-S = 6 total,
  ≤2/regime, UNK FLAT-fixed, SPY long/flat, no counter-trend, no grids,
  params convention-frozen (Turtle 20/10, Wilder ATR14, EMA20/50, SMA20,
  3.0x/0.5x ATR stops, min-hold 6, max-hold 24 regime bars / fold). The
  plan §5 sketch's UP_LONG_RISKOFF_EXIT is not carried; FLAT defaults cover
  the sketch's FLAT variants, and A4's `baseline_expressibility_note`
  documents that the V2 baseline mapping is expressible from the library.
  All acceptance bounds hold.

### F8 — INFO — Arm F tier-file totals are a FLAT-engine placeholder

- `_persist` writes arm F's `tier_1.json` totals from a FLAT engine
  (net 0.0); the real 21-seed null statistics live in `extra.f_control` and
  the summary carries the median. Disclosed by structure; note for the
  terminal analyst.

### F9 — INFO — Census counts eligible episodes only for the 20-episode floor

- Episodes shorter than `ELIGIBLE_MIN_BARS = 6` are excluded before the
  floor test — slightly tighter than plan §4.0's plain "independent
  episodes"; conservative, disclosed in the census docstring. SPY_D1
  UPTREND at 17 vs 20 is the nearest miss; the failure direction is
  protective (FLAT default).

---

## Evidence log (commands + results)

1. `git -C <a7 worktree> rev-parse HEAD` → 91f82aa69aac682bd9930abbe0300f3926be72c6; branch `orca/rsmv1-a7-preoutcome`; tree clean.
2. `git -C <V2 worktree> rev-parse HEAD` → 0c277a94ba2831636cde423d51fd9251ed487bfd; `status --porcelain` empty; branch `orca/jev-regime-router-v2-integration`.
3. `shasum -a 256` of the 3 V2 `JEV_ONLY_ROUTER/tier_1.json` artifacts → exactly the `artifact_sha256` pins in `rsmv1_arms_freeze.json` (11c9ecda…, ba172a8b…, 5e0b754f…).
4. `shasum -a 256` of 7 `data_local/` files vs `decision_cache_manifest.json` → 6/7 match; SPY bulk manifest entry malformed (F2). V2 originals byte-identical (`diff -q`).
5. `python tools/run_diagnostics.py timeline` → switches 90/31/34 OK, exit 0; stats effUNKNOWN 0.4271/0.2724/0.2908 vs expected 0.427/0.272/0.291; n_decisions 8567/1997/2751. Tree stayed clean (deterministic rewrite).
6. Mutation: in-memory `V2_EXPECTED["BTC_H1"].switches = 91` → `RegimeTimelineMismatch: switches 90 != V2 91` (fail-closed proven).
7. Independent census recomputation from `runtime/regime_timeline_*.json` + `fold_contract.json` (auditor's own run-length/fold code) → verdicts match the census exactly: BTC_H1 ACC/UP/DOWN PASS (23/28/34 episodes), BTC_H1 DIST + all BTC_H4 + all SPY_D1 THIN. No pooling (per-cell pure functions).
8. `python tools/cmd_equivalence.py` → `BTC_H1: MATCH / BTC_H4: MATCH / SPY_D1: MATCH / all_match: True`, exit 0; `evidence/engine_equivalence.json` rewritten byte-identically (tree clean).
9. `python -m pytest tests_py -q` → **113 passed, 1 xfailed** in 8.33s. xfail = `test_engine_golden.py::…buyhold…` (A5-F1), documented in `audits/a5_engine_cost_audit.md` (§A5-F1) and ACCEPTED in `audits/A1_arbitration_notes.md`.
10. `python tools/cmd_dryrun.py` → `all_pass: True`, exit 0; `pnl_anywhere: false`; `denominator_delta: 0`; 21 identities pairwise distinct; `selection_executed: false` in every cell; tree clean.
11. GO quarantine: no `SCORED_GO.json` present; `python tools/cmd_scored.py` → `REFUSED_BACKTEST_QUARANTINE`, exit **20**. Mutation (temp dir): token with trailing newline → exit 20 (refused); exact-phrase token → gate opens (import of rsmv1 attempted outside the cycle namespace). Expected sha `47ee5e6f2bde5957149db8e8b0381ff0f3d6ffa7529fe6d4474c62f2bfb2c70c` matches the phrase in plan §0 and `plans/CYCLE_REGISTRY.json` `go_phrase` (state `REGISTERED_NOT_CONSUMED`; budget 0/21; s1 SEALED_UNTOUCHED).
12. Freeze digests recomputed: all 5 `rsmv1_freeze_manifest.json` entries match; all 4 wrapper `parameter_source_of_truth.sha256` pins match the proposal files on disk (specialist 53aa8d9e…, selection ebb7555b…, turnover a8b48636…, evaluation 9928fe0f…).
13. Verbatim refutation of `specialists.py` vs the A4 proposal: every entry predicate, exit rule, stop anchor/multiplier (0.5 structural / 3.0 trend), max-hold (24 regime bars for ACC/DIS/DNT-RALLY; fold for DIPBUY/BREAKOUT/CASCADE), min-hold 6, SMA20=boll-mid, HH/LL trailing windows, asset eligibility (SPY filters `-S`), UNK FLAT — **all match; no parameter drift found**. `trailing_max/min` probe: window excludes the signal bar (PIT).
14. NO-LOOKAHEAD: `buffered_labels` pairs `regime_ts[k:]` with `persisted[:n-k]` (label known at ts[i] applies from ts[i+k]) — fixture `test_buffered_labels_delays_by_k` plus auditor mutation ((40,'B') present, (30,'B') absent). A2 `attribution.delay_labels` applies `persisted[j-k]` at j — same direction. Evidence routing reads only inner folds (`f < fid`); outer fold scored once. Engine `targets_from_regime`: governing decision strictly before exec open (V2-inherited; proven by B equivalence).
15. Engine registry: `SpecialistEngine.run` diff vs `Engine.run` = the two dispatch calls only (plus comments); structural stop overrides ATR stop when present; min-hold suppresses rule/regime exits only; max-hold never suppressed; `FIXED_POINT_MAX` 5 raises if min-hold suppression fails to converge (fail-closed).
16. Costs: `mapping_arms_freeze.json` = BTC 5+1 bps/side + funding 1.377e-5/8h; SPY 10 bps/fill; `scored.CellCtx.cost` multiplies fee+slip only, funding constant; tiers {1.0, 1.5, 2.0}.
17. Controls: arm F matching (2pp/10%/10%/2pp, 200 attempts) AND Q-11 movement (both stats > 0.02) inside acceptance; failure → `ControlMatchFailure` → recorded `NOT_RUN_CONTROL_MATCHING` (fail-closed; contrast V2's `null_invalid`). Arm D disclosed `OUTCOME_INFORMED_CONTROL` in the freeze. `_assert_b_equivalence` (5 totals fields + trade count, <1e-6) is called immediately after arm B and BEFORE `arm_c` in `run_all` — gate ordering verified in code.
18. Trial accounting: 21 = 3 cells × 7 arms in `ARMS`; FLAT/BUY_HOLD never scored; `observed` increments 7/cell even on F failure; `runtime/scored` does not exist.
19. S1/broker: `rsmv1/security.py` denies `/S1` and `s1_*` paths (guards live); no S1 path usage outside the guard; no broker/order/paper/live/testnet surface; no SANDBOX-OVERFIT-3ASSETS reference; credential hygiene code only.
20. Contamination: ceiling law `DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION`, promotion ban, successor law, S1 sealed — in the digest-pinned evaluation proposal (`contamination_disclosure`) and plan §7; verdict ladder + gates G1–G8 match plan §11.

## Sample-floor judgment (checklist 3, explicitly requested)

Floors 20/3/100 are **sensible and kept**. 20 independent episodes per
regime×cell is a defensible minimum for a selection claim with a stability
rule; 3/fold keeps every outer fold inside its own evidence; 100 eligible
decisions/fold is a minimal evaluation window. They are coherent with the
inner floors (5/150): a regime passing the outer floors can still fail
inner floors in early folds and defaults FLAT — conservative. No
adjustment proposed. The binding effect (only BTC_H1 ACC/UP/DOWN pass) is
the sample law doing its job, not a defect — note that F1 must be fixed so
the scored router actually honors these verdicts.

## Verdict statement

`REMEDIATION_REQUIRED` — the cycle may NOT proceed to STOP-1 until F1
(HIGH) is remediated (implement + test the frozen `OUTER_THIN` rule; fold
in F1b) and F2/F3 are corrected. On remediation, with the auditor's
re-measurements all reproduced exactly, no remaining barrier to
`AUTHORIZED_FOR_DISCOVERY_STOP` is known to this audit.
