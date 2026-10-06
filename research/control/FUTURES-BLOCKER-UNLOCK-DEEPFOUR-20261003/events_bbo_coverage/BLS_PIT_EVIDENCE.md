# BLS Release-Calendar PIT Evidence — CPI + Employment Situation, 2010–2026

Task FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003, lane A5-EVENTS-BBO-COVERAGE,
dimension 1. Generated 2026-10-03. $0 read-only lane: official bls.gov pages +
web.archive.org captures only; no accounts, no purchases, no surprise-data claims.

Machine-readable companion: `bls_dates.json` (same directory). Every fetch
attempt is logged in `fetch_log.jsonl` (timestamps there are session
reconstructions, flagged `utc_reconstructed`).

## 1. Verdicts

| series | verdict | coverage | time evidence |
|---|---|---|---|
| CPI (`news_release/cpi.htm`) | **PASS_EVIDENCED_CALENDAR** | 17/17 years (2010–2026), 12/12 scheduled releases per year = 204 | 204/204 rows printed "08:30 AM" |
| Employment Situation / NFP (`news_release/empsit.htm`) | **PASS_EVIDENCED_CALENDAR** | 17/17 years (2010–2026), 12/12 per year = 204 | 204/204 rows printed "08:30 AM" |

PIT quality tag (both series): **SCHEDULE_CALENDAR_OFFICIAL_ARCHIVE_VERIFIED**.
These are the official BLS schedule pages, machine-verified per year in the
repo's ECB 55/55 style: HTTP 200 + page title + verbatim date strings, with the
wayback snapshot timestamp embedded in the replay URL as the as-of verifier.

What this evidence supports and does not:

- CAN support: event-study window placement (calendar-day alignment of CPI/NFP
  events 2010–2026) and schedule-vintage discipline, at the *planned* release
  time of 08:30 Eastern.
- CANNOT support: actual-publish-latency in any downstream feed; any
  surprise-content claim. Actual-publish verification vs BLS API/ALFRED
  first-print: **NOT_RUN** (out of $0 scope, per dispatch "NO surprise-data
  claims — calendars only").

## 2. Method (machine-verifiable)

1. Live schedule pages (underscore path, hyphen variants 404):
   `https://www.bls.gov/schedule/news_release/cpi.htm` and
   `.../empsit.htm`. Each page states it is the BLS release schedule and shows
   the full current-year 12-month grid in advance (even January captures show
   the whole year), plus a prior-year tail.
2. For 2010–2025: web.archive.org CDX
   (`filter=statuscode:200`, `collapse=timestamp:4`) to enumerate snapshots,
   then raw replay `https://web.archive.org/web/<TS>id_/<original-url>` for the
   earliest in-year HTTP-200 snapshot. The snapshot timestamp `id_` in the URL
   is the machine-verifiable as-of. 2026 read from the live page 2026-10-03.
3. Timezone chain, two independent official statements:
   - schedule landing `https://www.bls.gov/schedule/`: "NOTE: All times on
     calendar are Eastern Time." (FACT, fetched 2026-10-03);
   - machine-readable `https://www.bls.gov/schedule/news_release/bls.ics`:
     `DTSTART;TZID=US-Eastern:YYYYMMDDT083000` entries (e.g. `20260113T083000`
     for CPI Jan-2026) with a VTIMEZONE block defining US-Eastern = EST
     −05:00 / EDT −04:00. The ics cross-checks the live-page dates.

## 3. Coverage by year (dates in bls_dates.json; snapshot ts = machine verifier)

CPI: 2010 `20100407094022` · 2011 `20110505154618` · 2012 `20120120090122` ·
2013 `20130116140338` · 2014 `20140122063527` · 2015 `20150106084259` ·
2016 `20160308032422` · 2017 `20170112182310` · 2018 `20180910095325` ·
2019 `20190109024228` · 2020 `20200404075328` · 2021 `20210128124146` ·
2022 `20220108094312` · 2023 `20230104040906` · 2024 `20240104231820` ·
2025 `20250104044048` · 2026 live page.

EMPSIT: 2010 `20100328171528` · 2011 `20110505154645` · 2012 `20120121112110` ·
2013 `20130116234712` · 2014 `20140122063531` · 2015 `20150112110626` ·
2016 `20160307033521` · 2017 `20170109225117` · 2018 `20180403044014` ·
2019 `20190109020429` · 2020 `20200401234727` · 2021 `20210225003256` ·
2022 `20220110090111` · 2023 `20230101123540` · 2024 `20240104231820` ·
2025 `20250104044052` · 2026 live page.

Per-year counts: every year 12/12 for both series; every row 08:30 AM. CPI
2013 includes Oct 30 (printed as such; no cause claim). Weekend-adjacent
oddities like 2012-12-07 / 2017-12-08 / 2023-12-08 EMPSIT (Friday prints) are
verbatim from the pages.

## 4. Anomalies (recorded, not resolved)

1. **CPI-2016-APRIL-DOUBLE-ENTRY**: archived 2016 CPI page lists the
   April-reference release twice (May 17 and Jun 2). Both dates are FACT(page);
   the monthly grid in `bls_dates.json` uses May 17.
2. **BLS-2025-LATE-YEAR-VINTAGE-DIVERGENCE**: archived Jan-2025 pages vs the
   CURRENT `bls.ics` disagree on late-2025: CPI Oct 15→Oct 24, Dec 10→Dec 18;
   EMPSIT Oct 3 absent in current ics, Nov 7→Nov 20, Dec 5→Dec 16. Both
   vintages recorded verbatim. This is live proof that BLS schedule pages are
   vintages and can be revised mid-year — event studies must pin the
   schedule vintage as-of the analysis date. No cause claims.

## 5. Limitations

- Calendar ≠ actual publish: no claim anywhere that data was publicly
  obtainable at 08:30:00.000; only that BLS scheduled 08:30 AM Eastern.
- 2026 grid from the live page (2026-10-03) remains revisable (see §4).
- First archived in-year capture is the earliest verifier we hold; earlier
  same-year vintages may have differed.
- Wayback snapshot timestamps are UTC (wayback convention); the release-time
  label is Eastern per §2.

## 6. Downstream state this unlocks

`DATACONTRACT_QUALIFICATION.md` §1.4 row "US CPI/NFP (BLS)" was
**NOT_RUN — bls_gate/ empty**. This artifact supplies the calendar-leg
evidence for that row (CPI + EMPSIT 2010–2026). It does NOT supply
actual-publish-time evidence, which remains NOT_RUN. Registration-gate
decisions stay with the owner per §3/§5 of that document.
