# BLS Schedule-Vintage Investigation — Late-2025 Divergence + CPI 2016-04 Double-Entry

Task FUTURES-OVERNIGHT-PREP-20261003, lane **P2C-BLS-VINTAGE**. Generated 2026-10-03 UTC.
$0 read-only lane. Sources: official bls.gov (live, 2026-10-03) + web.archive.org raw `id_`
replays only. 43 captures saved under `captures/` with sha256; every attempt logged in
`fetch_log.jsonl`. Machine companion: `bls_vintage_evidence.json`.

Parent inventory adjudicated:
`research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/events_bbo_coverage/`
(lane A5), anomalies §4.

---

## 1. Verdicts (headline)

| # | Parent anomaly | Verdict |
|---|---|---|
| 1 | BLS-2025-LATE-YEAR-VINTAGE-DIVERGENCE | **RESOLVED_EVIDENCED.** Genuine mid-year revision of the official schedule, officially caused by the **2025 lapse in appropriations** ("suspension of Federal government services", Oct 1 – Nov 12, 2025). Archived Jan-2025 pages = schedule **as-first-published**; current pages/ics = schedule **as-revised** (canceled events erased). Official cause statements OBTAINED (§3). Not "cause NOT_OBTAINED". |
| 2 | CPI-2016-APRIL-DOUBLE-ENTRY (May 17 and Jun 2) | **PARSING ARTIFACT on the parent's side — the double entry does not exist in any capture.** The exact snapshot the parent cited contains one April-2016 row (May 17); no "Jun 2" string exists in the raw bytes; the actual April-2016 CPI was released May 17, 2016 (embargo line on the official archive page). |

One correction to the parent's summary of anomaly 1: the divergence is not only
date shifts. Two releases were **canceled outright** (October-reference CPI on Nov 13;
October-reference Employment Situation on Nov 7), and the parent's "EMPSIT Nov 7→20"
conflates two different rows: the **September-reference** EMPSIT moved Oct 3 → Nov 20,
while the **October-reference** EMPSIT (scheduled Nov 7) was canceled. Full mapping below.

---

## 2. Which version each source represents

- **Archived Jan-2025 pages** (parent's `20250104044048` CPI / `20250104044052` EMPSIT;
  re-fetched raw here): the 2025 advance schedule **as known at capture time** —
  Sep-ref CPI Oct 15, Oct-ref CPI Nov 13, Nov-ref CPI Dec 10; Sep-ref EMPSIT Oct 3,
  Oct-ref EMPSIT Nov 7, Nov-ref EMPSIT Dec 5. Unchanged on the live pages through at
  least 2025-10-02/03 (CPI) and 2025-10-06 (EMPSIT — note the page still printed
  "Oct. 03" on Oct 6, three days after that date had passed with no release).
- **Current pages + bls.ics** (fetched 2026-10-03): the schedule **as revised** —
  revised dates in place, canceled events absent entirely. Current ics CPI 2025 events:
  …Sep 11, **Oct 24**, **Dec 18** (no Nov 13). EMPSIT 2025: …Sep 5, **Nov 20**,
  **Dec 16** (no Oct 3, no Nov 7).
- **Mid-window archived snapshots** show the live pages being edited **in place, silently**
  — four edits total (two per series), no banner or notice ever appeared on
  `cpi.htm`/`empsit.htm` at any capture 2025-01-04 → 2025-12-18. The announcements
  lived on separate pages (§3).

---

## 3. As-of timeline per affected release (all pinned to captures)

Release times are 08:30 AM Eastern (parent-verified, re-verified live). Wayback
timestamps UTC. "RD page" = official
`bls.gov/bls/2025-lapse-revised-release-dates.htm` (created as a stub by 2025-11-13;
dated entries from 2025-11-14; full table incl. cancellations by 2025-11-21).

