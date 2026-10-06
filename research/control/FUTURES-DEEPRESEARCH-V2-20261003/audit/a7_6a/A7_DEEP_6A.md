# A7-DEEP-6A — Independent audit of dossier `6A_DEEP_v2.md` + `analysis/6A_*`

> Task FUTURES-DEEPRESEARCH-V2-20261003, lane **A7-DEEP-6A** (fresh-context
> auditor). READ-ONLY over vendor + nonprice data; writes only under
> `audit/a7_6a/`. Worktree `prep/futures-behavior-10syms-20261002` @ `26d96eb4`
> (HEAD verified unchanged at audit start). Audit date 2026-10-02/03 (rba.gov.au
> access 2026-10-02).

**VERDICT: PASS_WITH_FINDINGS — 0 BLOCKER / 0 MAJOR / 3 MINOR / 4 NOTE.**
3 errata required (all prose-level number mislabels; every artifact and every
recomputable headline number reproduces).

Method: all recomputations were done with fresh, independent code
(`audit/a7_6a/recompute_core.py`, `recompute_cot.py`, `recompute_fomc.py`) that
does NOT import the lane's library or read its caches — raw ohlcv-1m parquet
union + nonprice sources, held chain rebuilt from the documented rule
(nearest HMUZ, roll at close of last session before delivery-month day-1).

---

## 1. Fresh recomputation results (≥6 required; 9 families delivered)

### R1 — Session structure (dossier §2.1) — MATCH, one prose defect (MINOR-1)

All 8 windows × 3 eras match within 0.05pp:

| Window | 2020-21 dossier→fresh | 2022-23 | 2024-26 |
|---|---|---|---|
| US RTH core 08:30-15:00 CT | 38.0→38.03 | 39.5→39.46 | 42.7→42.65 |
| Sydney day 07:00-17:00 | 27.7→27.66 | 26.2→26.24 | 26.3→26.26 |
| London 08:00-16:30 | 51.0→51.01 | 52.8→52.84 | 50.6→50.59 |
| Tokyo 09:00-15:00 | 20.4→20.41 | 19.3→19.29 | 18.5→18.49 |
| US data block 07:00-08:30 CT | 9.8→9.75 | 12.1→12.10 | 11.5→11.47 |
| Shanghai 09:30-10:00 | 2.3→2.34 | 2.3→2.34 | 2.2→2.21 |
| Evening 17:00-20:00 CT | 9.2→9.20 | 8.2→8.23 | 8.6→8.59 |
| Overnight 00:00-06:00 CT | 25.2→25.22 | 23.0→23.01 | 20.5→20.47 |

Bimodal U-curve (2024-26, mean |1m ret| by CT hour): primary peak 09:00 CT
1.681bp (dossier 1.68), secondary 19:00/20:00 CT 1.186/1.268bp (dossier
1.19-1.27), minimum 15:00 CT 0.682bp (dossier 0.68). MATCH. Sydney-morning
profile 09:00 0.60 → 10:00 1.78 → 11:00 1.81 → 11:30 2.35 MATCH (fresh
0.6015/1.7804/1.8124/2.3510).

**MINOR-1**: the claim "11:30 … ~4× the average half-hour intensity" (§2.1,
repeated §4.3) is wrong as written. The 2.35% share is exact, but it is
**1.13× the mean half-hour** (2.083% across the 48 Sydney-clock half-hours) and
**1.33× the median** (1.769%). ~4× holds only vs the quietest Sydney-morning
slot (09:00 = 0.60%; 2.35/0.60 = 3.9×). Erratum required (see §5).

### R2 — RBA event anatomy (§4.1) — MATCH

Gate table fresh parse: **67 meetings 2020-2026, 23 changes, 44 holds** (dossier
identical; rba.gov.au per-year counts 12/11/11/11/8/8/6 also sum to 67 with 23
changes). ±5min window medians: event volume **2,199** and |1m ret| **4.349bp**
reproduce EXACTLY; baselines 240 vol / 0.888bp (lane: 245 / 0.91) → ratios
**9.16× / 4.90×** vs dossier 9.0× / 4.8× (rounding-level; event medians
identical — see NOTE-2). Day split: event 83,793 vs non-event 79,382 median
volume; session range 38 vs 19 ticks; **change-days (23) 93,036 vol / 59-tick
range vs hold-days (44) 77,674 / 29** — all match. Special-meeting flag: only
2020-03-19 (Thu) — matches dossier.

