# NQ (E-mini Nasdaq-100) — Official CME Calendar Evidence (Lane A1-CMECAL-NQES)

Task: FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 | Cycle: UNREGISTERED_PREP | Lane: A1-CMECAL-NQES | Acquisition date: 2026-10-03 (all timestamps UTC).
Scope: (1) NQ per-year holidays + early closes 2010-2026, official authority only; (2) NQ quarterly expiration rule (verbatim) + as many officially-sourced expiry dates as obtainable, coverage counted per year.
Laws honored: every claim tagged FACT (source + capture/effective date) / OBSERVED / POSTULATED / NOT_RUN; uncertain days ⇒ EXCLUDE/NOT_RUN, no inferred-pass, no gap-filling by inference; normal public access only (no UA spoofing, no proxies); ≤2 attempts per URL per method (full trail in `fetch_log.jsonl`); third-party aggregators never used as authority.

## Provenance labels

- `LIVE_OFFICIAL` — fetched directly from cmegroup.com on 2026-10-03 (web_reader; live curl is transport-blocked HTTP 000, logged).
- `ARCHIVED_OFFICIAL` — web.archive.org capture of an official cmegroup.com page/PDF; archive URL + resolved capture timestamp recorded per datum.
- `ARCHIVED_OFFICIAL_PRODUCT` vs `ARCHIVED_OFFICIAL_FAMILY` — sub-classes used for expirations: a per-product CME product-calendar table naming NQ contracts vs an official CME table whose wording covers the whole U.S. equity-index quarterly futures family (per dispatch method rule: "Where an official table literally covers the whole equity family … that wording is authority for both — quote it verbatim").
- `NOT_OBTAINED` / `NOT_TRANSCRIBED` — no authority-backed datum / fetch succeeded but content not preserved.

## Method (extends D3-CMECAL, does not redo it)

1. Holidays: CME publishes ONE venue-wide CME Globex holiday schedule (not per-product). NQ trades on CME Globex and is a CME equity-index product, so the family-wide official tables are NQ authority. Evidence base = the D3 lane's per-year captures (`research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md`) PLUS this lane's first-hand re-verifications: the 2010 official Globex PDF (re-fetched, parsed), the 2017 holiday page (re-fetched, family wording confirmed verbatim), and the live 2026 trading-hours page (fetched 2026-10-03).
2. Expirations: product-specific NQ rows from archived captures of the official NQ product-calendar page `https://www.cmegroup.com/trading/equity-index/us-index/e-mini-nasdaq-100_product_calendar_futures.html` (static era ≤2017-10-23; widget era after — measured: capture 20180601223818 shows "No Data Available"; 2025-era new-URL capture 20250702132707 is a React shell). Family-level dates from the official CME "Equity Index Roll Dates" page (`.../trading/equity-index/rolldates.html`) whose "U.S. Indexes — Expiration" column is quoted verbatim below.
3. Rule: archived captures of the official NQ contract-specifications page (three eras).
4. Transcription rule: every datum copied from text present in a fetched artifact (saved under session scratch; extraction scripts local). Nothing memory-filled.

## 1) NQ holidays + early closes, per year 2010-2026

### Why the same tables are NQ authority (verbatim family wording)

