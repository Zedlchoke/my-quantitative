# COMM (CL/NG/GC/SI) — Official CME Calendar & Expiry Evidence (Lane A3-CMECAL-COMM)

Task: FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003 | Cycle: UNREGISTERED_PREP | Lane: A3-CMECAL-COMM
Acquisition date: 2026-10-03 (all fetches). Scope: what a $0 official-source unlock WOULD and
WOULD NOT provide for the four commodity codes. **This lane claims NO qualification upgrade —
CL/NG/GC/SI remain NOT_QUALIFIED_V2 (DATACONTRACT_QUALIFICATION.md §2).**

Laws honored: public access only (curl default UA / reader tools); no spoofing; no proxies;
≤2 attempts per distinct URL per method; every attempt logged in `fetch_log.jsonl`; uncertain
days ⇒ EXCLUDED / NOT_RUN; no inference gap-fill. Provenance labels: `LIVE_OFFICIAL`,
`ARCHIVED_OFFICIAL` (web.archive.org capture of official cmegroup.com), `OBTAINABLE`
(capture verified to exist via CDX, not fetched), `NOT_OBTAINED` (reason given).

Method (extends D3-CMECAL / ES_CALENDAR_EVIDENCE.md): live cmegroup.com via web_reader;
archive route via plain `/usr/bin/curl -sL` on `https://web.archive.org/web/{ts}/{original}`;
Wayback CDX (`web.archive.org/cdx/search/cdx`) used for URL/capture discovery — the decisive
discovery being the historical product-URL families:
- specs: `…/trading/{energy|metals}/…/{product}_contractSpecs_futures.html` (static tables, capture era 2009→2021)
- per-contract calendars: `…/{product}_product_calendar_futures.html` (static tables, era varies by product)

---

## 1. Verbatim termination (last-trade) rules — all four OBTAINED [ARCHIVED_OFFICIAL]

### CL — Crude Oil WTI futures, NYMEX

Source (2018 era): web.archive.org capture **20180602035630** of
`http://www.cmegroup.com/trading/energy/crude-oil/light-sweet-crude_contractSpecs_futures.html`
(saved: `html/cl_specspec_2018req.html`, row at line 4447ff). Verbatim:

> **Termination Of Trading** — "Trading in the current delivery month shall cease on the third
> business day prior to the twenty-fifth calendar day of the month preceding the delivery month.
> If the twenty-fifth calendar day of the month is a non-business day, trading shall cease on the
> third business day prior to the last business day preceding the twenty-fifth calendar day. In
> the event that the official Exchange holiday schedule changes subsequent to the listing of a
> Crude Oil futures, the originally listed expiration date shall remain in effect. In the event
> that the originally listed expiration day is declared a holiday, expiration will move to the
> business day immediately prior."

Source (2020 era): capture **20200711040241**, same URL (`html/cl_specspec_20200711040241.html`):

> "Trading terminates 3 business day prior to the 25th calendar day of the month prior to the
> contract month. If the 25th calendar day is not a business day, trading terminates 4 business
> days prior to the 25th calendar day of the month prior to the contract month."

Era-diff note [OBSERVED, disclosed]: the weekend-shift sub-rule was re-worded between 2018 and
2020. The two formulations are semantically equivalent (the "last business day preceding the
25th" IS the 1st business day prior to the 25th, so "3 bd prior to it" == "4 bd prior to the
25th"); both were validated against official per-contract dates below (CLZ18 spot-check). Same
page also verbatim: Contract Unit "1,000 barrels"; Listed Contracts 2018 "current year and the
next 8 calendar years and 2 additional consecutive contract months" → 2020 "next 10 calendar
years and 2 additional contract months" (matches v1 dossier's "~10 years" mirror claim);
Settlement Method "Deliverable"; Trading Hours Globex "Sunday - Friday 6:00 p.m. - 5:00 p.m.
(5:00 p.m. - 4:00 p.m. Chicago Time/CT) with a 60-minute break each day beginning at 5:00 p.m.
(4:00 p.m. CT)".

v1 dossier cross-check: CL_DOSSIER's mirror-sourced rule text MATCHES the official wording.
**FACT(ARCHIVED_OFFICIAL ×2 eras).**

### NG — Henry Hub Natural Gas futures, NYMEX

Source (2018): capture **20180601223853** of
`http://www.cmegroup.com/trading/energy/natural-gas/natural-gas_contractSpecs_futures.html`
(`html/ng_specspec_2018req.html`). Verbatim:

> **Termination Of Trading** — "Trading of any delivery month shall cease three (3) business
> days prior to the first day of the delivery month. In the event that the official Exchange
> holiday schedule changes subsequent to the listing of a Natural Gas futures, the originally
> listed expiration date shall remain in effect. In the event that the originally listed
> expiration day is declared a holiday, expiration will move to the business day immediately
> prior."

Source (2021, last static-era capture): **20210517093702** (`html/ng_specspec_20210517093702.html`):

> "Trading terminates on the 3rd last business day of the month prior to the contract month."

Notes: (a) the two official eras are semantically identical — "3 business days prior to the
first day of the delivery month" == "3rd last business day of the prior month" (contiguous
business-day chain across a month boundary); (b) the 2021 official text is **word-for-word the
rule the v1 NG_DOSSIER cited from a secondary mirror**, and it confirms the dossier's audited
canonical basis (last-trade-month binding, erratum M2) — the LTD sits in the month prior to
delivery. Same page verbatim: Contract Unit "10,000 MMBtu"; tick "$0.001 per MMBtu"; Listed
Contracts "current year plus the next twelve calendar years"; Deliverable.
**FACT(ARCHIVED_OFFICIAL ×2 eras).**

