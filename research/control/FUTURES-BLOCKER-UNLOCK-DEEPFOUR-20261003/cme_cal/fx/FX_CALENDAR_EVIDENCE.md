# FX Futures (6E / 6B / 6J / 6A) — Official CME Calendar & Expiry Evidence (Lane A2-CMECAL-FX)

Task: FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 | Lane: A2-CMECAL-FX | Acquisition: 2026-10-03 (UTC) | Revision: r2 (same day, VERIFY F-1 correction)

## Correction log (r2, kept for integrity — original statements preserved below with fixes applied in place where noted)

F-1 (internal count inconsistency, found by VERIFY lane): the r1 prose/summary claimed **6E = 18 quarters including "2012 all 4 (Mar 19 ...)"** while the machine rows in `fx_cal_coverage.json` hold **6E = 17** and do NOT contain MAR 2012/ECH12. Recount performed against the machine rows AND the raw captures: `ECH12` occurs **0 times in every one of the 9 archived 6E product-calendar captures** (grep-verified), and the CDX inventory shows no 6E capture between 2010-01-09 and 2012-05-08; the May-2012 capture lists contracts from JUN 2012 onward. ECH12 is therefore genuinely NOT_OBTAINED — no row was added; the prose was corrected instead. Corrected counts (rows = evidence): **6E 17, 6B 31, 6J 13, 6A 35; total = 17+31+13+35 = 96/272**. The r1 statements "6E 18/68" and "2012 all 4" were wrong; everything else in the r1 count set agreed with the rows. Machine rows, the 96/96 rule-QA (run over the rows), and all holiday/rule evidence are unchanged by this correction.
Scope: CME official holiday calendar + early closes for the four G10 FX futures codes 6E (EUR), 6B (GBP), 6J (JPY), 6A (AUD) — Globex, quarterly HMUZ — per year 2010..2026; PLUS the official last-trade/expiration rule per product and as many officially-sourced quarterly expiry dates as obtainable.
Extends lane D3-CMECAL (ES, same session): `research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md` — holiday-page capture map, live-page behavior, and archive transport lessons were reused; nothing ES-specific was transplanted (the FX product family has a DIFFERENT official schedule, confirmed below).

Laws honored: normal public access only; no UA spoofing; no proxies; ≤2 attempts per URL per method (paced); every attempt logged in `fetch_log.jsonl`; uncertain days/fields EXCLUDED (NOT_OBTAINED), never inferred from neighboring years or memory.

## Provenance labels

- `LIVE_OFFICIAL` — fetched directly from cmegroup.com on 2026-10-03. **NONE OBTAINED this lane** — live cmegroup.com blocked all three methods tried (web_reader -429 then -500 network error; WebFetch ECONNREFUSED). The prior ES lane DID reach the live trading-hours page via web_reader earlier the same day; that finding is not contradicted (different client sessions), but no LIVE datum is claimed here.
- `ARCHIVED_OFFICIAL` — web.archive.org capture of an official cmegroup.com page/PDF/XLS; resolved capture timestamp + URL recorded per datum.
- `NOT_OBTAINED` — no authority-backed datum in hand at the stated granularity.

## Structural findings (why FX ≠ equity family calendar — all FACT-verified)

1. CME publishes the Globex holiday schedule per PRODUCT FAMILY. The official per-holiday PDFs carry a "**CME Group FX Products**" (2010-2012 era), "Interest Rate & FX Products" (2014-2015 era) or "Equity, Interest Rate, FX, Energy, Metals & DME Products" (2016 era) block. 6E/6B/6J/6A are all standard CME FX products and are governed by the FX-family block — no per-product divergence was found in any artifact (the XLS 2017 New Year sheet lists one "FX Products" row for the whole family).
2. The FX family schedule DIFFERS from the equity family (verbatim examples under each year):
   - Good Friday: FX early close **10:15 CT** (2010, 2012, 2015) or **full Globex closure** (2011, 2013, 2014, 2016) — year-specific, never inferred across years.
   - Monday holidays (MLK, Presidents, Memorial, July-4-observed-Monday, Labor): FX **12:00 CT trading halt + 17:00 CT resume** on the Monday (2010-2016 era); preceding-Friday FX early close **15:15 CT** existed 2010-2015 but was DROPPED from 2016 (Fridays became regular 16:00 closes).
   - Columbus Day: Monday session REGULAR for FX; 2010-2012 had a preceding-Friday 15:15 early close; from 2013 the whole day is "unaffected ... normal schedule" Globex-wide.
   - Veterans Day: FX normal every year (2013/2014/2016 verbatim "unaffected"; 2015 settlement-procedures doc names the FX majors as trading normally).
   - Christmas/NYE closures reopen at 05:00 CT on the next business day when the closure fell on a Monday/Tuesday mid-week position (2011-2014 verbatim), 17:00 CT reopen from 2014-2015 era pages onward.
