# DISCREPANCY_REGISTER — D_VERIFY · NFL-PLAYERFEAT-PREP-V1 · 2026-10-05

Severity scale: BLOCKER > MAJOR > MINOR > INFO. Counts: BLOCKER 0 · MAJOR 0 · MINOR 2 · INFO 2.
Lane verdict: **VERIFIED_WITH_MINOR** (documentation-only findings; zero data-table,
manifest, determinism, or boundary discrepancies).

## MINOR-1 — COVERAGE_AUDIT.md §5 states an unmeasured max for `g3_top5_newly_absent_count`

- Claim: value-range table row `g3_top5_newly_absent_count | 632 | 0 | 5 | ≤ top-N`.
- Measured (verifier, from shipped parquet): n=632, min 0.0, **max 2.0**
  (distribution {0: 629, 1: 2, 2: 1}).
- Impact: none on data — the doc's "measured" table reports the theoretical top-N bound
  (5) instead of the realized max (2). Value is within the stated bound; all 7 other
  range rows reproduce exactly.
- Disposition: B_BUILD doc correction optional; no table/manifest change required.

## MINOR-2 — PIT_AUDIT.md §2 venue-direction wording for the worked example

- Claim (prose): "Target: 2024-11-17T21:25:00Z (16:25 ET), **BUF at KC**."
- Measured: `games.csv` row 2024_11_KC_BUF has away_team=KC, home_team=BUF (nflverse
  game_id convention away_home) → the game is **KC at BUF**; the KC row is `side=away`.
  The verifier initially recomputed the `home` row and got BUF's (consistent) numbers
  before re-keying on the correct side.
- Impact: none on any value — the section's numbers are all from the team==KC row and
  reproduce exactly (819/6/1/124, n_prior 9, rest 7.1424, G2 0.69312/0.22208/63.0/0.79299).
  Risk is only for a re-deriver following the prose to the wrong side row.
- Disposition: B_BUILD prose fix optional.

## INFO-1 — Pre-existing stray empty directory `lanes/"B_BUILD lanes"/D_VERIFY/`

- Empty directory tree created 2026-10-05 18:48 (dispatch-packet time, before either lane
  ran) — orchestrator path artifact. Not written by B_BUILD or D_VERIFY; left untouched
  (outside this lane's allowed paths). Already disclosed in handoff_B_BUILD.json
  known_limitations.

## INFO-2 — snap_counts 2026 release-lag posture (carried, by law)

- snap 2026 file (sha `fae0627d…8273`) lags stats 2026 (sha `49bc644e…6179`) by the
  in-season release cadence disclosed by B_BUILD (≤1 week, build vs fetch dates). Frozen
  sha256s are the evidence anchors; release-level caveat carried from predecessor — not a
  row-level defect. No action.

## Explicitly NOT discrepancies

- All 7 sha256 pins (6 inputs + output) — byte-exact.
- Join rates, censuses, coverage splits, flag counts, first-computable dates, universe
  counts, value ranges (except MINOR-1), determinism, sort law, NaN laws, outcome ban,
  NOT_RUN_PIT posture, boundary/isolation — all reproduce exactly.
- Verifier-side notes (no lane impact): the verifier's first sample pick used side=home
  for 2024_11_KC_BUF (BUF row) and was re-keyed to the KC away row (MINOR-2 root cause);
  two verdict-expression bugs in verifier work scripts were fixed in place and re-run.
