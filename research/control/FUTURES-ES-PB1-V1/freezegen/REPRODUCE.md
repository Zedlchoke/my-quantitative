# REPRODUCE — FUTURES-ES-PB1-V1 gate 2 (EXCLUDE-FREEZE lane)

Deterministic regeneration of `exclude_list.json` (M1) and
`selection_freeze.json` (M2). Every output element is a pure function of the
committed artifacts listed below (each cited inside the outputs with
file + field + sha256). No imputation; fail-closed: the builder aborts
without writing if any input sha mismatches or any rule check fails.

## Command

```bash
cd /Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep
/Users/hoangminhlong/my-quantitative/.venv/bin/python \
  research/control/FUTURES-ES-PB1-V1/freezegen/build_exclude_and_freeze.py
```

- Worktree HEAD at generation: `e7fc1d8db00e91af74683cee7e999620fa8ff361`
  (branch `prep/futures-es-reg-20261004`). Re-verify with ONE
  `git -C <worktree> rev-parse HEAD` before running.
- Single-shot parquet read of the ES panel (7,825,657 rows) is the only heavy
  step; no network, no S1, no signal/PnL computation.

## Expected outputs (bit-identical; sha256)

- `exclude_list.json` → `bc8a41b673eccb998017e704a9865d139e67438fe984906f7f522782f93b438a`
- `selection_freeze.json` → `e2b9934af01127ee698adda2fa0579d519f54881958e07463157728a8b96c1b7`
  (carries the exclude_list sha above; carries NO hash of itself)

Both files are written with `json.dumps(sort_keys=True, indent=2,
ensure_ascii=False)` + trailing newline; `generated_utc` is the fixed
date string `2026-10-04`, so generation is time-independent.

## Inputs (all committed at HEAD; sha256 verified by the builder)

| key | path (worktree-relative unless absolute) | sha256 |
|---|---|---|
| SPEC | research/control/FUTURES-ES-V1-PACKET/SPEC_PB1_ES.md | 445f749906481f33080185cab1628e6365ef2f6db3b9c4f9f0847646eb6b7073 |
| PLAN_REGISTERED | /Users/hoangminhlong/my-quantitative/plans/PLAN_futures_es_pb1_v1.md (ROOT repo, read-only side) | recorded by the builder at run time (input is outside this worktree; content-sha only) |
| identity_table_24 | research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/identity_table_24.json | 6e3919808ecea86d147ba67d8e5df4f4e83bed2414973f87de051054da6e471f |
| freeze_pins_v2 | research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/freeze_pins_v2.json | f7e1b580071c09526f13915523a287094ed56a530d2196adc4de0c85907b469a |
| pit_exclude_set | research/control/FUTURES-ES-PB1-REGPREP-20261004/freeze/pit_exclude_set.json | f504c7319f235f75449e5b5707014c74a37ea9bf1e558e32be59c36fada8d2f6 |
| D3_RECORDED | research/control/FUTURES-ES-PB1-REGPREP-20261004/auth/D3_RECORDED.json | f54610eb15e6cb41d32dec28616cdaaed6225fce0cfee9fe4cc3522b2fa1e355 (= freeze_pins_v2 sha256_v2 pin) |
| ES_fomc_stats | research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json | 228fe2d4efbde95984128b6b1f64a9162bb794ea406c488577036fa09518f213 |
| r3_fomc | research/control/FUTURES-DEEPRESEARCH-V2-20261003/audit/a7_es/r3_fomc.json | ba57bc3325559b7f57a3757c63c8b93e6a900d54592eebcd098d940acc4e34f3 |
| session_dispersion_es | research/control/FUTURES-K6GATE-PREP-20261004/es/session_dispersion_es.json | e56c4a53841983e02f5e643e60693581e2c9e096488a1f7491659a71bb7c43a4 (committed in-git; NOT one of the 34 v2 pins — its SYNTHESIS carrier SYNTHESIS_K6.md is pinned 03a8e77e2120f60c7a6d70802688c7f81dadf692e01e3c3d322575ff90de8237) |
| es_session_holiday | research/control/FUTURES-SIX-READINESS-20261004/es/es_session_holiday.json | 8885d5de4e7f4c5fbf06c194ea9a6b238e4a5450ac31e7d9807bc97d4ee71391 |
| calendar_close_delta | research/control/FUTURES-SIX-SCORED-GATE-PREP-20261004/cal_close/calendar_close_delta.json | 626deccc5debad9e8c24dce3a598c3371a937aeb5f792d0ce1f57314a09df8bb |
| es_o1m_roll_recheck | research/control/FUTURES-SIX-READINESS-20261004/es/es_o1m_roll_recheck.json | e7ab27ea2bfaab16009422bf7588d17e759f7e2652bf90f30c5ad4d9c5f1a66d |
| es_expiry_recheck | research/control/FUTURES-SIX-READINESS-20261004/es/es_expiry_recheck.json | 2b065d5b94540e2740791ba33560d590be460b5866d9ede037a8a9db934fa94b |
| es_1m_outright_parquet | research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet | 7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95 (v2 pin; panel located via DATA_READINESS_ES.md + es_o1m_roll_recheck.json) |
| cmecal_coverage | research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/cmecal_coverage.json | c82f50c4fa53cf93dfb0b652209007836e4d6ccfe29f3e4535a89f1f2086e157 |

