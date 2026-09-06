# A7 Prelaunch Re-Audit #2 — STOCKS-FREE-V10

**Verdict: `STOCKS_FREE_V10_S0_LAUNCH_AUTHORIZED`** (re-audit #2, fresh context, independent).
Full artifact: `a7_prelaunch_v10_r2.json` (schema `stocks_free_v10_run/a7_prelaunch@2`).

Audited state: branch `orca/stocks-free-v10-integration`, HEAD `afad4b1`, clean tree
(audited bytes = committed bytes), base = V9 terminal `3a61638` (verified via merge-base
and `725ce39`'s parent), remediation delta = exactly one commit touching 7 named files.

## Why authorized

The v1 REFUSED verdict rested on 2 HIGH findings in the D2 novelty gate. Both are now
fixed **and independently reproduced**:

1. **HIGH-1 (wc_stock_intensity never measured — fail-open).** `veto_ratio` now unpacks
   the `(AssetsCurrent, LiabilitiesCurrent)` tuple *before* any asof call
   (`d2_v10_novelty_measure.py` lines 465-476). The published artifact now shows the WC
   veto measured for all six proposals (n 1888–36375, was 0 everywhere).
2. **HIGH-2 (depletion veto measured on an accrual proxy).** New `veto_depletion()`
   (lines 483-504) implements `(RE_prior_FY − RE_now − Cash)/Assets` with exactly the
   three frozen V9 fields (`RetainedEarningsAccumulatedDeficit`,
   `CashAndCashEquivalentsAtCarryingValue`, `Assets`) — byte-verified against
   `v9_family_runner.py` constants and the V9 ARM_SPECS score string. The
   `cash_sub` proxy path is deleted.
3. **Fail-closed gate.** `novelty_pass = len(valid) == 9 and max(valid) <= 0.20`; a
   NOT_RUN veto now forces FAIL.

**Strongest evidence:** A7 re-ran the entire D2 measurement from the committed code
(copy patched only to write to /tmp; repo untouched) against the hash-pinned 1.49GB
panel — the output is **field-for-field identical** to the published artifact (only
`built_at_utc` differs): 9/9 vetoes measured for all six proposals, zero null rho,
maxima 0.1037 / 0.0338 / 0.1160 / 0.2912 / 0.0662 / 0.1244 — every eligibility
direction unchanged (A5-H2 still double-blocked at 0.2912 + control 0.98).

**Selection re-freeze is re-measurement, not gate adjustment:** all gates (0.20 /
0.95 / 0.70) and the rubric are unchanged; the re-measured numbers and a remediation
note are recorded; the selection is identical (SFV10-A4-H1 + SFV10-A5-H1, same arms).

**MEDIUM-1 pinned:** the new fixture constructs a same-month earlier-stamped peer that
the bucket rule must exclude. A7's mutation probe shows a day-strict stamp-window rule
would produce norm 29 / scale 2.9652 and fail both assertions (bucket rule: 30.0 /
1.4826). Suite: **22 passed**.

## Standing re-checks (all from bytes)

- Freeze chain: panel re-hashed `67591464…1447` (matches pin); timing/revision layers
  `b1477ea3…` / `7110cbf0…` with 5,453,478 / 1,667,422 rows match the manifest.
- PIT authority of `p0_v10_observables.py` re-verified end-to-end (own prior-only,
  month-bucket strict exclusion matching the P3 freeze, filer-period dedup, no
  asserted timestamps, negative lags counted).
- Signal specs match the freeze exactly; two-key guard verified by code read, the
  refusal test, and live probes (each key alone → SystemExit refusal).
- Dry-run evidence: 6/6 arms PASS non-vacuous, byte-identical x2, zero leak findings;
  UNFILLABLE_VOID classification unchanged and disclosed.
- Boundaries: S1 SEALED_UNTOUCHED, budget 0/6, stocks 30/30, staging gitignored, HEAD
  not on any remote, staged-by-name commits, no key material in committed bytes.
- Suites: 22/22 V10; full targeted 447 passed / 9 skipped / 1 failed — the failure is
  the known environmental V2-worktree `FileNotFoundError`, **git-verified** to fail
  identically at the V9 base worktree (its HEAD is exactly `3a61638`).

## Findings

- **MEDIUM-2 (carried, non-blocking):** D2 still measures A4-H1/A4-H2 exposures on a
  mean-over-window proxy of the frozen largest-first_avail exposure. Recorded as a
  launch condition: re-measure on the frozen exposure before/at terminal scoring.
- **LOW (carried):** void classification unpinned + scored-phase attribution gap;
  sig_timing tie-average convention; environmental test failure; D2 census dates.
- **LOW (new):** manifest `cohort_norm_rule` paraphrase under-describes the (stricter,
  safer) P3 month-bucket rule; control-artifact self-reported timestamps run ~2h ahead
  of both the git clock and observed real time (content verified independently).

Summary: 0 CRITICAL / 0 HIGH / 1 MEDIUM / 6 LOW (2 HIGH + 1 MEDIUM from v1 resolved).
Launch may proceed to owner GO under the two-key protocol; neither key exists yet.
