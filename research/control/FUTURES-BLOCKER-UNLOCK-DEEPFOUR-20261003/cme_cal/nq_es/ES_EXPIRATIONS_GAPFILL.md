# ES Gap-fill — Expirations 2019-2023 + 2026, and ES 2026 Globex times (Lane A1-CMECAL-NQES)

Task: FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 | Cycle: UNREGISTERED_PREP | Lane: A1-CMECAL-NQES | 2026-10-03 (UTC).
Prior state (D3-CMECAL, 2026-10-03): ES expirations 36/68 quarters ARCHIVED_OFFICIAL (summary count; their master table lists 37 rows — Mar/Jun 2010, Dec 2011, all 2012-2018, Sep/Dec 2024, all 2025 — a one-row counting slip in their `expiration_summary`, noted here for reconciliation); NOT_OBTAINED: all 2019-2023 + 2026, Mar/Jun 2024, Sep/Dec 2010, Mar/Jun/Sep 2011. ES 2026 Globex times NOT_OBTAINED (widget).

## 1) The unlock: official CME "Equity Index Roll Dates" page

Prior lane measured a Wayback capture gap (2017-04→2020-09) on the ES product-calendar BASE URL and React shells after. This lane found the actual data page (`..._product_calendar_futures.html`) has captures inside that window but they are widget-era ("No Data Available" — captures 20180419181410, 20181018233905, 20190719165518; static era ends 2017-10-17). The working official route for the missing years is instead the official CME page:

`https://www.cmegroup.com/trading/equity-index/rolldates.html`

whose table (verbatim heading and columns, capture 20260122070119): **"Customary Roll Dates for Upcoming Equity Index Quarterly Futures — Year | Month | U.S. Indexes: Expiration | Roll | Nikkei / TOPIX: Expiration | Roll"**. The "U.S. Indexes — Expiration" column is the official CME quarterly-futures expiration date for the U.S. equity-index family (ES and NQ are U.S. equity-index quarterly futures; per dispatch method rule the family-wide wording is authority for both). Page body also states (verbatim): "participants can roll their futures positions from June to September at any time. … Equity products roll date is the Monday prior to the third Friday of the expiration month." — i.e. Expiration, not Roll, is the contract expiry.

### Verbatim "U.S. Indexes — Expiration" values (gap years)

From capture 20191019064427 (2018Q1-2020Q4), 20210420094153 (2020Q1-2022Q4; identical in 20211124215638 / 20220127112011 / 20220817040258), 20240616114215 (2022Q4-2025Q4), 20260122070119 (2025Q1-2028Q4):

| Year | Mar | Jun | Sep | Dec | Captures |
|---|---|---|---|---|---|
| 2019 | 3/15/19 | 6/21/19 | 9/20/19 | 12/20/19 | R1 |
| 2020 | 3/20/20 | 6/19/20 | 9/18/20 | 12/18/20 | R1, R2 |
| 2021 | 3/19/21 | 6/18/21 | 9/17/21 | 12/17/21 | R2 |
| 2022 | 3/18/22 | 6/17/22 | 9/16/22 | 12/16 | R2, R3 |
| 2023 | — | — | — | 3/17 / 6/16 / 9/15 / 12/15 | R3 |
| 2024 | 3/15 | 6/21 | 9/20 | 12/20 | R3 |
| 2026 | 3/20 | 6/18 | 9/18 | 12/18 | R4 |

R1 = https://web.archive.org/web/20191019064427/https://www.cmegroup.com/trading/equity-index/rolldates.html
R2 = https://web.archive.org/web/20210420094153/https://www.cmegroup.com/trading/equity-index/rolldates.html
R3 = https://web.archive.org/web/20240616114215/https://www.cmegroup.com/trading/equity-index/rolldates.html
R4 = https://web.archive.org/web/20260122070119/https://www.cmegroup.com/trading/equity-index/rolldates.html

Jun 2026 = 6/18 — the Juneteenth shift (3rd Friday Jun 19 2026 = Juneteenth observed) is stated by the official table itself; also matches the data-side measured date in the NQ/ES dossiers.

### Cross-checks (official-vs-official, zero divergence)

- ES product-calendar (this lane re-derived prior-lane C10 with exact URL, capture 20171017001221 of `..._product_calendar_futures.html`): Dec 2017 15 Dec 2017; Mar 2018 16 Mar; Jun 2018 15 Jun; Sep 2018 21 Sep; Dec 2018 21 Dec — R1 family dates 2018: 3/16/18, 6/15/18, 9/21/18, 12/21/18 ⇒ EXACT match.
- ES product-calendar (prior-lane C11 record, 2024-09-27 fetch): Sep 2024 09/20/2024; Dec 2024 12/20/2024; Mar 2025 03/21/2025; Jun 2025 06/20/2025; Sep 2025 09/19/2025; Dec 2025 12/19/2025 — R3 gives 9/20, 12/20, 3/21, 6/20, 9/19, 12/19 ⇒ EXACT match.
- NQ product-calendar product-specific rows (this lane) vs family dates on all overlaps (2012-2018, R5 = capture 20120829175938 and R6 = 20141006184010): EXACT match on all 28 overlapping quarters.
- Live-page search-engine snippet of the current ES product calendar (discovery only, NOT authority): "Sep 2026 · ESU26 · … 18 Sep 2026 ; Dec 2026 · ESZ26 · … 18 Dec 2026 ; Mar 2027 · ESH27 · … 19 Mar 2027" — consistent with R4.