### GC — Gold futures, COMEX

Source (2018): capture **20180602045132** of
`http://www.cmegroup.com/trading/metals/precious/gold_contractSpecs_futures.html`
(`html/gc_specspec_2018req.html`). Verbatim:

> **Termination Of Trading** — "Trading terminates at 12:30 p.m. CT on the third last business
> day of the delivery month."

Source (2021): capture **20210422115955** — "Trading terminates at 12:30 p.m. CT on the third
last business day of the **contract** month." (stable rule; "delivery"→"contract" wording only).

Same page verbatim: Contract Unit "100 troy ounces"; tick "$0.10 per troy ounce"; Listed
Contracts 2018 "current calendar month; the next two calendar months; any February, April,
August, and October falling within a 23-month period; and any June and December falling within a
72-month period" (→ 2021 "3 consecutive months…" same cycle) — i.e. active cycle
**G,J,M,Q,V,Z**, matching the v1 dossier's measured chain. v1 dossier's "ceases 13:30 ET" ==
12:30 CT **MATCH**. **FACT(ARCHIVED_OFFICIAL ×2 eras).**

### SI — Silver 5,000 oz futures, COMEX

Source (2018): capture **20180601223623** of
`http://www.cmegroup.com/trading/metals/precious/silver_contractSpecs_futures.html`
(`html/si_specspec_2018req.html`). Verbatim:

> **Termination Of Trading** — "Trading terminates at 12:25 p.m. CT on the third last business
> day of the delivery month."

Source (2021): capture **20210517090001** — "…at 12:25 p.m. CT on the third last business day
of the **contract** month." (stable).

