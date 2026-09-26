# DIAG_DAEMON_REPORT — ERP1-TRACKA-COHORT-1 / diag lane (tracka1-diag-daemon)

**Labels: `DIAGNOSTIC_OUTCOME_EXPOSED` · `SINGLE_SOURCE_PANEL` ·
`FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK` · `PAPER_TIER`.**

Owner instruction (2026-09-26): score the CURRENT shadow strategy law
("daemon law") on EURUSD and GBPUSD. This is a DIAGNOSTIC exercise on
OUTCOME-EXPOSED surfaces — it can NEVER produce promotable evidence
regardless of results. One pass, both pairs, as specified: no parameter
tuned, no variant tried, no rescue.

Cycle: `ERP1-TRACKA-COHORT-1` · lane `tracka1-diag-daemon` · branch
`orca/erp1-tracka-cohort-1-diag` @ `4aae62269a8d7dd1736b0d05dd6081cce032da01`
(verified at start).

---

## 0. PRE-REGISTERED INTERPRETATION (written before results; verbatim intent)

> (a) These windows are outcome-exposed for the RANGEEXP family — positive
> results CANNOT count as candidate evidence (umbrella §5.8/§6 ancestry
> law; cohort plan §3).
>
> (b) If R-DAEMON is materially positive at k=1.0 with PF>>1 and beats
> beta: the reading is "warrants a properly frozen new identity + forward
> shadow test", NOT "edge proven".
>
> (c) If weak/negative: consistent with the seam attribution, closes the
> question.
>
> (d) No parameter is tuned, no variant tried, no rescue — one pass, both
> pairs, as specified.

The 2026-01..06 sub-window was already consumed by ancestry looks on
these pairs; everything from it is reported only as
`CONSUMED_SURFACE_DESCRIPTIVE`. The 2021-2025 folds are the family's own
development surfaces (F1..F6 = the cohort dev window) — outcome-exposed
by construction.

---

## 1. Data provenance (all inside the diag namespace)

Sources (read-only; sha-verified copies under
`research/control/ERP1-TRACKA-COHORT-1/diag/data_local/`):

| Pair | Source | Window copied | Files | sha verify | 20-file sample |
|---|---|---|---|---|---|
| EURUSD | fx-rangefade-2m-shadow-v1 · FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD | 2021-01-01..2026-06-30 | 4,014 (BID+ASK) | 4,014/4,014 OK vs `m1_manifest.json` (sha256 `12304eac…c3e64`) | 20/20 OK (seed 20260926) |
| GBPUSD | fx-majors-search-v1 (integration) · FX-MAJORS-SEARCH-V1/data_local/GBPUSD | 2021-01-01..2026-06-30 | 4,014 (BID+ASK) | 4,014/4,014 OK vs `m1_manifest.json` (sha256 `c64b6f0c…be1af`) | 20/20 OK (seed 20260926) |

2026-07+ ignored per the diagnostic window law. Verification reports:
`diag/data_local/derived/copy_verify_{PAIR}.json`.

### 1.1 Byte probe (pip / price scale / tradability band — PROVEN, not assumed)

Method = the cycle's committed `probe_pair.derive_scale` (unique
scale in {1e3,1e4,1e5,1e6} inside the registered guard with sane
spread/point checks; pip = 10 x point; band =
union(probe min×0.80 floor-to-pip, probe max×1.20 ceil-to-pip,
registered guard)), probe window 2024-10-26..2024-11-06 (EU+US DST ends,
two weekend rollovers). M1 candles only — the diagnostic sources carry
no tick corpus, so the ancestor probe's tick-vs-candle cross-check is
not available here (recorded limitation; OHLC invariants + 24-byte
layout asserted, 0 violations).

