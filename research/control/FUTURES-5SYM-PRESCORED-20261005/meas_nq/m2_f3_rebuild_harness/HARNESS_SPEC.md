# HARNESS_SPEC — NQ-F3 full-era rebuild harness (m2_f3_rebuild_harness)

- Round **FUTURES-5SYM-PRESCORED-20261005**, lane **MEAS-NQ**, wave 3, 2026-10-05.
- Class: **HARNESS + SYNTHETIC CHECKS ONLY.** The real-data rebuild on cache_v3 is
  **NOT_RUN** while ADOPT-D9 is unsigned — the harness hard-refuses (fail-closed), it does
  not default, and it is the refusal that this wave demonstrates and records.
- Files: `rebuild_harness.py` (pipeline + generator + gates), `expected_check.py`
  (independent pure-python expected-value calculator), `runs/` (recorded executions),
  `fixture law` emitted at `runs/<mode>/fixture/fixture_law.json`.

## 1. What the harness implements (per the committed k6gate method)

Method source of record: `FUTURES-K6GATE-PREP-20261004/nq/nq_f3_rebuild_a1a2.json`
(schema `nq_f3_rebuild_a1a2_v3@1`; recipes mirrored verbatim there from
`NQ_a1_regimes.py` / `NQ_a2_sessions.py`). The harness implements the same pipeline as
*code* so it can be pointed at cache_v3 after ratification, and at synthetic fixtures now:

1. **Input manifest**: every input path + sha256 + bytes is hashed at run start
   (`rebuild_input_manifest@1`) and re-verified before load — any drift is exit 2.
2. **Chain reconstruction inputs**: held-daily panel (close, rth_coverage, volume,
   true_range) + chain table (held contract per session).
3. **Per-session ret series (NaN-aware chain law)**: `log_close = log(close)`;
   `ret = log_close.diff()` — NaN whenever either side is NaN; **no synthetic jump is ever
   bridged across a hole**; `cov = clip(rth_coverage,0,1).fillna(0)`;
   `depleted = (cov < 0.25) | close NaN`.
4. **a1 aggregate tables**: `rvol_{5,10,20,60,120,252}d` (min/p5/p25/median/p75/p95/max/
   argmin/argmax/last; `min_periods = max(2, int(w*0.75))`), vol clustering
   (acf1 of |ret| over rolling 252, vol20-of-vol20), trend persistence
   (acf1 full + rolling-252 median/p10/p90, variance ratios q ∈ {5,20,60}),
   drawdown episodes ≥10% (dd in LOG space; depth = −100×dd_trough — the same log-axis
   convention as the committed artifact), yearly table (ret/vol_ann/skew/kurt/up-days/
   worst/best/max_dd/avg volume/median true range/depleted/med_rvol20), vol-regime
   terciles (756-session expanding window, ≥300 obs).
5. **a2-style tables**: held / clean (cov ≥ 0.6) / excluded-low-coverage counts,
   fold-sliced segments.
6. **Roll set**: held-contract switches from the chain table (dates + count).
7. **Fold boundaries per SPEC_NQ.md §6** (fold law, evaluation multipliers — never
   identity multipliers): F1 2010-06-06..2012-12-31 · F2 2013-01-01..2017-12-31 ·
   F3 2018-01-01..2021-12-31 · F4 2022-01-01..2026-09-30. Warmup = **252 held sessions**
   excluded from SCORING at each fold head (ES precedent); descriptive fold slices include
   all sessions and REPORT the warmup count (`n_scoring_sessions_if_scored`) without
   silently applying it.
8. **DST law: PRESERVED QUIRK.** Session-date labels are consumed exactly as carried by
   the input table (the cache's 35 Sunday-labeled (contract, session) rows flow through
   unchanged); the harness **never re-derives session boundaries** — changing that
   semantics would be a new chain build, out of scope. The quirk is an observable:
   `quirk_labeled_sessions` counts rows whose session_date label differs from the session
   index date; the synthetic fixture embeds exactly one such row and the self-check
   asserts it is carried through.
9. **Cross-check law (never trust a precomputed column)**: the harness recomputes rets
   from closes and diffs against any provided `ret` column
   (`max_abs_ret_diff`, NaN counts) — mirroring the committed artifact's
   `crosscheck_held_daily_v3` block (which measured 0.0 on cache_v3).

## 2. The D9 gate (fail-closed)

`--real` requires `--d9-ratification <path>`: an owner-signed artifact with

```json
{"schema": "d9_ratification@1", "decision": "ADOPT-D9-OptionA",
 "signed_by": "<owner>", "date": "<ISO date>"}
```

Anything else — absent, unparseable, wrong schema, wrong decision, missing signature —
refuses with exit **20**, prints `REFUSED_D9_UNSIGNED`, and writes a FINAL status artifact
`REAL_RUN_REFUSED.json` (`final: REFUSED_D9_UNSIGNED`, `real_rebuild_status: NOT_RUN`).
In ratified mode the harness still hash-verifies inputs against the manifest (exit 2 on
drift) before any pipeline work. ADOPT-D9 is UNSIGNED as of this wave
(`D8_D9_DECISION_SHEET.md`, FUTURES-SIX-ADOPT-PREP-20261004) — no such artifact exists,
so the only reachable real-mode outcome is the refusal.

## 3. Synthetic generator (deterministic; documented law)

`--synthetic` / `--selfcheck` generate (or reuse) a fixture: **1,044 business-day
sessions from 2017-01-02** (2 eras × 2 SPEC folds: 2017 sessions fall in F2, 2018–2020
in F3), prices from `random.Random(20261005).random()` only (MT19937, version-stable),
closes rounded to 2 decimals. Embedded structure:

| element | law | expected (independently computed) |
|---|---|---|
| **2 eras** | era A sessions 0..699 (0.5%-class daily vol, 300k-class volume); era B 700..1043 (×2 vol, ×3 volume) | per-year vol_ann and avg-volume rows flip at the boundary |
| **3 embedded rolls** | held contract NQFIX_A→B→C→D at sessions 300 / 640 / 900 | roll_dates = the 3 dates; n_rolls = 3 |
| **hole anomaly** | sessions 500..509 close=NaN, coverage 0 (vendor-hole analog) | 12 NaN rets (first + 10 hole + 1 bridge); depleted +10; rets never bridge |
| **thin anomaly** | sessions 760, 761 coverage 0.10, closes real | depleted by coverage law (+2) |
| **crash + recovery V** | deterministic ramp +2%/day ×40 (sessions 620..659, guarantees the pre-crash peak is the all-time high), crash −2%/day ×30 (660..689), recovery +1.5%/day ×40 (690..729) | exactly one episode with trough = crash end (session 689); depth = −100×dd_log = 30×ln(0.98)-class ≈ 60.8 (log axis; the same −100×dd_log convention as the committed artifact; the price-space equivalent is 1−0.98³⁰ ≈ 45.5%) |
| **DST quirk row** | session 703's session_date relabeled to its Sunday; `d` unchanged | `quirk_labeled_sessions == 1`, label carried through unchanged |

## 4. Expected-value checker (independent)

`expected_check.py` — **pure Python** (math/statistics only; no pandas, no numpy, no
import of the harness) — replays the same generator law with its own code and implements
the aggregate formulas from their definitions (sample std, linear-interpolation
quantiles, Pearson correlation, cummax/dd episode extraction). Comparison law:

- integer / count / boolean / string fields: **exact equality**;
- float aggregates: relative tolerance **1e-10** (identical real numbers through different
  summation orders / log-corr implementations may differ by ULPs; anything above 1e-10
  relative is a mismatch);
- the closed-form crash depth is additionally checked against the ideal unrounded law
  (30×ln(0.98)) at a coarse 1e-2 relative tolerance (closes rounded to 2 decimals).

Coverage honesty: the self-check asserts panel counts, roll set, NaN-aware chain behavior,
depleted/clean counts, per-year rows (n_sessions, vol_ann_pct, avg volume), fold slices
(n_sessions, warmup-adjusted scoring counts), the crash episode (trough date, ULP-level
depth, closed-form depth, recovery), the DST quirk, acf1(|ret|,252) median, and the
ret cross-check. NOT independently re-derived (implement-and-assert only, same formulas
mirrored from the committed recipes): rvol window summaries, variance ratios,
vol20-of-vol20, regime terciles.

## 5. Recorded executions (exit codes)

| run | command | exit | evidence |
|---|---|---|---|
| selfcheck run 1 | `python rebuild_harness.py --selfcheck --outdir runs/selfcheck_run1` | **0** | `runs/selfcheck_run1/selfcheck_results.json`: 39 checks, 0 failed, `PASS_SYNTHETIC_SELFCHECK` |
| selfcheck run 2 (fresh fixture) | `--selfcheck --outdir runs/selfcheck_run2` | **0** | identical aggregate outputs; `selfcheck_results.json` **byte-identical** to run 1 (sha256 `7a584da9…679cb0`) |
| selfcheck run 3 (reused run-1 fixture) | `--selfcheck --outdir runs/selfcheck_run3 --fixture-dir runs/selfcheck_run1/fixture` | **0** | `f3_rebuild_synthetic.json`, `selfcheck_results.json`, `input_manifest.json` all **byte-identical** to run 1 |
| determinism note | run 1 vs run 2 JSON | — | aggregates identical; the embedded `inputs_manifest` path fields differ only because the fixture directory moved — the sha256 fields are identical (`e4862da5…9dd9f`, `ce4c5259…a470c2`), and fixture parquets are byte-deterministic across generations |
| **refusal demo 1** | `--real --cache <real cache_v3>` (no ratification artifact) | **20** | `REFUSED_D9_UNSIGNED: no --d9-ratification supplied (ADOPT-D9 default = UNSIGNED)`; `runs/refusal_demo/REAL_RUN_REFUSED.json` |
| **refusal demo 2** | `--real` + malformed ratification artifact (wrong schema) | **20** | `REFUSED_D9_UNSIGNED: ratification schema != d9_ratification@1`; `runs/refusal_demo2/REAL_RUN_REFUSED.json` |

Exit-code map: 0 PASS · 2 input drift · 10 selfcheck mismatch · **20 REFUSED_D9_UNSIGNED** ·
21 missing input · 30 usage.

## 6. Status law

- **Real rebuild: NOT_RUN pending ADOPT-D9.** The harness is wired for cache_v3
  (`nq_held_daily_v3.parquet` + `held_volume_k5_v3.parquet` inputs, same schema as the
  synthetic panels) and can only execute after the owner presents a valid
  `d9_ratification@1` artifact; until then every real invocation ends in the recorded
  refusal. This lane did NOT run the real rebuild and did NOT consume cache_v3 through
  this harness (M1's descriptive reads are a separate, permitted read posture).
- No scored cells, no conditional-on-signal returns, no PnL anywhere in this harness —
  the pipeline is descriptive aggregation only.

— End HARNESS_SPEC.
