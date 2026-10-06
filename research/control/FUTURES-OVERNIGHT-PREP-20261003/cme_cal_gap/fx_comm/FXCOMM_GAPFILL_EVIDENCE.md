# FX + Commodities Calendar Gap-Fill Evidence (Lane P2B-CALGAP-FXCOMM)

Task: FUTURES-OVERNIGHT-PREP-20261003 | Cycle: UNREGISTERED_PREP | Lane: P2B-CALGAP-FXCOMM
Acquisition: 2026-10-03 (all timestamps UTC) | Worktree HEAD: a8cd06f2603a8df5a2db5999c63ab09c3a7134e7

Mission: close the four calendar gaps left by parent lanes A2-CMECAL-FX / A3-CMECAL-COMM
(`research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/{fx,comm}/`), official CME
sources only (live or web.archive.org captures of cmegroup.com), **zero extrapolation** — every
date/time below was read from a saved capture (sha256 in `captures/SHA256SUMS.txt`).

Laws honored: public access only; default curl UA / reader tools; no UA spoofing; no proxies;
≤2 attempts per URL per method (exceptions logged); every attempt in `fetch_log.jsonl`;
uncertain cells ⇒ NOT_OBTAINED / NOT_TRANSCRIBED, never inferred. Third-party sites used for
discovery only (one WebSearch; no datum taken from any non-cmegroup source).

Provenance labels: `ARCHIVED_OFFICIAL` (capture of official cmegroup.com artifact; file saved
+ sha256 + resolved timestamp), `NOT_OBTAINED` (reason given), `NOT_TRANSCRIBED` (artifact in
hand, extraction failed).

Headline results:

| Gap | Verdict |
|---|---|
| 1. FX quarterly expiries 2019-2026 (6E/6B/6J/6A) | 2019-2022 **CLOSED** for all four symbols + all pre-2019 stragglers closed (incl. 6E ECH12, the parent's hardest cell). **96 → 208/272** quarters (52/68 per symbol; 2010-2022 complete per symbol). 2023-2026 remains NOT_OBTAINED (all routes exhausted, below). |
| 2. FX 2017-2025 product-level holiday times | **Parent's "files not archived" finding OVERTURNED.** 2017 11/11, 2018 9/11, 2019 2/11, 2020 7/9, 2021 9/9, 2022 10/10, 2023 1/10 holidays OBTAINED (XLS, verbatim FX Products rows). 2024-2025 NOT_OBTAINED (advisories only — CDX inventory complete this lane). |
| 3. GC/SI expiry dates 2019-2026 | GC extended **Jun 2019 → Dec 2023**, SI extended **Dec 2019 → Dec 2022** via the last static product-calendar captures (2018-02-27; parent tested only ≥2018-06 = shells). GC 2024-2026 / SI 2023-2026 NOT_OBTAINED. |
| 4. Energy/metals 2011-2015 per-holiday PDFs | **43/45 cells OBTAINED** (2011 11/11, 2012 11/11, 2013 11/11, 2014 9/11, 2015 10/11) with verbatim NYMEX/COMEX family times. NOT_TRANSCRIBED: 2014-MLK (garbled PDF, artifact saved). NOT_OBTAINED: 2014/2015-Veterans (archived file = settlement-procedures doc). |

Bonus (same artifacts, no extra fetches): energy/metals product-line Globex times 2017-2023
(parent comm lane had 2010 full + 2011 sample only) — grid in `fxcomm_gapfill_coverage.json`
→ `bonus_energy_metals_2017_2023`.

---

## 1) FX quarterly expiry dates — 96 → 208/272

### 1a. The unlock: the `_product_calendar_futures.html` URL variant

Parent A2 used `/trading/fx/g10/{product}_product_calendar.html` (static era ended mid-2014;
2014+ captures JS shells — their measured finding, correct for that URL). This lane's CDX
discovery: the **`_product_calendar_futures.html` variant** of the same four FX product
calendars has captures through 2021-2022, and its static era runs to **2018-02/04** (verified
boundary: euro-fx 20180228224018 static 24 rows; 20180418031922 shell — 9 shell captures
tested across 2018-2021, all 0 contract rows). The old-format (2010-2011) captures render
static `<tr id="{CODE}FUT">` HTML tables with a `DATE_TYPE=LAST_TRADE` download link per row.

Captures used (all ARCHIVED_OFFICIAL, saved under `captures/`, sha256 pinned):

| sym | capture | resolved URL | format | rows | span |
|---|---|---|---|---|---|
| 6E | 20110527042052 | …/fx/g10/euro-fx_product_calendar_futures.html | old HTML | 7 | JUN 2011 → DEC 2012 |
| 6E | 20150111002610 | same | JSON-embedded | 20 | MAR 2015 → DEC 2019 |
| 6E | 20180228224018 | same | JSON-embedded | 24 | FEB 2018 → DEC 2022 |
| 6B | 20100219101527 | …/fx/g10/british-pound_product_calendar_futures.html | old HTML | 6 | MAR 2010 → JUN 2011 |
| 6B | 20180226190632 | same | JSON-embedded | 24 | FEB 2018 → DEC 2022 |
| 6J | 20100120181108 | …/fx/g10/japanese-yen_product_calendar_futures.html | old HTML | 6 | MAR 2010 → JUN 2011 |
| 6J | 20100814205214 | same | old HTML | 7 | SEP 2010 → MAR 2012 |
| 6J | 20141015223742 | same | JSON-embedded | 20 | DEC 2014 → SEP 2019 |
| 6J | 20180226182137 | same | JSON-embedded | 24 | FEB 2018 → DEC 2022 |
| 6A | 20180301074633 | …/fx/g10/australian-dollar_product_calendar_futures.html | JSON-embedded | 23 | MAR 2018 → DEC 2022 |

### 1b. New quarterly Last-Trade dates (112 new rows; full machine table in `fxcomm_gapfill_coverage.json` → `gap1_fx_expirations.new_rows_this_lane`)

Every previously-missing cell now held (selected verbatim rows; format `month | code | Last Trade`):

- **6E +35** (17→52): Sep 2011 ECU11 **09/19/2011**; Dec 2011 ECZ11 **12/19/2011**; Mar 2012 ECH12
  **03/19/2012** (the parent's hardest gap — absent from all 9 of their captures; verbatim row
  `MAR 2012 | ECH12 | First 09/14/2010 | Last 03/19/2012` with per-row
  `CmeWeb/event.dld?…CNTR_CODE=ECH2&DATE_TYPE=LAST_TRADE` link, capture 20110527042052);
  2015 H/M/U/Z = 03/16, 06/15, 09/14, 12/14; 2016 = 03/14, 06/13, **09/19**, 12/19; 2017 = 03/13,
  **06/19**, 09/18, 12/18; 2018 = 03/19, 06/18, 09/17, **12/17**; 2019 = 03/18, 06/17, 09/16, 12/16;
  2020 = 03/16, 06/15, 09/14, 12/14; 2021 = 03/15, 06/14, **09/13**, **12/13**; 2022 = 03/14,
  **06/13**, **09/19**, **12/19**. (Bold = Monday holiday/Juneteenth-shifted Mondays.)
- **6B +21** (31→52): 2010 all four = 03/15, 06/14, 09/13, 12/13; Dec 2018 BPZ18 = **12/17/2018**;
  2019 = 03/18, 06/17, 09/16, 12/16; 2020 = 03/16, 06/15, 09/14, 12/14; 2021 = 03/15, 06/14, 09/13,
  12/13; 2022 = 03/14, 06/13, 09/19, 12/19.
- **6J +39** (13→52): 2010 = 03/15, 06/14, 09/13, 12/13; Mar 2011 JYH11 = 03/14/2011, Jun 2011
  JYM11 = 06/13/2011; Dec 2014 J1Z14 = **12/15/2014**; 2015 = 03/16, 06/15, 09/14, 12/14; 2016 =
  03/14, 06/13, 09/19, 12/19; 2017 = 03/13, 06/19, 09/18, 12/18; 2018 = 03/19, 06/18, 09/17, 12/17;
  2019 = 03/18, 06/17, 09/16, 12/16; 2020 = 03/16, 06/15, 09/14, 12/14; 2021 = 03/15, 06/14, 09/13,
  12/13; 2022 = 03/14, 06/13, 09/19, 12/19.
- **6A +17** (35→52): Dec 2018 ADZ18 = **12/17/2018**; 2019-2022 identical dates to 6B (same
  quarterly calendar family; e.g. ADH19 03/18/2019 … ADZ22 12/19/2022).

### 1c. QA (script, `captures/assemble.py`)

- Capture-vs-capture conflict test on every overlapping code across the 10 captures + parent's
  96 rows: **zero conflicts** (e.g. ECM18 18 Jun 2018 identical in 2015- and 2018-captures;
  parent's ADZ17 12/18/2017 = this lane's J1/BP/EC/AD Z17 family).
- Rule consistency (declared rule "9:16 a.m. CT on the second business day immediately preceding
  the third Wednesday of the contract month"): **127/127 quarterly rows 2010-2022 equal the
  2nd business day preceding the 3rd Wednesday — zero deviations** (extends parent's 96/96 to
  208/208 overall).
- Serial (non-HMUZ) months present in the JSON captures are preserved in
  `captures/fx_gapfill_rows.json` as bonus data; coverage counts use HMUZ quarters only
  (272 = 17 years × 4 quarters × 4 symbols, parent's denominator).

### 1d. 2023-2026: NOT_OBTAINED — routes exhausted (all logged)

1. `_product_calendar_futures.html` captures 2018-04-18 → 2021-06: JS shells (9 tested, 0 rows).
2. New-URL `markets/fx/g10/euro-fx.productCalendar.html` (+ cn-s locale variant): **no Wayback
   captures at all** (CDX empty).
3. `trading/fx/rolldates.html` (the equity-index rolldates analogue — parent A1's high-yield
   lead): exists 2008-2015 (200), **301 from 2016 onward → `markets/fx.html?redirect=/trading/fx/rolldates.html`**
   (page retired; redirect verified on captures 20160122193708…20221226021343). Metals/energy/
   rates rolldates analogues: 404 / none (CDX).
4. Archived CmeWS/CmeWeb API responses: CDX probes returned only Ags/Reports + 2008-2011
   `event.dld` downloads for long-expired contracts — nothing in era.
5. Live legacy data endpoint `https://www.cmegroup.com/CmeWeb/event.dld?PROD_CODE=EC&…&CNTR_CODE=ECZ5&DATE_TYPE=LAST_TRADE`:
   web_reader −500 ×2 (2-attempt stop), WebFetch ECONNREFUSED ⇒ **BLOCKED_TRANSPORT**.
6. WebSearch for an official modern FX roll-dates/IMM page: none exists (third-party hits only —
   not authority).

Per the mission's no-extrapolation law, 2023-2026 FX dates are NOT derived from the IMM rule
even though the rule is official and 208/208-consistent; they remain NOT_OBTAINED.

---

## 2) FX 2017-2025 product-level holiday/early-close times

### 2a. Parent's blocker overturned

Parent A2 (FX_CALENDAR_EVIDENCE.md §structural finding 3): "From 2017 the per-holiday Globex
schedule PDFs/XLS stopped being reliably archived (CDX shows only clearing advisories…)". This
lane's full CDX inventory of `www.cmegroup.com/tools-information/holiday-calendar/files/`
(1,920 capture rows; `captures/cdx_holiday_files.txt`) shows the per-holiday
`{year}-{holiday}-holiday-schedule.xls` family IS archived for 2017-2023 (2024-2025 advisories
only). 52 XLS + XLSX files fetched, signature-verified, parsed (xlrd for .xls; stdlib zip/XML
for the one .xlsx), FX Products rows transcribed verbatim
(`captures/holiday_transcription.json`, per-file dumps under `captures/extracted/`).

### 2b. Cell grid (machine version: `fxcomm_gapfill_coverage.json` → gap2 cells)

Universe = holidays for which CME published a schedule file that era.
OBTAINED = 2017: 11/11 · 2018: 9/11 · 2019: 2/11 · 2020: 7/9 · 2021: 9/9 · 2022: 10/10 ·
2023: 1/10 · 2024: 0 · 2025: 0.

Key verbatim facts (all times CT; "FX Products" row of the official XLS; column groups
per each file's header — full rows in the transcription JSON):

- **Monday holidays (MLK/Presidents/Memorial/Labor), 2017-2021**: FX row shows
  `… | 12:00 | 12:00 | 17:00` in the Monday halt/pre-open/open group — i.e. **12:00 CT halt →
  17:00 CT resume** (2017 MLK @20170628172556; 2018 MLK @20180106225650; 2020 MLK
  @20250827082154; 2021 MLK @20220917190720 — same pattern every Monday holiday these years).
- **2022 regime change**: 2022 MLK FX row = `16:00 | 16:00 | 17:00` in the same columns —
  **normal 16:00 close + 17:00 reopen (no 12:00 halt)**; all 2022 Monday holidays identical
  (MLK/Presidents/Memorial/Juneteenth/Labor; e.g. Presidents @20220704073810). The 12:00 FX
  Monday halt of 2017-2021 is gone by 2022 — year-aware pipelines must treat this as a
  structural break.
- **Good Friday 2017-2022**: FX **"Globex Closed"** every year (2017 @20170505072315 …
  2022 @20220704065501) — full closure, consistent with the 2011/2013/2014/2016 parent-era
  alternation now settling on closure; 2021 @20210402141803 adds a Thursday 10:15 early close
  column (10:15 | 16:00 | 17:00) before the Friday closure.
- **Christmas-eve early close**: 2018-2020 XLS FX row `12:15 | Globex Closed | 16:00 | 17:00`
  (2018 @20180106225502, 2019 @20201111233949, 2020 @20201112011834) — **12:15 CT early close
  Dec 24, closed Dec 25, 16:00→17:00 reopen**; 2017 Christmas @20170628111918 = `16:00 | Globex
  Closed | 16:00 | 17:00` (regular Friday close, no early close).
- **Thanksgiving**: 2017/2018/2021 XLS FX rows end with a **12:15** tail value (Friday-after
  early close) — e.g. 2017 @20170628163054 `… 12:00 | 12:00 | 17:00 | 12:15`; 2022
  @20220704065423 same shape (16:45/17:00 Wednesday reopen + 12:15 Friday tail).
- **July 4th**: 2017/2018 `12:00 | 12:00 | 17:00` Monday pattern (holiday observed Monday July
  3 2017 / Tuesday July 4 2018 respectively per each file's date header); 2020 (July 4 = Saturday,
  observed Friday July 3) @20220707015539 shows `12:00 | 16:00 | 17:00` — 12:00 early close
  Friday; 2021 compact format "FX | Regular @ 1600 … | 1200 CT / 1700 UTC | Regular @ 1700"
  (halt 12:00, resume 17:00).
- **Columbus/Veterans 2017**: one-cell official statements — "Products listed on Globex are
  **unaffected and will run on a normal schedule**" (@20170505072245 Columbus Monday Oct 9;
  @20170628130541 Veterans Friday Nov 10 (Observed)) — FX normal.
- **New Year**: 2017 (parent already had the XLS; re-confirmed @20151203081804), 2018, 2019,
  2021, 2022, 2023 all `16:00 close | Globex Closed (Jan 1) | 16:00 → 17:00 reopen` shape.
- **2019 Thanksgiving**: the only archived "schedule" file
  (`2019-thanksgiving-day-holiday-schedule-arragements.xlsx`, fetched + parsed) is a **NYMEX
  BALMO/PRA settlement list — no Globex hours** ⇒ that cell stays NOT_OBTAINED.
- **2023**: only New Year OBTAINED (@20220704065501 → resolved 2023-new-years-holiday-schedule.xls,
  FX `16:00 | Globex Closed | 16:00 | 17:00`). The five 2023 `*-compact-mgex-dme.xls` files were
  fetched and verified to contain **DME/MGEX products only — no FX/NYMEX/COMEX rows** (content
  quoted in coverage JSON) ⇒ the other 2023 cells stay NOT_OBTAINED.
- **2024/2025**: CDX inventory shows advisories/settlement-times only — no schedule files ⇒
  NOT_OBTAINED (inventory artifact `captures/cdx_holiday_files.txt` is the evidence of absence).

### 2c. Independent cross-validation

This lane's own 2011-2015 PDF set (fetched for gap 4) reproduces parent A2's FX-family facts
verbatim where they overlap (e.g. 2011 Good Friday "CME Globex is closed"; 2012 Good Friday
"1015 CT - Early CME Globex close"; 2013 Monday halts 1200/1700; 2014 Jul 4 "1200 CT … Early
close (Day & GTD order elimination)") — pipeline cross-check, zero contradictions.

---

## 3) GC/SI expiry/last-trade dates 2019-2026

### 3a. Static-era extension

Parent A3 tested GC captures 20180602051402 / 20200525023744 and SI 20180614091251 /
20200803212643 — all JS shells — and concluded the wall. This lane tested the **untested
2018-02/2019 boundary and the 2019-12 captures**:

- `gold_product_calendar_futures.html` @**20180227093156**: STATIC — 22 visible rows + embedded
  JSON extending to **Dec 2023** (the JSON data blob carries 2 more rows than the rendered
  table: GCM23, GCZ23).
- @20180227093206 (silver): STATIC — 20 rows to **Dec 2022**.
- Shells confirmed (0 rows): GC 20190328183304, 20190908124623, 20191120151956; SI
  20180428160150, 20180429115735. So the wall for GC/SI calendars is 2018-02→2018-04, same as
  FX/CL/NG.

### 3b. New last-trade dates (verbatim from the two captures; full rows in coverage JSON)

**GC** (new beyond parent's Jun 2019): GCQ19 **28 Aug 2019**, GCV19 **29 Oct 2019**, GCZ19
**27 Dec 2019**, GCM20 **26 Jun 2020**, GCZ20 **29 Dec 2020**, GCM21 **28 Jun 2021**, GCZ21
**29 Dec 2021**, GCM22 **28 Jun 2022**, GCZ22 **28 Dec 2022**, GCM23 **28 Jun 2023**, GCZ23
**27 Dec 2023**. (2019 cycle months G/J/M also held: GCG19 26 Feb, GCJ19 26 Apr, GCM19 26 Jun
— GCM19 matches parent's row exactly.) Interim G/J/Q/V months of 2020-2023 are NOT listed on a
Feb-2018 capture (23-month window) — noted per-row in the coverage JSON; the 72-month Jun/Dec
chain is complete to Dec 2023.

**SI** (new beyond parent's Dec 2019): SIF20 **29 Jan 2020**, SIN20 **29 Jul 2020**, SIZ20
**29 Dec 2020**, SIN21 **28 Jul 2021**, SIZ21 **29 Dec 2021**, SIN22 **27 Jul 2022**, SIZ22
**28 Dec 2022**. (SIZ19 27 Dec 2019 = parent's row ✓.) Interim F/H/K/U months of 2020-2022 not
listed (same window logic); Jul/Dec chain complete to Dec 2022.

### 3c. QA

- Overlap rows identical to parent (GCM19 26 Jun 2019; SIZ19 27 Dec 2019) — zero conflicts.
- Third-last-business-day rule check: all rows conform **except GCH18/SIH18 (27 Mar 2018)**,
  which my naive weekend-only QA flagged — explained by **Good Friday 30 Mar 2018** removing
  Mar 30 from the business-day chain (third-last bd of Mar 2018 = 27, table correct; same
  holiday-shift class the parent documented for CLZ18/Thanksgiving). Zero other deviations.

### 3d. GC 2024-2026 / SI 2023-2026: NOT_OBTAINED

No static calendar captures exist after 2018-04 (verified above); no metals rolldates page
(CDX 404); no archived CmeWS responses; new-URL productCalendar pages never archived; the
72/60-month forward listing in the 2018-02-27 captures is the last official static listing.
Not derived from the rule per mission law.

---

## 4) Energy/metals 2011-2015 per-holiday PDFs (NYMEX/COMEX family times)

All 53 PDFs fetched (every per-holiday file archived for 2011-2015; manifest +
sha256), text extracted (pypdf), **"NYMEX, COMEX® and DME Products on CME Globex"** /
"NYMEX & COMEX®…" / "NYMEX, COMEX & Dubai Mercantile (DME) Products" / "Energy, Metals & DME
Products" sections transcribed verbatim (`captures/holiday_transcription.json` →
`energy_metals`). Per-year coverage:

| Year | Cells OBTAINED / universe | Gaps |
|---|---|---|
| 2011 | 11/11 | — |
| 2012 | 11/11 | — |
| 2013 | 11/11 (Columbus & Veterans = official one-pagers "Products listed on Globex are unaffected and will run on a normal schedule") | — |
| 2014 | 9/11 | MLK NOT_TRANSCRIBED (PDF text garbled by pypdf — vertical fragments; artifact saved @20140326160215 for re-parse); Veterans NOT_OBTAINED (archived file = settlement-procedures doc, no hours) |
| 2015 | 10/11 | Veterans NOT_OBTAINED (settlement doc — matches parent) |

Verbatim essentials (times CT; full rows in coverage JSON):

- **Monday holidays 2011-2012** (MLK/Presidents/Memorial/Jul-4-observed/Labor): pre-holiday
  Friday **1515 CT early close** + Monday **1215 CT trading halt → 1700 CT resume**
  (e.g. 2011 MLK @20110114202403: "Friday, Jan 14 1515 CT / 1615 ET – Early CME Globex close …
  Monday, Jan 18 1215 CT / 1315 ET – Trading halt … 1700 CT – Halted products resume trading").
- **2013-2015 change**: pre-holiday Fridays become **regular 1615 CT closes** (early close
  dropped, mirroring the FX-family 2016 change but happening earlier here); Monday halts
  become **1200 CT → 1700 CT** (e.g. 2015 MLK @2015…-martin-luther-king…: "Friday, Jan 16 1615
  CT / 1715 ET / 2215 UTC – Regular close … Monday, Jan 19 1200 CT / 1300 ET …").
- **Good Friday 2011-2015**: **full closure** every year ("CME Globex is closed" / 2012: "No CME
  Globex Trading on Good Friday").
- **Thanksgiving**: Wednesday regular close 1615 + 1700 reopen (Fri trade date); Thursday
  1215/1200 halt → 1700; **Friday early close 1245 CT** (2011 @20110114202528 "Friday, Nov 25
  1245 CT / 1345 ET – Early CME Globex close", TAS exception 12:30 CT — matches parent's
  2011-thanksgiving.pdf exactly; 2013-2015 same 1245 shape).
- **Christmas**: 2011-2013 Dec 23/24 patterns with per-metal TAS exceptions quoted verbatim
  (2013 Christmas @20121119021305: "Copper TAS – Early Close 1100 CT / 1200 ET · Silver TAS -
  Early Close 1125 CT · Gold TAS – Early Close 1130 CT"); 2014/2015 **Dec 24 early close 1245
  CT**, Dec 25 closed, 1700 reopen for Dec 26 trade date.
- **Columbus/Veterans 2011-2012**: pre-holiday Friday 1515 early close + Monday/Nov-11 regular
  sessions; 2013+: normal schedule (one-pagers).
- **New Year transitions**: 2011 "Friday, Dec 31 1515 CT / 1615 ET – Early CME Globex close";
  2012/2013 "1615 CT regular close + Jan 1 closed + 0500/1700 reopen" shapes — all verbatim in
  the transcription JSON.

---

## Bonus: energy/metals product-line Globex times 2017-2023

The same gap-2 XLS files carry the "Energy, Metal(s), Softs & DME Products" row (2018/2021
spelling "Energy, Metal, Softs & DME Products"). Key facts: Monday-holiday halts **12:00 CT →
17:00 CT in 2018-2021** (2018 MLK @20180106225650 row `Energy, Metal, Softs & DME Products |
16:00 | 16:00 | 17:00 | … | 12:00 | 12:00 | 17:00`; 2020 Memorial compact "Energy, Metals &
DME … HALT 1200 CT / 1700 UTC"; 2021 MLK @20220917190720 same), changing to **13:30 CT halt
in 2022** (2022 MLK @20220117212230: family Monday group `13:30 | 13:30 | 17:00` while FX
shows `16:00 | 16:00 | 17:00`); Good Friday full closure 2017-2022 (energy/metals row "Globex
Closed" 2020 @20241202115016, 2022 @20220704065501); Christmas-eve early close 12:15 (2020
Christmas @20201112011834) with family reopen 16:00→17:00. Grid: coverage JSON →
`bonus_energy_metals_2017_2023` (same cell status as gap 2).

---

## NOT_OBTAINED register (honest list, with reason)

1. FX quarterly expiries **2023-2026** (64 cells): all archive routes exhausted (§1d); live
   endpoint BLOCKED_TRANSPORT. Rule remains official and 208/208-consistent — derivation
   forbidden by law, so NOT_OBTAINED.
2. GC **2024-2026**, SI **2023-2026** last-trade dates (§3d). GC/SI interim non-Jun/Jul/Dec
   cycle months of the far-out years (2020-2023) not listed on the last static captures.
3. FX holiday times **2024-2025** (advisories only in archive); **2019** 9 of 11 holidays;
   **2020** Presidents + New Year; **2018** Columbus/Veterans; **2023** all but New Year.
4. Energy/metals: **2014 MLK** NOT_TRANSCRIBED (artifact saved); **2014/2015 Veterans**
   (settlement docs, no hours).
5. FX rolldates-page analogue: page retired 2016 (redirect verified) — nothing to fetch.

## Incident/etiquette notes

- web.archive.org intermittent connection failures (exit 7 / "Temporarily Offline") several
  times; handled by sleep+retry within the ≤2-attempt budget (one rolldates redirect resolve
  needed a retry; batch fetcher had 0 failures on 112 files).
- One live-endpoint probe (event.dld): web_reader ×2 (-500) then WebFetch ×1 (ECONNREFUSED) —
  2 attempts per method, stop; no bypass attempted.
- All extraction scripts (parse_old_fx.py, assemble.py, extract_all.py, xls_dump.py,
  transcribe_final.py, build_coverage.py) and intermediate data files preserved under
  `captures/` for reproduction.
- Zero third-party data used; one WebSearch (discovery only, negative result).
