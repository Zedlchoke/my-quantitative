# FALSIFIER-2 PREP REPORT — ERP1-TRACKA-COHORT-2 — FALSIFIER2_PREP_REPORT.md

- Lane: `impl-falsifier-prep` (A8-style engineering / falsifier prep)
- task_id: `tracka2-impl-falsifier-prep`, cycle `ERP1-TRACKA-COHORT-2`
- Worktree: `.../erp1-tracka-cohort-2/integration`, branch
  `orca/erp1-tracka-cohort-2-integration`, actual_start_sha =
  `5ed2457be9a7b6550406e1f34a78e6a2fc3540b2` (measured, = dispatch sha)
- HARD LAWS honored: **no PnL exists anywhere in this lane's code, runs or
  artifacts** (engine runs were used ONLY to extract trade counts, entry/
  exit timestamps and fill-hour histograms; the engine's pips/px/equity
  outputs were stripped at source and the equity curve discarded unread —
  enforced in code by `f6_census._assert_clean` over the persisted JSON);
  **the sealed window 2026-01-01..2026-06-30 was never read** (every plane
  came through `scripts/dev_plane2.py` with its row pins; during the M1
  aggregation pass, only day files containing dev bars were opened — 2026
  day files were never opened); **both laws are implemented from the frozen
  proposal texts**, with every ambiguity quoted and resolved below (no
  silent picks).

## 1. What was built (committed paths, lane-relative)

| Path | Content |
|---|---|
| `scripts/qcrd_dinv_lib.py` | The two frozen candidate laws + declared twins as pure functions df -> int8 target array; docstring transcribes each frozen constant with its proposal-text source. Also hosts the TRACKA1-M3 spread-gated-fade shadow builder. |
| `scripts/build_t2_planes.py` | Heavy build: M1 aggregation (sha-verified read-only against the cohort-1 archive, machine-wide heavy lock `impl-t2-planes`), candidate target arrays + all named shadow arrays on the dev H1 grid, `data_local/derived/t2_planes_manifest.json` (row pins, per-array sha256, shadow status, code shas, warmup index, frozen fold table). |
| `scripts/run_f2_battery.py` | Runs `pit_battery2` (M-T/M-F/M-V) on both anchors + twins on both pairs + the disclosed M-F extension; writes `falsifier/F2_battery_results.json`. |
| `scripts/f6_census.py` | Fold-population census, counts only; writes `falsifier/F6_census_counts.json`. |
| `tests/test_t2_laws.py` | Fixtures (a)-(d) below. 13/13 lane tests PASS (6 pre-existing pit-battery fixtures + 7 new). |
| `data_local/derived/m1agg_{SYM}.parquet` | Per-dev-H1-bar M1 aggregates (cache). |
| `data_local/derived/t2_p3a_{SYM}_{arm}.npy`, `t2_p3b_{SYM}_{arm}.npy`, `t2shadow_{name}_{SYM}.npy` | int8 target/shadow arrays (shas pinned in the manifest). |
| `falsifier/F2_battery_results.json`, `falsifier/F6_census_counts.json` | Battery + census artifacts (counts only). |
| `handoffs/HANDOFF_impl_falsifier_prep.json` | Structured handoff `zcode_orch_v3_handoff@1`. |

## 2. Dev planes and the sealed law

- `bars1h_ANC` dev rows (pin asserted by the loader, fail-closed):
  **27,608 AUDUSD / 27,583 USDCAD**; `bars15_ANC` dev rows **118,275 /
  118,231** (asserted when the M3 shadow loaded the 15m plane).
- M1 raw bytes: read-only from the cohort-1 archive
  `.worktrees/erp1-tracka-cohort-1/integration/.../data_local/duka/M1`
  (path override recorded; bytes never copied). Every day file sha256-
  verified against the cohort-1 manifests (AUDUSD `f869cfa3…`, USDCAD
  `0f9a7df7…`). Only day files containing dev bars were opened.
- M1 aggregate per valid dev H1 bar over its 60 consecutive tradable
  minutes (hard gate `nmin == 60`; 0 violations on both pairs): sum of the
  59 intrabar dlog mid closes, its absolute-sum, median minute relative
  spread, minute count. Cached as `m1agg_{SYM}.parquet` (manifest sha).