| Pair | Verdict | Scale | Pip | Probe min/max | Derived band | Registered guard |
|---|---|---|---|---|---|---|
| EURUSD | PROBE_PASS | 1e5 | 1e-4 | 1.068375 / 1.093665 | **[0.80, 1.35]** | ~0.80–1.35 (guard won both sides) |
| GBPUSD | PROBE_PASS | 1e5 | 1e-4 | 1.283525 / 1.304785 | **[1.0268, 1.5658]** | ~1.03–1.42 (±20% padding won; band covers guard — same outcome as the USDCAD precedent, band_hi 1.6751) |

Reports: `diag/data_local/derived/probe_{PAIR}.json`; config written only
on PROBE_PASS (`pair_configs_diag.json`).

### 1.2 Census (hardened `tracka_census@2` schema, cycle's gate set)

| Gate | EURUSD | GBPUSD |
|---|---|---|
| days / 15m bars / H1 bars | 2,007 / 130,911 / 30,550 | 2,007 / 131,488 / 30,876 |
| midweek tradable share (>0.90) | 0.98814 PASS | 0.98847 PASS |
| nonpos-spread share (<1%) | 0.0% PASS | 0.0% PASS |
| duplicate 15m ts = 0 | PASS | PASS |
| reconcile p50 within rounding | PASS | PASS |
| plane spreads identical (ANC vs true-H/L) | PASS (max abs diff 0.0) | PASS (max abs diff 0.0) |
| overall open-spread p50 (pips) | 0.3 | 0.8 |
| weekday zero-tradable days / short-record days | 1 / 0 | 1 / 0 |

ANC-convention 15m highs sit below the true highs on 120,475 / 131,488
bars (mean gap 0.71 / 0.94 pips) — the documented narrower-top
consequence of the ancestor convention. Census + plane diffs:
`diag/data_local/derived/{census,plane_diff}_{PAIR}.json`.

---

## 2. Emulation semantics (what was scored)

- **R-DAEMON** = `tracka_lib.f_rangeexp_daemon` — the M-3 emulation
  machinery from the cycle's falsifier battery, **reused unmodified**.
  Pinned semantics: at each signal bar the mode is the searchsorted-left
  percentile of the day's PARTIAL range over that day's bars up to and
  including the bar, vs the trailing 60 full prior-day ranges; the
  fade/follow state machine consumes the CURRENT bar's mode (mid-day
  mode flips allowed; position persists within the day; pd_h/pd_l =
  prior day's full hi/lo). This is the "growing panel, last target"
  semantics of the running shadow law as pinned by the falsifier lane.
- **Plane**: all arms run on the **ANCESTRY-convention H1 SIGNAL plane**
  (15m high = max CLOSE column, low = min LOW column) per the cohort's
  plane pin; the true-H/L plane remains the cost plane; spreads are
  bit-identical across conventions (census gate).
- **Executor**: the committed `engine.run_strategy` (want = target[i-1]):
  signal on a CLOSED H1 bar fills at the NEXT H1 open at the opposite
  quote; cost = the fill bar's OWN measured spread × k ∈ {1.0, 1.5, 2.0};
  no fills on/after the 19:00 bar; force-flat at the day-close bar close
  (20:00 UTC); weekend flat. PnL in the pair's own pips.
- **Fixtures** (`diag/tests/test_daemon_diag.py`, 6 passed): hand-built
  panel with hand-computed partial-range percentiles; the daemon target
  chained through the executor proving the fill bar, direction, opposite-
  quote price law at k=1.0 and k=2.0, no-fill-into-day-close, ANC plane
  convention + spread identity, arm plumbing, G-gate block.

Pinned choice (no alternative tried): `warmup_end_idx = 0` for every arm
— no warmup parameter is introduced; the law's own history machinery
governs when modes exist.

