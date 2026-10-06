# BLS Vintage Normalization — the concrete PIT rule + machine vintage table

Task FUTURES-P3-QUARANTINE-20261004, lane **Q4-DATA-CHECKS**. Generated 2026-10-04 UTC.
Read-only transformation of the P2C investigation
`research/control/FUTURES-OVERNIGHT-PREP-20261003/bls_vintage/{BLS_VINTAGE_INVESTIGATION.md, bls_vintage_evidence.json}`
(captures + sha256 under `bls_vintage/captures/`, 43 files) into the normalization rule a
future backtest consumes. Machine companion: `bls_vintage_table.json` (same dir).
No new fetches were performed in this lane; every dated statement below is
FACT(source+capture) per the P2C evidence chain, re-cited here.

---

## 1. The normalization rule (BINDING for any BLS-event PIT construction)

**Rule.** For a historical decision time `t`, the expected-release calendar is the
**schedule vintage as-of `t`**: for each affected release, use its
**as-first-published** date for `t` strictly before the revision's *official
announcement date* `a`, and its **as-revised** value (or CANCELED status) for
`t >= a`. Formally:

```
expected_release(release R, decision_time t) =
    first_published(R)            if t <  announce(R)
    revised(R)                    if t >= announce(R)        # revised(R) may be CANCELED
```

- `announce(R)` is the **official announcement date** — pinned independently by the
  notice page's own "Last modified" date and its first wayback capture (P2C §3), NOT
  by the schedule-page edit window. The announcement is the knowability bound: the
  revised date was public information from `announce(R)` even on days when the
  schedule page still displayed the stale row (all four 2025 schedule-page edits
  were silent in-place edits; announcements lived on separate pages — P2C §2).
- The P2C §5 decision-range boundaries (2025-10-10, 2025-11-14, 2025-11-21) are
  exactly these announcement dates; this rule inherits them.
- **FORBIDDEN (explicit):** inferring the historical expected calendar from the
  **current** BLS calendar/ics for any decision date before the last revision's
  announcement. The current calendar silently erases canceled events and backfills
  revised dates; naive use injects look-ahead bias and phantom/missing events (P2C
  §5 consequences: Sep-2025 CPI misplaced Oct 15→Oct 24; the two expected-but-
  canceled events Nov-13 CPI / Nov-7 EMPSIT lost — whose NON-arrival was itself
  information; Nov-20 / Dec-16 / Dec-18 events placed at dates unknowable before
  Nov-14 / Nov-21).
- Consequence for 2025 data grids: **CPI has 11 events, EMPSIT 10** in 2025 (no
  October-reference print for either). Any backtest assuming 12/12 is structurally
  wrong for 2025. [FACT per RD-page verbatim notes: Oct-2025 CPI never published;
  EMPSIT Oct-2025 never published; CES Oct data published with November data.]
- Release times are 08:30 AM Eastern on every row affected here (official landing
  note + ics TZID; P2C parent-verified, re-verified live). Wayback timestamps are
  UTC (wayback convention). A decision time `t` on the announcement date itself
  should carry an intraday timestamp; the conservative default is to treat
  knowledge as available only from the next UTC day unless the capture time of the
  announcement is pinned (all three 2025 announcement pages have first-archived
  capture times listed in §3 of the machine table).

## 2. Affected releases and decision-date ranges each vintage applies to

Seven releases. All dates below 08:30 ET release time.

| Release | as-first-published | announce(R) | as-revised | Vintage-A (first-published) applies to decision dates | Vintage-B (revised) applies to |
|---|---|---|---|---|---|
| CPI Sep-2025-ref | **2025-10-15** | **2025-10-10** (reschedule notice; first archived 20251010153854) | **2025-10-24** | t < 2025-10-10 | t >= 2025-10-10 |
| CPI Oct-2025-ref | 2025-11-13 | **2025-11-21** (RD page "Canceled"; capture 20251121165438) | **CANCELED** (never published) | t < 2025-11-21 | t >= 2025-11-21 (expected: no event) |
| CPI Nov-2025-ref | 2025-12-10 | 2025-11-21 (same RD-page edit) | **2025-12-18** | t < 2025-11-21 | t >= 2025-11-21 |
| EMPSIT Sep-2025-ref | 2025-10-03 | **2025-11-14** (RD page last-modified Nov 14; first dated entries capture 20251115003655) | **2025-11-20** | t < 2025-11-14 | t >= 2025-11-14 |
| EMPSIT Oct-2025-ref | 2025-11-07 | 2025-11-21 (RD page "Canceled") | **CANCELED** | t < 2025-11-21 | t >= 2025-11-21 (expected: no event) |
| EMPSIT Nov-2025-ref | 2025-12-05 | 2025-11-21 | **2025-12-16** | t < 2025-11-21 | t >= 2025-11-21 |
| CPI Jan-2026-ref | **2026-02-11** | **NOT_PINNED** from existing artifacts (see §3) | **2026-02-13** | t < announce (unpinned) | t >= announce (unpinned) |