### ES closure arithmetic (68 quarters 2010-2026)

- Was (D3): 37 rows product-specific (their summary said 36 — counting slip, table has 37).
- Closed this lane (family-level ARCHIVED_OFFICIAL, rolldates): 2019×4, 2020×4, 2021×4, 2022×4, 2023×4, Mar 2024, Jun 2024, 2026×4 = **26 quarters**.
- Now: **63/68**. Remaining NOT_OBTAINED: **Sep 2010, Dec 2010, Mar 2011, Jun 2011, Sep 2011** (5 quarters). Measured reason: rolldates URL has NO Wayback capture before 2012-08-29 (requests @20100901 and @20110601 resolve forward to 20120829175938), and the ES product-calendar static era has no capture listing those quarters (D3 gap facts). Rule in force then (verbatim, capture 20200317052532 of the ES spec page, and 2015-capture 20150319105531): "Trading can occur up to 8:30 a.m. on the 3rd Friday of the contract month" / (2020) "Trading terminates at 9:30 a.m. ET on the 3rd Friday of the contract month" — but per law these five dates are NOT derived from the rule; they stay NOT_OBTAINED.

Verdict (ES expirations blocker): **PARTIAL → now 63/68 (from 36/68)**; every previously-missing year 2019-2023 and 2026 is now closed at official family level; 5 quarters (2010-2011) remain NOT_OBTAINED with the archive facts recorded.

## 2) ES 2026 Globex session times — verdict NOT_OBTAINED (blocked at transport/widget layer)

Evidence trail (all logged in fetch_log.jsonl, 2026-10-03):

1. LIVE trading-hours page (web_reader SUCCESS): product-level Globex holiday hours are behind the interactive widget — verbatim: "Please note that with the 2026 calendar year the CME Group will be providing downloadable holiday calendars for Globex and incorporating with Regular Trading hours into one location. To view the trading hours for a specific holiday please select the appropriate date in the 'DATE' field and the data will automatically update in the table below the date field." Static HTML carries only family-level notes ("some products will close early at 13:15 p.m. CT and others will close early at 13:00 p.m. CT … Equity and Interest Rate products trade normal hours on Martin Luther King Day and Presidents Day", TAS early closes, floor/ClearPort times) — no ES-specific Globex times.
2. Widget host `https://www.cmegroup.com/holidaycalendar` — web_reader -500 upstream network error ×2 ⇒ BLOCKED_TRANSPORT; stopped per etiquette (no bypass attempted).
3. Guessed downloadable-calendar PDF URLs (`/tools-information/holiday-calendar/files/2026/2026-globex-holiday-calendar.pdf` and dam-path variant): Wayback 404; live web_reader -500.
4. ES live product calendar + contractSpecs pages: React/JS shells (prior lane measurement; this lane's captures concur — e.g. new-URL capture 20250702132707 shell; ES futures-subpage requests 2024-2026 resolve to 2021 shell).
5. Browser automation to operate the widget: "Browser is not available in subagent" (browser-use skill, node_repl) — recorded.
6. rulebook.cmegroup.com live: web_reader -500.

What IS authority-backed for ES 2026 (from the live page + rolldates R4): the 11 holiday windows (verbatim in NQ file §1), floor early closes 12:00 CT (May 22, Jul 2, Nov 27, Dec 24, Dec 31), Good Friday Apr 3 floor close 10:00 CT, ClearPort closures + 13:15 ET prior-day pattern, family Holiday Notes, and all four 2026 expirations (3/20, 6/18, 9/18, 12/18). NOT_OBTAINED: the ES-specific Globex early-close/open TIMES for 2026 holidays (requires widget/JS or the downloadable calendar files whose URLs are only exposed inside the widget).

## 3) Reconciliation notes for the Lead

- D3 `expiration_summary.quarters_obtained` said 36; the D3 master table contains 37 rows. This lane counts from rows. Combined coverage now: 37 product-specific (D3) + 26 family-level (this lane) = 63/68; missing 5 (Sep 2010, Dec 2010, Mar 2011, Jun 2011, Sep 2011).
- The D3-stated "capture gap 2017-04→2020-09" applies to the product-calendar BASE URL; the `_product_calendar_futures.html` data page had captures in that window but they are widget-era "No Data Available" (2018-04-19, 2018-10-18, 2019-07-19) — so the D3 conclusion (no product-specific data 2018-2026 from that URL family) stands; only the reason is refined.
- Prior-lane C11 (2024-09-27 product-calendar data) could not be re-derived: all 2024-2026 requests to both URL forms resolve to shells; C11's dates are nonetheless corroborated exactly by rolldates R3 — keep C11's "exact URL not preserved" caveat as-is.