## 3. Frozen laws as implemented (constants + citation)

**P3-A `TRACKA2-P3A-QCRD-H1`** (home AUDUSD; replicate USDCAD) — decision at
each closed H1 bar with close time τ_t ∈ [01:00, 19:00] UTC (= bar-open
hours 0..18): LONG next bar iff S_t ≥ +0.25 AND P_t ≤ 0.40; SHORT iff
S_t ≤ −0.25 AND P_t ≤ 0.40 (PROPOSAL A field 5, verbatim transcription in
the lib docstring). S_t = signed efficiency ratio of the bar's M1 mid
closes; P_t = empirical percentile of the bar's median minute spread within
the trailing same-clock-hour pool over the previous 60 calendar days,
strictly past. Warmup 61 traded days flat (SKEPTIC §3.1.1). Array
convention per SKEPTIC §4: sign at the decision bar, filled next bar.

**P3-B `TRACKA2-P3B-DINV-1D`** (home USDCAD; replicate AUDUSD) — decision at
the 20:00 UTC close of day d: LONG next traded day open iff S_d ≥ +0.20 AND
P_d ≤ 0.40; SHORT iff S_d ≤ −0.20 AND P_d ≤ 0.40 (PROPOSAL B field 5);
position held on the next session day's 00:00→20:00 bars (engine enters at
the day's first session bar and force-flattens at its 20:00 close); S_d =
signed efficiency ratio over the day's H1 mid closes; P_d = percentile of
the day's median H1 s_close within the trailing 60 same-weekday days
(strictly past; resolution R4 below). Days without both the 00:00 and the
19:00 (20:00-close) session bars are not decided (fail-closed flat). Warmup
61 traded days (SKEPTIC §3.2).

Target-array nonzero counts (full dev panel, incl. non-fillable carry bars
for P3-B — §5.2): P3-A anchor 1,171 AUDUSD / 1,229 USDCAD; P3-B anchor
6,001 AUDUSD / 4,540 USDCAD (≈ decision day-close bar + position-day
session bars per fired day). All array sha256s pinned in the manifest.

## 4. F-2 PIT battery (falsifier/F2_battery_results.json)

Harness: inherited `scripts/pit_battery2.py` (unchanged, sha in the JSON).
Seed 20260926; 24 truncation points per M-T; decision masks per dispatch:
P3-A in-session 7..18 UTC, P3-B traded-day decision bars (hour 19).

| Law / pair | M-T | M-F | M-F-ext | M-V twins (share) | Verdict |
|---|---|---|---|---|---|
| P3-A / AUDUSD | PASS (0 diff) | PASS (0) | PASS (0) | index_shift_pool 0.032, mirror_wide 1.000, volgate 0.690, ungated 0.577 | **PASS_PIT** |
| P3-A / USDCAD | PASS (0) | PASS (0) | PASS (0) | 0.027 / 1.000 / 0.690 / 0.559 | **PASS_PIT** |
| P3-B / AUDUSD | PASS (0) | PASS (0) | PASS (0) | weekday_shuffle 0.831, mirror_wide 1.000, ungated 0.528 | **PASS_PIT** |
| P3-B / USDCAD | PASS (0) | PASS (0) | PASS (0) | 0.862 / 1.000 / 0.625 | **PASS_PIT** |

All mutation twins clear the ≥2% non-vacuity floor. The weakest twin is
P3-A `index_shift_pool` (pool window shifted one calendar day): 2.7–3.2% of
the union pool moves — above the floor, mechanically consistent with a
±1–2-of-~60 entry pool perturbation.

**M-F dual run (disclosed).** The frozen harness's `future_mutation_test`
mutates a fixed 6-column price list, which cannot perturb M1-derived inputs
(P3-A consumes ONLY M1 aggregates; P3-B also consumes `s_close`). This lane
added `future_mutation_test_ext` — identical logic, seed and perturbation,
with the M1 aggregate columns and `s_close` appended to the mutation list —
and requires BOTH to pass. Both pass everywhere. The frozen harness file
was not modified.

