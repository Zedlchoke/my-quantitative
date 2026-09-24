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

READ-ONLY boundaries: everything under
`.worktrees/crypto-historical-replication-3f-v1/` is referenced by absolute
path only, never copied over, never edited. The frozen engine
(`recovered/v11_root`, `c97283e0`) is never modified.