## Deterministic procedure (per class; priority = FOMC > HOLIDAY_FACT_EARLYCLOSE > HOLIDAY_UNCERTAIN > COVERAGE_LT60 > WARMUP)

1. **FOMC_STATEMENT_DAY (131)** — `ES_fomc_stats.json:per_event_day_level[].date`
   (n_in_data=131 of n_statements_total=132). SPEC §3 [ERRATUM A7-SPEC-M3].
   The 132nd statement, 2020-03-15 (Sunday, `release_time_note` irregular
   list), has no session to exclude (panel has zero weekend RTH sessions) —
   carried as a law note, not a session exclude.
2. **HOLIDAY_FACT_EARLYCLOSE (10 in-panel sessions; 12 chain-span dates)** —
   2010: `es_session_holiday.json:year_2010_product_level_reference`
   (E1-(ii) proof source, per-day/per-time 2010 official PDF); 2026:
   `holiday_deviation_windows_2017_2026[2026].holiday_dates_for_legality`
   with Q5-verified OBTAINED grid + 3 FACT-grade windows
   (`calendar_close_delta.json:cells_obtained[1]`, capture shas inside).
3. **HOLIDAY_UNCERTAIN (60 in-panel sessions; 77 chain-span dates, 2017-2025)** —
   `holiday_deviation_windows_2017_2026[year].holiday_dates_for_legality`
   where `es_product_globex_times` = NOT_TRANSCRIBED; SPEC §2-E1 fail-closed.
4. **COVERAGE_LT60 (69 in-panel sessions)** — rule
   `sessions[].rth_core_coverage < 0.6` applied to
   `session_dispersion_es.json` (SPEC §3 [ERRATUM A7-SPEC-M4]); the rule
   output equals the file's own `excluded_dates` (139) exactly; margin
   0.5795 below / 0.9641 above the 0.60 floor (no borderline session).
   INDEPENDENT RECOMPUTE: the builder re-reads the pinned ES panel
   (single shot) and recounts bars with `raw_symbol == held_symbol` and
   bar-start 08:30..14:59 America/Chicago for **all 4,204 sessions**;
   all counts equal `sessions[].bars_rth_core_held` (asserted; abort on
   any mismatch). 70 of the 139 are absorbed (labelled) by classes 1-3.
5. **WARMUP (1,008 = 4 × 252)** — first 252 surviving sessions of each fold
   window F1 2010-06-01..2012-12-31 · F2 2013-01-01..2017-12-31 ·
   F3 2018-01-01..2021-12-31 · F4 2022-01-01..2026-09-30 (plan §3 / SPEC §7;
   excluded from scoring, mission M1(d) class extension).

Session universe: `session_dispersion_es.json:sessions[]` (4,204 sessions,
2010-06-07..2026-10-01; the 2026-10-01 tail stub is inside COVERAGE_LT60 and
outside every fold window → `fold: null`).

## NOT_RUN elements (recorded, never silently narrowed)

- **Per-day holiday enumeration 2011-2016 — NOT_RUN.** No committed
  machine-readable per-day list exists: `es_session_holiday.json`
  deviation windows start at 2017; `cmecal_coverage.json` 2011-2016
  coverage lists carry only window-level category labels (holidays /
  early_closes / expirations, no dated cells). Class HOLIDAY_UNCERTAIN is
  therefore **fail-closed-pending** for 2011-2016: a 2011-2016
  holiday/early-close day with ≥60% RTH-core coverage and no other
  named-law exclusion is NOT provably excluded by this freeze and must be
  resolved (owner/next gate) before scored execution. 2011-2016 early
  closes with <60% coverage remain excluded via COVERAGE_LT60; FOMC days
  remain excluded via FOMC_STATEMENT_DAY.
- E3 (2026 bounds), E4 (uncertain prev-session ⇒ signal-day exclude), E5
  (strays/dash/break-bars) are signal-time laws carried into scoring; they
  are not enumerable at this 0-cost gate and are NOT assumed empty.
- All 8 carried NOT_RUN items of `pit_exclude_set.json` are restated
  verbatim in `selection_freeze.json:not_run_register`.

## Resulting evaluation surface (post-exclude)

4 folds × (survivors − 252 warmup) = 375 + 950 + 711 + 890 = **2,926 eval
sessions**; in-panel session exclusions 1,278; non-session law dates in-span
19; law dates outside the chain span 8 (2010 pre-panel-start ×5, 2026
post-panel-end ×3).
