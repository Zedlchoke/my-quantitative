# DATA_AUDIT_REPORT — Lane D (data/PIT/cost audit), pool B

**Program:** PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO), candidate pool B
(volume-profile / tick-volume strategy class on M1 FX).
**Task id:** `PC12A_D_data_audit` · **Date:** 2026-09-29 · **Lane:** D, root
checkout, READ-ONLY on panels (no git, no network, no S1).
**Tooling:** `.venv/bin/python` 3.12.14 + numpy 2.5.2; heavy lock inspected
before the run — `FREE_PROVEN` (light single-pass decode, no heavy job).

**Reproducibility:** every number below is emitted by
`audit_scripts.py` (this directory) into `audit_summary.json`;
per-file hashes are in `panel_hashes_{EURUSD,GBPUSD,USDJPY}.jsonl`.
Runtime of the full deterministic pass: ~24 s.

## Panels audited (physically, file by file)

| pair | panel root | sides | files | bytes (BID+ASK) |
|---|---|---|---|---|
| EURUSD | `.worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/M1` | BID, ASK | 2092 + 2092 | 36,722,777 |
| GBPUSD | `.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/M1` | BID, ASK | 2092 + 2092 | 36,601,602 |
| USDJPY | `.worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/USDJPY/M1` | BID, ASK | 2092 + 2092 | 38,433,187 |

Total: **12,552 files, 111,757,566 bytes**, every one read, hashed (sha256)
and lzma-decoded during this audit.

## Headline verdicts

1. **Panels are physically complete and internally consistent** — 0 missing
   calendar days (weekday *and* weekend), 0 zero-byte files, 0 undecodable
   files, 0 malformed names, every file exactly 1440 records, 0 OHLC
   invariant violations, 0 negative-spread minutes across all 6.02M
   minute-slots per pair. Coverage and format: **MEASURED / PASS**.
2. **Record format empirically confirmed**: 24-byte big-endian records
   `>u4 ×5 + >f4` = (sec-offset, open, close, low, high, volume_f32), prices
   ÷1e5 (EURUSD, GBPUSD) / ÷1e3 (USDJPY). **MEASURED / PASS** (§B).
3. **The dispatch's volume premise is REFUTED**: the M1 volume column is
   **NOT a tick count** — it is a predominantly non-integral float32
   (only 2.5–3.7% of active minutes are integral), i.e. a
   **size-weighted sum of per-tick volumes** in Dukascopy's volume unit
   (absolute unit NOT verifiable from the candles alone). A "tick-volume"
   strategy built on this column is actually a *size-weighted volume*
   strategy; if true tick counts are required, tick data must be staged
   (not present in these panels). See §C — this is the audit's main
   strategy-semantics finding.
4. **Cost-table spread cells re-measured on the full populations:**
   C1 (Friday 20:00 fill spread) reproduces the COST_AUTHORITY_TABLE
   **exactly** on all three pairs (n=286/286 each). C2 **Friday** roll-window
   cell reproduces **exactly**. C2 **Mon–Thu** cell does **NOT** reproduce on
   its declared (21:00,22:00] UTC window — the table's numbers match the
   **22:00–23:00 UTC** hour instead; the declared window's true p50/p90 are
   ~1.5–2× wider (e.g. EURUSD 1.2/3.7 vs table 0.6/2.7). **MATERIAL
   discrepancy flagged** — the Mon–Thu roll cell currently *understates*
   rollover-window costs (§D).
5. **Provenance:** file counts, byte totals, corpus digests, tradable-minute
   censuses and **all 4,184 per-file sha256 in each staged
   `m1_manifest.json` agree 100%** with this audit's independent
   re-measurement. Two clerical divergences in the prior
   `data_manifest_fx.json` are flagged (§F): a non-reproducible
   `largest_tradable_minute_run` field and a one-character typo in the
   recorded USDJPY `m1_manifest.json` hash. Neither affects data identity.

---

## A. Inventory, coverage, gaps (task a)

Identical picture on all three pairs and both sides (BID and ASK date-sets
are identical; every value from `audit_summary.json: panels.<pair>`):