**Leak-class proof on these laws' own code (tests).** Deliberately leaky
variants (P3-A: percentile pool = whole panel incl. the decision bar and
future bars; P3-B: future-window re-anchored same-weekday pool, decision
day included) FAIL M-T (`KILL_PIT_SEAM`) while the clean laws pass —
fixtures `test_b_*`. Wide-mirror non-vacuity on synthetic data: fixture
`test_c_*`. Warmup boundary: nothing fires while session-day ordinal < 61;
forced-fire fixtures confirm firing begins exactly at ordinal 61
(`test_d_*`).

## 5. Fold-population census — counts only (falsifier/F6_census_counts.json)

Frozen fold table (by traded-day count, `np.array_split`, identical for
both pairs): F1 2021-01-04..2021-11-02 (217d), F2 2021-11-03..2022-09-01
(217d), F3 2022-09-02..2023-06-30 (216d), F4 2023-07-03..2024-05-01
(216d), F5 2024-05-02..2025-03-03 (216d), F6 2025-03-04..2025-12-31
(216d). Warmup index (first decision-eligible bar): 1,334 AUDUSD / 1,307
USDCAD (inside F1). Engine: inherited `run_strategy`, k=1.0, warmup
honored; equity/pips discarded at source; counts attributed by entry day.

Round trips (per fold; last-6-months dev window = 2025-07-01..2025-12-31):

| Book | F1 | F2 | F3 | F4 | F5 | F6 | last-6m | **Total** | floor ≥100 RT | span days | floor ≥6m |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P3-A / AUDUSD (home) | 85 | 131 | 233 | 168 | 185 | 247 | 137 | **1,049** | PASS | 1,722 | PASS |
| P3-A / USDCAD | 79 | 178 | 194 | 235 | 185 | 242 | 164 | **1,113** | PASS | 1,736 | PASS |
| P3-B / USDCAD (home) | 18 | 4 | 42 | 84 | 39 | 39 | 39 | **226** | PASS | 1,729 | PASS |
| P3-B / AUDUSD | 28 | 9 | 42 | 94 | 70 | 50 | 46 | **293** | PASS | 1,721 | PASS |

All four books clear both adjudication floors (≥100 RT total AND ≥6 months
of entries). Decision-bar / occupied-bar counts per fold are in the JSON
(P3-A: e.g. last-6m 2,442 decision bars / 152 occupied on AUDUSD; P3-B:
last-6m 129 decision days / 775 occupied bars on USDCAD).

### 5.1 Fill-hour histograms — gated (anchor) entries, UTC entry hour

Lane-C pricing input (conditional-bucket keyed). Full-window → counts:

- **P3-A / AUDUSD** (entry bar = decision bar + 1; hour-19 fills dropped by
  the inherited engine): {1:62, 2:56, 3:51, 4:57, 5:67, 6:55, 7:69, 8:52,
  9:54, 10:52, 11:45, 12:50, 13:69, 14:75, 15:62, 16:66, 17:47, 18:59,
  0:1}. Last-6m spread roughly uniform over hours 1..18.
- **P3-A / USDCAD**: {1:72, 2:68, 3:41, 4:46, 5:56, 6:69, 7:71, 8:58,
  9:59, 10:61, 11:53, 12:60, 13:72, 14:63, 15:66, 16:61, 17:65, 18:72}.
