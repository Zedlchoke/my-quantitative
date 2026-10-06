# DELTA-VERIFY-SOURCE — independent verification of NONPRICE-SOURCE-FIX2

Lane `DELTA-VERIFY-SOURCE` (fresh-context; original auditors lost to power
outage) · task `FUTURES-DEEPRESEARCH-V2-20261003` · 2026-10-03 · worktree
`prep` @ `26d96eb4bdd4be85e151055dace3354638498a44` (branch
`prep/futures-behavior-10syms-20261002`, `git rev-parse HEAD` verified).
READ-ONLY except this directory + `dispatch/handoff_DELTA-SOURCE.json`. No
network, no key use, no raw/data writes. Nonprice + vendor data dirs treated
read-only throughout.

Scope: verify the source-level fixes of implementer `NONPRICE-SOURCE-FIX2`
(resumed after the outage) against audit findings `A7_INTEGRATION.md`
F-1/F-2/F-3 (+ F-4/F-5/N-2) and `A7_DEEP_6J.md` MAJOR-1. Method: independent
re-derivation from raw (my own parsers/queries, never the lane's measurement
code), plus one full rerun of the shipped test suite.

## VERDICT: **PASS — 9/9 findings VERIFIED, 0 NOT_VERIFIED, 0 new findings**

| # | Audit finding | Required fix | Verdict |
|---|---|---|---|
| D-1 | A7-INTEGRATION F-1 (fin tidy 365 dup dates/series) | dedupe + precedence + gate + test | **VERIFIED** |
| D-2 | A7-INTEGRATION F-1 incident (power-outage inverted precedence) | annual-wins pin; `.bak_bulkwins` | **VERIFIED** |
| D-3 | A7-INTEGRATION F-2 (NQJ0 "422" misreport) | 504/NOT_RUN retraction; 8 calls | **VERIFIED** |
| D-4 | A7-INTEGRATION F-5 + N-2 (alias uniqueness; 51) | instruments 2563+2173; 49+9 | **VERIFIED** |
| D-5 | A7-INTEGRATION F-3 (old fin rows 17,337 wrong) | report VI correction to 13,898 | **VERIFIED** |
| D-6 | A7-INTEGRATION F-4 (spread total +100,000) | 2,537,950 in contaminant_scan.md | **VERIFIED** |
| D-7 | A7-DEEP-6J M-1 (MOF 81 vs 386 ops) | rebuild tidy + recount + .bak | **VERIFIED** |
| D-8 | Suite regression coverage | rerun, expect 59/59 | **VERIFIED** |
| D-9 | Report VI NONPRICE-SOURCE-FIX2 erratum block | present + fin chain corrected | **VERIFIED** |

---

## D-1. Fin tidy dedupe (F-1) — VERIFIED