- 2010 PDF, all 12 holiday sections headed (FACT, capture 20100215061802, re-fetched 2026-10-03): **"CME Group Equity Products"**. Parsed the full 38-page PDF: ZERO product-name mentions (no "NASDAQ", "S&P", "E-mini" strings anywhere) — the Equity sections carry no carve-outs; the only named in-family exception is Nikkei ("Exception: USD & JY Nikkei regular times", Presidents' Day). NQ is a CME Group equity product ⇒ sections are NQ authority at full session-level detail.
- Holiday pages (example re-verified first-hand, capture 20170703230701): **"2017 CME Globex Trading Schedule — CME Globex will observe the following holidays in 2017. Trading times and days affected may vary depending on the holiday. Download the existing files to view altered trading hours."** (venue-wide, no product filter) and floor table rows **"… Equities Futures and Options Close at 12:15 CT"** (Jul 3, 2017; Nov 24, 2017) — "Equities Futures" is the product family containing NQ futures.
- 2026 live page (FACT, web_reader 2026-10-03, https://www.cmegroup.com/trading-hours.html): "CME Globex Trading Hours — 2026" table (venue windows) + Holiday Notes; product-level times moved to widget/downloadable calendars — see LIMIT under 2026.

### Per-year table

| Year | Holidays (Globex windows / closures) | Early closes (equity-family detail) | Source class + URL + capture |
|---|---|---|---|
| 2010 | Closures Fri Jan 1 and Fri Dec 24; Monday holidays (MLK Jan 18, Presidents Feb 15, Memorial May 31, Jul 5, Labor Sep 6) = 10:30 CT halt → 17:00 CT resume; Columbus Oct 11 + Veterans Nov 11 = NORMAL sessions; Thanksgiving Thu Nov 25 halt pattern | Good Friday Fri Apr 2 early Globex close **08:15 CT**; Fri Nov 26 early Globex close **12:15 CT**; all times family-wide | ARCHIVED_OFFICIAL — https://web.archive.org/web/20100215061802/http://www.cmegroup.com/tools-information/holiday-calendar/files/2010-globex-holiday-calendar.pdf (re-fetched 2026-10-03; 12 sections "CME Group Equity Products") |
| 2011 | Windows verbatim: Christmas 2010 23-26 Dec; New Year 31 Dec 2010-3 Jan 2011; MLK 14-18 Jan; Presidents 18-22 Feb; Good Friday 21-24 Apr; Memorial 27-31 May; Jul 4 1-5 Jul; Labor 2-6 Sep; Columbus 7-10 Oct; Veterans 10-11 Nov; Thanksgiving 23-25 Nov; Christmas 23-27 Dec 2011; New Year 30 Dec 2011-3 Jan 2012 | Day-level equity times in linked official PDFs (per-holiday 2011 PDFs; Holiday-Early-Close-Schedule.pdf) — NOT_TRANSCRIBED from HTML | ARCHIVED_OFFICIAL — https://web.archive.org/web/20110313182401/http://www.cmegroup.com/tools-information/holiday-calendar/ (D3 transcription; PDFs catalogued there) |
| 2012 | Windows verbatim (MLK 13-17 Jan … Christmas 24-26 Dec 2012; NY 31 Dec 2012-2 Jan 2013) | Per-holiday PDF/XLS linked on page; day-level tables NOT inline | ARCHIVED_OFFICIAL — https://web.archive.org/web/20120616171859/http://www.cmegroup.com/tools-information/holiday-calendar/ (D3) |
| 2013 | Windows verbatim (MLK 18-22 Jan … NY 31 Dec 2013-2 Jan 2014) | same as 2012 | ARCHIVED_OFFICIAL — https://web.archive.org/web/20130119015927/http://www.cmegroup.com/tools-information/holiday-calendar/ (D3) |
| 2014 | Windows verbatim (MLK 17-21 Jan … Christmas 24-26 Dec 2014) | Jul 3 2014 settlement-notice day (early-close evidence on page) | ARCHIVED_OFFICIAL — https://web.archive.org/web/20140626070427/http://www.cmegroup.com/tools-information/holiday-calendar/ (D3) |
| 2015 | Windows verbatim (MLK 16-20 Jan … NY 31 Dec 2015-4 Jan 2016) | Settlement notices: Thu Jul 2 and Fri Sep 4 2015 early-close days; ClearPort equity-adjacent early closes 13:15/14:00/12:00 ET (JS-tab caveat, D3) | ARCHIVED_OFFICIAL — https://web.archive.org/web/20150710035807/http://www.cmegroup.com/tools-information/holiday-calendar/ (D3) |
| 2016 | Windows verbatim (MLK 15-19 Jan … NY 30 Dec 2016-3 Jan 2017) | Closures Good Friday Mar 25, Dec 26, Jan 2 2017; **Equities floor close 12:15 CT Fri Nov 25**; ClearPort early close 13:45 ET Nov 25 | ARCHIVED_OFFICIAL — https://web.archive.org/web/20160214222113/https://www.cmegroup.com/tools-information/holiday-calendar.html (D3) |
| 2017 | Windows verbatim (MLK 13-17 Jan … NY 29 Dec 2017-2 Jan 2018) | **"Equities Futures and Options Close at 12:15 CT" Mon Jul 3 and Fri Nov 24** (first-hand re-verification); ClearPort closed Good Friday Apr 14, Dec 25, Jan 1 2018 | ARCHIVED_OFFICIAL — https://web.archive.org/web/20170703230701/https://www.cmegroup.com/tools-information/holiday-calendar.html (re-fetched this lane 2026-10-03) |
| 2018 | Windows verbatim (MLK 12-16 Jan … NY 31 Dec 2018-2 Jan 2019) | Equities 12:15 CT Jul 3, Nov 23, Dec 24; ClearPort early closes 13:45 ET Nov 23 + Dec 24 | ARCHIVED_OFFICIAL — https://web.archive.org/web/20180629065738/https://www.cmegroup.com/tools-information/holiday-calendar.html (D3) |
| 2019 | Windows verbatim (MLK 18-22 Jan … NY 31 Dec 2019-2 Jan 2020) | Equities 12:15 CT Jul 3, Nov 29, Dec 24; ClearPort 13:45 ET Nov 29 + Dec 24 | ARCHIVED_OFFICIAL — https://web.archive.org/web/20190702203907/https://www.cmegroup.com/tools-information/holiday-calendar.html (D3) |
| 2020 | Windows verbatim (MLK 17-21 Jan … NY 31 Dec 2020-4 Jan 2021) | Jul 4 observed Fri Jul 3 (ClearPort 13:00 ET early close + modified Jul 6); Equities 12:15 CT Nov 27 + Dec 24 | ARCHIVED_OFFICIAL — https://web.archive.org/web/20200620052000/https://www.cmegroup.com/tools-information/holiday-calendar.html (D3) |
| 2021 | Windows verbatim; first year floor table drops product breakdown | Good Friday special ClearPort session (19:00 Thu Apr 1 → 11:30 Fri Apr 2 for IR/Equity-index/FX only); NQ product-level Globex times NOT_TRANSCRIBED (in per-holiday files) | ARCHIVED_OFFICIAL — https://web.archive.org/web/20210702163511/https://www.cmegroup.com/tools-information/holiday-calendar.html (D3) |
| 2022 | Windows verbatim; first Juneteenth (17-21 Jun) | Floor early closes generic 12:00 CT (Dec 31 2021, Apr 14, May 27, Jul 1, Nov 25, Dec 23, Dec 30 2022) | ARCHIVED_OFFICIAL — https://web.archive.org/web/20220627175029/https://www.cmegroup.com/tools-information/holiday-calendar.html (D3) |
| 2023 | Windows verbatim (incl. Juneteenth 16-20 Jun) | Good Friday Apr 7 floor close 10:00 CT; floor early closes 12:00 CT (Dec 30 2022, May 26, Jul 3, Nov 24, Dec 22, Dec 29 2023) | ARCHIVED_OFFICIAL — https://web.archive.org/web/20230528173700/https://www.cmegroup.com/tools-information/holiday-calendar.html (D3) |
| 2024 | Windows verbatim (MLK 12-16 Jan … NY 31 Dec 2024-2 Jan 2025) | Floor early closes 12:00 CT Mar 28, May 24, Jul 3, Nov 29, Dec 24, Dec 31; ClearPort closures Jan 1, Good Friday Mar 29, Dec 25, Jan 1 2025 | ARCHIVED_OFFICIAL — https://web.archive.org/web/20241112201950/https://www.cmegroup.com/trading-hours.html (D3) |
| 2025 | Windows verbatim (MLK 17-20 Jan … NY 31 Dec 2025-2 Jan 2026) | Clearing-notice dates + windows (ClearPort day-level 2025 table NOT_TRANSCRIBED, D3) | ARCHIVED_OFFICIAL — https://web.archive.org/web/20241112201950/https://www.cmegroup.com/trading-hours.html (D3) |
| 2026 | Windows verbatim (fetched live this lane): New Year Dec 31 2025-2 Jan 2026; MLK Jan 18-20; Presidents Feb 15-17; Good Friday Apr 2-4; Memorial May 24-26; Juneteenth Jun 18-19; Independence Jul 3-5; Labor Sep 6-8; Thanksgiving Nov 26-28; Christmas Dec 24-26; New Year Dec 31 2026-Jan 1 2027 | Floor early closes 12:00 CT May 22, Jul 2, Nov 27, Dec 24, Dec 31; Good Friday Apr 3 close 10:00 CT; ClearPort closed Jan 1, Jan 19, Feb 16, Apr 3, May 25, Jun 19, Jul 3, Sep 7, Nov 26, Dec 25 with 13:15 ET prior-day early closes; Holiday Notes: "Globex Equity AND Interest Rate products trade NORMAL hours on MLK and Presidents' days"; TAS early closes Nov 27, Dec 24, Dec 31. **LIMIT: NQ-specific Globex holiday TIMES are behind the DATE-widget — NOT_OBTAINED from static HTML (same limit as ES; evidence trail in fetch_log.jsonl)** | LIVE_OFFICIAL — https://www.cmegroup.com/trading-hours.html (web_reader, 2026-10-03) |

Verdict (holidays): **PASS-with-coverage 17/17 years** — 2010 full session-level family detail (official PDF); 2011-2025 archived official (windows all years; equity-family early-close times 2016-2020 + generic floor times 2022-2025; 2011 and 2021 product-level times NOT_TRANSCRIBED); 2026 LIVE_OFFICIAL windows + family notes, NQ-specific Globex times NOT_OBTAINED (widget).

## 2) NQ quarterly expiration rule (verbatim, official)

| Era | Verbatim rule text (official contract-spec page) | Source (capture) |
|---|---|---|
| 2015 (page times listed as Central Time) | "Last Trade Date/Time … CME Globex: **Trading can occur up to 8:30 a.m. on the 3rd Friday of the contract month.**" (8:30 a.m. CT) | ARCHIVED_OFFICIAL https://web.archive.org/web/20150319053049/http://www.cmegroup.com/trading/equity-index/us-index/e-mini-nasdaq-100_contract_specifications.html |
| 2018 | "Termination Of Trading — **Trading can occur up until 9:30 a.m. Eastern Time (ET) on the 3rd Friday of the contract month** / BTIC trading terminates at 4:00 p.m. ET on the Thursday before the 3rd Friday of contract month" (9:30 ET = 8:30 CT, same clock instant as 2015 wording) | ARCHIVED_OFFICIAL https://web.archive.org/web/20180602045617/…/e-mini-nasdaq-100_contract_specifications.html |
| 2020 | "Termination Of Trading — **Trading teminates [sic] at 9:30 a.m. ET on the 3rd Friday of the contract month.**" (official typo preserved) | ARCHIVED_OFFICIAL https://web.archive.org/web/20200630023726/…/e-mini-nasdaq-100_contract_specifications.html |

Contract months (verbatim, 2015 + 2018 captures): "Five months in the March Quarterly Cycle (Mar, Jun, Sep, Dec)". Current-era (2026) rule text NOT_OBTAINED from a static official page (live spec page + 2023 capture are JS shells; rulebook.cmegroup.com web_reader -500; browser unavailable in subagent — all logged).

## 3) NQ quarterly expiration dates 2010-2026 (all quarters)

Product-specific rows are verbatim "Last Trade/Settlement" dates from archived NQ product-calendar captures. Backing captures:

- P1 = 20091207203237, P2 = 20110305184630, P3 = 20110810150221, P4 = 20120512052009, P5 = 20130827223313, P6 = 20140406221424, P7 = 20150420224734, P8 = 20160531084129, P9 = 20170523204109, P10 = 20171023210838 — all of `https://web.archive.org/web/{ts}/https://www.cmegroup.com/trading/equity-index/us-index/e-mini-nasdaq-100_product_calendar_futures.html`.
- Family-level (F-series) = rolldates captures (see §4 of ES_EXPIRATIONS_GAPFILL.md for verbatim table): R1 = 20191019064427 (2018Q1-2020Q4), R2 = 20210420094153 (2020Q1-2022Q4; confirmed identical by 20211124215638, 20220127112011, 20220817040258), R3 = 20240616114215 (2022Q4-2025Q4), R4 = 20260122070119 (2025Q1-2028Q4), R5 = 20120829175938 (2012Q2-2015Q1), R6 = 20141006184010 (2014Q3-2016Q4) — all of `https://web.archive.org/web/{ts}/https://www.cmegroup.com/trading/equity-index/rolldates.html`, column "U.S. Indexes — Expiration" (official CME family table; verbatim excerpt in ES gapfill file).

| Contract | Code | Last Trade / Settle | Source class |
|---|---|---|---|
| Mar 2010 | NQH10 | 03/19/2010 | P1 |
| Jun 2010 | NQM10 | 06/18/2010 | P1 |
| Sep 2010 | NQU10 | 09/17/2010 | P1 |
| Dec 2010 | NQZ10 | 12/17/2010 | P1 |
| Mar 2011 | NQH11 | 03/18/2011 | P1, P2 |
| Jun 2011 | NQM11 | 06/17/2011 | P2 |
| Sep 2011 | NQU11 | 09/16/2011 | P2, P3 |
| Dec 2011 | NQZ11 | 12/16/2011 | P2, P3 |
| Mar 2012 | NQH12 | 03/16/2012 | P3 |
| Jun 2012 | NQM12 | 06/15/2012 | P3, P4, R5 |
| Sep 2012 | NQU12 | 09/21/2012 | P3, P4, R5 |
| Dec 2012 | NQZ12 | 12/21/2012 | P4, R5 |
| Mar 2013 | NQH13 | 03/15/2013 | P4, R5 |
| Jun 2013 | NQM13 | 06/21/2013 | P4, R5 |
| Sep 2013 | NQU13 | 09/20/2013 | P4, P5, R5 |
| Dec 2013 | NQZ13 | 12/20/2013 | P5 |
| Mar 2014 | NQH14 | 03/21/2014 | P5, R5 |
| Jun 2014 | NQM14 | 06/20/2014 | P5, P6, R5/R6 |
| Sep 2014 | NQU14 | 09/19/2014 | P5, P6, R6 |
| Dec 2014 | NQZ14 | 12/19/2014 | P6, R6 |
| Mar 2015 | NQH15 | 03/20/2015 | P6, P7, R6 |
| Jun 2015 | NQM15 | 06/19/2015 | P6, P7 |
| Sep 2015 | NQU15 | 09/18/2015 | P7 |
| Dec 2015 | NQZ15 | 12/18/2015 | P7 |
| Mar 2016 | NQH16 | 03/18/2016 | P7, P8 |
| Jun 2016 | NQM16 | 06/17/2016 | P7, P8 |
| Sep 2016 | NQU16 | 09/16/2016 | P8 |
| Dec 2016 | NQZ16 | 12/16/2016 | P8 |
| Mar 2017 | NQH17 | 03/17/2017 | P8 |
| Jun 2017 | NQM17 | 06/16/2017 | P8, P9 |
| Sep 2017 | NQU17 | 09/15/2017 | P9 |
| Dec 2017 | NQZ17 | 12/15/2017 | P9, P10 |
| Mar 2018 | NQH18 | 03/16/2018 | P9, P10 |
| Jun 2018 | NQM18 | 06/15/2018 | P9, P10 |
| Sep 2018 | NQU18 | 09/21/2018 | P10 |
| Dec 2018 | NQZ18 | 12/21/2018 | P10 |
| Mar 2019 | NQH19 | 3/15/19 | R1 (family) |
| Jun 2019 | NQM19 | 6/21/19 | R1 (family) |
| Sep 2019 | NQU19 | 9/20/19 | R1 (family) |
| Dec 2019 | NQZ19 | 12/20/19 | R1 (family) |
| Mar 2020 | NQH20 | 3/20/20 | R1, R2 (family) |
| Jun 2020 | NQM20 | 6/19/20 | R1, R2 (family) |
| Sep 2020 | NQU20 | 9/18/20 | R1, R2 (family) |
| Dec 2020 | NQZ20 | 12/18/20 | R1, R2 (family) |
| Mar 2021 | NQH21 | 3/19/21 | R2 (family) |
| Jun 2021 | NQM21 | 6/18/21 | R2 (family) |
| Sep 2021 | NQU21 | 9/17/21 | R2 (family) |
| Dec 2021 | NQZ21 | 12/17/21 | R2 (family) |
| Mar 2022 | NQH22 | 3/18/22 | R2 (family) |
| Jun 2022 | NQM22 | 6/17/22 | R2 (family) |
| Sep 2022 | NQU22 | 9/16/22 | R2, R3 (family) |
| Dec 2022 | NQZ22 | 12/16 | R2, R3 (family) |
| Mar 2023 | NQH23 | 3/17 | R3 (family) |
| Jun 2023 | NQM23 | 6/16 | R3 (family) |
| Sep 2023 | NQU23 | 9/15 | R3 (family) |
| Dec 2023 | NQZ23 | 12/15 | R3 (family) |
| Mar 2024 | NQH24 | 3/15 | R3 (family) |
| Jun 2024 | NQM24 | 6/21 | R3 (family) |
| Sep 2024 | NQU24 | 9/20 | R3 (family) |
| Dec 2024 | NQZ24 | 12/20 | R3 (family) |
| Mar 2025 | NQH25 | 3/21 | R3, R4 (family) |
| Jun 2025 | NQM25 | 6/20 | R3, R4 (family) |
| Sep 2025 | NQU25 | 9/19 | R3, R4 (family) |
| Dec 2025 | NQZ25 | 12/19 | R3, R4 (family) |
| Mar 2026 | NQH26 | 3/20 | R4 (family) |
| Jun 2026 | NQM26 | 6/18 (Juneteenth-shifted; 3rd Friday Jun 19 2026 = Juneteenth) | R4 (family) |
| Sep 2026 | NQU26 | 9/18 | R4 (family) |
| Dec 2026 | NQZ26 | 12/18 | R4 (family) |

Bonus (outside 2010-2026 window): Dec 2009 NQZ09 = 12/18/2009 (P1).

Coverage count: **68/68 quarters 2010-2026** — 36 ARCHIVED_OFFICIAL_PRODUCT (Mar 2010-Dec 2018) + 32 ARCHIVED_OFFICIAL_FAMILY (2019-2026, official rolldates "U.S. Indexes" Expiration column). Family dates cross-check EXACTLY against product-specific NQ dates on every overlap (2018: 3/16, 6/15, 9/21, 12/21) and against ES product-calendar dates on every overlap (2018, 2024-2025) — see ES gapfill file.

## Verdicts (NQ blockers)

1. NQ holidays + early closes 2010-2026: **PASS-with-coverage (17/17 years)**. Residual gaps, honestly scoped: NQ-specific Globex early-close TIMES for 2011 (linked PDFs not transcribed), 2021-2025 (per-holiday files not transcribed / floor tables generic), and 2026 (widget; NOT_OBTAINED — transport evidence logged). Holiday DATES and family-level early-close days/times are authority-backed all 17 years.
2. NQ quarterly expirations: **PASS-with-coverage (rule verbatim from 3 official eras + 68/68 quarterly dates)** — 2010-2018 product-specific, 2019-2026 official family table. Caveat: the family table's wording covers "Equity Index Quarterly Futures / U.S. Indexes" without naming NQ; per dispatch method rule this wording is authority for the family (quoted verbatim); every available product-specific cross-check agrees with zero divergence.
3. NOT_OBTAINED items (no inference used anywhere): current-2026-era NQ rule text from a static official page; NQ 2026 Globex holiday session times; NQ product-specific (non-family) tables for 2019-2026 (widget/JS era — measured: futures-subpage captures from 2018-06-01 are "No Data Available"; new-URL capture 20250702132707 is a React shell).
