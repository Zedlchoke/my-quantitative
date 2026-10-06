# NQ2020_ADDENDUM — alias-recovered re-measurement of the 2020 aggregates

Lane **NQ-2020-REMEASURE**, task **FUTURES-DATACONTRACT-QUAL-V1** (2026-10-03).
ADDENDUM to `FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/NQ_DEEP_v2.md` per its
ERRATUM F1 consequence — the dossier itself was NOT edited (read-only). Machine
results: `nq2020_remeasure.json`; producer: `nq2020_remeasure.py`. All numbers
below are **OBSERVED** (script `nq2020_remeasure.py`, window stated per row;
vendor parquet read-only; no PnL, no signals, descriptive only).

## 1. Method

- **Frozen view rule (ERRATUM F1)**: `instrument_id==16908 AND utc_date <
  2020-06-01 -> raw_symbol 'NQM0'`. Raw rows under id 16908: alias
  `NQU8-NQM9` 2018-08-15..2020-05-31 (92,075 bars, 24,686,121 contracts),
  `NQM0` 2020-06-01..06-19 (19,406 bars, 5,159,596; last bar 06-19 13:29Z).
  Through the alleged hole (UTC 2020-03-23..05-29) id 16908 printed **58
  trading dates, 21,824,572 contracts, max day 690,803** — every count matches
  the ERRATUM F1 / A7-NQ audit exactly. OBSERVED.
- **Panels built from the same raw rows** (chunks
  `AV1R-O1M-NQ-DELTA__2018-06-01_2020-06-01` + `__2020-06-01_2022-06-01`,
  trimmed 2018-06-01..2021-01-31): **NEW** = alias-recovered view (rule above);
  **OLD'** = the v2 behavior (drop every dash symbol — the alias disappears,
  hole sessions NaN) used as the methodology-control run.
- **Conventions identical to the v2 build** (verified against
  `NQ_deep_lib.py` / `NQ_build_cache.py` / `NQ_a1_regimes.py`, read-only):
  session D = 17:00 CT D-1 -> 16:00 CT D (era-B throughout), America/Chicago
  DST-correct wall-clock session dating, maintenance-break bars dropped after
  counting, time-cluster contract registry for one-digit-year symbols,
  per-(contract,session) table, PIT **k=5 volume-crossover** front rule
  (v2 loop verbatim: trailing-5-session mean volume of the next quarterly vs
  current, decided at close of t), **unadjusted** held closes (roll spreads
  absorbed in switch-day returns, as in v2), `ret = diff(log(close))`,
  aggregates per a1 (yearly sum of log rets incl. the year-boundary ret;
  ddof=1 std × sqrt(252); within-year drawdown on log closes).
- **Front-chain verification** (mission requirements, all OBSERVED):
  held contract on every hole session 2020-03-23..05-29 is `NQM0_2020`
  (49 sessions), and 100% of its underlying bars carry `instrument_id 16908`.
  The March roll (NQH0->NQM0) fires at the close of **2020-03-19**
  (trail5 NQM0 ~357k > NQH0 ~229k); NQH0 expires 2020-03-20 (last data);
  NQM0 expires 2020-06-19; **NQU0 becomes front 2020-06-18** (identical to
  the v2 cache). The v2 chain held NQH0 through the hole (its NQM0 appeared
  only 06-01) — hence the NaN hole.
- **Methodology control**: OLD' vs the delivered v2 cache
  (`held_volume_k5.parquet`): **0 held-contract mismatches over 537 sessions**
  (2019-01-02..2021-01-31), and OLD' reproduces the v2 2020 numbers exactly
  on yearly return, worst/best day, max DD, COVID episode and both rvol
  maxima. Differences therefore come from the alias recovery, not from a
  different methodology. One convention difference, disclosed: the v2 CACHE
  contains a phantom session 2020-11-01 (DST fall-back Sunday-open chunk
  17:00-23:59 CST assigned to Sunday; the CURRENT v2 lib code — replicated
  here — assigns it to Monday 11-02). That one cache row explains the only
  OLD'-vs-v2 gap: ann vol 33.62% vs 33.54% (+0.08pp) and 259 vs 260 session
  rows; the yearly return sum is unaffected (telescoping). OBSERVED.