### R3 — CIP / roll gaps (§3.1-3.2) — MATCH

27 rolls (fresh count identical). Material-differential subset (|RBA−DFF| ≥
25bp): **16/16 sign agreement (100%)**; overall **20/27 = 74.1%** (dossier 74%).
2026 rolls: Mar −0.42% ann / Jun −0.75% / Sep −1.87% vs differentials
+0.21 / +0.73 / +0.72pp — exact match, incl. "2026-09-01 −1.87% vs +0.72pp"
and RBA 4.35 > DFF 3.63 at the Sep roll (DFF latest-vintage). Roll-gap summary:
median +0.414% ann (dossier +0.41%), 4/27 negative (14.8%), range −1.87…+1.82.
Volume crossover lags the declared roll by 9-15 days (median 11) — artifact
check confirms; ramp-to-10k 4-12 days (median 8) — artifact check confirms.

### R4 — Drawdowns / regimes (§1) — MATCH (peak-date labeling, MINOR-3)

Worst DD **−25.17%** (dossier −25.2%), trough **2025-04-08** — exact. COVID leg
**−17.97%** (dossier −18.0%), trough 2020-03-19, peak 2020-01-02 — exact.
COVID week 2020-03-09..13 **−6.83%** — exact. USD-cycle peak: fresh running-max
close **2021-02-24** vs dossier 2021-02-25 (MINOR-3; depth/trough unaffected).
Annualized vol by year (rolled): 12.1/8.9/13.4/10.8/8.4/9.5/8.4 matches
(§1.1 table). Trend persistence 48.9% overall (artifact) matches.

### R5 — OI leads volume (§3.3) — MATCH; disclosed 2024 outlier is a definition artifact (NOTE-1)

Fresh roll-anchored measurement on GLBX statistics (stat_type 9, 2023-10+):
**all 12 completed rolls show OI crossover leading volume crossover by exactly
2-3 calendar days** (2-3 sessions; every pair lands mid-week). Lane's examples
2025-12-09 vs 12-12 and 2026-09-09 vs 09-11 reproduce exactly. The
dossier-disclosed outlier ("U4→Z4 OI cross 2024-04-03, months early") comes
from the lane's unanchored first-crossover scan over the pair's full joint
window (a6 script §4); roll-anchored, U4→Z4 OI crosses 2024-09-11 (2-day
lead). The lane flagged it honestly; conclusion "2-3 sessions at every roll"
stands under the roll-anchored definition.

### R6 — CoT on the FIXED tidy (§5) — ALL MATCH; fix changed nothing for 6A

Recomputed on the REGENERATED `cftc_legacy_tidy.parquet` (INTEGRATION-FIX-V2,
2026-10-03 08:43 — i.e. AFTER `6A_a5_cot.py` ran at 07:51): 1,082 weeks,
2006-01-03→2026-09-22, 0 duplicate dates, single market line
"AUSTRALIAN DOLLAR - CHICAGO MERCANTILE EXCHANGE". Yearly means 2021-25:
−33.08/−51.57/−52.36/−38.15/−66.13k (dossier −33.1/−51.6/−52.4/−38.2/−66.1).
2026: mean +16.05k (16.0), max **+85.64k** (85.6). OI 137.8k (2020) → **278.0k**
(2026 mean). Crowding 2021-25 −0.187…−0.364 (−0.19…−0.36). Series min −107.54k
@2024-03-19; max +103.38k @2012-12-11. **Row-level diff fixed vs pre-fix backup:
1,082 shared rows, 0 mismatches** on net_noncomm and OI — the CFTC
substring-mapping defect did not affect COT_LEGACY_6A (single-line symbol), so
the dossier's CoT block remains valid on the fixed tidy. No re-statement
needed beyond this verification record.

### R7 — Data quality (§7, §3.4) — MATCH (count prose mislabel, MINOR-2)

