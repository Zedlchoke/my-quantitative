# V12 I BAB-LOWBETA — implementation-lane evidence summary

Lane: `orca/v12i-blind-family`, family `A12-V12-BAB-LOWBETA` (selected blind
proposal `V12-A5-P1-BAB-LOWBETA`), frozen contract
`research/control/v12_run/selection_freeze_specs/A12-V12-BAB-LOWBETA.json`.

Scope discipline: NO scored PnL on real data was computed anywhere in this
lane. Real-data evidence is schedule-only (counts, weights extrema, turnover
and holding durations, funding-event counts, PIT proofs). Synthetic closed-form
fixtures carry every causal claim.

## Frozen identity (digests reproduce the freeze EXACTLY, asserted in tests)

| arm | role | arm_config_id | direction | arm_config_digest |
|---|---|---|---|---|
| `BAB-90D-W` | anchor | `90D-BETA` | `long_low_beta_short_high_beta` | `0cadb6149e7c3f2e0b19d6567497bfbf1e8010fd38e65f4b5faa4ae004410e74` |
| `BAB-DOWNCORR-90D-W` | neighbour | `90D-DOWNCORR` | `long_low_downcorr_short_high` | `1303532922418aacdb3329d02f1d0d31cf124184f2bbd53086d332519a29541e` |
| `BAB-90D-W-INV` | causal_negative_control | `90D-BETA-INV` | `inverted` | `66327932d9caad851c5cca9a0f050deb00a7ec3ffa88518a38d403c5a45f8231` |

Identity payload: `strategy_id="hyp_a12_v12_bab_lowbeta"`,
`family_id="A12-V12-BAB-LOWBETA"`, `benchmark_symbols_excluded=("BTCUSDT",)`,
`funding_sign_convention="LONG_PAYS_POSITIVE_RATE"`,
`matrix_cohort_hint="v12"`, window `2025-08-22T00:00:00Z..2026-08-21T00:00:00Z`,
`config` = the frozen per-arm dict verbatim. Digest over
`research.v11.publication_identity.arm_config_digest`.

## Artifacts (this directory)

* `c1_fields.json` — C1 field verification on real stamps:
  completed 15m bars only (all 20 staged symbols positive/finite closes,
  ~48.6k bars each from 2025-04-01 warmup start); close decode crosscheck
  `raw i128 / 1e16` vs the repo decoder (A9-F F7 convention; exactness is
  asserted against the decoder and in the integer domain — float64 cannot
  round-trip a 17-digit scaled integer); PIT beta proof at 4 real stamps
  (full-frame book == bars-truncated-at-stamp book, byte-identical). PASS.
* `schedule_feasibility.json` — every stamp book of every arm through
  `research.v12.feasibility`: 52 weekly Monday stamps (first 2025-08-25),
  50 book stamps + 2 fold-boundary force-flats + 1 terminal edge, **0 skip
  stamps**, frozen 4+4 legs on every book stamp, max |w| 0.174 (anchor/control)
  / 0.164 (neighbour) <= 0.30, one-way turnover + holding diagnostics +
  funding-event counts while held. PASS for all 3 arms. No PnL.
* `double_generation.json` — two independent real-data reloads produce
  byte-identical stamp books for all 3 arms (sha256 equality). PASS.
* `drop_one.json` — L-V11-7: drop-one selects the held maximum-|weight|
  symbol (ACEUSDT at the probe stamp); the generic
  `derive_family_stress_matrix` (L-V11-1, realized-weight rule) selects the
  SAME symbol; the reduced book survives at 4+4 legs within the cap.
  PASS.
* `dryrun.json` — exact-arm dummy dry-run through the REAL adapter path
  (`research.adapter_v10.runner.run_strategy`) on the SYNTHETIC closed-form
  frame; DUMMY finite metrics published via `research.v12.accounting`
  `publish_v12_cell` into a temporary EMPTY ledger: per arm PUBLISHED (+1) ->
  IDEMPOTENT_REPLAY (0) and zero-position output REFUSED
  (`REFUSED_ZERO_POSITIONS`, separate scratch ledger — the trial key is
  identity-only). No real scored metric anywhere. PASS.

## Frozen mechanism as implemented (no parameter menu)

* feature: trailing 90-day daily BTC beta (anchor/control) or trailing 90-day
  downside-correlation over BTC-down days (neighbour), from completed 15m bars
  aggregated to daily UTC log returns; eligibility = fully covered 90-day
  block (96 completed bars/day) + >= 60 valid paired observations; fail-closed
  on < 9 eligible or < 4/leg (`SKIP_NO_SELECTION`, never a partial book).
* book: long 4 lowest / short 4 highest featured names, equal within leg;
  frozen 90d BTC leg-ratio hedge `m = mean(beta_short)/mean(beta_long)`
  (book beta exactly 0; BTC never a position); ONE uniform whole-book scale
  `c = min(1, 0.30/max|w|)` — individual names are never clipped
  (the cap is unreachable at 4+4 legs; the scale is a frozen safety rule).
* control: weights negated exactly (spread flips sign with no residual —
  verified to float precision on the fixture).
* schedule: Mondays 00:00:00Z strictly inside the window (52 stamps,
  2025-08-25..2026-08-17); folds F0 2025-08-22..2025-12-21 (17 stamps),
  F1 2025-12-22..2026-04-21 (18), F2 2026-04-22..2026-08-21 (17);
  force-flat at fold boundaries and at the terminal edge.
* execution: ONE declared lag — the fill event is the first completed 15m bar
  STRICTLY after the stamp, fill recorded at that bar's close
  (`FILLED_NEXT_EVENT`); stress walks `event_delay_events` further completed
  events.
* costs: frozen V10 floors (taker 5.0 bps, +1 adverse tick) via the generic
  `rebalance_cost_between`; native funding while held under
  `LONG_PAYS_POSITIVE_RATE` via the shared PIT hook.

## Hand-computed causal fixtures (committed under `research/v12/families/bab_lowbeta/golden/`)

* `micro_weights_case.json` — 9 names, betas 0.2..1.8: longs S0..S3 at
  +0.1875, shorts S5..S8 at −0.0625, book beta exactly 0, gross 1.0, cap scale
  1; INV negates every weight exactly. 8-eligible case fails closed with
  `BELOW_MIN_ELIGIBLE`.
* `beta_ranking_fixture.json` — 12 names, designed betas 0.4+0.1i (exact OLS
  betas at the first stamp) and a forward drift 0.002·(1.6−beta): low-beta
  names are constructed to OUTPERFORM. Anchor legs = hand-computed ranking at
  every stamp; adapter-path price spread > 0; INV spread negates it exactly
  (sum 0.0).
* `downcorr_fixture.json` — designed `corr_i = 1/sqrt(1 + 40000·(d_i/beta_i)^2)`
  (Sxx=0.0009, Svv=36, holds at every stamp); neighbour book is the exact
  mirror of the anchor book on this frame — the neighbour sort demonstrably
  differs from the beta sort.

## Tests

`tests/test_v12i_bab_{identity,pit,causal,determinism,feasibility}.py` —
digest equality 3/3 against the freeze file, PIT truncation equality at every
stamp, golden causal fixtures, byte-identical double generation, real-artifact
feasibility re-assertions, dry-run publish/replay/refusal semantics.
