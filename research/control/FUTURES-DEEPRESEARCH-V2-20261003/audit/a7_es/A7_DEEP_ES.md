# A7-DEEP-ES — Independent audit of the ES deep-research v2 dossier

- Task: **FUTURES-DEEPRESEARCH-V2-20261003**, audit lane **A7-DEEP-ES** (fresh
  context, read-only except `audit/a7_es/`)
- Audited: `dossiers_v2/ES_DEEP_v2.md` + `analysis/ES_*` (scripts, JSONs, cache)
- Checkout: `prep/futures-behavior-10syms-20261002` @
  `26d96eb4bdd4be85e151055dace3354638498a44` (== dispatch base_head; verified)
- Audit window: 2026-10-03 (UTC). All recomputes are FRESH scripts in
  `audit/a7_es/` (`a7_r1_roll.py`, `a7_r2_sessions.py`, `a7_r3_fomc.py`,
  `a7_r4_cot.py`, `a7_r5_quality.py`; outputs `r1_roll.json`,
  `r2_sessions.json`, `r3_fomc.json`, `r4_cot.json`, `r5_jumps.json`,
  `r1_run.log`) reading the vendor parquet / raw CoT zips / FOMC statement
  archive directly — no reuse of the lane's ES_cache intermediates for any
  headline number.