**Books**: R-DAEMON (object of the owner's question) · R-ORIG
(byte-faithful leaky ancestor law — placement reference, never
selectable) · R-ANCHOR (PIT-clean pct[d-1] reference) · SHORT_ALWAYS ·
LONG_ALWAYS (day-session baselines; SHORT_ALWAYS is the beta-matched
book for both quote-USD pairs). SHORT/LONG_ALWAYS run 00:00→20:00
force-flat through the identical executor.

---

## 3. RESULTS

Panel: 2021-01-03T21:00Z .. 2026-06-30T23:00Z (first/last H1 bar),
1,427 / 1,426 traded days (EURUSD / GBPUSD).

### 3.1 Full period — net pips / PF / round trips at k=1.0 (1.5 / 2.0 nets)

**EURUSD**

| Arm | net@k1.0 | PF@k1.0 | RT@k1.0 | net@k1.5 | net@k2.0 | daily SR (k1.0) |
|---|---:|---:|---:|---:|---:|---:|
| **R-DAEMON** | **+812.2** | **1.0624** | **1,062** | +467.2 | +122.2 | 0.0160 |
| R-ORIG | +7,322.7 | 1.6791 | 1,090 | +6,968.9 | +6,615.2 | 0.1357 |
| R-ANCHOR | +1,052.7 | 1.0792 | 1,088 | +698.0 | +343.2 | 0.0206 |
| SHORT_ALWAYS | +704.6 | 1.0307 | 1,453 | +224.2 | −256.3 | 0.0096 |
| LONG_ALWAYS | −1,665.5 | 0.9310 | 1,453 | −2,145.9 | −2,626.4 | −0.0227 |

**GBPUSD**

| Arm | net@k1.0 | PF@k1.0 | RT@k1.0 | net@k1.5 | net@k2.0 | daily SR (k1.0) |
|---|---:|---:|---:|---:|---:|---:|
| **R-DAEMON** | **−1,708.9** | **0.9049** | **1,066** | −2,580.1 | −3,451.3 | −0.0266 |
| R-ORIG | +8,589.9 | 1.5793 | 1,084 | +7,706.1 | +6,822.3 | 0.1194 |
| R-ANCHOR | +2,061.7 | 1.1197 | 1,093 | +1,167.8 | +274.0 | 0.0296 |
| SHORT_ALWAYS | −2,352.0 | 0.9252 | 1,449 | −3,571.8 | −4,791.5 | −0.0243 |
| LONG_ALWAYS | −87.5 | 0.9971 | 1,449 | −1,307.2 | −2,527.0 | −0.0009 |

Every arm decays monotonically with k on both pairs. R-ORIG is strongly
positive on both pairs — the expected ancestry-consistent facts
(placement reference only; it contains the recorded PIT seam and is
never selectable).

### 3.2 Per-fold decomposition F1..F6 (k=1.0 net pips; folds = 2021-2025)

| Arm | F1 (21/01-10) | F2 (21/11-22/08) | F3 (22/09-23/06) | F4 (23/07-24/04) | F5 (24/05-25/02) | F6 (25/03-12) | pos folds |
|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD R-DAEMON | −188.8 | −884.4 | +1,049.8 | +348.3 | −191.5 | +257.0 | 3/6 |
| EURUSD R-ORIG | +1,425.0 | +1,875.7 | +1,141.6 | +1,275.2 | +555.9 | +873.7 | 6/6 |
| EURUSD R-ANCHOR | −14.7 | −467.0 | +1,576.6 | −536.3 | +45.0 | +451.8 | 3/6 |
| EURUSD SHORT_ALWAYS | +420.5 | +838.8 | −283.0 | +134.8 | −170.1 | −379.2 | 3/6 |
| EURUSD LONG_ALWAYS | −557.3 | −996.7 | +100.8 | −242.1 | +62.6 | +189.6 | 2/6 |
| GBPUSD R-DAEMON | −121.5 | +111.2 | −1,272.7 | +789.8 | −407.1 | −728.8 | 2/6 |
| GBPUSD R-ORIG | +1,477.3 | +1,542.3 | +1,644.0 | +1,349.3 | +1,055.9 | +1,456.4 | 6/6 |
| GBPUSD R-ANCHOR | +624.6 | +450.2 | +1,120.1 | +231.6 | −789.3 | +377.6 | 5/6 |
| GBPUSD SHORT_ALWAYS | −382.6 | +1,009.0 | −1,002.6 | −304.0 | −628.3 | −867.1 | 1/6 |
| GBPUSD LONG_ALWAYS | +35.7 | −1,424.3 | +490.6 | −48.9 | +299.2 | +554.3 | 4/6 |

### 3.3 2026-01..06 sub-window — `CONSUMED_SURFACE_DESCRIPTIVE` ONLY

(Consumed by ancestry looks on these pairs; descriptive, never evidence.)

| Arm | EURUSD net (trades, PF) | GBPUSD net (trades, PF) |
|---|---:|---:|
| R-DAEMON | +421.8 (86, 1.5502) | −79.8 (93, 0.9429) |
| R-ORIG | +175.6 (90, 1.1800) | +64.7 (95, 1.0418) |
| R-ANCHOR | −2.7 (88, 0.9973) | +46.9 (97, 1.0313) |
| SHORT_ALWAYS | +142.8 (128, 1.0813) | −176.4 (131, 0.9324) |
| LONG_ALWAYS | −222.4 (128, 0.8856) | +5.9 (131, 1.0023) |

### 3.4 R-DAEMON mode-flip statistics (full panel, 1,427 / 1,426 traded days)

| Statistic | EURUSD | GBPUSD |
|---|---:|---:|
| Days with ≥1 mid-day mode change | 888 (62.23%) | 923 (64.73%) |
| Total mid-day mode-change events | 1,010 | 1,051 |
| Events/day histogram (0/1/2) | 539 / 766 / 122 | 503 / 795 / 128 |
| Days first-mode FLAT (early-silenced, absolute) | 687 (48.1%) | 718 (50.4%) |
| Days R-ORIG-active but daemon first-mode FLAT | 656 | 688 |
| Days R-ORIG-flat but daemon active | 0 | 0 |
| First-mode counts (flat/fade/follow) | 687 / 713 / 27 | 718 / 684 / 24 |
| In-session bars differing vs R-ORIG | 3,010 / 16,933 (17.8%) | 3,271 / 16,967 (19.3%) |
| In-session bars differing vs R-ANCHOR | 3,160 (18.7%) | 3,170 (18.7%) |

Note the zero in the "R-ORIG-flat but daemon-active" row: it is
structural, not empirical — the daemon's partial range is ≤ the day's
full range, so daemon mode > 0 implies R-ORIG pct > 0. The daemon can
silence a day the ancestor would trade, never the reverse.

### 3.5 Beta check (R-DAEMON minus SHORT_ALWAYS, k=1.0)

| Pair | R-DAEMON | SHORT_ALWAYS | **daemon − beta** |
|---|---:|---:|---:|
| EURUSD | +812.2 | +704.6 | **+107.6** |
| GBPUSD | −1,708.9 | −2,352.0 | **+643.1** |

Directionally positive on both pairs, but on EURUSD the margin (+107.6
pips over ~1,062 trips) is inside cost noise — the k=1.5 book sheds
−345.0 pips (net@1.5 − net@1.0 = −345.0), more than the whole margin —
and on GBPUSD it is positive only because the beta book itself is
deeply negative.

### 3.6 R-DAEMON G1–G8 arithmetic (INFORMATIVE ONLY — no promotion semantics exist in a diagnostic)

Thresholds = the cohort's frozen scored-phase gates; panel = full
diagnostic panel (fold assignment and concentration shares cover
F1..F6, 2021-2025).

| Gate (threshold) | EURUSD | GBPUSD |
|---|---|---|
| G1 net>0 @k1.0 | PASS (+812.2) | FAIL (−1,708.9) |
| G2 PF ≥ 1.20 @k1.0 | FAIL (1.0624, margin −0.1376) | FAIL (0.9049, margin −0.2951) |
| G3 ≥4/6 folds positive | FAIL (3/6, margin −1) | FAIL (2/6, margin −2) |
| G4 net>0 @k1.5 | PASS (+467.2) | FAIL (−2,580.1) |
| G5 RT ≥ 100 & months ≥ 6 | PASS (1,062 / 30 mo) | PASS (1,066 / 30 mo) |
| G6 top-fold share ≤ 0.50 | PASS (0.4170) | PASS (0.4472) |
| G7 top-5-trades share ≤ 0.50 | PASS (0.4359) | PASS (0.4476) |
| G8 top-hour share ≤ 0.50 | PASS (0.2399) | PASS (0.1940) |

---

## 4. Reading (under the pre-registered interpretation; results above)

Clause (a) governs everything: these panels are the RANGEEXP family's
own development surfaces plus an ancestry-looked 2026H1 — no number here
is candidate evidence, and R-ORIG's strongly positive books (PF 1.68 /
1.58, 6/6 positive folds) are the expected ancestry-consistent facts of
a leaky law, recorded for placement only. Clause (b)'s branch is NOT
met: R-DAEMON is not materially positive with PF>>1 anywhere — EURUSD
scores +812.2 pips at PF 1.0624 (failing the informative PF gate by
−0.14 and the folds gate at 3/6, with the whole book decaying to +122.2
pips by k=2.0), and GBPUSD is outright negative at every cost tier.
Under clause (c) the reading is therefore: **weak-to-negative, consistent
with the seam attribution — the question is closed.** The PIT-legal
emulation of the running law loses the large majority of the ancestor's
numbers (R-ORIG − R-DAEMON ≈ 6,511 pips on EURUSD and 10,299 pips on
GBPUSD at k=1.0), and the mode-flip statistics quantify the mechanism:
the daemon re-ranks the range mid-day on ~62–65% of days and is
early-silenced (flat at the day's first in-session bar while the leaky
ancestor trades) on ~48–50% of days — the operational cost of the
partial-range percentile is a different, later, and noisier signal
plane, and what remains after real spreads does not clear even the
diagnostic's own informative gates. The beta margins are positive but
not meaningful (see §3.5). Per clause (d) nothing was retried: one pass,
both pairs, no rescue.

