# Equity-Family Calendar Gap-Fill — ES 2010-2011 expirations + ES/NQ 2026 Globex product times (Lane P2A-CALGAP-EQ)

Task: FUTURES-OVERNIGHT-PREP-20261003 | Cycle: UNREGISTERED_PREP | Lane: P2A-CALGAP-EQ | 2026-10-03 (all timestamps UTC).
Inputs honored: parent A1 evidence `research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es/{NQ_CALENDAR_EVIDENCE.md, ES_EXPIRATIONS_GAPFILL.md, nq_cal_coverage.json, es_expiry_coverage.json, fetch_log.jsonl}` and D3 base `research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md` — re-read before work; all URLs below re-fetched first-hand this lane unless labeled otherwise.
Laws honored: official/archived-official authority only; no inference of product times from family tables; no inference of dates from the 3rd-Friday rule; uncertain ⇒ NOT_OBTAINED; ≤2 attempts/URL/method (full trail in `fetch_log.jsonl`); no UA spoofing, no proxies; every relied-on capture saved under `captures/` with sha256.

## Gap 1 — ES expirations Sep 2010, Dec 2010, Mar 2011, Jun 2011, Sep 2011: **CLOSED** (ARCHIVED_OFFICIAL_PRODUCT, dual independent captures)

### How (measurement, not memory)

Wayback CDX enumeration of the ES product-calendar DATA page
`https://www.cmegroup.com/trading/equity-index/us-index/e-mini-sandp500_product_calendar_futures.html`
(673→71 captures listed; CDX query logged) shows a **static-era capture set 2009-10-16 through 2017-06** that neither D3 nor parent-A1 had enumerated for the pre-2012 window (D3 used the BASE URL `..._product_calendar.html`; A1 probed the data page only at 2017+ timestamps). Two captures in that set cover exactly the gap window and were fetched and saved this lane:

- **G1a = 20100528164817** (captured 2010-05-28) — lists JUN 2010 through SEP 2011, i.e. ALL FIVE gap quarters.
- **G1b = 20100418154051** (captured 2010-04-18) — lists JUN 2010 through JUN 2011, i.e. four of the five (all but SEP 2011).

Both are Wayback captures of official cmegroup.com pages. Page heading verbatim (both captures): **"Product Calendar for E-mini S&P 500 (Dollar) Futures"**; table header verbatim: **"Contract Month | Product Code | First Trade Last Trade | Settlement | First Holding Last Holding | First Position Last Position | First Notice Last Notice | First Delivery Last Delivery"**.

### The five quarters, verbatim from G1a (cells: Contract Month | Product Code | First Trade, Last Trade | Settlement)

| Contract | Code | First Trade | **Last Trade / Settle** | Also in |
|---|---|---|---|---|
| SEP 2010 | ESU10 | 06/19/2009 | **09/17/2010** | G1b |
| DEC 2010 | ESZ10 | 09/18/2009 | **12/17/2010** | G1b |
| MAR 2011 | ESH11 | 12/18/2009 | **03/18/2011** | G1b |
| JUN 2011 | ESM11 | 03/19/2010 | **06/17/2011** | G1b |
| SEP 2011 | ESU11 | 06/18/2010 | **09/16/2011** | G1a only (Sep-2011 contract had no other pre-expiry capture in the window) |

Verbatim row examples (G1a): `SEP 2010 | ESU10 | 06/19/2009 09/17/2010 | 09/17/2010 | - - | - - | - - | - -`; `SEP 2011 | ESU11 | 06/18/2010 09/16/2011 | 09/16/2011 | - - | - - | - - | - -`. G1b agrees exactly on the four overlapping quarters (dates identical to the day).

### Cross-checks (official-vs-official)

1. **G1a vs G1b** (independent captures 6 weeks apart): exact agreement on Sep 2010, Dec 2010, Mar 2011, Jun 2011.
2. **vs NQ product-calendar product rows** (parent-A1 P1/P2/P3, re-fetched this lane; see hypothesis note below): NQ same-quarter dates are identical — NQU10 09/17/2010, NQZ10 12/17/2010, NQH11 03/18/2011, NQM11 06/17/2011, NQU11 09/16/2011. Zero divergence.
3. **vs the rule in force** (OBSERVED consistency, NOT used as authority): all five dates are the 3rd Friday of the contract month, per the verbatim rule already on file ("Trading can occur up to 8:30 a.m. on the 3rd Friday of the contract month", ES spec capture 20150319105531 / 20200317052532, D3/A1 evidence). No date was derived from the rule.

### Mission hypothesis check (recorded honestly)

Mission lead said the NQ product-calendar captures "almost certainly carry an ES column or sibling rows". **Refuted first-hand**: this lane re-fetched NQ captures P1 = 20091207203237 and P2 = 20110305184630 (saved) and mined them for ES rows — page heading is "Product Calendar for E-mini NASDAQ-100 Futures", contract rows are NQ-only, **zero ES product codes anywhere on the page** (the only "S&P" strings are the site-wide nav menu). The ES unlock instead came from the ES page's own un-enumerated capture window (above). The NQ captures remain useful as cross-check #2.