## 2. Old -> new: 2020 headline aggregates

Window 2020-01-02..2020-12-31 sessions (a1 conventions). "old" = dossier §2
(v2 a1 JSON); "new" = alias-recovered.

| metric | old (hole-aware) | new (recovered) | delta |
|---|---|---|---|
| sessions with data | 210 (of 260; 50 NaN rets) | **259 (of 259; 0 NaN)** | +49 held sessions recovered |
| yearly cumulative log ret | **+13.20%** | **+38.43%** | **+25.23pp** |
| ann vol (std x sqrt 252) | 33.54% ("lower bound") | **34.88%** | +1.34pp |
| worst day | −11.15% (see date note) | **−11.15% @2020-03-12** | unchanged (real day, pre-hole) |
| best day | +8.85% | **+8.85% @2020-03-13** | unchanged (real day, pre-hole) |
| max drawdown (close) | −32.28% | **−34.12%** | −1.84pp |
| COVID episode | 02-27 -> trough 03-16 -> recovered 06-05; fall 12, rec 58* | 02-27 -> trough **03-20** -> recovered **06-05**; fall **16**, rec **54** | deeper + 4 sessions later trough; recovery DATE unchanged, now measured not hole-bridged |
| rvol20 max | 92.41% @2020-03-27 | **88.65% @2020-03-30** | −3.76pp, date shifts |
| rvol60 max | 57.13% @2020-04-13 | **60.24% @2020-05-18** | +3.12pp, date shifts |

Decomposition of the +25.23pp return delta (reconciles exactly): recovered
hole returns 03-23..06-01 sum **+32.65pp**, roll-week restatement
**−7.42pp** (see §4: the old 03-20 return used a stale NQH0 print).
OBSERVED (script, window 2020).

## 3. What changes for the dossier's claims

- **§2 yearly table, 2020 row** — "2020: +13.2% (hole-adjusted sum of log
  rets; sessions with data), vol 33.5% ann, worst day −11.15%, best +8.85%,
  DD −32.3%": becomes **+38.4%, vol 34.9%, worst −11.15% @2020-03-12, best
  +8.85% @2020-03-13, DD −34.1%**. The "hole-adjusted" +13.2% materially
  UNDERSTATED 2020 (the entire Apr-May rally was missing). The claim "vol
  33.5% is a lower bound" resolves to 34.9% — direction confirmed,
  magnitude modest (+1.3pp) because the recovered window's realized vol was
  below the March crash weeks.
- **§2 COVID episode** — "2020-02-27 / 2020-03-16 / 2020-06-05, −32.3%, fall
  12 sessions, recovery 58*" becomes **02-27 / trough 2020-03-20 (close
  6,920.25) / 06-05, −34.1%, fall 16, recovery 54 (all real)**. The recovery
  DATE is unchanged; the "58*" asterisk (spanning the hole) is resolved to a
  measured 54 sessions. OBSERVED.
- **§1 rvol table** — "20d max 92.4% (2020-03-27)" becomes **88.6%
  (2020-03-30)**; "60d max 57.1% (2020-04-13)" becomes **60.2%
  (2020-05-18)**. Note the 20d max REVISES DOWN (the old window contained the
  stale +3.39% NQH0 03-20 return, inflating the std), while the 60d max
  revises UP (recovered Apr-May high-vol sessions enter the trailing window).
  The §1 percentiles/min/median rows were NOT re-measured here (build window
  is 2018-06..2021-01) — flagged for the full-era rebuild if §1 is refreshed.
- **§6/§9 consequence items** — "2020 alias-window re-measurement ... MUST be
  recomputed at $0 before any registered cycle": DONE by this addendum at $0.
- **Direction of qualitative claims preserved**: 2020 remains the era's
  deepest-drawdown / highest-vol year in the recovered view; no §3/§4/§5
  number (rolls, DTE, FOMC, CoT) is touched by this re-measurement.