- **P3-B / USDCAD** (day-open entries): {**0:205**, 1:20, 4:1}. Last-6m:
  hour 0 × 39 (all of them). The hour-1 entries are days whose 00:00 H1
  bar is invalid in the plane (day's first session bar is 01:00) — the law
  enters at the day's open, wherever it falls.
- **P3-B / AUDUSD**: {**0:286**, 1:7}. Last-6m: 0:3, 1:42, 2:1.

## 6. Shadow construction (F-1 fixtures, arrays + status in the manifest)

Per pair, **47/47 shadows constructed — 0 NOT_CONSTRUCTIBLE** (status per
array with sha256 in `t2_planes_manifest.json`):

- **R-ANCHOR** (`f_rangeexp_anchor_shift`) and **R-ORIG**
  (`f_rangeexp_orig`) — local `tracka_lib.py` (sha `1e09b368…`, the
  A7-certified bytes pinned by `freeze/ENGINE_INHERITANCE_shas.txt`) on the
  dev ANC signal plane via `SignalPlane` (cohort-1 convention), default
  frozen band lo_q=0.3/hi_q=0.7.
- **TRACKA1-M3 spread-gated-fade shadow** — CONSTRUCTIBLE. Implemented from
  the skeptic §4 spec ("spread ≤ same-hour p60 gate on the band-fade law:
  absorb prev-day-band breaks only when just-closed break hour's median
  spread ≤ trailing 20-trading-day same-hour p60"): base = R-ANCHOR
  fade-arm days only; break entries at bar i absorbed iff the hour's median
  15m s_open (built on the same dev grid from `bars15_ANC`, dev-pinned) ≤
  quantile(pool, 0.60) over the same-hour values of the previous 20 traded
  days, strictly past; NaN spread / empty pool ⇒ no entry (fail-closed).
  Nonzero: 4,827 AUDUSD / 4,421 USDCAD. Declared conventions (the cohort-1
  M3 code itself was not ported into this worktree): hour spread = median
  of the hour's four 15m `s_open`; p60 = `np.quantile` linear; base law =
  the certified PIT form R-ANCHOR.
- **11 census families × C1..C4** — `v2_lib.py` (sha `efb87e37…`) imported
  VERBATIM from the EURUSD-OPEN-SEARCH-V2 worktree, binding its own
  ancestor engine (import-order law asserted in code: `E.PIP = 1e4` equals
  both pairs' pip multiplier, so numerics equal the census spec), with the
  FROZEN configs of `v2_campaign.py` (sha `6147beff…`) passed positionally
  exactly as v2_campaign's lambdas do (config key names `min_past`/`atr_n`
  differ from v2_lib's parameter names — resolved by positional passing,
  not renaming). Families: FX2-GAP, FX2-PDHLOC, FX2-DOW, FX2-ASIAFADE,
  FX2-SESSMA, FX2-H1TSMOM, FX2-H1DONCH, FX2-DAYMOM, FX2-STOCH,
  FX2-ROUNDNUM, FX2-HOURREV. All 44 arrays OK per pair.

The named-shadow target arrays are on the SAME dev H1 grid and int8 —
ready for the F-1 rho runner (skeptic §4 protocol; worst-shadow governs;
this lane ran NO rho).

## 7. Deviations / ambiguities — each quoted and resolved (no silent picks)

1. **"over the bar's 60 M1 returns" (P3-A field 5).** A valid H1 bar carries
   60 M1 closes → 59 intrabar minute-to-minute returns. RESOLVED: 59
   intrabar returns over the bar's own 60 minute closes (no bar-boundary
   return; the bar's span is its own data).
2. **Minute mid / spread level.** "mid m_m=(bid_m+ask_m)/2" does not say
   open or close of the minute. RESOLVED: minute CLOSE
   (m_m=(bid_c+ask_c)/2, s_m=(ask_c−bid_c)/m_m) — the settled state,
   consistent with the plane's close conventions; used for S_t, rv and the
   median-minute-spread identically.
3. **Empirical percentile convention.** RESOLVED to the program's standing
   convention (searchsorted-left / len, as `tracka_lib.pct_full_panel`).
4. **P3-B pool "trailing 60 same-weekday days".** P3-A says explicitly
   "previous 60 calendar days"; P3-B's phrase is ambiguous (60 same-weekday
   OCCURRENCES ≈ 60 weeks vs 60 calendar days ≈ 8 occurrences). RESOLVED to
   the literal reading: the trailing 60 same-weekday traded-day
   occurrences, strictly past.
5. **Vol-content control pool.** "trailing realized-vol percentile of the
   same bar" specifies no pool. RESOLVED: realized vol = the bar's own
   Σ|Δlog m| ; percentile within the anchor's own same-hour 60-calendar-day
   trailing pool — only the gated quantity changes, the hour-marginal is
   held fixed.
6. **P3-B array carry encoding (implementation-layer, self-caught).** The
   engine fills bar i from array[i−1] and never fills on non-session bars;
   writing the sign only on the 19:00 decision bar + next-day session bars
   made the engine enter at 01:00 (the decision signal is washed out by the
   20:00–24:00 bars between the days) — measured by this lane's own first
   census (entries {1:170, 0:40} USDCAD). RESOLVED: the sign is carried on
   the decision day's non-session bars (hours 20..23), on any intervening
   non-session day's bars (weekend pre-open), and on the position day's
   00:00..18 session bars; carry bars are never fill-eligible, so the book
   enters exactly at the day's open (measured after fix: {0:205, 1:20, 4:1}
   USDCAD) and exits at the 20:00 close. This is the encoding of the frozen
   representation ("±1 held on the next traded day's 00:00→20:00 session
   bars"), not a law change; battery + census re-run in full after the fix.
7. **P3-A execution delta at the 19:00 bar.** The proposal's decision clock
   admits decisions on bars closing 19:00 (open-hour 18), whose entry bar
   is the 19:00 bar. The INHERITED engine's fill law (`SignalPlane.fill_ok`
   = hour ≤ 18) drops fills at/after the 19:00 bar. RESOLVED: decision law
   implemented exactly (mask 0..18); the engine governs execution; the
   census counts engine-executable books (hour-18 decisions drop out — 1 of
   19 decision hours).