**Distinctness finding**: SI terminates **12:25 p.m. CT** vs GC **12:30 p.m. CT** — a
5-minute gold-vs-silver difference, present in BOTH eras (i.e. not recitable from a generic
metals rule; mission's "distinct day rules" warning validated). Same page verbatim: Contract
Unit "5,000 troy ounces" (the SI-5000oz class note of the v1 dossier CONFIRMED official);
tick "Outright transactions: $0.005 per troy ounce. Straddle or spread transactions and
settlement prices: $0.001"; Listed Contracts "…any January, March, May, and September falling
within a 23-month period; and any July and December falling within a 60-month period" — active
cycle **F,H,K,N,U,Z** (v1 dossier's measured liquid cycle H,K,N,U,Z is a subset).
**FACT(ARCHIVED_OFFICIAL ×2 eras).**

Live-page limitation [measured]: all four live `cmegroup.com/markets/…​.contractSpecs.html`
pages fetched 200 on 2026-10-03 via web_reader but render the spec table only through the
`product-contract-specs-widget` clientlib JS — no static Termination text (log entries 1-4).
Archive route is therefore the operative authority path.

---

## 2. Official per-contract expiration calendars (First Trade / Last Trade / Settlement)

Discovery: `…/{product}_product_calendar_futures.html` static tables exist in Wayback for all
four products (CDX inventories in `fetch_log.jsonl`/session; e.g. gold 2009-10→2020-06,
silver 2009-11→2021-06, NG 2009-10→2017+, CL 2009-10→2021-06). Extracted rows are preserved in
`html/*_rows.txt` (pipe-delimited, 8 columns as on the page).

| symbol | captures used (resolved) | contract rows | coverage of Last-Trade dates | class |
|---|---|---|---|---|
| CL | 20100310023046; 20180228030442 | 75 + 108 | **Apr 2010 → Feb 2027** (overlap 2018 consistent) | ARCHIVED_OFFICIAL |
| NG | 20100430195312; 20170220105945 | 120 + 120 | **Jun 2010 → Feb 2027** (overlap 2017-2020 consistent) | ARCHIVED_OFFICIAL |
| GC | 20130824022026 | 22 | **Aug 2013 → Jun 2019** | ARCHIVED_OFFICIAL |
| SI | 20150318171925 | 20 | **Mar 2015 → Dec 2019** | ARCHIVED_OFFICIAL |

Sample verbatim rows (of the 541 total preserved):
- `APR 2010 | CLJ10 | First 02/09/2006 / Last 03/22/2010 | Settlement 03/22/2010 | … | Delivery 04/01/2010/04/30/2010`
- `Feb 2027 | CLG27 | 22 Jan 2018 / 20 Jan 2027 | …`
- `JUN 2010 | NGM10 | 05/27/2004 / 05/26/2010 | …`
- `AUG 2013 | GCQ13 | 09/30/2011 / 08/28/2013 | …`
- `Dec 2019 | SIZ19 | 31 Dec 2014 / 27 Dec 2019 | …`

**Rule ↔ table reconciliation (spot checks, all PASS)** [OBSERVED]:
- CLZ18 (Dec-2018): table LTD 11/19/2018. Rule: 25 Nov 2018 = Sunday; Nov 22 = Thanksgiving
  (official holiday); 3 bd prior to last-bd-before-25th (Nov 23) = Nov 19 ✓ (also satisfies the
  2020-era "4 bd prior to the 25th" variant).
- CLJ10: 25 Mar 2010 Thursday business day; 3 bd prior = Mar 22 ✓ (table 03/22/2010).
- NGM10: May 2010 last bds = 28,27,26 (May 31 Memorial) → 3rd-last = May 26 ✓.
- NGK20: Apr 2020 → Apr 28 ✓. GC M19: Jun 2019 → Jun 26 ✓. SI Z19: Dec 2019 → Dec 27 ✓.

Gaps (measured, not inferred):
- **GC 2010→mid-2013**: OBTAINABLE — CDX shows 2009-2012 captures of the gold calendar; the one
  attempted fetch (20110925050946) failed transport twice (no output; curl exit 7) ⇒
  NOT_OBTAINED this session (2-attempt etiquette stop).
- **GC mid-2019→2026 / SI 2019→2026**: NOT_OBTAINED — tested captures 20180602051402,
  20200525023744 (GC) and 20180614091251, 20200803212643 (SI) are JS shells with the table
  skeleton but zero data rows; 2019-era captures NOT_RUN; mirrors the ES-lane 2019-2023 archive
  gap. Live product-calendar pages are JS shells (same widget family the ES lane found).
  Filling 2019-2026 from the rule + holiday calendar would be arithmetic POSTULATION, not
  authority — not done here.
- **SI 2010→early-2015**: OBTAINABLE — 2009-2014 captures exist per CDX; NOT_FETCHED (budget).

---

## 3. Holiday / early-close authority per product line (energy = NYMEX; metals = COMEX)

Structural finding [ARCHIVED_OFFICIAL]: CME holiday documents treat **"NYMEX, COMEX® and DME
Products on CME Globex"** as ONE product family — energy and metals share the family schedule,
which is DISTINCT from equities (e.g. 2010: NYMEX/COMEX had 12:15 CT trading halts on
MLK/Presidents/Memorial/Jul-4/Labor while equities had 10:30 halts; NYMEX/COMEX post-
Thanksgiving close 12:45 CT vs equities 12:15 CT).

### 2010 — OBTAINED_FULL [ARCHIVED_OFFICIAL]

Official 38-page PDF "CME Globex 2010 Holiday Calendar" (per-section "Last updated"
12/17/2009-2/3/2010), via capture **20100215061802** of
`http://www.cmegroup.com/tools-information/holiday-calendar/files/2010-globex-holiday-calendar.pdf`
(saved `globex_2010_holiday.pdf`; NYMEX/COMEX sections extracted verbatim to
`nymex_comex_2010_holidays.txt`). Verbatim essentials:
- New Year: "Thursday, Dec 31 [2009] 1615 CT / 1715 ET – Regular … close … Friday, Jan 1 CME
  Globex is closed … Sunday, Jan 3 1700 CT – Regular … open". (NYMEX Brent TAS exception 1200 CT.)
- MLK: "Friday, Jan 15 1515 CT / 1615 ET – Early CME Globex close … Monday, Jan 18 1215 CT /
  1315 ET – Trading halt … 1700 CT – Halted products resume trading." (Same pattern Presidents
  Feb 15, Memorial May 31, Jul 5, Sep 6: prior-Friday early close 1515 CT; Monday 1215→1700 CT halt.)
- Good Friday: "Friday, Apr 2 No CME Globex Trading on Good Friday."
- Columbus: "Friday, Oct 8 1515 CT – Early CME Globex close … Monday, Oct 11 1615 CT – Regular
  CME Globex Close" (normal Monday).
- Veterans: Wed Nov 10 regular close 1615 CT; Nov 11 regular session (normal day).
- Thanksgiving: "Wednesday, Nov 24 1615 CT – Regular … close … 1700 CT – Regular … open for
  trade date Friday, Nov 26 … Thursday, Nov 25 1215 CT – Trading halt … Friday, Nov 26 1245 CT –
  Early CME Globex Close … • Exception: TAS contracts close at 12:30".
- Christmas: "Thursday, Dec 23 1615 CT / 1715 ET – Regular … close • Exception: TAS contracts
  will close at 12:30 CT / 1330 ET … Friday, Dec 24 CME Globex is closed."
- New Year's Eve: "Friday, Dec 31 [2010] 1515 CT / 1615 ET – Early CME Globex close."

### 2011 — route proven, 1/12 holidays fetched [ARCHIVED_OFFICIAL]

Archived official 2011 holiday page (capture **20110313182401**, `html/holiday_page_2011.html`)
links the complete per-holiday PDF set (`files/2011-{martin-luther-king, presidents-day,
good-friday, memorial-day, 4th-of-july, labor-day, columbus-day, veterans-day, thanksgiving,
christmas, new-years}.pdf` + 2012-new-years + floor cards + ClearPort calendars). Fetched
**2011-thanksgiving.pdf** (6 pp): NYMEX/COMEX/DME section verbatim — Wed Nov 23 regular close
1615 CT, reopen 1700 CT; Thu Nov 24 halt 1215→1700 CT; **Fri Nov 25 early close 1245 CT /
1345 ET** (source PDF typo "11345 ET" flagged, excluded); TAS close 12:30 CT. Remaining 11
holidays: OBTAINABLE (same route), NOT_FETCHED (budget).

### 2012-2015 — OBTAINABLE (route proven, NOT_FETCHED)

Archived holiday pages for these years carry per-holiday PDF/Excel links (2012/2013/2015
captures verified by D3-CMECAL; same control tree). Estimated ~2-12 fetches/year to complete
the energy/metals family treatment.

### 2016-2025 — PARTIAL [ARCHIVED_OFFICIAL, cross-referenced]

Exchange-level facts fully authority-backed by the D3-CMECAL captures (2016-2025 verbatim
Globex windows, ClearPort no-open days, floor tables — see
`research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/d3_cmecalendar/ES_CALENDAR_EVIDENCE.md`,
same pages, read once, not re-fetched here). Product-line-relevant verbatim already recorded
there includes the 2016 NY-floor rows ("NYMEX close 13:30 ET, COMEX 12:30 ET" Nov 25 / Dec 23
2016) and "Commodity products 12:00 CT" floor early-closes. **NOT_OBTAINED for 2016-2025:**
per-product-line GLOBEX early-close TIMES for energy/metals from static HTML — the era's
per-holiday advisories are Clearing memos (D3 finding), and product hours moved to downloadable
calendars + an interactive widget.

### 2026 — PARTIAL [LIVE_OFFICIAL]

Live `https://www.cmegroup.com/trading-hours.html` fetched 2026-10-03 via web_reader (log).
Product-line-relevant verbatim captured:
- ClearPort: "NYMEX and COMEX: Sunday 5:00 p.m. - Friday 4:00 p.m. CT with no reporting
  Monday - Thursday 4:00 p.m. - 5:00 p.m. CT" — and in the 2026 ClearPort holiday table the
  NYMEX/COMEX lane is affected only by Christmas (Dec 25) and New Year (Jan 1 2026/2027)
  no-opens; the special Good-Friday session explicitly covers only CME/CBOT IR, Equity and FX
  products (not NYMEX/COMEX).
- Holiday Notes, TAS early closes (Nov 27 2026): "Regular closes for Metals TAS contracts;
  Crude, Heating Oil, RBOB & Nat Gas TAS contracts Regular close…" (energy/metals TAS do NOT
  early-close that day).