---

## 5. Ledger, outputs, limitations

Ledger: `diag/diag_ledger.jsonl` — 10 rows (5 arms × 2 pairs), each
labeled `[DIAGNOSTIC_OUTCOME_EXPOSED, SINGLE_SOURCE_PANEL,
FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK, PAPER_TIER]`, verdict class
`DIAGNOSTIC_DESCRIPTIVE`. Machine-readable results:
`diag/diag_daemon_results.json` (includes sha chain of committed code,
diag code, censuses, manifests, copy-verify and probe reports).

Known limitations:

1. **Contaminated windows** — 2021-2025 folds are the family's dev
   surfaces; 2026H1 was consumed by ancestry looks
   (`CONSUMED_SURFACE_DESCRIPTIVE`).
2. **No placebo control in the diagnostic set** — the 5-book set is the
   dispatch's diagnostic set; the cohort's CAUSAL-PLACEBO book is not
   part of it, so schedule-similarity confounds are not controlled here.
3. **Ancestry-plane emulation of a TrueFX-marks daemon** — the shadow
   daemon runs on its own marks; this emulation scores the pinned law on
   the cohort's ANC signal plane over Dukascopy M1 BID/ASK census bytes.
   The law's shape is emulated, not the daemon's fill reality
   (FILL_QUALITY_UNMEASURABLE_ON_M1_BIDASK).
4. M1-candle-only probe (no tick-vs-candle cross-check available on this
   corpus); single data source (SINGLE_SOURCE_PANEL).
5. `warmup_end_idx = 0` pinned for every arm (no warmup parameter
   introduced; disclosed, not tuned). G1-G8 arithmetic ran on the full
   diagnostic panel (informative); fold/concentration shares cover
   F1..F6.
6. DSR-style context is reported as raw non-annualized daily SR only
   (no trial-count deflation — the diagnostic adds no promotable trial).

Incidents: one lane-internal bug during the copy-verification step (the
20-file sample check looked up `M1/…` paths under the copied layout);
fixed before any downstream use — the full 4,014-file verification had
already passed on the first run and was re-confirmed after the fix. No
data, namespace, registry, or foreign-lane impact.