`~/.my-quantitative-data/futures-nonprice-10syms/normalized/cftc_tff_disagg_tidy.parquet`
read directly with pandas (my own count, not the lane's):

- sha256 `c3ba5391d3e3c4d9fa123e59123399573489beafd76929d890c5957d11c62936`
  (== handoff). **15,065 rows, 23 distinct `series_id`.**
- **Duplicate-date count per series, recomputed for all 23 series: 0 in every
  series** (10 canonical at exactly 1,059 rows each — DISAGG CL/GC/NG/SI,
  TFF ES/NQ/6E/6J/6A/6B, all full-span 2006-06-13..2026-09-22 — plus 13
  `__ALT__` series, 4,475 rows, 0 dups). Total duplicate-date rows: **0**.
  The pre-fix state (per the shipped regression test message and my read of
  the preserved `1dbb5e93` backup, below) was 1,825 dup rows — now 0.
- Backup chain on disk, all preserved and identified by sha:
  - `.bak_dup_overlap_20261003` = **1dbb5e93…**, 15,170 rows — the
    INTEGRATION-FIX-V2 output F-1 was written against; my own recount of it
    shows the defect state: COT_DISAGG_CL/GC = **365 dup dates each**
    (1,424 rows over 1,059 distinct dates), TFF series 0 — exactly F-1.
  - `.bak_bulkwins_20261003` = **3e32e0ee…**, 15,065 rows (see D-2).
- Code: `normalize/cftc_normalize.py` implements `_from_bulk` source map →
  descending sort → `drop_duplicates(keep="last")` (annual sorts last =
  annual wins), an `assert_fin_clean()` generation gate (line ~399) and a
  generation-time conflict log; docstring discloses the incident.

## D-2. Annual-wins precedence pin + outage incident (F-1 incident) — VERIFIED

Pin cell `COT_TFF_6A` 2016-05-31 `Pct_of_OI_Lev_Money_Long_All`, traced to
**raw** in `~/.my-quantitative-data/futures-nonprice-10syms/cftc/tff/` (my
own zip readers):

| source | raw value read by me | zip sha256 |
|---|---|---|
| annual `fut_fin_txt_2016.zip` (`FinFutYY.txt`, ISO dates) | **23.9** | `e8570bcd…` |
| bulk `fin_fut_txt_2006_2016.zip` (`F_TFF_2006_2016.txt`, `5/31/2016 12:00:00 AM`) | **24.000000** | `c3a8d017…` |

- FINAL parquet cell = **23.9**, `source_zip=fut_fin_txt_2016.zip`,
  `provenance_sha256=e8570bcd…` → annual value kept, provenance matches the
  raw zip bit-for-bit.
- `.bak_bulkwins` (the power-outage intermediate `3e32e0ee`) = **24.0**,
  `source_zip=fin_fut_txt_2006_2016.zip`, provenance `c3a8d017…` → the
  inverted-precedence state is preserved exactly as disclosed. **Preserved:
  YES.**
- Full diff FINAL vs `.bak_bulkwins` (my merge): **row set identical
  (15,065/15,065), exactly 4 value-cell differences** — all `Pct_of_OI_*`
  rounding cells (6A 2016-08-02 8.4/8.5, 6A 2016-05-31 23.9/24.0, 6B
  2016-03-01 6.3/6.4, ES-ALT-consolidated 2016-08-16 12.9/13.0) — **plus
  4,983 rows whose source_zip/provenance re-attribute to annual zips**.
  Matches the handoff's diff claim exactly.
- Side-confirmations from raw: the bulk TFF file really uses `M/D/YYYY`
  dates (vs ISO in annual) — the date-parse fix was necessary; canonical TFF
  floor 2006-06-13 with 1,059 rows verified in the parquet.

## D-3. nq2020_hole_probe.md — NQJ0 relabel + call count (F-2) — VERIFIED

`analysis/integration/nq2020_hole_probe.md` (sha `6f24182f…`, == handoff):

- Erratum block item 1 + the evidence table row now read **"HTTP 504 gateway
  timeout — probe timed out; serial coverage NOT_RUN"**, with the "422 /
  unresolvable / not in feed" claim explicitly **retracted** (stated as
  supporting nothing about resolvability). The untouched JSON artifact and
  the INTEGRATION-FIX-V2 handoff still carry the old narrative string —
  correctly left as recorded artifacts; the md erratum supersedes both.
- Call count: erratum item 2 + body now say **"8 metadata calls"**
  (record_count ×6 incl. the timed-out NQJ0 attempt, get_cost ×1,
  billable_size ×1) with the "7" explicitly marked wrong.

## D-4. Alias uniqueness + session arithmetic (F-5, N-2) — VERIFIED

- The md erratum item 3 documents **instruments 2563 and 2173** with the
  generalized family+time-contiguity view-rule recommendation (16908 ✓,
  2563 ✓, 2173 ✗ cross-family collision → stays quarantined). I re-queried
  the vendor parquet myself (`AV1R-O1M-NQ-DELTA`, `AV1R-O1M-ES-DELTA`,
  `AV1B-O1M-6B-BACKFILL2`):
  - id **2563**: `NQH5-NQM5` 5,946 bars 2014-12-18..2016-05-31, then
    `NQU6` 92,208 bars 2016-06-01..09-16 — matches the md and audit F-5.
  - id **2173**: 1 `ESU6-ESU7` bar 2016-08-04 (ES delta) + `6BX1` 629 bars
    2021-08-04..2021-11-15 (6B backfill2) — matches the md exactly.
