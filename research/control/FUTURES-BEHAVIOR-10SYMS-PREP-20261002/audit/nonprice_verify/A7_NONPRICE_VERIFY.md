# A7-NONPRICE-VERIFY — independent audit of NONPRICE-DATA-ACQUISITION

Task `FUTURES-BEHAVIOR-10SYMS-PREP-20261002` · Lane `A7-NONPRICE-VERIFY` (fresh-context auditor)
Date 2026-10-02 · Base HEAD `8ce10f7e4b43a0234f33d27fb8e4532b7ff65f9e` (unchanged; audit commits nothing)
Scope: `nonprice_acquisition/**` (uncommitted, in-repo) + raw `~/.my-quantitative-data/futures-nonprice-10syms/` (READ-ONLY; `acquisition_download/` never touched).

## Verdict

**PASS_WITH_FINDINGS** — 0 BLOCKER, 2 MAJOR, 5 MINOR, 4 NOTE.

The raw archive is genuine, complete-as-claimed, and fully hash-reconciled; the PIT
machinery (released_at vs observation separation, NOT_PIT flags, issued-vs-observed
separation, no-future-rows) is real and test-enforced (29/29 reproduced independently,
exit 0, log digest identical to the lane's own). The WNGSR-embedded The Desk survey
claim is **verified real and correctly typed** (significant free-consensus source,
2018+, owner adjudication required). The two MAJORs are: (1) an unreliable
`net_change_bcf` column shipped in the WNGSR tidy table; (2) readiness status-label
optimism — one outright mislabel (`6J-H3 READY_DATA` with a named MISSING leg) plus
granularity caveats not carried into status labels. Neither invalidates the archive;
both must be fixed or fenced before downstream use.

## 1. Raw sample verify (all 6+ required sources) — VERIFIED

**Full re-hash, not just sampling:** all 10,520 unique `ok` paths in
`raw_manifest.jsonl` (12,550 records: 10,579 ok / 1,960 http_error / 11 wait_storage)
re-hashed against disk: **0 missing, 0 sha256 mismatches, 0 size mismatches**.
Only on-disk extras: 14 `normalized/*.parquet` outputs (expected). Manifest totals
reconcile exactly with the claims: 10,579 ok records / 1,348,112,607 B = 1.348 GB;
`du` = 1.289 GiB incl. normalized — the "1.35 GB / 2 GiB cap" claim holds.

| Source (family) | Claim | Measured | Content-class check (opened files) |
|---|---|---|---|
| CFTC CoT legacy | 59 files, 85.8 MB, 2006-01-03→2026-09-22 | 21+18+18+2 ok records; tidy shows 9/10 symbols 2006-01-03 start, NQ 2010-06-15 (official consolidated series start) | `deacot2015.zip`→`annual.txt` = genuine CFTC legacy futures-only schema (As-of-Date Tuesday, noncomm/comm/reportable cols) ✓ |
| EIA WNGSR | 1,205 HTML + 254 PDF | 1205 + 254 exactly | Issues are per-week as-published pages; The Desk survey text present (§5) ✓ |
| EIA WPSR | 790 issues + 3,120 tables | 790 + 2370 CSV + 750 PDF exactly; +errata sheet + 2 dnav | `2026_07_29_ttable4.csv` has the `Cushing` row; table1 has crude commercial/SPR/gasoline ✓ |
| FRED/ALFRED | 12 latest + 122 vintages | 12 + 122 exactly | Vintage files carry column pinned to vintage date (e.g. `DGS10_20121231`), **zero post-vintage observations across all 122** ✓ |
| NOAA CPC issued | 4,459 daily + 65 weekly + 31 pilot, 2012-09-11→2025-06-30 | exact; first/last filenames = `610temp_20120911`/`610temp_20250630` | Zips contain issued shapefile forecast sets (`.shp/.dbf/.prj`); internal file mtime = issue date; inventory `issued_at` from filename, separate table from observed ✓ |
| FOMC | 147 statements | 147 on disk | `monetary20120801a.html` = genuine as-issued statement ("For immediate release", Bernanke-era text) ✓ |
| BoJ / MOF | 181 BoJ statements; MOF daily 1991-04+ | BoJ **180** on disk (see MINOR-1); MOF CSV = genuine Shift-JIS intervention file, period April 1991+, 81 daily ops in tidy | `k220922a.html` = genuine BoJ MPM statement 2022-09-22 ✓ |

All manifest hosts are official primaries (cftc.gov, eia.gov/ir.eia.gov,
federalreserve.gov, boj.or.jp, mof.go.jp, ecb.europa.eu, bankofengland.co.uk,
ons.gov.uk, gov.uk, rba.gov.au, bls.gov, *.stlouisfed.org, cpc.ncep.noaa.gov,
ncei.noaa.gov, noaa-ndfd-pds S3). No third-party mirrors, no key/token params in any URL.

## 2. Normalized / PIT laws — VERIFIED (tests reproduced)

Reran `nonprice_acquisition/tests/test_parse.py` myself:
**29/29 PASS, exit 0**, log digest `ce86025a753a2fd6fb1953e5a3a32eb40af28b67d9c539ef43925d22894f89b8`
— byte-identical to the lane's recorded digest.

- released_at vs observation_period: CFTC tidy separation 2–4 days (Tuesday as-of →
  following-Friday convention string `…T15:30:00-05:00/America_New_York_convention`),
  enforced by test across all 13,369 legacy rows. ✓
- Revised-latest NOT presented as PIT: `fred_latest_tidy.vintage_flag ==
  'latest_revised_NOT_PIT'` on all 101,898 rows (tested); latest-vs-vintage
  distinguishability proven (24,561 differing values across 5 series). ✓
- ALFRED vintages flagged `pit_snapshot_asof_{date}`; per-file column/date audit
  (mine, all 122): pinned columns, no observation after its vintage date. ✓
- Issued vs observed weather: two separate parquet tables, disjoint series_id sets
  (`CPC_*_ISSUED*` vs `NCLIMDIV_*`), tested. Observed HDD/CDD uses official divisional
  files with **pre-declared frozen** census weights (`hdd_cdd_weights.py`
  "frozen-by-declaration" header; nearest-prior-census anchor = real-time knowable). ✓
- No-future-rows test exists and passes on 7 tables (max dates all ≤ 2026-10-02). ✓
- TFF/disagg backcast caveat: present in code (`classification_backcast_NOT_vintage`,
  `first_available_at=None`), manifest_sources WARNING, and report. ✓
- MOF `official_history_published_with_lag`, BoE gilt `DECLARED_LAG` route. ✓

## 3. WNGSR-embedded survey — **CLAIM UPHELD** (precise typing below)

Opened issues across years (2012, 2016, 2019, 2023, 2024):

- 2019-09-12: "According to **The Desk survey** of natural gas analysts, estimates of
  the weekly net change … ranged from net injections of 74 Bcf to 95 Bcf, with a
  **median estimate of 82 Bcf**." → tidy: median 82, low 74, high 95, direction
  injections. Correct.
- 2024-01-18: median 163, range 132–176 withdrawals → tidy matches exactly. Correct.
- 2023-01-12: median present in raw ("median estimate of net withdrawals of 3 Bcf")
  but **missed by the extractor** (see NOTE-1).
- 2016-01-14: pre-2018 phrasing "Market expectations, on average, called for a
  withdrawal of 178 Bcf" — exists in raw, not extracted as survey (different semantics:
  an average, not The Desk median; The Desk quoting starts 2018).