- Environment caveat discovered mid-audit: the local nonprice root
  `~/.my-quantitative-data/futures-nonprice-10syms/` was EMPTIED during the
  audit window (raw `fed/`, `cftc/`, … and `normalized/` including the FIXED
  `cftc_legacy_tidy.parquet` and its `.bak`). The iCloud mirror
  (`~/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures/nonprice/`,
  written by lane DATA-BACKUP, which reports COPY not MOVE) holds the raw zips
  and the PRE-FIX tidy, and was used for the CoT/FOMC recomputes. See INCIDENT
  I-1. The vendor av1trim root is intact (all 13 ES chunks present; 8,710,520
  vendor rows read; 7,825,657 ES-quarterly rows = dossier's count exactly).

---

## 1. Verdict

**PASS_WITH_ERRATA.** Every mandated headline number reproduces exactly from
primary data (§2). One MAJOR errata (the OI-crossover "leads volume by 1
calendar day" claim is a timezone-labeling artifact, and the mechanism claim
built on it is unsupported), five MINOR/NOTE wording errata, one environment
incident to disclose (nonprice root emptied mid-audit — not caused by the ES
lane). No BLOCKER: no fabricated or non-reproducible number was found, no
return-conditioned selection table exists, taxonomy/PIT discipline is sound,
and the handoff is canonical (15/15 output sha256 verified; dispatch_sha ==
actual_start_sha == HEAD; commit null + disclosure).

Errata are REQUIRED before owner consumption of §0.1/§4 (OI claim) and the
minor wording items in §3/§4/§5.

---

## 2. Fresh recomputes (mandated list) — match table

| # | Dossier claim (section) | Fresh recompute | Verdict |
|---|---|---|---|
| 1 | 66 rolls; volume crossover 3–5 sessions before expiry, median 5, mean 4.64 (§0.1/§4) | min 3 / median 5.0 / max 5 / mean 4.636; all 66 crossover DATES identical to lane | **MATCH (exact)** |
| 2 | T5 calendar rule deviation 0 to −2 sessions, never >3 (§0.1/§4) | t5−cross ∈ [−2, 0]; n(\|dev\|>3) = 0; (implies VOL/T5 disagreement = Σ(1−dev) = 90 sessions = the claimed 97.9% agreement, exactly) | **MATCH (exact)** |
| 3 | DECL thin window median 9, range 6–11, 65 rolls (§0.3/§4) | median 9.0, min 6, max 11, n=65 | **MATCH (exact)** |
| 4 | Roll-spread sign series: 27 pos / 39 neg; 61/66 sign-match vs (DFF−1.8pp); by-year medians −1.78%…+4.70%…+3.35% (§4) | 27/39; 61/66; all 17 year-medians identical to 0.01pt (spread values identical roll-by-roll, incl. 2026-09 +67.75) | **MATCH (exact)** |
| 5 | 2026-09 roll spread +67.75 pts "matches v1 exactly" (§4) | spread at 2026-09-11 close = +67.75 (exact). BUT v1's +67.75 is a different quantity (IBKR daily-close gap at the DECLARED roll 2026-08-31; vendor last-trade same day = 68.00) — numerical coincidence, see E5 | **MATCH / framing errata** |
| 6 | Overnight variance share by year: 2020 peak 53.8%, 2018 low 20.9%, band 21–54%; era table 38.5/38.6/43.6/28.4/50.7/32.8/34.2; corr(ON,RTH) −0.10…+0.15; RTH vol share ~79–86% (§0.4/§3) | 2020 = 53.82, 2018 = 20.90, min/max years 2018/2020; all 7 era shares exact; all 7 correlations exact; RTH share 0.793–0.858. Robust: ratio-adjusting the 66 switch sessions moves era shares ≤0.9pp | **MATCH (exact)** |
| 7 | FOMC: pre-release (−120→−15) 0.72–0.81 flat; release bucket 2.91× (\|1m ret\| 3.19×); +30m 2.65×; elevation to +165; day-level ×1.14 vol / ×1.38 range vs baseline ×0.98 (n=3,913); reaction median +1 min, 55% at 0–1, 76% ≤5; quieting 0.93 (§0.6/§5) | pre band 0.724–0.805; 2.906 / 3.188; 2.653; full 20-bucket ratio table identical to 3 decimals (vol AND abs-ret); day-level 1.143/1.376 vs 0.991/0.978 (n=131/3913); reaction 1.0/0.549/0.758; quieting 0.9258 | **MATCH (exact)** |
| 8 | FOMC statement inventory: 132 statements; 92 timed (85 @ 14:00 ET + 7 irregular with exact list); 40 untimed 2011-2015; 131 in-data; 91 timed with 1m data (§5) | 147 archive files = 132 `monetary*a` + 15 b/c; 92 timed; 85 @14:00; irregulars exactly {(2019-10-11 11:00), (2020-03-03 10:00), (2020-03-15 17:00 Sun), (2020-03-23 08:00), (2020-03-31 08:30), (2020-08-27 09:10), (2025-08-22 10:00)}; 131 in-data; 91 timed with data; 106/147 files carry clock text (92 a + 14 b/c) — matches the dispatch's "106/147"; fed calendars corroborate 8 meetings/yr 2011–2015 = 40 = untimed statements | **MATCH (exact)** |
| 9 | CoT U-shape: Q1 14.9 / Q5 14.4 vs Q2–Q4 11.9–12.7 fwd 21d vol (+~2pp tails); deciles −227k→16.8 / +180k→15.9; COVID 13th pctl (fwd rv 90.5), 2022 bear 94th, Aug-2011 58th, 2025-04 78th; Spearman −0.07; OI 1.40M 2006 → 2.95M 2016 → 1.98M 2026; 1,082 weeks / 922 usable (§0.7/§6) | Q1 14.85/Q2 11.86/Q3 12.72/Q4 12.39/Q5 14.36 (+2.0–3.0pp tails); deciles −226,926→16.75 / +179,770→15.95; anchors 0.128/0.942/0.577/0.782 (rv 90.5 exact); Spearman −0.0672; by-year OI identical; 1,082/0 dups; 922 usable — recomputed with an INDEPENDENT ratio-adjusted chain | **MATCH (exact)** |
| 10 | >2% 1m jumps: exactly 10, all macro minutes; −5.67% at 2020-03-16 08:45 CT; 2022 trio all at 07:30 CT CPI (§7) | 10 events: 2011-08-05 07:30 (+2.10), 2020-03-03 09:00, 2020-03-09 08:30, 2020-03-16 08:30 (−2.13) AND 08:45 (−5.67 — exact), 2022-09-13/10-13/11-10 all 07:30 (exact), 2025-04-07 17:02, 2025-04-09 12:19; n(\|ret\|>1%) = 64 = sum of ledger era counts | **MATCH (exact)** |
| 11 | Stray-print floors (≥100k vol / ≥500k OI) | see §3 (floor sensitivity) — floors hide nothing real | **CONFIRMED** |
| 12 | Contract calendar: last session == 3rd Friday for every expired contract except ESM6 2026-06-18; ESM7 2027-06-17 from definitions (§1/§7) | 66/66 true expired contracts match the holiday-adjusted model (naive 3F: 65/66, only ESM6); ESM7 definition expiration = 2027-06-17 13:30Z (08:30 ET) verified in AV1T-definition parquet. Columbus Day cannot hit ES quarterlies (Mar/Jun/Sep/Dec 3rd Fridays; the only in-window Friday holiday collision is Juneteenth-in-June 2022+) | **MATCH (exact)** |
| 13 | Panel integrity: 7,825,657 rows; 0 dup (instrument, minute); 71 contracts; statistics 5,425 contract-days (§1) | 7,825,657 / 0 / 71 / 5,425 (stat_type=9, update_action=1, dedup) — all exact | **MATCH (exact)** |

Two of my own interim results (65.50 spread; \|1m ret\| 2.98×) were MY audit
bugs (minute-of-day sort across the session-midnight boundary; missing
np.log); after fixing, they reconcile exactly. Disclosed for transparency —
the lane's numbers were right.

## 3. Stray-print floor sensitivity (mandate #3)

- **Volume floor (new ≥100k)**: re-computed crossovers at floors 10k / 50k /
  100k → IDENTICAL (3–5 sessions before expiry, median 5, all 66 dates equal).
  Without any floor: 51/66 rolls' "crossover" moves 150–260 sessions earlier
  (median 205), triggered by 2–402-lot deferred stray prints (e.g. 2011-03:
  6 lots on 2010-07-19). The floor is not hiding any real early crossover —
  a real crossover needs front-scale volume, and any floor in [10k, 100k]
  yields the same answer. The lane's ESU6-2025 incident handling is validated.
- **OI floor (new ≥500k)**: without it, 4 extra fake OI "crossovers" appear
  347–483 days early at 644–5,337 lots (including the dossier's own ESM6
  2→5,337→2 calendar-spread artifact on 2025-04-02/03, which I reproduce).
  With it: exactly the 12 in-era rolls. Floor justified.

## 4. CoT on the FIXED tidy (mandate #2)

The fixed tidy no longer exists locally (see I-1); it is a DERIVED table from
immutable raw zips. I therefore (a) reproduced the dossier's exact-name filter
on the mirror's PRE-FIX tidy (2,208 rows / 1,126 dup weeks — the contamination
is exactly as described), yielding 1,082 rows / 0 dups / 2006-01-03→2026-09-22;
(b) rebuilt the canonical exact-name union directly from the 21 raw
`deacot*.zip` annuals: 1,082 rows / 0 dup dates, and **100% row-for-row value
equality (OI, noncomm long/short) with the dossier's filtered series**. Hence
fixed-tidy canonical == the series the dossier actually used, and every §6
claim carries over to the fixed source unchanged (all numbers in §2 row 9).
The INTEGRATION-FIX-V2 normalizer's ES mapping is consistent with raw truth.