Cross-check against P2C §5's four-range PIT table (all consistent):
- **2025-01-04 .. 2025-10-09** — all six 2025 releases at first-published values
  (CPI Oct 15 / Nov 13 / Dec 10; EMPSIT Oct 3 / Nov 7 / Dec 5).
- **2025-10-10 .. 2025-11-13** — CPI Sep-ref known revised (Oct 24); the other
  five still first-published as listed (none had occurred; the reschedule notice
  said no other releases until resumption of regular government services).
- **2025-11-14 .. 2025-11-20** — + EMPSIT Sep-ref Nov 20 known; CPI Nov 13 / Dec 10
  and EMPSIT Nov 7 / Dec 5 still the listed expectations (cancellations NOT yet
  announced — the still-listed Nov 13 CPI and Nov 7 EMPSIT are *expected events*
  in this range whose non-arrival was information).
- **from 2025-11-21** — cancellations + Dec 16 / Dec 18 known; schedule pages
  updated by Nov 21–23; current calendar == as-known calendar from here.

Capture evidence per version (all FACT, files + sha256 under
`FUTURES-OVERNIGHT-PREP-20261003/bls_vintage/captures/`):

| Version | Evidence captures (sha256 families per P2C §3) |
|---|---|
| CPI page, first-published vintage | `wb_20250104044048_cpi.htm` (`943d94b0…`) → `wb_20250910071545_cpi.htm` (`39056af3…`) → `wb_20251002120859_cpi.htm` (`9aabec51…`, rows untouched) |
| CPI page, Oct-24 vintage | `wb_20251011012756_cpi.htm` = `wb_20251025032156_cpi.htm` = `wb_20251113143722_cpi.htm`, all `1f738e9e…`; edit window (2025-10-03T09:29:09Z, 2025-10-11T01:27:56Z] = single in-place edit `Oct. 15→Oct. 24` + appended Dec-ref tail row |
| CPI page, final vintage (Oct-ref row deleted, Dec 18) | `wb_20251121185534_cpi.htm` (`f438037f…`); edit window (2025-11-13T14:37:22Z, 2025-11-21T18:55:34Z] |
| EMPSIT page, first-published vintage | `wb_20250104044052_empsit.htm` (`f0ade86c…`) → `wb_20250910073017_empsit.htm` = `wb_20250917054731_empsit.htm` (`9e1fcdf3…`) → `wb_20251006223843_empsit.htm` (`1cf76cb4…`, still original on Oct 6 — the page printed "Oct. 03" three days after it passed with no release) |
| EMPSIT page, intermediate (Sep-ref→Nov 20, stale Oct-ref row) | `wb_20251118191021_empsit.htm` = `wb_20251119144405_empsit.htm` (`c5df0f6c…`) |
| EMPSIT page, final vintage (no Oct-ref row, Dec 16) | `wb_20251121185540_empsit.htm` = `wb_20251123023725_empsit.htm` = `wb_20251218182154_empsit.htm`, all `6ae82ecc…` |
| Revised-dates page (RD) evolution | stub `wb_20251113205426` (`0ad44b34…`) → first dated entries `wb_20251115003655` (`1caa329e…`, last-mod Nov 14: EMPSIT Sep Oct 3→Nov 20) → `wb_20251119035927` (`1a105288…`) → full table + cancellations `wb_20251121165438` (`4530808c…`) |
| Reschedule notice (CPI Sep → Oct 24) | `wb_20251010153854_cpi_reschedule-notice.htm`, page "Last modified: October 10, 2025"; linked from homepage box `wb_20251013000831_bls_home.htm` |
| 2026 revision (CPI Jan → Feb 13; EMPSIT Jan → Feb 11) | RD page live fetch 2026-10-03T15:31:28Z (WebFetch; `fetch_log.jsonl` line: "2026-lapse section lists further revisions (e.g. CPI Jan 2026 Feb 11->Feb 13)") + `captures/live_bls_ics_20261003_subset.txt` VEVENTs `DTSTART;TZID=US-Eastern:20260211T083000` (Employment Situation) and `:20260213T083000` (Consumer Price Index) |