### Coverage arithmetic

ES expirations 2010-2026: was 63/68 (37 product-specific D3 + 26 family-level A1). This lane +5 product-specific ⇒ **68/68 quarters** (42 product-specific + 26 official family rolldates). 2010 and 2011 are now complete years at product-specific level.

## Gap 2 — ES-specific 2026 Globex session times: **NOT_OBTAINED** (blocked at widget layer; every static/archived official route measured and saved)

Attempt trail (each logged in `fetch_log.jsonl`; cumulative with parent-A1's trail noted where relevant):

1. **Complete official 2026 file inventory enumerated** — CDX prefix enumeration of `cmegroup.com/tools-information/holiday-calendar/files` (673 distinct archived URLs) plus the full static href inventory of trading-hours capture 20260924120320. The ENTIRE official 2026 file set is three classes: (a) `{holiday}-clearing-advisory.pdf` (ClearPort/clearing), (b) `{holiday}-holiday-settlement-times-2026.pdf` (12 files), (c) `otc-{holiday}-2026.pdf`. **No Globex session-hours file exists anywhere in the archived inventory**; naming pattern `globex-holiday-calendar.pdf` appears only for 2009/2010 (and a 404 probe for 2008/2011).
2. **Settlement-times PDFs fetched and parsed** (3 of 12, saved): `mlk-day-…`, `good-friday-…`, `thanksgiving-holiday-settlement-times-2026.pdf` (captures 2025-10-13). Content is **settlement-price derivation times**, not session hours — e.g. Thanksgiving PDF verbatim: "Equity & Crypto Products **Settlement Time: 12:00:00 CT**"; MLK PDF: "All products will settle at their normal times on Friday January 16th … Monday January 19, 2026 CME Group will not derive or disseminate settlement prices for CME, CBOT, NYMEX or COMEX". Settlement time ≠ trading close; per law, NO session-time inference drawn from these.
3. **Live trading-hours page re-fetched with link enumeration** (web_reader 2026-10-03): static content = the same family/venue tables and file links as the archived capture; per-holiday product hours sit behind the DATE widget. Verbatim note (saved capture 20260924120320): **"Globex Trading Hours and Holiday Schedules — Please note that with the 2026 and 2027 calendar year the CME Group will be providing downloadable holiday calendars for Globex and incorporating with Regular Trading hours into one location. To view the trading hours for a specific holiday please select the appropriate date in the 'DATE' field and the data will automatically update in the table…"** All "Holiday Schedule" links in the holiday-window tables resolve to the in-page anchor `trading-hours.html#trading-holiday-hours` (the widget), and **zero** hrefs to any downloadable Globex-hours file exist in the page source.
4. **All 23 static tables of the 2026-era trading-hours page extracted from saved capture 20260924120320**: venue Globex windows, ClearPort, floor, freeze calendar, repo/BrokerTec/EBS/fixings — **no product-named session-times table** (no "ES", "E-mini", "S&P 500", "Nasdaq" session rows; the only "Equity" strings are the family notes, e.g. ClearPort Good-Friday special "…CME & CBOT Equity Indices…"). Family tables do not name ES ⇒ not authority for ES product times.
5. **Widget host** `https://www.cmegroup.com/holidaycalendar` — web_reader -500 upstream network error (1 attempt this lane; parent-A1 2 attempts 2026-10-03) ⇒ **BLOCKED_TRANSPORT**; no bypass attempted. No CmeWS/API endpoint is referenced in the page source (grep: 0 hits).
6. **ES spec + product pages, 2025-2026 captures** (saved): old spec URL @20260114231448 (redirects to `markets/equities/sp/e-mini-sandp500.contractSpecs.html` content): 300KB page with spec-section scaffolding verbatim `{"title": "Trading Hours", "value": "TradingHours"}` and ES product identity JSON (`"globexGroupCode":"ES"`), but **values client-rendered — zero hours text in static HTML** (0 hits for "Sunday"/"p.m."). ES product page @20261001064354: nav links only.
7. **rulebook.cmegroup.com**: zero Wayback captures (CDX, 2 URL forms); live route already measured -500 by parent.
8. **CME notices**: archived `/notices/` inventory has no 2026 holiday trading-hours notice (only a 2025 weather-products trading-hours change); live `notices.html` is a JS search tool. WebSearch surfaced a "Thanksgiving Day 2026.docx" hosted on cmegroup.com, but the engine truncates its URL; exact-title searches did not recover it; domain-wide CDX regex query 502'd twice (too heavy — stopped per etiquette). Third-party hits (camovia.com, ampfutures.com, ninjatrader vendor pages) = cross-check class only, NEVER authority.
9. Parent-A1's measured blockers stand unrebutted: guessed `files/2026/2026-globex-holiday-calendar.pdf` (Wayback 404 / live -500), React-shell product-calendar pages 2018+.

**What IS authority-backed for ES 2026** (unchanged from parent, now with a saved capture): 11 holiday windows, floor early closes 12:00 CT (May 22, Jul 2, Nov 27, Dec 24, Dec 31), Good Friday Apr 3 floor close 10:00 CT, ClearPort closures + 13:15 ET prior-day pattern, family Holiday Notes (Equity+IR normal hours on MLK/Presidents), TAS early closes, and all four 2026 ES expirations. **NOT_OBTAINED: the ES-specific Globex holiday session (open/early-close) TIMES for 2026** — they live only inside the DATE widget / widget-exposed downloadable calendars.

## Gap 3 — NQ-specific 2026 Globex session times: **NOT_OBTAINED** (same evidence base; NQ-specific attempts below)

Same routes as Gap 2 — the widget, files inventory, and page tables are product-agnostic and contain no NQ-named session rows. NQ-specific measurements this lane:
1. Old spec URL `e-mini-nasdaq-100_contract_specifications.html` @20251102121109 (latest capture): 2.2KB **"Access Denied"** block page — no content.
2. NQ product page `markets/equities/nasdaq/e-mini-nasdaq-100.html` @20260930171821 (saved): nav links ("Holiday & Trading Hours" → /trading-hours.html), no hours values in static HTML.
3. NQ new contractSpecs captures exist through 2026-10-01 (CDX) but the ES sibling measured this lane (same AEM/React architecture, spec values client-rendered) shows the class is a shell; parent-A1 measured the NQ live contractSpecs page as a JS shell on 2026-10-03.
Verdict: **NOT_OBTAINED — NQ-specific 2026 Globex holiday session times** (widget-only; BLOCKED_TRANSPORT trail above). No inference from the family page, from 2025 hours, or from settlement-time PDFs.

## Saved captures (captures/, sha256)

| File | What it is | sha256 |
|---|---|---|
| es_pcal_20100528164817.html | **Gap-1 primary** — ES product-calendar page, capture 2010-05-28 (all 5 quarters) | bb996a77e8f7e56f54fcf07d57f80b39a34e83897227686d865bdc5fa5e9072b |
| es_pcal_20100418154051.html | Gap-1 cross-check — ES product-calendar page, capture 2010-04-18 | b2e2e13512843277c0087e802092e669cf5131d4ac616b7c1c46df1c5fa5cd8d |
| nq_pcal_20110305184630.html | Hypothesis test — NQ product-calendar capture 2011-03-05 (NQ rows only, no ES rows) | 038d649d8badbf978e8fc269b47e5de7e6637cb66800c0bda02c0e827b3f7775 |
| nq_pcal_20091207203237.html | Hypothesis test — NQ product-calendar capture 2009-12-07 (NQ rows only, no ES rows) | e660fbeb105192acd20086fb… (full in eq_gapfill_coverage.json outputs) |
| tradinghours_20260924120320.html | **Gap-2/3 proof** — trading-hours page capture 2026-09-24 (all 23 static tables; widget note verbatim; full 2026 file href inventory) | fedf3e33e06ef02254733b7dae4abfcc7f3dcac8a3e39adf264c30a2373e4f08 |
| es_olspec_20260114231448.html | Gap-2 proof — ES spec page capture 2026-01-14 (scaffolding only, hours client-rendered) | 49244a22b0eabb8623f31026… |
| nq_olspec_20251102121109.html | Gap-3 proof — NQ old-spec capture 2025-11-02 = "Access Denied" | d278bdf5bf2a729c0344053d… |
| es_prod_20261001064354.html | Gap-2 proof — ES product page capture 2026-10-01 (nav only) | see coverage json |
| nq_prod_20260930171821.html | Gap-3 proof — NQ product page capture 2026-09-30 (nav only) | see coverage json |
| mlk-day-holiday-settlement-times-2026.pdf | Official 2026 MLK settlement-times advisory (settlement-price times, NOT session hours) | 9a9e3b1e4bf16d6551003ed7f507bb0f9898a0bf46746d3b7eee9ec4d258a4f4 |
| good-friday-holiday-settlement-times-2026.pdf | Official 2026 Good Friday settlement-times advisory | fed0b2d58bee1f25b10f7682756f803ad15f7263c5db468603f506c235e1a35d |
| thanksgiving-holiday-settlement-times-2026.pdf | Official 2026 Thanksgiving settlement-times advisory | 560e905d4c70605f0e1a8d0a6b780db594befbc074114ac11225e504c9ba3b14 |

## Verdicts

1. **ES expirations 5 gap quarters: CLOSED** — ARCHIVED_OFFICIAL_PRODUCT, dual captures (G1a primary, G1b 4/5 cross-check), NQ cross-check exact. ES total 2010-2026: **68/68**.
2. **ES-specific 2026 Globex session times: NOT_OBTAINED** — widget-only existence; complete static/archived official route trail saved; no inference used.
3. **NQ-specific 2026 Globex session times: NOT_OBTAINED** — same class of evidence; NQ-specific attempts recorded.