- Session arithmetic: the md now states **"58 dates = 49 weekdays + 9 Globex
  Sunday opens, Good Friday 2020-04-10 closed"** with DEEP-NQ's "51" marked
  a weekday-only count (49+9 = 58 ✓, consistent with A7-INTEGRATION's
  independently verified 58-date/0-gap window).

## D-5. Old fin row count 13,898 (F-3) — VERIFIED

Report VI NONPRICE-SOURCE-FIX2 erratum carries an explicit correction of the
INTEGRATION-FIX-V2 erratum's figure: old `d798ed27` file = **13,898 rows**
(not 17,337), with the per-series breakdown (DISAGG CL 2,708 / GC 1,588 /
NG 1,434 / SI 1,429; TFF ES 1,966 / NQ 1,393; FX 845×4) — which I
re-summed: **= 13,898 exactly**, and which matches A7-INTEGRATION F-3's
mirror-verified measurement. The correction is an adjacent correction-on-
erratum (the 2026-10-02 block's historical text left intact, superseded
explicitly) — proper evidence-trail practice, not a silent rewrite. The old
`d798ed27` file is indeed no longer on disk; evidence remains the
SHA-verified DATA-BACKUP mirror + the preserved `1dbb5e93` successor.

## D-6. Spread total 2,537,950 (F-4) — VERIFIED

`analysis/integration/contaminant_scan.md` (sha `3fc9f36e…`, == handoff):
- Erratum banner states the prose total overstated by exactly 100,000 and
  gives the corrected **2,537,950**; the view-rule section body also carries
  the corrected figure with an inline ERRATUM note.