## 5. Taxonomy / PIT sweep (mandate #4)

- Tags: sections/claims consistently FACT/OBSERVED/POSTULATED/NOT_RUN-tagged;
  §10's NOT_RUN list is accurate against the artifacts.
- No return-conditioned selection tables anywhere: forward outcomes in
  `ES_cot_stats.json` are vol/drawdown only; FOMC is volume/range timing only;
  `ES_regime_stats.json` contains descriptive means/ACF/VR only. Grep for
  fwd/mean/return-table fields: clean.
- Strict-past thresholds verified in code: FOMC day-level medians
  `rolling(20).shift(1)`; CoT trailing percentile over releases `[k−156, k)`;
  chain rules use prior-session data only. One wording nit (E7).
- Statement-time evidence basis: as-issued HTML text; calendars corroborate.
  The dispatch's "53/58" figure could not be reproduced or identified as any
  statement-inventory quantity; the dossier's own counts (132/92/85+7/40/131/91)
  all verify exactly (§2 row 8).
- FOMC release times: proven (parsed from primary artifacts; irregular list
  reproduces to the minute).

## 6. Handoff canonical check (mandate #5)

`dispatch/handoff_DEEP-ES.json`: `dispatch_sha` == `actual_start_sha` ==
`26d96eb4bdd4be85e151055dace3354638498a44` == checkout HEAD (verified at audit
start). `commit_sha: null` with a specific, accurate disclosure (multi-lane
shared branch; untracked-only outputs). All **15/15** output sha256s match the
files on disk. Tests/limitations/incidents sections present and consistent
with what I observed (incl. the CoT and stray-print incidents, which I
independently reproduced).

---

## 7. Findings

### BLOCKER
None.

### MAJOR
- **M-1 — "OI crossover leads volume crossover by exactly 1 calendar day
  (12/12); positions migrate first, flow follows next session" (§0.1, §4,
  and the H1 refinement in §8) is a date-convention artifact, not an economic
  lead.** The OI table's dates are the Chicago CALENDAR date of `ts_ref`
  (UTC midnight of trading day T), i.e. T−1: all twelve lane OI "crossovers"
  are SUNDAYS (e.g. 2023-12-10), one calendar day before the Monday volume
  crossovers. Proof that `ts_ref=T` labels trading day T: Databento
  stat_type 6 (cleared volume) at `ts_ref=T` tracks session-T traded volume
  at a stable 1.03–1.14× (cleared incl. spreads) on quiet weeks, while the
  T−1 alignment is wild (0.87–12.3×). Under a consistent session-date
  convention the OI crossover falls on the SAME trading day as the volume
  crossover in 12/12 rolls. Consequences: (a) exec-summary/§4/H1 must be
  errata'd to "OI crosses on the same trading day as volume (12/12, 2023-10+
  statistics era)"; (b) the OI chain's "prior published OI" rule
  (`oiq.index < s`) with the shifted labels actually consumes same-trading-day
  OI published the following morning ~08:28–08:58 CT — a few-hours
  publication-lag leak in a descriptive-only stat (98.4% agreement), disclosed
  here, no PnL impact. Required errata; fix is one paragraph, no re-run of any
  scored artifact.