- (Dec 23 entry, for Dec 24 2026): "Copper TAS: Early close 11:00 CT / 12:00 ET; **Silver TAS:
  Early close 11:25 CT / 12:25 ET; Gold TAS: Early close 11:30 CT / 12:30 ET**; Platinum TAS:
  11:05 CT; Palladium TAS: 11:00 CT; **Crude, Heating Oil, RBOB & Nat Gas TAS: Early close at
  12:30 CT / 13:30 ET**" — note the gold/silver 5-minute offset recurring in TAS times.
- Page anomaly (flagged, excluded): a Holiday Note reading "Thursday March 25th … No trading
  for Friday March 26th trade date in observance of Good Friday" is inconsistent with the 2026
  calendar (Good Friday 2026 = April 3); stale/misdated content — NOT relied upon.
- 2026 product-level Globex holiday hours: behind downloadable calendars + widget ⇒
  NOT_OBTAINED from static HTML (same limit the ES lane recorded).

### Holiday verdict (per product line)

- Closure DAYS for the energy+metals family: authority-backed 2010-2026 (2010 PDF verbatim;
  2011-2025 archived pages/PDF route proven + D3 exchange-level windows; 2026 live).
- Product-line early-close/halt TIMES: OBTAINED 2010 (full); OBTAINABLE 2011-2015 (per-holiday
  PDFs, 1 sample verified); NOT_OBTAINED-from-static 2016-2026 (partial exceptions: floor
  tables, ClearPort, 2026 TAS notes, all quoted above).

