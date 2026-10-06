# NQ Chain/Roll Reconstruction Integrity Check

Task FUTURES-P3-QUARANTINE-20261004, lane **Q4-DATA-CHECKS**. Generated 2026-10-04 UTC.
Read-only verification of the v2 NQ reconstruction from EXISTING artifacts + light
predicate-filtered reads of the existing chain caches on disk. Machine companion:
`nq_reconstruction_check.json`.

Artifacts under test (all `research/control/FUTURES-DEEPRESEARCH-V2-20261003/`):
`analysis/NQ_build_cache.py`, `analysis/NQ_deep_lib.py`, `analysis/NQ_a3_term.{py,json}`,
`analysis/NQ_cache/` (parquets), `analysis/integration/nq2020_hole_probe.{md,py,json}`,
`dossiers_v2/NQ_DEEP_v2.md` (§0, §3, §7 ERRATUM F1, §10 F1/F6).

Disk re-measurements run by this lane (venv python; predicate-pushdown counts and
date-slices only; NO full scans, no lock):
`NQ_cache/held_volume_k5.parquet` (full read, 26 KB), `NQ_cache/nq_outright_1m.parquet`
(metadata + instrument_id==16908 and raw_symbol=='NQU8-NQM9' filtered counts),
`NQ_cache/nq_annotated_1m.parquet` (6 session-date slices), `NQ_a3_term.json` (full read).

---

## (a) Alias-view rule — documented, NOT applied in the chain build (by design); lineage verified from disk

**Rule under test**: `instrument_id == 16908 AND date < 2020-06-01 → raw_symbol = 'NQM0'`
(ERRATUM F1, dossier §7; probe adjudication `A_ALIAS_NOT_ABSENCE`,
`integration/nq2020_hole_probe.md` "Required fix (VIEW RULE)").

- **Presence**: the rule is present and fully specified in
  `integrity probe nq2020_hole_probe.md §Required fix` and `dossiers_v2/NQ_DEEP_v2.md`
  §7 / §10-ERRATUM-F1, with the 92,075-bar `NQU8-NQM9` alias window
  (2018-08-15→2020-05-31, 24,686,121 contracts) and 19,406-bar `NQM0` relabeled
  window (2020-06-01→06-19, 5,159,596). [FACT(artifact)]
- **Application in the v2 chain build**: **NOT APPLIED — by documented decision.**
  `NQ_deep_lib.py::load_outright_1m()` (L73–84) loads `AV1R-O1M-NQ-DELTA` +
  `AV1T-O1M-NQ` and drops every row whose `raw_symbol` contains "-"
  (`d[~d["raw_symbol"].str.contains("-")]`) — the dash alias chunk is excluded, no
  relabel view exists anywhere in `NQ_build_cache.py` / `NQ_deep_lib.py`. This is
  the documented ERRATUM F1 handling: "handling stays as-is (hole-window sessions
  carry NaN closes; no synthetic jumps)… 2020 aggregates … are recomputable at $0
  and MUST be re-measured before any registered cycle uses them" (dossier §7).
  [OBSERVED: code read `NQ_deep_lib.py:73-84`; FACT(artifact) dossier §7]
- **92,075 / 19,406 lineage verified from disk** [OBSERVED, this lane, script
  window = filtered counts on `NQ_cache/nq_outright_1m.parquet`]:
  - `raw_symbol == 'NQU8-NQM9'` rows in the cached chain panel: **0** (the 92,075
    alias bars are absent — dash-filtered).
  - `instrument_id == 16908` rows: **exactly 19,406**, all `raw_symbol == 'NQM0'`,
    span `2020-06-01 00:00Z → 2020-06-19 13:29Z` — matching the probe's relabeled
    window and its "last bar 2020-06-19 13:29Z" verbatim.
  - Cached panel total rows: **6,688,533** — equals dossier §0 "6,688,533 outright
    ohlcv-1m bars" (7,330,320 parent minus 641,787 dash/spread rows).
- **Alias window boundary verified from disk** [OBSERVED, slices of
  `NQ_cache/nq_annotated_1m.parquet`, session_dates 2020-05-28/29 vs 06-01/02]:
  - 2020-05-28/29: only deferred trickle present (`NQU0_2020` 595 / 687 contracts,
    217 / 181 bars; `NQZ0_2020` stray 3 / 2 bars) — the front is absent from the
    chain cache exactly as documented (the front lives under the excluded alias).
  - 2020-06-01: `NQM0_2020` appears with **326,956 contracts / 1,245 bars**
    (close 9592.50), alongside the NQU0 trickle — the relabel boundary
    2020-06-01 is exact.