| metric | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|
| .bi5 files per side | 2,092 | 2,092 | 2,092 |
| filename span | 2021-01-01 … 2026-09-23 | same | same |
| calendar days in span | 2,092 | 2,092 | 2,092 |
| **missing weekday files** | **0** | **0** | **0** |
| **missing weekend files** | **0** | **0** | **0** |
| 0-byte files | 0 | 0 | 0 |
| undecodable files (lzma) | 0 | 0 | 0 |
| files with records ≠ 1440 | 0 | 0 | 0 |
| non-conforming filenames | 0 | 0 | 0 |
| decode anomalies (any) | 0 | 0 | 0 |

FX is 24/5, so "weekend closure" is expressed not by missing files but by
zero-volume carry-forward content. Measured census (BID; ASK identical):

| metric | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|
| tradable minutes (vol>0), BID | 2,130,647 | 2,130,680 | 2,131,564 |
| tradable minutes, ASK | 2,130,647 | 2,130,680 | 2,131,564 |
| first tradable minute | 2021-01-03T22:00Z | same | same |
| last tradable minute | 2026-09-23T23:59Z | same | same |
| zero-tradable **weekdays** (holiday closures) | 2021-01-01 only | 2021-01-01 only | 2021-01-01 only |
| zero-tradable weekend days | 300 | 301 | 301 |
| longest uninterrupted tradable run | 5,787 min from Sun 2024-11-17 22:39Z | 4,377 min from Mon 2021-01-25 22:35Z | 5,764 min from Sun 2021-11-28 22:00Z |

Notes:
- **Weekday gaps: none.** The single zero-tradable weekday (2021-01-01, New
  Year Friday) is a genuine market closure with a carry-forward file (see
  §B). All other weekdays, including Christmas/Boxing-day dates sampled in
  §B/§C, have at least some tradable minutes.
- **Weekend closures:** all ~299 Saturdays per pair are pure carry-forward
  (0 tradable minutes); Sundays reopen late in the UTC day (§B DST
  evidence), leaving ~1 zero-tradable Sunday per pair (EURUSD) / 2
  (GBPUSD, USDJPY).
