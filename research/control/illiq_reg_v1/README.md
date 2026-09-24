# research/control/illiq_reg_v1 — cycle namespace (ILLIQ-REG-V1)

Plan: `plans/PLAN_illiq_reg_gate_v1.md` (registered, `PLANNED_NOT_STARTED`,
budget 0/4). Branch `orca/illiq-reg-v1-integration`, base
`482dc81b3da7326a8827144291d11c62e6972432`.

Contents:

- `gate_module.py` — frozen gate spec (plan §3) as pure functions: PIT daily
  DV-share, CONC(28)/CONC(90), S90, rvol30, hysteresis machines (V1 p70/p90,
  V2 floor p10 ×0.90), gate walk, falsification verdict bars
  (net ≥ −0.2947 AND MDD ≤ 0.4372), seeded random-gate controls
  (200, min run 4, seed from cycle id).
- `wiring.py` — plan §9/§11 law: per-fold funding-scan mapping (S0R/FWD →
  `scan_2026_a`, pre-window → `scan_2026`; the B2 lesson), bars load
  start −125d / end +3d, coverage verification fail-closed, and the 4-label
  invariant validator (`WINDOW_FOLD`, `OUTCOME_EXPOSED_ANCESTRY`,
  `REPLICATION_NOT_PROSPECTIVE`+`scored=False`, `FUNDING_WIRING`).
- `gate_series_build.py` — `--check-coverage-only` (bootstrap-safe, done) and
  the full catalog build (gate-sequence step 3, heavy lock, NOT implemented
  past the guard).
- `tests/` — 35 M0 tests (offline hand fixtures + live small-file wiring
  proofs against the READ-ONLY CHR3F scans).

Bootstrap evidence:

- `coverage_status.json` digest
  `b6db25834dc52144a79129cdeceb21768b3d91c79ab966dc5207b1325b8384db`:
  S0R scan_2026_a 20/20 symbols 26208 rows; FWD scan_2026_a 20/20 26461
  rows; Y2021 scan_2026 13/20 listed-in-window 14196 rows (7 not yet listed —
  PIT fact, not a gap); Y2024P scan_2026 20/20 15624 rows.

NOT RUN at bootstrap (honest inventory):

- Full gate-series build over catalogs (heavy lock; step 3).
- Sanitized dry-run, A7 prelaunch, any cell (steps 4–7; STOP owner GO first —
  `GO ILLIQ REG V1 SCORED EXECUTION`, typed only at its own gate).
- Phase 2 / FWD window: not authorized by this cycle's budget (4 = phase 1
  only).

Implementation update (2026-09-24, prelaunch implementer lane):

- `gate_series_build.full_build` IMPLEMENTED and RUN under the heavy lock
  (wrapper `full_build_locked.py`): S0R COMPLETE from catalog_live_crypto_s0r;
  FWD observables from catalog_live_crypto_a20 as an UNPINNED-CATALOG
  DIAGNOSTIC (the wiring law keeps `FOLD_WIRING["FWD"]["catalog"] = None`;
  measured a20 coverage is 20/20 symbols across the full FWD window, zero
  gaps — the "bars end 2025-09" premise was outdated). Artifact
  `gate_series.json` sha256 `e09187f925e761cfabe94e0766ca2104b3b45f5def76fad
  c061cdbc09c51702d`, byte-identical across two locked runs (determinism).
  Cross-check vs the frozen dossier single-shot: S0R s90 max abs diff 0.0;
  states 49/52 match — the 3 deltas are the strictly-PIT rvol30 window
  (gate_module) vs the dossier's descriptive `<= stamp` reading, by design.
- `dryrun.py` IMPLEMENTED and RUN: sanitized GATED traversal over S0R —
  52 stamps, 43 gated ON (34 with constructible book, 7 frozen
  WEIGHT_CAP_BREACH skips, 2 fold-boundary force-flat), 9 GATE_OFF skips,
  non_vacuous true, no PnL fields (report `dryrun_report.json`).
- Still NOT RUN: A7 prelaunch verdict, any cell (owner GO gate), FWD strategy
  stage (catalog pinning step pending), random-gate PnL controls (cell time).

READ-ONLY boundaries: everything under
`.worktrees/crypto-historical-replication-3f-v1/` is referenced by absolute
path only, never copied over, never edited. The frozen engine
(`recovered/v11_root`, `c97283e0`) is never modified.