- 2012-05-31: no survey text at all (only EIA boilerplate) — consistent with coverage
  table below.

Tidy coverage by year (issues / totals parsed / survey-median parsed): survey medians
exist **2018+ only** (2018: 32/49 … 2022: 50/50 … 2026: 3/3; total 352). Totals parsed
693/1205 all-era, 93.17% for 2014+ (test asserts ≥90%; report said "93–100%" — matches).

**Adjudication:** the WNGSR issue as published on release Thursday embeds the
pre-release consensus (median + range) *in the same document* as the actual — so
actual-vs-consensus surprise is computable from one as-published primary-source file,
free. This is a genuine, significant free-consensus record. Bounds that must travel
with it: (a) coverage starts 2018 (pre-2018 raw carries a differently-phrased
"market expectations (average)" sentence, unextracted); (b) ~5–10% of 2018+ issues
miss the survey or the parse; (c) it is median+range only, not a per-analyst vendor
archive; (d) numbers are The Desk's as quoted by EIA (public/official text). The
lane's typing ("NOT a vendor consensus archive; owner adjudicates fitness" for NG-H1)
is exactly right. **Owner should adjudicate NG-H1 consensus fitness with these bounds.**

## 4. Hypothesis readiness re-derivation — statuses mostly honest; labels need repair