| Release (ref month) | As-first-published | Revised to | Officially announced | Schedule-page edit window (byte-diff) | Cause (official, verbatim source) |
|---|---|---|---|---|---|
| CPI Sep-2025 | **Oct 15, 2025** | **Oct 24, 2025** | **Oct 10, 2025** — `092025-cpi-reschedule-notice.htm` (page "Last modified: October 10, 2025"; first archived 20251010153854) | (2025-10-03T09:29Z, 2025-10-11T01:27Z] — single in-place edit `Oct. 15→Oct. 24` + appended Dec-ref tail row | "BLS will publish the September 2025 CPI on Friday, October 24, 2025, at 8:30 A.M. ET. No other releases will be rescheduled or produced until the resumption of regular government services. This release allows the Social Security Administration to meet statutory deadlines…" |
| CPI Oct-2025 | **Nov 13, 2025** | **CANCELED** (never published) | by **Nov 21, 2025** (RD page entry "Canceled"; absent at Nov-18 last-modified, present at 20251121165438) | (2025-11-13T14:37Z, 2025-11-21T18:55Z] — row **deleted** + `Dec. 10→Dec. 18` | "BLS could not collect October 2025 reference period survey data due to a lapse in appropriations. BLS is unable to retroactively collect these data… BLS will publish the November 2025 CPI news release on December 18, 2025." |
| CPI Nov-2025 | **Dec 10, 2025** | **Dec 18, 2025** | by **Nov 21, 2025** (RD page) | same edit as above | same CPI note (extended processing; no 1-month % changes where Oct data missing) |
| EMPSIT Sep-2025 | **Oct 3, 2025** | **Nov 20, 2025** | **Nov 14, 2025** (RD page last-modified Nov 14; first dated entries at 20251115003655; stub only at 20251113205426) | (2025-10-06T22:38Z, 2025-11-18T19:10Z] — Sep-ref row rewritten `Oct. 03→Nov. 20`; intermediate captures (Nov 18, Nov 19) still carried the stale `October 2025 → Nov. 07` row | 2025 lapse in appropriations |
| EMPSIT Oct-2025 | **Nov 7, 2025** | **CANCELED** (never published) | by **Nov 21, 2025** (RD page "Canceled") | (2025-11-19T14:44Z, 2025-11-21T18:55Z] — row **deleted** + `Dec. 05→Dec. 16` | "BLS will not publish an October 2025 Employment Situation news release… Household survey data from the Current Population Survey were not collected for the October 2025 reference period due to a lapse in appropriations and will not be collected retroactively… Establishment survey data… for October 2025 will be published with the November 2025 data." |
| EMPSIT Nov-2025 | **Dec 5, 2025** | **Dec 16, 2025** | by **Nov 21, 2025** (RD page) | same edit as above | "the collection period for November 2025 data will be extended, and extra processing time will be needed" |

General official context: `bls.gov/bls/2025_october_shutdown.htm` (first archived
2025-10-01 16:38 UTC): "This website is currently not being updated due to the
suspension of Federal government services. The last update to the site was Wednesday,
October 1, 2025." (an Oct-28 capture updates that to "Friday, October 24, 2025"). The
BLS homepage announcement box carried "Suspension of Federal Government Services." from
Oct 1 and "September 2025 CPI release rescheduled." by Oct 13 (capture 20251013000831).
Note the live BLS site remained current enough to post the Oct-10 reschedule notice and
edit the schedule pages during the suspension; no claim is made here beyond what the
captures show.

Corroboration of the revised outcome: the Oct-26 homepage (capture 20251026000703)
already features "CPI for all items rises 0.3% in September" as the latest release,
with day-of-month "24".

### Capture chain (sha256 in `captures/`; identical shas = identical content)

- CPI page: 20250104 `943d94b0…` → 20250910 `39056af3…` → 20251002 `9aabec51…`
  (nav-only change; rows untouched) → **20251011 = 20251025 = 20251113 all
  `1f738e9e…` (Oct 24 vintage)** → 20251121 `f438037f…` (Oct-ref row gone, Dec 18).
- EMPSIT page: 20250104 `f0ade86c…` → 20250910 = 20250917 `9e1fcdf3…` → 20251006
  `1cf76cb4…` (still original) → 20251118 = 20251119 `c5df0f6c…` (Sep-ref→Nov 20,
  stale Oct-ref row still present) → **20251121 = 20251123 = 20251218 all
  `6ae82ecc…` (final vintage: Sep-ref Nov 20, Nov-ref Dec 16, no Oct-ref row)**.
- RD page: 20251113 stub `0ad44b34…` → 20251115 (last-mod Nov 14, first dates)
  `1caa329e…` → 20251119 (last-mod Nov 18) `1a105288…` → **20251121 (last-mod Nov 21,
  full table + cancellations + notes) `4530808c…`**.

---

## 4. CPI 2016-04 double-entry — adjudication

Claim under test (parent §4.1): the archived 2016 CPI page at snapshot `20160308032422`
"lists the April-2016 release twice (May 17 and Jun 2)".

Findings, all from raw captures:

1. The exact cited snapshot (re-fetched raw, `captures/wb_20160308032422_cpi.htm`,
   sha256 `b55e3f8f…`) contains **one** `release-list` table with 14 rows. The only
   April-2016 row: `April 2016 | May 17, 2016 | 08:30 AM`.
2. Grep of the raw bytes for `June 2|Jun. 2|Jun 2` returns exactly one hit — line 663
   `<td>June 2016</td>`, the June **reference-month** cell (the `Jun. 2` pattern
   matched across "June 2016" only because `.` matched the letter `e`). **No June-2
   release date exists anywhere in the file.**
