# VERIFICATION_LOG — FUTURES-DATACONTRACT-QUAL-V1 / Lane DC-VERIFY

- **Date run**: 2026-10-03 (all commands executed live on this date)
- **Worktree**: `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep` (branch `prep/futures-behavior-10syms-20261002`)
- **HEAD at run**: `b71c837d1f72d17b35475ab5e2795f6d113c1f9f` (== dispatch_sha; no commits made by this lane)
- **Interpreter**: `/Users/hoangminhlong/my-quantitative/.venv/bin/python`
- **Purpose**: cheap on-disk raw-vs-normalized reconciliation re-runs backing the FUTURES-DEEPRESEARCH-V2-20261003 errata.
- **Verdict tags**: `FACT` (exact expected value confirmed by command), `OBSERVED` (measured, no exact comparator — honest deltas), `NOT_RUN` (not completable; never inferred).
- **Evidence artifacts** (this dir): `check1_2_mof_cftc.py`, `check3_cot_alt.sh`, `check4_nq_alias.py`, `check5_6e_oi.py`, `check6_inventory.py` (inline heredoc, JSON output kept), `check6_inventory.json`, `check8_ibkr_freshness.json`, `out_check*.txt` (captured stdout of the saved scripts).

**Summary: 8/8 checks completed; 0 NOT_RUN. Checks 1–5 FACT (all exact), 6 OBSERVED (ballparks, honest deltas), 7 FACT, 8 OBSERVED (mtimes measured; interpretation advisory).**

---

## Check 1 — MOF tidy (rows, 2022-10-24 row, 81-row backup)

- **Command** (saved: `check1_2_mof_cftc.py`):
  `cd <verify dir> && /Users/hoangminhlong/my-quantitative/.venv/bin/python check1_2_mof_cftc.py`
- **Exit code**: 0 (initial exploratory run exited 1 on a date-column IndexError before adapting to `observation_period`; the saved script is the adapted, clean version)
- **Expected**: 386 rows; 2022-10-24 row present (amount 7296 × 100m JPY, JPY-buying); backup `mof_intervention_tidy.parquet.bak_81rows_20261003` exists with 81 rows.
- **Observed**:
  - rows = **386** (date range 1991-05-13 .. 2026-05-06)
  - 2022-10-24 row present: `series_id=MOF_FX_INTERVENTION_DAILY`, `value_yen_100m=7296.0`, `direction=JPY_buying`, `pair_desc="the US dollar (sold) the Japanese yen (bought)"`, `vintage_flag=official_history_published_with_lag`
  - backup exists = True; backup rows = **81**
- **Verdict**: **FACT** — every expected value confirmed exactly.

## Check 2 — CFTC fixed tidy sha256 + pre-fix backup

- **Command**: same `check1_2_mof_cftc.py` run (sha256 section).
- **Exit code**: 0
- **Expected**: sha256 of `.../normalized/cftc_legacy_tidy.parquet` prefix `f7a2719e745c2f6f`; pre-fix backup (`.bak_prefix_mixed_20261003` or similar) exists.
- **Observed**:
  - sha256 = `f7a2719e745c2f6f89f927ddafcb96df75ed7a6e89e69b84447e2acde6362fca` → **prefix match True**
  - current file rows = 15,347
  - backup `cftc_legacy_tidy.parquet.bak_prefix_mixed_20261003` exists: 13,369 rows, sha256[:16] `4f9cd78944ee79dc` (differs from current, as expected for a pre-fix snapshot)
- **Verdict**: **FACT**.

## Check 3 — NQ CoT ALT loader (deep-research lib)

- **Command** (saved: `check3_cot_alt.sh`):
  `cd /Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003 && /Users/hoangminhlong/my-quantitative/.venv/bin/python -c "...import NQ_deep_lib as L; c=L.load_cot_nq_all_lines(); s=c[c.series_id=='COT_LEGACY_NQ__ALT__NASDAQ_100_CONSOLIDATED_CHICAGO_MERCANTILE_EXCHANGE']; ..."`
- **Exit code**: 0
- **Expected**: 850 rows, window 2010-06-15..2026-09-22.
- **Observed**: rows = **850**; window = **2010-06-15 .. 2026-09-22**. Column adaptation: no `report_date_as_yyyy_mm_dd`; the loader exposes `obs_date` (derived from `observation_period`) — used `obs_date.min()/.max()`. Loader NOT modified. Loader also returns 3 sibling series (`COT_LEGACY_NQ`, `__ALT__MICRO_E_MINI...`, `__ALT__NASDAQ_100_STOCK_INDEX...`).
- **Verdict**: **FACT**.

