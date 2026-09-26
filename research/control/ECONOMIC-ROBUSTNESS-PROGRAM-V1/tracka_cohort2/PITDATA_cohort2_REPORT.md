# PITDATA_cohort2_REPORT — ERP1-TRACKA-COHORT-2 — Lane A (PIT/data auditor)

- Cycle: `ERP1-TRACKA-COHORT-2` (registry row 69: ACTIVE_LIGHT, phase REGISTERED, s1 `SEALED_UNTOUCHED`, budget 0/18)
- Role: outcome-blind PIT/data auditor. **No PnL-bearing artifact was opened**: cohort-1 `SCORED_REPORT.md`, `scored_*.json`, `series/*`, `trial_ledger.jsonl`, and MAP outcome bullets were NOT read. All reads below are structural (schemas, row counts, timestamp bounds, sha256, JSON keys, gate fields).
- Measured HEAD (root `main`): `3de439ab988d82cd246731ae6c277a688f6e2c31`. Cohort-1 integration worktree measured HEAD: `fa93b8071a0a34ebf2dd50f8147dbe3d30cc25bc` (branch `orca/erp1-tracka-cohort-1-integration` — matches the registry TERMINAL row exactly). Heavy lock: `FREE_PROVEN` (no conflict, no worker started).
- Data authority resolution location (P-13): `/Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1/integration/research/control/ERP1-TRACKA-COHORT-1/` (`data_local/`, `freeze/`, `scripts/`).

## A1 — Corpora re-resolution (P-13 law): PASS

Corpus root: `.../ERP1-TRACKA-COHORT-1/data_local/`. Raw `duka/M1/{BID,ASK}/{SYMBOL}/`: **2,007 day files per side per pair** (4,014/pair), 0 missing days, manifests committed. Derived (pyarrow structural scan, 2026-09-26):

| file | rows | ts min (UTC) | ts max (UTC) | rows ≤ 2025-12-31 | rows > 2025-12-31 (2026-H1) | dup ts | monotonic |
|---|---|---|---|---|---|---|---|
| bars15_AUDUSD.parquet | 130,160 | 2021-01-03 22:15 | 2026-06-30 23:45 | 118,275 | **11,885** (first 2026-01-01 22:30) | 0 | true |
| bars15_USDCAD.parquet | 130,102 | 2021-01-03 22:15 | 2026-06-30 23:45 | 118,231 | **11,871** (first 2026-01-01 22:15) | 0 | true |
| bars15_ANC_AUDUSD.parquet | 130,160 | same ts set as bars15_AUDUSD (verified equal) | | 118,275 | **11,885** | 0 | true |
| bars15_ANC_USDCAD.parquet | 130,102 | same ts set as bars15_USDCAD (verified equal) | | 118,231 | **11,871** | 0 | true |
| bars1h_AUDUSD.parquet | 30,420 | 2021-01-03 23:00 | 2026-06-30 20:00 | 27,608 | **2,812** (first 2026-01-01 23:00) | 0 | true |
| bars1h_USDCAD.parquet | 30,386 | 2021-01-03 23:00 | 2026-06-30 23:00 | 27,583 | **2,803** (first 2026-01-01 23:00) | 0 | true |
| bars1h_ANC_AUDUSD.parquet | 30,420 | same ts set as bars1h_AUDUSD | | 27,608 | **2,812** | 0 | true |
| bars1h_ANC_USDCAD.parquet | 30,386 | same ts set as bars1h_USDCAD | | 27,583 | **2,803** | 0 | true |

Schemas: 15m = `ts (timestamp[ms, tz=UTC]), b_o,b_h,b_l,b_c, a_o,a_h,a_l,a_c, s_open, s_close`; 1h = same minus `a_h, a_l` (H1 valid iff exactly 4 consecutive 15m bars, per census law). ANC↔port timestamp sets verified byte-equal (4/4 true); only the `b_h` construction differs (ancestor close-column high), per the freeze artifact `plane_semantics_pin`.