Official cause (verbatim quotes in `bls_vintage_evidence.json`
`official_cause_documents`): the 2025 lapse in appropriations (government-services
suspension Oct 1 – Nov 12, 2025) — shutdown page `wb_20251001163841_shutdown.htm`,
reschedule notice, RD-page CPI/EMPSIT notes. The 2026 revisions are attributed to
the 2026 lapse (RD page title now "…2025 and 2026 lapses in appropriations").

## 3. CPI Jan-2026 row — evidence grade and required follow-up

The 2026 row is **weaker-evidenced than the six 2025 rows** and is labeled as such:

- as-revised **2026-02-13**: FACT via the live ics capture (2026-10-03) and the RD
  page's 2026-lapse section. No archived as-of captures of the 2026 window exist in
  the artifact set.
- as-first-published **2026-02-11**: FACT per the RD page 2026-lapse section as
  quoted in `fetch_log.jsonl` (live WebFetch 2026-10-03T15:31:28Z). No capture of
  the 2026 advance schedule page as-first-published exists.
- **announce(CPI Jan-2026) = NOT_PINNED**: the 2026-lapse section's own
  last-modified date / first-archived capture was NOT captured. Therefore the
  vintage-A/vintage-B decision-date split for 2026-02-11→02-13 **cannot be
  enumerated from existing artifacts**. Required follow-up (cheap, permitted
  routes): CDX the 2026-01/02 window of `bls.gov/schedule/news_release/cpi.htm`,
  byte-diff adjacent captures for the `Feb. 11→Feb. 13` edit, and capture the RD
  page's 2026-lapse section with its last-modified date. Until then, any backtest
  with decision dates in 2026-01..02 must treat the CPI Jan-2026 expected date as
  **vintage-ambiguous** and exclude or sensitivity-split the cell (NOT_RUN is the
  default, never an inferred PASS).
- Sibling fact (out of the 7 mandated rows, recorded for completeness): EMPSIT
  Jan-2026 revised 2026-02-06 → **2026-02-11** (same evidence set; same
  NOT_PINNED announcement caveat).

## 4. General as-of keying recipe for future event sources

Every external event/calendar source must be keyed by **(source_page_url,
capture_timestamp, sha256_of_raw_bytes)** — the *vintage key* — never by "the
page" as a timeless object:

1. **Capture, don't quote**: store the raw bytes (curl-direct / web.archive.org
   `id_` replay) + sha256; wayback TS (UTC) embedded in the replay URL is the
   machine-verifiable capture timestamp. Textual renderings (WebFetch/webReader)
   are acceptable only when raw-bytes routes are blocked, and must be logged as
   such (P2C practice: `fetch_log.jsonl` records every attempt incl. blocks).
2. **Multiple vintages per page are the norm**: expect silent in-place edits (all
   four 2025 BLS schedule edits were silent; zero banners at any capture
   2025-01-04→2025-12-18). Detect via byte-diff of adjacent captures; bound edit
   instants by the capture pair, pin announcements independently by the notice
   page's own last-modified date + first archived capture.
3. **PIT join rule**: for decision time `t`, select the vintage with the LATEST
   capture/announcement timestamp `<= t`; never the latest-available vintage.
   A release missing from the as-of-`t` vintage's successor (a cancellation) is
   itself an event expectation to model, not a gap to repair.
4. **Registry shape** (what `bls_vintage_table.json` provides): one row per
   (release, vintage) with `as_first_published`, `announce_date`,
   `as_revised | CANCELED`, `applies_to_decision_dates`, and the evidence capture
   list — so a loader can reconstruct the as-of calendar mechanically.

## 5. Claim taxonomy summary

- All §1–§2 dates/captures: **FACT(source+capture)** per
  `bls_vintage_evidence.json` (as-of timeline, capture chain sha256 families, RD
  page evolution, ics VEVENTs) — no new evidence fetched by this lane.
- §3 NOT_PINNED items and the required follow-up: **NOT_RUN** (explicit).
- The rule itself (§1) and the recipe (§4): **INFERENCE(policy)** derived from
  P2C's §5 law, made mechanical here; boundaries inherited from pinned
  announcement dates.
- Limitations inherited unchanged from P2C §6: calendar/schedule evidence only
  (actual-publish-latency vs downstream feeds NOT_RUN); edit instants bounded by
  adjacent captures; 08:30 ET vs UTC convention as stated.