## Check 4 — NQ 2020 alias (vendor parquet, instrument_id 16908)

- **Command** (saved: `check4_nq_alias.py`): loads only `instrument_id, ts_event, raw_symbol, volume` from the 13 `*NQ*` parquet chunks under `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet/`, filters `instrument_id==16908`.
- **Exit code**: 0
- **Expected**: `NQU8-NQM9` present 2018-08-15..2020-05-31 (~92,075 bars); `NQM0` 2020-06-01..06-19 (~19,406 bars); within 2020-03-23..2020-05-29: 58 distinct trading dates, ~21.8M contracts volume.
- **Observed**:
  - total rows instrument_id 16908 = 111,481 (date range 2018-08-15..2020-06-19; distinct symbols exactly `['NQM0','NQU8-NQM9']`)
  - `NQU8-NQM9` bars 2018-08-15..2020-05-31 = **92,075** (exact)
  - `NQM0` bars 2020-06-01..2020-06-19 = **19,406** (exact; 92,075+19,406 = 111,481 = total, fully consistent)
  - 2020-03-23..2020-05-29: distinct trading dates = **58** (exact); total volume = **21,824,572** (~21.8M)
- **Verdict**: **FACT**.

## Check 5 — 6E venue-OI dedupe probe (GLBX statistics)

- **Command** (saved: `check5_6e_oi.py`): reads `AV1T-statistics-ALL10__2024-04-01_2024-06-01.parquet` + `__2024-06-01_2024-08-01.parquet`, filters `stat_type==9`, `raw_symbol` startswith `6E`, `ts_ref` date == 2024-06-04; dedupe = keep latest `ts_event` per `(raw_symbol, ref_date)`, then sum `quantity`.
- **Exit code**: 0
- **Schema note**: statistics files have `instrument_id, raw_symbol, ts_event, ts_ref, stat_type, stat_flags, price, quantity, update_action` — no venue/channel column; `stat_flags` was all 0 and `update_action` all 1 on these rows. Ref date is `ts_ref` (ns → date), publication is `ts_event`.
- **Expected**: deduped total 671,736; raw (non-deduped) sum different (retracted artifact).
- **Observed**:
  - 18 raw rows = 9 contracts (`6EH5,6EM4,6EM5,6EN4,6EQ4,6EU4,6EU5,6EZ4,6EZ5`) × 2 publication timestamps
  - **Raw (non-deduped) sum = 1,343,543** — different from expected, consistent with the retracted double-count artifact (≈ 2 × 671,736 + 71)
  - **Deduped sum = 671,736** (exact). Largest component 6EM4 = 633,694; latest publication batch 2024-06-05 13:29:30.249713339.
- **Verdict**: **FACT** — both the corrected value (671,736) and the distinctness of the raw sum reproduced.

## Check 6 — Vendor parquet inventory (metadata row counts)

- **Command** (inline heredoc, output kept in `check6_inventory.json`): `pyarrow.parquet.ParquetFile(...).metadata.num_rows` per file under every `*AV1*-O1M-<SYM>*` dir; spread split via reading only the `raw_symbol` column and counting symbols containing `-` (proxy: outright = rows whose raw_symbol has no `-`).
- **Exit code**: 0
- **Measured vs expected (honest deltas, no force-match)**:

| Sym | Dirs (rows) | Parent total | Spread rows | Outright rows | Expected | Delta vs expected |
|-----|-------------|--------------|-------------|---------------|----------|-------------------|
| NQ | AV1R-O1M-NQ-DELTA 5,760,720; AV1T-O1M-NQ 1,569,600 | **7,330,320** | 641,787 | **6,688,533** | parent ~7.33M; outright ~6.69M | parent +320 (+0.004%); outright −147 (−0.002%) |
| ES | AV1R-O1M-ES-DELTA 7,012,852; AV1T-O1M-ES 1,697,668 | **8,710,520** | 884,863 | **7,825,657** | ~7.83M quarterly 1m after filter; raw parent may differ | outright −4,343 (−0.06%); raw parent recorded 8,710,520 |
| 6E | AV1B-O1M-6E-BACKFILL2 951,387; AV1R-O1M-6E-BACKFILL 2,081,877; AV1T-O1M-6E 403,469 | **3,436,733** | 375,722 | **3,061,011** | outright ~3.05M | +11,011 (+0.36%) |
| 6B | AV1B 792,552; AV1R 1,750,771; AV1T 195,349 | **2,738,672** | 189,039 | **2,549,633** | ~2.55M | −367 (−0.01%) |
| 6A | AV1B 824,446; AV1R 1,842,452; AV1T 209,370 | **2,876,268** | 171,473 | 2,704,795 | raw ~2.87M | raw +6,268 (+0.22%) |
| 6J | AV1B 812,558; AV1R 1,935,669; AV1T 372,014 | **3,120,241** | 275,066 | **2,845,175** | outright ~2.84M | +5,175 (+0.18%) |

- **Verdict**: **OBSERVED** — all six symbols within the stated ballparks (max deviation 0.36%). Caveats: "outright" is my proxy (raw_symbol without `-`), and per-dir AV1B/AV1R/AV1T families may overlap in time coverage; the metadata totals are raw file sums, not a deduplicated union.

## Check 7 — Data roots presence

- **Command** (shell): `for p in ...; do [ -e "$p" ] && echo EXISTS || echo MISSING; done` + `find ... | wc -l` counts.
- **Exit code**: 0
- **Expected**: physical av1trim root (NO leading dot) exists; dotted alias may or may not; nonprice + IBKR raw roots exist.
- **Observed**:
  - `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim` — **EXISTS** (76 parquet files under `parquet/`)
  - `/Users/hoangminhlong/.my-quantitative-data/futures-databento-av1trim` — **MISSING** (no databento entry at all under the dotted root)
  - `/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms` — EXISTS (18 files in `normalized/`)
  - `/Users/hoangminhlong/.my-quantitative-data/futures-10syms-v1/raw` — EXISTS (**1,160 files**)
- **Verdict**: **FACT** — note the asymmetry: the av1trim vendor root lives ONLY on the non-dotted physical path; anything resolving the dotted alias for av1trim will fail.

## Check 8 — IBKR legacy front-file freshness (mtime per family)

- **Command** (inline heredoc, output kept in `check8_ibkr_freshness.json`): max `os.path.getmtime` over `{RAW}/{FAM}_*` files.
- **Exit code**: 0
- **Observed** (all times local, 2026-10-02):
  - NQ: 65 files, max mtime **2026-10-02T09:37:14** (newest `NQ_NQZ7_586139864_ASK_1day_1Y.json`)
  - ES: 65 files, max mtime **2026-10-02T09:40:27** (`ES_ESZ7_586139767_ASK_1day_1Y.json`)
  - 6E: 115 files, max mtime **2026-10-02T10:24:23** (`6E_6EF8_881167116_ASK_1day_1Y.json`)
  - 6B: 115 files, max mtime **2026-10-02T10:39:03** (`6B_6BF8_881167056_ASK_1day_1Y.json`)
  - 6A: 115 files, max mtime **2026-10-02T10:46:20** (`6A_6AF8_881166975_ASK_1day_1Y.json`)
  - 6J: 115 files, max mtime **2026-10-02T10:31:40** (`6J_6JF8_881167190_ASK_1day_1Y.json`)
- **Reading** (advisory): the full serial fetch spans ~09:37→10:46 (≈69 min wall) on 2026-10-02; every family is already ≥1 day stale at verification time, consistent with the "serial IBKR re-fetch is time-critical" blocker — freshness decays as the fetch window advances.
- **Verdict**: **OBSERVED** (mtimes are measured facts; the blocker reading is interpretation).

---

## Incidents / deviations

- Check 1 first exploratory run exited 1 (`IndexError` — no column literally named `*date*` besides `observation_period`); adapted and re-ran clean (exit 0). No data touched.
- Check 3: anticipated column-name deviation (`report_date_as_yyyy_mm_dd` absent; used loader-derived `obs_date`). Loader untouched.
- Check 5: statistics schema has no venue column; venue-OI interpreted via stat_type==9 with latest-publication dedupe as specified. Reported as found.
- No writes outside `analysis/verify/` + `dispatch/handoff_DC-VERIFY.json`. No commits, no pushes, no network.