- **Held map through the hole** [OBSERVED, `held_volume_k5.parquet` slice
  2020-03-18..2020-06-24]: held stays `NQH0_2020` through (at least) 2020-03-27,
  is `NQM0_2020` by 2020-06-15, rolls to `NQU0_2020` on 2020-06-18 — the chain
  passes through the alias window with hole-aware (NaN-close) sessions; the a3
  script itself flags "2020-hole rolls cross months early: exclude (dte>45)"
  (`NQ_a3_term.py:104`), i.e. the hole-window rolls are quarantined out of the
  daily-crossover DTE stat (n=62 of 66).

**Verdict (a)**: PASS_WITH_DISCLOSED_GAP — rule documented with exact lineage
(92,075 / 19,406 / 6,688,533 all re-verified from disk); chain build intentionally
excludes the alias chunk (NaN-hole handling); **any registered cycle consuming
2020 NQ aggregates must first apply the view rule and re-measure** (ERRATUM F1
obligation, still open).

## (b) k=5 roll rule + cease-guard — 66 rolls confirmed on disk; the k=5 cease hazard is real but did NOT bite NQ

- **k=5 rule**: `NQ_deep_lib.py::front_by_volume_crossover(sess, k=5)` — trailing
  5-session mean volume, crossover to the NEXT quarterly only, decided on data
  through session t. Present and used by `NQ_build_cache.py:83`
  (`held_vol = L.front_by_volume_crossover(sess, k=5)`). [OBSERVED: code read]
- **66 rolls — verified BOTH from the artifact JSON and independently recomputed
  from disk**: `NQ_a3_term.json n_rolls = 66`; this lane's recount of
  `held_volume_k5.parquet` (held != prev-held): **66 switches**, 4,219 sessions,
  span 2010-06-07 → 2026-10-01 — all three equal dossier §0. First roll
  2010-06-15 (NQM0_2010→NQU0_2010), last 2026-09-17 (NQU6_2026→NQZ6_2026).
  [OBSERVED(script+window) + FACT(artifact)]
- **Cease-guard presence**: the implementation has only an *implicit, weak*
  cease-guard: the state switches to the next quarterly when the current
  contract's trailing-k mean goes NaN (`elif pd.isna(cur_v): state = nxt`,
  `NQ_deep_lib.py:266-267`) — i.e., only after the ceased contract has been absent
  a full k-session window. A contract whose *stale* trailing-5 mean still exceeds
  the successor's ramp is held past cessation. That is exactly the
  **2022-09-20 cease-guard artifact law** as established on the sibling
  implementation: 6J dossier §8 ERRATUM M-5 — on 2022-09-20 the exchange was
  open, Z2 traded 125,303 lots, yet the k=5 rule still "held" the ceased U2
  (stale trailing-5 mean > Z2 ramp), silently dropping a live session from the
  1,745-session chain mid-intervention-week (verbatim also in
  `JPY_AUD_HYPOTHESES.md` coverage §10 "2022-09-20 cease-guard artifact law").
  [FACT(artifact) 6J_DEEP_v2.md §8]
- **NQ-specific check around that date** [OBSERVED, `held_volume_k5.parquet` slice
  2022-09-12..23]: NQ rolled `NQU2_2022 → NQZ2_2022` on **2022-09-15**, one day
  before the Sep-16 expiry/cessation — no post-cessation hold, no dropped session;
  the 2022 roll set (03-16, 06-15, 09-15, 12-14) shows no artifact. The cease
  hazard therefore did NOT materialize in the NQ chain, but the rule family
  carries the structural weakness and any future chain builder must add an
  explicit expiry/cessation guard (the 6J law).
- **Roll-table content spot-checks** (see (d) for slice evidence): the max-gap
  roll 2026-06-17 (NQM6→NQU6) carries `spread_pts_roll_day = 302.0` in the JSON,
  matching the independent slice close gap 30,141.75 − 29,839.75 = **302.0 pts**.

**Verdict (b)**: PASS for NQ as built (66 rolls verified twice; roll before
cessation in every checked quarter; 2022-09 clean for NQ); DEFECT-CLASS DISCLOSED
at rule level (weak implicit cease-guard; the 2022-09-20 6J law proves the
failure mode is real in this code family).

## (c) Phantom-drift / NEW-4 — corr 0.999 verified from disk; no adjusted series used as price anywhere

- **corr(roll-day gap, trailing-10-session spread) = 0.999**: verified from disk —
  `NQ_a3_term.json roll_gap_distribution.corr_gap_vs_spreadmed10 = 0.99908`
  (n=65 rolls with valid old-contract roll-day volume). Dossier §3 quotes 0.999 —
  consistent. [OBSERVED(JSON read) + FACT(artifact dossier §3)]
