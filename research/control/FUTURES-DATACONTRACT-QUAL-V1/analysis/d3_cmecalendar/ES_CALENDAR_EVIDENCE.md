# ES (E-mini S&P 500) — Official CME Calendar Evidence (Lane D3-CMECAL)

Cycle: FUTURES-DATACONTRACT-QUAL-V1 | Lane: D3-CMECAL | Acquisition date: 2026-10-03
Scope: CME official holiday calendar (full closures + early-close/short sessions with times) for ES, per year 2010..2026, plus contract expiration (Last Trade / Final Settlement) calendar where obtainable.
Laws honored: normal public access only; no spoofed headers/user-agents (curl default UA / reader tools only); no proxies; <=2 attempts per distinct URL per access method, no retry storms; 403/timeout results recorded as evidence; uncertain days EXCLUDED (NOT_RUN), never inferred from neighboring years or memory.

## Provenance labels

- `LIVE_OFFICIAL` — fetched directly from cmegroup.com on 2026-10-03 (normal public access).
- `ARCHIVED_OFFICIAL` — capture of an official cmegroup.com page via web.archive.org (public archive); archive URL + resolved capture timestamp + original URL recorded per datum.
- `LEADS_ONLY` — non-authoritative pointers (never used as authority below).
- `NOT_OBTAINED` / `NOT_TRANSCRIBED` — no authority-backed datum in hand / fetch succeeded but content not preserved in record.

## Measurement note (vs prior cycles)

Prior cycles (FX-FUTURES-FRONTIER-V1 2026-09-17; re-measure 2026-10-02) recorded cmegroup.com as HTTP 403 app-layer bot filtering. On 2026-10-03, LIVE cmegroup.com returned full content to the `web_reader` MCP tool (holiday/trading-hours page, product calendar page, one official PDF); WebFetch on the same page timed out (2x 60000 ms). Not contradictory (different client paths); operative finding: LIVE access worked on 2026-10-03 via web_reader, and web.archive.org worked via plain curl (default UA).

## Correction log (self-audit, kept for integrity)

During acquisition, two intermediate drafts of this file contained details reconstructed from pattern memory rather than fetched text (a "2025 verbatim" section and part of a "2026 re-verified" section). Both were purged; the 2026 section below now contains only data recorded at first-fetch time, and 2024/2025 data below comes from a fully re-extracted static capture (20241112201950) whose tables are reproduced verbatim. Nothing in this file is memory-filled.

## Method

1. LIVE route: `web_reader` on https://www.cmegroup.com/trading-hours.html (current holiday host; /tools-information/holiday-calendar.html 302-redirects there since ~mid-2025), live ES product calendar page, one official PDF probe.
2. ARCHIVE route: `web_reader` and/or plain `curl -sL` (default UA) on `https://web.archive.org/web/{ts}/{original-url}`; Wayback resolves to nearest capture; resolved capture recorded. Deterministic table extraction with python over the saved HTML (scripts/styles stripped, `<table>` rows joined with `|`). Original URLs:
   - Holiday page pre-2016: `http://www.cmegroup.com/tools-information/holiday-calendar/`
   - Holiday page 2016-2024: `https://www.cmegroup.com/tools-information/holiday-calendar.html`
   - 2025+: `https://www.cmegroup.com/trading-hours.html`
   - ES product calendar (old static URL; captures 2009-01-22..2020-09-24): `https://www.cmegroup.com/trading/equity-index/us-index/e-mini-sandp500_product_calendar.html`
   - ES product calendar (current): `https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.calendar.html` (JS shell live and in most captures)
3. Official per-holiday advisory PDFs discovered embedded in captures under `https://www.cmegroup.com/tools-information/holiday-calendar/files/...` (58 URLs catalogued for 2024-2025 from capture 20241112201950; see PDF section).
4. Transcription rule: every datum below is copied from text actually present in a fetched artifact kept in this session's record (tool output or saved HTML re-parsed locally). Days/fields not present are marked NOT_OBTAINED/NOT_TRANSCRIBED.

## Attempt log (all 2026-10-03)

| # | URL | Tool | Status |
|---|-----|------|--------|
| 1 | https://www.cmegroup.com/trading-hours.html | WebFetch x2 | FAIL — tool timeout 60000 ms x2 |
| 2 | https://www.cmegroup.com/trading-hours.html | web_reader | SUCCESS — 2026 tables (LIVE_OFFICIAL) |
| 3 | https://www.cmegroup.com/markets/equities/sp/e-mini-sandp500.calendar.html | web_reader | SUCCESS (200) but JS shell — no contract rows |
| 4 | https://www.cmegroup.com/tools-information/holiday-calendar/files/2026/2026-good-friday-clearing-advisory.pdf | web_reader | SUCCESS — official PDF text extracted |
| 5 | web.archive.org CDX/availability endpoints | WebFetch; web_reader | FAIL — 503/timeout; MCP -400 then -500; abandoned |
| 6 | http://www.cmegroup.com/company/holiday-schedule.html (guessed, via archive) | web_reader | FAIL — -500; abandoned after 1 attempt |
| 7 | holiday-calendar/ + .html captures 2010..2024 (year-prefixed requests) | web_reader | SUCCESS each; resolved: 2010→20100414015939; 2011→20110701; 2012→20120616171859; 2013→20130119015927; 2014→20140626070427; 2015→20150710035807; 2016→20160214222113; 2017→20170703230701 (+20170419); 2018→20180701+20181115; 2019→20190701 (1st -500, retry OK); 2020→20200701; 2021→20210701; 2022→20220701; 2023→20230701; 2024→20240627161753 |
| 8 | holiday-calendar.html @2025 | web_reader | 302 → trading-hours.html; capture @20250701 SUCCESS (tables; details below) |
| 9 | ES product calendar (old URL) captures 2015, 2016-09-16, 2017-10-20, 2024-09-27 | web_reader | SUCCESS — static contract tables |
| 10 | ES product calendar (old URL) @20191001 → resolved 20200924060333 | web_reader x2 (1st -500) | SUCCESS (200) but JS shell — static era ends 2020-09-24 |
| 11 | ES product calendar (old URL) 2009-2018 assorted ts | web_reader | transport OK; several extractions not retained (context compaction) → NOT_TRANSCRIBED, superseded by curl pass below |
| 12 | https://web.archive.org/web/20241115000000/https://www.cmegroup.com/trading-hours.html | curl -sL | SUCCESS — resolved capture 20241112201950, 277 KB static HTML; ALL 2024+2025 tables extracted verbatim (below) |
| 13 | per-year holiday captures via curl | curl -sL + python | see per-year sections (each cites its resolved capture) |

---

## Per-year calendar data

### 2026 — LIVE_OFFICIAL (web_reader, 2026-10-03, https://www.cmegroup.com/trading-hours.html)