### MINOR
- **m-1 — DFF sign-match attribution (§4)**: "the 5 mismatches are 2017
  transition rolls and 2021" — actual mismatch years: 2017×1, 2018×2, 2019×1,
  2022×1; there is NO 2021 mismatch (2021 spreads were negative with DFF≈0.08,
  proxy negative → match). Count 61/66 itself is exact.
- **m-2 — Overnight std range (§0.4)**: "sd(ON) ≈ 0.4–1.4%/day" — the dossier's
  own year table (and my recompute) has 2017 sd(ON) = 0.25%; honest range
  0.25–1.41. (RTH 0.3–1.3 is fine.)
- **m-3 — FOMC elevation band (§0.6/§5)**: "stays elevated (1.3–2.7×) for 3+
  hours" — the dossier's own table dips to 1.107 (+105 min) and 1.212
  (+120 min); and "+135→+165 min (early Globex)" mislabels RTH-tail buckets
  (13:00 CT anchor ⇒ 15:15–15:45 CT) as Globex.

### NOTE
- **n-1 — v1 cross-check framing (§4)**: v2's +67.75 (vendor close spread at
  2026-09-11, session before crossover) and v1's +67.75 (IBKR daily-close gap
  at the declared roll 2026-08-31; vendor last-trade same day = 68.00) are
  different quantities that happen to coincide numerically. "Cross-validation
  PASS" overstates it; suggest "consistent in sign and magnitude (0.25-pt
  mark-convention difference on the vendor-declared-roll comparison)".
- **n-2 — 2011-08-05 attribution (§7)**: the 07:30 CT +2.10% minute precedes
  the S&P downgrade announcement (post-close Aug 5); it is the 07:30 macro
  (payrolls) slot. Same cluster-day; wording loose.
- **n-3 — regime-map docstring**: "the tag on day t uses returns up to t−1" —
  the tagged vol63 includes day t's own return (thresholds ARE strict-past).
  Occupancy stat is descriptive only.
- **n-4 — statistics window endpoints (§1)**: "2023-09-28→2026-09-28" is the
  Chicago-date rendering; UTC dates are 2023-09-29→2026-09-29. Count 5,425
  exact.
- **n-5 — my own audit bugs, disclosed**: two interim mismatches (spread
  65.50; abs-ret ratio 2.98) were bugs in MY scripts (hhmm-sort across the
  session-midnight boundary; missing log). Lane numbers were correct.

### INCIDENT (environment, NOT the ES lane)
- **I-1 — local nonprice root emptied mid-audit**: during this audit the local
  `~/.my-quantitative-data/futures-nonprice-10syms/` lost all raw subdirs
  (`fed/`, `cftc/`, …) and `normalized/` (incl. the FIXED
  `cftc_legacy_tidy.parquet` and its `.bak_prefix_mixed_20261003`). The iCloud
  mirror holds the raw zips and the PRE-FIX tidy (mirror copy predates the
  fix); the fixed tidy is regenerable from raw via the modified
  `cftc_normalize.py`. Consequence: the dossier's §11 reproduction commands
  that read the nonprice root now fail until the root is restored. This
  touches the workspace law "raw immutable; no deletions" and needs owner
  attention/action; the audit itself reconstructed everything needed from the
  mirror + vendor roots. The vendor av1trim root is intact.

## 8. Errata required (owner-facing list)

1. §0.1 + §4 + §8-H1: replace the OI-lead claim per M-1; disclose the OI-chain
   publication-lag nuance.
2. §4: correct mismatch-year attribution per m-1.
3. §0.4: correct sd(ON) range per m-2.
4. §0.6/§5: correct elevation band + "early Globex" label per m-3.
5. §4: reframe the v1 +67.75 cross-validation per n-1 (optional but advised).
6. Restore or re-point the nonprice data root; record I-1 in the task ledger.

## 9. Bottom line

The DEEP-ES dossier is reproducible to the last decimal on every mandated
headline (13/13 recompute rows match, several "exact to 3 decimals" across
full tables), the two in-lane data incidents (CoT contamination; stray-print
floors) are real, correctly handled, and independently validated, taxonomy
and PIT discipline hold, and the handoff is canonical. The single substantive
correction is the OI-lead timezone artifact (M-1) plus small wording errata.
Verdict: **PASS_WITH_ERRATA** (counts: BLOCKER 0 / MAJOR 1 / MINOR 3 / NOTE 5
/ INCIDENT 1).
