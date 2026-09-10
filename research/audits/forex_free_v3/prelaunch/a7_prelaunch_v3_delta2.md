# FOREX-FREE-V3 — A7 Prelaunch DELTA Re-Audit (THIRD pass, V3-Q)

- Audited: 2026-09-04T21:05:30Z (machine_date_u)
- Auditor: A7 independent delta re-audit (audit artifacts only; zero repairs)
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v3/q-a7-prelaunch3`
- Branch: `orca/forex-free-v3-q-a7-prelaunch3` — HEAD `019d844`, porcelain empty at start
- Audited freeze: `FOREX_FREE_V3_W3C` = `331a3893184b10782f735be1248d9fa792fe5783` (code-bearing; ancestor of HEAD; verified)
- Delta commit under review: `327ded4` ("I-D1-ALPHA-FIX": D1 alpha dispatch + M1-DEV binding 6/8; I1 settled control-plane-side)
- Pass-2 audit: `research/audits/forex_free_v3/prelaunch/a7_prelaunch_v3_delta.json` (067d4b4, S0_LAUNCH_BLOCKED on D1, M1-DEV conditional)
- **Scope is NARROW**: closure of D1 and M1-DEV, I1 settlement, determinism at the new freeze, chain/bytes at W3C, regression sweep of `327ded4`, carried-findings status.

## Method

`git show 327ded4` reviewed hunk-by-hunk against the pass-2 findings and **both binding proposals**. The A5 operationalization was quoted from the proposal bytes and compared to the implemented formula and its in-code transcription. Frozen W3C sources re-read at HEAD (HEAD − W3C = the recording commit only: `event_log.jsonl` +1 line, `state.json` bookkeeping; zero code bytes). All hashes recomputed from bytes in **both twin trees**. The 6-arm dummy dry-run **re-executed independently** in this auditor tree (W3C bytes, verified 7/7) against the e-exec-1 twin data (`freeze_token=None`), then recursively scanned for leaks. Targeted pytest re-run by the auditor.

## Verdict: `FOREX_FREE_V3_S0_LAUNCH_AUTHORIZED`

Zero unresolved HIGH/CRITICAL. Both pass-2 blockers are closed and independently verified at the new freeze.

## Per-check results

| Check | Verdict |
|---|---|
| C1 pin/twin integrity (HEAD/branch/porcelain; twins detached at W3C, clean) | PASS |
| C2 data+code chain (price 156/156 + macro 9/9 + code_hashes 7/7 vs the NEW W3C `w3_freeze.json`, in BOTH twins; budget 0/6; no V3 scored ledger) | PASS |
| C3 independent 6-arm dry-run at W3C (determinism vs freeze + recursive zero-leak scan) | PASS |
| C4 **D1 closure** (A5 verbatim dispatch, fail-closed paths, diagnostic demotion) | PASS |
| C5 **M1-DEV closure** (8-scenario suite, binding 6/8, boundary pinned) | PASS |
| C6 regression sweep of `327ded4` (no frozen-gate weakening, no arm-semantics change beyond the delta) | PASS |
| C7 carried findings (I1 settled; I2 INFO; L1 LOW) | PASS |
| C8 tests (`pytest tests/assets/forex_free_v3 -q`) | PASS — 95 passed, 2 skipped in 42.9s |

### Check 1 — D1 closure: CLOSED

- **Dispatch**: a scored anchor's alpha is computed per the family-declared `meta.alpha_definition`; anything else — including absent — raises `ALPHA_DEFINITION_UNKNOWN` **before** `call_family_arm(BENCHMARK_ARM)` is invoked (source order verified, lines 825–834).
- **family1** declares `a5_per_pair_day_normalized_v1`. The A5 proposal field, **verbatim**: *"overall incremental alpha := (full-sample sum of the anchor's after-cost financing-adjusted per-pair-day PnL) - (same for the benchmark), both normalized per pair-day of the identical post-warmup schedule window, with identical notional units per active position. Gate: > 0. The per-trade expectancy difference (anchor - benchmark) is reported alongside as a diagnostic, not the gate."* Implemented as `round((fsum(anchor fin-adj pnls) − fsum(benchmark fin-adj pnls)) / post_warmup_pair_days(...), 10)`: `(sumA/N) − (sumB/N) == (sumA − sumB)/N` over the SAME N; N = pair-day count of the identical post-warmup schedule window (per pair: daily 16:00-NY decision bars of the authorized snapshot minus the frozen warmup prefix; 63-bar anchor warmup is the deeper, hence the common window). The in-code transcription matches the proposal text verbatim; identical notional holds via the same kernel/unit.
- **family2** declares `per_trade_expectancy_difference_v1` — its own frozen A6 gate, **unchanged** (that branch returns exactly the per-trade expectancy difference).
- **Diagnostic demotion**: the per-trade difference is computed on every scored anchor and reported only as `benchmark_treatment.per_trade_expectancy_difference_diagnostic`; the record echoes `incremental_alpha_definition`. The gate (`INCREMENTAL_ALPHA_NOT_POSITIVE`, unchanged) now evaluates the frozen per-pair-day value.
- **Fail-closed additions exercised by tests**: `ALPHA_WARMUP_NOT_DECLARED`, `ALPHA_PRICE_SOURCE_MISSING`, `ALPHA_WINDOW_EMPTY`. The window reader is the same `load_daily_16ny_closes` the USD index consumes.
- **Sign-divergence proof**: a hand-computed golden pins diagnostic `+3.1313131313` vs frozen alpha `−0.4646464647` (N=6) — the gate follows the frozen value, i.e., the exact D1 failure mode is now covered in the direction the proposal froze.
- Dry-run never dispatches (branch is inside `not dry_run and arm == "anchor"`); re-confirmed by the C3 rerun.

### Check 2 — M1-DEV closure: CLOSED

- `DROPOUT_SCENARIOS = 8`, `DROPOUT_MIN_SURVIVAL = 6` binding in the runner; gate reason renamed `DROPOUT_SURVIVAL_BELOW_6_OF_8`; constant and gate comments both cite `a7_prelaunch_v3_delta.json` finding M1-DEV.
- Boundary pinned by tests: 7/8 passes, exactly **6/8 passes**, **5/8 FAILS** with `DROPOUT_SURVIVAL_BELOW_6_OF_8`; constants pinned `== 8` / `== 6`.
- Semantics unchanged (survival = reduced-book financing-adjusted expectancy > 0; unevaluable fold fails closed). The pass-2 condition is discharged **in code ahead of any scored cell** (budget still 0/6).

### Check 3 — Determinism at the new freeze: PASS

Auditor-executed dry-run (audit-tree W3C bytes, e-exec-1 twin data, `freeze_token=None`, exit 0):

- `scored=false`, `real_pnl=false`, `published=false`, `dry_run=true` on all 6 arms; `incremental_alpha=None`, `benchmark_treatment=None` everywhere (the new `incremental_alpha_definition` field is a config label, like `financing_formula`).
- Recursive zero-leak scan: **zero nonzero floats** across all 6 records (stronger than the allowance — even `cost_tier` contributed none); nonzero integers are counts/indices only.
- Record IDs pairwise unique **and** 6/6 equal to `w3_freeze.json six_arm_dummy_dry_run`; `n_decisions` 6/6 equal (family1 312/302/154, family2 138/344/145).

### Check 4 — Chain and bytes: PASS

- Twins `e-exec-1` and `r-reproduce` both detached at `331a389` (W3C), porcelain clean.
- Price **156/156** (digests_exec2 / digests_repro2) and macro **9/9** (`w3_freeze.json macro_vintages.file_sha256`) in **both** twins.
- Code hashes **7/7** vs the NEW W3C `w3_freeze.json` in the audit tree **and both twins** (3 re-frozen by the delta, 4 byte-identical to W3B).
- Budget **0/6**; no V3 scored ledger in the audit tree or either twin (only prior-cycle V1 dry-run fixture ledgers, byte-identical across twins, sha256 re-verified equal).
- Regression sweep of `327ded4`: **no frozen-gate weakening** (the only gate-constant change is the dropout floor 5→6 — the M1-DEV strengthening; every other frozen constant byte-identical); **no arm-semantics change beyond the delta** (behavioral delta confined to the scored-anchor branch + dropout gate floor/rename; dry-run and sanitizer untouched; family diffs are meta declarations only); no nondeterminism introduced.

### Check 5 — Carried findings: PASS

- **I1 SETTLED**: `event_log.jsonl` records under `DELTA_REAUDIT_BLOCKED_D1` (20:08:36Z) *"i1": "settled: fold-drop scenario = best-fold drop (strictest single fold), recorded as the frozen intent"* and again under `W3C_FROZEN` (20:48:37Z) *"i1": "settled: best-fold-drop is the frozen fold scenario"*. Suite stays 8 scenarios; no code change made or needed.
- **I2** still INFO/ACCEPTED (legacy fallback present, unreachable in the published pipeline). **L1** still LOW/ACCEPTED WART (`call_family_arm` untouched by `327ded4`).

## Findings

| ID | Severity | Status |
|---|---|---|
| D1 | — | **CLOSED** (verified at W3C) |
| M1-DEV | — | **CLOSED** (binding 6/8 verified) |
| I1 | INFO | SETTLED (recorded owner disposition ×2 in event_log) |
| I2 | INFO | ACCEPTED, non-blocking |
| L1 | LOW | ACCEPTED WART, non-blocking |

- INFO (non-blocking): `w3_freeze.json`'s descriptive `twins` prose still reads "detached @ 9d9611…" — stale text carried from the W3 entry; the actual twins verify detached at W3C with clean porcelain. Correct the prose at the next manifest touch.

## Authorization

`FOREX_FREE_V3_S0_LAUNCH_AUTHORIZED`. Phase E may start, subject to the run contract's own standing terms (hard-stop discipline before the first scored cell; 6-cell budget, currently 0/6).