- Longest-run values above were re-verified with an independent one-off
  decode of the window 2024-11-16…23 (EURUSD: Sun 22:39 reopen → gap-free
  through Thu 23:06, next gap; daily counts 119/1440/1440/1440/1439/1320).
  They **diverge from the prior manifest's** `largest_tradable_minute_run:
  4321 @ 2024-01-01 (identical for all 3 pairs)` — that field does not
  reproduce (actual longest run around 2024-01-01 is 1,418 min) and looks
  like a prior-cycle computation/copy error. Immaterial to coverage, but it
  is a provenance divergence (§F).

## B. Record format — empirical verification (task b)

**Structured decode sample: 68 days per pair, both sides** (from
`format_and_volume.<pair>.sample_dates`): a 45-day grid every 47 days from
2021-01-01 to 2026-09-11 (47 mod 7 = 5 ⇒ samples all weekday phases, not
just Fridays) **plus** 4 Sunday-reopen days (2021-01-03, 2022-01-02,
2024-01-07, 2025-06-15), 11 Christmas/New-Year days (2021-12-24/27/31,
2022-12-23/26/27/30, 2023-01-02, 2024-12-25/31, 2025-01-01), 5 roll-window
Wednesdays (2023-03-01, 2023-06-14, 2024-06-12, 2025-06-11, 2026-01-07)
and 3 macro-anchor days (2022-09-26, 2022-09-28, 2024-07-03). Weekday mix:
Mon 11, Tue 8, Wed 16, Thu 6, Fri 11, Sat 6, Sun 10.

### Confirmed binary format

- LZMA (alone-format) compressed; **every one of the 12,552 files**
  decompresses; payload is always 1440 × 24 bytes.
- **Record = 24 bytes, big-endian, six 4-byte fields:**
  `struct '>5I' + '>f4'` (equivalently the structured dtype
  `>u4,>u4,>u4,>u4,>u4,>f4`):
  `t` = seconds offset from 00:00 UTC (0…86340, always step 60),
  `open`, `close`, `low`, `high` = price × 10^5 (EURUSD/GBPUSD) or × 10^3
  (USDJPY), `volume` = float32.
- The dispatch's alternative "30-byte '>IIIff'" hypothesis is refuted by
  payload size alone (34,560 = 1440×24).

### Evidence for each element

| test | result |
|---|---|
| timestamp units | t_max = 86,340, all consecutive diffs = 60 ⇒ **seconds**, one record per minute, UTC day grid |
| field order (t,o,c,l,h) | OHLC invariant `low ≤ min(o,c) ≤ max(o,c) ≤ high`: **0 violations** on all 70,475–70,713 tradable sample records per pair; alternative orders refuted: (t,o,h,l,c) violates 1,206–1,333 of 1,437–1,440 busy-day records; (t,o,c,h,l) violates 1,402–1,431 |
| close identification | next-open vs prev-close: p50 = 0.1 pip, p90 = 0.2 pip with close = field 2; the field-4-as-close candidate gives p50 0.4–0.8 / p90 1.5–2.6 pips ⇒ **close is field 2** |
| price-scale divisor | candidate divisors tested against plausibility bands: only 1e5 (EURUSD, GBPUSD) and 1e3 (USDJPY) give in-band fraction = 1.000; 1e3/1e4/1e6 for the majors give 0.000 (observed raws 95,383–139,148 / 103,097–162,415) |
| price sanity vs known levels | sample observed ranges: EURUSD 0.95383–1.22523 (task band 0.95–1.16; the >1.16 max is the genuine Jan-2021 high), GBPUSD 1.03618–1.39148 (task band 1.07–1.35; the min is the 2022-09-26 low, the max early-2021), USDJPY 103.097–162.415 (task band 100–162 ✓) |
| macro anchor days | 2022-09-28 EURUSD BID low 0.95383 (multi-decade low area); 2022-09-26 GBPUSD low 1.03618 (flash-low day); 2024-07-03 USDJPY high 161.948 — all at the historically correct magnitudes |
| holiday carry file | 2021-01-01: all 1440 records o=c=l=h, vol=0, flat at EURUSD 1.22141 / GBPUSD 1.3663 / USDJPY 103.259 — the well-known 2020-12-31 closes, another scale anchor |
| weekend carry | every sampled Saturday: exactly 1 distinct price all day, 0 minutes with volume (e.g. EURUSD 2021-05-22 flat 1.21778) |
| UTC timezone | Sunday reopen first tradable minute 22:00–22:05Z on winter Sundays (2021-01-03, 2022-01-02, 2024-01-07) but 21:00–21:04Z on the summer Sunday 2025-06-15 ⇒ stamps are UTC and the NY-close/open boundary shifts with US DST exactly as expected |
| BID/ASK coherence | ask ≥ bid on every one of the ~2.13M tradable minutes per pair (0 negative spreads, open and close, across the entire panel); BID and ASK tradable masks are **identical** (symmetric difference = 0) |

## C. Volume field (task c)

All statistics on the 68-day structured sample, BID side (ASK side
qualitatively identical; `format_and_volume.<pair>.volume`).

### Is it a tick count? — NO (dispatch premise refuted)

- Decoded as float32 the values are plausible and activity-correlated, but
  **only 2.49% (EURUSD) / 3.50% (GBPUSD) / 3.71% (USDJPY) of active minutes
  have integral volume**. A per-minute tick count must be integral;
  float32 represents integers exactly up to 2^24. ⇒ **not a count.**
- The raw 4 bytes are float32 bit patterns (non-zero raw uint32 values are
  1.04–1.16 × 10^9, i.e. float encodings of 0.09–2,985 — reading the field
  as a uint count would give ~10^9 "ticks per minute", absurd).
- Values are dominated by 2-decimal quantization at small sizes (min
  positive 0.10/0.09/0.12; 86–97% of positive values are multiples of 0.01,
  large sums carry finer fractional parts from float accumulation).

**Verdict: the volume column is a size-weighted sum of per-tick volumes
(Dukascopy volume units) per minute per side — an activity/size proxy, NOT
a tick count and NOT confirmed to any absolute unit.** The unit basis
(lots vs millions of base currency) cannot be verified from the candles
alone — instrument metadata or tick files would be needed; nothing in these
panels pins it. Consequences for the strategy class: (i) relabel
"tick-volume" features as size-weighted volume features, or stage tick
data if actual tick counts are wanted; (ii) within-pair relative profiles
(hour-of-day, percentile ranks) are unit-invariant and safe; (iii) absolute
level comparisons across pairs are only valid if the unit is confirmed.

### Distribution and activity correlation (BID side)

| statistic | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|
| minutes with vol>0 — all minutes | 72.08% | 71.97% | 72.22% |
| — weekdays only | 92.13% | 92.05% | 92.33% |
| — weekends only | 6.89% | 6.73% | 6.85% |
| vol p10/p50/p90/p99 — **all minutes** | 0 / 43.2 / 304.95 / 1126.09 | 0 / 35.31 / 183.04 / 616.85 | 0 / 66.30 / 461.89 / 1019.94 |
| vol p10/p50/p90/p99 — **vol>0 minutes** | 11.79 / 84.68 / 392.89 / 1239.62 | 10.80 / 62.52 / 224.05 / 713.78 | 17.80 / 137.42 / 546.20 / 1095.19 |
| max volume in sample | 2,360.2 | 2,646.9 | 2,984.9 |
| mean vol, London/NY core 12–16Z | 289.9 | 165.1 | 341.4 |
| mean vol, Asia lull 22–06Z | 91.5 | 68.3 | 173.5 |
| core/lull ratio | **3.17×** | **2.42×** | **1.97×** |
| Pearson corr(vol, H−L range in pips) | 0.675 | 0.519 | 0.565 |
| Pearson corr(BID vol, ASK vol) | 0.890 | 0.720 | 0.912 |
| total-volume ratio ASK/BID | 0.937 | 0.962 | 0.930 |

Hour-of-day profile (weekday, vol>0, mean volume, UTC — the input a
volume-profile strategy would consume):

| pair | 00 | 02 | 04 | 06 | 08 | 10 | 12 | 14 | 16 | 18 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EURUSD | 108 | 108 | 81 | 143 | 221 | 184 | 255 | 346 | 211 | 205 | 85 | 42 | 37 |
| GBPUSD | 72 | 75 | 69 | 95 | 131 | 110 | 139 | 185 | 138 | 110 | 77 | 58 | 43 |
| USDJPY | 247 | 183 | 161 | 227 | 304 | 232 | 312 | 405 | 242 | 216 | 99 | 55 | 64 |

(Full 24-hour vectors in `audit_summary.json`. The profile is exactly what
FX microstructure predicts: London/NY overlap peak at 13–15Z, Tokyo bump at
00–01Z for USDJPY, 21–22Z rollover trough, Friday-evening decay.)

**Volume honestly tracks activity**: 2–3× core/lull ratio, 0.52–0.67
correlation with per-minute range, weekday active fraction 92%. The
BID/ASK volumes are two slightly different measures of the same flow
(ratio 0.93–0.96, corr 0.72–0.91) and their tradable masks are identical.

## D. Per-hour spread spot-check vs COST_AUTHORITY_TABLE (task d)

Method: `spread = ask_open − bid_open` of the named M1 bar, converted with
the empirically derived pip size (0.0001 / 0.0001 / 0.01); percentiles by
linear interpolation. Comparison table:
`research/control/SLEEVE-FX5-100K-V1/pitcost/COST_AUTHORITY_TABLE.md`.

### (i) Task-required spot check — 20 evenly spaced weekdays, 4 time points

The 20 weekdays span 2021-01-01 → 2026-09-23 (list in
`spread.<pair>.spot_check_20_weekdays.sample_dates`; includes the 2021-01-01
holiday, which is why n_tradable = 19; one further day has a non-tradable
21:30 bar — the roll window can be tick-empty). p50/p90 in pips over
tradable bars:

| pair | 02:00Z | 12:00Z | 20:00Z (fill hour) | 21:30Z (roll) |
|---|---|---|---|---|
| EURUSD | 0.30 / 0.52 | 0.30 / 0.52 | 0.30 / 0.40 | 1.15 / 3.05 |
| GBPUSD | 0.90 / 1.10 | 0.80 / 1.18 | 0.70 / 0.92 | 3.75 / 7.65 |
| USDJPY | 0.60 / 0.92 | 0.40 / 0.76 | 0.40 / 0.72 | 2.80 / 6.25 |

Liquid hours are flat-tight; the roll-window half-hour is 3–10× wider —
consistent with the cost table's C1/C2 split.

### (ii) C1 re-measurement on the full population (the real table check)

All 286 Fridays of the table's window 2021-01-08…2026-06-26, spread_open of
the [20:00,20:01) bar, tradable bars only:

| pair | this audit p50/p90 (n) | COST_AUTHORITY_TABLE C1 | verdict |
|---|---|---|---|
| EURUSD | **0.3 / 0.5** (286/286) | 0.3 / 0.5 (286/286) | **exact agreement** |
| GBPUSD | **0.8 / 1.3** (286/286) | 0.8 / 1.3 (286/286) | **exact agreement** |
| USDJPY | **0.5 / 0.9** (286/286) | 0.5 / 0.9 (286/286) | **exact agreement** |

No discrepancy at the sleeve's fill hour. (All 286 Friday 20:00 bars are
tradable, matching the table's 286/286.)

### (iii) C2 roll window — full-window re-measurement and a MATERIAL flag

Per-minute **close** spread, minutes closing in (21:00,22:00] UTC, tradable
minutes only, full sleeve window (1,140 Mon–Thu days; 286 Fridays):

| pair | (21:00,22:00] Mon–Thu (mine) | table Mon–Thu | (21:00,22:00] Fri (mine) | table Fri |
|---|---|---|---|---|
| EURUSD | **1.2 / 3.7** (n=65,109) | 0.6 / 2.7 | **0.5 / 1.1** (n=5,978) | 0.5 / 1.1 ✓ exact |
| GBPUSD | **2.8 / 7.8** (n=65,274) | 1.4 / 5.8 | **1.2 / 2.3** (n=5,979) | 1.2 / 2.3 ✓ exact |
| USDJPY | **2.1 / 7.4** (n=64,892) | 1.0 / 4.9 | **0.8 / 1.8** (n=5,964) | 0.8 / 1.8 ✓ exact |

The Friday cell reproduces exactly; the Mon–Thu cell does not. Window-variant
localisation (`spread.<pair>.c2_window_variants`):

| pair | Mon–Thu 21:00–22:00Z | Mon–Thu **22:00–23:00Z** | Fri 22:00–23:00Z |
|---|---|---|---|
| EURUSD | 1.2 / 3.7 | **0.7 / 2.6** (≈ table 0.6/2.7) | 0 obs (market closed) |
| GBPUSD | 2.8 / 7.8 | **1.6 / 5.7** (≈ table 1.4/5.8) | 0 obs |
| USDJPY | 2.1 / 7.4 | **1.1 / 4.8** (≈ table 1.0/4.9) | 0 obs |

**Finding:** the table's Mon–Thu roll numbers match the **22:00–23:00 UTC**
hour, not the (21:00,22:00] window its own spec text declares. Since Friday
22:00–23:00Z has zero tradable minutes, the Friday cell can only have come
from the true window — which is why it reproduces. The prior lane's Mon–Thu
cell was therefore measured on an hour-shifted window (method error), and
the **declared** 21:00–22:00 UTC roll window is in fact ~1.5–2× wider at p50
and ~1.3–1.5× wider at p90 than the table states. Materiality: `S_roll =
max(cell p90, general-hour p90)` currently undercharges rollover-window
fills on Mon–Thu (e.g. EURUSD 2.7 vs the true 3.7 pips p90). This cell
should be corrected before any roll-window-sensitive trial is costed.
(For completeness: with the stale-carry minutes included the Mon–Thu
21–22Z numbers barely move: 1.2/3.7 → 1.2/3.7 EURUSD — the discrepancy is
not a tradability-filter artifact.)

### (iv) C3 Sunday-reopen corroboration (small n)

First tradable bar of the 4 sample Sundays, spread_open pips:
EURUSD 1.5 / 8.6 / 15.2 / 0.1 (median 5.05; table p50/p90 5.9/9.0);
GBPUSD 12.9 / 15.7 / 29.7 / 15.0 (median 15.35; table 13.4/23.8);
USDJPY 4.3 / 14.2 / 24.0 / 15.5 (median 14.85; table 11.0/22.0).
Order-of-magnitude agreement on all three; n=4 is corroboration only, the
table cell used n=283/284 full-population Sundays.

### (v) Spread sanity across the whole panels

0 negative spread_open and spread_close minutes anywhere (all 2,092×1,440
minute-slots × 3 pairs); max spread_open observed 33.1 / 40.0 / 53.7 pips
(plausible reopen/news extremes).

## E. Hashes — DATA_FREEZE input (task e)

- `panel_hashes_<PAIR>.jsonl` (3 files, this directory): one JSON line per
  file — `pair, side, file, path, bytes, sha256`; 4,184 lines per pair,
  12,552 total, sorted (side, date) for determinism.
- Aggregate digests (method: sha256 of `"\n".join(sorted
  "<date>|<bytes>|<sha256>" lines)`, side-scoped; pair/overall lines carry
  `<SIDE>`/`<PAIR>:<SIDE>` prefixes — exact method recorded in
  `digests.method` of the summary):

| scope | sha256 |
|---|---|
| EURUSD BID | `26648b89a408f0eec7dfb499b630e658e2bd3b2ecfa139f09424742d3dfa9960` |
| EURUSD ASK | `afee64c7b76a7b15716b4ea0d68b75f8f68ba5e62da338d8b892f0d62b142633` |
| EURUSD pair | `964abbac52132489896e1d193ee9fbb9f9f8e85ef015654d11ba271dcf9bad34` |
| GBPUSD BID | `09aef66d4809333269d9d7b3ae1eec27c24f1fbca2c813c65465b4a68ea2848d` |
| GBPUSD ASK | `eb6325e118615560bf2c527d55923de45fcc5b739c7ce5a5671335699b10cc4c` |
| GBPUSD pair | `9ffb0e4ba747de0ceb6095767c9f08db63b426c4dff98c94de8e61ed85c30fb9` |
| USDJPY BID | `b6be1c4e03da241f26f294afa8e29c8378d46ad529b2f913f31be804b65c8079` |
| USDJPY ASK | `7537dd569e13a244c74546fec1cfa63790283217cd0082028864512183a4b974` |
| USDJPY pair | `57b77f770b29690db1473a058f1215fccbde53838ab34a0cb6268012fe88fdad` |
| **overall (all 12,552 files)** | `d8d9807fbdad8f6ecd253382520a0c33907dd75ef26bb653a2df1c66e58690f3` |

Additionally, the prior manifest's own corpus-digest method (sha256 over
sorted `filename,size` lines, no trailing newline) was reproduced and
matches its recorded per-side values for all 6 sides — see §F.

## F. Provenance cross-check (task f)

`data_manifest_fx.json` was **not** present under the fx-rangefade or
fx-majors control dirs (searched); the only copy is
`.worktrees/portfolio-router-12assets-100k-v1/integration/research/pr12a100k/data_manifest_fx.json`
(schema `pr12a100k.data_manifest_fx@1`, measured 2026-09-28 by the prior
cycle's I1a lane). The staged per-file manifests
`fxm.m1_manifest@1` do exist next to each corpus
(`<PAIR>/m1_manifest.json`), as do `<PAIR>/derived/census.json`.

Agreement matrix (this audit vs prior manifest, per pair):

| check | EURUSD | GBPUSD | USDJPY |
|---|---|---|---|
| side file counts (2092/2092) | ✓ | ✓ | ✓ |
| total bytes per side | ✓ | ✓ | ✓ |
| corpus digest per side (reproduced) | ✓ | ✓ | ✓ |
| file name range / 0 missing days | ✓ | ✓ | ✓ |
| first/last tradable ts | ✓ | ✓ | ✓ |
| tradable_minutes | ✓ (2,130,647) | ✓ (2,130,680) | ✓ (2,131,564) |
| zero_tradable_weekdays = [2021-01-01] | ✓ | ✓ | ✓ |
| **per-file sha256 vs m1_manifest.json** | **4184/4184 ✓** | **4184/4184 ✓** | **4184/4184 ✓** |
| index-manifest hashes (m1_manifest/census/bars1h) | ✓ all 3 | ✓ both | census ✓; m1_manifest **hash typo** (below) |
| largest_tradable_minute_run | **✗ divergent** | **✗ divergent** | **✗ divergent** |

Divergences found (both clerical, neither affects data identity):

1. **`largest_tradable_minute_run: 4321 @ 2024-01-01`, identical for all 3
   pairs, does not reproduce.** This audit measures 5,787 min (EURUSD, from
   Sun 2024-11-17 22:39Z), 4,377 (GBPUSD, Mon 2021-01-25 22:35Z), 5,764
   (USDJPY, Sun 2021-11-28 22:00Z) — distinct per pair, as independent
   feeds should be — and the longest run around 2024-01-01 is only 1,418
   min. The prior value looks like a computation or copy error in the
   prior manifest's `gaps` block.
2. **USDJPY `m1_manifest.json` recorded hash has a one-character typo**:
   claimed `…cec`a`53b36a6c50…`, actual `…cec`e`a53b36a6c50…`
   (position 33). Verified with an independent `shasum -a 256`. The
   per-file hashes *inside* that manifest match this audit 4184/4184, so
   the corpus is unaffected — the prior manifest simply transcribed the
   wrapper-file hash incorrectly. (EURUSD's 3 and GBPUSD's 2 index hashes
   all agree, including the derived `bars1h.parquet`.)

## Verdict summary for the strategy-class gate

| requirement | verdict |
|---|---|
| Panels physically present, complete, decodable | **MEASURED — PASS** (0 gaps/0 anomalies/0 corrupt across 12,552 files) |
| Record format + price scale | **MEASURED — PASS** (format §B fully pinned empirically) |
| Two-sided PIT spread availability | **MEASURED — PASS** (identical BID/ASK masks, 0 negative spreads, 92% weekday minutes active) |
| Volume semantics | **MEASURED — REFUTED premise**: size-weighted per-tick volume sum, NOT a tick count; absolute unit UNVERIFIED (needs instrument metadata/tick files). Strategy labels and any cross-pair absolute-volume logic must be adjusted accordingly |
| Cost table C1 (Friday 20:00 fill spread) | **REPRODUCED EXACTLY** (3/3 pairs, 286/286 Fridays) |
| Cost table C2 roll window | Friday cell **REPRODUCED EXACTLY**; **Mon–Thu cell DISCREPANT — measured on the wrong hour (22–23Z) vs its declared (21:00,22:00] window; true values 1.2/3.7, 2.8/7.8, 2.1/7.4 pips p50/p90 (≈1.3–2× the table). Understates roll-window cost; correct before costing roll-sensitive trials** |
| Cost table C3 Sunday reopen | Corroborated (small n=4, same magnitudes) |
| Hashes for DATA_FREEZE | **DONE** — 12,552 sha256 + per-side/pair/overall aggregates (§E) |
| Provenance | Counts/bytes/digests/per-file hashes **all agree**; 2 clerical divergences flagged (§F) |
| UNAVAILABLE / NOT_RUN | Absolute volume unit (NOT_RUN — not derivable from candles); venue transfer to IBKR (out of scope, remains UNMEASURED per the cost table's own caveat); C3 full-population re-measurement not re-run (table cell corroborated on sample only) |

**Bottom line:** the three panels are physically sound and freezable as-is
(§E digests are the DATA_FREEZE input), the sleeve's headline fill-hour cost
authority is confirmed exactly, but (1) the "tick-volume" premise of the
candidate strategy class is refuted — the volume column is size-weighted,
and (2) the Mon–Thu roll-window cost cell in COST_AUTHORITY_TABLE.md is
measured on the wrong hour and understates the declared window by
~1.3–2×; both must be corrected/relabeled before pool-B trials are costed.