8. **Battery decision masks.** Dispatch: P3-A sampled/pooled on the
   in-session 7..18 UTC mask (narrower than the full 0..18 decision clock —
   battery sampling only, not the law); P3-B on the traded-day decision
   bars (hour 19). Implemented as directed.
9. **M-F extension** — see §4; the frozen harness was not modified; the
   extension is a strict superset of the mutated columns.

## 8. Incidents

- **INCIDENT-1 (self-caught, fixed, disclosed per P-19 honesty class):** the
  first P3-B build used the naive array encoding; the first census run
  exposed day-open entries landing at 01:00 (§7 item 6). Root cause:
  evening non-session bars between decision and next open in the
  target[i−1] engine convention. Fixed in `dinv_1d_target`; full test suite
  (13/13), battery (4× PASS_PIT) and census re-run from scratch; the fix is
  covered by fixture (d) and the census itself.
- One infrastructural miss (missing `research/` on sys.path for the
  governance import) aborted the first two build invocations BEFORE any
  artifact write beyond the AUDUSD m1agg cache; no partial artifacts were
  consumed; the final build revalidated everything fail-closed.

## 9. Known limitations

- The M3 shadow's declared conventions (§6) are this lane's faithful
  implementation of the skeptic-cited spec text; cohort-1's own M3 code was
  not present in the cohort-1 scripts directory to byte-diff against.
- Census counts are engine-executable (P3-A hour-19 fill drop); the
  decision-bar counts in the JSON report the law's full decision clock.
- `weekday_shuffle` twin permutes S_d across all decided days (exact
  marginal preservation); P_d stays with its day — the calendar-geometry
  null as designed.
- Battery M-V share for P3-A `index_shift_pool` is 2.7–3.2%, close to the
  2% floor by mechanism (small pool perturbation); it is NOT vacuous but
  the margin should be remembered when reading the twin's F-2 role.
- Arrays/parquets under `data_local/derived/` are machine-local build
  outputs committed here (following the GO-1 precedent) for sha binding;
  A7 recompute is the default verification path.

## 10. One-shot / next-lane notes

- The F-1 rho fixture (skeptic §4) can now run against the committed
  arrays/runner state; this lane measured NO rho, NO expectancy, NO PnL.
- Lane-C (cost) input: §5.1 histograms + per-fold entry counts in
  `F6_census_counts.json` (gated books; home legs P3-A/AUDUSD,
  P3-B/USDCAD).
- Fold table is frozen in `t2_planes_manifest.json`; F1 contains the 61
  warmup traded days (warmup index 1,334 / 1,307) — fold-population
  comparisons should account for that when reading F1 counts.

— Lane `impl-falsifier-prep`, 2026-09-26.
