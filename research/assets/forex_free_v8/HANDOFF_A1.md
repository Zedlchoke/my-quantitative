# HANDOFF NOTES — lane A8 → A1 (FOREX-FREE-V8, family FXFV8-A5-P1)

Lane A8 implementation of the FROZEN family FXFV8-A5-P1 ("US
inflation-compensation term-structure dispersion regime").  This file
records resolved conventions, deviations, OPEN_QUESTIONs and the exact
operating commands.  Nothing here alters a frozen number; where an
ambiguity existed it is listed for A1 instead of silently decided.

## Files (all new, additive)

- `research/assets/forex_free_v8/conditioning.py`  — staged vintaged
  series loader + as-of reconstruction (AX2-C1/C2/C4) + z-score.
- `research/assets/forex_free_v8/family_a5p1_v8.py` — family runner:
  driver series (z_slope(252) anchor / z_slope(504) neighbour /
  z_dgs10level(252) control), per-pair state machine, folds,
  arm_config_digest.  Decisions only — no PnL.
- `research/assets/forex_free_v8/exec_driver_v8.py` — scored driver:
  kernel booking (V3 accounting), V5-ledger financing, dual books,
  cost ladder {1.0,1.5,2.0} tier-2.0 primary, gates 1..10 with P-2
  margins, falsification rules R1..R4, diagnostic emission, modes
  dryrun / scored (two-key refusal) / diagnostic-smoke.
- `research/assets/forex_free_v8/synthetic_fixture_v8.py` —
  deterministic LCG fixture (staged-format series + H1 snapshot + V5
  ledger) for tests and the diagnostic smoke.
- `tests/assets/forex_free_v8/test_v8_runner.py` — 47 tests, synthetic
  hand-computed fixtures only.

## Measured on the real staged bytes (local smokes, NOT committed tests)

- Grid census: 1907 clocks, 2018-04-04 .. 2025-07-24 — EXACT match to
  the P2 freeze (`p2_conditioning_clocks_v8.json`, n_clocks_S0=1907).
- Binding clocks: 1824 (83 holiday grid rows carry no numeric value and
  never bind — AX2-C4 binding is first-binding-vintage driven).
- Warmup: first usable decision clock = **2019-04-12** (first clock with
  252 binding clocks strictly before it).  The proposal says "on or
  about 2019-04-04"; the 6-trading-day difference is exactly the
  non-binding holiday rows.  Spec wording ("the first 252 BINDING
  clocks of S0 are burned") is implemented literally.
- Dry-run structural results: anchor 314 entries (proposal sanity band
  230–460), neighbour 322, control 301; fold populations
  70/133/111 (anchor) — non-vacuity floors (>=200 pooled, >=25/fold)
  met.  Holds mean ~19.7 clocks (cap 21 binds often — cost-viability
  note in the proposal applies).

## Resolved conventions (documented, not silent)

1. **z window is INCLUSIVE of the current clock** ("trailing 252
   binding clocks" = the last 252 bound values ending at t; the current
   as-of value is the last element of its own window).  Population
   std (ddof=0), pinned by a hand-computed fixture test.  Warmup burns
   252 binding clocks strictly BEFORE the first usable clock.
2. **Neighbour needs its full 504-value window before it emits z** — the
   family warmup stays 252 (frozen), so neighbour decisions start only
   after 504 bound values exist (~2020-04 on real bytes).  Spec-literal:
   no min_periods was frozen.
3. **"21 business days" = 21 grid clocks**; exit at entry_idx+21 when
   hysteresis has not fired (entry fills at t, exit fills exactly 21
   clocks later).  Time-cap exits dominate (~87% of anchor exits on real
   bytes).
4. **Boolean gates 6/7/10 encoding deviation (needs A1 ratification —
   see OPEN_QUESTION-1).**  The V6/V7 literal encoding
   (observed 1.0 vs threshold 1.0, pass rule margin > 0) makes those
   gates unpassable BY CONSTRUCTION (margin exactly 0).  V8 encodes them
   observed-in-{0.0,1.0} vs threshold 0.0 so the frozen semantics
   ("passes iff the property holds") is executable; margin reads 1.0
   when held, 0.0 when violated.  Same strict pass rule (margin > 0),
   same P-2 row shape.
5. **per_period_series covers EVERY usable decision clock per arm**
   (0.0 when nothing is realized that clock; a trade's booked PnL lands
   on its exit clock) — so DSR at terminal consumes a complete
   per-decision-clock series as the mission states.
6. **Benchmark treatment inherited from V7**: the equal-weight USD-leg
   index is a diagnostic-only benchmark; benchmark_context rows carry
   fold PnL as excess_return (never a gate input).
7. **Cost exactly once per fill** via the V3 kernel primitive:
   round-trip cost = 2 x bps_cost(notional, tier); tiers re-BOOKED,
   never scaled post hoc (test-pinned).
8. **arm_config_digest** = sha256 of the arm's frozen config JSON
   (canonical sort_keys, compact separators); carried in every decision
   record, the run meta, identity rows and every scored ledger row.

## OPEN_QUESTIONs for A1

- **OPEN_QUESTION-1 (gate semantics ratification).**  Gate 5 is frozen
  as "break_even_bps_le_1.5_floor".  The inherited V6/V7 comparator is
  `<=` (passes iff break-even bps <= 1.5), while the name and the
  proposal's cost-viability note ("the family needs a per-trade gross
  edge > ~6 bps ... to clear rule 1/5") read like a FLOOR (pass iff
  break-even >= 1.5 per side).  V8 implements the V6/V7 machinery
  VERBATIM (`<=`, threshold 1.5) per "identical_to_v7_thresholds: true"
  and the machinery-unchanged directive.  If A1 ratifies the floor
  reading, the one-token comparator flip is isolated in
  `evaluate_gates` row 5 of `exec_driver_v8.py`.  No gate outcome is
  decided on this lane.
- **OPEN_QUESTION-2 (diagnostic schema ids).**  p3's
  diagnostic_output_contract names `diag/folds@1` and `diag/margins@1`
  and an outputs set smaller than the validator's
  MANDATORY_CATEGORIES (`research/governance/diagnostic_persistability.py`
  requires per_fold_breakdown / stress_tiers / drop_one_inputs /
  benchmark_context / counters / reproduction_inputs and the three
  conditionals).  V8 emits the full canon set with the REGISTERED ids
  (`diag/per_fold_breakdown@1`, `diag/margins_to_fail@1`) so the
  machinery validates unchanged; a `control_rows.jsonl`
  (`diag/control_rows@1`, p3-mandated, unregistered in the validator)
  is additionally emitted.  A1 should reconcile the p3 contract text
  with the registered canon before the run contract is assembled.
- **OPEN_QUESTION-3 (boolean-gate encoding, see resolved convention 4).**
  Ratify the {0,1}-vs-0.0 encoding for gates 6/7/10, or supply the
  intended V6/V7 semantics if one exists that makes them passable.

## Commands (from any worktree root that has the gitignored bytes)

- Tests (no real bytes needed):
  `.venv/bin/python -m pytest tests/assets/forex_free_v8 -q`  → 47 passed.
- Dry-run (structural only; real staged bytes pinned against the
  committed manifest sha256 c8ae7877…28e7c):
  `.venv/bin/python research/assets/forex_free_v8/exec_driver_v8.py --dry-run`
  (alias: positional `dryrun`; `--out PATH` also writes the report JSON).
- Twin smoke (synthetic, cwd-relative, byte-identical artifacts from any
  two working directories — test-pinned):
  `.venv/bin/python research/assets/forex_free_v8/exec_driver_v8.py diagnostic-smoke`
  (writes ./synthetic_data + ./artifacts in CWD; counts as a rerun).
- Scored: REFUSES (exit 2) unless
  `research/control/forex_free_v8_run/run_contract.json` carries the
  cycle id, `s0_launch_authorized` + verdict
  `FOREX_FREE_V8_S0_LAUNCH_AUTHORIZED`, fresh owner phrase
  `GO FOREX V8 SCORED EXECUTION`, and budget `used + 3 <= 6`.  NEVER run
  outside the E-phase two-key protocol.

## Data copies used for local smokes (gitignored, never committed)

`research/control/forex_free_v8_run/staged_vintaged/` and
`data_raw/forex_free_v1/` were copied from the integration worktree for
the dry-run smoke.  They are gitignore-covered (verified with
`git check-ignore`) and absent from the commit.

## Inherited-suite status (additive-only confirmation)

With this lane's files present, `pytest tests --ignore=tests/assets/
forex_free_v8` gives 7 failed + 6 errors — ALL pre-existing at the base
SHA and environmental (gitignored data absent/differing in this
worktree): the same subset fails identically with this lane's files
stashed, and strictly MORE fail (9, incl. two extra V5 pin tests)
without the copied bytes.  V3/V6/V7 suites: 214 passed, 1 skipped.
No inherited file was modified.