- **Unadjusted-chain drift numbers** verified from the same JSON
  (`unadjusted_chain_embedded_pts_per_year`): 2023 **+722.8**, 2024 **+1,014.0**,
  2025 **+906.8**, 2026 **+809.5** pts/yr — matching dossier §3's "+723, +1,014,
  +907, +810 (~4-5%/yr of price)" phantom-trend hazard statement (2010-16 −5..−31,
  2018-19 +95..+110 also confirmed). [OBSERVED]
- **No adjusted series is used as price anywhere**: `NQ_deep_lib.py` header law
  "No vendor-stitched continuous series: held-contract series are built here from
  per-contract bars"; grep of all NQ analysis scripts finds no
  adjustment/back-fill/stitching code — the only occurrences of "unadjusted" are
  the a3 *measurement* of what an unadjusted chain would embed
  (`NQ_a3_term.py:141-144`), which is a hazard metric, not a series;
  `NQ_a1_regimes.py:26-32` computes returns from raw held closes with "keep NaN
  closes so diff() yields NaN, never a synthetic jump"; a3 closes are raw
  per-contract session closes (pivot of `nq_sessions.parquet` close, /1e9 scale).
  [OBSERVED: code read NQ_a1/a3/deep_lib]

**Verdict (c)**: PASS — artifact numbers exist exactly as cited (0.99908, per-year
embed table) and re-verified; price series are unadjusted per-contract closes with
hole-aware NaNs; the phantom-drift finding is a *measurement of the hazard of NOT
adjusting*, correctly labeled.

## (d) Disk slice spot-verification (caches PRESENT — all checks OBSERVED-from-disk, none NOT_RUN)

Chain caches exist on disk under `analysis/NQ_cache/` (nq_outright_1m.parquet
147,517,755 B; nq_annotated_1m.parquet 176,114,434 B; held_volume_k5.parquet;
held_calendar.parquet; nq_sessions.parquet; nq_held_daily.parquet;
contract_registry.json). Three roll dates + the alias boundary re-verified by
date-filtered slices (results in `nq_reconstruction_check.json.spot_checks`):

| Roll session | old → new | old/new session closes (pts, /1e9) | roll-day volumes old vs new |
|---|---|---|---|
| 2010-06-15 | NQM0_2010 → NQU0_2010 | 06-14: 1847.75 / 1846.75 · 06-15: 1893.00 / 1891.75 | 27,756 vs 300,116 |
| 2022-09-15 | NQU2_2022 → NQZ2_2022 | 09-14: 12169.0 / 12250.0 · 09-15: 11904.0 / 11973.0 | 132,245 vs 712,732 |
| 2026-06-17 | NQM6_2026 → NQU6_2026 | 06-16: 29986.50 / 30300.50 · 06-17: 29839.75 / 30141.75 | 34,849 vs 531,548 |

All three: both legs have bars+closes on the roll session AND the prior session
(no gap), the new contract already dominates roll-day volume (k=5 crossover
mechanics confirmed), and the 2026-06-17 close gap is exactly the JSON's 302.0
max-gap. Alias boundary (2020-05-28/29 vs 06-01/02) as detailed in (a).

**Verdict (d)**: PASS — OBSERVED-from-disk for every check (nothing NOT_RUN-per-disk).

## Overall verdict

**NQ reconstruction integrity: CLEAN as built, with two disclosed obligations:**
1. ERRATUM F1 obligation (open): apply the alias view rule and re-measure all
   2020 aggregates before any registered cycle consumes them.
2. Rule-family defect (structural, proven on 6J): add an explicit cease-guard to
   any future k=5 chain builder; NQ's own 66 rolls show no manifestation
   (spot-checked quarters roll 1+ day pre-cessation).

| Check | Result | Taxonomy |
|---|---|---|
| (a) alias rule presence + lineage | documented; NOT applied by design; 0 / 19,406 / 6,688,533 re-verified from disk | FACT(artifact) + OBSERVED(script+filters) |
| (b) k=5 + cease-guard | 66 rolls verified twice; weak implicit guard; NQ 2022-09 clean; 6J 2022-09-20 law cross-cited | OBSERVED + FACT(artifact 6J §8) |
| (c) corr 0.999 / no adjusted price | 0.99908 + embed table verified; no adjustment code | OBSERVED(JSON) + OBSERVED(code read) |
| (d) disk slices | 3 rolls + alias boundary verified; caches present | OBSERVED(script+date-filters) |