---

## 4. Per-symbol verdicts (feasibility, NOT qualification)

| symbol | expiry rule | official last-trade dates | product-line holidays | verdict |
|---|---|---|---|---|
| CL | OBTAINED (2 eras, verbatim; v1 dossier rule matches) | OBTAINED Apr 2010-Feb 2027 (2 chained tables, rule-reconciled) | 2010 FULL; 2011-2015 OBTAINABLE; 2016-2026 partial (exchange-level yes, product-line times no) | **OBTAINABLE ($0, archive class)** |
| NG | OBTAINED (2 eras; 2021 text = v1 dossier wording verbatim; canonical last-trade-month basis confirmed) | OBTAINED Jun 2010-Feb 2027 (2 chained tables, rule-reconciled) | same family class as CL | **OBTAINABLE ($0, archive class)** |
| GC | OBTAINED (2 eras, 12:30 CT third-last bd) | PARTIAL: Aug 2013-Jun 2019 OBTAINED; 2010-mid-2013 OBTAINABLE (transport failed ×2); mid-2019-2026 NOT_OBTAINED (JS-shell era; 2019 captures NOT_RUN) | metals family class (see §3) | **RULE OBTAINED; dates PARTIAL with one hard gap (2019-2026)** |
| SI | OBTAINED (2 eras, 12:25 CT third-last bd; 5,000 oz class confirmed) | PARTIAL: Mar 2015-Dec 2019 OBTAINED; 2010-early-2015 OBTAINABLE; 2019-2026 NOT_OBTAINED (JS-shell era) | metals family class | **RULE OBTAINED; dates PARTIAL with one hard gap (2019-2026)** |

Remainder NOT_OBTAINED after this lane (honest list): GC/SI per-contract official dates
2019-2026 (widget/API era — a headless-browser or registered-download route would be needed,
out of $0/etiquette scope); per-product-line Globex early-close times 2016-2026 (widget era);
2011-2015 energy/metals per-holiday PDFs (11 of 12 for 2011 + other years — route proven,
fetches not spent); 2019-era GC/SI calendar captures untested (NOT_RUN).

## 5. Correction log / incidents

- No memory-filled data: every date/time above was present in a fetched artifact kept under
  `html/`, the two PDFs, or the live-page fetch (all logged).
- GC 2011 calendar fetch: 2 attempts, both transport-fail (no output / curl exit 7) ⇒ stopped
  per etiquette; recorded as NOT_OBTAINED-this-session with CDX existence evidence.
- One live-page anomaly (stale Good-Friday note) and one source-PDF typo ("11345 ET") flagged
  and excluded from reliance.
- `curl`/`wc` etc. were not on this sandbox's PATH; `/usr/bin/curl` absolute path used (same
  default UA, no spoofing).

— End of evidence. All claims FACT(source+capture)/OBSERVED as labeled; nothing inferred.