**Window verdict**: panel covers 2021-01-03 22:00Z .. 2026-06-30 23:59Z (2,007 days, census `first_ts`/`last_ts`), i.e. dev 2021-01..2025-12 plus the full 2026-H1 holdout window. **ALL EIGHT parquets physically contain 2026-H1 bars; NO parquet is holdout-free.** The dev/holdout seam is therefore NOT physical — it is enforced by the timestamp filter `ts <= 2025-12-31 23:59:59 UTC`, which is deterministic and reproducible because every file is strictly monotonic-increasing with 0 duplicate timestamps. Seal enforcement condition for every dev consumer: apply the mask, then assert `max(ts) <= 2025-12-31 23:59:59 UTC` and row counts {118,275 / 118,231 / 27,608 / 27,583}. Any row count mismatch ⇒ the plane changed ⇒ fail-closed.

**Census keys (schema `tracka_census@2`, both pairs, verdict `BUILD_PASS`)** — cost authority that exists:
- **Per-session spread curves** (the sole cost authority; fill-bar's own measured spread × k∈{1.0, 1.5, 2.0}): 8 fixed-UTC buckets `asia_00_07, london_07_12, ny_overlap_12_16, ny_late_16_21, rollover_21_22, late_22_24, friday_20_23_open, sunday_open_21_22`, each with n + OPEN and CLOSE quantiles (p50/p75/p90/p95/p99, pips). Overall OPEN p50/p99: AUDUSD **1.0 / 4.1** pips; USDCAD **1.2 / 6.2** pips. Tail buckets: sunday_open AUDUSD p50 4.6 (p99 14.789), USDCAD 6.8 (p99 21.38); friday AUDUSD 1.1, USDCAD 1.3. Per-bucket p50 table in DATAGATE_REPORT §"Session-spread census" (AUDUSD rollover 2.0, USDCAD 2.3). Rollover bucket n = 3,497 / 3,680; sunday-open cell n = 312 / 321 — both above the n=100 floor, `LOW_SAMPLE_BUCKET` fired on no bucket.
- **DST fixtures**: `gap_census.dst_shift_table` = 24 US/EU transition Sundays; **22 in-panel** with observed first-Sunday-bar UTC hour (21↔22 across the US DST regime — vendor convention recorded, not assumed); 2 future (2026-10-25, 2026-11-01) `in_panel=false`, hour null.
- **Rollover fixture**: dedicated `rollover_21_22` bucket, count assert > 0 green (`fixture_asserts.rollover_bucket_count_gt_0`).
- **Weekend/holiday fixtures**: 286 Friday→next-open boundaries per pair, gap p50 48.5 h, min 47.25/47.5 h, max 73.25/73.0 h (long weekends); zero-tradable days = 288 weekend + **exactly 1 weekday holiday (2021-01-01)**; 0 missing days.
- **Integrity fixtures**: micro-gaps 6,051 / 5,930 interior slots (~3/day); `nonpos_spread_minutes` = 0; `price_range_violations` = 0; reconcile max diff **0.0 pip** (tolerance 5e-4), `pass: true`.
- Embedded `pair_config` (pip/price_scale/band + probe provenance) and `data_manifest` (bars15/bars1h rows, m1_manifest sha, day_files=2007).

No price statistics were computed in this audit (timestamp bounds and counts only; spread pips are costs, which is the authorized content).

## A2 — Freeze-pin re-resolution: PASS (parquet scope documented)

Pin source: `.../ERP1-TRACKA-COHORT-1/freeze/GO1_freeze_artifact.json` (`cost_book`), + `scripts/pair_configs.json` (probe pins). Measured sha256 (current bytes) vs pins:

| file | pin field | pinned sha (head) | measured sha (head) | verdict |
|---|---|---|---|---|
| census_AUDUSD.json | GO1 `cost_book.census_sha256.AUDUSD` | `d337ff2c4e499238…` | `d337ff2c4e499238…` | **PASS** (exact) |
| census_USDCAD.json | GO1 `cost_book.census_sha256.USDCAD` | `27958f5a6b67ae01…` | `27958f5a6b67ae01…` | **PASS** (exact) |
| m1_manifest_AUDUSD.json | GO1 `cost_book.m1_manifest_sha256.AUDUSD` | `f869cfa32210194c…` | `f869cfa32210194c…` | **PASS** (exact) |
| m1_manifest_USDCAD.json | GO1 `cost_book.m1_manifest_sha256.USDCAD` | `0f9a7df78bcaf481…` | `0f9a7df78bcaf481…` | **PASS** (exact) |
| probe_AUDUSD.json | `pair_configs.json` `probe_report_sha256` | `fe54fe4ccda1ceae…` | `fe54fe4ccda1ceae…` | **PASS** (exact) |
| probe_USDCAD.json | `pair_configs.json` `probe_report_sha256` | `dcd706be501a8dd6…` | `dcd706be501a8dd6…` | **PASS** (exact) |

**Parquets**: the cohort-1 freeze dir holds **no byte-level sha pins for parquets** (they are machine-local by `data_local/derived/.gitignore`: `*.parquet`; committed authority = census JSONs + manifests). Their **structural pins** in GO1 `plane_semantics_pin.verification` — `bars15_rows` 130,160/130,102, `bars1h_rows` 30,420/30,386, ANC↔port `ts_sets_equal: true` — are all re-verified against current files: **PASS**. To close the pin gap for cohort-2, this lane measured and records the current parquet sha256 as the resolution anchor (recorded here; the cohort-1 freeze artifact was NOT modified — read-only):

- bars15_AUDUSD `17f07ab11f959ef2f90bac0fa937f595704e7b015b741f8254a32e6db38fd343`
- bars15_USDCAD `806a5e45dbadd4c8756b2a20de296b3f4a3087de3f665f4ccf5924894315e08f`
- bars1h_AUDUSD `2a346e028f3867b892d3cfd0e1df33677fd5a6e2948ea93249e1406899a90344`
- bars1h_USDCAD `c2d9fdb641afbe2a842113a03fca30ba2aca6ca8cffa739bd7af52d564e126de`
- bars15_ANC_AUDUSD `79ad8eeed709fdd91e0177d0800a9bc8ab01a2b07f8c385e90c49d854c43e435`
- bars15_ANC_USDCAD `b0f68d00c8fa55ca6a1883f11d2af853504bcdad3dff5a45bdd2ed26ab05156c`
- bars1h_ANC_AUDUSD `4e0ca174a21e155271a481727259daa0d3df888bb9f96eb7a34d8c6f06881364`
- bars1h_ANC_USDCAD `335a6e2aab25aebff17f9198f1b939448262186ed20e63f3041f8818d02f376b`

**P-13 archive-location note (recorded)**: cohort-2 inherits the census/manifest/probe pins AND the parquet anchors above; the resolution location is the cohort-1 worktree `/Users/hoangminhlong/my-quantitative/.worktrees/erp1-tracka-cohort-1/integration/research/control/ERP1-TRACKA-COHORT-1/`, per the registry TERMINAL row (cycle 68: lifecycle TERMINAL, phase CLOSED_REJECT_ALL, `integration_worktree` path, head `fa93b807…`, go-phrase state DEAD). Cohort-2 consumes only the data/cost/pin assets of that row — never its scored outputs.

## A3 — Exposure ledger (structural): PASS

Authority: `plans/CYCLE_REGISTRY.json` (phase fields) + `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/forex_program/LESSON_TO_GATE_MATRIX.md` outcome-exposure map (binding for every child plan). Cohort-1 `trial_ledger.jsonl` was **not opened** (no-PnL honored); exposure state below is taken from the matrix + registry only.

| Surface | Exposure state (matrix, verbatim class) | Permitted use |
|---|---|---|
| AUDUSD / USDCAD, dev 2021-01-01..2025-12-31 | **OUTCOME-EXPOSED for the range-fade class** (cohort-1 M1 arms R-ANCHOR/R-ORIG/R-NEIGH/placebo/inverted/baselines scored there) | Dev surface only for mechanisms with a NEW observable never searched there (D2 adjudicates + ancestry rho); fixture; cost authority |
| AUDUSD / USDCAD, holdout 2026-01-01..2026-06-30 | **SEALED — UNREAD** (A7 terminal C-3, `HOLDOUT_UNREAD_CONSUMED_BY_NONE`; no cohort-1 arm looked) | One-look OOS for a new identity only: full dev gates, separate GO, membership frozen pre-pass |
| EURUSD / GBPUSD / USDJPY, 2021-01..2026-06 | OUTCOME-EXPOSED (V1/V2/RANGEEXP-SCORED/FX-MAJORS + 12-family census; holdouts consumed) | **Ancestry-only**: (a) ancestry disclosure, (b) engine-parity fixture, (c) spread-curve/cost authority. Never new evidence/OOS |
| 12 FX census families | OUTCOME-EXPOSED on EURUSD/GBPUSD/USDJPY dev outcomes | Failure memory + ancestry rho shadows; no re-selection from remembered dev PnL |
| USDCHF | OUTCOME-FREE, **not downloaded**; download requires owner amendment **D2-2** (GO1_RECORDED `forbidden_and_stopped_at`: "NO USDCHF download (D2-2 NOT GRANTED)") | Full replication-transfer surface only after data gate + owner slate amendment |

Registry corroboration: cohort-1 row TERMINAL/CLOSED_REJECT_ALL with s1 `SEALED_UNTOUCHED`; cohort-2 row ACTIVE_LIGHT/REGISTERED with s1 `SEALED_UNTOUCHED`, go-phrase `REGISTERED_NOT_CONSUMED`, budget 0/18. Consistency check passed: the freeze artifact `windows` block states dev `2021-01-01..2025-12-31` (folds F1..F6 ending 2025-12-31) and `holdout_untouched_here: 2026-01-01..2026-06-30` — matching the matrix and the physical parquet seams measured in A1.

## A4 — F-2 PIT-audit contract (per candidate; executes for EVERY new signal code, child plan §8 F-2)

Standing context for all items: planes = cohort-1 corpus (A1); **dev mask = `ts <= 2025-12-31 23:59:59 UTC`** applied before any computation, with the row-count assertion of A1; warmup 61 traded days; folds F1..F6 frozen; holdout files are never opened pre-GO (one-look law, membership frozen before any pass). "Byte-identical" = identical after canonical serialization of the decision record (ts, arm, direction, size, reason code) with fixed key order.

**(i) Independent-implementation equivalence (M-1).**
Procedure: a second implementation of the candidate's signal law is written from the frozen law SPEC (not from candidate source) in a separate lane/context; both implementations run on the identical dev-masked 15m/1h planes; full decision series compared element-wise.
Pass: 100% identical decision series on the dev window; any divergence > 0 on the frozen signal voids the artifact and routes to `KILL_PIT_SEAM` (L1 law).
Artifact: both series files (sha256), the diff report, independent impl code path + sha, spec sha.

**(ii) Mutation non-vacuity ≥ 2% (M-2 + freeze pin iii).**
Procedure: every mutation used in (iii)/(iv) and every mode-sham/shuffle placebo is first calibrated: the mutated input must change ≥ 2% of decision-vector elements (or ≥ 2% of matched-pair labels for the mode channel) on the dev window. Calibration runs on a deliberately-leaky harness variant to prove the mutation can move a downstream consumer.
Pass: ≥ 2% changed per mutation; a mutation moving < 2% is VACUOUS — the test is `NOT_RUN` and must be re-specified stronger before it counts; mode-channel non-vacuity failure < 2% ⇒ `KILL_VACUOUS_MUTATION` per freeze pin (iii).
Artifact: mutation manifest (spec, seed, harness, pct-changed per mutation).

**(iii) Panel-truncation replay (M-5).**
Procedure: for every decision time t_d (exhaustive where compute allows; otherwise a seeded stratified sample that MUST include all fold boundaries, all day-start decisions, and ≥ 200 seeded-random decision times), rebuild the panel truncated at `ts <= t_d`, re-run the frozen signal end-to-end, and compare the decision at t_d and the entire prefix against the full-panel run.
Pass: byte-identical output at every t_d — ANY divergence > 0 voids the artifact + `KILL_PIT_SEAM` (cohort-1 M-5 precedent: R-ORIG diverged on 72–75% of replays).
Artifact: replay matrix (t_d, full-panel decision hash, truncated hash, identical flag), sample spec + seed, hashes of both full runs.

**(iv) Future-data mutation test.**
Procedure: for the same stratified sample of t_d, deterministically mutate ALL bars with `ts > t_d` (pinned seed; magnitude from the (ii) calibration so it provably moves any downstream aggregate), re-run the frozen signal on the mutated panel, compare t_d output and prefix.
Pass: output unchanged (byte-identical) at every tested t_d; mutation proven non-vacuous per (ii) on the leaky harness.
Artifact: mutation spec + seed, before/after decision hashes per t_d, calibration evidence.

**(v) Day-boundary variable audit (the RANGEFADE leak class, L1).**
Procedure: enumerate every variable/state the candidate reads or materializes; classify each by window bounds; for every day-start (first-decision-of-traded-day) evaluation, prove each consumed variable is computable strictly from bars with `ts <` that day's start (completed previous day(s) or explicitly lagged series). Any same-day statistic (full/partial-day range percentile, day high/low, day VWAP, session aggregate ending at/after the decision) consumed at a day-start or early-day decision = leak. Dynamic probe: recompute each day-start decision from data truncated at that day's start (ties into (iii)).
Pass: zero same-day statistics in any day-start decision; all feature windows documented and lagged correctly.
Artifact: feature inventory (name, window bounds, boundary law, lag, PASS/FAIL) — feeds the (vi) table.

**(vi) Timestamp authority table per feature (P-1 law).**
Procedure: one row per feature/event: event time, effective time, available time, join law (bar-close vs as-of), timezone law (UTC fixed; DST handled only via the observed Sunday-open hour fixtures of A1), lag in bars, holiday/weekend rule, missing-data rule. Each row carries `EVIDENCED / ASSERTED / UNEVIDENCED`.
Pass: for every feature, `available_time <= decision time` is provable from plane timestamps; bar-close joins consume CLOSED bars only (H1 signal on closed H1 bar, fill at next H1 open, per freeze pin iv UTC-close semantics); any `ASSERTED` availability makes the item `NOT_RUN` (fail-closed, never inferred PASS).
Artifact: the committed table with the EVIDENCED column.

**(vii) DST / rollover / holiday fixture list (from census keys — the falsifier asserts against these).**
Fixtures: (a) 22 in-panel DST transition Sundays with observed first-Sunday-bar UTC hour 21/22 (`gap_census.dst_shift_table`, both pairs same pattern); synthetic force-flat DST tests for Sunday-open shapes 21/22/23 UTC exist in `tests/test_engine.py` and must run green; (b) `rollover_21_22` cost bucket (n=3,497/3,680) applied whenever a fill lands there; (c) `sunday_open_21_22` cell (n=312/321) — Sunday fills priced from the Sunday curve, never the weekly p50; (d) `friday_20_23_open` bucket; (e) 286 weekend boundaries, gap p50 48.5 h / max 73.25/73.0 h — no decisions or fills in non-tradable slots; (f) holiday 2021-01-01 (only weekday zero-tradable day); (g) micro-gap rule (interior holes ~3/day) — missing-bar handling must be the census rule, not silent forward-fill.
Pass: signal runs green on all fixtures; no decision/fill in any non-tradable slot; correct cost bucket at every fill timestamp.
Artifact: fixture-run log keyed to the census fields + the enumerated list above.

**(viii) Blind-packet verification — EXECUTED, PASS.**
`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort2/PACKET_dead_family_labels.json` (sha256 `27764e4491c04b2a51ed0f78367eb5b81b3de1f93c3c0250b677b45e4112e3dd`) was fully scanned: schema `erp1_tracka_cohort2_blind_packet_deadfamilies_labels@1`; top keys `schema, note, count, families`; `families` = 129 entries; **exactly one numeric leaf in the whole document (`/count = 129`, a list cardinality)**; 776 string leaves = family ids/titles/verdict classes/failure codes; zero matches on the outcome-keyword regex (pnl/profit/pf/win_rate/wr/sharpe/expectancy/net/return/drawdown/equity/score/gain/loss). The packet is label-only as its own note declares. Standing rule for the falsifier phase: re-scan the packet sha before every proposer dispatch; proposers may not seek numeric outcomes; any numeric outcome appearing in a packet voids the blinded lane.

Riders carried verbatim from child plan §8 F-2: daemon-seam emulation (M-3) is N/A unless the candidate is consumed by a shadow/third law — if it is, emulate partial-panel daemon consumption and require the shadow law to be the same law; self-test-blindness fixture (M-4): same-function/same-panel parity is never semantic evidence; self-tests must be structurally blind to the seam class.

## A5 — Data gates for cohort-2: PASS

**No new downloads are authorized.** USDCHF (and any unsearched pair) is gated behind a separate owner amendment (D2-2); `GO1_RECORDED.json` explicitly forbids the USDCHF download at GO-1. Independent sources remain BLOCKED (D-C posture; Twelve Data = mid-price reconciliation-only). All verdicts keep the `SINGLE_SOURCE_PANEL` label.

**Gates carrying over BUILD_PASS from cohort-1** (source: cohort-1 `DATAGATE_REPORT.md` — verdict line "DATA GATE GREEN", census `verdict: BUILD_PASS` re-read from the pinned census bytes today), per pair AUDUSD and USDCAD:
1. `midweek_tradable_share_gt_0.90` — 0.98611 / 0.98607 (margin +0.08611 / +0.08607)
2. `nonpos_spread_share_lt_1pct` — 0 nonpositive-spread minutes (margin +0.01000)
3. `bars15_gt_100k` — 130,160 / 130,102 bars (margin +30,160 / +30,102)
4. `duplicate_15m_ts_eq_0` — 0 duplicates (fail-closed), re-verified today
5. `reconcile_p50_within_rounding` — max diff 0.0 pip ≤ 5e-4
Plus: `PROBE_PASS` (scale/pip/band derivation from probe bytes), corpus manifest integrity (re-verified vs pins today, A2), census schema `tracka_census@2` committed, and the full panel 2021-01..2026-06 with 0 missing days.

**Per-pair fixtures already existing** — `.../ERP1-TRACKA-COHORT-1/scripts/pair_configs.json` verified present, probe-proven (`proven: true`), probe-report shas match current bytes:
- AUDUSD: pip 0.0001, price_scale 100000.0, band [0.5209, 0.85]
- USDCAD: pip 0.0001, price_scale 100000.0, band [1.1057, 1.6751]

**What a NEW signal must additionally fixture** (beyond inheriting the above):
1. Fail-close on missing/unproven pair config (`load_pair_config` → `FAIL_CLOSED`); no engine code may run without the probe-proven config.
2. Dev-mask enforcement + assertion (A1 counts) before any computation; holdout never read pre-GO.
3. Plane semantics: ANC plane for the signal plane, port true-H/L bars remain the COST plane (freeze `plane_semantics_pin.decision_rule`); spreads bit-identical across conventions (max abs diff 0.0 verified at freeze).
4. Cost book: per-session census spread at the fill bar's own timestamp × k∈{1.0, 1.5, 2.0}; no global p50; ceiling arithmetic (F-5) before any PnL.
5. UTC-close semantics (freeze pin iv): signal on CLOSED H1 bar, fill next H1 open at opposite quote; no fills on/after the 19:00 H1 bar; force-flat at 20:00 UTC; weekend flat; structural-zero financing.
6. Window machinery: warmup 61 traded days; folds F1..F6; F-2 battery items (i)–(viii) above; F-3 clock-placebo + mode-sham with non-vacuity; F-4 beta baselines (AUDUSD → SHORT_ALWAYS, USDCAD → LONG_ALWAYS); seam-law constants (c_rt base book: AUDUSD 2.0 pips, USDCAD 2.4 pips; limb-3 min N 20, fail-closed).
7. Exposure labels on every artifact (ancestry disclosure per child plan §3); blind packets label-only (item viii).

## Conditions for the falsifier phase

1. Resolve all planes ONLY at the P-13 archive location (A2) and re-verify the A2 pins (census/manifest/probe byte pins; parquet structural pins + recorded sha anchors) before the first F-2 run; mismatch on any pin ⇒ fail-closed.
2. Every dev computation starts from the mask `ts <= 2025-12-31 23:59:59 UTC` and asserts the A1 dev row counts {118,275 / 118,231 / 27,608 / 27,583}; holdout rows physically present in all eight parquets must never be read pre-GO; the one-look holdout pass requires frozen membership artifact sha before the pass.
3. Execute F-2 items (i)–(viii) for EVERY new signal code, in the plan §8 order F-0 → F-1 → F-2..F-7, before the first scored cell; any (iii)/(iv) divergence > 0 or any (v) same-day statistic ⇒ artifact void + `KILL_PIT_SEAM`; any ASSERTED availability in (vi) ⇒ `NOT_RUN`.
4. Re-scan `PACKET_dead_family_labels.json` (expect sha `27764e44…`, single numeric leaf `/count`) before each proposer dispatch.
5. No downloads; USDCHF only after D2-2 owner amendment + full cohort-1 §5.2 data gate.
6. Cost authority = the pinned per-session census curves × k∈{1.0,1.5,2.0} at fill-bar timestamps; F-5 ceiling pre-PnL.
7. Record any pin divergence, seal-breach suspicion, or vacuous-mutation finding as an incident in the lane handoff — missing evidence is `NOT_RUN`, never inferred PASS.

— Lane A (pit-data-auditor), 2026-09-26. Outcome-blind honored: zero PnL-bearing bytes read.