## 4. Incidental findings (outside the mission, reported honestly)

1. **Dossier date error (minor)**: §2 says "worst day −11.15% (2020-03-16)".
   The a1 value −11.1487% is dated **2020-03-12** both in the v2 cache and in
   this rebuild (03-16 was −10.42%). The a1 JSON never carried the date; the
   dossier prose added the wrong one. OBSERVED.
2. **Stale expiry-week print contaminated the old series' last pre-hole
   return**: on 2020-03-20 the dying NQH0 (6,248 contracts) last-printed
   7,453.50 while the liquid June front (NQM0/id 16908, 554,299 contracts)
   closed 6,920.25 and Sep (NQU0) 6,900.00 — a +7.7% same-index discrepancy;
   two liquid deferred contracts corroborate each other. The old series'
   03-20 return (+3.39%) is therefore stale-print contaminated; the recovered
   series replaces it (roll at 03-19; new 03-20 return −3.75%). OBSERVED.
3. **v2 cache artifact**: phantom session 2020-11-01 (DST fall-back
   Sunday-open chunk) — see §1 "methodology control"; current lib code does
   not reproduce it. 260 vs 259 session rows in 2020; +0.08pp on the old vol.
4. **Two stray 1e7-scale bars** on id 16908 (2018-08-15, 2018-09-13; 2
   contracts total; prices 8,105.00/9,475.00 at the 1e7 fixed-point scale vs
   the panel's 1e9 scale): they sit in a <50-bar stray cluster excluded from
   the held path; no effect on any number. Disclosed for the QA ledger.
5. The relabeled alias bars create thin `NQM0_2020` sessions in H2-2019
   (~40 bars/day, spread-scale) — they never win the k=5 front comparison
   (trail ~1.4k vs front ~300-500k) and are never held; no effect.

## 5. Integrity of the alias bars (0 expected, 0 found)

Duplicates `(instrument_id, ts_event)` 0 (also 0 across the chunk boundary);
`(raw_symbol, minute)` 0; `high<low` 0; negative prices 0; close outside
[low,high] 0; zero-volume bars 0 — panel-wide (both views) and inside the
hole window specifically. Hole-window closes stay within 7,082.50..9,586.75
(outright scale) with max |daily log ret| 5.70%. The frozen view rule leaves
no gap at the 2020-05-31/06-01 boundary (same instrument both sides).
OBSERVED.

## 6. Limitations

- Build window 2018-06-01..2021-01-31 (chain warmup from chunk start); the
  full-era §1 distribution rows (percentiles, medians, ACF/VR) were not
  re-measured — only the flagged 2020 aggregates and the rvol 20/60 maxima.
- Returns remain **unadjusted** (v2 convention): switch-day returns absorb
  calendar roll spreads (Mar/Jun spread contributed −0.28pp on 2020-03-19);
  no back-adjustment, no stitching — consistent with the dossier's numbers.
- Yearly "ret" is a sum of log returns over the year's session rows
  (includes the Jan-2 boundary return) — a1 convention, kept for
  comparability.

## 7. ERRATUM (applied 2026-10-03, A1, per independent audit `audit/a7_dc/A7_DATACONTRACT.md` F2)

- **[ERRATUM A7-DC-F2]** §1 and the JSON note quote "trail5 NQM0 ~357k >
  NQH0 ~229k" as the k=5 crossover evidence at close 2020-03-19. The
  magnitude **357k does not reproduce**: A7's raw-bytes recompute gives
  NQM0(id 16908) trailing-5-session mean volume at close 2020-03-19 =
  **428,574** (ending 03-18: 339,953); the NQH0 side (229,267) is exact.
  The crossover DATE is unaffected (fires at close 03-19, not 03-18; all
  roll-week closes/volumes match the JSON 10/10) and no downstream number
  (return decomposition −7.423182pp, worst-day-date correction) depends on
  the 357k figure. Old text retained above; read "~357k" as "~428.6k".