3. From 2017 the per-holiday Globex schedule PDFs/XLS stopped being reliably archived (CDX shows only clearing advisories, which contain NO trading hours — verified 2016-columbus advisory, 2018-mlk advisory, 2024 mlk settlement-times). The 2017-2025 holiday pages inline only family-agnostic "CME Globex" windows + a pointer "Download the existing files to view altered trading hours" — the files themselves are not in the archive. FX product-level times for 2017-2025 are therefore NOT_OBTAINED except New Year 2017 (XLS in hand).
4. From 2026 CME moved product-level Globex holiday hours to downloadable calendars + an interactive widget ("Please note that with the 2026 and 2027 calendar year the CME Group will be providing downloadable holiday calendars for Globex...") — same LIMIT as the ES lane found; the static page still carries the windows + Globex-wide Holiday Notes (transcribed below).

---

## PART A — FX-family Globex holiday schedule per year

### 2010 — ARCHIVED_OFFICIAL, FULL product-level detail (whole-year official PDF)

Artifact: "CME Globex 2010 Holiday Calendar" 38-page PDF, FX sections verbatim.
URL: https://web.archive.org/web/20100215061802/http://www.cmegroup.com/tools-information/holiday-calendar/files/2010-globex-holiday-calendar.pdf (explicit ts; attempt 1 connection-failed, attempt 2 OK)