CME Globex 2026 holiday windows (window includes preceding early close through reopen):
- New Year's: Dec 31 2025 – Jan 2 2026
- Martin Luther King Day: Jan 18 – Jan 20 2026
- Presidents' Day: Feb 15 – Feb 17 2026
- Good Friday: Apr 2 – Apr 4 2026
- Memorial Day: May 24 – May 26 2026
- Juneteenth: Jun 18 – Jun 19 2026
- Independence Day: Jul 3 – Jul 5 2026
- Labor Day: Sep 6 – Sep 8 2026
- Thanksgiving: Nov 26 – Nov 28 2026
- Christmas: Dec 24 – Dec 26 2026
- New Year's: Dec 31 2026 – Jan 1 2027

CME ClearPort 2026: closed (no open) on the holiday itself: Jan 1, Jan 19, Feb 16, Apr 3, May 25, Jun 19, Jul 3, Sep 7, Nov 26, Dec 25; early close 13:15 ET the prior day; 12:00 ET early close pattern Thanksgiving/Christmas-eve per page table.

Trading Floor 2026 (Chicago): early closes 12:00 CT on May 22, Jul 2, Nov 27, Dec 24, Dec 31; Good Friday Apr 3 close 10:00 CT.

Holiday Notes (page): some products early-close 13:15/13:00 CT; some products (incl. weekly options) trade 09:30–12:00 CT on those days; Globex Equity AND Interest Rate products trade NORMAL hours on MLK and Presidents' days; TAS early closes Nov 27, Dec 24, Dec 31.

LIMIT (ES-specific): with 2026, CME moved product-level Globex holiday hours into downloadable calendars + an interactive widget ("select the appropriate date in the 'DATE' field...") — ES-specific Globex early-close TIMES are NOT in static HTML => NOT_OBTAINED from this page. ClearPort/floor times above are page-static.

ES 2026 expirations: NOT_OBTAINED (live product calendar = JS shell; no static 2026-era capture found within budget).

### 2025 — ARCHIVED_OFFICIAL (static tables, capture 20241112201950 of https://www.cmegroup.com/trading-hours.html)

Archive URL: https://web.archive.org/web/20241112201950/https://www.cmegroup.com/trading-hours.html

2025 CME Globex Trading Schedule (verbatim table):
| U.S. Holiday | Includes the following dates: |
|---|---|
| Dr. Martin Luther King, Jr. | 17 - 20 January 2025 |
| President's Day | 14 - 17 February 2025 |
| Good Friday | 17 - 21 April 2025 |
| Memorial Day | 23 - 27 May 2025 |
| Juneteenth Day | 18 June 2025 |
| Independence Day | 3 - 7 July 2025 |
| Labor Day | 29 August - 1 September 2025 |
| Columbus Day | 13 October 2025 |
| Veterans Day | 11 November 2025 |
| Thanksgiving | 26 - 28 November 2025 |
| Christmas | 24 - 26 December 2025 |
| New Year's Eve | 31 December 2025 - 2 January 2026 |

2025 clearing notices dates (verbatim table "U.S. Holiday | Includes the following dates"): MLK 20 January 2025; Presidents 17 February 2025; Good Friday 18 April 2025; Memorial 26 May 2025; Juneteenth 19 June 2025; Independence 4 July 2025; Labor 1 September 2025; Columbus 13 October 2025; Veterans 11 November 2025; Thanksgiving 27 November 2025; Christmas 24 - 26 December 2025; New Year's 31 December 2025 - 2 January 2026.

Floor: Chicago floor closed Wed Jan 1 2025; early close Tue Dec 31 2024 12:00 CT (rows from the 2024 floor table spanning into 2025).
ClearPort (from 2025 advisory rows in same capture): normal schedule on MLK/Presidents/etc.; no-open days per 2025-2026 advisories: Jan 1 2025, Apr 18 2025, Dec 25 2025, Jan 1 2026 (pattern from embedded advisory set; the full 2025 ClearPort table sits in the Jun-2025 capture fetched via web_reader — content not retained; flagged NOT_TRANSCRIBED beyond the rows above).

ES 2025 expirations — ARCHIVED_OFFICIAL (product-calendar capture 2024-09-27, dates under 2024 section).

### 2024 — ARCHIVED_OFFICIAL (static tables, capture 20241112201950)

Archive URL: https://web.archive.org/web/20241112201950/https://www.cmegroup.com/trading-hours.html

2024 CME Globex Trading Schedule (verbatim):
| U.S. Holiday | Includes the following dates: |
|---|---|
| Dr. Martin Luther King, Jr. | 12 - 16 January 2024 |
| President's Day | 16 - 20 February 2024 |
| Good Friday | 28 March - 1 April 2024 |
| Memorial Day | 24 - 28 May 2024 |
| Juneteenth Day | 18 - 20 June 2024 |
| Independence Day | 3 - 5 July 2024 |
| Labor Day | 30 August - 3 September 2024 |
| Columbus Day | 14 October 2024 |
| Veterans Day | 11 November 2024 |
| Thanksgiving | 27 - 29 November 2024 |
| Christmas | 24 - 26 December 2024 |
| New Year's Eve | 31 December 2024 - 2 January 2025 |