Recomputed from `hypothesis_readiness.json`: 34 READY_DATA / 7 BLOCKED_CONSENSUS /
6 PARTIAL-family (2 PAID_OWNER + 2 NOT_RUN_PIT_GFS + 1 PARTIAL + 1 DECLARED_LAG) /
2 VENDOR_PAID-family / 1 MISSING = 50. (Dispatch's "3 PAID" counts ES-H2/SI-H3's paid
pieces inside PARTIAL_PAID_OWNER; the JSON's own taxonomy is authoritative.)

Cross-checked ≥12 against `configs/symbols/*.yaml` + raw files:

- **NQ-H2 (READY)** — CoT legacy 2006+/2010+ acquired, release convention encoded and
  tested. NOTE-3: config's named field is *leveraged-fund* net (TFF) which is only
  available backcast-flagged; the PIT-clean series is legacy noncommercial. Archive
  floor as written is met; owner should note the proxy.
- **NQ-H1 (READY)** — see MAJOR-2 (year-end vintage granularity vs config's
  "first-release vintage mandatory").
- **6J-H3 (READY)** — see MAJOR-2 (TONA leg named MISSING_ROUTE).
- **GC-H1 (MISSING)** — correct: `serial_contracts_refetch` is the IBKR-entitlement
  6-serial GC re-fetch, a data-lane action, time-critical ~Q1-2027. Correctly not
  pushed onto nonprice-public.
- **NG-H1 (PARTIAL)** — honest and well-typed (survey partial coverage + M1 vendor
  gate + archive starts 1996 vs floor 1994, disclosed).
- **NG-H2/NG-H4 (PARTIAL_NOT_RUN_PIT_GFS)** — honest: GFS/NDFD vintages measured
  unobtainable free (NDFD bucket not S3-versioned); CPC issued is the PIT-legal
  forecast series from 2012-09; config's observable (GFS 00Z vintage revisions) is a
  *different product* — the lane says so rather than substituting. Good.
- **ES-H2 / SI-H3 (PARTIAL_PAID_OWNER)** — rates legs done (DTB3/SOFR vintages+latest);
  dividend-yield / LBMA lease legs named paid. Honest.
- **CL-H3 (VENDOR_PAID_PARTIAL)**, **6A-H2 (VENDOR_PAID)**, **6B-H3
  (PARTIAL_DECLARED_LAG)** — exact missing pieces named; gilt latest-vintage only;
  gov.uk budget collection 404 recorded. Honest.
- **BLOCKED_CONSENSUS ×7** (NQ-H3, ES-H3, GC-H2, CL-H2, 6E-H3, 6E-H4, 6B-H2) — no
  free as-issued consensus archive exists; actuals never substituted. Verified no
  fabrication anywhere.
- **6E-H2 (READY)** — SOFR + ESTR: fine for the descriptive minimal test (same
  year-end-vintage caveat class as NQ-H1).
- **ES-H4 (READY)** — FOMC-date leg legal (147 statements + calendars); CPI-date leg
  approximated (see MAJOR-2 / MINOR-5).

## 5. Hygiene — VERIFIED

- **Secrets:** none. `OWNER_ONLY_STEPS.md` contains only *instructions* for the owner
  to store future keys (`read -s`, chmod 700/600) — no values. No `.env`/credential
  files in the lane; no api_key/token params in any of 12,550 manifest URLs (the
  32-char regex hits are just sha256s).
- **Licenses:** every URL is a public/official primary host (table §1); excluded
  paywalled classes are enumerated in `manifest_sources.excluded_by_design`
  (LBMA, S&P div-yield, HG/iron-ore, RB/HO, Databento, GDELT-BigQuery). No paywalled
  content fetched.
- **Disk:** 1.348 GB manifest-summed / 1.289 GiB `du` vs claimed 1.35 GB; cap 2 GiB,
  NOAA subcap in code (`1_181_116_211` B). Consistent.
- **Rate limits / dedupe:** politeness 0.5–1.0 s per source in code + manifest
  (report's "0.15–1s" floor not found in code — cosmetic). `retrieved_at_utc` on every
  record. 60 duplicate (url, sha) fetch pairs / 10,579 (0.6%): 58 are ALFRED
  vintage files fetched twice ~20 s apart (consistent with the deliberate
  vintage-column verification pass), 1 CPC zip, 3 NCEI dir listings — identical shas,
  no integrity impact (MINOR-2).
- **403/404 gates recorded, not bypassed:** BLS site + download.bls.gov, RBA
  (int-rate-decisions 404; cash-rate page 200 archived), ir.eia.gov (except
  schedule.html), CPC /products/archives/*, gov.uk budget collection; EIA archive
  403s on some pre-2005 WNGSR issues (explains the 1,506-enumerated vs 1,459-stored
  delta in manifest_sources' measured finding). `collect/common.py` breaks on
  403/401/407/451 without retry-bypass and records the gate. ✓
- **wait_storage (11)**: matches report exactly (3 CPC big files, climdiv
  tmax/tmin `-inv` deliberately skipped, 1 BoJ PDF >4 MB with same-day HTML sibling,
  1 BLS bulk probe).

## Findings

### BLOCKER — none.

### MAJOR

**M-1. `net_change_bcf` in `eia_wngsr_vintages_tidy.parquet` is unreliable (first-mention grab).**
The regex takes the first "net injection/withdrawal of X Bcf" anywhere in the issue,
which is often NOT the actual weekly change. Measured: agrees with the
consecutive-totals difference in only **62/561 (11.1%)** of comparable rows. Concrete
misgrabs verified against raw text: `2016_01_14`→178 (the *market expectation*),
`2016_03_17`→19 (an *analyst prediction*), `2018_10_11`→74 (*The Desk survey range
low*), `2023_01_12`→157 (*last year's* same-week value; actual ≈190),
`2019_03_14`→99 (*five-year average*; actual 204). Not covered by any test; not
claimed in the report — but it ships in a tidy table named "vintages" and is a
landmine exactly where NG-H1 surprise work will look. **Fix: drop the column or
recompute from consecutive as-published totals; never consume as-is.**

**M-2. Readiness status-label optimism (one outright mislabel + granularity caveats not carried into labels).**
- `6J-H3 = READY_DATA` while its own `pieces.boj_tona` says `MISSING_ROUTE`, its own
  `manifest_sources.hypothesis_to_needs` lists `boj_tona` as REQUIRED, and the report
  §3 narrative itself lists 6J-H3 among the PARTIALs ("thiếu TONA daily free-route").
  Internal contradiction; correct class is PARTIAL (named TONA piece missing).
- `ES-H4 = READY_DATA` with the date-level CPI calendar typed MISSING/approximated in
  its own pieces (FOMC leg is genuinely ready).
- NQ-H1 / GC-H5 / CL-H4 / 6E-H2 (+ rates legs of ES-H2, SI-H3): labelled READY_DATA on
  **year-end-only** ALFRED/ESTR vintage granularity, while the configs demand
  "ALFRED first-release vintage mandatory". Year-end snapshots cannot supply
  same-year daily values at decision time (a June-2023 snapshot does not exist; the
  latest available is 2022-12-31), so the strict-PIT daily trigger is not computable
  from what was acquired without the owner-key route. All disclosed in
  pieces/known_limitations — but the status label does not carry the granularity
  caveat, and 6J-H3/ES-H4 contradict the lane's own evidence. **Fix: relabel 6J-H3
  (and ES-H4's CPI leg) and add a vintage-granularity qualifier to the rates-family
  READY labels, or get the owner key.**

### MINOR

- **m-1.** BoJ claim "181 statements" = URLs enumerated; **180 on disk** (one PDF
  `k241219b.pdf` wait_storage'd >4 MB; its same-day statement sibling exists).
  Additionally the normalized inventory (`boj_fomc_statement_inventory.parquet`)
  carries only the 66 HTML statements (2018+) — the 114 PDFs (2010–17) are archived
  raw but not inventoried in tidy.
- **m-2.** Dedupe claim slightly overstated: "re-running does not re-download" is true
  across runs (checkpoint logic verified), but 60 within-session duplicate fetch
  pairs exist (see §5). "10,579 files" counts manifest records; unique files = 10,520.
- **m-3.** Dead, misleadingly-named probe file
  `fred_alfred/pit/DFII10/DFII10_asof_2024-12-31.csv` actually contains the LATEST
  vintage (column `DFII10_20261002`, observations through 2026-09-30) — the
  `realtime_start/realtime_end` route ignores those params (correctly measured and
  disclosed in manifest_sources `vintage_method`). Not ingested by any normalizer, but
  its path under `pit/` invites future misuse. Rename/remove with a manifest note.
- **m-4.** `issue_date_raw` in the WNGSR tidy is unreliable (first "Month DD, YYYY"
  match anywhere in the page; e.g. `2016_01_14` → "2016-January-13", non-ISO). The
  tests correctly use the filename date; consumers must too.
- **m-5.** Config vs finding conflict: `6B-H5`/`ES-H4` configs say
  `floor_met=True, "BLS CPI schedule (FACT, fetched)"` while the nonprice lane found
  BLS 403-gated and approximated CPI dates via ALFRED vintage dates. The config FACT
  ("12 of 2026 dates verified") has no artifact in nonprice raw. Cross-lane
  reconciliation needed before CPI-date event tags are used as FACT.

### NOTE

- **n-1.** Survey-median regex misses "median estimate of net withdrawals of X Bcf"
  (direction words intervene) → the 352 count slightly undercounts; mixed-direction
  ranges (2023-01-12: withdrawals 35 to injections 16) also unparseable. Pre-2018
  "market expectations (average)" sentences are present in raw but unextracted —
  different semantics (average, not median), extraction would extend the free record.
- **n-2.** "At close" manifest hashes disagree between artifacts (report:
  `339d022b…`, handoff: `b69fc2c9…`; current file is larger — append-only growth).
  Not an integrity problem; cite one canonical value going forward.
- **n-3.** CFTC tidy contains multiple market rows per symbol-week (pattern matches
  both consolidated and mini variants, e.g. ES 2,208 rows > ~850 weeks).
  `market_name` disambiguates; consumers must aggregate consciously.
- **n-4.** Test name `wngsr_totals_parsed_2014plus_95pct` asserts ≥0.90 (measured
  93.17%) — naming vs threshold mismatch, harmless.

## Recommended next actions

1. Owning lane (or follow-up patch): fence/fix `net_change_bcf` (M-1) before any
   NG-H1 work; relabel 6J-H3 + ES-H4 CPI-leg + add vintage-granularity qualifiers
   (M-2); rename/remove the mislabeled `pit/DFII10` probe (m-3).
2. Owner: adjudicate WNGSR-embedded The Desk survey as NG-H1 consensus source under
   the §3 bounds (2018+, median+range only); decide FRED key (per-release vintages)
   and the PAID list per `OWNER_ONLY_STEPS.md`.
3. Data lane: GC-H1 serial re-fetch stays time-critical (~Q1-2027 age-out).

---

# DELTA AUDIT — NONPRICE-FIX verification (2026-10-02, same A7 auditor, read-only)

Scope: verify the fix lane's claims for M-1, M-2, the 41-test suite, and the five
minors. Method: independent reruns and recomputations (not trusting the fix lane's
own flags where an independent basis exists). HEAD still `8ce10f7e…`; raw manifest
still 12,550 lines (no-new-downloads rule held); only `nonprice_acquisition/**` +
`dispatch/handoff_NONPRICE-FIX.json` changed by the fix lane.

## Delta findings

**D-1 / M-1 (net_change rebuild) — DELTA_VERIFIED.**
My independent consecutive-totals-diff check on the rebuilt
`eia_wngsr_vintages_tidy.parquet`: **746/758 comparable rows agree exactly on
SIGNED values = 98.4%** (matches the claim; pre-fix was 62/561 = 11.1%). The 12
residual disagreements: 10 flagged `OK_PRIOR_WEEK_REVISED` (EIA revised the prior
week's total in-issue — legitimately explained, flag carries it) and 2 differ by
1–2 Bcf, inside the extractor's declared 2 Bcf tolerance (`OK_VERIFIED_TOTALS_DIFF`).
Column is now SIGNED (+injection/−withdrawal); legacy first-mention values preserved
in `net_change_legacy_firstmention_bcf` (962 non-null). Quarantine verified: 27 rows
`EXTRACT_LOW_CONFIDENCE`, **all** `net_change_bcf=NULL **with recorded reason**.
All 5 audit misgrab cases now correct against raw narrative (2016_01_14→−168 vs
prior-week 3,643→3,475; 2019_03_14→−204 with survey 209 [201,220]; 2023_01_12→+11 —
raw literally reads "The net injections into storage totaled 11 Bcf for the week
ending January 6", the same sentence carrying the 157 trap). Totals coverage rose
693→954/1205 (spot-checked vs raw). Stocks-table anchoring + in-table cur−prior
consistency check + stale-embedded-table guard confirmed in code. Flag taxonomy
(733/190/58+44/10/9/27/178) matches the handoff exactly.

**D-2 / M-2 (readiness re-derivation) — DELTA_VERIFIED.**
Mechanical recount from `hypothesis_readiness.json` reproduces `status_counts`
exactly: **READY_DATA 27** (was 34) · **+4 PARTIAL_VINTAGE** (NQ-H1, GC-H5, CL-H4,
6E-H2 — precisely the four my M-2 named) · **+3 PARTIAL_MISSING_ROUTE** (6J-H3 —
TONA leg, the outright mislabel; ES-H4 — CPI-date leg; 6B-H5 — same MISSING
structure, caught by the mechanical rule beyond my named set and disclosed in the
erratum). Rules R1–R5 exist in `build_readiness.py` and every downgrade cites its
rule; a mechanical scan confirms no READY_DATA status carries a MISSING piece
(6J-H4's READY is legitimate — its "WAIT" text is the disclosed wait_storage'd BoJ
PDF with same-day HTML sibling present). All other statuses unchanged and still
honest (BLOCKED_CONSENSUS 7, PAID family, NG PARTIALs, GC-H1 MISSING).

**D-3 / tests — DELTA_VERIFIED.**
Independent rerun: **41/41 PASS, exit 0**, log digest
`ea387d1e0dd5c1566ed40a8996d9165226cd90a12a9f3219bb99bffcd4dea6d0` — identical to
the fix lane's recorded digest. The 12 new tests are real regression pins (5 misgrab
pins + 18 known-good pins + quarantine-null-with-reason + agreement≥95% + survey
pins incl. the previously-missed 2023-01-12 median 3 + issue_date robust + 3
readiness mechanical rules + BoJ 180 pdf/html + DFII10 fence), not tautologies.

**D-4 / minors — DELTA_VERIFIED (all five).**
- m-1 BoJ: inventory now 327 rows = 180 BOJ (114 PDF + 66 HTML) + 147 FOMC — PDFs
  now in tidy; "181 enumerated vs 180 on disk" disclosed in report erratum and
  6J-H4 pieces (the 181st was NOT downloaded — no-new-downloads held).
- m-2 dedupe: session-level URL-skip rule added in `collect/common.py` with erratum
  comment (matches my 60-duplicate finding verbatim).
- m-3 DFII10 probe: fenced — probe sha absent from both `fred_vintage_attempts_tidy`
  and `fred_latest_tidy` provenance sets (checked mechanically) + fence test PASS;
  raw file left immutable with manifest erratum (acceptable alternative to deletion).
- m-4 issue_date: robust ISO column added (`issue_date` + `issue_date_source`;
  1,169/1,205 from "Release date:" header; 1,185/1,205 match filename;
  `issue_date_raw` retained but documented unreliable). Verified on the m-4 case:
  2016_01_14 → `issue_date=2016-01-14`, and the new `storage_week_ending`
  (2016-01-08 / 2023-01-06 = Friday stocks as-of) properly separates stocks date
  from the Wednesday report week — good semantics.
- m-5 BLS FACT: ES-H4/6B-H5 pieces now type the CPI-date leg MISSING (rule R1) with
  the config-"FACT, fetched" conflict explicitly disclosed; report erratum block
  carries old→new counts including the honest re-basing of the pre-fix agreement
  number (my 11.1% totals-basis vs their 20.2% table-basis, both stated).

## Residuals after the fix (new)

- **r-1 (MINOR). Survey sign semantics underspecified for surprise math.**
  `survey_median_bcf`/`survey_low/high` are UNSIGNED magnitudes with a separate
  `survey_direction` column (injections 247 / withdrawals 87 / **NaN 35**). The fix
  handoff's shorthand "surprise = actual(net_change_bcf) − survey_median with sign
  convention" would mis-sign withdrawal-side medians (e.g. 2019_03_14: actual −204,
  median 209 withdrawals → signed surprise +5; naive −413). The data needed to do it
  right is present, but the formula must be pinned (sign the survey columns at
  extraction, or document sign(survey_median) = −1 iff direction=withdrawals) and
  the 35 median-without-direction rows handled before any NG-H1 surprise computation.
- **r-2 (NOTE).** 178/1205 issues remain net_change NOT_PARSED (2004–2011 phrasings
  + genuinely stale embedded tables, guard-excluded); disclosed; raw retained.
  Mixed-direction survey ranges (2023-01-12: 35 withdrawals to 16 injections) still
  unparseable (low/high NaN) — partially addressed (median now parsed), as disclosed.
- **r-3 (NOTE).** Observed one transient parquet read failure on the shared raw tree
  (an active `acq_pipeline.py` from the download lane writes the same `normalized/`
  area; retry succeeded, hashes stable). No integrity impact observed, but
  normalized-dir read/write races between lanes are real — worth a word in the
  integration notes.

## Delta verdict

**DELTA_VERIFIED — PASS.** Both MAJORs resolved and independently reproduced
(98.4% signed agreement; readiness mechanically honest with 27/4/3 new taxonomy);
41/41 tests reproduced with identical digest; all five minors addressed. Residuals:
1 MINOR (survey sign convention for NG-H1 surprise; 35 no-direction rows) + 2 NOTEs.
WNGSR survey adjudication stands as previously typed (369 medians now, 2018+), with
r-1 as the one item to pin before the owner's NG-H1 fitness decision is *used*.