- Arithmetic re-verified by me: 641,787 + 884,863 + 375,722 + 275,066 +
  189,039 + 171,473 = **2,537,950** (per-root numbers unchanged, and already
  independently bar-verified by A7-INTEGRATION's rescan).
- Grep: "2,637,950" survives only inside the erratum explanations — no
  uncorrected authoritative use.

## D-7. MOF tidy rebuild (A7-DEEP-6J MAJOR-1) — VERIFIED

`~/.my-quantitative-data/futures-nonprice-10syms/normalized/mof_intervention_tidy.parquet`:

- sha256 `6a5ce702ff03531e3e067846429aef77c77028f6fb652a8f627651825b87accb`
  (== handoff). **386 rows**, 1991-05-13 → 2026-05-06 (== audit M-1's true
  record bounds; kills the old "81 ops" / "1991-04" header claims).
- **2022-10-24 present**: `value_yen_100m = 7,296` (× ¥100m = **¥0.73T**),
  `direction = JPY_buying`,
  `pair_desc = "the US dollar (sold) the Japanese yen (bought)"` — the exact
  op the audit proved was dropped (raw row 519, blank year AND month cells —
  I confirmed that raw line myself: `,,24日,,,24,"7,296",米ドル売り・日本円買い,…`).
- `.bak_81rows_20261003` preserved: **81 rows** (pre-fix undercount state).
- **Independent row-set re-verification against the raw CSVs** (my own
  Shift-JIS parser: era-year map 平成/令和, month from either the JA or EN
  column with carry-forward over blank merged cells, day from `日` or the
  numeric column, quarterly 期計 total rows excluded):
  - Full-file recount: **386 daily ops, 0 unresolved rows**; set equality
    vs the tidy parquet on (date, amount, direction): **0 missing, 0
    extra** — 386 == 386 exact, stronger than the required 3-month sample.
  - Required 3-month sample incl. one blank month — Sep/Oct/Nov 2022:
    Sep: recount [09-22 ¥28,382] == parquet; **Oct: [10-21 ¥56,202,
    10-24 ¥7,296] == parquet** (10-24 is the blank-month carry-forward row);
    **Nov (fully blank month): [] == []** — no phantom rows created by the
    carry-forward, no absorption of the Q4 期計 total row.
  - Cross-check: Q4-2022 daily sum 56,202 + 7,296 = 63,498 vs CSV quarterly
    total 63,499 (+1 MOF rounding unit) — matches audit M-1 and the
    regression test.

## D-8. Test suite rerun — VERIFIED (59/59, exit 0)

Command (from worktree root):
`/Users/hoangminhlong/my-quantitative/.venv/bin/python research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/nonprice_acquisition/tests/test_parse.py`
→ last line **"59/59 tests passed"**, **exit code 0**; 59 `PASS` lines
counted. The 11 new regression checks are present and pass, including:
`cftc_fin_zero_duplicate_dates_all_series` (15,065 = 10,590 canonical +
4,475 ALT; pre-fix 1,825 dups → 0), `cftc_fin_dedupe_annual_wins_precedence_pin`
(23.9 from `fut_fin_txt_2016.zip`), `cftc_fin_disagg_canonical_1059_full_span`,
`cftc_fin_tff_floor_2006_regained` (845@2010-07-20 → 1,059@2006-06-13),
`cftc_fin_value_columns_present`, `mof_record_386_daily_ops_1991_05_13`,
`mof_2022_10_24_jpy_buying_op_recovered` (¥0.73T; Q4-2022 63,498 vs 63,499),
`mof_inwindow_2020s_op_count_10_not_9`,
`mof_q4_2022_daily_sum_matches_quarterly_total`,
`mof_tidy_set_equals_raw_carryforward_recount` (386==386, 0 missing/extra).
Legacy checks unchanged (10 × 1,082 weeks, 0 dups).

## D-9. Report VI erratum block — VERIFIED

`research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/nonprice_acquisition/PUBLIC_DATA_ACQUISITION_REPORT_VI.md`
(sha `b39900ec…`, == handoff): block
**"## ERRATUM 2026-10-03 (lane NONPRICE-SOURCE-FIX2, …) — MOF thiếu 305 ops
+ fin tidy trùng archive-overlap"** present (line 114), covering: MOF 81 →
386 with `.bak_81rows` + carry-forward mechanism + 2022-10-24 recovery +
2020+ ops 9 → 10 + set==recount; fin dedupe chain `1dbb5e93` → `c3ba5391`
with annual-wins rule, 1,825 dup rows, TFF date-parse fix and value-column
carry; the power-outage INCIDENT with the inverted `3e32e0ee` intermediate
preserved as `.bak_bulkwins` and caught by the 23.9/24.0 pin; the F-3
correction (D-5); the md-correction index (D-3/D-4/D-6); tests 48/48 →
59/59. Every number in the block cross-checks against my own measurements
above.

## Process reconciliation (advisory, all clean)

- All 9 handoff-declared output sha256s re-verified **9/9** (4 tracked files
  + 2 mds + 3 out-of-tree parquets incl. bit-identical legacy `f7a2719e`).
- `git status` matches the handoff `tree_status`: exactly 4 tracked mods
  within grant; foreign FX-BACKFILL changes (`COMPLETION_LEDGER.json`,
  `backfill_20261003/`) present and untouched; this lane's writes confined
  to `audit/delta/source/**` + `dispatch/handoff_DELTA-SOURCE.json`.
- No raw/vendor writes by the fix lane observed (nonprice raw mtimes
  2026-10-02; only normalized/ + .bak files carry Oct-3 mtimes).

## Advisory notes (no action required for this delta; for the owner)

1. Residual wrong "422" strings remain in two *recorded* artifacts
   (`nq2020_hole_probe.json` adjudication narrative and
   `handoff_INTEGRATION-FIX-V2.json`) — deliberately not rewritten; the md
   erratum supersedes. Consumers must read the md, not the JSON narrative.
2. The iCloud DATA-BACKUP normalized mirror is stale (still `1dbb5e93`-era
   fin tidy; current = `c3ba5391` fin + `6a5ce702` mof) — disclosed;
   re-sync is a backup-lane/owner action.
3. DEEP-6J dossier errata (M-1..M-5) still owed by the dossier lane/owner;
   the source side (this delta) is now clean.

Nothing here is a GO; verification/infrastructure only. Prep law intact.