3. Five further 2016-window snapshots — 20160312, 20160413, 20160508, 20160529
   (after May 17), 20160618 (after Jun 2) — all show the identical 14-row table with
   the single May-17 April row. So it is not a two-vintage artifact either.
4. Actual-release corroboration (official archive, live 2026-10-03):
   `CONSUMER PRICE INDEX — APRIL 2016`, embargo line verbatim: "Transmission of
   material in this release is embargoed until **8:30 a.m. (EDT) May 17, 2016**
   USDL-16-0986".

**Resolution: PARSING ARTIFACT.** The "Jun 2" row does not exist in the source; it was
introduced on the parent's side (their fetch log shows that snapshot was read via
WebFetch, i.e., through an extraction-model rendering). The parent's 2016 monthly grid
(which already uses 2016-05-17) is correct as-known AND as-actual; the anomaly entry
should be retired/annotated, no date changes needed.

---

## 5. PIT implication table (the law, made concrete)

**Law: for a historical decision date D, the correct expected-release calendar is the
schedule vintage as known at D — pinned by a dated capture — never the current
calendar.** The current calendar silently erases canceled events and backfills revised
dates, so naive use injects look-ahead bias and phantom/missing events.

| Decision-date range | Correct as-known late-2025 calendar | What the CURRENT calendar would wrongly give |
|---|---|---|
| 2025-01-04 … 2025-10-09 | CPI: Oct 15 / Nov 13 / Dec 10 · EMPSIT: Oct 3 / Nov 7 / Dec 5 | CPI Oct 24, Dec 18, **no Nov 13** · EMPSIT Nov 20, Dec 16, **no Oct 3, no Nov 7** |
| 2025-10-10 … 2025-11-13 | CPI Sep-ref Oct 24 known; Nov 13 + Dec 10 still listed; EMPSIT Oct 3 / Nov 7 / Dec 5 still listed (none had occurred; notice said "no other releases… until resumption") | same errors as above |
| 2025-11-14 … 2025-11-20 | + EMPSIT Sep-ref Nov 20 officially known (Nov 14) | would also omit the still-listed Nov 13 CPI / Nov 7 EMPSIT expected events |
| from 2025-11-21 | Cancellations + Dec 16/Dec 18 known; pages updated by Nov 21–23 | current calendar correct from here |

Backtest consequences:

1. Event windows keyed to the current calendar place the Sep-2025 CPI event on Oct 24
   instead of the as-then-expected Oct 15; miss the two expected-but-canceled events
   (Nov 13 CPI, Nov 7 EMPSIT) whose **non-arrival** was itself information; and place
   Nov 20 / Dec 16 / Dec 18 events that were unknowable before Nov 14 / Nov 21.
2. The 2025 monthly grid has permanent holes: no October-2025 CPI reference-month
   survey data (partial nonsurvey-based values only, published with the November data),
   no October-2025 CPS household data; CES October data published with November.
   2025 actual print counts: **CPI 11 events, EMPSIT 10 events** — any backtest assuming
   12/12 is structurally wrong for 2025.
3. The phenomenon is **recurrent**: the same official page already lists 2026-lapse
   revisions (CPI Jan-2026 Feb 11 → Feb 13; EMPSIT Jan-2026 Feb 6 → Feb 11 — visible in
   the current ics as `20260213`/`20260211`). The same vintage discipline must be applied
   to any 2026 windows.

---

## 6. Limitations

- Calendar/schedule evidence only. Actual-publish-latency verification (BLS API /
  ALFRED first-print) remains **NOT_RUN**, unchanged from the parent.
- Schedule-page edit instants are bounded by adjacent wayback captures; the true edit
  lies inside each stated window. Announcement dates are pinned independently by the
  official pages' own "Last modified" dates + first archived captures.
- bls.gov live blocked curl (logged BLOCKED_TRANSPORT); live pages evidenced via
  WebFetch/webReader outputs quoted here and in the evidence JSON. All web.archive.org
  captures are raw bytes with sha256.
- Wayback timestamps are UTC (wayback convention); the 08:30 label is Eastern
  (official landing note + ics TZID).

## 7. Files

- `bls_vintage_evidence.json` — machine-readable everything (timeline, verbatim
  notices, sha256s, PIT rows).
- `captures/` — 43 files: 30 raw wayback replays, 6 CDX inventories, ics subset,
  extracted-tables digest. `extract_tables.py`, `fetch_capture.py` — reproducible
  extraction/fetch helpers.
- `fetch_log.jsonl` — every attempt (curl, WebFetch, webReader, WebSearch), incl.
  blocks, voids and retries.