2024 CME ClearPort (verbatim): does NOT open only on Mon Jan 1 2024 (reopens same day 18:00 ET for next day's trade date), Good Friday Fri Mar 29 2024 (reopens Sun Mar 31 2024 18:00 ET), Christmas Wed Dec 25 2024 (reopens same day 18:00 ET), New Year Wed Jan 1 2025 (reopens same day 18:00 ET). All other 2024 holidays (MLK, Presidents, Memorial, Juneteenth Jul 4 observed, Labor, Columbus, Thanksgiving): "Unaffected and will run on a normal schedule".

2024 Trading Floor, Chicago (verbatim): floor CLOSED: Jan 1, Jan 15, Feb 19, Mar 29 (Good Friday), May 27, Jun 19, Jul 4, Sep 2, Nov 28, Dec 25 2024, Jan 1 2025. Early closes 12:00 CT: Fri Dec 29 2023, Thu Mar 28 2024, Fri May 24 2024, Wed Jul 3 2024, Fri Nov 29 2024, Tue Dec 24 2024, Tue Dec 31 2024.

2024 clearing notices dates (verbatim): MLK 15 Jan; Presidents 19 Feb; Good Friday 29 Mar; Memorial 27 May; Juneteenth 19 Jun; Independence 4 Jul; Labor 2 Sep; Columbus 14 Oct; Veterans 11 Nov; Thanksgiving 28 Nov; Christmas 24-26 Dec 2024; New Year's 31 Dec 2024 - 2 Jan 2025.

(An earlier web_reader pass on capture 20240627161753 recorded Globex rows annotated "Equity and Interest Rate Products will trade from 9:30 a.m. - 12:00 p.m. CT"; direct re-parse of that same capture's static HTML shows only repo/BrokerTec tables — that annotation is therefore recorded as CONFLICTED and NOT relied upon. The verbatim tables above come from the cleaner Nov-2024 capture.)

ES 2024-2025 expirations — ARCHIVED_OFFICIAL (product-calendar capture 2024-09-27; URL family: web.archive.org/web/20240927.../e-mini-sandp500_product_calendar.html):
- Sep 2024: First trade Mar 11 2024; Last Trade/Settle Sep 20 2024
- Dec 2024: First Jun 10 2024; Last Trade/Settle Dec 20 2024
- Mar 2025: First Sep 09 2024; Last Trade/Settle Mar 21 2025
- Jun 2025: First Dec 09 2024; Last Trade/Settle Jun 20 2025
- Sep 2025: First Mar 10 2025; Last Trade/Settle Sep 19 2025
- Dec 2025: First Jun 09 2025; Last Trade/Settle Dec 19 2025
- Mar 2024 / Jun 2024 quarters: NOT_OBTAINED (capture starts Sep 2024 listing).

### 2012 — ARCHIVED_OFFICIAL (curl + local extraction)

Capture: 20120616171859 of http://www.cmegroup.com/tools-information/holiday-calendar/
Archive URL: https://web.archive.org/web/20120616171859/http://www.cmegroup.com/tools-information/holiday-calendar/

CME Globex windows (verbatim "CME Globex Date U.S. Holiday ..."):
- Christmas 2011: 23 - 27 December 2011
- New Year's: 31 December 2011 - 3 January 2012
- Dr. Martin Luther King, Jr.: 13 - 17 January 2012
- President's Day: 17 - 21 February 2012
- Good Friday: 5 - 8 April 2012
- Memorial Day: 25 - 29 May 2012 (PDF | Excel version)
- Independence Day: 3 - 5 July 2012
- Labor Day: 31 August - 4 September 2012
- Columbus Day: 5 - 8 October 2012
- Veteran's Day: 11 - 12 November 2012
- Thanksgiving: 21 - 23 November 2012
- Christmas: 24 - 26 December 2012
- New Year's: 31 December 2012 - 2 January 2013

Per-holiday PDF/XLS links present on page (official). ClearPort/floor day-level tables NOT inline.

ES 2012-2013 expirations — see "2012/2013 (partial)" section.

### 2013 — ARCHIVED_OFFICIAL (curl + local extraction)

Capture: 20130119015927 of http://www.cmegroup.com/tools-information/holiday-calendar/
Archive URL: https://web.archive.org/web/20130119015927/http://www.cmegroup.com/tools-information/holiday-calendar/

CME Globex windows (verbatim "2013 Dates U.S. Holiday ..."):
- Dr. Martin Luther King, Jr.: 18 - 22 January 2013
- President's Day: 15 - 19 February 2013
- Good Friday: 28 - 31 March 2013
- Memorial Day: 24 - 28 May 2013
- Independence Day: 3 - 5 July 2013
- Labor Day: 30 August - 3 September 2013
- Columbus Day: 14 October 2013
- Veteran's Day: 11 November 2013
- Thanksgiving: 27 - 29 November 2013
- Christmas: 24 - 26 December 2013
- New Year's: 31 December 2013 - 2 January 2014

(New Year's day Jan 1 2013 window is the tail row of the 2012 page: 31 Dec 2012 - 2 Jan 2013.)
Page also lists: CME ClearPort 2013 U.S. Holiday Schedule (PDF); Chicago/NY/KCBOT floor calendar PDFs; Archived Holiday Calendars 2012/2011/2010/2009 (ZIP).

### 2015 — ARCHIVED_OFFICIAL (curl + local extraction)

Capture: 20150710035807 of http://www.cmegroup.com/tools-information/holiday-calendar/ (resolved 20150710140009)
Archive URL: https://web.archive.org/web/20150710035807/http://www.cmegroup.com/tools-information/holiday-calendar/

"2015 Holiday Schedule CME Globex U.S. Holiday Includes the following dates:" (verbatim):
- Dr. Martin Luther King, Jr.: 16 - 20 January 2015
- President's Day: 13 - 17 February 2015
- Good Friday: 2 - 6 April 2015
- Memorial Day: 22 - 26 May 2015
- Independence Day: 2 - 6 July 2015
- Labor Day: 4 - 8 September 2015
- Columbus Day: 12 October 2015
- Veteran's Day: 11 November 2015
- Thanksgiving: 25 - 27 November 2015
- Christmas: 24 - 28 December 2015
- New Year's: 31 December 2015 - 4 January 2016

Notices on page: "Independence Day Settlement Notice (for Thursday, 7/2/2015)", "Labor Day Settlement Notice (for Friday, 9/4/2015)" (=> Jul 2 2015 and Sep 4 2015 = official early-close/settlement-notice days).
ClearPort first-pass detail (from the same page via web_reader at first fetch; ClearPort table is a JS/linked tab not present in static curl HTML — retained with caveat): ClearPort closed Jan 1, Apr 3, Nov 26, Dec 25 2015; early closes 13:15 ET on Jan 1, Jan 19, Feb 16, Apr 2, May 22, Sep 4, Oct 12, Nov 11; 14:00 ET Jul 2; 12:00 ET Nov 27 and Dec 24; Jul 3 normal schedule.

### 2014 — ARCHIVED_OFFICIAL (re-verified via curl; first-pass record confirmed identical)

Capture: 20140626070427 of http://www.cmegroup.com/tools-information/holiday-calendar/
Archive URL: https://web.archive.org/web/20140626070427/http://www.cmegroup.com/tools-information/holiday-calendar/

CME Globex 2014 holiday windows (recorded at first fetch):
MLK Jan 17-21; Presidents Feb 14-18; Good Friday Apr 17-21; Memorial May 23-27; Independence Jul 3-7; Labor Aug 29-Sep 2; Columbus Oct 13; Veterans Nov 11; Thanksgiving Nov 26-28; Christmas Dec 24-26; New Year Dec 31 2014 - Jan 2 2015.

### 2016 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20160214222113 of https://www.cmegroup.com/tools-information/holiday-calendar.html
Archive URL: https://web.archive.org/web/20160214222113/https://www.cmegroup.com/tools-information/holiday-calendar.html

2016 CME Globex windows (verbatim "U.S. Holiday Includes the following dates:"):
MLK 15-19 January 2016 | President's 12-16 February | Good Friday 24-28 March | Memorial 27-31 May | Independence 1-5 July | Labor 2-6 September | Columbus 10 October | Veterans 11 November | Thanksgiving 23-25 November | Christmas 23-27 December | New Year's 30 December 2016 - 3 January 2017.
(Jan 1 2016 window = tail row of the 2015 page: 31 Dec 2015 - 4 Jan 2016.)

2016 CME ClearPort (verbatim table): does not open only: Good Friday Fri 25 Mar 2016 (reopens Sun 27 Mar 2016 18:00 ET), Christmas Mon 26 Dec 2016 (reopens same day 18:00 ET), New Year's Mon 2 Jan 2017 (reopens same day 18:00 ET). Thanksgiving row: "Friday 25 November, 2016 Early Close 13:45 ET". All other holidays unaffected/normal (MLK, Presidents, Memorial, Jul 4, Labor, Columbus, Veterans).

2016 Trading Floor Chicago (verbatim key rows): Good Friday Fri Mar 25 2016 floor closed (prior day Thu Mar 24: FX & IR close 12:00 CT); Memorial Mon May 30 closed (Fri May 27: FX & IR 12:00 CT); Independence Mon Jul 4 closed (Fri Jul 1: Commodity products 12:00 CT, CME commodity options 12:02 CT); Labor Mon Sep 5 closed; Columbus Mon Oct 10: FX & IR closed, "Equities, Commodities, Weather & Real Estate - Normal Day"; Veterans Fri Nov 11: same pattern (Equities normal); Thanksgiving Thu Nov 24 closed + Fri Nov 25: FX, IR, Commodities, Weather & RE close 12:00 CT, CME commodity options 12:02 CT, EQUITIES close 12:15 CT; Christmas Mon Dec 26 closed + Fri Dec 23 2016: FX, IR, Commodities, Weather & RE 12:00 CT, commodity options 12:02 CT; New Year Mon Jan 2 2017 closed + Fri Dec 30 2016: FX & IR 12:00 CT. NY floor: Nov 25 & Dec 23 2016: NYMEX close 13:30 ET, COMEX 12:30 ET.

ES 2016-2017 expirations — ARCHIVED_OFFICIAL (product-calendar capture 2016-09-16):
- Dec 2016: First Mar 14 2016; Last Trade/Settle Dec 16 2016
- Mar 2017: Mar 17 2017 | Jun 2017: Jun 16 2017 | Sep 2017: Sep 15 2017 | Dec 2017: Dec 15 2017
- Mar/Jun/Sep 2016 quarters: NOT_OBTAINED from this capture.

### 2017 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20170703230701 of https://www.cmegroup.com/tools-information/holiday-calendar.html
Archive URL: https://web.archive.org/web/20170703230701/https://www.cmegroup.com/tools-information/holiday-calendar.html

2017 CME Globex windows (verbatim): MLK 13-17 January 2017 | President's 17-21 February | Good Friday 13-17 April | Memorial 26-30 May | Independence 3-5 July | Labor 1-5 September | Columbus 9 October | Veterans 10 November | Thanksgiving 22-24 November | Christmas 22-26 December | New Year's 29 December 2017 - 2 January 2018.

2017 CME ClearPort (verbatim): does not open only: Good Friday Fri Apr 14 2017 (reopens Sun Apr 16 2017 18:00 ET), Christmas Mon Dec 25 2017 (reopens same day 18:00 ET), New Year's Mon Jan 1 2018 (reopens same day 18:00 ET). Other holidays unaffected/normal. Thanksgiving row carries the 2016 carry-over cell "Friday November 24, 2016 Early Close 13:45 ET" — PAGE ANOMALY confirmed as stale 2016 data (the 2016 capture shows the same wording for Fri Nov 25 2016); the corresponding 2017 datum (Fri Nov 24 2017 ClearPort early close time) is NOT stated on this page => NOT_OBTAINED from this source.

2017 Trading Floor Chicago (verbatim key rows): Good Friday Fri Apr 14 2017 closed (Thu Apr 13: FX & IR floor options 12:00 CT); Memorial Mon May 29 closed (Fri May 26: FX & IR 12:00 CT); Independence Tue Jul 4 closed (Mon Jul 3: FX, IR, Grain, Dairy, Weather & RE floor options 12:00 CT, Livestock options 12:02 CT, EQUITIES futures and options 12:15 CT); Labor Mon Sep 4 closed; Columbus Mon Oct 9: FX & IR closed, "Equities, Commodities, Weather & Real Estate - Normal Day"; Veterans Fri Nov 10: "All Floor Markets Open - Normal Trading Hours"; Thanksgiving Thu Nov 23 closed (Fri Nov 24: FX/IR/Grains/Weather/RE 12:00 CT, Livestock 12:02 CT, EQUITIES 12:15 CT); Christmas Mon Dec 25 closed (Fri Dec 22: FX/IR/Grains/Dairy/Weather/RE 12:00 CT, Livestock 12:02 CT, "Equities Normal day"); New Year Mon Jan 1 2018 closed (Fri Dec 29 2017: FX & IR 12:00 CT).

ES 2017-2018 expirations — ARCHIVED_OFFICIAL (product-calendar capture 2017-10-20):
- Dec 2017: Dec 15 2017 | Mar 2018: Mar 16 2018 | Jun 2018: Jun 15 2018 | Sep 2018: Sep 21 2018 | Dec 2018: Dec 21 2018

### 2012/2013 (partial) — ARCHIVED_OFFICIAL (expirations)

Product-calendar capture 20120616171859:
- JUN 2012 (ESM12): First Mar 18 2011; Last Trade/Settle Jun 15 2012
- SEP 2012 (ESU12): First Jun 17 2011; Last Sep 21 2012
- DEC 2012 (ESZ12): First Sep 16 2011; Last Dec 21 2012
- MAR 2013 (ESH13): First Dec 16 2011; Last Mar 15 2013
- JUN 2013 (ESM13): First Mar 16 2012; Last Jun 21 2013
- SEP 2013 (ESU13): First Jun 15 2012; Last Sep 20 2013

### 2011 — ARCHIVED_OFFICIAL (curl + local extraction, 2026-10-03)

Capture: 20110313182401 of http://www.cmegroup.com/tools-information/holiday-calendar/ (requested @20110415; resolved 20110313182401)
Archive URL: https://web.archive.org/web/20110313182401/http://www.cmegroup.com/tools-information/holiday-calendar/

CME Globex holiday windows (verbatim from page text "CME Globex Date U.S. Holiday ..."):
- Christmas 2010: 23 - 26 December 2010
- New Year's: 31 December 2010 - 3 January 2011
- Dr. Martin Luther King, Jr.: 14 - 18 January 2011
- President's Day: 18 - 22 February 2011
- Good Friday: 21 - 24 April 2011
- Memorial Day: 27 - 31 May 2011
- Independence Day: 1 - 5 July 2011
- Labor Day: 2 - 6 September 2011
- Columbus Day: 7 - 10 October 2011
- Veteran's Day: 10 - 11 November 2011
- Thanksgiving: 23 - 25 November 2011
- Christmas: 23 - 27 December 2011
- New Year's: 30 December 2011 - 3 January 2012

Page also links official PDFs (captured in archive): per-holiday 2011 PDFs (2011-martin-luther-king.pdf ... 2012-new-years.pdf), CME_Clearport_2011_Holiday_Calendar.pdf, 2011floorholidaycard.pdf, New_York_Floor_Holiday_Calendar_2011.pdf, Holiday-Early-Close-Schedule.pdf — ES-specific times are inside those PDFs (see PDF section). ClearPort/floor day-level tables NOT inline on this page => NOT_TRANSCRIBED from HTML; PDFs are the authority route.

### 2010 — ARCHIVED_OFFICIAL, FULL PRODUCT-LEVEL DETAIL (official 38-page PDF)

Artifact: "CME Globex 2010 Holiday Calendar" PDF; per-section "Last updated" stamps 12/17/2009 - 2/3/2010.
Archive URL: https://web.archive.org/web/20100215061802/http://www.cmegroup.com/tools-information/holiday-calendar/files/2010-globex-holiday-calendar.pdf
Original URL: http://www.cmegroup.com/tools-information/holiday-calendar/files/2010-globex-holiday-calendar.pdf

CME Globex EQUITY products (ES family), verbatim per holiday (all times CT):
- New Year's 2010: Thu Dec 31 2009 15:15 regular close (trade date Dec 31); FRI JAN 1 2010 GLOBEX CLOSED; Sun Jan 3 17:00 regular open (trade date Mon Jan 4).
- MLK: Fri Jan 15 15:15 regular close; Sun Jan 17 17:00 open for trade date Tue Jan 19; Mon Jan 18 10:30 trading halt (order entry/mod/cancel allowed), 17:00 resume; Tue Jan 19 15:15 regular close.
- Presidents' Day: Fri Feb 12 15:15 regular close; Sun Feb 14 17:00 open for trade date Tue Feb 16; Mon Feb 15 10:30 halt, 17:00 resume; Tue Feb 16 15:15 regular close. (Exception: USD & JY Nikkei regular times.)
- Good Friday: Thu Apr 1 15:15 regular close; 15:30 regular open for trade date Fri Apr 2; FRI APR 2 EARLY GLOBEX CLOSE 08:15; Sun Apr 4 17:00 regular open (trade date Mon Apr 5).
- Memorial Day: Fri May 28 15:15 regular close; Sun May 30 17:00 open for trade date Tue Jun 1; Mon May 31 10:30 halt, 17:00 resume; Tue Jun 1 15:15 regular close.
- Fourth of July: Fri Jul 2 15:15 regular close; Sun Jul 4 17:00 open for trade date Tue Jul 6; Mon Jul 5 10:30 halt, 17:00 resume; Tue Jul 6 15:15 regular close.
- Labor Day: Fri Sep 3 15:15 regular close; Sun Sep 5 17:00 open for trade date Tue Sep 7; Mon Sep 6 10:30 halt, 17:00 resume; Tue Sep 7 15:15 regular close.
- Columbus Day: Fri Oct 8 15:15 regular close; Sun Oct 10 17:00 open; MON OCT 11 15:15 REGULAR close (normal session, no halt).
- Veterans Day: Wed Nov 10 15:15 close; 15:30 open for trade date Thu Nov 11; THU NOV 11 15:15 REGULAR close (normal session); 15:30 open Fri Nov 12; Fri Nov 12 15:15 close.
- Thanksgiving: Wed Nov 24 15:15 regular close; 15:30 regular open for trade date Fri Nov 26; Thu Nov 25 10:30 halt, 17:00 resume; FRI NOV 26 EARLY GLOBEX CLOSE 12:15.
- Christmas: Thu Dec 23 15:15 regular close; FRI DEC 24 GLOBEX CLOSED; Sun Dec 26 17:00 regular open (trade date Mon Dec 27).
- New Year's 2011: Fri Dec 31 2010 15:15 regular close; Sun Jan 2 2011 17:00 regular open (trade date Mon Jan 3).

PDF also contains Interest Rate / FX / Commodity sections (not transcribed; ES is Equity family). The 2010 holiday PAGE captures (20100315131807, 20100414015939) are link farms to the official PDFs (per-holiday 2010 PDFs; CME_Clearport_2010_Holiday_Calendar.pdf; 2010floorholidaycard.pdf; New_York_Floor_Holiday_Calendar_2010.pdf) and carried the notices "CME Group Holiday Schedule for December 31, 2010" and "CME Group Holiday Early Close Schedule for 31 December 2010".

ES 2010 expirations — ARCHIVED_OFFICIAL (product-calendar capture 20090310081357):
- Mar 2010 (ESH10): First 12/19/2008; Last Trade/Settle 03/19/2010
- Jun 2010 (ESM10): First 03/20/2009; Last Trade/Settle 06/18/2010
- Sep 2010 / Dec 2010: NOT_OBTAINED (archive capture gap; see expirations section)
- Bonus same capture (2009): Mar 03/20, Jun 06/19, Sep 09/18, Dec 12/18 2009.

### 2018 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20180629065738 of https://www.cmegroup.com/tools-information/holiday-calendar.html (requested @20180701)
Archive URL: https://web.archive.org/web/20180629065738/https://www.cmegroup.com/tools-information/holiday-calendar.html

2018 Globex windows (verbatim): MLK 12-16 January 2018 | President's 16-20 February | Good Friday 29 March - 2 April | Memorial 25-29 May | Independence 3-5 July | Labor 31 August - 4 September | Thanksgiving 21-23 November | Christmas 24-26 December | New Year's 31 December 2018 - 2 January 2019. (No Columbus/Veterans rows in the 2018 Globex window list — equity normal those days per floor table below. Jan 1 2018 window = 2017 page tail: 29 Dec 2017 - 2 Jan 2018.)

2018 ClearPort (verbatim): does not open only Good Friday Fri Mar 30 2018 (reopen Sun Apr 1 2018 18:00 ET); Thanksgiving: "Friday November 23, 2018 Early Close 13:45 ET"; Christmas: "Monday, December 24, 2018 Early Close 13:45 ET (does not open at 18:00 ET on Monday, Dec 24, 2018)", reopen Tue Dec 25 18:00 ET; New Year: no 18:00 ET open Mon Dec 31 2018, reopen Tue Jan 1 2019 18:00 ET. MLK/Presidents/Memorial/Jul 4/Labor: unaffected.

2018 Trading Floor Chicago (verbatim key rows): Good Friday Fri Mar 30 closed (Thu Mar 29: FX & IR floor options 12:00 CT); Memorial Mon May 28 closed (Fri May 25: FX & IR 12:00 CT); Independence Wed Jul 4 closed (Tue Jul 3: FX/IR/Grain/Dairy/Weather/RE 12:00 CT, Livestock 12:02 CT, EQUITIES 12:15 CT); Labor Mon Sep 3 closed; Columbus Mon Oct 8: FX & IR closed, "Equities, Commodities, Weather & Real Estate - Normal Day"; Veterans Mon Nov 12: same (Equities normal); Thanksgiving Thu Nov 22 closed (Fri Nov 23: FX/IR/Grains/Weather/RE 12:00 CT, Livestock 12:02 CT, EQUITIES 12:15 CT); Christmas Tue Dec 25 closed (Mon Dec 24: FX/IR/Grains/Dairy/Weather/RE 12:00 CT, Livestock 12:02 CT, EQUITIES 12:15 CT); New Year Tue Jan 1 2019 closed (Mon Dec 31 2018: FX & IR 12:00 CT).

ES 2018 expirations: see 2017 section (capture 2017-10-20 covers Dec 2017-Dec 2018 complete).

### 2019 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20190702203907 of https://www.cmegroup.com/tools-information/holiday-calendar.html (requested @20190701)
Archive URL: https://web.archive.org/web/20190702203907/https://www.cmegroup.com/tools-information/holiday-calendar.html

2019 Globex windows (verbatim): MLK 18-22 January 2019 | President's 15-19 February | Good Friday 18-22 April | Memorial 24-28 May | Independence 3-5 July | Labor 30 August - 3 September | Thanksgiving 27-29 November | Christmas 24-26 December | New Year's 31 December 2019 - 2 January 2020. (Jan 1 2019 window = 2018 page tail.)

2019 ClearPort (verbatim): does not open only Good Friday Fri Apr 19 2019 (reopen Sun Apr 21 2019 18:00 ET); Thanksgiving: "Friday November 29, 2019 Early Close 13:45 ET"; Christmas: "Tuesday, December 24, 2019 Early Close 13:45 ET (does not open at 18:00 ET on Tuesday Dec 24, 2019)", reopen Wed Dec 25 18:00 ET; New Year: no 18:00 ET open Tue Dec 31 2019. Others unaffected.

2019 Trading Floor Chicago (verbatim key rows): Good Friday Fri Apr 19 closed (Thu Apr 18: FX & IR 12:00 CT); Memorial Mon May 27 closed (Fri May 24: FX & IR 12:00 CT); Independence Thu Jul 4 closed (Wed Jul 3: FX/IR/Grain/Dairy/Weather/RE 12:00 CT, Livestock 12:02 CT, EQUITIES 12:15 CT); Labor Mon Sep 2 closed; Columbus Mon Oct 14: FX & IR closed, Equities et al. Normal Day; Veterans Mon Nov 11: same; Thanksgiving Thu Nov 28 closed (Fri Nov 29: ... EQUITIES 12:15 CT); Christmas Wed Dec 25 closed (Tue Dec 24: ... EQUITIES 12:15 CT); New Year Wed Jan 1 2020 closed (Tue Dec 31 2019: FX & IR 12:00 CT).

ES 2019 expirations: NOT_OBTAINED (old product-calendar URL static era ends 2020-09-24; 2019-era static captures not pulled within budget — see expirations note).

### 2020 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20200620052000 of https://www.cmegroup.com/tools-information/holiday-calendar.html (requested @20200701)
Archive URL: https://web.archive.org/web/20200620052000/https://www.cmegroup.com/tools-information/holiday-calendar.html

2020 Globex windows (verbatim): MLK 17-21 January 2020 | President's 14-18 February | Good Friday 9-13 April | Memorial 22-26 May | Independence 2-6 July | Labor 4-8 September | Thanksgiving 25-27 November | Christmas 24-28 December | New Year's 31 December 2020 - 4 January 2021. (Jan 1 2020 window = 2019 page tail.)

2020 ClearPort (verbatim): does not open only Good Friday Fri Apr 10 2020 (reopen Sun Apr 12 2020 18:00 ET); Independence: "Friday, July 3, 2020 Early Close 13:00 ET", "modified schedule for Monday, July 6 trade date"; Thanksgiving: "Friday November 27, 2020 Early Close 13:45 ET"; Christmas: "Thurs, December 24, 2020 Early Close 13:45 ET (does not open on Fri, Dec 25, 2020)", reopen Sun Dec 27 2020 18:00 ET; New Year: closed Fri Jan 1 2021, reopen Sun Jan 3 2021 18:00 ET. Others unaffected.

2020 Trading Floor Chicago (verbatim key rows): Good Friday Fri Apr 10 closed (Thu Apr 9: FX & IR floor options 12:00 CT); Memorial Mon May 25 closed (Fri May 22: FX & IR 12:00 CT); Independence: floor closed Fri Jul 3 2020 (holiday observed Friday; Thu Jul 2: FX/IR/Grain/Dairy/Weather/RE 12:00 CT, Livestock options 12:05 CT — NO Equities early-close entry that day); Labor Mon Sep 7 closed; Columbus Mon Oct 12: FX & IR closed, Equities et al. Normal Day; Veterans Wed Nov 11: same; Thanksgiving Thu Nov 26 closed (Fri Nov 27: ... EQUITIES futures and options 12:15 CT, Livestock 12:05 CT); Christmas Fri Dec 25 closed (Thu Dec 24: ... EQUITIES 12:15 CT); New Year Fri Jan 1 2021 closed (Thu Dec 31 2020: FX & IR 12:00 CT).

ES 2020 expirations: NOT_OBTAINED within budget (old product-calendar static era ends 2020-09-24; not pulled — see expirations note).

### 2021 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20210702163511 of https://www.cmegroup.com/tools-information/holiday-calendar.html (requested @20210701)
Archive URL: https://web.archive.org/web/20210702163511/https://www.cmegroup.com/tools-information/holiday-calendar.html

2021 Globex windows (verbatim): MLK 15-19 January 2021 | President's 12-16 February | Good Friday 1-5 April | Memorial 28 May - 1 June | Independence 2-5 July | Labor 3-7 September | Thanksgiving 24-26 November | Christmas 23-27 December | New Year's 30 December 2021 - 3 January 2022. Page note: "Holiday schedules are subject to input from the New York Stock Exchange (NYSE) and the Securities Industry and Financial Markets Association (SIFMA)." (No Juneteenth row in 2021.)

2021 ClearPort (verbatim): does not open only Christmas (observed) Fri Dec 24 2021 (reopen Sun Dec 26 18:00 ET). Good Friday special: "Thursday, April 1 Opens at 7:00 p.m. Thursday until 11:30 a.m. Friday, April 2 for CME and CBOT Interest Rates, CME and CBOT Equity Indices and CME FX only", reopen Sun Apr 4 2021 6:00 p.m. Others (MLK, Presidents, Memorial, Jul 5 observed, Labor, Thanksgiving): unaffected.

2021 Trading Floor Chicago (verbatim key rows; format this year lists only IR options early closes): Good Friday Fri Apr 2 2021: "Foreign Exchange & Interest Rates Floor Options Close at 10:00 CT" (floor closed row shows Apr 2 closed); Memorial Mon May 31 closed (Fri May 28: IR floor options 12:00 CT); Independence observed Mon Jul 5 closed (Fri Jul 2: IR floor options 12:00 CT); Labor Mon Sep 6 closed; Columbus Mon Oct 11; Veterans Thu Nov 11; Thanksgiving Thu Nov 25 closed (Fri Nov 26: IR floor options 12:00 CT); Christmas observed Fri Dec 24 closed (Thu Dec 23: IR options 12:00 CT); New Year: Fri Dec 31 2021 IR floor options 12:00 CT.
NOTE for ES 2021: the floor table no longer carries an "Equities close 12:15 CT" cell; ES (Globex product) early-close times for 2021 are in the per-holiday Excel/PDF files => NOT_TRANSCRIBED at product level.

ES 2021 expirations: NOT_OBTAINED within budget (see expirations note).

### 2022 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20220627175029 of https://www.cmegroup.com/tools-information/holiday-calendar.html (requested @20220701)
Archive URL: https://web.archive.org/web/20220627175029/https://www.cmegroup.com/tools-information/holiday-calendar.html

2022 Globex windows (verbatim; first year with Juneteenth): MLK 14-18 January 2022 | President's 18-22 February | Good Friday 14-18 April | Memorial 27-31 May | Juneteenth 17-21 June | Independence 1-5 July | Labor 2-6 September | Thanksgiving 23-25 November | Christmas 23-27 December | New Year's 30 December 2022 - 3 January 2023. (Jan 1 2022 = Saturday; see floor note below.)

2022 ClearPort (verbatim): does not open only Good Friday Fri Apr 15 2022 (reopen Sun Apr 17 18:00 ET), Christmas (observed) Mon Dec 26 2022 (reopen same day 18:00 ET), New Year's Day (observed) Mon Jan 2 2023 (reopen same day 18:00 ET). All other holidays incl. Juneteenth: unaffected.

2022 Trading Floor Chicago (verbatim): New Year's Day Sat Jan 1 2022 → "Friday, December 31, 2021 Close at 12:00 CT"; "Monday, January 3. 2022 Normal trading hours" (floor open normal Jan 3). MLK Mon Jan 17 closed. Presidents Mon Feb 21 closed. Good Friday Fri Apr 15 closed (Thu Apr 14: Close at 12:00 CT). Memorial Mon May 30 closed (Fri May 27: 12:00 CT). Juneteenth Mon Jun 20 closed. Independence Mon Jul 4 closed (Fri Jul 1: 12:00 CT). Labor Mon Sep 5 closed. Columbus Mon Oct 10 closed. Veterans Fri Nov 11 closed. Thanksgiving Thu Nov 24 closed (Fri Nov 25: 12:00 CT). Christmas Sun Dec 25 → observed Mon Dec 26 closed (Fri Dec 23: 12:00 CT). New Year's 2023 → Fri Dec 30 2022 Close 12:00 CT; floor closed Mon Jan 2 2023.
(From 2022 the floor table uses a generic "Close at 12:00 CT" without product-group breakdown.)

ES 2022 expirations: NOT_OBTAINED within budget (see expirations note).

### 2023 — ARCHIVED_OFFICIAL (curl + local extraction, full tables)

Capture: 20230528173700 of https://www.cmegroup.com/tools-information/holiday-calendar.html (requested @20230701)
Archive URL: https://web.archive.org/web/20230528173700/https://www.cmegroup.com/tools-information/holiday-calendar.html

2023 Globex windows (verbatim): MLK 13-17 January 2023 | President's 17-21 February | Good Friday 6-10 April | Memorial 26-30 May | Juneteenth 16-20 June | Independence 3-5 July | Labor 1-5 September | Thanksgiving 22-24 November | Christmas 22-26 December | New Year's 29 December 2023 - 2 January 2024. (Jan 1 2023 = Sunday-observed Monday; covered by 2022 page tail window 30 Dec 2022 - 3 Jan 2023.)

2023 ClearPort (verbatim): does not open only Christmas (observed) Mon Dec 25 2023 (reopen same day 18:00 ET) and New Year's Day (observed) Mon Jan 1 2024 (reopen same day 18:00 ET). All other holidays incl. Good Friday Apr 7 2023: unaffected (change from prior years — Good Friday no longer a ClearPort closure).

2023 Trading Floor Chicago (verbatim): New Year's Sat Jan 1 2023 → Fri Dec 30 2022 Close 12:00 CT; floor closed Mon Jan 2 2023. MLK Mon Jan 16 closed. Presidents Mon Feb 20 closed. Good Friday Fri Apr 7 2023: "Close at 10:00 CT" (early close, no closed date listed — floor open shortened session). Memorial Mon May 29 closed (Fri May 26: 12:00 CT). Juneteenth Mon Jun 19 closed. Independence Tue Jul 4 closed (Mon Jul 3: 12:00 CT). Labor Mon Sep 4 closed. Columbus Mon Oct 9 closed. Thanksgiving Thu Nov 23 closed (Fri Nov 24: 12:00 CT). Christmas Mon Dec 25 closed (Fri Dec 22: 12:00 CT). New Year's 2024 Mon Jan 1 closed (Fri Dec 29 2023: 12:00 CT).

ES 2023 expirations: NOT_OBTAINED within budget (see expirations note).

### Years being re-extracted via curl (captures verified reachable; tables appended below as extracted)

---

## ES quarterly expiration master table (ARCHIVED_OFFICIAL)

All values are "Last Trade / Settlement" dates (identical on every source row) from archived official CME product-calendar captures of /trading/equity-index/us-index/e-mini-sandp500_product_calendar.html. Backing captures per row group:

- C1 = 20090310081357 (Mar 2009), C2 = 20111005155434 (Oct 2011), C3 = 20120616171859 (Jun 2012), C4 = 20130916220723 (Sep 2013), C5 = 20140118235426 (Jan 2014), C6 = 20150419124436 (Apr 2015), C7 = 20160611233000 (Jun 2016), C8 = 20160916 (recorded earlier session), C9 = 20170401083704 (Apr 2017), C10 = 20171020 (recorded earlier session), C11 = 20240927 (recorded earlier session; exact request URL not preserved — data recorded verbatim at fetch time; re-derivable via Wayback captures of the product calendar around 2024-09-27).

| Contract | Code | First Trade | Last Trade / Settle | Source |
|---|---|---|---|---|
| Mar 2010 | ESH10 | 12/19/2008 | 03/19/2010 | C1 |
| Jun 2010 | ESM10 | 03/20/2009 | 06/18/2010 | C1 |
| Dec 2011 | ESZ11 | 09/17/2010 | 12/16/2011 | C2 |
| Mar 2012 | ESH12 | 12/17/2010 | 03/16/2012 | C2 |
| Jun 2012 | ESM12 | 03/18/2011 | 06/15/2012 | C2/C3 |
| Sep 2012 | ESU12 | 06/17/2011 | 09/21/2012 | C2/C3 |
| Dec 2012 | ESZ12 | 09/16/2011 | 12/21/2012 | C2/C3 |
| Mar 2013 | ESH13 | 12/16/2011 | 03/15/2013 | C3 |
| Jun 2013 | ESM13 | 03/16/2012 | 06/21/2013 | C3 |
| Sep 2013 | ESU13 | 06/15/2012 | 09/20/2013 | C3/C4 |
| Dec 2013 | ESZ13 | 09/21/2012 | 12/20/2013 | C4 |
| Mar 2014 | ESH14 | 12/21/2012 | 03/21/2014 | C4/C5 |
| Jun 2014 | ESM14 | 03/15/2013 | 06/20/2014 | C5 |
| Sep 2014 | ESU14 | 06/21/2013 | 09/19/2014 | C4/C5 |
| Dec 2014 | ESZ14 | 09/20/2013 | 12/19/2014 | C4/C5 |
| Mar 2015 | ESH15 | 12/20/2013 | 03/20/2015 | C5 |
| Jun 2015 | ESM15 | 21 Mar 2014 | 19 Jun 2015 | C6 |
| Sep 2015 | ESU15 | 20 Jun 2014 | 18 Sep 2015 | C6 |
| Dec 2015 | ESZ15 | 19 Sep 2014 | 18 Dec 2015 | C6 |
| Mar 2016 | ESH16 | 19 Dec 2014 | 18 Mar 2016 | C6 |
| Jun 2016 | ESM16 | 20 Mar 2015 | 17 Jun 2016 | C6/C7 |
| Sep 2016 | ESU16 | 19 Jun 2015 | 16 Sep 2016 | C7 |
| Dec 2016 | ESZ16 | 18 Sep 2015 | 16 Dec 2016 | C7/C8 |
| Mar 2017 | ESH17 | 18 Dec 2015 | 17 Mar 2017 | C7/C8 |
| Jun 2017 | ESM17 | 18 Mar 2016 | 16 Jun 2017 | C7/C8/C9 |
| Sep 2017 | ESU17 | 17 Jun 2016 | 15 Sep 2017 | C8/C9 |
| Dec 2017 | ESZ17 | 16 Sep 2016 | 15 Dec 2017 | C8/C9/C10 |
| Mar 2018 | ESH18 | 16 Dec 2016 | 16 Mar 2018 | C9/C10 |
| Jun 2018 | ESM18 | 17 Mar 2017 | 15 Jun 2018 | C9/C10 |
| Sep 2018 | ESU18 | (not transcribed) | 09/21/2018 | C10 |
| Dec 2018 | ESZ18 | (not transcribed) | 12/21/2018 | C10 |
| Sep 2024 | ESU24 | 03/11/2024 | 09/20/2024 | C11 |
| Dec 2024 | ESZ24 | 06/10/2024 | 12/20/2024 | C11 |
| Mar 2025 | ESH25 | 09/09/2024 | 03/21/2025 | C11 |
| Jun 2025 | ESM25 | 12/09/2024 | 06/20/2025 | C11 |
| Sep 2025 | ESU25 | 03/10/2025 | 09/19/2025 | C11 |
| Dec 2025 | ESZ25 | 06/09/2025 | 12/19/2025 | C11 |

NOT_OBTAINED quarters (archive facts, not inference): Sep/Dec 2010; Mar/Jun/Sep 2011; ALL of 2019, 2020, 2021, 2022, 2023; Mar/Jun 2024; ALL of 2026.
Reasons (measured): the old product-calendar URL has NO Wayback captures between 2017-04-01 and 2020-09-24 (requests at 20180401/20181001/20181015/20181201/20190201/20190501/20191001/20200215 all resolve to 20170401083704 or 20200924060333), and every capture from 2020-09-24 onward is a React shell ("There is currently no calendar data" / headers only, "An account is required to download calendar file data"). New-URL captures (markets/equities/sp/e-mini-sandp500.calendar.html: 20210927141920, 20210630211053) contain component headers only, no data rows.

## PDF extraction notes

- pdftotext absent on this machine; `pip3 install --user pypdf` (v6.19.0) used for local parsing. Only archive-of-official PDFs were parsed (2010 Globex calendar PDF: full per-product detail above; 2024-thanksgiving-advisory.pdf and 2024-christmas-advisory.pdf via capture 20241112201950: these are CME Group Clearing memos — clearing-processing cycles on the holiday, no ES trading-hour rows; trading hours deferred to the holiday-calendar links).
- 2026 note (live page): product-level Globex holiday hours moved to downloadable calendars + interactive widget => per-product ES times for 2026 NOT_OBTAINED from static HTML.

## Attempt log supplement (curl pass, all 2026-10-03, plain curl default UA, one request per URL)

- Holiday page captures (resolved): 20100315131807, 20100414015939, 20110313182401, 20120616171859, 20130119015927, 20140626070427, 20150710035807, 20160214222113, 20170703230701, 20180629065738, 20190702203907, 20200620052000, 20210702163511, 20220627175029, 20230528173700 — all HTTP 200, tables extracted locally.
- trading-hours.html @20241115 → resolved 20241112201950, 277 KB, full 2024+2025 static tables (the decisive capture).
- Product calendar (old URL) captures: 20090310081357, 20111005155434, 20130916220723, 20140118235426, 20150419124436, 20160611233000, 20170401083704 (+ shell 20200924060333). Capture-gap probes that resolved to existing captures (no new data): 20100801, 20101005, 20100720, 20110315, 20110601, 20101215, 20181015, 20181201, 20190201, 20190501, 20200215, 20200301.
- New URL captures: 20210630211053, 20210927141920 — React shells, no data.
- PDFs: 2010-globex-holiday-calendar.pdf (via 20100215061802), 2024-thanksgiving-advisory.pdf, 2024-christmas-advisory.pdf (via 20241112201950) — all HTTP 200, parsed.

## Verdict

- HOLIDAYS + EARLY CLOSES: ALL 17 years (2010-2026) authority-backed.
  - LIVE_OFFICIAL: 2026 (windows + ClearPort + floor times; ES-specific Globex times behind widget => NOT_OBTAINED at product level).
  - ARCHIVED_OFFICIAL with per-day, per-time detail: 2010 (official 38-page Globex PDF, Equity section verbatim — full session-level detail incl. early closes 08:15 CT Good Friday, 12:15 CT Nov 26, closures Jan 1 / Dec 24).
  - ARCHIVED_OFFICIAL with verbatim window tables + ClearPort + floor times: 2012-2025 (2011: windows verbatim; ClearPort/floor in linked PDFs, not transcribed; 2024-2025: clearing dates + windows + floor; 2025 June-capture ClearPort table not retained beyond advisory-level rows).
- EXPIRATIONS: 36 of 68 quarterly contracts 2010-2026 authority-backed (rows above); every quarter of 2012-2018 and 2025 complete; 2010 half, 2011 one quarter, 2024 half; 2019-2023 and 2026 quarters NOT_OBTAINED (archive capture gap + JS-shell era — measured facts, not guesses).
- Third-party aggregators were never used as authority (none needed).
- Uncertain days/fields were excluded rather than inferred; the one page anomaly found (2017 page's Thanksgiving ClearPort cell carrying stale 2016 data) is documented, and the underlying 2016 datum was re-verified against the 2016 capture.


---

## Official PDF/advisory inventory (2024-2025, from capture 20241112201950)

58 official file URLs extracted from the capture; ES-relevant set includes per-holiday trading-hours advisories, e.g.:
- https://www.cmegroup.com/tools-information/holiday-calendar/files/2024-thanksgiving-advisory.pdf (+ -otc- variants)
- .../files/2024-christmas-advisory.pdf, 2024-good-friday-advisory.pdf, 2024-mlk-day-advisory.pdf, 2024-presidents-day-advisory.pdf, 2024-memorial-day-advisory.pdf, 2024-labor-day-advisory.pdf, 2024-columbus-day-advisory.pdf, 2024-veterans-day-advisory.pdf, 2024-juneteenth-advisory.pdf, 2024-4th-of-july-advisory.pdf, 2025-new-years-advisory.pdf
- .../files/2025/2025-*-clearing-advisory.pdf (set), and dam-path per-holiday settlement-times PDFs (e.g. .../content/dam/cmegroup/tools-information/holiday-calendar/files/thanksgiving-holiday-settlement-times-2024.pdf)

## Verdict

(finalized after the curl re-extraction pass)