Raw 2,876,268 rows; spread bars 171,473; **outright negative bars 0**; **spread
negative bars 32,694**; era split **5,067 / 45 / 757 / 11,836 / 14,989** — all
EXACT (the dispatch's "5,067" erratum confirmed as the 2020-21 subset).
Contaminant `6BU5`: **1,584 bars, instrument 1318, 2020-05-12→08-17, volume
4,888** — exact, and 1:1 with `analysis/integration/contaminant_scan.json`
(same count in the 6A root; the 90,551-bar 6BU5 entry there is the 6B root's
legitimate series). Spread-mark vs outright-implied (six most-printed, last 90
days): median |diff| 0.00018-0.000785 USD = 3.6-15.7 ticks (dossier
"0.0002-0.0008 USD / 4-16 ticks"). **MINOR-2**: the dossier header's "2,704,795
outright bars … after excluding 1,584" is internally inconsistent — 2,704,795
is the PRE-exclusion count; post-exclusion is **2,703,211** (the lane's own
`build_report.json` and this audit agree). §7's "1 break-window bar in
2,704,795" repeats the mislabel. Artifacts correct; prose wrong.

### R8 — FOMC (§4.2) — MATCH

59 statements 2020-2026 (fresh count identical). ±5min: 3,213 vs 393 median
volume = **8.18×** (dossier 8.2×); |1m ret| 5.670 vs 0.917bp = **6.19×**
(dossier 6.2×, "5.67 vs 0.92bp" exact). Event-day volume 96,832 vs 78,676
(+23.1%); session range 53.5 vs 19.0 ticks — all match.

---

## 2. ABS family absence + 11:30-slot separation — VERIFIED

- Corpus: nonprice root contains 14 families (bls_gate, boe, boj, cftc, ecb,
  eia, fed, fred_alfred, govuk, mof, noaa, normalized, ons, rba) — **no ABS
  family**; recursive search for `*abs*`/`*australian bureau*` returns nothing.
- The 6A scripts reference ABS only in docstrings/comments and `NOT_RUN`
  notes; no ABS-anchored loader or computation exists. No ABS-derived number
  appears anywhere in the dossier.
- The 11:30-Sydney intensity claim is computed by pure time-of-day grouping
  (`volume_by_syd_halfhour`, all sessions, no event conditioning) — the
  separation the dispatch required HOLDS. The §4.3 erratum (dispatch packet
  claimed an ABS calendar; corpus has none) is itself verified true. Only the
  "~4× average" multiplier is wrong (MINOR-1); the 2.35% share and the
  all-days computation are exact.

## 3. RBA gate cross-check vs rba.gov.au — 9/9 MATCH

WebFetch of https://www.rba.gov.au/statistics/cash-rate/ (access 2026-10-02),
compared against the in-corpus gate HTML (announcement = effective − 1 AU
business day):

| Effective (corpus) | change → rate (corpus) | rba.gov.au | verdict |
|---|---|---|---|
| 2020-03-04 (chg) | −0.25 → 0.50 | 4 Mar −0.25 → 0.50 | MATCH |
| 2020-03-20 (chg, special) | −0.25 → 0.25; ann Thu 2020-03-19 | 20 Mar −0.25 → 0.25 | MATCH |
| 2020-11-04 (chg) | −0.15 → 0.10 | 4 Nov −0.15 → 0.10 | MATCH |
| 2020-12-02 (hold) | 0.00 → 0.10 | 2 Dec 0.00 → 0.10 | MATCH |
| 2023-04-05 (hold) | 0.00 → 3.60 | 5 Apr 0.00 → 3.60 | MATCH |
| 2023-06-07 (chg) | +0.25 → 4.10 | 7 Jun +0.25 → 4.10 | MATCH |
| 2025-02-19 (chg) | −0.25 → 4.10 | 19 Feb −0.25 → 4.10 | MATCH |
| 2026-06-17 (hold) | 0.00 → 4.35 | 17 Jun 0.00 → 4.35 | MATCH |
| 2026-09-30 (chg) | +0.25 → 4.60 | 30 Sep +0.25 → 4.60 | MATCH |

Per-year decision counts 12/11/11/11/8/8/6 = 67 and 23 changes — identical
corpus vs web. The dossier's "2026 hikes Feb/Mar/May/Sep to 4.60" is confirmed
by the web rows (4 Feb 3.85, 18 Mar 4.10, 6 May 4.35, 30 Sep 4.60). 0
mismatches in the sample (5 change-days incl. the special, 4 holds).

## 4. Taxonomy / PIT / gates — VERIFIED

- Taxonomy tags used throughout (50 OBSERVED / 23 NOT_RUN / 4 POSTULATED /
  FACT where sourced). Missing evidence recorded as NOT_RUN, never PASS.
- Strict-past verified in code: vol-regime quintiles from prior-2y window
  (`iloc[i-504:i]`), trend persistence `prior50.shift(1)`, large-move q95 of
  `absr.shift(1).rolling(126)`, CoT percentile vs trailing 3y (`iloc[lo:i]`)
  with forward windows starting at release (obs + 3 BD) — PIT-legal.
- No conditional mean-return tables: A4 computes volume / mean-abs-return /
  range only; A5 forward reads are vol / max-DD only. Dispatch law honored.
- HG: definitions ALL10 carry **zero HG-family symbols** (prefixes present:
  6A 6B 6E 6J CL ES GC NG NQ SI + vendor composites) — NOT_IN_CORPUS
  re-verified; iron-ore absent from nonprice — consistent everywhere (§6-H2,
  §8.4).
- 6BU5 exclusion consistent across build_report (1,584), integration scan
  (1,584), dossier (1,584), fresh audit (1,584).

## 5. Findings register

**BLOCKER: none. MAJOR: none.**

- **MINOR-1** (§2.1, §4.3): "~4× the average half-hour intensity" for the
  11:30-Sydney slot is wrong — 2.35% is 1.13× the mean half-hour (2.08%) and
  1.33× the median (1.77%); ~3.9× holds only vs the quietest 09:00 slot
  (0.60%). The share itself and the all-days time-of-day computation are
  exact; the ABS separation is unaffected. **Erratum: restate as "2.35% of
  daily volume in that half-hour — the Sydney-morning modal peak, ~1.1× the
  average half-hour and ~3.9× the quiet 09:00 Sydney-open slot."**
- **MINOR-2** (header, §7): "2,704,795 outright bars … after excluding 1,584"
  mislabels the pre-exclusion count; post-exclusion is 2,703,211 (matches the
  lane's own build_report.json). **Erratum: replace 2,704,795 with 2,703,211
  in both places (or relabel as pre-exclusion).**
- **MINOR-3** (§1.2): USD-cycle DD peak labeled 2021-02-25; fresh running-max
  close is 2021-02-24 (depth −25.2%, trough 2025-04-08 unchanged).
  **Erratum: peak → 2021-02-24** (or state the convention).
- **NOTE-1**: the §3.3 "2024 outlier (U4→Z4 OI cross 2024-04-03)" is an
  artifact of the lane's unanchored first-crossover scan; roll-anchored OI
  cross is 2024-09-11 (lead 2 days). Disclosure was honest; conclusion
  unchanged.
- **NOTE-2**: RBA baseline medians differ at rounding level between audit
  (240 vol / 0.888bp) and lane (245 / 0.91) — event medians identical
  (2,199 / 4.35bp); ratios 9.2×/4.9× vs 9.0×/4.8×. No action.
- **NOTE-3**: CFTC tidy regeneration (INTEGRATION-FIX-V2) is row-identical
  for COT_LEGACY_6A (0/1082 mismatches vs pre-fix backup) — dossier §5 valid
  on the fixed tidy; timing note: a5 ran 07:51, tidy regenerated 08:43, so
  the dossier was written against the pre-fix tidy (harmless for 6A).
- **NOTE-4**: DFF latest-vintage month-end value 2026-09-30 is 3.88; the
  dossier's "DFF 3.63" is the Sep-1 roll-date value — correct in context,
  recorded for completeness.

## 6. Handoff canonicity — VERIFIED

`dispatch/handoff_DEEP-6A.json`: schema `zcode_orch_v3_handoff@1`;
`dispatch_sha` = `actual_start_sha` = `26d96eb4` (current HEAD, verified);
`commit_sha: null` WITH explicit disclosure (prep-class, uncommitted
working-tree artifacts, owner/lead to commit). All **16/16** output sha256
digests re-hashed and match, including the dossier itself
(`84c13660…`). The dossier's four header hashes (v1 dossier `85956ee6…`,
owner framework `6f1e1413…`, dispatch manifest `c2ecffa8…`) also verify.

## 7. Audit artifacts (this lane)

- `audit/a7_6a/recompute_core.py` → `recompute_core.json` (R1-R5, R7;
  independent chain/registry/hub-clock implementation from raw parquet)
- `audit/a7_6a/recompute_cot.py` → `recompute_cot.json` (R6, fixed vs pre-fix
  tidy diff + dossier claim table)
- `audit/a7_6a/recompute_fomc.py` → `recompute_fomc.json` (R8)
- `audit/a7_6a/a7_chain_daily.parquet` (intermediate; regenerable)
- `audit/a7_6a/A7_DEEP_6A.md` (this report)

**Errata required (owner/lead):** MINOR-1, MINOR-2, MINOR-3 as worded in §5.
Everything else stands as published.