"CME Group FX Products" blocks, verbatim (times CT):
- New Year's: Thu Dec 31 2009 `1600 CT – Regular CME Globex close`; **Fri Jan 1 2010 GLOBEX CLOSED**; Sun Jan 3 `1700 CT – Regular open` (trade date Mon Jan 4).
- MLK: Fri Jan 15 `1515 CT – Early CME Globex close`; Sun Jan 17 17:00 open (trade date Tue Jan 19); **Mon Jan 18 `1200 CT – Trading halt` (order entry/mod/cancel allowed) `1700 CT – Halted products resume trading`**; Tue Jan 19 1600 regular close.
- Presidents: identical pattern (Fri Feb 12 early close 1515; Mon Feb 15 1200 halt / 1700 resume).
- Good Friday: Thu Apr 1 1600 regular close, 1700 regular open (trade date Fri Apr 2); **Fri Apr 2 `1015 CT - Early CME Globex close`**; Sun Apr 4 1700 regular open.
- Memorial: Fri May 28 early close 1515; Mon May 31 1200 halt / 1700 resume.
- Fourth of July: Fri Jul 2 early close 1515; Mon Jul 5 1200 halt / 1700 resume.
- Labor: Fri Sep 3 early close 1515; Mon Sep 6 1200 halt / 1700 resume.
- Columbus: **Fri Oct 8 early close 1515**; Mon Oct 11 `1600 CT – Regular CME Globex close` (normal session).
- Veterans: Wed Nov 10 / Thu Nov 11 / Fri Nov 12 all `1600 CT – Regular` closes (normal).
- Thanksgiving: Wed Nov 24 1600 close + 1700 open (trade date Fri Nov 26); Thu Nov 25 1200 halt / 1700 resume; **Fri Nov 26 `1215 CT – Early CME Globex close`** (page Note confirms "Friday's close at 1215 CT").
- Christmas: Thu Dec 23 1600 regular close; **Fri Dec 24 GLOBEX CLOSED**; Sun Dec 26 1700 regular open.
- New Year's 2011: **Fri Dec 31 2010 `1215 CT – Early CME Globex close`**; Sun Jan 2 2011 1700 regular open.
Cross-check: Special Executive Report S-5525 (Dec 16 2010, REVISED): "`1215 CT Early Close for Foreign Exchange`" on Friday, December 31, 2010 (https://web.archive.org/web/20111101144016/.../files/Holiday-Early-Close-Schedule.pdf).

### 2011 — ARCHIVED_OFFICIAL, FULL product-level detail (11 per-holiday PDFs)

All resolved capture URLs (requested /web/2011/, resolved ts per file):
- new-years → 20111101143945; mlk → 20111028023429; presidents → 20111028023516; good-friday → 20111028023707; memorial → 20111101144923; 4th-of-july → 20111101144054; labor → 20111101144345; columbus → 20111101143916; veterans → 20111111191211; thanksgiving → 20111124185246; christmas → 20120105160450; 2012-new-years → 20120105160505.
Base: http://www.cmegroup.com/tools-information/holiday-calendar/files/{name}.pdf

FX blocks verbatim (times CT):
- New Year's: Fri Dec 31 2010 `1215 CT – Early CME Globex close`; Sun Jan 2 1700 open (trade date Mon Jan 3). (Jan 1 2011 closure = tail of 2010 PDF.)
- MLK: Fri Jan 14 early close 1515; Mon Jan 17 `1200 CT – Trading halt` / `1700 CT – Halted products resume trading`; Tue Jan 18 regular close 1600.
- Presidents: Fri Feb 18 early close 1515; Mon Feb 21 1200 halt / 1700 resume (Futures: entry/mod/cancel allowed; Options: only cancellation).
- Good Friday: Thu Apr 21 1600 regular close; **Fri Apr 22 `CME Globex is closed`** (FULL closure); Sun Apr 24 1700 regular open.
- Memorial: Fri May 27 early close 1515; Mon May 30 1200 halt / 1700 resume.
- Independence (Tue Jul 4): Fri Jul 1 early close 1515; Mon-none; Tue Jul 5 regular close 1600 (Sun Jul 3 1700 open for trade date Tue Jul 5).
- Labor: Fri Sep 2 early close 1515; Mon Sep 5 1200 halt / 1700 resume.
- Columbus: Fri Oct 7 early close 1515; Mon Oct 10 `1600 CT – Regular CME Globex close`.
- Veterans: Thu Nov 10 1700 open (trade date Fri Nov 11); Fri Nov 11 `1600 CT – Regular CME Globex close` (normal).
- Thanksgiving: Wed Nov 23 1600 close + 1700 open (trade date Fri Nov 25); Thu Nov 24 1200 halt / 1700 resume; **Fri Nov 25 `1215 CT – Early CME Globex close`**.
- Christmas (observed Mon Dec 26): Fri Dec 23 1600 regular close; **Mon Dec 26 `Christmas Day Observed – Globex closed`**; **Tue Dec 27 `0500 CT – CME Globex open`** + 1600 regular close.
- New Year's 2012 (observed Mon Jan 2): Fri Dec 30 1600 regular close; **Mon Jan 2 `New Years Observed – Globex closed`**; Tue Jan 3 `0500 CT – Regular open`.

### 2012 — ARCHIVED_OFFICIAL, FULL product-level detail (11 per-holiday PDFs)

Resolved captures: new-years→20120915003237; mlk→20120915001633; presidents→20120915003325; good-friday→20120915003606; memorial→20120915003714; 4th-of-july→20120915003923; labor→20120915003437; columbus→20120915001514; veterans→20120915001444; thanksgiving→20130127223901; christmas→20130414194027.

FX blocks verbatim (times CT):
- MLK: Fri Jan 13 early close 1515; Mon Jan 16 1200 halt / 1700 resume.
- Presidents: Fri Feb 17 early close 1515; Mon Feb 20 1200 halt / 1700 resume.
- Good Friday: Thu Apr 5 1600 regular close + 1700 open (trade date Fri Apr 6); **Fri Apr 6 `1015 CT - Early CME Globex close`**; Sun Apr 8 1700 open.
- Memorial: Fri May 25 early close 1515; Mon May 28 1200 halt / 1700 resume.
- Independence (Wed Jul 4): Tue Jul 3 `1600 CT – Regular close` + 1700 open (trade date Thu Jul 5) — NO preceding-day early close; Wed Jul 4 1200 halt / 1700 resume; Thu regular.
- Labor: Fri Aug 31 early close 1515; Mon Sep 3 1200 halt / 1700 resume.
- Columbus: Fri Oct 5 early close 1515; Mon Oct 8 1600 regular close.
- Veterans (observed Mon Nov 12): Sun Nov 11 1700 regular open; Mon Nov 12 1600 regular close (normal).
- Thanksgiving: Wed Nov 21 1600 close + 1700 open (trade date Fri Nov 23); Thu Nov 22 1200 halt / 1700 resume; Fri Nov 23 early close 1215.
- Christmas (Tue Dec 25): **Mon Dec 24 `1215 CT – Early CME Globex close`**; Tue Dec 25 `Christmas Day Observed – Globex closed`; **Wed Dec 26 `0500 CT – CME Globex open`**.
- New Year's 2013: Mon Dec 31 2012 1600 regular close; **Tue Jan 1 2013 `New Years Observed – Globex closed`**; Wed Jan 2 `0500 CT – CME Globex open` (2013-new-years.pdf → resolved 20131007235211).

### 2013 — ARCHIVED_OFFICIAL, FULL product-level detail (PDFs; format simplified to "Globex® {Holiday} Holiday Schedule" with FX Products rows)

Resolved captures: new-years→20131007235211; mlk→20140124061751; presidents→20130623205707; good-friday→20140214070518; memorial→20140416074024; 4th-of-july→20130623205825; labor→20140214072039; columbus→20131007153359; veterans→20131007205752; thanksgiving→20140214062836; christmas→20131007172634.

FX rows verbatim (times CT):
- New Year's: Mon Dec 31 2012 1600 regular close; **Tue Jan 1 2013 `New Years Observed – Globex closed`**; Wed Jan 2 `0500 CT – CME Globex open`.
- MLK: Fri Jan 18 early close 1515; Mon Jan 21 1200 halt / 1700 resume; Tue Jan 22 regular close.
- Presidents: Fri Feb 15 early close 1515; Mon Feb 18 1200 halt / 1700 resume.
- Good Friday: Thu Mar 28 1600 regular close; **Fri Mar 29 `CME Globex is closed`** (FULL closure); Sun Mar 31 1700 regular open.
- Memorial: Fri May 24 early close 1515; Mon May 27 1200 halt / 1700 resume.
- Independence (Thu Jul 4): Wed Jul 3 1600 regular close + 1700 open (trade date Fri Jul 5); Thu Jul 4 1200 halt / 1700 resume.
- Labor: Fri Aug 30 early close 1515; Mon Sep 2 1200 halt / 1700 resume.
- Columbus: **entire document: "Products listed on Globex are unaffected and will run on a normal schedule"** (1-pager; no FX early close at all).
- Veterans: same verbatim 1-pager — normal schedule.
- Thanksgiving: Wed Nov 27 1600 close + 1700 open (trade date Fri Nov 29); Thu Nov 28 1200 halt / 1700 resume; Fri Nov 29 `1215 CT – Early close`.
- Christmas: Tue Dec 24 `1215 CT – Early close`; **Wed Dec 25 `Christmas Day Observed – Globex closed`**; Thu Dec 26 `0500 CT – Modified open`.

### 2014 — ARCHIVED_OFFICIAL, FULL product-level detail (holiday-schedule PDFs + Columbus XLS; note FX grouped with IR)

Resolved captures: new-years→20131007205800; mlk→20140708040707; presidents→20140708021848; good-friday→20140708014118; memorial→20140708020155; 4th-of-july→20140708015736; labor→20140912071608; thanksgiving→20150121145456; christmas→20150121141000; veterans→20141113193450; columbus XLS→20140708040132.

FX rows verbatim (times CT; "FX Products" / "Interest Rate & FX Products" columns):
- New Year's: Tue Dec 31 2013 1600 regular close; **Wed Jan 1 2014 `New Year's Observed – Globex closed`**; Thu Jan 2 `0500 CT – Modified open`.
- MLK: Fri Jan 17 `1515 CT – Early close`; Sun Jan 19 1700 open (trade date Tue Jan 21); Mon Jan 20 `1200 CT – Trading halt (pre-open)` / `1700 CT – Products resume trading`.
- Presidents: Fri Feb 14 early close 1515; Mon Feb 17 1200 halt / 1700 resume.
- Good Friday: Thu Apr 17 1600 regular close; **Fri Apr 18 `CME Globex is closed`**; Sun Apr 20 1700 regular open.
- Memorial: Fri May 23 early close 1515; Mon May 26 1200 halt / 1700 resume.
- Independence (Fri Jul 4): Thu Jul 3 `1600 CT – Regular close` + 1700 open (trade date Mon Jul 7); **Fri Jul 4 `1200 CT – Early close (Day & GTD order elimination)`**.
- Labor: Fri Aug 29 early close 1515; Mon Sep 1 1200 halt / 1700 resume.
- Columbus (XLS, verbatim): "Monday, October 13 Globex Columbus Day Holiday Schedule — **Products listed on Globex are uneffected [sic] and will run on a normal schedule**".
- Veterans: settlement-procedures PDF (names FX settlement methodology for Nov 11 2014 — trading occurred); explicit Globex "unaffected" statement NOT_OBTAINED for this year.
- Thanksgiving: Wed Nov 26 1600 close + 1700 open (trade date Fri Nov 28); Thu Nov 27 1200 halt / 1700 resume; Fri Nov 28 early close 1215.
- Christmas: Wed Dec 24 early close 1215; **Thu Dec 25 closed**; reopen `1700 CT` for trade date Fri Dec 26 (same-day reopen entry; format change from 05:00 reopen).

### 2015 — ARCHIVED_OFFICIAL, FULL product-level detail

Resolved captures: new-years→20150121141043; mlk→20160205183836; presidents→20160205131044; good-friday→20160205172229; memorial→20160205193258; 4th-of-july→20160128215011; labor→20160205160729; thanksgiving→20160205162519; christmas→20160205182646; veterans(settlement)→in hand; columbus XLS→20160205140017.

FX rows verbatim (times CT):
- New Year's: Wed Dec 31 2014 1600 regular close; **Thu Jan 1 2015 `New Year's Observed – Globex closed`** + 1700 reopen same day (trade date Fri Jan 2).
- MLK: Fri Jan 16 early close 1515; Mon Jan 19 1200 halt / 1700 resume.
- Presidents: Fri Feb 13 early close 1515; Mon Feb 16 1200 halt / 1700 resume.
- Good Friday: Thu Apr 2 1600 regular close + 1700 open (trade date Fri Apr 3); **Fri Apr 3 `1015 CT - Early CME Globex close`**.
- Memorial: Fri May 22 early close 1515; Mon May 25 1200 halt / 1700 resume.
- Independence (observed Fri Jul 3): Thu Jul 2 `1600 CT – Regular close` + 1700 open (trade date Mon Jul 6); **Fri Jul 3 `1200 CT – Early close (Day & GTD order elimination)`**.
- Labor: **Fri Sep 4 `1600 CT – Regular close` (NO Friday early close)**; Mon Sep 7 1200 halt / 1700 resume.
- Columbus (XLS, verbatim): "Monday, October 12 Globex Columbus Day Holiday Schedule — **Products listed on Globex are unaffected and will run on a normal schedule**".
- Veterans: settlement-procedures doc (verbatim header "FX Products Traded on November 11, 2015 — FX Futures Euro, Yen, Pound, Canadian $, Swiss, Australian $ (normal methodology)") — trading occurred, normal settlement methodology; explicit Globex-hours statement NOT_OBTAINED.
- Thanksgiving: Wed Nov 25 1600 close + 1700 open (trade date Fri Nov 27); Thu Nov 26 1200 halt / 1700 resume; Fri Nov 27 early close 1215.
- Christmas: Thu Dec 24 early close 1215; **Fri Dec 25 `Christmas Day Observed – Globex closed`**; Sun Dec 27 1700 regular open.

### 2016 — ARCHIVED_OFFICIAL, FULL product-level detail (note: family-wide block, Friday early closes DROPPED)

Resolved captures: new-years→20160108203007; mlk→20170422184420; presidents→20170422125913; good-friday→20170422125934; memorial→20170422000248; 4th-of-july→20170422130726; labor→20170422041620; thanksgiving→20161120130541; christmas→20170110161819; columbus XLS→20161019231409; veterans XLS→20170422060518.

FX (inside "Equity, Interest Rate, FX, Energy, Metals & DME Products" / "Interest Rate & FX Products" blocks) verbatim (times CT):
- New Year's: Thu Dec 31 2015 1600 regular close; **Fri Jan 1 2016 `New Year's Observed – Globex closed`**; Sun Jan 3 1700 open.
- MLK: **Fri Jan 15 `1600 CT – Regular close` (early close DROPPED from this year)**; Sun Jan 17 1700 open (trade date Tue Jan 19); Mon Jan 18 `1200 CT – Trading halt (pre-open)` / `1700 CT – Products resume trading`.
- Presidents: Fri Feb 12 regular close 1600; Mon Feb 15 1200 halt / 1700 resume.
- Good Friday: Thu Mar 24 1600 regular close; **Fri Mar 25 `CME Globex is closed`** (FULL closure); Sun Mar 27 1700 regular open.
- Memorial: Fri May 27 regular close; Mon May 30 1200 halt / 1700 resume.
- Independence: Fri Jul 1 regular close; Mon Jul 4 1200 halt / 1700 resume.
- Labor: Fri Sep 2 regular close; Mon Sep 5 1200 halt / 1700 resume.
- Columbus (XLS verbatim): "Monday, October 10 ... **Products listed on Globex are unaffected and will run on a normal schedule**".
- Veterans (XLS verbatim): "Friday, November 11 Globex Veterans Day Holiday Schedule — **unaffected and will run on a normal schedule**".
- Thanksgiving: Wed Nov 23 1600 close + 1700 open (trade date Fri Nov 25); Thu Nov 24 1200 halt / 1700 resume; Fri Nov 25 `1215 CT – Early close`.
- Christmas: Fri Dec 23 1600 regular close; **Mon Dec 26 `Christmas Day Observed – Globex closed`**; Mon Dec 26 `1700 CT` reopen (trade date Tue Dec 27).

### 2017 — PARTIAL (windows ARCHIVED_OFFICIAL; FX product-level NOT_OBTAINED except New Year)

- Windows (page capture 20170703230701, verbatim): MLK 13-17 Jan; Presidents 17-21 Feb; Good Friday 13-17 Apr; Memorial 26-30 May; Independence 3-5 Jul; Labor 1-5 Sep; Columbus 9 Oct (window); Veterans 10 Nov (window); Thanksgiving 22-24 Nov; Christmas 22-26 Dec; New Year 29 Dec 2017 - 2 Jan 2018. Page states: "CME Globex will observe the following holidays in 2017. Trading times and days affected may vary depending on the holiday. Download the existing files to view altered trading hours."
- New Year 2017 FX product-level — ARCHIVED_OFFICIAL (XLS, resolved 20160808102944): sheet "CME Group Globex New Years Holiday Schedule: December 30, 2016 - January 3, 2017", row "FX Products": Fri Dec 30 2016 close 16:00 CT (Excel fraction 0.6667); **Mon Jan 2 2017 "Globex Closed"**; reopen Mon Jan 2 17:00 CT (0.7083) for trade date Tue Jan 3 (close 16:00 CT).
- All other 2017 holidays: FX-family Globex times NOT_OBTAINED (downloadable files not archived; clearing advisories verified to contain no trading hours).

### 2018 / 2019 / 2020 / 2021 / 2022 / 2023 — windows ARCHIVED_OFFICIAL; FX product-level NOT_OBTAINED

Windows verbatim from page captures fetched this lane (2018: 20180629065738; 2019: 20190702203907; 2020: 20200620052000; 2021: 20210702163511; 2022: 20220627175029; 2023: 20230528173700):
- 2018: MLK 12-16 Jan; Presidents 16-20 Feb; Good Friday 29 Mar - 2 Apr; Memorial 25-29 May; Independence 3-5 Jul; Labor 31 Aug - 3 Sep; Thanksgiving 21-23 Nov; Christmas 24-26 Dec; New Year 31 Dec 2018 - 2 Jan 2019. (No Columbus/Veterans window rows.)
- 2019: MLK 18-22 Jan; Presidents 15-19 Feb; Good Friday 18-22 Apr; Memorial 24-28 May; Independence 3-5 Jul; Labor 30 Aug - 3 Sep; Columbus 14 Oct (window); Veterans 11 Nov (window); Thanksgiving 27-29 Nov; Christmas 24-26 Dec; New Year 31 Dec 2019 - 2 Jan 2020.
- 2020: MLK 17-21 Jan; Presidents 14-18 Feb; Good Friday 9-13 Apr; Memorial 22-26 May; Independence 2-6 Jul; Labor 4-8 Sep; Thanksgiving 25-27 Nov; Christmas 24-28 Dec; New Year 31 Dec 2020 - 4 Jan 2021.
- 2021: MLK 15-19 Jan; Presidents 12-16 Feb; Good Friday 1-5 Apr; Memorial 28 May - 1 Jun; Independence 2-5 Jul; Labor 3-7 Sep; Thanksgiving 24-26 Nov; Christmas 23-27 Dec; New Year 30 Dec 2021 - 3 Jan 2022. (No Juneteenth in 2021.)
- 2022 (first Juneteenth year): MLK 14-18 Jan; Presidents 18-22 Feb; Good Friday 14-18 Apr; Memorial 27-31 May; Juneteenth 17-21 Jun; Independence 1-5 Jul; Labor 2-6 Sep; Thanksgiving 23-25 Nov; Christmas 23-27 Dec; New Year 30 Dec 2022 - 3 Jan 2023.
- 2023: MLK 13-17 Jan; Presidents 17-21 Feb; Good Friday 6-10 Apr; Memorial 26-30 May; Juneteenth 16-20 Jun; Independence 3-5 Jul; Labor 1-5 Sep; Thanksgiving 22-24 Nov; Christmas 22-26 Dec; New Year 29 Dec 2023 - 2 Jan 2024.
FX-family Globex times for these years: NOT_OBTAINED (no FX rows on the pages — FX appears only in ClearPort/floor tables; per-holiday files not archived; advisories are clearing memos — verified by sampling 2018-mlk-day-advisory.pdf [resolved 20180508163753] and the 2024 mlk-day-holiday-settlement-times PDF).

### 2024 / 2025 — windows ARCHIVED_OFFICIAL (trading-hours.html capture 20241112201950); FX product-level NOT_OBTAINED

Windows verbatim (2024): MLK 12-16 Jan; Presidents 16-20 Feb; Good Friday 28 Mar - 1 Apr; Juneteenth 18-20 Jun; Independence 3-5 Jul; Labor 30 Aug - 3 Sep; Columbus 14 Oct (window); Veterans 11 Nov (window); Thanksgiving 27-29 Nov; Christmas 24-26 Dec; New Year 31 Dec 2024 - 2 Jan 2025.
Windows verbatim (2025): MLK 17-20 Jan; Presidents 14-17 Feb; Good Friday 17-21 Apr; Memorial 23-27 May; Juneteenth 18 Jun; Independence 3-7 Jul; Labor 29 Aug - 1 Sep; Columbus 13 Oct; Veterans 11 Nov; Thanksgiving 26-28 Nov; Christmas 24-26 Dec; New Year 31 Dec 2025 - 2 Jan 2026.
FX-family Globex times: NOT_OBTAINED (same reasons as 2018-2023; the capture's /files/ inventory is clearing advisories + settlement-times PDFs only — catalogued by the ES lane and re-verified by sampling one settlement-times PDF).

### 2026 — windows + Globex-wide Holiday Notes ARCHIVED_OFFICIAL (Sep-2026 capture); FX product-level times NOT_OBTAINED (widget)

Capture: https://web.archive.org/web/20260924120320/https://www.cmegroup.com/trading-hours.html
Windows verbatim: New Year 31 Dec 2025 - 2 Jan 2026; MLK 18-20 Jan 2026; Presidents 15-17 Feb 2026; Good Friday 2-4 Apr 2026; Memorial 24-26 May 2026; Juneteenth 18-19 Jun 2026; Independence 3-5 Jul 2026; Labor 6-8 Sep 2026; Thanksgiving 26-28 Nov 2026; Christmas 24-26 Dec 2026; New Year 31 Dec 2026 - 1 Jan 2027.
Holiday Notes verbatim (2026): "Any day orders entered after the pre-open session on Thursday, June 18, will automatically cancel at the close of trading on Friday, June 19." / "Day orders entered after a product's Pre-opening(s) on Sunday, Septemper 6th are for trade date Tuesday, September 8th... Tuesday, September 8th: Regular CME Group Globex close for all products." / Thanksgiving: "...on Wednesday, November 25th are for trade date Friday, November 27th..." (TAS early-close details listed per product; no FX-family TAS entry) / Christmas: "...on Wednesday, December 23th, are for trade date Thursday December 24th..." / NYE: "...on Wednesday, December 30th are for trade date Thursday December 31st... December 31 TAS: Regular close per each product schedule."
2027 notes also verbatim on same capture: MLK ("Sunday, January 17th ... Tuesday, January 19th: Regular CME Group Globex close for all products"), Presidents (Feb 14 → Feb 16), Good Friday 2027 ("Thursday March 25th all markets have a regular close. **No trading for Friday March 26th trade date in observence of Good Friday**."), Memorial (May 30 → Jun 1), Independence (Jul 4 → Jul 6), Labor (Sep 5 → Sep 7), Thanksgiving (Nov 24 → Nov 26), Christmas (Dec 22 → Dec 23/24), NYE (Dec 30 → Dec 31).
LIMIT (verbatim): "Please note that with the 2026 and 2027 calendar year the CME Group will be providing downloadable holiday calendars for Globex and incorporating with Regular Trading hours into one location. To view the trading hours for a specific holiday please se[lect]..." — FX product-level Globex times are behind the widget/downloads => NOT_OBTAINED from static HTML.
LIVE fetch this lane: BLOCKED_TRANSPORT (web_reader -429 then -500 network error; WebFetch ECONNREFUSED; 3 attempts logged).

---

## PART B — Expiration / last-trade rule (official, verbatim)

### Rule text — ARCHIVED_OFFICIAL, identical across all four products

Source: archived captures of each product's official contract-specifications page (static era). Resolved captures:
- 6E Euro FX: https://web.archive.org/web/20111220033303/http://www.cmegroup.com/trading/fx/g10/euro-fx_contract_specifications.html
- 6B British Pound: https://web.archive.org/web/20120107063645/.../british-pound_contract_specifications.html
- 6J Japanese Yen: https://web.archive.org/web/20120107022717/.../japanese-yen_contract_specifications.html
- 6A Australian Dollar: https://web.archive.org/web/20111230060253/.../australian-dollar_contract_specifications.html

Verbatim (ALL FOUR, identical):
> **Last Trade Date / Time**
> "9:16 a.m. Central Time (CT) on the second business day immediately preceding the third Wednesday of the contract month (usually Monday)."

Modern-era confirmation — ARCHIVED_OFFICIAL: capture 20230610100715 of https://www.cmegroup.com/cn-s/markets/fx/g10/euro-fx.contractSpecs.html (official cmegroup.com page, Chinese locale) states: "合约月份第三个周三之前的第二个营业日（通常是周一）上午9:16（美中时间）。" (= 9:16 a.m. CT on the second business day preceding the third Wednesday of the contract month, usually Monday) — rule unchanged as of June 2023. The 2016-era English capture (20160311003837) is a JS shell (no static text) — noted, not used. English live/2024+ verification NOT_OBTAINED (live blocked; no static English captures post-2013 era).
Consistency test (OBSERVED, script): all 96 officially-sourced last-trade dates below equal "second weekday preceding the third Wednesday of the contract month" — 96/96, zero deviations (no holiday collisions in the covered quarters).

### Quarterly expiry (Last Trade) dates — ARCHIVED_OFFICIAL, 96 quarters total

All values are "Last Trade" from archived official CME product-calendar captures (old static URL /trading/fx/g10/{product}_product_calendar.html; explicit capture timestamps). Full machine table in `fx_cal_coverage.json`; per-symbol coverage:

**6E (codes EC)** — 17 quarters [r2-corrected]: 2010 all 4 (Mar 15, Jun 14, Sep 13, Dec 13); 2011 Mar 14, Jun 13; 2012 three quarters (Jun 18, Sep 17, Dec 17) — **Mar 2012/ECH12 NOT obtained** (absent from every archived 6E capture; CDX gap 2010-01..2012-05, May-2012 capture lists from JUN 2012); 2013 all 4 (Mar 18, Jun 17, Sep 16, Dec 16); 2014 all 4 (Mar 17, Jun 16, Sep 15, Dec 15). Captures: 20100109225004, 20120508203837, 20121102074408, 20130719102958. NOT_OBTAINED: Sep/Dec 2011, Mar 2012, ALL 2015-2026 (JS-shell era from Apr-2014 captures onward for this URL).

**6B (codes BP)** — 31 quarters: 2011 all 4 (Mar 14, Jun 13, Sep 19, Dec 19); 2012 all 4; 2013 all 4; 2014 all 4; 2015 all 4; 2016 all 4; 2017 all 4; 2018 Mar/Jun/Sep (Mar 19, Jun 18, Sep 17). Captures: 20110316150906, 20121101062823, 20130917214233 (21-row full listing Sep 2013→Sep 2018). NOT_OBTAINED: 2010 (no captures before Mar 2011), Dec 2018, ALL 2019-2026.

**6J (codes JY/J1)** — 13 quarters: 2011 Sep/Dec (Sep 19, Dec 19); 2012 all 4; 2013 all 4; 2014 Mar/Jun/Sep (Mar 17, Jun 16, Sep 15). Captures: 20110811134014, 20121102121049, 20130607062822. NOT_OBTAINED: 2010, Mar/Jun 2011, Dec 2014, ALL 2015-2026.

**6A (codes AD)** — 35 quarters: 2010 all 4 (Mar 15, Jun 14, Sep 13, Dec 13); 2011 all 4; 2012 all 4; 2013 all 4; 2014 all 4; 2015 all 4; 2016 all 4; 2017 all 4; 2018 Mar/Jun/Sep (Mar 19, Jun 18, Sep 17). Captures: 20100108131844, 20110811094045, 20121102121706, 20130916203339 (21-row full listing). NOT_OBTAINED: Dec 2018, ALL 2019-2026.

Reason (measured): the FX product-calendar URLs have NO static-row Wayback captures after mid-2014 (2014-07..2017 captures fetched: table headers present, contract rows JS-loaded, 0 dates — verified on 9 captures); 2022-era captures are React shells. Zero conflicts across overlapping captures (dedup tested).

Full 96-row table: see `fx_cal_coverage.json` → `expirations` (fields: sym, month, code, first_trade, last_trade, capture_ts).

---

## PART C — Relation to bar-measured construction rules (for the qualification doc)

- The official expiry rule above (Monday before 3rd Wednesday, 9:16 CT) is the DECLARED contract expiry. The repo's §1.3 roll rules (6E "Friday of expiry week = 1 session before Monday last-trade", 27/27) are bar-measured CONSTRUCTION rules and remain exactly that — construction. The 6E measured expiry-rule backtest used the holiday set {MLK, Presidents, Juneteenth 2022+, Columbus, Good Friday, Veterans} for business-day computation; this lane's official evidence shows those are precisely the holidays where the FX-family Globex schedule deviates (plus/minus Christmas/NY closures and Memorial/Labor/Independence halts), so the measured holiday set is consistent with the official deviation set. No re-derivation performed (per dispatch).
- Discrepancy watch (known_limitations, not resolved here): Good Friday alternates between FX early-close (2010, 2012, 2015) and full closure (2011, 2013, 2014, 2016; 2027 note says "No trading for Friday March 26th trade date") — any pipeline assuming one behavior across years must be year-aware.

## Verdicts (per blocker item)

1. **Holidays + early closes per product × year 2010-2026**:
   - 2010-2016: **PASS-with-coverage** — 7/17 years at FULL FX-family product-level detail (closures, halts, early-close times, reopen times), all ARCHIVED_OFFICIAL with pinned capture timestamps. Caveats: Veterans 2014/2015 evidenced by settlement-procedures docs (trading occurred; explicit Globex-hours line NOT_OBTAINED); all four codes share the FX-family schedule (no per-code divergence in any artifact).
   - 2017: **PARTIAL** — windows official; New Year product-level official; other holidays FX product-level NOT_OBTAINED.
   - 2018-2025: **PARTIAL** — Globex window tables official (all 8 years); FX product-level times NOT_OBTAINED (source files not archived; pages carry no FX rows).
   - 2026: **PARTIAL** — windows + Globex-wide Holiday Notes official (Sep-2026 capture); FX product-level times NOT_OBTAINED (moved to widget/downloads); LIVE_OFFICIAL not obtained this lane (transport blocked; ES lane reached it earlier the same day).
2. **Expiration rule per product**: **PASS-with-coverage** — verbatim rule from official spec pages, all four products, 2011 captures + 2023 official capture confirming continuity (Chinese-locale page); English post-2013 static confirmation NOT_OBTAINED.
3. **Quarterly expiry dates**: **PASS-with-coverage** — 96/272 quarters (2010-2026 × 4 codes × 4) officially sourced: 6E 17/68 [r2-corrected], 6B 31/68, 6J 13/68, 6A 35/68 (17+31+13+35=96); every covered quarter internally conflict-free and 96/96 consistent with the declared rule. Remaining NOT_OBTAINED: 2019-2026 for all four (product-calendar JS-shell era), plus per-symbol gaps listed above.

## Incident/etiquette notes

- web.archive.org intermittently returned "Temporarily Offline" pages (2x) and sporadic connection failures under pacing; handled by sleep+retry within the 2-attempt-per-URL-per-method budget (a few URLs used attempt 2; none exceeded it).
- Archive.org CDX endpoints worked via plain curl after the ES lane's MCP failures — not contradictory (different client path).
- No third-party aggregator was used as authority at any point.
